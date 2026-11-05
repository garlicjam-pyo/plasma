"""두 전원 ICP 안테나의 위상 · 교환 전력 · 정합 리액턴스 (결정 4·5 보조 계산)

결합 인덕터(L1, L2, M12)에 플라즈마가 반사하는 임피던스 ΔZ = R' + jX'를 더한 집중 상수 모델로,
두 코일 전류가 I2 = k·I1·e^{jφ}일 때 다음을 계산한다 (상세설계보고서 결정 4·5의 식).

    P_plasma = |I1|² [R'11 + k² R'22 + 2 k R'12 cos φ]          (플라즈마 흡수 전력)
    P_exch   = |I1|² (ωM12 + X'12) k sin φ                      (전원 간 교환 전력)
    P1       = |I1|² [R'11 + k R'12 cos φ − k (ωM12 + X'12) sin φ]
    P2       = |I1|² [k² R'22 + k R'12 cos φ + k (ωM12 + X'12) sin φ]
    Z_in,1   = R'11 + jωL1 + jX'11 + (R'12 + j(ωM12 + X'12)) k e^{jφ}

반사 임피던스와 동작점은 sim/presentation1_estimates.py phase 와 같은 것을 쓴다.
  - ΔZ: two_zone_icp.plasma_coupling (단일 턴 루프, 창 아래 균일 반공간의 Dodd–Deeds 해, 고정 밀도).
    X'12 ≈ −4 ~ −6 Ω 이 ωM12 = 7.8 Ω 을 상당 부분 상쇄하므로 반드시 넣는다 (2026-11-05 검토).
  - 동작점: n = 3×10¹⁶, 10¹⁷ m⁻³ × p = 10, 20 mTorr, 중앙 영역 전력 몫 0.20 (R ≈ 1 근처)이 되는 k.
  - 위상 허용 오차: (ωM12 + X'12)·k·|sin δφ| ≤ 0.1·P_plasma(φ0) 의 δφ.
  - 효율: η = P_plasma / (P_plasma + R_c (1 + k²)), 두 코일 모두 R_c = 0.23 Ω (KC20 값, 가정).
  - 교환 전력 비: φ = 90° 에서 |P_exch| / P_plasma(90°), 각 위상의 동작점 k에서.
처음 판(번들)은 반사 저항을 placeholder로, X'12 를 −0.5 Ω 으로 두어 위상 허용 오차를 좁게 냈다.

정합 리액턴스 변화는 두 가지로 낸다.
  - 코일 항만: ωM12·k·cos φ / ωL1 (보고서의 +48% / −22%가 이 값)
  - X'12 포함: (ωM12 + X'12)·k·cos φ / ωL1 (정합기가 실제로 보는 변화에 더 가까움)

실행
  python sim/two_source_phase.py            # 4개 동작점, 표 출력, figures/two_source_phase.csv 저장
  python sim/two_source_phase.py --manual --R11 1.4 --R22 4.4 --R12 1.2 --X12 -4.5 --k0 2.0 --k180 0.9
                                            # 반사 임피던스를 직접 넣는 집중 상수 계산 (CSV 저장 안 함)

단위: 저항·리액턴스 Ω, 인덕턴스 H, 전력은 |I1|² = 1 A² 당 W.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import two_zone_icp as m  # noqa: E402
import presentation1_estimates as pe  # noqa: E402

FIG = Path(__file__).resolve().parent.parent / "figures"
OPERATING_POINTS = ((3e16, 2.5, 10), (3e16, 2.2, 20), (1e17, 2.5, 10), (1e17, 2.2, 20))  # (n [m⁻³], T_e [eV], p [mTorr])
X_C = 0.20          # 비교 동작점의 중앙 영역 전력 몫 (presentation1_estimates.phase 와 같음)
FRAC = 0.10         # 허용 교환 전력 비 (흡수 전력 대비)
P_REF = 300.0       # 코일 전류를 환산할 흡수 전력 [W]


class TwoCoil:
    def __init__(self, omega, L1, L2, M12, R11, R22, R12, X11=0.0, X22=0.0, X12=0.0, Rc1=0.23, Rc2=0.23):
        self.w = omega
        self.L1, self.L2, self.M12 = L1, L2, M12
        self.R11, self.R22, self.R12 = R11, R22, R12
        self.X11, self.X22, self.X12 = X11, X22, X12
        self.Rc1, self.Rc2 = Rc1, Rc2

    @classmethod
    def from_plasma(cls, dZ, prm):
        """two_zone_icp.plasma_coupling 의 ΔZ (2×2) 로 만든다."""
        w = 2 * math.pi * prm.f
        return cls(w, m.loop_self(prm.a1, prm.wire_r), m.loop_self(prm.a2, prm.wire_r), m.mutual(prm.a1, prm.a2, 0.0),
                   dZ[0, 0].real, dZ[1, 1].real, 0.5 * (dZ[0, 1] + dZ[1, 0]).real,
                   dZ[0, 0].imag, dZ[1, 1].imag, 0.5 * (dZ[0, 1] + dZ[1, 0]).imag, prm.R1, prm.R1)

    # --- 전력 (|I1|² = 1 A² 당) -------------------------------------------
    def xm(self) -> float:
        """상호 리액턴스 ωM12 + X'12 [Ω]"""
        return self.w * self.M12 + self.X12

    def p_plasma(self, k: float, phi: float) -> float:
        return self.R11 + k * k * self.R22 + 2 * k * self.R12 * math.cos(phi)

    def p_exch(self, k: float, phi: float) -> float:
        return self.xm() * k * math.sin(phi)

    def p1(self, k: float, phi: float) -> float:
        return self.R11 + k * self.R12 * math.cos(phi) - k * self.xm() * math.sin(phi)

    def p2(self, k: float, phi: float) -> float:
        return k * k * self.R22 + k * self.R12 * math.cos(phi) + k * self.xm() * math.sin(phi)

    def efficiency(self, k: float, phi: float) -> float:
        """η = P_plasma / (P_plasma + 구리 손실), 교재 식 2.57의 꼴"""
        pp = self.p_plasma(k, phi)
        return pp / (pp + self.Rc1 + k * k * self.Rc2)

    def phase_tolerance_deg(self, k: float, phi0: float, frac: float = FRAC) -> float:
        """|P_exch(φ0 + δφ)| ≤ frac·P_plasma(φ0) 를 지키는 δφ [deg] (presentation1_estimates.phase 와 같은 정의)"""
        return math.degrees(math.asin(min(1.0, frac * self.p_plasma(k, phi0) / (abs(self.xm()) * k))))

    def dX(self, k: float, phi: float, with_plasma: bool = True):
        """상대 코일 전류가 만드는 코일 1, 2의 리액턴스 변화 (ωL 대비 비)"""
        x = self.xm() if with_plasma else self.w * self.M12
        z = complex(self.R12 if with_plasma else 0.0, x)
        d1 = (z * k * complex(math.cos(phi), math.sin(phi))).imag / (self.w * self.L1)
        d2 = (z / k * complex(math.cos(phi), -math.sin(phi))).imag / (self.w * self.L2)
        return d1, d2


