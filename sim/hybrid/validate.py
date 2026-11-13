"""반경 1D 수송 모델을 (r, z) 2D 수송 모델과 비교해 축소 오차를 잰다.

두 모델은 전자기장, 계수, 경계 조건이 모두 같고 수송의 차원만 다르다.
따라서 차이는 1D 모델의 두 가정(z 방향 기본 모드, T_e 의 z 균일)에서만 나온다.

  validation_study : 기준점의 J_ctrl 비교 + 여러 운전점의 n̄_w, ρ 비교 + 계산 시간
"""
from __future__ import annotations

import numpy as np

from .config import Config
from .control import control_jacobian
from .coupled import solve_point

# 비교할 운전점: (이름, 기준 설정에서 바꾸는 운전 조건)
CASES = (
    ("기준 (k=1, φ=0°)", {}),
    ("k=0.5, φ=0°", dict(k=0.5)), ("k=2, φ=0°", dict(k=2.0)),
    ("k=0.5, φ=180°", dict(k=0.5, phi=np.pi)), ("k=2, φ=180°", dict(k=2.0, phi=np.pi)),
    ("P_tot=100 W", dict(P_tot=100.0)), ("P_tot=600 W", dict(P_tot=600.0)),
    ("단일 코일(안쪽)", dict(coil_mode="single_inner")),
    ("5 mTorr", dict(p_mtorr=5.0)), ("20 mTorr", dict(p_mtorr=20.0)), ("50 mTorr", dict(p_mtorr=50.0)),
)


def solve_pair(cfg: Config):
    """같은 운전점을 1D, 2D 수송으로 각각 푼다. 2D 는 1D 해에서 출발한다."""
    s1 = solve_point(cfg.with_num(transport="radial_1d"))
    s2 = solve_point(cfg.with_num(transport="full_2d"), guess=s1.state)
    return s1, s2


def validation_study(cfg: Config) -> dict:
    rows, pairs = [], {}
    for name, change in CASES:
        s1, s2 = solve_pair(cfg.with_op(**change))
        pairs[name] = (s1, s2)
        rows.append(dict(
            case=name, n_bar_1d=s1.metrics.n_bar, n_bar_2d=s2.metrics.n_bar,
            rho_1d=s1.metrics.rho, rho_2d=s2.metrics.rho,
            err_n_bar=s1.metrics.n_bar / s2.metrics.n_bar - 1.0, err_rho=s1.metrics.rho / s2.metrics.rho - 1.0,
            Te_z_spread=float(np.max(np.ptp(s2.state.Te, axis=0))),          # 2D 해에서 T_e 의 z 방향 최대 차 [V]
            t_1d_s=s1.timing["total"], t_2d_s=s2.timing["total"], converged=s1.converged and s2.converged))
    j1 = control_jacobian(cfg.with_num(transport="radial_1d"))
    j2 = control_jacobian(cfg.with_num(transport="full_2d"))
    return dict(rows=rows, pairs=pairs, jac_1d=j1, jac_2d=j2,
                err_J=float(np.max(np.abs(j1.J_norm - j2.J_norm))))
