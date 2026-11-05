"""2-영역 0D 모델의 검증·제어 지도·응답 행렬·민감도 계산.

실행 (저장소 루트에서):
    python sim/run_two_zone.py validate     # KC20 측정값과 비교
    python sim/run_two_zone.py sweep        # 압력 × 커패시턴스 제어 지도
    python sim/run_two_zone.py jacobian     # 응답 행렬 J (00_과제정의.md 3.1절)
    python sim/run_two_zone.py sensitivity  # 가정별 민감도
    python sim/run_two_zone.py all

결과 CSV·그림은 figures/two_zone_*.{csv,png} 에 저장한다.
측정값은 Kim & Chung, Phys. Plasmas 27, 063511 (2020) [KC20] 의 본문 수치와 Fig. 3·8 을
눈금에서 읽은 값(디지타이즈, 로그 축이라 ±15% 정도 오차)이다.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).parent))
import two_zone_icp as tz  # noqa: E402

FIG = Path(__file__).resolve().parent.parent / "figures"
FIG.mkdir(exist_ok=True)
BASE = tz.Params()
C_NONRES = 10.1e-12        # VVC 최솟값 = 비공진 (가정: KC20 은 비공진 C 값을 밝히지 않음)
C_VAC_RES = 139e-12        # 진공 공진 (문헌: KC20 Fig. 2)

# ---------------------------------------------------------------- 측정값 (KC20)
# 급전 전류 I1 [A]: 본문 수치. 150 W, 50 mTorr 는 본문의 η 와 R1 = 0.23 Ω 으로 역산.
MEAS_I1 = {
    (150, 1): (8.5, 4.0),
    (50, 1): (5.9, 2.0),
    (50, 50): (4.5, 2.0),
    (150, 50): (np.sqrt(150 * (1 - 0.93) / 0.23), np.sqrt(150 * (1 - 0.98) / 0.23)),
}
MEAS_ETA = {(150, 1): (0.89, 0.97), (50, 1): (0.83, 0.98), (50, 50): (0.91, 0.98), (150, 50): (0.93, 0.98)}
# 반경 분포 n_e(r) [cm^-3], Fig. 3(50 W)·Fig. 8(150 W) 디지타이즈: (비공진, 공진)
R_PTS = np.array([0, 2, 4, 6, 8, 10, 12, 14, 16, 17.0])
MEAS_PROFILE = {
    (50, 50): ([4.5e9, 4.6e9, 5.5e9, 7.5e9, 9.0e9, 8.5e9, 6.0e9, 3.0e9, 1.5e9, 1.0e9],
               [1.1e9, 1.3e9, 1.8e9, 2.7e9, 4.0e9, 6.0e9, 7.8e9, 6.5e9, 4.0e9, 2.8e9]),
    (50, 1): ([5.5e8, 5.5e8, 5.5e8, 5.3e8, 5.2e8, 4.8e8, 4.5e8, 3.8e8, 3.0e8, 2.3e8],
              [2.0e9, 2.1e9, 2.2e9, 2.3e9, 2.4e9, 2.3e9, 2.2e9, 2.0e9, 1.6e9, 1.3e9]),
    (150, 50): ([1.0e10, 1.15e10, 1.4e10, 1.6e10, 1.75e10, 1.6e10, 1.15e10, 7.0e9, 4.5e9, 4.0e9],
                [9.0e8, 1.0e9, 1.4e9, 2.0e9, 3.2e9, 5.0e9, 7.5e9, 1.15e10, 1.4e10, 1.2e10]),
    (150, 1): ([1.5e10, 1.5e10, 1.5e10, 1.5e10, 1.5e10, 1.45e10, 1.3e10, 1.0e10, 6.5e9, 5.0e9],
               [1.7e10, 1.75e10, 1.85e10, 2.0e10, 2.15e10, 2.2e10, 2.05e10, 1.9e10, 1.6e10, 1.3e10]),
}


def zone_average(r_cm, n, lo, hi):
    """면적 가중 평균 ∫ n r dr / ∫ r dr (선형 보간)."""
    rr = np.linspace(lo, hi, 400)
    nn = np.interp(rr, r_cm, n)
    return np.trapezoid(nn * rr, rr) / np.trapezoid(rr, rr)


def measured_zones(key, which):
    prof = np.array(MEAS_PROFILE[key][which])
    rb = BASE.r_b * 100
    nc = zone_average(R_PTS, prof, 0, rb)
    ne = zone_average(R_PTS, prof, rb, R_PTS[-1])
    nbar = zone_average(R_PTS, prof, 0, R_PTS[-1])
    return nc, ne, nbar


# ---------------------------------------------------------------- 공통 도우미
def find_resonance(P, p, prm, lo=140e-12, hi=230e-12, n=12, init=None):
    """I1 을 최소로 만드는 C (실험의 '공진' 튜닝에 해당) 를 찾는다."""
    Cs = np.linspace(lo, hi, n)
    ops = []
    for C in Cs:
        op = tz.operating_point(P, p, C, prm, init)
        init = op
        ops.append(op)
    i = int(np.argmin([o["I1"] for o in ops]))
    # 이웃 구간에서 한 번 더 세분
    lo2, hi2 = Cs[max(i - 1, 0)], Cs[min(i + 1, n - 1)]
    best = ops[i]
    for C in np.linspace(lo2, hi2, 7):
        op = tz.operating_point(P, p, C, prm, best)
        if op["I1"] < best["I1"]:
            best = op
    return best


def row_of(op, extra=None):
    d = {k: op[k] for k in ("P_in", "p", "C", "I1", "I2", "eta", "edge_frac", "w",
                            "nc", "ne", "nbar", "R", "Tc", "Te", "Pc", "Pe", "delta", "nu")}
    d["C"] *= 1e12
    for k in ("nc", "ne", "nbar"):
        d[k] *= 1e-6
    if extra:
        d.update(extra)
    return d


def write_csv(name, rows):
    path = FIG / name
    with path.open("w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        for r in rows:
            wr.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in r.items()})
    return path


# ---------------------------------------------------------------- 1. 검증
def _validate_case(args):
    (P, p), prm, label = args
    non = tz.operating_point(P, p, C_NONRES, prm)
    vac = tz.operating_point(P, p, C_VAC_RES, prm, non)
    res = find_resonance(P, p, prm, init=vac)
    out = []
    for tag, op, which in (("non-res", non, 0), ("C=139pF", vac, 1), ("res(I1 min)", res, 1)):
        m_nc, m_ne, m_nbar = measured_zones((P, p), which)
        out.append(row_of(op, {"case": label, "state": tag,
                               "I1_meas": MEAS_I1[(P, p)][which], "eta_meas": MEAS_ETA[(P, p)][which],
                               "nbar_meas": m_nbar, "R_meas": m_nc / m_ne}))
    return out


def calibrate_energy_factor(P, p, nbar_target, prm):
    """β_E 를 측정 평균 밀도에 맞춘다 (밀도 정합 변형용)."""
    def f(b):
        return np.log(tz.operating_point(P, p, C_NONRES, replace(prm, energy_factor=b))["nbar"]) - np.log(nbar_target)
    return brentq(f, 0.2, 30.0, xtol=1e-3)


def validate():
    cases = [((150, 1), BASE, "기본"), ((150, 50), BASE, "기본"), ((50, 1), BASE, "기본"), ((50, 50), BASE, "기본")]
    # 밀도 정합 변형: 150 W 비공진 측정 평균 밀도에 β_E 를 맞춘 뒤 같은 압력의 다른 점을 예측
    matched = {}
    for p in (1, 50):
        target = measured_zones((150, p), 0)[2] * 1e6
        b = calibrate_energy_factor(150, p, target, BASE)
        matched[p] = b
        cases += [((150, p), replace(BASE, energy_factor=b), f"밀도 정합 β_E={b:.2f}"),
                  ((50, p), replace(BASE, energy_factor=b), f"밀도 정합 β_E={b:.2f}")]
    with Pool(2) as pool:
        rows = [r for chunk in pool.map(_validate_case, cases) for r in chunk]
    path = write_csv("two_zone_validation.csv", rows)
    print(f"# 검증 ({path.name})\n")
    print("| 조건 | 모델 | 상태 | C [pF] | I1 측정 | I1 모델 | η 측정 | η 모델 | n̄ 측정 [cm⁻³] | n̄ 모델 | R 측정 | R 모델 | 가장자리 전력비 |")
    print("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        print(f"| {r['P_in']:.0f} W, {r['p']:g} mTorr | {r['case']} | {r['state']} | {r['C']:.0f} | {r['I1_meas']:.1f} | {r['I1']:.2f} | "
              f"{r['eta_meas']:.2f} | {r['eta']:.3f} | {r['nbar_meas']:.2e} | {r['nbar']:.2e} | {r['R_meas']:.2f} | {r['R']:.2f} | {r['edge_frac']:.2f} |")
    print("\n밀도 정합 β_E:", {k: round(v, 3) for k, v in matched.items()})
    return rows, matched


# ---------------------------------------------------------------- 2. 제어 지도
PRESSURES = [1, 2, 3, 5, 7, 10, 15, 20, 30, 50]
C_GRID = [10.1, 60, 100, 130, 145, 155, 162, 168, 174, 180, 186, 192, 200, 215, 240, 300]


def _sweep_pressure(args):
    p, prm, P = args
    rows, init = [], None
    for C in C_GRID:
        op = tz.operating_point(P, p, C * 1e-12, prm, init)
        init = op
        rows.append(row_of(op))
    return rows


def sweep(prm=BASE, P=150.0, name="two_zone_sweep.csv", pressures=PRESSURES, quiet=False):
    with Pool(2) as pool:
        rows = [r for chunk in pool.map(_sweep_pressure, [(p, prm, P) for p in pressures]) for r in chunk]
    write_csv(name, rows)
    summary = []
    for p in pressures:
        sub = [r for r in rows if r["p"] == p]
        non = sub[0]
        rmin = min(sub, key=lambda r: r["R"])
        rmax = max(sub, key=lambda r: r["R"])
        summary.append({"p": p, "R_nonres": non["R"], "R_min": rmin["R"], "C_at_Rmin": rmin["C"],
                        "contrast": non["R"] / rmin["R"], "R_max": rmax["R"],
                        "nbar_nonres": non["nbar"], "nbar_at_Rmin": rmin["nbar"],
                        "edge_frac_max": max(r["edge_frac"] for r in sub), "w": non["w"]})
    write_csv(name.replace(".csv", "_summary.csv"), summary)
    if not quiet:
        print(f"\n# 제어 지도 요약 ({name})\n")
        print("| p [mTorr] | w | R 비공진 | R 최소 | C @R최소 [pF] | 대비 R_non/R_min | n̄ 변화 @R최소 | 가장자리 전력비 최대 |")
        print("|---:|---:|---:|---:|---:|---:|---:|---:|")
        for s in summary:
            print(f"| {s['p']:g} | {s['w']:.2f} | {s['R_nonres']:.2f} | {s['R_min']:.2f} | {s['C_at_Rmin']:.0f} | "
                  f"{s['contrast']:.2f} | {s['nbar_at_Rmin'] / s['nbar_nonres'] - 1:+.0%} | {s['edge_frac_max']:.2f} |")
    return rows, summary


# ---------------------------------------------------------------- 3. 응답 행렬
def _jac_case(args):
    p, prm, P0, C0 = args
    base = tz.operating_point(P0, p, C0, prm)
    dlnP, dC = 0.05, 2e-12
    pts = {}
    for key, (P, C) in {"P+": (P0 * np.exp(dlnP), C0), "P-": (P0 * np.exp(-dlnP), C0),
                        "C+": (P0, C0 + dC), "C-": (P0, C0 - dC)}.items():
        pts[key] = tz.operating_point(P, p, C, prm, base)
    y = {k: np.array([np.log(o["nbar"]), np.log(o["R"])]) for k, o in pts.items()}
    J = np.column_stack([(y["P+"] - y["P-"]) / (2 * dlnP), (y["C+"] - y["C-"]) / (2 * dC * 1e12)])
    # 열마다 비대각/대각 비 (단위와 무관): 전력 열은 R 누설, C 열은 n̄ 누설
    leak_P = abs(J[1, 0]) / abs(J[0, 0])
    leak_C = abs(J[0, 1]) / abs(J[1, 1])
    return {"p": p, "C0": C0 * 1e12, "R0": base["R"], "nbar0": base["nbar"] * 1e-6,
            "dlnn_dlnP": J[0, 0], "dlnR_dlnP": J[1, 0], "dlnn_dC": J[0, 1], "dlnR_dC": J[1, 1],
            "leak_P": leak_P, "leak_C": leak_C}


def jacobian(prm=BASE, P0=150.0, C0=162e-12, pressures=(1, 5, 10, 20, 50)):
    with Pool(2) as pool:
        rows = pool.map(_jac_case, [(p, prm, P0, C0) for p in pressures])
    write_csv("two_zone_jacobian.csv", rows)
    print(f"\n# 응답 행렬 J (P0 = {P0:.0f} W, C0 = {C0 * 1e12:.0f} pF), y = [ln n̄, ln R], u = [ln P, C(pF)]\n")
    print("| p [mTorr] | ∂ln n̄/∂ln P | ∂ln R/∂ln P | ∂ln n̄/∂C [/pF] | ∂ln R/∂C [/pF] | 전력 열 누설 | C 열 누설 |")
    print("|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        print(f"| {r['p']:g} | {r['dlnn_dlnP']:.3f} | {r['dlnR_dlnP']:+.3f} | {r['dlnn_dC']:+.4f} | {r['dlnR_dC']:+.4f} | "
              f"{r['leak_P']:.2f} | {r['leak_C']:.2f} |")
    return rows


# ---------------------------------------------------------------- 4. 민감도
def sensitivity():
    variants = {
        "기본": BASE,
        "r_b = 12 cm": replace(BASE, r_b=0.12),
        "r_b = 15 cm": replace(BASE, r_b=0.15),
        "Δ_h = 4 cm (λε 2배와 같음)": replace(BASE, delta_heat=0.04),
        "Δ_h = 16 cm (λε 절반과 같음)": replace(BASE, delta_heat=0.16),
        "비국소 브리지 끔": replace(BASE, nonlocal_bridge=False),
    }
    # z_gap = 1.5 cm 는 κ_ν 를 다시 보정해야 같은 측정점을 재현한다
    k15 = tz.calibrate_nu_factor(8.5, 150, 1, C_NONRES, replace(BASE, z_gap=0.015), lo=12, hi=30)
    variants[f"z_gap = 1.5 cm (κ_ν={k15:.1f} 재보정)"] = replace(BASE, z_gap=0.015, nu_factor=k15)
    out = []
    for name, prm in variants.items():
        _, summ = sweep(prm, name="_tmp_sens.csv", pressures=[1, 10, 50], quiet=True)
        s = {d["p"]: d for d in summ}
        out.append({"variant": name,
                    "R_non_1": s[1]["R_nonres"], "contrast_1": s[1]["contrast"],
                    "R_non_10": s[10]["R_nonres"], "contrast_10": s[10]["contrast"],
                    "R_non_50": s[50]["R_nonres"], "contrast_50": s[50]["contrast"],
                    "nbar_50": s[50]["nbar_nonres"]})
        print(f"  done: {name}", flush=True)
    (FIG / "_tmp_sens.csv").unlink(missing_ok=True)
    (FIG / "_tmp_sens_summary.csv").unlink(missing_ok=True)
    write_csv("two_zone_sensitivity.csv", out)
    print("\n# 민감도 (150 W, 대비 = R_비공진 / R_최소)\n")
    print("| 변형 | R 비공진 1 mTorr | 대비 1 | R 비공진 10 | 대비 10 | R 비공진 50 | 대비 50 |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for r in out:
        print(f"| {r['variant']} | {r['R_non_1']:.2f} | {r['contrast_1']:.2f} | {r['R_non_10']:.2f} | {r['contrast_10']:.2f} | "
              f"{r['R_non_50']:.2f} | {r['contrast_50']:.2f} |")
    return out


# ---------------------------------------------------------------- 그림
def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = list(csv.DictReader((FIG / "two_zone_sweep.csv").open()))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    shown = [1, 5, 10, 20, 50]
    cmap = plt.get_cmap("Blues")
    for i, p in enumerate(shown):
        sub = [r for r in rows if float(r["p"]) == p and float(r["C"]) > 50]
        ax[0].plot([float(r["C"]) for r in sub], [float(r["R"]) for r in sub], "o-", ms=3,
                   color=cmap(0.35 + 0.6 * i / (len(shown) - 1)), label=f"{p} mTorr")
    ax[0].axvline(139, color="0.6", ls="--", lw=0.8)
    ax[0].set_xlabel("C [pF]")
    ax[0].set_ylabel("R = n_c / n_e")
    ax[0].set_title("Density ratio vs passive-antenna capacitance (150 W)")
    ax[0].legend(frameon=False, fontsize=8)
    summ = list(csv.DictReader((FIG / "two_zone_sweep_summary.csv").open()))
    ax[1].semilogx([float(s["p"]) for s in summ], [float(s["contrast"]) for s in summ], "o-", color="C0")
    ax[1].set_xlabel("p [mTorr]")
    ax[1].set_ylabel("R_nonres / R_min")
    ax[1].set_title("Controllable range of R")
    for a in ax:
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(FIG / "two_zone_control.png", dpi=150)
    print(f"그림 저장: {FIG / 'two_zone_control.png'}")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("validate", "all"):
        validate()
    if what in ("sweep", "all"):
        sweep()
        plot()
    if what in ("jacobian", "all"):
        jacobian()
    if what in ("sensitivity", "all"):
        sensitivity()
    if what == "plot":
        plot()
