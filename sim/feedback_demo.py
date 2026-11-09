"""바깥 루프(FHP 배열 → J⁻¹ → 전력·분배 설정값) 되먹임의 동작 예시.

플랜트는 2-영역 0D 모델(설계 형상, 20 mTorr, 영역별 흡수 전력 직접 지정)이다.
docs/조정절차.md 3절의 절차를 따른다.
  3단계 피드포워드: Δu = K̂⁻¹ Δy*, |Δx| > 0.1이면 0.1로 자름
  5단계 바깥 루프: 매 갱신(약 1 s) u ← u + g·K̂⁻¹ e, e = 목표 − 측정 (적분 동작)
  측정 잡음: ln n̄, ln R_Γ 각각 1% (FHP 불확도 약 1.1%)
  분배 한계: 중앙 몫 0.07–0.93 (코일 선택도)
한 걸음의 오차 배율은 (1 − g·K/K̂)이므로 0 < g·K/K̂ < 2이면 수렴한다.

    python sim/feedback_demo.py
"""
import numpy as np

import presentation1_estimates as pe

prm = pe.m.Params(**pe.DESIGN)
p = 20
P0, x0 = 300.0, 0.2


def plant(P, x):
    y = pe._out(P, x, p, prm)
    return np.array([y[0], y[1]])


def run(Khat, target_R=0.8, g=0.5, noise=0.01, steps=10, seed=1):
    rng = np.random.default_rng(seed)
    y0 = plant(P0, x0)
    yt = np.array([y0[0], np.log(target_R)])          # 평균 밀도는 유지, R만 목표로
    Ki = np.linalg.inv(Khat)
    u = np.array([np.log(P0), x0])
    du = Ki @ (yt - y0)                                 # 피드포워드
    if abs(du[1]) > 0.1:
        du *= 0.1 / abs(du[1])
    u = u + du
    rows = []
    for k in range(steps):
        u[1] = np.clip(u[1], 0.07, 0.93)
        y = plant(np.exp(u[0]), u[1])
        e = yt - (y + rng.normal(0, noise, 2))          # FHP 측정 (잡음 포함)
        rows.append((k, np.exp(u[0]), u[1], np.exp(y[1]), np.exp(y[0] - y0[0]) - 1, e[1]))
        u = u + g * (Ki @ e)                            # 적분 보정
    return np.exp(y0[1]), rows


def main():
    K = np.array([[1.0, 0.254], [0.0, 2.43]])           # x = 0.2에서 구한 J (sim/k_operating_point.py)
    cases = (("K̂ = 출발점의 J", K),
             ("K̂의 형상 이득 40% 과소", np.array([[1.0, 0.254], [0.0, 2.43 * 0.6]])),
             ("K̂의 형상 이득 2.2배 과대", np.array([[1.0, 0.254], [0.0, 2.43 * 2.2]])))
    for name, Kh in cases:
        R0, rows = run(Kh)
        print(f"== {name} (시작 R = {R0:.2f}, 목표 R = 0.80, n̄ 유지, g = 0.5)")
        print("  갱신   P [W]    x      R     n̄ 변화   측정 ln R 오차")
        for k, P, x, R, dn, e in rows:
            print(f"  {k:3d}  {P:6.1f}  {x:.3f}  {R:.3f}  {dn*100:+5.1f}%   {e:+.3f}")


if __name__ == "__main__":
    main()
