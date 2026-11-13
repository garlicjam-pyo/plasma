"""하이브리드 ICP 모델(전자기장 2D + 수송 반경 1D) 실행 스크립트.

    python sim/run_hybrid.py point                   # 기준 운전점 1개: 그림 + 데이터
    python sim/run_hybrid.py point --k 1.5 --phi 180 --P 300 --mode dual
    python sim/run_hybrid.py jacobian                # J_ctrl (이중 코일 2×3, 단일 코일 2×1)
    python sim/run_hybrid.py iso                     # 평균 밀도 유지 + k 스캔 (φ = 0, 90, 180°)
    python sim/run_hybrid.py map                     # (k, φ) 평면의 ρ·n̄_w 지도
    python sim/run_hybrid.py timing                  # 격자별 계산 시간·마진·격자 오차
    python sim/run_hybrid.py check                   # 자체 검산 (포인팅·상반성·보존·T_e 균일 극한의 해석해)
    python sim/run_hybrid.py validate2d              # 반경 1D 수송을 (r, z) 2D 수송과 비교 (축소 오차)
    python sim/run_hybrid.py point --transport 2d    # 2D 수송으로 운전점 계산 (jacobian, iso, map 에도 쓸 수 있음)
    python sim/run_hybrid.py margin                  # J_ctrl 을 바깥 제어 루프에 넣었을 때의 위상 여유 어림
    python sim/run_hybrid.py compare 파일 [--r-scale 0.01 --n-scale 1e6]   # 외부(COMSOL) 분포와 비교
    python sim/run_hybrid.py all                     # 위 계산을 차례로 모두

결과는 figures/hybrid/ 에 저장한다. 설정 기본값은 sim/hybrid/config.py 에 있다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hybrid import control, export, loop, plots_control, plots_point, plots_validate, timing, validate, verify  # noqa: E402
from hybrid.config import Config  # noqa: E402
from hybrid.coupled import solve_point  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "figures" / "hybrid"


def make_config(a) -> Config:
    """명령줄 인자를 설정에 반영한다."""
    cfg = Config().with_op(P_tot=a.P, k=a.k, phi=np.radians(a.phi), p_mtorr=a.p, coil_mode=a.mode)
    return cfg.with_num(transport="full_2d" if a.transport == "2d" else "radial_1d")


def cmd_point(a) -> None:
    cfg = make_config(a)
    sol = solve_point(cfg, verbose=True)
    tag = f"point_{a.mode}_P{a.P:g}_k{a.k:g}_phi{a.phi:g}" + ("_2d" if a.transport == "2d" else "")
    paths = export.save_solution(sol, OUT, tag)
    plots_point.plot_point(sol, OUT / f"{tag}.png")
    m, b = sol.metrics, sol.balance
    print(f"수렴 {sol.converged} · {sol.timing['outer_iters']}회 · {sol.timing['total']*1e3:.0f} ms")
    print(f"n_c = {m.n_c:.4e}, n_edge = {m.n_edge:.4e}, n̄_w = {m.n_bar:.4e} m^-3, ρ = {m.rho:.4f}")
    print(f"I_0 = {sol.heating.I0:.3f} A, P_abs = {sol.heating.P_abs:.1f} W, "
          f"입자 수지 오차 {b['particle_error']:.1e}, 에너지 수지 오차 {b['energy_error']:.1e}")
    print("저장:", OUT / f"{tag}.png", *[p.name for p in paths.values()])


def _save_jacobian(jc: control.ControlJacobian, name: str) -> None:
    y = jc.base.metrics
    data = dict(inputs=jc.inputs, outputs=["n_bar_m3", "rho"], base=dict(n_bar=y.n_bar, rho=y.rho, n_c=y.n_c, n_edge=y.n_edge),
                J=jc.J, J_norm=jc.J_norm, singular_values=jc.singular_values, rank=jc.rank, condition=jc.condition,
                shape_gain=jc.shape_gain, steps=jc.steps, seconds=jc.seconds,
                note="J 단위: 행 [m^-3, 1] / 열 [W, 1, rad]. J_norm: d ln y / d ln u (phi 열은 rad 당).")
    (OUT / f"{name}.json").write_text(json.dumps(export._jsonable(data), ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_jacobian(a) -> None:
    cfg = make_config(a).with_op(coil_mode="dual")
    dual = control.control_jacobian(cfg)
    single = control.control_jacobian(cfg.with_op(coil_mode="single_series"))
    tag = f"jacobian_P{a.P:g}_k{a.k:g}_phi{a.phi:g}"
    _save_jacobian(dual, tag + "_dual"); _save_jacobian(single, tag + "_single")
    rows = []
    for mode, jc in (("dual", dual), ("single_series", single)):
        for i, out in enumerate(("n_bar", "rho")):
            vals = list(jc.J_norm[i]) + [""] * (3 - jc.J_norm.shape[1])     # 단일 코일은 P_tot 열만 있음
            rows.append([mode, out, *vals])
    export.write_csv(OUT / f"{tag}.csv", ["coil_mode", "output", "dln/dlnP", "dln/dlnk", "dln/dphi_rad"], rows)
    plots_control.plot_jacobian(dual, single, OUT / f"{tag}.png")
    np.set_printoptions(precision=4, linewidth=140)
    print("이중 코일 J_ctrl [행: n̄_w, ρ / 열: P_tot, k, φ]"); print(dual.J)
    print("무차원 J_norm"); print(dual.J_norm)
    print(f"특이값 {dual.singular_values}, 계수 {dual.rank}, 조건수 {dual.condition:.2f}, 형상 감도 {dual.shape_gain}")
    print("단일 코일 J_norm", single.J_norm.ravel(), "계수", single.rank)
    print(f"계산 시간: 이중 {dual.seconds:.2f} s, 단일 {single.seconds:.2f} s · 저장: {OUT / (tag + '.png')}")


def cmd_iso(a) -> None:
    cfg = make_config(a).with_op(coil_mode="dual", phi=0.0)
    k_values = np.linspace(0.4, 3.0, 11)
    first = control.iso_mean_scan(cfg, k_values, 0.0)       # 이 스캔의 기준점 n̄_w 를 목표값으로 삼는다
    target = first["target"]
    scans = [first] + [control.iso_mean_scan(cfg, k_values, np.radians(d), target) for d in (90.0, 180.0)]
    rows = [[np.degrees(s["phi"]), *vals] for s in scans
            for vals in zip(s["k"], s["P_tot"], s["n_bar"], s["rho"], s["n_c"], s["n_edge"], s["I0"])]
    export.write_csv(OUT / "iso_mean_scan.csv", ["phi_deg", "k", "P_tot_W", "n_bar_m3", "rho", "n_c_m3", "n_edge_m3", "I0_A"], rows)
    plots_control.plot_iso_scan(scans, OUT / "iso_mean_scan.png")
    for s in scans:
        print(f"φ = {np.degrees(s['phi']):5.0f}°: ρ {s['rho'].min():.3f} – {s['rho'].max():.3f}, "
              f"P_tot {s['P_tot'].min():.0f} – {s['P_tot'].max():.0f} W, n̄_w 편차 {np.max(np.abs(s['n_bar']/target-1)):.1e}")
    print("저장:", OUT / "iso_mean_scan.png")


def cmd_map(a) -> None:
    cfg = make_config(a).with_op(coil_mode="dual")
    mp = control.response_map(cfg, np.linspace(0.3, 3.0, 19), np.radians(np.linspace(-180, 180, 25)))
    rows = [[np.degrees(p), k, mp["n_bar"][i, j], mp["rho"][i, j]] for i, p in enumerate(mp["phi"]) for j, k in enumerate(mp["k"])]
    export.write_csv(OUT / "response_map.csv", ["phi_deg", "k", "n_bar_m3", "rho"], rows)
    plots_control.plot_map(mp, cfg, OUT / "response_map.png")
    print(f"ρ 범위 {mp['rho'].min():.3f} – {mp['rho'].max():.3f} · 저장: {OUT / 'response_map.png'}")


def cmd_timing(a) -> None:
    study = timing.timing_study(make_config(a))
    keys = list(study["rows"][0].keys())
    export.write_csv(OUT / "timing.csv", keys, [[r[k] for k in keys] for r in study["rows"]])
    plots_control.plot_timing(study, OUT / "timing.png")
    print(" 격자      운전점[s]  J_ctrl[s]  마진(점)  마진(J)  오차 n̄_w   오차 ρ    오차 J")
    for r in study["rows"]:
        print(f"{r['Nr']:4d}×{r['Nz']:<4d} {r['t_point_s']:9.3f} {r['t_jacobian_s']:10.2f} {r['margin_point']:8.1f} "
              f"{r['margin_jacobian']:8.1f}  {r['err_n_bar']:.1e}  {r['err_rho']:.1e}  {r['err_J']:.1e}")
    rec = study["recommended"]
    print("추천 격자:", f"{rec['Nr']}×{rec['Nz']}" if rec else "조건을 만족하는 격자 없음", "· 저장:", OUT / "timing.png")


def cmd_check(a) -> None:
    results = verify.run_checks(make_config(a))
    for name, val, tol, ok in results:
        print(f"{'통과' if ok else '실패'}  {name:50s} {val:9.2e}  (허용 {tol:.0e})")
    export.write_csv(OUT / "check.csv", ["item", "value", "tolerance", "passed"], results)
    if not all(r[3] for r in results):
        raise SystemExit("검산 실패 항목이 있습니다.")


def cmd_validate2d(a) -> None:
    study = validate.validation_study(make_config(a))
    keys = list(study["rows"][0].keys())
    export.write_csv(OUT / "validate2d.csv", keys, [[r[k] for k in keys] for r in study["rows"]])
    plots_validate.plot_validation(study, OUT / "validate2d.png")
    print("운전점               n̄_w 차[%]   ρ 차[%]   T_e z차[V]   1D[s]  2D[s]")
    for r in study["rows"]:
        print(f"{r['case']:18s} {100*r['err_n_bar']:+9.2f} {100*r['err_rho']:+9.2f} {r['Te_z_spread']:10.2f} "
              f"{r['t_1d_s']:8.2f} {r['t_2d_s']:6.2f}")
    j1, j2 = study["jac_1d"], study["jac_2d"]
    np.set_printoptions(precision=4, linewidth=140)
    print("J_norm (1D)"); print(j1.J_norm); print("J_norm (2D)"); print(j2.J_norm)
    print(f"J 성분 최대 차 {study['err_J']:.4f} · 형상 감도 1D {j1.shape_gain} / 2D {j2.shape_gain}")
    print(f"J_ctrl 계산 시간 1D {j1.seconds:.2f} s / 2D {j2.seconds:.2f} s · 저장: {OUT / 'validate2d.png'}")


def cmd_margin(a) -> None:
    rows = loop.margin_study(make_config(a))
    keys = list(rows[0].keys())
    export.write_csv(OUT / "loop_margin.csv", keys, [[r[k] for k in keys] for r in rows])
    plots_control.plot_margin(rows, OUT / "loop_margin.png")
    print(f"적분 제어 ω_c = {loop.OMEGA_C} rad/s, 구동기 지연 {loop.TAU_ACT} s, 입력 (P_tot, k), φ 고정")
    print("경우                  λ_min  λ_max  위상[°]  PM(T_d=1 s)  PM(T_d=2 s)  GM(2 s)  설정 시간[s]")
    for r in rows:
        print(f"{r['scenario']:18s} {r['lam_min']:6.2f} {r['lam_max']:6.2f} {r['lam_phase_deg']:7.1f} {r['pm_Td1']:10.1f} "
              f"{r['pm_Td2']:12.1f} {r['gm_Td2']:8.1f} {r['settle_s']:10.0f}")
    print("저장:", OUT / "loop_margin.png")


def cmd_compare(a) -> None:
    sol = solve_point(make_config(a))
    data = export.load_table(Path(a.file), scale=(a.r_scale, a.n_scale))
    cmp = export.compare_radial(sol, data[:, 0], data[:, -1])
    plots_point.plot_compare(cmp, OUT / "compare_radial.png")
    for key in ("n_bar_model", "n_bar_external", "n_bar_ratio", "rho_model", "rho_external", "rho_diff",
                "profile_rms_rel", "profile_max_rel", "shape_rms"):
        print(f"{key:18s} {cmp[key]:.4e}")
    print("저장:", OUT / "compare_radial.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["point", "jacobian", "iso", "map", "timing", "check", "validate2d", "margin", "compare", "all"])
    ap.add_argument("file", nargs="?", help="compare 에서 읽을 외부 결과 파일 (열: r, 값 또는 r, z, 값)")
    ap.add_argument("--P", type=float, default=300.0, help="총 공급 전력 [W]")
    ap.add_argument("--k", type=float, default=1.0, help="전류 크기비")
    ap.add_argument("--phi", type=float, default=0.0, help="위상차 [deg]")
    ap.add_argument("--p", type=float, default=10.0, help="압력 [mTorr]")
    ap.add_argument("--mode", default="dual", choices=["dual", "single_series", "single_inner"])
    ap.add_argument("--transport", default="1d", choices=["1d", "2d"], help="수송 모델: 반경 1D(기본) 또는 (r, z) 2D 검증판")
    ap.add_argument("--r-scale", type=float, default=1.0, help="외부 파일의 r 을 m 로 바꾸는 배수")
    ap.add_argument("--n-scale", type=float, default=1.0, help="외부 파일의 밀도를 m^-3 로 바꾸는 배수")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    table = dict(point=cmd_point, jacobian=cmd_jacobian, iso=cmd_iso, map=cmd_map, timing=cmd_timing,
                 check=cmd_check, validate2d=cmd_validate2d, margin=cmd_margin, compare=cmd_compare)
    for name in (["check", "point", "jacobian", "iso", "map", "timing", "validate2d", "margin"] if a.command == "all" else [a.command]):
        print(f"\n===== {name} =====")
        table[name](a)


if __name__ == "__main__":
    main()