def center_fraction_k(pc, prm, phi_deg: float, x_c: float = X_C) -> float:
    """중앙 영역 전력 몫이 x_c 가 되는 전류비 k (presentation1_estimates.phase 와 같은 방법)"""
    def f(kk):
        r, fl = pe._flux(pc, np.array([1.0, kk * np.exp(1j * np.deg2rad(phi_deg))]), prm)
        return fl[r <= prm.r_b].sum() / fl.sum() - x_c
    return brentq(f, 0.05, 10.0)


def summarize(c: TwoCoil, k0: float, k180: float) -> dict:
    out = {}
    for name, phi0, k in (("0", 0.0, k0), ("180", math.pi, k180)):
        pp = c.p_plasma(k, phi0)
        p90 = c.p_plasma(k, math.pi / 2)
        d1c, d2c = c.dX(k, phi0, with_plasma=False)
        d1p, d2p = c.dX(k, phi0, with_plasma=True)
        out[name] = dict(k=k, P_plasma=pp, P_vs_90deg=pp / p90, eta=c.efficiency(k, phi0),
                         phase_tol_deg=c.phase_tolerance_deg(k, phi0), exch90_over_P90=abs(c.xm()) * k / p90,
                         I1_A_at_300W=math.sqrt(P_REF / pp), I2_A_at_300W=k * math.sqrt(P_REF / pp),
                         dX1_coil=d1c, dX2_coil=d2c, dX1_plasma=d1p, dX2_plasma=d2p)
    return out


ROWS = (("전류비 k = I2/I1", "k", "%.2f"),
        ("같은 전류에서 흡수 전력 (90° 대비)", "P_vs_90deg", "%.2f"),
        ("효율 η (두 코일 0.23 Ω)", "eta", "%.3f"),
        ("교환 전력 ≤ 10% 위상 허용 오차 [±°]", "phase_tol_deg", "%.1f"),
        ("90° 교환 전력 / 흡수 전력", "exch90_over_P90", "%.2f"),
        ("300 W에서 I1 [A]", "I1_A_at_300W", "%.1f"),
        ("300 W에서 I2 [A]", "I2_A_at_300W", "%.1f"),
        ("안쪽 리액턴스 변화, 코일 항만", "dX1_coil", "%+.2f"),
        ("안쪽 리액턴스 변화, X'12 포함", "dX1_plasma", "%+.2f"),
        ("바깥 리액턴스 변화, 코일 항만", "dX2_coil", "%+.2f"),
        ("바깥 리액턴스 변화, X'12 포함", "dX2_plasma", "%+.2f"))


def _range(vals, fmt):
    lo, hi = min(vals), max(vals)
    return (fmt % lo) if fmt % lo == fmt % hi else "%s – %s" % (fmt % lo, fmt % hi)


