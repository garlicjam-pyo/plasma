"""팀 이론 정리 문서(2026-11-09)의 압력별 수치를 다시 계산해 대조한다.

문서 부록 B의 방법을 따른다.
- 기하: 원통 R = 21 cm, 플라즈마 높이 L = 6 cm (Zhao et al. 2026 기하), Ar, T_g = T_i = 300 K
- 흡수 전력 225 W (300 W x 효율 0.75)
- 반응 계수: Lieberman & Lichtenberg 표 3.3 피팅식 (K_iz, K_ex, K_el)
- h 인자: h_L = 0.86(3 + L/2λ_i)^-1/2, h_R = 0.80(4 + R/λ_i)^-1/2 (L&L 형태, 교재 식 2.71 형태도 함께 출력)
- 입자 균형 K_iz/u_B = 1/(n_g d_eff) → T_e, 전력 균형 n_0 = P/(e u_B ε_T A_eff)
- D_a = eT_e/(M ν_in), ν_in = v̄_i/λ_i, λ_i = 1/(330 p[Torr]) cm
- 일반 분산식 k² = (ω/c)²[1 − ω_pe²/(ω(ω − jν_m))] → δ = 1/|Im k|, 깊이 δ당 위상 회전 = |Re k / Im k|
- Robin 조건 k_z tan(k_z L/2) = u_B/D_a → 반경 혼합 길이 ℓ_r = 1/k_z
- 유체 에너지 완화 길이 λ_ε = √(κ_e/(∂P_loss/∂T_e)), κ_e = (5/2) e n D_e

추가로 자화 수송 표(3, 10, 20, 33, 50 G)와 두 교차 성분의 거리 비교를 출력한다.

    python sim/theory_note_check.py
"""
import numpy as np
from scipy.optimize import brentq

e = 1.602176634e-19
me = 9.1093837e-31
M = 39.948 * 1.66053907e-27
kB = 1.380649e-23
eps0 = 8.8541878128e-12
c = 2.99792458e8

R, L, Tg, P = 0.21, 0.06, 300.0, 225.0
w = 2 * np.pi * 13.56e6
EPS_EX = 12.0  # 문서 값. 11.5 eV로 바꿔도 n̄ 차이는 3% 안


def Kiz(T):
    return 2.34e-14 * T**0.59 * np.exp(-17.44 / T)


def Kex(T):
    return 2.48e-14 * T**0.33 * np.exp(-12.78 / T)


def Kel(T):
    lt = np.log(T)
    return 2.336e-14 * T**1.609 * np.exp(0.0618 * lt**2 - 0.1171 * lt**3)


def uB(T):
    return np.sqrt(e * T / M)


def state(p_mtorr):
    p = p_mtorr * 1e-3 * 133.322
    ng = p / (kB * Tg)
    li = 1.0 / (330 * p_mtorr * 1e-3) * 1e-2
    hL = 0.86 * (3 + L / (2 * li)) ** -0.5
    hR = 0.80 * (4 + R / li) ** -0.5
    hR_tb = 0.80 * (4 + R / (2 * li)) ** -0.5
    Aeff = 2 * np.pi * R**2 * hL + 2 * np.pi * R * L * hR
    deff = np.pi * R**2 * L / Aeff
    Te = brentq(lambda T: Kiz(T) / uB(T) - 1 / (ng * deff), 0.5, 10)
    ec = 15.76 + Kex(Te) / Kiz(Te) * EPS_EX + Kel(Te) / Kiz(Te) * 3 * me / M * Te
    eT = ec + 7.2 * Te
    n0 = P / (e * uB(Te) * eT * Aeff)
    vi = np.sqrt(8 * kB * Tg / (np.pi * M))
    nu_in = vi / li
    Da = e * Te / (M * nu_in)
    x = brentq(lambda x: x * np.tan(x) - uB(Te) / Da * L / 2, 1e-6, np.pi / 2 - 1e-9)
    kz = x / (L / 2)
    num = ng * Kel(Te)
    wpe = np.sqrt(n0 * e**2 / (eps0 * me))
    k = (w / c) * np.sqrt(1 - wpe**2 / (w * (w - 1j * num)) + 0j)
    mue = e / (me * num)
    mui = e / (M * nu_in)
    De = mue * Te
    dT = 1e-4

    def ploss(T):
        return Kiz(T) * 15.76 + Kex(T) * EPS_EX + Kel(T) * 3 * me / M * T

    dP = (ploss(Te + dT) - ploss(Te - dT)) / (2 * dT) * ng
    lam_fluid = np.sqrt(2.5 * De / dP)
    return dict(p=p_mtorr, Te=Te, ec=ec, eT=eT, hL=hL, hR=hR, hR_tb=hR_tb,
                side=2 * np.pi * R * L * hR / Aeff, n0=n0, Da=Da, DauB=Da / uB(Te),
                lr=1 / kz, nu=num, delta=1 / abs(k.imag),
                phase=np.degrees(abs(k.real / k.imag)), lam_fluid=lam_fluid,
                lam_kc=1.19 / p_mtorr, mue=mue, mui=mui, Ti=kB * Tg / e)


