"""전자기장–수송 자기일관 반복 (발표 덱 11쪽).

    (n_e, T_e)^(m) → σ_p → E_θ → I_0, p_abs → 에너지–입자 연립 → (n_e, T_e)^(m+1)

수렴 판정은 덱의 세 가지를 모두 기록한다.
  ① 수치 갱신량   : 연속 반복 사이 ln n_e, T_e 의 최대 상대 변화
  ② 결합 잔차     : 현재 상태로 장을 다시 풀어 얻은 가열을 넣었을 때의 수송 잔차 max|F|
  ③ 보존 오차     : 입자 수지(생성 = 벽 손실), 에너지 수지(흡수 = 손실)의 상대 오차
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from .config import Config
from .em_field import EMSolver, Heating, UnitFields
from .metrics import WaferMetrics, wafer_metrics
from .state import Grid
from .transport_1d import RadialTransport
from .transport_2d import Transport2D


@dataclass
class Solution:
    """한 운전점의 수렴 결과."""
    cfg: Config
    grid: Grid
    state: object                       # PlasmaState (반경 1D) 또는 PlasmaState2D
    unit: UnitFields
    heating: Heating
    metrics: WaferMetrics
    balance: dict                       # 입자·에너지 수지 항과 상대 오차
    history: list = field(default_factory=list)   # 바깥 반복별 수렴 기록 (dict 목록)
    converged: bool = False
    timing: dict = field(default_factory=dict)    # 계산 시간 [s]: total, em, transport


def balance_report(tr, state, heat: Heating) -> dict:
    """전체 체적의 입자·에너지 수지 (덱 11쪽 수렴 판정 ②③)."""
    t = tr.terms(state, heat)
    gen, ax, rad = t["gen"].sum(), t["loss_axial"].sum(), t["wall_radial_n"]
    p_in = t["heat"].sum()
    p_out = dict(coll=t["coll"].sum(), wall_axial=t["wall_axial"].sum(),
                 wall_radial=t["wall_radial_e"], field_work=-t["work"].sum())
    return dict(gen=gen, loss_axial=ax, loss_radial=rad,
                particle_error=(gen - ax - rad) / gen,
                P_abs=p_in, **{"P_" + k: v for k, v in p_out.items()},
                energy_error=(p_in - sum(p_out.values())) / p_in)


def make_transport(grid: Grid, cfg: Config):
    """설정에 따라 수송 모델을 고른다. 두 모델은 같은 메서드(initial_state, pack, unpack, residual, solve, terms)를 가진다."""
    return Transport2D(grid, cfg) if cfg.num.transport == "full_2d" else RadialTransport(grid, cfg)


def solve_point(cfg: Config, guess=None, verbose: bool = False) -> Solution:
    """운전점 하나를 수렴시킨다. `guess` 를 주면 그 상태에서 출발한다(가까운 운전점의 해 재사용)."""
    t_start = time.perf_counter()
    grid = Grid(cfg)
    em, tr = EMSolver(grid, cfg), make_transport(grid, cfg)
    state = tr.initial_state(guess)
    history, t_em, t_tr, converged = [], 0.0, 0.0, False
    alpha = cfg.num.relax
    for m in range(cfg.num.outer_max + 1):
        t0 = time.perf_counter()
        unit = em.solve_unit(state)                  # 5.2–5.3: 전도도와 단위 전류 장
        heat = em.heating(unit)                      # 5.4–5.5: I_0 와 흡수 전력
        t1 = time.perf_counter()
        x_old = tr.pack(state)                       # x = [ln(n/n_ref), T_e]
        coupled_res = float(np.max(np.abs(tr.residual(x_old, heat))))
        res = tr.solve(heat, state)                  # 5.6–5.8: 에너지–입자 연립
        t2 = time.perf_counter()
        t_em += t1 - t0; t_tr += t2 - t1
        x_new = tr.pack(res.state)
        half = x_old.size // 2
        d_n = float(np.max(np.abs(x_new[:half] - x_old[:half])))
        d_T = float(np.max(np.abs(x_new[half:] / x_old[half:] - 1.0)))
        bal = balance_report(tr, state, heat)
        history.append(dict(iter=m, coupled_residual=coupled_res, d_ln_n=d_n, d_Te=d_T,
                            newton_iters=res.iterations, I0=heat.I0, P_abs=heat.P_abs,
                            particle_error=bal["particle_error"], energy_error=bal["energy_error"]))
        if verbose:
            print(f"  반복 {m:2d}: 결합 잔차 {coupled_res:9.2e}  Δln n {d_n:9.2e}  ΔT_e {d_T:9.2e}"
                  f"  Newton {res.iterations:2d}회  I0 {heat.I0:6.2f} A  P_abs {heat.P_abs:6.1f} W")
        if max(d_n, d_T) < cfg.num.outer_tol:        # 장을 다시 풀어도 상태가 변하지 않음 → 수렴
            converged = True
            break
        if not res.converged:
            alpha = max(0.3, 0.5 * alpha)            # 안쪽 Newton 이 실패하면 완화를 강하게
        state = tr.unpack((1 - alpha) * x_old + alpha * x_new)   # 완화: 밀도는 로그 값으로 섞인다
    total = time.perf_counter() - t_start
    return Solution(cfg, grid, state, unit, heat, wafer_metrics(state, grid, cfg),
                    balance_report(tr, state, heat), history, converged,
                    dict(total=total, em=t_em, transport=t_tr, outer_iters=len(history)))
