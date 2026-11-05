"""FHP 배열 섭동 실험에서 응답 행렬 J 를 구하는 스크립트 (docs/측정계획.md · 백로그 B16)

입력: 섭동 실험 CSV. 한 줄이 한 번의 측정이고 열은

    step, du_total, du_split, r_mm, n_rel

  step      섭동 단계 이름 (예: base, Itot+5, Itot-5, x+0.05, x-0.05)
  du_total  총 전류의 상대 변화 Δln I_tot (기준 0)
  du_split  중앙 전력 몫의 변화 Δx (기준 0)
  r_mm      FHP 점의 반지름 [mm]
  n_rel     그 점의 이온 포화 전류(또는 밀도)를 기준 상태의 같은 점으로 나눈 값

처리 (docs/측정계획.md 4–5절, 상세설계보고서 결정 7):
  1. 점별 로그 변화 Δln n(r_i) = ln n_rel
  2. 최소제곱으로 Δln n = a0 + a1·ψ(r) + ε 를 풂.  ψ = +1/2 (r ≤ 25 mm), −1/2 (r ≥ 135 mm), 보간 (그 사이)
     a0 ≈ Δln n̄ (전체 변화), a1 = Δln R (분포 변화), ε 는 모양 변화 잔차
  3. 같은 조작 변수의 ± 섭동 쌍에서 중앙 차분으로 J 의 열을 구함:
     J = [[∂ln n̄/∂ln I_tot, ∂ln n̄/∂x], [∂ln R/∂ln I_tot, ∂ln R/∂x]]
  4. 열별 누설(비대각/대각), 조건수, RGA λ11 을 출력
  5. 보고서의 J 는 첫 조작 변수가 ln P 다. 총 전류 섭동으로 잰 첫 열을 P ∝ I² (부하 고정, 가정)로
     ln P 기준으로 바꿔 함께 출력한다: J(ln P) = J(ln I_tot) 의 첫 열 / 2. 누설비와 RGA 는 열 배율과 무관하다.

실행
  python sim/jacobian_fit.py                      # 내장 합성 데이터로 시연 (20 mTorr 설계 형상의 J + 잡음 2%)
  python sim/jacobian_fit.py --csv data/jfit_20mTorr.csv
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from collections import defaultdict

import numpy as np


def psi(r_mm: float) -> float:
    if r_mm <= 25:
        return 0.5
    if r_mm >= 135:
        return -0.5
    return 0.5 - (r_mm - 25) / (135 - 25)


def fit_a0_a1(points):
    """points: [(r_mm, n_rel), ...] → (a0, a1, rms_residual)"""
    y = np.log(np.array([p[1] for p in points]))
    X = np.column_stack([np.ones(len(points)), np.array([psi(p[0]) for p in points])])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    return float(coef[0]), float(coef[1]), float(np.sqrt(np.mean(resid ** 2)))


def central_diff(fits, du_key):
    """fits: {step: (du_total, du_split, a0, a1)}; du_key = 0 (total) or 1 (split)
    같은 변수의 +·− 섭동을 짝지어 (Δy)/(Δu) 평균"""
    plus = [(f[du_key], f[2], f[3]) for f in fits.values() if f[du_key] > 0 and f[1 - du_key] == 0]
    minus = [(f[du_key], f[2], f[3]) for f in fits.values() if f[du_key] < 0 and f[1 - du_key] == 0]
    if not plus or not minus:
        return None
    dp = np.mean([p[0] for p in plus]); dm = np.mean([m[0] for m in minus])
    a0p = np.mean([p[1] for p in plus]); a0m = np.mean([m[1] for m in minus])
    a1p = np.mean([p[2] for p in plus]); a1m = np.mean([m[2] for m in minus])
    return (a0p - a0m) / (dp - dm), (a1p - a1m) / (dp - dm)


# 20 mTorr 설계 형상의 J (ln P 기준 [[1, 0.25], [0, 2.44]], presentation1_estimates.py jacobian)를
# P ∝ I² 로 총 전류 기준으로 옮긴 값 (가정). J21 = 0 은 "T_e 가 전력과 무관"이라는 모델 가정의 귀결이다.
J_SYNTH = ((2.0, 0.25), (0.0, 2.44))


def synthetic(J=J_SYNTH, noise=0.02, seed=1):
    """보고서 20 mTorr 동작점의 J 로 합성 측정값을 만든다 (잡음은 점별 상대 2%)"""
    rng = random.Random(seed)
    radii = [0] + [25] * 4 + [75] * 4 + [140] * 8          # docs/측정계획.md 2절의 배치 (17점)
    steps = [("base", 0, 0)]
    for rep in range(3):
        steps += [(f"Itot+5_{rep}", +0.05, 0), (f"Itot-5_{rep}", -0.05, 0),
                  (f"x+0.05_{rep}", 0, +0.05), (f"x-0.05_{rep}", 0, -0.05)]
    rows = []
    for name, dt, dx in steps:
        dln_n = J[0][0] * dt + J[0][1] * dx
        dln_R = J[1][0] * dt + J[1][1] * dx
        for r in radii:
            val = math.exp(dln_n + dln_R * psi(r)) * (1 + rng.gauss(0, noise))
            rows.append({"step": name, "du_total": dt, "du_split": dx, "r_mm": r, "n_rel": val})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", help="섭동 실험 CSV (없으면 합성 데이터)")
    a = ap.parse_args()

    if a.csv:
        with open(a.csv, newline="", encoding="utf-8") as f:
            rows = [dict(r, du_total=float(r["du_total"]), du_split=float(r["du_split"]),
                         r_mm=float(r["r_mm"]), n_rel=float(r["n_rel"])) for r in csv.DictReader(f)]
    else:
        rows = synthetic()
        print("합성 데이터: J_true(ln I_tot) = [[2, 0.25], [0, 2.44]] (ln P 기준 [[1, 0.25], [0, 2.44]]), "
              "점별 잡음 2%, 17점, 섭동 3회 왕복\n")

    by_step = defaultdict(list)
    meta = {}
    for r in rows:
        by_step[r["step"]].append((r["r_mm"], r["n_rel"]))
        meta[r["step"]] = (r["du_total"], r["du_split"])

    fits = {}
    print("%-12s %9s %8s %8s %8s %8s" % ("step", "ΔlnItot", "Δx", "a0", "a1", "ε_rms"))
    for step, pts in by_step.items():
        a0, a1, rms = fit_a0_a1(pts)
        fits[step] = (meta[step][0], meta[step][1], a0, a1)
        print("%-12s %9.3f %8.3f %8.4f %8.4f %8.4f" % (step, meta[step][0], meta[step][1], a0, a1, rms))

    col_t = central_diff(fits, 0)
    col_x = central_diff(fits, 1)
    if col_t is None or col_x is None:
        print("\n± 섭동 쌍이 부족해 J 를 구할 수 없다.")
        return
    J = np.array([[col_t[0], col_x[0]], [col_t[1], col_x[1]]])
    JP = J.copy()
    JP[:, 0] /= 2.0          # P ∝ I² (가정)
    print("\nJ (행: ln n̄, ln R · 열: ln I_tot, x) =")
    print("  [[%7.3f  %7.3f]" % (J[0, 0], J[0, 1]))
    print("   [%7.3f  %7.3f]]" % (J[1, 0], J[1, 1]))
    print("J (열: ln P, x; P ∝ I² 가정) =")
    print("  [[%7.3f  %7.3f]" % (JP[0, 0], JP[0, 1]))
    print("   [%7.3f  %7.3f]]" % (JP[1, 0], JP[1, 1]))
    leak_t = abs(J[1, 0] / J[0, 0]) if J[0, 0] else float("nan")
    leak_x = abs(J[0, 1] / J[1, 1]) if J[1, 1] else float("nan")
    lam11 = 1.0 / (1.0 - J[0, 1] * J[1, 0] / (J[0, 0] * J[1, 1])) if J[0, 0] * J[1, 1] else float("nan")

    def level(v):
        return "L2" if v <= 0.1 else "L1 (L2 기준 0.1 초과)"
    # 분배 열은 예측값 자체가 0.10 (10–30 mTorr) 이라 L2 기준과 같다 → 잡음에 따라 L1/L2 로 갈리는 경계
    print("누설 (열별, L2 기준 0.1): 총 전류 열 %.3f (J21/J11) → %s, 분배 열 %.3f (J12/J22) → %s"
          % (leak_t, level(leak_t), leak_x, level(leak_x)))
    print("조건수 κ(J) = %.2f (ln I_tot 기준), %.2f (ln P 기준), RGA λ11 = %.3f"
          % (np.linalg.cond(J), np.linalg.cond(JP), lam11))


if __name__ == "__main__":
    main()
