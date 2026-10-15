"""ICP 중앙부·가장자리 독립 제어 검토를 위한 1차 스케일 추정.

docs/01_배경이론.md 의 수치 표를 재현한다. 값은 모두 차수(order-of-magnitude)
추정용이며, 기준 챔버·운전 조건이 정해지면 상단 PARAMETERS 를 바꿔 다시 실행한다.

실행: python sim/scale_estimates.py
"""

import math

# ---------------------------------------------------------------- 물리 상수 (SI)
E = 1.602176634e-19        # 기본 전하 [C]
ME = 9.1093837015e-31      # 전자 질량 [kg]
KB = 1.380649e-23          # 볼츠만 상수 [J/K]
EPS0 = 8.8541878128e-12    # 진공 유전율 [F/m]
C = 2.99792458e8           # 광속 [m/s]
AMU = 1.66053906660e-27    # 원자 질량 단위 [kg]
TORR = 133.322368          # 1 Torr [Pa]

# ---------------------------------------------------------------- PARAMETERS (예시값)
GAS_MASS_AMU = 39.948      # Ar
T_GAS = 300.0              # 기체·이온 온도 [K]
TE_EV = 3.0                # 전자 온도 [eV]
SIGMA_IN = 1.0e-18         # 이온-중성 충돌 단면적 [m^2] (Lieberman: lambda_i ≈ 1/(330 p[Torr]) cm 에 해당)
F_RF = 13.56e6             # 구동 주파수 [Hz]

PRESSURES_MTORR = [1, 5, 10, 30, 100]
DENSITIES_CM3 = [1e10, 1e11, 1e12]
CHAMBER_R_M = 0.20         # 챔버 반지름 [m] (300 mm 웨이퍼용 예시)
GAPS_M = [0.05, 0.10, 0.20]  # 유전체 창~웨이퍼 간격 L [m]

J01 = 2.404825557695773    # J0 의 첫 번째 영점


def neutral_density(p_mtorr: float) -> float:
    """중성 기체 밀도 [m^-3]."""
    return p_mtorr * 1e-3 * TORR / (KB * T_GAS)


def ion_mfp(p_mtorr: float) -> float:
    """이온-중성 평균 자유 행로 [m]."""
    return 1.0 / (neutral_density(p_mtorr) * SIGMA_IN)


def ambipolar_D(p_mtorr: float) -> float:
    """양극성 확산 계수 D_a ≈ mu_i * T_e [m^2/s] (T_e >> T_i, lambda_i << 챔버 크기 가정)."""
    m_i = GAS_MASS_AMU * AMU
    v_i = math.sqrt(8 * KB * T_GAS / (math.pi * m_i))
    mu_i = E * ion_mfp(p_mtorr) / (m_i * v_i)
    return mu_i * TE_EV


def skin_depth(n_cm3: float) -> float:
    """무충돌 표피 깊이 delta_p = c / omega_pe [m]."""
    n = n_cm3 * 1e6
    w_pe = math.sqrt(n * E**2 / (EPS0 * ME))
    return C / w_pe


def diffusion_length(r_m: float, l_m: float) -> float:
    """원통형 챔버의 기본 확산 길이 Lambda [m]."""
    return 1.0 / math.sqrt((J01 / r_m) ** 2 + (math.pi / l_m) ** 2)


def main() -> None:
    print(f"# 스케일 추정 (Ar, T_gas={T_GAS:.0f} K, Te={TE_EV} eV, R={CHAMBER_R_M*100:.0f} cm)\n")

    print("## 1. 압력별 기체·수송 스케일\n")
    print("| p [mTorr] | n_g [cm^-3] | λ_i [cm] | D_a [m²/s] |")
    print("|---:|---:|---:|---:|")
    for p in PRESSURES_MTORR:
        print(f"| {p} | {neutral_density(p)/1e6:.2e} | {ion_mfp(p)*100:.2f} | {ambipolar_D(p):.1f} |")

    print("\n## 2. 밀도별 표피 깊이 (무충돌)\n")
    print("| n_e [cm^-3] | ω_pe/2π [GHz] | δ_p [cm] |")
    print("|---:|---:|---:|")
    for n in DENSITIES_CM3:
        d = skin_depth(n)
        f_pe = C / d / (2 * math.pi)
        print(f"| {n:.0e} | {f_pe/1e9:.2f} | {d*100:.2f} |")

    print("\n## 3. 챔버 간격(L)별 확산 길이와 반경 방향 퍼짐 길이\n")
    print("| L [cm] | Λ [cm] | 축 방향 항 (π/L)² 비중 | ℓ = L/π [cm] | τ_D @10 mTorr [μs] |")
    print("|---:|---:|---:|---:|---:|")
    for l in GAPS_M:
        lam = diffusion_length(CHAMBER_R_M, l)
        ax = (math.pi / l) ** 2
        rad = (J01 / CHAMBER_R_M) ** 2
        tau = lam**2 / ambipolar_D(10)
        print(f"| {l*100:.0f} | {lam*100:.2f} | {ax/(ax+rad)*100:.0f}% | {l/math.pi*100:.2f} | {tau*1e6:.0f} |")


if __name__ == "__main__":
    main()
