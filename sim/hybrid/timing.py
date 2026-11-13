"""계산 시간 예산과 타이밍 마진 분석.

이 모델의 용도는 설계 탐색이다. 세 입력 (P_tot, k, φ) 를 바꿔 가며 J_ctrl 과 응답 지도를
대화하듯 뽑아 보는 것이 목적이므로, 아래 예산을 요구 조건으로 둔다.

    운전점 1개 수렴      : 1 초 이내
    J_ctrl 1개 (7회 수렴): 10 초 이내

평소 실행 시간은 예산의 1/3 이하가 되게 격자를 고른다(마진 3배 이상). 격자 오차는 0.1 % 이하로 둔다. 남는 2/3 는
(1) 더 느린 컴퓨터, (2) 수렴이 느린 운전점(저전력·저밀도), (3) 나중에 식이 늘어날 때를 위한 여유다.
`timing_study` 는 격자를 바꿔 가며 실제 시간과 격자 오차를 재서 이 조건을 만족하는 격자를 고른다.
"""
from __future__ import annotations

import statistics
import time

import numpy as np

from .config import Config
from .control import control_jacobian
from .coupled import solve_point

BUDGET_POINT_S = 1.0        # 운전점 1개 예산 [s]
BUDGET_JACOBIAN_S = 10.0    # J_ctrl 1개 예산 [s]
MIN_MARGIN = 3.0            # 요구 마진 (예산 ÷ 실제 시간)
MAX_GRID_ERROR = 0.001      # 허용 격자 오차 (기준 격자 대비 n̄_w, ρ 의 상대 차). 모델 가정의 오차보다 훨씬 작게 둔다

# (Nr, Nz_plasma, Nz_upper). 마지막이 오차 기준으로 쓰는 가장 촘촘한 격자.
GRIDS = ((30, 12, 16), (42, 16, 22), (60, 24, 32), (84, 32, 44), (120, 48, 64))
REFERENCE_GRID = (168, 64, 88)


def _with_grid(cfg: Config, grid) -> Config:
    return cfg.with_num(Nr=grid[0], Nz_plasma=grid[1], Nz_upper=grid[2])


def timing_study(cfg: Config, repeats: int = 3) -> dict:
    """격자별 계산 시간, 격자 오차, 마진을 표로 만든다."""
    ref = control_jacobian(_with_grid(cfg, REFERENCE_GRID))
    y_ref = ref.base.metrics.as_vector()
    solve_point(_with_grid(cfg, GRIDS[0]))                  # 첫 호출의 준비 시간을 측정에서 빼기 위한 예열
    rows = []
    for grid in GRIDS:
        c = _with_grid(cfg, grid)
        runs = [solve_point(c) for _ in range(repeats)]     # 0D 초기값에서 출발하는 가장 느린 경우
        t_point = statistics.median(s.timing["total"] for s in runs)
        sol = runs[-1]
        t0 = time.perf_counter()
        jc = control_jacobian(c)                            # 기준점 포함 7회 수렴
        t_jac = time.perf_counter() - t0
        y = sol.metrics.as_vector()
        rows.append(dict(
            Nr=grid[0], Nz=grid[1] + grid[2], em_unknowns=grid[0] * (grid[1] + grid[2]),
            t_point_s=t_point, t_jacobian_s=t_jac, outer_iters=sol.timing["outer_iters"],
            em_fraction=sol.timing["em"] / sol.timing["total"],
            err_n_bar=abs(y[0] / y_ref[0] - 1), err_rho=abs(y[1] / y_ref[1] - 1),
            err_J=float(np.max(np.abs(jc.J_norm - ref.J_norm))),
            margin_point=BUDGET_POINT_S / t_point, margin_jacobian=BUDGET_JACOBIAN_S / t_jac))
    ok = [r for r in rows if max(r["err_n_bar"], r["err_rho"]) < MAX_GRID_ERROR
          and min(r["margin_point"], r["margin_jacobian"]) >= MIN_MARGIN]
    # 오차와 마진 조건을 모두 만족하는 격자 가운데 가장 빠른(성긴) 것을 추천한다
    return dict(rows=rows, recommended=ok[0] if ok else None,
                reference=dict(grid=REFERENCE_GRID, t_jacobian_s=ref.seconds))
