"""가열 분포를 기울였을 때 밀도 분포가 얼마나 따라 기우는지 선형 응답으로 어림한다.

얇은 챔버(R = 21 cm, L = 6 cm)를 높이 기본 모드로 투영한 반경 방향 n–T_e 모델을
균일한 기준 상태 둘레에서 선형화하고, 반경 파수 k인 가열 섭동 δp/p = π에 대한
밀도 응답 δn/n = R(k)·π를 구한다.

  입자: D_a∇²(δn/n + δT/T) + ν_L β′ δT/T = 0          (Γ = −μ_i∇(nT_e), 축 방향 손실 ν_L = D_a k_z²)
  에너지: (5/2)T ∇·δΓ − κ_e∇²δT = δp − δP_loss       (P_loss = e n F(T), F = n_g Σ Kε + ν_L·7.2T)

  R(k) = 1 / (1 + [γ(1 + k²λ²) + 2.5 T β′/ε_T] · k²ℓ_r² / (β′ − k²ℓ_r²))
  β′ = d ln(n_g K_iz/ν_L)/d ln T,  γ = d ln F/d ln T,  λ² = κ_e/(e n dF/dT),  ℓ_r = 1/k_z

비교 모델(국소 생성, T_e 고정, G = p/(eε_T))은 R_loc(k) = 1/(1 + k²ℓ_r²)이다.
중앙–가장자리 기울기는 반경 2차 모드 k = 5.52/R로 대표한다. 크기 어림이며 설계값이 아니다.

    python sim/zone_control_authority.py
"""
import numpy as np
from scipy.optimize import brentq

import theory_note_check as t

CHI = {'m=2': 5.520, 'm=3': 8.654}


def coeffs(p_mtorr):
    s = t.state(p_mtorr)
    T0 = s['Te']
    p = p_mtorr * 1e-3 * 133.322
    ng = p / (t.kB * t.Tg)
    li = 1.0 / (330 * p_mtorr * 1e-3) * 1e-2
    nu_in = np.sqrt(8 * t.kB * t.Tg / (np.pi * t.M)) / li

    def Da(T):
        return t.e * T / (t.M * nu_in)

    def kz(T):
        x = brentq(lambda x: x * np.tan(x) - t.uB(T) / Da(T) * t.L / 2, 1e-9, np.pi / 2 - 1e-12)
        return x / (t.L / 2)

    def nuL(T):
        return Da(T) * kz(T) ** 2

    def ploss(T):
        return t.Kiz(T) * 15.76 + t.Kex(T) * t.EPS_EX + t.Kel(T) * 3 * t.me / t.M * T

    h = 1e-4
    dln = lambda f: (np.log(f(T0 * (1 + h))) - np.log(f(T0 * (1 - h)))) / (2 * h)
    b_iz, b_L = dln(t.Kiz), dln(nuL)
    nu_iz = ng * t.Kiz(T0)
    F0 = ng * ploss(T0) + nu_iz * 7.2 * T0                       # 기준 상태에서 ν_L = ν_iz
    dF = ng * (ploss(T0 * (1 + h)) - ploss(T0 * (1 - h))) / (2 * h * T0) \
        + nu_iz * 7.2 * (1 + b_L)
    De = t.e * T0 / (t.me * ng * t.Kel(T0))
    lam = np.sqrt(2.5 * De / dF)
    lr = 1 / kz(T0)
    return dict(T0=T0, b=b_iz - b_L, g=T0 * dF / F0, epsT=F0 / nu_iz, lam=lam, lr=lr,
                lam_fluid=s['lam_fluid'])


def response(c, k):
    x = (k * c['lr']) ** 2
    num = c['g'] * (1 + (k * c['lam']) ** 2) + 2.5 * c['T0'] * c['b'] / c['epsT']
    return 1 / (1 + num * x / (c['b'] - x)), 1 / (1 + x)


def main():
    print(" p    T_e   β′    γ    ℓ_r   λ_proj  λ_fluid  √(ℓ_rλ)  |  R(m=2) R_loc(m=2)  |  R(m=3) R_loc(m=3)")
    for p in (5, 10, 20, 30, 50):
        c = coeffs(p)
        out = []
        for chi in CHI.values():
            out += list(response(c, chi / t.R))
        print(f"{p:3d} {c['T0']:5.2f} {c['b']:5.2f} {c['g']:5.2f} {c['lr']*100:5.2f} {c['lam']*100:6.1f}"
              f"   {c['lam_fluid']*100:6.1f}   {np.sqrt(c['lr']*c['lam'])*100:5.1f}  |"
              f"  {out[0]:6.2f}   {out[1]:6.2f}      |  {out[2]:6.2f}   {out[3]:6.2f}")
    print("길이 cm. R = 밀도 기울기 / 가열 기울기. R_loc는 T_e 고정·국소 생성 비교 모델.")
    print(f"k(m=2) = {CHI['m=2']/t.R:.1f} m⁻¹, k(m=3) = {CHI['m=3']/t.R:.1f} m⁻¹")


if __name__ == '__main__':
    main()
