"""독립 제어의 역문제: 목표 (n̄_w, ρ) 를 주면 그것을 만드는 입력 (P_tot, k) 를 찾는다.

위상 φ 는 고정값으로 두고(위상별로 J 가 크게 달라지므로) 두 입력으로 두 출력을 맞춘다.
풀이는 두 단계다.

  1) 빠른 길 (바깥 제어 루프와 같은 꼴: 오차 e = 목표 − 현재, 보정 Δu = J⁻¹ e)
       변수 v = (ln P_tot, ln k),  출력 y = (ln n̄_w, ln ρ)
       출발점에서 J 를 차분으로 한 번 구하고, 걸음마다 Broyden 식으로 고친다 (걸음당 수렴 계산 1회).
  2) 확인 길: 빠른 길이 목표에 닿지 못하면 k 를 탐색 범위 전체에서 훑는다.
       k 마다 전력으로 평균 밀도를 맞춘 뒤 ρ(k) 곡선에서 목표를 사이에 둔 구간을 찾아 좁힌다.
       φ = 180° 에서는 ρ(k) 가 단조가 아니어서(봉우리와 골이 있다) 빠른 길이 엉뚱한 쪽 끝으로 갈 수 있다.
       확인 길은 그런 경우에도 해를 놓치지 않고, 해가 없으면 낼 수 있는 ρ 범위를 알려 준다.

단일 코일은 입력이 P_tot 하나뿐이라 n̄_w 만 맞추고 ρ 는 얻어지는 값을 보고한다.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from .config import Config
from .coupled import Solution, solve_point

K_RANGE = (0.05, 5.0)         # 전류비 k 탐색 범위
P_RANGE = (30.0, 1500.0)      # 총 전력 탐색 범위 [W]
MAX_STEP = 0.6                # 빠른 길의 한 걸음에서 ln P, ln k 가 바뀔 수 있는 최대 크기
SCAN_POINTS = 12              # 확인 길에서 훑는 k 의 개수 (로그 간격)


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


def _match_mean(run, cfg: Config, n_target: float, state, P_range, tol: float = 1e-5, max_iter: int = 14):
    """전력만 바꿔 n̄_w 를 목표에 맞춘다 (ln P 에 대한 할선법, 전력 범위 안에서만).

    반환: (해, 맞췄는가). 전력 범위 끝에 걸리거나 플라즈마가 유지되지 않으면 False."""
    lo, hi = np.log(P_range)
    x0 = float(np.clip(np.log(cfg.op.P_tot), lo, hi))
    s0 = run(cfg.with_op(P_tot=float(np.exp(x0))), state)
    if not s0.converged:                                   # 낮은 전력에서 방전이 꺼진 경우: 범위 한가운데에서 다시
        x0 = 0.5 * (lo + hi)
        s0 = run(cfg.with_op(P_tot=float(np.exp(x0))), None)
        if not s0.converged:
            return s0, False
    f0 = float(np.log(s0.metrics.n_bar / n_target))
    x1 = float(np.clip(x0 - f0, lo, hi))                   # 0D 에서 n ∝ P 이므로 첫 보정은 비례식
    for _ in range(max_iter):
        if abs(f0) < tol:
            return s0, True
        if x1 == x0:                                       # 범위 끝에서 더 갈 수 없음
            return s0, False
        s1 = run(cfg.with_op(P_tot=float(np.exp(x1))), s0.state)
        if not s1.converged:
            return s0, False
        f1 = float(np.log(s1.metrics.n_bar / n_target))
        slope = (f1 - f0) / (x1 - x0)
        if not np.isfinite(slope) or slope < 0.05:         # 기울기가 이상하면 비례식으로 되돌린다
            slope = 1.0
        x0, s0, f0 = x1, s1, f1
        x1 = float(np.clip(x0 - f0 / slope, lo, hi))
    return s0, abs(f0) < tol


def _scan_k(run, cfg: Config, n_target: float, rho_target: float, start: Solution, tol: float, P_range, k_range):
    """확인 길: k 전 범위에서 평균 밀도를 맞춘 ρ(k) 를 구하고, 목표를 사이에 둔 구간을 좁힌다.

    반환: (해 또는 None, 평균을 맞출 수 있었던 점들의 [(ln k, 오차 g, 해)])."""
    pts, sol = [], start
    for lk in np.linspace(*np.log(k_range), SCAN_POINTS):   # 훑을 때는 평균을 0.1 % 까지만 맞춘다 (구간 찾기에는 충분)
        s, ok = _match_mean(run, sol.cfg.with_op(k=float(np.exp(lk))), n_target, sol.state if sol.converged else None,
                            P_range, tol=1e-3)
        if ok:
            pts.append((float(lk), float(np.log(s.metrics.rho / rho_target)), s))
            sol = s
    # 이웃한 두 점에서 오차의 부호가 바뀌는 구간들. 여러 개면 지금의 k 에 가장 가까운 것을 고른다.
    brackets = [(a, b) for a, b in zip(pts[:-1], pts[1:]) if a[1] * b[1] <= 0]
    if not brackets:
        return None, pts
    lk_now = np.log(max(start.cfg.op.k, k_range[0]))
    a, b = min(brackets, key=lambda ab: abs(0.5 * (ab[0][0] + ab[1][0]) - lk_now))
    for _ in range(30):                                    # 가위치법(Illinois): 구간을 유지하면서 좁힌다
        best = min((a, b), key=lambda p: abs(p[1]))
        if abs(best[1]) < tol:
            return best[2], pts
        lk = (a[0] * b[1] - b[0] * a[1]) / (b[1] - a[1]) if b[1] != a[1] else 0.5 * (a[0] + b[0])
        s, ok = _match_mean(run, best[2].cfg.with_op(k=float(np.exp(lk))), n_target, best[2].state, P_range)
        if not ok:
            break
        c = (float(lk), float(np.log(s.metrics.rho / rho_target)), s)
        if c[1] * b[1] < 0:
            a = b
        else:
            a = (a[0], 0.5 * a[1], a[2])                   # 같은 쪽 끝이 계속 남으면 그 값을 반으로 (수렴 가속)
        b = c
    best = min((a, b), key=lambda p: abs(p[1]))
    return (best[2] if abs(best[1]) < tol else None), pts


def solve_targets(cfg: Config, n_target: float, rho_target: float, start: Solution | None = None,
                  tol: float = 1e-4, max_iter: int = 14, P_range=P_RANGE, k_range=K_RANGE) -> ControlResult:
    """cfg 의 (P_tot, k) 에서 출발해 목표 (n̄_w, ρ) 를 만드는 (P_tot, k) 를 찾는다. φ·압력·코일 구성은 cfg 그대로."""
    t0 = time.perf_counter()
    traj: list = []
    count = 0

    def run(c: Config, state):
        nonlocal count
        count += 1
        return solve_point(c, guess=state)

    def finish(success: bool, msg: str, sol: Solution, record: bool = True) -> ControlResult:
        if record:
            _record(traj, sol)
        return ControlResult(success, msg, sol, traj, count, time.perf_counter() - t0)

    guess = start.state if start is not None else None
    if cfg.op.coil_mode != "dual":                      # 단일 코일: 전력 하나로 평균 밀도만 맞춘다
        first = run(cfg, guess)
        _record(traj, first)
        sol, ok = _match_mean(run, cfg, n_target, first.state if first.converged else None, P_range)
        head = "단일 코일은 입력이 전력 하나뿐이라 밀도비를 따로 맞출 수 없습니다. "
        tail = (f"평균 밀도만 맞췄고, 이때 밀도비는 {sol.metrics.rho:.3f} 입니다." if ok else
                f"전력 범위({P_range[0]:.0f}–{P_range[1]:.0f} W) 안에서는 목표 평균 밀도에도 닿지 못했습니다.")
        return finish(False, head + tail, sol)

    # ---------------------------------------------------------------- 1) 빠른 길
    lo = np.log([P_range[0], k_range[0]]); hi = np.log([P_range[1], k_range[1]])
    target = np.log([n_target, rho_target])
    make = lambda v: cfg.with_op(P_tot=float(np.exp(v[0])), k=float(np.exp(v[1])))
    v = np.clip(np.log([cfg.op.P_tot, max(cfg.op.k, k_range[0])]), lo, hi)
    sol = run(make(v), guess)
    last_good = sol
    if sol.converged:
        y = _outputs(sol)
        _record(traj, sol)
        J = np.zeros((2, 2))
        for j in range(2):                              # 출발점의 민감도 행렬 (전진 차분)
            vp = v.copy(); vp[j] += 0.03 if vp[j] + 0.03 <= hi[j] else -0.03
            J[:, j] = (_outputs(run(make(vp), sol.state)) - y) / (vp[j] - v[j])
        for _ in range(max_iter):
            err = target - y
            if np.max(np.abs(err)) < tol:
                return finish(True, f"목표에 도달했습니다 (수렴 계산 {count}회).", sol, record=False)
            if not np.all(np.isfinite(J)):
                break
            dv = np.linalg.lstsq(J, err, rcond=None)[0]
            dv *= min(1.0, MAX_STEP / max(np.max(np.abs(dv)), 1e-12))
            if np.any(((v <= lo + 1e-9) & (dv < 0)) | ((v >= hi - 1e-9) & (dv > 0))):
                break                                   # 범위 끝에 있는 입력을 더 밀어야 함 → 확인 길에서 판정
            v_new = np.clip(v + dv, lo, hi)
            s = v_new - v
            sol_new = run(make(v_new), sol.state)
            if not sol_new.converged:                   # 방전이 유지되지 않는 영역으로 들어감 → 확인 길로
                break
            y_new = _outputs(sol_new)
            J += np.outer((y_new - y) - J @ s, s) / (s @ s)   # Broyden 갱신: 이번 걸음에서 본 응답을 J 에 반영
            v, y, sol = v_new, y_new, sol_new
            last_good = sol
            _record(traj, sol)
        if np.max(np.abs(target - y)) < tol:
            return finish(True, f"목표에 도달했습니다 (수렴 계산 {count}회).", sol, record=False)

    # ---------------------------------------------------------------- 2) 확인 길
    found, pts = _scan_k(run, cfg, n_target, rho_target, last_good, tol, P_range, k_range)
    if found is not None:
        return finish(True, f"목표에 도달했습니다 (전류비 전 범위를 훑어 찾음, 수렴 계산 {count}회).", found)
    span = f"전류비 {k_range[0]:g}–{k_range[1]:g}, 전력 {P_range[0]:.0f}–{P_range[1]:.0f} W"
    if not pts:                                         # 어떤 k 에서도 평균 밀도를 맞추지 못함
        sol, _ = _match_mean(run, last_good.cfg, n_target, last_good.state if last_good.converged else None, P_range)
        msg = (f"탐색 범위({span}) 안에서는 목표 평균 밀도에 닿지 못했습니다. "
               f"가장 가까운 결과는 평균 밀도 {sol.metrics.n_bar * 1e-16:.2f}×10¹⁶ m⁻³, 밀도비 {sol.metrics.rho:.3f} 입니다.")
        return finish(False, msg, sol)
    rhos = [p[2].metrics.rho for p in pts]
    near = min(pts, key=lambda p: abs(p[1]))[2]         # 목표에 가장 가까운 밀도비를 내는 점
    sol, _ = _match_mean(run, near.cfg, n_target, near.state, P_range)   # 그 점의 평균 밀도를 정밀하게 다시 맞춘다
    msg = (f"이 위상·압력에서 평균 밀도를 목표로 유지하며 낼 수 있는 밀도비는 약 {min(rhos):.3f}–{max(rhos):.3f} 입니다 ({span}). "
           f"목표 {rho_target:.3f} 은 이 범위 밖이라, 가장 가까운 {sol.metrics.rho:.3f} 로 맞췄습니다.")
    return finish(False, msg, sol)


def reachable_band(cfg: Config, P_range=P_RANGE, k_range=K_RANGE, n_power: int = 5, n_k: int = 10) -> dict:
    """(n̄_w, ρ) 평면에서 도달할 수 있는 영역의 위·아래 경계를 어림한다.

    전력을 몇 개 고르고 각 전력에서 k 를 훑어, ρ 가 최대·최소인 점을 경계로 삼는다.
    방전이 유지되지 않는(수렴하지 않는) 점은 뺀다."""
    upper, lower = [], []
    sol = None
    for P in np.geomspace(2 * P_range[0], P_range[1], n_power):
        pts = []
        for kv in np.geomspace(*k_range, n_k):
            s = solve_point(cfg.with_op(P_tot=float(P), k=float(kv)), guess=sol.state if sol else None)
            if s.converged:
                pts.append((s.metrics.n_bar, s.metrics.rho))
                sol = s
            else:
                sol = None
        if pts:
            upper.append(max(pts, key=lambda p: p[1])); lower.append(min(pts, key=lambda p: p[1]))
    return dict(upper=upper, lower=lower)
