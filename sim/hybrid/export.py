"""결과를 파일로 내보내고, 외부(COMSOL 등) 결과와 비교하는 도구.

내보내는 파일 (tag 는 운전점 이름):
  {tag}_summary.json     설정, 지표, 수지, 포트 임피던스, 계산 시간
  {tag}_radial.csv       반경별 n0, n_w, T_e, S, 생성률, 손실 주파수
  {tag}_field_rz.csv     (r, z) 격자점별 |E_θ|, 위상, p_abs, n_e, T_e  ← COMSOL 내보내기와 같은 긴 표 형식
  {tag}_convergence.csv  바깥 반복별 수렴 기록

COMSOL 과 비교할 때는 COMSOL 에서 같은 양을 "r, z, 값" 또는 "r, 값" 열의 텍스트로 내보낸 뒤
`load_table` 로 읽어 `compare_radial` 에 넣는다. 열 이름·단위는 아래 COLUMNS 에 적은 것과 맞춘다.
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .coupled import Solution
from .metrics import ring_average

# 파일에 쓰는 열 이름과 단위 (COMSOL 쪽 내보내기 설정을 이 표에 맞춘다)
COLUMNS = {
    "r_m": "반지름 [m]", "z_m": "높이 [m] (웨이퍼 = 0)",
    "n0_m3": "중간 높이 전자 밀도 [m^-3]", "n_wafer_m3": "관측 높이 z_w 의 전자 밀도 [m^-3]",
    "Te_V": "전자온도 [V] (radial.csv 에서는 z 평균)", "S_W_m2": "z 적분 흡수 전력 [W/m^2]",
    "G_m2s": "z 적분 이온화 생성률 [1/(m^2 s)]", "nuL_1s": "축 방향 벽 손실 주파수 [1/s]",
    "E_abs_V_m": "|E_θ| [V/m]", "E_phase_deg": "E_θ 위상 [deg]", "p_abs_W_m3": "흡수 전력 밀도 [W/m^3]",
    "ne_m3": "전자 밀도 [m^-3]",
}


def _jsonable(obj):
    """numpy 값·복소수를 JSON 에 쓸 수 있는 형태로 바꾼다."""
    if isinstance(obj, dict):
        return {k: _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return _jsonable(obj.tolist())
    if isinstance(obj, complex):
        return {"re": obj.real, "im": obj.imag}
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    return obj


def write_csv(path: Path, header: list, rows) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def save_solution(sol: Solution, out_dir: Path, tag: str) -> dict:
    """운전점 하나의 결과를 네 개 파일로 저장하고 경로를 돌려준다."""
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg, g, st, heat = sol.cfg, sol.grid, sol.state, sol.heating
    col = st.column(cfg, g)                     # z 로 적분한 양 (1D·2D 상태 공통 메서드)
    paths = {k: out_dir / f"{tag}_{k}" for k in ("summary.json", "radial.csv", "field_rz.csv", "convergence.csv")}
    summary = dict(
        config=asdict(cfg), converged=sol.converged, metrics=asdict(sol.metrics), balance=sol.balance,
        heating=dict(I0_A=heat.I0, P_abs_W=heat.P_abs, P_coil_W=heat.P_coil, P_port_W=heat.P_port,
                     efficiency=heat.P_abs / cfg.op.P_tot),
        Z_port_ohm=sol.unit.Z_port, R_plasma_ohm=sol.unit.R_pl.real, timing=sol.timing, columns=COLUMNS)
    paths["summary.json"].write_text(json.dumps(_jsonable(summary), ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(paths["radial.csv"], ["r_m", "n0_m3", "n_wafer_m3", "Te_V", "S_W_m2", "G_m2s", "nuL_1s"],
              zip(g.r, st.midplane(cfg), st.wafer_profile(cfg), st.Te_radial(), heat.S, col["G"], col["nuL"]))
    zp = g.z[: g.Nzp]
    ne, Te = st.ne_rz(zp, cfg), st.Te_rz(zp)
    rows = []
    for j in range(g.Nz):                       # 창·코일 영역은 장만 있고 플라즈마 양은 0
        for i in range(g.Nr):
            in_pl = j < g.Nzp
            rows.append([g.r[i], g.z[j], abs(heat.E[j, i]), np.degrees(np.angle(heat.E[j, i])),
                         heat.p_abs[j, i] if in_pl else 0.0, ne[j, i] if in_pl else 0.0, Te[j, i] if in_pl else 0.0])
    write_csv(paths["field_rz.csv"], ["r_m", "z_m", "E_abs_V_m", "E_phase_deg", "p_abs_W_m3", "ne_m3", "Te_V"], rows)
    write_csv(paths["convergence.csv"], list(sol.history[0].keys()), [h.values() for h in sol.history])
    return paths


# ------------------------------------------------------------------ 외부 결과와 비교
def load_table(path: Path, scale: tuple = ()) -> np.ndarray:
    """COMSOL 텍스트/CSV 내보내기를 읽는다. '%' 나 '#' 로 시작하는 줄과 글자 머리줄은 건너뛴다.

    scale 로 열마다 단위 환산 배수를 준다. 예: r 이 cm, 밀도가 cm^-3 이면 scale=(1e-2, 1e6)."""
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line[0] in "%#":
            continue
        try:
            rows.append([float(v) for v in line.replace(",", " ").split()])
        except ValueError:
            continue                              # 열 이름이 적힌 머리줄
    data = np.array(rows)
    for c, s in enumerate(scale):
        data[:, c] *= s
    return data


def compare_radial(sol: Solution, r_ext: np.ndarray, n_ext: np.ndarray) -> dict:
    """외부에서 온 웨이퍼 높이 밀도 분포 n(r) 와 이 모델의 n_w(r) 를 비교한다.

    외부 분포를 이 모델의 반경 격자로 보간한 뒤, 같은 정의로 n̄_w 와 ρ 를 계산해 나란히 돌려준다."""
    cfg, g = sol.cfg, sol.grid
    order = np.argsort(r_ext)
    n_on_grid = np.interp(g.r, r_ext[order], n_ext[order])
    geo = cfg.geom
    n_c = ring_average(n_on_grid, g, 0.0, geo.r_c)
    n_edge = ring_average(n_on_grid, g, geo.r_1, geo.r_2)
    n_bar = ring_average(n_on_grid, g, 0.0, geo.R_w)
    ours = sol.state.wafer_profile(cfg)
    inside = g.r <= geo.R_w
    rel = (ours[inside] - n_on_grid[inside]) / n_on_grid[inside]
    m = sol.metrics
    return dict(r=g.r, model=ours, external=n_on_grid,
                n_bar_model=m.n_bar, n_bar_external=n_bar, rho_model=m.rho, rho_external=n_c / n_edge,
                n_bar_ratio=m.n_bar / n_bar, rho_diff=m.rho - n_c / n_edge,
                profile_rms_rel=float(np.sqrt(np.mean(rel**2))), profile_max_rel=float(np.max(np.abs(rel))),
                # 절대값이 아니라 모양만 비교: 각자 자기 평균으로 나눈 분포의 차이
                shape_rms=float(np.sqrt(np.mean((ours[inside] / m.n_bar - n_on_grid[inside] / n_bar) ** 2))))
