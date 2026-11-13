"""정적 모델의 J_ctrl 을 바깥 제어 루프에 넣었을 때의 위상 여유 어림.

이 저장소의 플라즈마 모델은 정상상태만 푼다. 플라즈마 응답(0.1 ms 대)이 센서·정합기보다 훨씬 빨라서
루프 안에서 플라즈마는 정적 이득 J 로 보고, 동특성은 적분 제어기·측정 지연·구동기 지연이 정한다
(docs/조정절차.md 의 바깥 루프와 같은 구조).

    제어기 : du/dt = ω_c · K · e ,  K = J_nom 의 (의사)역행렬,  e = 목표 − 측정 (ln n̄_w, ln ρ)
    개루프 : L(s) = (ω_c / s) · e^(−s T_d) / (1 + s τ_a) · M ,   M = J_true · K

M 의 고유값 λ 하나하나가 독립된 루프처럼 움직인다.
  |λ|   : 실제 이득 ÷ 제어기가 믿는 이득 → 교차 주파수가 |λ| 배가 된다
  arg λ : 방향 오차가 만드는 위상 → 위상 여유에서 그대로 빠진다
  Re λ < 0 이면 적분 제어가 반대 방향으로 밀어 불안정하다
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

OMEGA_C = 0.2       # 설계 교차 주파수 [rad/s] (docs/조정절차.md)
T_DELAY = (1.0, 2.0)  # 측정 지연 T_d 후보 [s] (FHP 갱신과 평균)
TAU_ACT = 0.3       # 구동기(전원·정합기) 1차 지연 시상수 [s] (0.1–1 s 추정값의 중간)


def controller_gain(J_nom: np.ndarray) -> np.ndarray:
    """J_nom (2×입력 수) 의 역행렬. 입력이 3개면 의사역행렬(최소 노름 해)."""
    return np.linalg.pinv(J_nom)


def margins(lam: complex, T_d: float, omega_c: float = OMEGA_C, tau: float = TAU_ACT) -> dict:
    """고유값 λ 인 루프 하나의 교차 주파수 [rad/s], 위상 여유 [deg], 이득 여유 [배]."""
    if lam.real <= 0:
        return dict(omega_x=np.nan, pm=-np.inf, gm=0.0)
    mag = lambda w: abs(lam) * omega_c / (w * np.hypot(1.0, w * tau))
    lag = lambda w: 0.5 * np.pi + w * T_d + np.arctan(w * tau) + abs(np.angle(lam))   # 위상 지연 [rad]
    w_x = brentq(lambda w: mag(w) - 1.0, 1e-6, 1e3)                 # 이득이 1 이 되는 주파수
    w_180 = brentq(lambda w: lag(w) - np.pi, 1e-6, 1e3)             # 위상이 −180° 가 되는 주파수
    return dict(omega_x=w_x, pm=float(np.degrees(np.pi - lag(w_x))), gm=float(1.0 / mag(w_180)))


def loop_report(J_true: np.ndarray, K: np.ndarray) -> dict:
    """실제 플랜트 J_true 와 제어기 K 조합의 고유값과, 가장 나쁜 고유 루프의 여유."""
    lam = np.linalg.eigvals(J_true @ K)
    out = dict(eigenvalues=lam)
    for T_d in T_DELAY:
        ms = [margins(complex(l), T_d) for l in lam]
        worst = min(ms, key=lambda m: m["pm"])
        out[f"pm_Td{T_d:g}"] = worst["pm"]; out[f"gm_Td{T_d:g}"] = worst["gm"]
        out[f"omega_x_Td{T_d:g}"] = max(m["omega_x"] for m in ms)
    out["settle_s"] = float(4.0 / (np.min(np.abs(lam)) * OMEGA_C))   # 가장 느린 고유 루프의 설정 시간 ≈ 4/(|λ| ω_c)
    return out


def scenarios(cfg) -> list:
    """제어기가 기준점의 1D 모델 J 를 믿을 때, 실제 플랜트가 달라지는 경우들 (이름, 설정)."""
    return [
        ("기준 (모델 = 실제)", cfg), ("2D 수송", cfg.with_num(transport="full_2d")),
        ("운전점 이동 k = 0.5", cfg.with_op(k=0.5)), ("운전점 이동 k = 2", cfg.with_op(k=2.0)),
        ("운전점 이동 100 W", cfg.with_op(P_tot=100.0)), ("운전점 이동 600 W", cfg.with_op(P_tot=600.0)),
        ("위상을 180° 로 바꿈", cfg.with_op(phi=np.pi)),
        ("압력 5 mTorr", cfg.with_op(p_mtorr=5.0)), ("압력 20 mTorr", cfg.with_op(p_mtorr=20.0)),
        ("열전도 0.3배", cfg.with_num(kappa_scale=0.3)), ("열전도 3배", cfg.with_num(kappa_scale=3.0)),
        ("열전도 10배", cfg.with_num(kappa_scale=10.0)), ("축 닫힘 h_L", cfg.with_num(axial_closure="h_factor")),
    ]


def margin_study(cfg, columns=(0, 1)) -> list:
    """시나리오별 고유값과 여유. columns 는 쓰는 입력 열 (0: P_tot, 1: k, 2: φ)."""
    from .control import control_jacobian
    K = controller_gain(control_jacobian(cfg).J_norm[:, columns])
    rows = []
    for name, c in scenarios(cfg):
        rep = loop_report(control_jacobian(c).J_norm[:, columns], K)
        lam = np.sort_complex(rep.pop("eigenvalues"))
        rows.append(dict(scenario=name, lam_min=float(np.min(np.abs(lam))), lam_max=float(np.max(np.abs(lam))),
                         lam_phase_deg=float(np.max(np.abs(np.degrees(np.angle(lam))))), **rep))
    return rows

