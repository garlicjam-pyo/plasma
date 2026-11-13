"""독립 제어의 역문제: 목표 (n̄_w, ρ) 를 주면 그것을 만드는 입력 (P_tot, k) 를 찾는다.

위상 φ 는 고정값으로 두고(위상별로 J 가 크게 달라지므로) 두 입력으로 두 출력을 맞춘다.
풀이는 바깥 제어 루프와 같은 꼴이다: 오차 e = 목표 − 현재, 보정 Δu = J⁻¹ e.

    변수 v = (ln P_tot, ln k),  출력 y = (ln n̄_w, ln ρ)
    1) 출발점에서 J 를 차분으로 한 번 구한다 (수렴 계산 2회)
    2) v ← v + J⁻¹ (y* − y), 한 걸음의 크기는 제한
    3) 새 결과로 J 를 Broyden 식으로 고친다 (걸음마다 수렴 계산 1회)

단일 코일은 입력이 P_tot 하나뿐이라 n̄_w 만 맞추고 ρ 는 얻어지는 값을 보고한다.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from .config import Config
from .control import solve_for_mean
from .coupled import Solution, solve_point

K_RANGE = (0.05, 10.0)        # 전류비 k 탐색 범위
P_RANGE = (20.0, 3000.0)      # 총 전력 탐색 범위 [W]
MAX_STEP = 0.6                # 한 걸음에서 ln P, ln k 가 바뀔 수 있는 최대 크기


@dataclass
class ControlResult:
    success: bool                 # 두 목표를 모두 허용 오차 안으로 맞췄는가
    message: str                  # 화면에 보여 줄 결과 설명
    solution: Solution            # 마지막 운전점의 해
    trajectory: list = field(default_factory=list)   # 걸음별 (P_tot, k, n_bar, rho)
    n_solves: int = 0             # 수렴 계산 횟수
    seconds: float = 0.0


def _outputs(sol: Solution) -> np.ndarray:
    return np.log([sol.metrics.n_bar, sol.metrics.rho])


def _record(traj: list, sol: Solution) -> None:
    k, _ = sol.cfg.op.effective_k_phi()
    traj.append(dict(step=len(traj), P_tot=sol.cfg.op.P_tot, k=k, n_bar=sol.metrics.n_bar, rho=sol.metrics.rho))


def solve_targets(cfg: Config, n_target: float, rho_target: float, start: Solution | None = None,
                  tol: float = 1e-4, max_iter: int = 30) -> ControlResult:
    """cfg 의 (P_tot, k) 에서 출발해 목표 (n̄_w, ρ) 를 만드는 (P_tot, k) 를 찾는다. φ·압력·코일 구성은 cfg 그대로."""
    t0 = time.perf_counter()
    traj: list = []
    guess = start.state if start is not None else None
    if cfg.op.coil_mode != "dual":                      # 단일 코일: 전력 하나로 평균 밀도만 맞춘다
        first = solve_point(cfg, guess=guess)
        _record(traj, first)
        sol = solve_for_mean(cfg, n_target, guess=first)
        _record(traj, sol)
        msg = (f"단일 코일은 입력이 전력 하나뿐이라 밀도비를 따로 맞출 수 없습니다. "
               f"평균 밀도만 맞췄고, 이때 밀도비는 {sol.metrics.rho:.3f} 입니다.")
        return ControlResult(False, msg, sol, traj, 0, time.perf_counter() - t0)

    lo = np.log([P_RANGE[0], K_RANGE[0]]); hi = np.log([P_RANGE[1], K_RANGE[1]])
    target = np.log([n_target, rho_target])
    count = 0

    def run(v, state):
        nonlocal count
        count += 1
        return solve_point(cfg.with_op(P_tot=float(np.exp(v[0])), k=float(np.exp(v[1]))), guess=state)

    v = np.clip(np.log([cfg.op.P_tot, max(cfg.op.k, K_RANGE[0])]), lo, hi)
    sol = run(v, guess)
    y = _outputs(sol)
    _record(traj, sol)
    J = np.zeros((2, 2))
    for j in range(2):                                  # 출발점의 민감도 행렬 (전진 차분)
        vp = v.copy(); vp[j] += 0.03 if vp[j] + 0.03 <= hi[j] else -0.03
        J[:, j] = (_outputs(run(vp, sol.state)) - y) / (vp[j] - v[j])
    for _ in range(max_iter):
        err = target - y
        if np.max(np.abs(err)) < tol:
            msg = f"목표에 도달했습니다 (수렴 계산 {count}회)."
            return ControlResult(True, msg, sol, traj, count, time.perf_counter() - t0)
        dv = np.linalg.lstsq(J, err, rcond=None)[0]
        dv *= min(1.0, MAX_STEP / np.max(np.abs(dv)))
        v_new = np.clip(v + dv, lo, hi)
        pinned = ((v <= lo + 1e-9) & (dv < 0)) | ((v >= hi - 1e-9) & (dv > 0))
        if pinned.any():                                # 범위 끝에 있는 입력을 더 밀어야 함 → 도달할 수 없는 목표
            break
        sol_new = run(v_new, sol.state)
        y_new = _outputs(sol_new)
        s = v_new - v
        J += np.outer((y_new - y) - J @ s, s) / (s @ s)  # Broyden 갱신: 이번 걸음에서 본 응답을 J 에 반영
        v, y, sol = v_new, y_new, sol_new
        _record(traj, sol)
    # 두 목표를 함께 맞추지 못한 경우: 지금의 k 에서 평균 밀도만이라도 맞춘 결과를 돌려준다
    sol = solve_for_mean(sol.cfg, n_target, guess=sol)
    _record(traj, sol)
    at_edge = np.isclose(sol.cfg.op.k, K_RANGE).any() or np.isclose(sol.cfg.op.P_tot, P_RANGE).any()
    reason = "입력이 탐색 범위 끝에 닿았습니다" if at_edge else "반복 횟수 안에 수렴하지 못했습니다"
    msg = (f"이 위상에서는 목표 밀도비 {rho_target:.3f} 에 도달하지 못했습니다 ({reason}). "
           f"평균 밀도를 맞춘 상태에서 얻은 밀도비는 {sol.metrics.rho:.3f} 입니다.")
    return ControlResult(False, msg, sol, traj, count, time.perf_counter() - t0)


def reachable_band(cfg: Config, powers=(60.0, 150.0, 350.0, 800.0),
                   k_values=(0.05, 0.3, 0.6, 1.0, 1.6, 2.6, 5.0, 10.0)) -> dict:
    """(n̄_w, ρ) 평면에서 도달할 수 있는 영역의 위·아래 경계를 어림한다.

    전력을 몇 개 고르고 각 전력에서 k 를 훑어, ρ 가 최대·최소인 점을 경계로 삼는다."""
    upper, lower = [], []
    sol = None
    for P in powers:
        pts = []
        for kv in k_values:
            sol = solve_point(cfg.with_op(P_tot=P, k=kv), guess=sol.state if sol else None)
            pts.append((sol.metrics.n_bar, sol.metrics.rho))
        upper.append(max(pts, key=lambda p: p[1])); lower.append(min(pts, key=lambda p: p[1]))
    return dict(upper=upper, lower=lower)
