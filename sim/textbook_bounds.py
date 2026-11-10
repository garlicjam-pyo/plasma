"""교재(정진욱, 『플라즈마 전자공학』 4판) 식만으로 ρ 제어를 볼 때 나오는 두 극한과 그 사이.

1) 교재 확산 방정식 (1.76) ∂n/∂t − D_a∇²n = ν_iz n, ν_iz는 위치와 무관(교재 63쪽: T_e 균일)
   → 원통 해 (1.83) n ∝ J0(2.41 r/R), 높이 해 (1.79) cos(πz/L). ρ는 기하로 고정되고 가열 분포와 무관하다.
2) 교재 전력 균형 (2.68)을 구역마다 따로 적용(구역 가열 = 구역 생성)하고, 구역 사이는 양극성 확산만 둔다
   → 가열 기울기의 전달률 R_loc = 1/(1 + k²ℓ_r²). 교재 높이 해의 손실 길이 ℓ_r = L/π를 쓴다.
3) 두 극한 사이를 KC20 식 (5) λ_ε = √(λ_m λ_inel/3)로 잇는 보간 (1 − e^(−Δ/λ_ε))·R_loc (가정).
4) 비교: 에너지 수송을 넣은 선형 응답 R (zone_control_authority.py).

    python sim/textbook_bounds.py
"""
import numpy as np
from scipy.integrate import quad
from scipy.special import j0

import theory_note_check as t
import zone_control_authority as z

R, L = t.R, t.L
K2 = 5.520 / R            # 반경 2차 모드
DELTA = 0.09              # 두 코일 묶음 중심 사이 거리 [m] (6 cm, 15 cm)
LAM_KC_1MTORR = 1.19      # KC20 그림 5, 15.7 eV, ∝ 1/p [m]


def area_mean(f, a, b):
    return quad(lambda r: f(r) * r, a, b)[0] / quad(lambda r: r, a, b)[0]


def main():
    prof = lambda r: j0(2.405 * r / R)
    rho_j0 = area_mean(prof, 0, 0.05) / area_mean(prof, 0.12, 0.145)
    rho_uni = area_mean(lambda r: 1 - (r / R) ** 2, 0, 0.05) / area_mean(lambda r: 1 - (r / R) ** 2, 0.12, 0.145)
    print(f"교재 고유모드 (1.83) J0(2.41r/R): ρ = {rho_j0:.2f} (코일 전류와 무관)")
    print(f"참고: 균일 생성 포물선 해: ρ = {rho_uni:.2f}")
    r_loc_tb = 1 / (1 + (K2 * L / np.pi) ** 2)
    print(f"\n가열 기울기 → 밀도 기울기 전달률 (반경 2차 모드, Δ = {DELTA*100:.0f} cm)")
    print(" p    교재 고유모드  보간(KC20 λ_ε)  선형 응답(에너지 수송)  교재 구역별 전력 균형")
    for p in (5, 10, 20, 30, 50):
        lam_kc = LAM_KC_1MTORR / p
        bridge = (1 - np.exp(-DELTA / lam_kc)) * r_loc_tb
        r_lin = z.response(z.coeffs(p), K2)[0]
        print(f"{p:3d}       0          {bridge:5.2f} (λ_ε={lam_kc*100:4.1f} cm)      {r_lin:5.2f}"
              f"                 {r_loc_tb:5.2f}")


if __name__ == '__main__':
    main()
