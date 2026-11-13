"""Ar 플라즈마의 반응 계수와 닫힘 관계식.

- 반응 계수 K_iz, K_ex, K_el: Lieberman & Lichtenberg 표 3.3 의 피팅식 (저장소 기존 코드와 같은 식)
- 봄 속도, 이온 이동도, 복소 전도도 (교재 식 2.26)
- 축 방향 기본 모드 닫힘: 2D 식을 z 로 적분해 r 만의 식으로 줄일 때 필요한 양
- 0D 균형으로 구한 초기값 (교재 식 2.70, 2.73)

모든 함수는 numpy 배열을 그대로 받는다 (셀 단위로 한꺼번에 계산).
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

from .config import E_CHARGE as e, K_BOLTZ, M_ARGON as M, M_ELECTRON as me, Config

EPS_IZ = 15.76      # Ar 이온화 에너지 [V]
EPS_EX = 12.14      # Ar 대표 여기 에너지 [V]
# 벽으로 빠지는 전자–이온 쌍 하나가 가져가는 에너지 계수: ε_e + ε_i = (2 + V_s/T_e + 1/2)·T_e
V_SHEATH = 0.5 * np.log(M / (2 * np.pi * me))    # 쉬스 전압 / T_e (Ar 에서 약 4.68)
WALL_COEF = 2.0 + V_SHEATH + 0.5                 # 약 7.2 (교재 식 2.65 의 ε_e + ε_i)


# ------------------------------------------------------------------ 반응 계수 [m^3/s]
def K_iz(Te):
    """이온화 속도 계수. T_e 에 지수적으로 민감하다."""
    return 2.34e-14 * Te**0.59 * np.exp(-17.44 / Te)


def K_ex(Te):
    """여기 속도 계수."""
    return 2.48e-14 * Te**0.33 * np.exp(-12.78 / Te)


def K_el(Te):
    """탄성(운동량 전달) 충돌 속도 계수."""
    lt = np.log(Te)
    return 2.336e-14 * Te**1.609 * np.exp(0.0618 * lt**2 - 0.1171 * lt**3)


def bohm_speed(Te):
    """봄 속도 u_B = sqrt(e T_e / M) [m/s]."""
    return np.sqrt(e * Te / M)


def collision_loss_rate(Te, n_gas):
    """전자 하나가 충돌로 잃는 에너지율 [V/s] = n_g Σ K_j ε_j (이온화 + 여기 + 탄성)."""
    return n_gas * (K_iz(Te) * EPS_IZ + K_ex(Te) * EPS_EX + K_el(Te) * 3 * me / M * Te)


# ------------------------------------------------------------------ 수송 계수
def ion_neutral_freq(cfg: Config) -> float:
    """이온–중성 충돌 주파수 ν_in = v̄_i / λ_i [1/s] (λ_i = 1/(330 p[Torr]) cm)."""
    lam_i = 1.0 / (330.0 * cfg.op.p_mtorr * 1e-3) * 1e-2
    v_i = np.sqrt(8 * K_BOLTZ * cfg.op.T_gas / (np.pi * M))
    return v_i / lam_i


def ion_mobility(cfg: Config) -> float:
    """이온 이동도 μ_i = e / (M ν_in) [m^2/(V s)]. 양극성 확산 계수는 D_a = μ_i T_e."""
    return e / (M * ion_neutral_freq(cfg))


def conductivity(ne, Te, cfg: Config):
    """복소 전도도 σ_p = n_e e^2 / (m_e (ν_m + jω)) [S/m] (교재 식 2.26)."""
    nu_m = cfg.op.n_gas * K_el(Te)
    return ne * e**2 / (me * (nu_m + 1j * cfg.op.omega))


def thermal_conductivity(ne, Te, cfg: Config):
    """전자 열전도도 κ_e = (5/2) n_e e^2 T_e / (m_e ν_m) [W/(m V)]."""
    nu_m = cfg.op.n_gas * K_el(Te)
    return 2.5 * ne * e**2 * Te / (me * nu_m)


# ------------------------------------------------------------------ 축 방향 기본 모드 닫힘
def axial_mode(Te, cfg: Config):
    """z 방향 분포를 n(r, z) = n0(r)·cos(k_z (z − L/2)) 로 두었을 때의 (x, ν_L, ḡ).

    x   = k_z L / 2            : 모드의 위상각 (0 < x < π/2)
    ν_L = 축 방향 벽 손실 주파수 [1/s] (위·아래 벽으로 빠지는 입자 수 ÷ 그 반경의 입자 수)
    ḡ   = sin(x)/x             : z 평균 밀도 ÷ 중간 높이 밀도

    robin    : 유체 식의 Bohm 경계 −D_a ∂n/∂z = n u_B → x·tan(x) = u_B L / (2 D_a), ν_L = D_a k_z²
    h_factor : 교재 h_L 로 벽 밀도를 정함 → cos(x) = h_L, ν_L = 2 h_L u_B / (ḡ L)
    """
    L = cfg.geom.L
    uB = bohm_speed(Te)
    if cfg.num.axial_closure == "h_factor":
        lam_i = 1.0 / (330.0 * cfg.op.p_mtorr * 1e-3) * 1e-2
        hL = 0.86 / np.sqrt(3.0 + L / (2 * lam_i))
        x = np.arccos(hL) * np.ones_like(Te)
        gbar = np.sin(x) / x
        return x, 2 * hL * uB / (gbar * L), gbar
    Da = ion_mobility(cfg) * Te
    biot = uB * L / (2 * Da)
    # x·tan(x) = Bi 를 Newton 법으로 푼다. 초기값은 작은 Bi 와 큰 Bi 양쪽 극한을 잇는 식.
    x = 0.5 * np.pi * np.sqrt(biot / (biot + 0.25 * np.pi**2))
    for _ in range(8):
        f = x * np.tan(x) - biot
        df = np.tan(x) + x / np.cos(x) ** 2
        x = np.clip(x - f / df, 1e-6, 0.5 * np.pi - 1e-6)
    return x, Da * (2 * x / L) ** 2, np.sin(x) / x


# ------------------------------------------------------------------ 0D 초기값
def zero_d_initial(cfg: Config, efficiency: float = 0.75):
    """0D 입자·전력 균형으로 (T_e0, n_*) 를 구한다. 반복의 출발점으로만 쓴다."""
    g, op = cfg.geom, cfg.op
    lam_i = 1.0 / (330.0 * op.p_mtorr * 1e-3) * 1e-2
    hL = 0.86 / np.sqrt(3.0 + g.L / (2 * lam_i))
    hR = 0.80 / np.sqrt(4.0 + g.R / lam_i)
    A_eff = 2 * np.pi * g.R**2 * hL + 2 * np.pi * g.R * g.L * hR      # 유효 손실 면적
    d_eff = np.pi * g.R**2 * g.L / A_eff                              # 유효 플라즈마 크기
    Te0 = brentq(lambda T: K_iz(T) / bohm_speed(T) - 1.0 / (op.n_gas * d_eff), 0.5, 15.0)
    eps_T = collision_loss_rate(Te0, op.n_gas) / (op.n_gas * K_iz(Te0)) + WALL_COEF * Te0
    n_star = efficiency * op.P_tot / (e * bohm_speed(Te0) * eps_T * A_eff)
    return Te0, n_star
