"""모델 자체 검산. 식을 제대로 풀었는지를 해석해·항등식과 대조한다.

  ① 포인팅 검산   : 코일 단자에서 본 저항 Re(Z) − R_coil 과 플라즈마 안 흡수 적분 R_pl 이 같은가
  ② 상반성        : Z_io = Z_oi 인가 (같으면 교차 저항의 위상 ψ_0 는 0 또는 π)
  ③ 보존          : 수렴해에서 입자 수지·에너지 수지가 닫히는가
  ④ T_e 균일 극한 : 열전도도를 아주 크게 하면 밀도 분포가 해석해 J_0(κr) 가 되는가
                    (D_a κ J_1(κR) = u_B J_0(κR), 발표 덱 5쪽 문제 3 의 식)
  ⑤ 같은 극한에서 ρ 가 k 와 무관한가 (T_e 가 균일하면 분포 모양이 고정된다)

  ⑥ 구동부        : 전원별 전력의 합이 포트 전력과 같은가
  ⑦ 역문제        : φ = 180° 처럼 ρ(k) 가 단조가 아닌 조건에서도 목표를 찾는가, 닿을 수 없는 목표를 실패로 판정하는가

수치 수렴을 확인하는 것이며, 국소 Maxwellian·유체 수송 가정이 맞는지를 검증하는 것은 아니다.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq
from scipy.special import j0, j1

from . import inverse
from . import physics as ph
from .config import Config
from .coupled import solve_point
from .em_field import port_drive


def _rho_bessel(Te: float, cfg: Config) -> float:
    """T_e 가 균일할 때의 해석 밀도비. n ∝ J_0(κ r), ∫J_0(κr) r dr = r J_1(κr)/κ."""
    g = cfg.geom
    Da, uB = ph.ion_mobility(cfg) * Te, ph.bohm_speed(Te)
    kap = brentq(lambda q: Da * q * j1(q * g.R) - uB * j0(q * g.R), 1e-3, 2.404 / g.R)
    integ = lambda r: r * j1(kap * r) / kap
    n_c = 2 * integ(g.r_c) / g.r_c**2
    n_edge = 2 * (integ(g.r_2) - integ(g.r_1)) / (g.r_2**2 - g.r_1**2)
    return n_c / n_edge


def run_checks(cfg: Config) -> list:
    """검산 항목별 (이름, 값, 허용치, 통과 여부) 목록을 돌려준다."""
    out = []
    sol = solve_point(cfg)
    Z, R = sol.unit.Z_port, sol.unit.R_pl
    R_coil = np.diag([cfg.op.R_coil_in, cfg.op.R_coil_out])
    poynting = np.max(np.abs(Z.real - R_coil - R.real)) / np.max(np.abs(R.real))
    out.append(("① 포인팅 검산: |Re Z − R_coil − R_pl| / R_pl", poynting, 1e-8))
    out.append(("② 상반성: |Z_io − Z_oi| / |Z_io|", abs(Z[0, 1] - Z[1, 0]) / abs(Z[0, 1]), 1e-8))
    out.append(("② 교차 저항의 허수부 / 실수부 (ψ_0 = 0)", abs(R[0, 1].imag / R[0, 1].real), 1e-8))
    out.append(("③ 입자 수지 상대 오차", abs(sol.balance["particle_error"]), 1e-8))
    out.append(("③ 에너지 수지 상대 오차", abs(sol.balance["energy_error"]), 1e-6))
    # T_e 균일 극한: 열전도도 10^5 배, 양극성 장의 일도 T_e 가 균일하면 식에서 모양에 영향을 주지 않는다
    lim = cfg.with_num(kappa_scale=1e5)
    rhos = []
    for k in (0.5, 1.0, 2.0):
        s = solve_point(lim.with_op(k=k))
        rhos.append(s.metrics.rho)
        if k == 1.0:
            Te = float(np.mean(s.state.Te))
            out.append(("④ T_e 균일 극한: T_e 의 반경 변동 (max − min)/평균", float(np.ptp(s.state.Te)) / Te, 1e-3))
            out.append(("④ ρ 수치해 / 해석해(J_0) − 1", abs(s.metrics.rho / _rho_bessel(Te, lim) - 1), 5e-3))
    out.append(("⑤ T_e 균일 극한에서 k = 0.5, 1, 2 의 ρ 변동", float(np.ptp(rhos)) / float(np.mean(rhos)), 1e-3))
    # 구동부: 위상차가 있어 전원 사이에 전력이 오가는 조건에서도 합은 포트 전력과 같아야 한다
    s90 = solve_point(cfg.with_op(phi=0.5 * np.pi))
    d = port_drive(s90.unit, s90.heating, s90.cfg)
    out.append(("⑥ 전원별 전력의 합 / 포트 전력 − 1 (φ = 90°)", abs((d["P_in"] + d["P_out"]) / s90.heating.P_port - 1), 1e-8))
    # 역문제: 찾은 입력을 처음부터 다시 풀어 목표와 대조한다
    goal = (9.72e16, 1.542)                                 # φ = 180°, k = 4 에서 출발하면 빠른 길이 실패하는 목표
    res = inverse.solve_targets(cfg.with_op(P_tot=700.0, k=4.0, phi=np.pi), *goal)
    again = solve_point(res.solution.cfg).metrics
    miss = max(abs(again.n_bar / goal[0] - 1), abs(again.rho / goal[1] - 1)) if res.success else 1.0
    out.append(("⑦ 역문제: 비단조 조건(φ = 180°)의 목표 재현 오차", miss, 1e-3))
    far = inverse.solve_targets(cfg, 5e16, 0.45)            # 10 mTorr, φ = 0 에서는 ρ 0.69 아래로 내려가지 못한다
    out.append(("⑦ 역문제: 닿을 수 없는 목표를 성공으로 잘못 판정 (0 이면 정상)", float(far.success), 0.5))
    return [(name, val, tol, val < tol) for name, val, tol in out]