def check_against_phase_csv(results) -> None:
    """figures/presentation1_phase.csv (presentation1_estimates.py phase 결과) 와 비교"""
    path = FIG / "presentation1_phase.csv"
    if not path.exists():
        print("\n(비교 생략: figures/presentation1_phase.csv 없음)")
        return
    with path.open(newline="") as f:
        ref = {(float(r["n_m3"]), int(r["p_mTorr"]), int(r["phi_deg"])): r for r in csv.DictReader(f)}
    worst = {}
    for (n, p), s in results:
        for name in ("0", "180"):
            r = ref.get((n, p, int(name)))
            if r is None:
                continue
            for key in ("k", "eta", "phase_tol_deg", "exch90_over_P90", "I1_A_at_300W", "I2_A_at_300W"):
                worst[key] = max(worst.get(key, 0.0), abs(float(r[key]) - s[name][key]))
    print("\npresentation1_phase.csv 와의 최대 차이 (반올림 수준이면 일치): "
          + ", ".join("%s %.3g" % kv for kv in worst.items()))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manual", action="store_true", help="반사 임피던스를 직접 넣는다 (아래 값 사용)")
    ap.add_argument("--R11", type=float, default=1.6, help="안쪽 코일 반사 저항 [Ω] (--manual)")
    ap.add_argument("--R22", type=float, default=4.6, help="바깥 코일 반사 저항 [Ω] (--manual)")
    ap.add_argument("--R12", type=float, default=1.25, help="교차 저항 [Ω] (--manual)")
    ap.add_argument("--X12", type=float, default=-4.9, help="플라즈마 상호 리액턴스 X'12 [Ω] (--manual)")
    ap.add_argument("--k0", type=float, default=2.0, help="0° 동작점의 전류비 (--manual)")
    ap.add_argument("--k180", type=float, default=0.93, help="180° 동작점의 전류비 (--manual)")
    a = ap.parse_args()

    prm = m.Params(**pe.DESIGN)
    w = 2 * math.pi * prm.f
    L1, L2, M12 = m.loop_self(prm.a1, prm.wire_r), m.loop_self(prm.a2, prm.wire_r), m.mutual(prm.a1, prm.a2, 0.0)
    print("회로 상수 (단일 턴, 설계 형상): ωL1 = %.1f Ω, ωL2 = %.1f Ω, ωM12 = %.2f Ω (결합 계수 %.2f)"
          % (w * L1, w * L2, w * M12, M12 / math.sqrt(L1 * L2)))

    if a.manual:
        c = TwoCoil(w, L1, L2, M12, a.R11, a.R22, a.R12, 0.0, 0.0, a.X12, prm.R1, prm.R1)
        s = summarize(c, a.k0, a.k180)
        print("반사 임피던스 (직접 입력): R'11 = %.2f, R'22 = %.2f, R'12 = %.2f, X'12 = %.2f Ω\n" % (a.R11, a.R22, a.R12, a.X12))
        print("   %-36s %10s %10s" % ("항목", "0°", "180°"))
        for label, key, fmt in ROWS:
            print("   %-36s %10s %10s" % (label, fmt % s["0"][key], fmt % s["180"][key]))
        return

    results, sweep = [], []
    for n, Te, p in OPERATING_POINTS:
        pc = m.plasma_coupling(n, Te, p, prm)
        c = TwoCoil.from_plasma(pc["dZ"], prm)
        k0, k180 = center_fraction_k(pc, prm, 0.0), center_fraction_k(pc, prm, 180.0)
        s = summarize(c, k0, k180)
        results.append(((n, p), s))
        print("n = %.0e m⁻³, p = %d mTorr: R'11 = %.2f, R'22 = %.2f, R'12 = %.2f, X'12 = %.2f Ω → ωM12 + X'12 = %.2f Ω, k0 = %.3f, k180 = %.3f"
              % (n, p, c.R11, c.R22, c.R12, c.X12, c.xm(), k0, k180))
        for deg in range(0, 181, 30):
            phi = math.radians(deg)
            sweep.append({"n_m3": n, "p_mTorr": p, "phi_deg": deg, "k": round(k0, 3),
                          "P_plasma": round(c.p_plasma(k0, phi), 3), "P_exch": round(c.p_exch(k0, phi), 3),
                          "P1": round(c.p1(k0, phi), 3), "P2": round(c.p2(k0, phi), 3)})

    print("\n0° vs 180° (중앙 전력 몫 0.20, 네 동작점의 범위)")
    print("   %-36s %16s %16s" % ("항목", "0°", "180°"))
    for label, key, fmt in ROWS:
        print("   %-36s %16s %16s" % (label, _range([s["0"][key] for _, s in results], fmt),
                                      _range([s["180"][key] for _, s in results], fmt)))

    cd = 1.0 / (w * w * M12)
    print("\nM 상쇄 커패시터 (공통 귀환 가지, 백로그 B06): C_d = 1/(ω² M12) = %.2f nF (플라즈마 항 X'12 는 남음)" % (cd * 1e9))

    check_against_phase_csv(results)

    FIG.mkdir(exist_ok=True)
    out = FIG / "two_source_phase.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(sweep[0].keys()))
        wr.writeheader()
        wr.writerows(sweep)
    print("\n위상 스윙 (0° 동작점의 k 고정, |I1|² = 1 A² 당 W) -> figures/%s" % out.name)


if __name__ == "__main__":
    main()