def main():
    print("압력별 0D·길이 척도 (문서 8·9·10장 표와 대조)")
    print(" p    T_e   ε_c  ε_T  h_L   h_R(L&L/교재)  측벽몫  n0[m^-3]  D_a  D_a/u_B  ℓ_r   δ     위상/δ  λ_ε(유체/KC)")
    for p in (5, 10, 20, 30, 40):
        s = state(p)
        print(f"{p:>3}  {s['Te']:.2f}  {s['ec']:4.0f} {s['eT']:4.0f}  {s['hL']:.2f}  {s['hR']:.3f}/{s['hR_tb']:.3f}  "
              f"{s['side']:.2f}   {s['n0']:.2e}  {s['Da']:4.0f}  {s['DauB']*100:4.1f}cm  {s['lr']*100:.1f}cm "
              f"{s['delta']*100:.2f}cm  {s['phase']:4.0f}°   {s['lam_fluid']*100:.1f}/{s['lam_kc']*100:.1f} cm")

    s = state(10)
    print("\n10 mTorr 자화 수송 (고전적 횡방향 수송, 문서 11장 표 + 3 G 행)")
    print("  B     ω_ce/ν_m  ω_ce/ω  D_e⊥/D_e  D_a⊥/D_a  λ_ε⊥/λ_ε")
    Di = s['mui'] * s['Ti']
    Da0 = (s['mui'] * s['mue'] * s['Te'] + s['mue'] * Di) / (s['mui'] + s['mue'])
    for B in (3e-4, 1e-3, 2e-3, 3.3e-3, 5e-3):
        wce = e * B / me
        f = 1 / (1 + (wce / s['nu']) ** 2)
        mue_p = s['mue'] * f
        Da_p = (s['mui'] * mue_p * s['Te'] + mue_p * Di) / (s['mui'] + mue_p)
        print(f"  {B*1e4:4.0f} G  {wce/s['nu']:6.2f}   {wce/w:5.2f}   {f:.3f}     {Da_p/Da0:.2f}      {np.sqrt(f):.2f}")
    print(f"  13.56 MHz 전자 사이클로트론 공명 자기장: {w*me/e*1e4:.2f} G")

    print("\n교차 성분별 거리 (문서 기준 형상: 안쪽 코일 r = 3·6·9 cm, 바깥 r = 12·15·18 cm, 중앙 r < 5 cm, 가장자리 12–14.5 cm)")
    for name, d in (("K21 안쪽 코일 → 가장자리 (9 → 12 cm)", 0.03), ("K12 바깥 코일 → 중앙 (12 → 5 cm)", 0.07)):
        print(f"  {name}: {d*100:.0f} cm, 단순 지수 커널 exp(-d/ℓ_r) = {np.exp(-d/s['lr']):.2f}, exp(-d/λ_ε,KC) = {np.exp(-d/s['lam_kc']):.2f}")
    print(f"  λ_ε(KC 환산)가 7 cm가 되는 압력 {119/7:.0f} mTorr, 3 cm가 되는 압력 {119/3:.0f} mTorr")


if __name__ == "__main__":
    main()
