"""이론 개정본 7·8·9장을 잇는 수치 점검.

7장의 에너지 완화 길이 λ_ε와 8장의 반경 혼합 길이 ℓ_r을 압력별로 같은 표에 놓고,
균일 생성일 때 얇은 챔버(분리변수 단일 모드)와 무한 원통(8.4절)의 ρ를 비교한다.
4장 h_L과 8.5절 Robin 해가 주는 벽/중심 밀도비도 함께 출력한다.

    python sim/ch7_9_links.py
"""
import numpy as np
from scipy.integrate import quad
from scipy.special import i0, i1

import theory_note_check as t

R, L = t.R, t.L
RC, R1, R2 = 0.05, 0.12, 0.145          # 중앙 0–5 cm, 가장자리 12–14.5 cm (1.4절)


def rho_thin(s):
    """균일 g(r), 높이 기본 모드, 측벽 Robin: f = 1 + C·I0(k_z r)."""
    kz = 1 / s["lr"]
    uB = s["Da"] / s["DauB"]
    C = -uB / (s["Da"] * kz * i1(kz * R) + uB * i0(kz * R))
    f = lambda r: 1 + C * i0(kz * r)
    nc = quad(lambda r: f(r) * r, 0, RC)[0] * 2 / RC**2
    ne = quad(lambda r: f(r) * r, R1, R2)[0] * 2 / (R2**2 - R1**2)
    return nc / ne


def rho_infcyl(c=0.0):
    """8.4절 (8.21)·(8.30): n ∝ R² − r² + c, c = 2R·D_a/u_B (Robin) 또는 0 (Dirichlet)."""
    nc = R**2 - RC**2 / 2 + c
    ne = R**2 - (R1**2 + R2**2) / 2 + c
    return nc / ne


def main():
    print("압력별 길이 척도와 균일 생성 ρ (중앙–가장자리 간격: 영역 경계 7 cm, 무게중심 약 10 cm)")
    print("  p   T_e   λ_ε 유체  λ_ε KC   ℓ_r   L/π   ρ(얇은 챔버)")
    for p in (5, 10, 20, 40):
        s = t.state(p)
        print(f"{p:4d} {s['Te']:5.2f} {s['lam_fluid']*100:7.1f} {s['lam_kc']*100:7.1f}"
              f" {s['lr']*100:6.2f} {L/np.pi*100:5.2f} {rho_thin(s):9.3f}")
    s = t.state(10)
    print()
    print("10 mTorr, 균일 생성의 ρ")
    print(f"  무한 원통 Dirichlet (8.21): {rho_infcyl():.2f}")
    print(f"  무한 원통 Robin (8.30):     {rho_infcyl(2 * R * s['DauB']):.2f}")
    print(f"  얇은 챔버 단일 모드:        {rho_thin(s):.2f}")
    print(f"  Dirichlet 고유값 항 (χ01/R)² = {(2.4048/R)**2:.0f}, (π/L)² = {(np.pi/L)**2:.0f} m⁻²"
          " → 위·아래 손실이 대부분")
    uB = s["Da"] / s["DauB"]
    print()
    print("벽/중심 밀도비 비교 (10 mTorr)")
    print(f"  4장 h_L (교재 식): {s['hL']:.3f}")
    print(f"  8.5절 평판 Robin, 균일 생성: 1/(1 + u_B L/4D_a) = {1/(1 + uB*L/(4*s['Da'])):.3f}")
    print("  → 상수 D_a Robin과 4장 h 인자가 다르다. ℓ_r은 Dirichlet 극한 L/π까지 줄 수 있다.")


if __name__ == "__main__":
    main()
