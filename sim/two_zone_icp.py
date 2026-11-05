"""2-영역(중앙/가장자리) 0D ICP 모델 + 4권선 회로 모델.

로드맵의 M1(회로 모델)과, M2(2D 확산 모델) 이전 단계인 0D 2-영역 모델(M2a)을
하나로 묶은 자기일관 모델이다.

    입력  : 입력 전력 P_in, 압력 p, 수동 안테나 커패시턴스 C
    회로  : 급전 안테나(1) · 수동 공진 안테나(2) · 중앙 플라즈마 루프(3) · 가장자리 플라즈마 루프(4)
            → 영역별 흡수 전력 P_c, P_e, 전력 전달 효율 eta, 급전 전류 I1
    브리지 : 전자 에너지 완화 길이 lambda_eps 로 국소/비국소 가열을 잇는다
    수송  : 영역별 입자·에너지 균형 (h-factor 벽 손실 + 영역 간 플럭스)
            → n_c, n_e, Te_c, Te_e
    출력  : 평균 밀도 n_bar, 밀도비 R = n_c / n_e (00_과제정의.md 표기)

기준 챔버와 안테나 값은 Kim & Chung, Phys. Plasmas 27, 063511 (2020) [KC20] 을 따른다.
값 출처 표기: (문헌) (가정) (보정) (계산) — 03_작업계획.md 6절 규칙.
모든 단위는 SI, 전자 온도는 eV.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.optimize import brentq, least_squares
from scipy.special import ellipe, ellipk

# ---------------------------------------------------------------- 물리 상수 (SI)
E = 1.602176634e-19        # 기본 전하 [C]
ME = 9.1093837015e-31      # 전자 질량 [kg]
KB = 1.380649e-23          # 볼츠만 상수 [J/K]
EPS0 = 8.8541878128e-12    # 진공 유전율 [F/m]
C0 = 2.99792458e8          # 광속 [m/s]
MU0 = 1.25663706212e-6     # 진공 투자율 [H/m]
AMU = 1.66053906660e-27    # 원자 질량 단위 [kg]
TORR = 133.322368          # 1 Torr [Pa]

# ---------------------------------------------------------------- 기체 (Ar)
M_ION = 39.948 * AMU       # Ar 이온 질량 [kg]
T_GAS = 300.0              # 기체·이온 온도 [K] (가정)
TI_EV = KB * T_GAS / E     # 이온 온도 [eV]
SIGMA_IN = 1.0e-18         # 이온-중성 충돌 단면적 [m^2] (문헌: Lieberman, λ_i ≈ 1/(330 p[Torr]) cm)
E_IZ = 15.76               # 이온화 에너지 [eV] (문헌: Lieberman 표 3.3)
E_EX = 12.14               # 여기 에너지 [eV] (문헌: Lieberman 표 3.3)
# 전자 에너지 완화 길이 기준값: 1 mTorr, 15.7 eV 에서 119 cm, ∝ 1/p (문헌: KC20 Fig. 5)
LAMBDA_EPS_1MTORR = 1.19   # [m]


@dataclass(frozen=True)
class Params:
    """챔버·안테나·모델 매개변수. 기본값은 KC20 챔버."""

    # 챔버 (문헌: KC20 2절)
    R: float = 0.19             # 챔버 반지름 [m]
    L: float = 0.10             # 챔버 높이 [m]
    # 영역 경계: 두 안테나 반지름의 중간 (가정) → 중앙 영역 대표 반지름 r_b/√2 ≈ 9.5 cm = 급전 안테나
    r_b: float = 0.135          # [m]
    # 안테나 (문헌: KC20 2절)
    a1: float = 0.095           # 급전 안테나 반지름 [m]
    a2: float = 0.175           # 수동 안테나 반지름 [m]
    wire_r: float = 2.0e-3      # 안테나 도체 반지름 [m] (보정: L2 ≈ 1 μH 측정값에 맞춤)
    R1: float = 0.23            # 급전 측 저항(정합기 포함) [Ω] (문헌: KC20 측정값)
    R2: float = 0.03            # 수동 안테나 저항 [Ω] (문헌: KC20 계산값)
    f: float = 13.56e6          # 구동 주파수 [Hz]
    # 안테나 도체 중심 ~ 플라즈마 표면 거리 [m] (가정: 석영 판 위에 놓인 φ4 mm 관, 민감도 1.5 cm 비교)
    z_gap: float = 0.010
    # 확률적 가열 배수 κ_ν: ν_eff = ν_m + κ_ν·v̄_e/(4δ)
    # (보정: 150 W, 1 mTorr, 비공진에서 측정 I1 = 8.5 A 를 재현하도록 정함 → calibrate_nu_factor)
    nu_factor: float = 10.2
    # 표피층 밀도: 'bulk' = 영역 밀도 n (저압 global 모델의 "균일 벌크 + 벽 근처 급감" 가정과 일치),
    #             'sheath_edge' = h_l·n (KC20 의 R_p 정의, 민감도 비교용)
    skin_density: str = "bulk"
    # 비국소 브리지 거리 = 두 안테나 반지름 차 [m] (가정)
    delta_heat: float = 0.08
    # 비국소 브리지 사용 여부 (False = 완전 국소 가열)
    nonlocal_bridge: bool = True
    # 충돌 에너지 손실 배수 β_E (기본 1 = 맥스웰 분포 그대로). 민감도 분석에서 측정 밀도에
    # 맞춘 "밀도 정합" 변형을 만들 때만 바꾼다 (비맥스웰 EEDF·기체 가열 등을 한데 묶은 보정).
    energy_factor: float = 1.0

    # ---- 유도 기하량
    @property
    def V(self) -> float:
        return np.pi * self.R**2 * self.L

    @property
    def Vc(self) -> float:
        return np.pi * self.r_b**2 * self.L

    @property
    def Ve(self) -> float:
        return np.pi * (self.R**2 - self.r_b**2) * self.L

    @property
    def rc_star(self) -> float:
        """중앙 영역 대표 반지름 (면적 이등분) [m]."""
        return self.r_b / np.sqrt(2.0)

    @property
    def re_star(self) -> float:
        """가장자리 영역 대표 반지름 (면적 이등분) [m]."""
        return np.sqrt((self.R**2 + self.r_b**2) / 2.0)


# ================================================================ 기체·반응 데이터
def n_gas(p_mtorr: float) -> float:
    """중성 기체 밀도 [m^-3]."""
    return p_mtorr * 1e-3 * TORR / (KB * T_GAS)


def lambda_i(p_mtorr: float) -> float:
    """이온-중성 평균 자유 행로 [m]."""
    return 1.0 / (n_gas(p_mtorr) * SIGMA_IN)


def lambda_eps(p_mtorr: float) -> float:
    """15.7 eV 전자의 에너지 완화 길이 [m] (KC20 Fig. 5 기준값, ∝ 1/p)."""
    return LAMBDA_EPS_1MTORR / p_mtorr


def k_iz(Te):
    """Ar 이온화 속도 계수 [m^3/s] (Lieberman 표 3.3, 맥스웰 분포)."""
    return 2.34e-14 * Te**0.59 * np.exp(-17.44 / Te)


def k_ex(Te):
    """Ar 여기 속도 계수 [m^3/s] (Lieberman 표 3.3)."""
    return 2.48e-14 * Te**0.33 * np.exp(-12.78 / Te)


def k_el(Te):
    """Ar 탄성(운동량 전달) 속도 계수 [m^3/s] (Lieberman 표 3.3)."""
    lt = np.log(Te)
    return 2.336e-14 * Te**1.609 * np.exp(0.0618 * lt**2 - 0.1171 * lt**3)


V_SHEATH = np.log(np.sqrt(M_ION / (2 * np.pi * ME)))  # 부유 벽 쉬스 전압 / Te (Ar ≈ 4.68)


def e_c(Te):
    """전자-이온 쌍 하나를 만드는 데 드는 충돌 에너지 손실 [eV]."""
    return E_IZ + E_EX * k_ex(Te) / k_iz(Te) + k_el(Te) / k_iz(Te) * 3 * ME / M_ION * Te


def e_wall(Te):
    """벽으로 잃는 쌍 하나가 가져가는 운동 에너지 [eV]: 전자 2Te + 이온 (Te/2 + V_s)."""
    return 2.0 * Te + 0.5 * Te + V_SHEATH * Te


def u_bohm(Te):
    return np.sqrt(E * Te / M_ION)


def d_ambipolar(p_mtorr: float, Te):
    """양극성 확산 계수 D_a = D_i (1 + Te/Ti) [m^2/s]."""
    v_i = np.sqrt(8 * KB * T_GAS / (np.pi * M_ION))
    d_i = E * TI_EV * lambda_i(p_mtorr) / (M_ION * v_i)
    return d_i * (1 + Te / TI_EV)


# ================================================================ h-factor (Lee & Lieberman 1995; Lieberman 10.2절)
def h_slab(l: float, p_mtorr: float, Te):
    """두께 l 인 평판의 쉬스 경계/중심 밀도비 (저압~고압 보간식)."""
    lam = lambda_i(p_mtorr)
    hp = 0.86 * l * u_bohm(Te) / (np.pi * d_ambipolar(p_mtorr, Te))
    return 0.86 / np.sqrt(3 + l / (2 * lam) + hp**2)


def h_cyl(R: float, p_mtorr: float, Te):
    """반지름 R 인 원통 측벽의 쉬스 경계/중심 밀도비."""
    lam = lambda_i(p_mtorr)
    hp = 0.80 * R * u_bohm(Te) / (2.405 * 0.5191 * d_ambipolar(p_mtorr, Te))
    return 0.80 / np.sqrt(4 + R / lam + hp**2)


# ================================================================ 단일 영역 global 모델 (기준선)
def single_zone(P_abs: float, p_mtorr: float, prm: Params = Params()) -> dict:
    """Lee & Lieberman (1995) 형 단일 영역 모델: 입자 균형 → Te, 에너지 균형 → n0."""
    ng = n_gas(p_mtorr)
    a_ax, a_side = 2 * np.pi * prm.R**2, 2 * np.pi * prm.R * prm.L

    def a_eff(Te):
        return h_slab(prm.L, p_mtorr, Te) * a_ax + h_cyl(prm.R, p_mtorr, Te) * a_side

    def f(Te):
        return ng * k_iz(Te) * prm.V - u_bohm(Te) * a_eff(Te)

    Te = brentq(f, 0.8, 30.0)
    n0 = P_abs / (E * u_bohm(Te) * a_eff(Te) * (prm.energy_factor * e_c(Te) + e_wall(Te)))
    return {"Te": Te, "n0": n0, "h_l": h_slab(prm.L, p_mtorr, Te), "h_R": h_cyl(prm.R, p_mtorr, Te)}


# ================================================================ 2-영역 수송 모듈
def zone_coefficients(p_mtorr: float, Tc: float, Te: float, prm: Params) -> dict:
    """영역별 손실 계수와 영역 간 전도도."""
    d_side = prm.R - prm.re_star            # 가장자리 대표점 ~ 측벽 거리
    dist = prm.re_star - prm.rc_star        # 두 대표점 사이 거리
    T_avg = 0.5 * (Tc + Te)
    # 영역 간 플럭스: Γ_b = G (n_c - n_e), 확산 저항과 자유 흐름(보옴 속도) 저항의 직렬 연결 (가정)
    G = 1.0 / (dist / d_ambipolar(p_mtorr, T_avg) + 1.0 / u_bohm(T_avg))
    return {
        "h_ax_c": h_slab(prm.L, p_mtorr, Tc),
        "h_ax_e": h_slab(prm.L, p_mtorr, Te),
        "h_side": h_slab(2 * d_side, p_mtorr, Te),   # 얇은 고리 → 국소적으로 평판 (가정)
        "G": G,
        "A_c_ax": 2 * np.pi * prm.r_b**2,
        "A_e_ax": 2 * np.pi * (prm.R**2 - prm.r_b**2),
        "A_side": 2 * np.pi * prm.R * prm.L,
        "A_b": 2 * np.pi * prm.r_b * prm.L,
    }


def zone_residuals(x, Pc, Pe, p_mtorr, prm):
    nc, ne, Tc, Te = np.exp(x[0]), np.exp(x[1]), x[2], x[3]
    ng = n_gas(p_mtorr)
    k = zone_coefficients(p_mtorr, Tc, Te, prm)
    Gam = k["G"] * (nc - ne) * k["A_b"]                       # 중앙 → 가장자리 입자 흐름 [1/s]
    T_up = Tc if Gam > 0 else Te
    Q_b = 2.0 * T_up * Gam                                    # 그 흐름이 나르는 전자 에너지 [eV/s]

    iz_c = ng * k_iz(Tc) * nc * prm.Vc
    iz_e = ng * k_iz(Te) * ne * prm.Ve
    wall_c = nc * u_bohm(Tc) * k["h_ax_c"] * k["A_c_ax"]
    wall_e = ne * u_bohm(Te) * (k["h_ax_e"] * k["A_e_ax"] + k["h_side"] * k["A_side"])

    r1 = (iz_c - wall_c - Gam) / iz_c
    r2 = (iz_e + Gam - wall_e) / iz_e
    bE = prm.energy_factor
    r3 = (E * (iz_c * bE * e_c(Tc) + wall_c * e_wall(Tc) + Q_b) - Pc) / (Pc + Pe)
    r4 = (E * (iz_e * bE * e_c(Te) + wall_e * e_wall(Te) - Q_b) - Pe) / (Pc + Pe)
    return np.array([r1, r2, r3, r4])


def solve_zones(Pc: float, Pe: float, p_mtorr: float, prm: Params, x0=None) -> dict:
    """영역별 흡수 전력 → n_c, n_e, Tc, Te."""
    if x0 is None:
        sz = single_zone(Pc + Pe, p_mtorr, prm)
        x0 = [np.log(sz["n0"]), np.log(0.6 * sz["n0"]), sz["Te"], sz["Te"]]
    sol = least_squares(zone_residuals, x0, args=(Pc, Pe, p_mtorr, prm),
                        bounds=([20, 20, 0.8, 0.8], [45, 45, 20, 20]), xtol=1e-12, ftol=1e-12)
    nc, ne, Tc, Te = np.exp(sol.x[0]), np.exp(sol.x[1]), sol.x[2], sol.x[3]
    return {"nc": nc, "ne": ne, "Tc": Tc, "Te": Te, "x": sol.x,
            "res": float(np.max(np.abs(sol.fun)))}


def nonlocal_weight(p_mtorr: float, prm: Params) -> float:
    """가열 위치에서 Δ_h 떨어진 곳까지 에너지가 운반되는 비율 w = exp(-Δ_h/λ_ε) (가정)."""
    if not prm.nonlocal_bridge:
        return 0.0
    return float(np.exp(-prm.delta_heat / lambda_eps(p_mtorr)))


def bridge(Pc: float, Pe: float, p_mtorr: float, prm: Params):
    """국소(w→0): 각 영역이 자기 전력 사용 / 비국소(w→1): 전력이 부피 비로 퍼짐."""
    w = nonlocal_weight(p_mtorr, prm)
    P = Pc + Pe
    return (1 - w) * Pc + w * P * prm.Vc / prm.V, (1 - w) * Pe + w * P * prm.Ve / prm.V


# ================================================================ 회로 모듈 (안테나 2개 + 플라즈마 반공간)
# 플라즈마를 유전체 창 아래의 균일한 도체 반공간(복소 전도도 σ)으로 보고, 동축 원형 루프와
# 반공간 사이의 결합을 Hankel 변환으로 정확히 푼다 (Dodd & Deeds, J. Appl. Phys. 39, 2829, 1968).
#   ΔZ_ij = jωμ0 π a_i a_j ∫ J1(λa_i) J1(λa_j) e^{-2λh} (λ-α)/(λ+α) dλ,   α² = λ² + jωμ0σ
# 플라즈마가 없을 때 같은 적분에서 반사항을 빼면 자유 공간 상호 인덕턴스가 된다.
from scipy.special import j1 as _j1

_GRID_CACHE: dict = {}


def mutual(a: float, b: float, d: float) -> float:
    """동축 원형 루프 두 개(반지름 a, b, 축 간격 d)의 상호 인덕턴스 [H] (Maxwell 식)."""
    m = 4 * a * b / ((a + b) ** 2 + d**2)
    k = np.sqrt(m)
    return MU0 * np.sqrt(a * b) * ((2 / k - k) * ellipk(m) - 2 / k * ellipe(m))


def loop_self(a: float, rho: float) -> float:
    """반지름 a, 도체 반지름 rho 인 원형 루프의 고주파 자기 인덕턴스 [H]."""
    return MU0 * a * (np.log(8 * a / rho) - 2.0)


def skin_layer(n_s: float, Te: float, p_mtorr: float, f: float, nu_factor: float = 1.0):
    """표피 깊이 δ [m] 와 유효 충돌 주파수 ν_eff = ν_m + κ_ν·ν_stoc [1/s] (자기일관)."""
    w = 2 * np.pi * f
    wpe2 = n_s * E**2 / (EPS0 * ME)
    nu_m = n_gas(p_mtorr) * k_el(Te)
    v_e = np.sqrt(8 * E * Te / (np.pi * ME))
    delta = C0 / np.sqrt(wpe2)
    for _ in range(100):
        nu = nu_m + nu_factor * v_e / (4 * delta)       # 확률적(비정상 표피) 가열 (Lieberman 11.1절)
        eps = 1 - wpe2 / (w * (w - 1j * nu))
        d_new = C0 / (w * abs(np.sqrt(eps).imag))
        if abs(d_new - delta) < 1e-10:
            break
        delta = 0.5 * (delta + d_new)
    return delta, nu


def _grid(prm: Params) -> dict:
    """λ 격자와 Bessel 행렬 (플라즈마와 무관하므로 한 번만 계산)."""
    key = (prm.a1, prm.a2, prm.z_gap, prm.R)
    if key not in _GRID_CACHE:
        h = prm.z_gap
        lam = np.linspace(1e-3, 60.0 / h, 24000)
        dl = lam[1] - lam[0]
        r = np.linspace(0.0, 0.40, 401)[1:]              # 창 아래 반경 격자 [m]
        dr = r[1] - r[0]
        Ja = np.vstack([_j1(lam * prm.a1), _j1(lam * prm.a2)])   # (2, Nλ)
        Jr = _j1(np.outer(r, lam))                               # (Nr, Nλ)
        _GRID_CACHE[key] = {"lam": lam, "dl": dl, "r": r, "dr": dr, "Ja": Ja, "Jr": Jr,
                            "eh": np.exp(-lam * h), "e2h": np.exp(-2 * lam * h)}
    return _GRID_CACHE[key]


def plasma_coupling(n_s: float, Te: float, p_mtorr: float, prm: Params) -> dict:
    """균일 플라즈마 반공간에 대한 반사 임피던스 행렬 ΔZ (2×2) 와 표면 장 (단위 전류당)."""
    g = _grid(prm)
    w = 2 * np.pi * prm.f
    delta, nu = skin_layer(n_s, Te, p_mtorr, prm.f, prm.nu_factor)
    wpe2 = n_s * E**2 / (EPS0 * ME)
    kp2 = wpe2 / C0**2 * w / (w - 1j * nu)               # jωμ0σ (복소 전도도, 변위 전류 무시)
    lam = g["lam"]
    alpha = np.sqrt(lam**2 + kp2)
    refl = (lam - alpha) / (lam + alpha)
    trans = 2 * lam / (lam + alpha)
    a = np.array([prm.a1, prm.a2])
    dZ = np.empty((2, 2), complex)
    for i in range(2):
        for j in range(2):
            dZ[i, j] = 1j * w * MU0 * np.pi * a[i] * a[j] * np.sum(g["Ja"][i] * g["Ja"][j] * g["e2h"] * refl) * g["dl"]
    # 창 바로 아래(z=0-) 의 E_θ 와 H_r, 루프 i 의 단위 전류당
    Et = np.empty((2, g["r"].size), complex)
    Hr = np.empty((2, g["r"].size), complex)
    for i in range(2):
        kern = g["Ja"][i] * g["eh"] * trans * g["dl"]
        A = MU0 * a[i] / 2 * (g["Jr"] @ kern)
        Et[i] = -1j * w * A
        Hr[i] = -a[i] / 2 * (g["Jr"] @ (kern * alpha))
    return {"dZ": dZ, "Et": Et, "Hr": Hr, "r": g["r"], "dr": g["dr"], "delta": delta, "nu": nu}


def circuit(state: dict, p_mtorr: float, C: float, prm: Params, weights=(0.5, 0.5)) -> dict:
    """I1 = 1 A(rms) 기준 수동 안테나 전류, 입력 임피던스, 영역별 흡수 전력.

    weights: 표피층 전도도를 정할 때 쓰는 중앙/가장자리 가중치 (직전 반복의 흡수 전력 비).
    """
    w = 2 * np.pi * prm.f
    wc, we = weights
    n_bulk = wc * state["nc"] + we * state["ne"]
    T_s = wc * state["Tc"] + we * state["Te"]
    n_s = h_slab(prm.L, p_mtorr, T_s) * n_bulk if prm.skin_density == "sheath_edge" else n_bulk
    pc = plasma_coupling(n_s, T_s, p_mtorr, prm)
    dZ = pc["dZ"]
    L1, L2 = loop_self(prm.a1, prm.wire_r), loop_self(prm.a2, prm.wire_r)
    M12 = mutual(prm.a1, prm.a2, 0.0)
    Z12 = 1j * w * M12 + dZ[0, 1]
    Z22 = prm.R2 + 1j * w * L2 + 1 / (1j * w * C) + dZ[1, 1]
    I2 = -Z12 / Z22
    Zin = prm.R1 + 1j * w * L1 + dZ[0, 0] + Z12 * I2
    I = np.array([1.0, I2])
    p_plasma = float(np.real(np.conj(I) @ dZ @ I))       # 플라즈마 흡수 전력 / I1²
    # 창을 통과하는 포인팅 플럭스로 영역을 나눈다 (r > R 몫은 가장자리에 포함)
    Et, Hr = I @ pc["Et"], I @ pc["Hr"]
    flux = np.real(Et * np.conj(Hr)) * 2 * np.pi * pc["r"] * pc["dr"]
    inside = pc["r"] <= prm.r_b
    f_c = flux[inside].sum() / flux.sum()
    return {"I2": I2, "Zin": Zin, "p_plasma": p_plasma, "p2": abs(I2) ** 2 * prm.R2,
            "pc": f_c * p_plasma, "pe": (1 - f_c) * p_plasma, "flux_check": flux.sum() / p_plasma,
            "profile": (pc["r"], flux / (2 * np.pi * pc["r"] * pc["dr"])),
            "delta": pc["delta"], "nu": pc["nu"], "n_s": n_s, "dZ": dZ,
            "L1": L1, "L2": L2, "M12": M12}


def loaded_resonance_C(state: dict, p_mtorr: float, prm: Params, weights=(0.5, 0.5)) -> float:
    """플라즈마 부하를 포함한 수동 안테나 공진 커패시턴스 [F] (Im Z22 = 0)."""
    w = 2 * np.pi * prm.f
    wc, we = weights
    n_bulk = wc * state["nc"] + we * state["ne"]
    T_s = wc * state["Tc"] + we * state["Te"]
    n_s = h_slab(prm.L, p_mtorr, T_s) * n_bulk if prm.skin_density == "sheath_edge" else n_bulk
    dZ = plasma_coupling(n_s, T_s, p_mtorr, prm)["dZ"]
    X = w * loop_self(prm.a2, prm.wire_r) + dZ[1, 1].imag
    return 1.0 / (w * X)


# ================================================================ 자기일관 결합
def operating_point(P_in: float, p_mtorr: float, C: float, prm: Params = Params(),
                    init: dict | None = None, tol: float = 1e-5, max_iter: int = 400) -> dict:
    """P_in, p, C → 회로 ↔ 수송 반복으로 동작점을 구한다."""
    if init is None:
        sz = single_zone(0.9 * P_in, p_mtorr, prm)
        state = {"nc": sz["n0"], "ne": 0.6 * sz["n0"], "Tc": sz["Te"], "Te": sz["Te"]}
        x0, weights = None, (prm.Vc / prm.V, prm.Ve / prm.V)
    else:
        state = {k: init[k] for k in ("nc", "ne", "Tc", "Te")}
        x0, weights = init.get("x"), init.get("weights", (0.5, 0.5))
    relax = 0.5
    for it in range(max_iter):
        cir = circuit(state, p_mtorr, C, prm, weights)
        R_in = cir["Zin"].real
        I1 = np.sqrt(P_in / R_in)
        Pc, Pe = I1**2 * cir["pc"], I1**2 * cir["pe"]
        Pc_eff, Pe_eff = bridge(Pc, Pe, p_mtorr, prm)
        z = solve_zones(Pc_eff, Pe_eff, p_mtorr, prm, x0)
        new = {"nc": np.exp(relax * np.log(z["nc"]) + (1 - relax) * np.log(state["nc"])),
               "ne": np.exp(relax * np.log(z["ne"]) + (1 - relax) * np.log(state["ne"])),
               "Tc": relax * z["Tc"] + (1 - relax) * state["Tc"],
               "Te": relax * z["Te"] + (1 - relax) * state["Te"]}
        change = max(abs(np.log(new["nc"] / state["nc"])), abs(np.log(new["ne"] / state["ne"])))
        state, x0 = new, z["x"]
        # 표피층 전도도는 실제로 전력을 흡수하는 영역의 밀도를 따른다 (흡수 전력 가중)
        weights = (Pc / (Pc + Pe), Pe / (Pc + Pe))
        if change < tol:
            break
    nbar = (state["nc"] * prm.Vc + state["ne"] * prm.Ve) / prm.V
    return {**state, "x": x0, "weights": weights, "P_in": P_in, "p": p_mtorr, "C": C,
            "I1": I1, "I2": abs(cir["I2"]) * I1, "R_in": R_in,
            "Pc": Pc, "Pe": Pe, "Pc_eff": Pc_eff, "Pe_eff": Pe_eff,
            "eta": (Pc + Pe) / P_in, "edge_frac": Pe / (Pc + Pe),
            "w": nonlocal_weight(p_mtorr, prm),
            "nbar": nbar, "R": state["nc"] / state["ne"],
            "iters": it + 1, "converged": bool(change < tol), "zone_res": z["res"],
            "delta": cir["delta"], "nu": cir["nu"], "n_s": cir["n_s"], "flux_check": cir["flux_check"],
            "profile": cir["profile"]}


def calibrate_nu_factor(target_I1: float, P_in: float, p_mtorr: float, C: float,
                        prm: Params = Params(), lo: float = 0.5, hi: float = 60.0) -> float:
    """측정된 급전 전류 하나에 맞춰 확률적 가열 배수 κ_ν 를 정한다."""
    def f(k):
        return operating_point(P_in, p_mtorr, C, replace(prm, nu_factor=k))["I1"] - target_I1
    return brentq(f, lo, hi, xtol=1e-3)


def resonant_C(prm: Params = Params()) -> float:
    """플라즈마가 없을 때 수동 안테나 공진 커패시턴스 [F]."""
    return 1.0 / ((2 * np.pi * prm.f) ** 2 * loop_self(prm.a2, prm.wire_r))
