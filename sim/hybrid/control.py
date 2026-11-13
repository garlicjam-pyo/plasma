"""제어 가능성 판정: 국소 민감도 행렬 J_ctrl 과 등평균 스캔 (발표 덱 13쪽).

    u = (P_tot, k, φ)  →  [자기일관 계산]  →  y = (n̄_w, ρ)
    [Δn̄_w, Δρ]ᵀ ≈ J_ctrl [ΔP, Δk, Δφ]ᵀ ,   J_ctrl ∈ R^(2×3)

- control_jacobian : 기준 운전점 둘레에서 입력을 하나씩 ± 로 흔들어 수렴해를 다시 구하고
                     중심 차분으로 J_ctrl 을 만든다 (입력 3개 → 수렴 계산 7회).
- 단일 코일(coil_mode 가 single_*)은 입력이 P_tot 하나뿐이라 J_ctrl 이 2×1 이 된다.
- iso_mean_scan    : k 를 바꾸면서 n̄_w 가 목표값을 유지하도록 P_tot 를 맞추고 ρ 를 기록한다.
                     선형 근사가 아니라 실제 비선형 해로 "평균 유지 + 비 변경"을 확인하는 계산.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from .config import Config
from .coupled import Solution, solve_point

INPUT_NAMES = ("P_tot", "k", "phi")


@dataclass
class ControlJacobian:
    base: Solution
    inputs: tuple                   # 실제로 흔든 입력 이름
    J: np.ndarray                   # ∂(n̄_w, ρ)/∂u, 모양 (2, 입력 수). 단위: [m^-3 또는 1] / [W, 1, rad]
    J_norm: np.ndarray              # 무차원화: 행은 y 로 나누고, P_tot·k 열은 그 값을 곱함 (d ln y / d ln u, φ 는 rad 당)
    singular_values: np.ndarray     # J_norm 의 특이값
    shape_gain: dict                # 평균 밀도를 고정했을 때 각 입력의 순수 형상 감도 d ln ρ / (d ln k 또는 dφ)
    steps: dict                     # 사용한 차분 폭
    seconds: float                  # 전체 계산 시간
    points: dict = field(default_factory=dict)   # 흔든 운전점들의 (y⁺, y⁻)

    @property
    def rank(self) -> int:
        """독립으로 움직일 수 있는 출력 방향의 수 (특이값이 최대값의 1e-3 배보다 큰 것)."""
        s = self.singular_values
        return int(np.sum(s > 1e-3 * s[0]))

    @property
    def condition(self) -> float:
        s = self.singular_values
        return float(s[0] / s[-1]) if s.size == 2 and s[-1] > 0 else float("inf")


def control_jacobian(cfg: Config, base: Solution | None = None,
                     rel_P: float = 0.02, d_k: float = 0.02, d_phi: float = np.radians(2.0)) -> ControlJacobian:
    """중심 차분으로 J_ctrl 을 구한다. 흔든 점은 기준 해에서 출발해 빨리 수렴시킨다."""
    t0 = time.perf_counter()
    base = base or solve_point(cfg)
    op = cfg.op
    steps = {"P_tot": rel_P * op.P_tot, "k": d_k, "phi": d_phi}
    inputs = INPUT_NAMES if op.coil_mode == "dual" else ("P_tot",)
    cols, points = [], {}
    for name in inputs:
        h = steps[name]
        y_pm = []
        for sign in (+1, -1):
            sol = solve_point(cfg.with_op(**{name: getattr(op, name) + sign * h}), guess=base.state)
            y_pm.append(sol.metrics.as_vector())
        points[name] = y_pm
        cols.append((y_pm[0] - y_pm[1]) / (2 * h))
    J = np.array(cols).T
    y0 = base.metrics.as_vector()
    u_scale = np.array([{"P_tot": op.P_tot, "k": op.k if op.k > 0 else 1.0, "phi": 1.0}[n] for n in inputs])
    J_norm = J * u_scale[None, :] / y0[:, None]
    # 덱 13쪽 예시 4단계: Δρ = [∂ρ/∂x − (∂ρ/∂P)(∂n̄/∂x)/(∂n̄/∂P)] Δx  (x = k 또는 φ)
    gain = {}
    for j, name in enumerate(inputs[1:], start=1):
        gain[name] = float(J_norm[1, j] - J_norm[1, 0] * J_norm[0, j] / J_norm[0, 0])
    sv = np.linalg.svd(J_norm, compute_uv=False)
    return ControlJacobian(base, inputs, J, J_norm, sv, gain, steps, time.perf_counter() - t0, points)


def solve_for_mean(cfg: Config, target: float, guess: Solution | None = None,
                   tol: float = 1e-6, max_iter: int = 12) -> Solution:
    """n̄_w 가 target 이 되도록 P_tot 를 조정한다 (할선법, 보통 3–4회 수렴 계산).

    cfg 의 P_tot 가 첫 추정값이다. guess 는 가까운 운전점의 해(출발 상태로 재사용)."""
    P0 = cfg.op.P_tot
    s0 = solve_point(cfg, guess=guess.state if guess else None)
    if abs(s0.metrics.n_bar / target - 1.0) < tol:
        return s0
    P1 = P0 * target / s0.metrics.n_bar                     # 0D 에서 n ∝ P 이므로 첫 보정은 비례식
    for _ in range(max_iter):
        s1 = solve_point(cfg.with_op(P_tot=P1), guess=s0.state)
        if abs(s1.metrics.n_bar / target - 1.0) < tol:
            break
        slope = (s1.metrics.n_bar - s0.metrics.n_bar) / (P1 - P0)
        P0, s0 = P1, s1
        P1 = P1 - (s1.metrics.n_bar - target) / slope
    return s1


def iso_mean_scan(cfg: Config, k_values, phi: float, target: float | None = None) -> dict:
    """위상 φ 를 고정하고 k 를 훑으면서 평균 밀도 n̄_w 를 target 으로 유지한다.

    반환: k, P_tot, n_bar, rho, n_c, n_edge, I0 배열과 각 점의 해(solutions).
    target 을 주지 않으면 cfg 의 운전점에서 얻은 n̄_w 를 쓴다.
    """
    sol = solve_point(cfg)                                   # 기준 운전점 (목표 평균 밀도의 출처)
    target = target or sol.metrics.n_bar
    out = {key: [] for key in ("k", "P_tot", "n_bar", "rho", "n_c", "n_edge", "I0")}
    solutions = []
    for kv in k_values:
        sol = solve_for_mean(cfg.with_op(k=float(kv), phi=phi, P_tot=sol.cfg.op.P_tot), target, guess=sol)
        m = sol.metrics
        for key, val in zip(out, (kv, sol.cfg.op.P_tot, m.n_bar, m.rho, m.n_c, m.n_edge, sol.heating.I0)):
            out[key].append(val)
        solutions.append(sol)
    return {**{k_: np.array(v) for k_, v in out.items()}, "phi": phi, "target": target, "solutions": solutions}


def response_map(cfg: Config, k_values, phi_values) -> dict:
    """P_tot 를 고정하고 (k, φ) 평면을 훑어 n̄_w 와 ρ 지도를 만든다. 모양 (len(phi), len(k))."""
    n_bar = np.zeros((len(phi_values), len(k_values))); rho = np.zeros_like(n_bar)
    row_start = None
    for i, ph_ in enumerate(phi_values):
        sol = row_start
        for j, kv in enumerate(k_values):
            sol = solve_point(cfg.with_op(k=float(kv), phi=float(ph_)), guess=sol.state if sol else None)
            if j == 0:
                row_start = sol                              # 다음 줄의 첫 점은 이 해에서 출발
            n_bar[i, j], rho[i, j] = sol.metrics.n_bar, sol.metrics.rho
    return dict(k=np.asarray(k_values), phi=np.asarray(phi_values), n_bar=n_bar, rho=rho)
