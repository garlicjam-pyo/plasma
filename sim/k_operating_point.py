"""응답 행렬 J가 운전점에 따라 얼마나 변하는지, 작은 신호 선형 예측이 어디까지 맞는지 본다.

2-영역 0D 모델(설계 형상, 영역별 흡수 전력 직접 지정, T_e·손실 계수 고정)을 쓴다.
이 모델에는 밀도에 따른 표피 깊이·코일 부하 변화, E–H 전이, 위상 ψ(n), 전류 한계가 없으므로
실제 비선형성의 하한만 보여 준다.

    python sim/k_operating_point.py [압력 mTorr, 기본 20]
"""
import sys

import numpy as np

import presentation1_estimates as pe

prm = pe.m.Params(**pe.DESIGN)
P = 300.0


def jac(x, p):
    dP, dx = 0.02, 0.005
    a, b = pe._out(P * np.exp(dP), x, p, prm), pe._out(P * np.exp(-dP), x, p, prm)
    c, d = pe._out(P, x + dx, p, prm), pe._out(P, x - dx, p, prm)
    return np.array([[(a[0] - b[0]) / (2 * dP), (c[0] - d[0]) / (2 * dx)],
                     [(a[1] - b[1]) / (2 * dP), (c[1] - d[1]) / (2 * dx)]])


def main(p):
    print(f"{p} mTorr, 설계 형상, P = {P:.0f} W. 입력 (ln P, x = 중앙 흡수 몫), 출력 (ln n̄, ln R)")
    print("  x     R     J12     J22   누설 |J12/J22|  조건수")
    for x in (0.08, 0.12, 0.2, 0.3, 0.4, 0.5, 0.6):
        J = jac(x, p)
        R = np.exp(pe._out(P, x, p, prm)[1])
        print(f" {x:.2f}  {R:.2f}  {J[0,1]:+.3f}  {J[1,1]:.2f}     {abs(J[0,1]/J[1,1]):.3f}        {np.linalg.cond(J):.1f}")

    x0 = 0.2
    y0, J0 = pe._out(P, x0, p, prm), jac(x0, p)
    print(f"\nx0 = {x0} (R = {np.exp(y0[1]):.2f})의 J로 한 번에 예측한 값과 실제 값")
    for x in (0.25, 0.3, 0.4, 0.5):
        y = pe._out(P, x, p, prm)
        print(f" x = {x}: R 실제 {np.exp(y[1]):.2f}, 선형 {np.exp(y0[1] + J0[1,1]*(x-x0)):.2f}"
              f" | n̄ 변화 실제 {np.exp(y[0]-y0[0])-1:+.3f}, 선형 {np.exp(J0[0,1]*(x-x0))-1:+.3f}")

    print("\nx0의 J를 고정한 반복 x ← x + (ln R* − ln R)/J22 (중앙 몫 하한 0.07, 코일 선택도)")
    for target in (0.8, 0.7, 0.5):
        x, hist = x0, []
        for _ in range(8):
            lnR = pe._out(P, x, p, prm)[1]
            hist.append(round(float(np.exp(lnR)), 2))
            err = np.log(target) - lnR
            if abs(err) < 0.02:
                break
            x = min(max(x + err / J0[1, 1], 0.07), 0.93)
        print(f" 목표 R = {target}: {hist}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
