"""국소 Maxwellian 닫힘에서 T_e가 조금 변할 때 반응계수가 얼마나 바뀌는지 본다 (10 mTorr 기준).

이론 정리 개정 3의 "수치적 주의"(d ln K_iz/d ln T_e ≈ 7)를 표로 확인하고,
같은 평균 T_e라도 공간 분포가 고르지 않으면 평균 이온화가 커지는 정도(볼록성)를 함께 출력한다.
반응계수는 theory_note_check와 같은 L&L 표 3.3 피팅식이다.

    python sim/kiz_sensitivity.py
"""
import numpy as np

import theory_note_check as t


def eps_c(T):
    return 15.76 + t.Kex(T) / t.Kiz(T) * t.EPS_EX + t.Kel(T) / t.Kiz(T) * 3 * t.me / t.M * T


def main():
    s = t.state(10)
    ng = 10e-3 * 133.322 / (t.kB * t.Tg)
    T0 = s['Te']
    print(f"10 mTorr, n_g = {ng:.3e} m^-3, 0D 기준 T_e = {T0:.2f} eV")
    print(" T_e   K_iz [m3/s]  K_iz/K_iz(T0)  K_ex/K_iz  eps_c [V]  nu_m [1/s]  dlnK/dlnT")
    for T in (2.5, 2.6, T0, 2.9, 3.0):
        print(f"{T:5.2f}  {t.Kiz(T):.3e}   {t.Kiz(T)/t.Kiz(T0):6.2f}      {t.Kex(T)/t.Kiz(T):5.2f}"
              f"     {eps_c(T):5.1f}     {ng*t.Kel(T):.2e}    {0.59 + 17.44/T:5.2f}")

    lo, hi = T0 - 0.15, T0 + 0.15
    k_mix = 0.5 * (t.Kiz(lo) + t.Kiz(hi))
    print(f"\n볼록성 예: 절반 {lo:.2f} eV, 절반 {hi:.2f} eV (평균 {T0:.2f} eV)")
    print(f"  평균 K_iz / K_iz(평균 T_e) = {k_mix / t.Kiz(T0):.3f}")


if __name__ == '__main__':
    main()
