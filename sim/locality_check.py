"""이론 정리 개정 3의 국소성 판정(9쪽 (A1)–(A3))을 압력별로 다시 계산한다.

  η_RF = v_th / (L_E √(ν_m² + ω²))   국소 RF 전도도 (5장 보강 (L2))
  η_K  = λ_ε,fluid / L_ch, L_ch = L   국소 Maxwellian 유체 닫힘 (A3)
v_th는 평균 속도 √(8eT_e/πm_e), L_E는 표피 깊이 δ와 코일 묶음 간격 3 cm 두 가지로 본다.
값은 0D 잠정 T_e, n₀(theory_note_check.state)에 기댄 크기 추정이다.

    python sim/locality_check.py
"""
import numpy as np

import theory_note_check as t

OMEGA = 2 * np.pi * 13.56e6
E, ME = 1.602e-19, 9.109e-31


def main():
    print(" p   T_e   ν_m [s⁻¹]  ℓ_RF   δ     η_RF(δ)  η_RF(3cm)  λ_ε,fluid  λ_ε/L   ℓ_r")
    for p in (5, 10, 20, 30, 40):
        s = t.state(p)
        v = np.sqrt(8 * s['Te'] * E / (np.pi * ME))
        l_rf = v / np.hypot(s['nu'], OMEGA)
        print(f"{p:3d} {s['Te']:5.2f} {s['nu']:9.2e} {l_rf*100:5.2f} {s['delta']*100:5.2f}"
              f" {l_rf/s['delta']:7.2f} {l_rf/0.03:9.2f} {s['lam_fluid']*100:9.1f} {s['lam_fluid']/t.L:7.2f}"
              f" {s['lr']*100:5.2f}")
    print("길이 단위 cm. ℓ_RF = v_th/√(ν_m² + ω²). η ≪ 1이 국소 조건이다.")


if __name__ == '__main__':
    main()
