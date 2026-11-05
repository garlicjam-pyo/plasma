"""1차 발표(주제 3) 문서의 수치를 다시 만드는 스크립트.

claude.ai 문서 "주제 3 · 1차 발표 정리"에 옮긴 수치의 출처다. 실행하면 figures/presentation1_*.csv 를 쓴다.

    python sim/presentation1_estimates.py scales      # λε, w, g_R, 확산 누설, 자기장 기준값 (식만)
    python sim/presentation1_estimates.py phase       # 독립 전원 2대의 위상 0°/180° 비교 (회로·장, 고정 밀도)
    python sim/presentation1_estimates.py jacobian    # 영역 전력을 직접 지정할 때의 J (플라즈마만)
    python sim/presentation1_estimates.py range       # 중앙 전력 몫 2–98%로 낼 수 있는 R 범위
    python sim/presentation1_estimates.py all

설계 형상: R = 20 cm, L = 10 cm, 안쪽 코일 8 cm, 바깥 코일 15.5 cm, 영역 경계 12 cm (가정).
코일은 단일 턴 루프, 플라즈마는 창 아래 균일 반공간(Dodd–Deeds 해)이다 (가정).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parent))
import two_zone_icp as m  # noqa: E402

FIG = Path(__file__).resolve().parent.parent / "figures"
DESIGN = dict(R=0.20, L=0.10, a1=0.08, a2=0.155, r_b=0.12)
DELTA = 0.075          # 코일 간격 Δ [m] (설계)
TE_REF = 2.5           # 자기장 기준값 계산용 전자 온도 [eV] (가정)
P_REF = 300.0          # 코일 전류를 환산할 흡수 전력 [W] (가정)
X_SEL = (0.05, 0.07)   # 바깥 코일만 켜도 중앙에 떨어지는 전력 몫 (코일 선택도 0.93–0.95에서, 계산)
ME, QE = 9.109e-31, 1.602e-19


def _write(name: str, rows: list[dict]) -> None:
    FIG.mkdir(exist_ok=True)
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(FIG / name, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"-> figures/{name}")


# ------------------------------------------------------------------ 식만으로 계산하는 척도
def scales() -> None:
    rows = []
    for p in (1, 5, 10, 15, 20, 30):
        lam = m.lambda_eps(p)
        w = np.exp(-DELTA / lam)
        nu_m = m.n_gas(p) * m.k_el(TE_REF)
        b1 = ME * nu_m / QE * 1e4                       # ω_ce = ν_m 인 자기장 [G]
        x = np.sqrt(max((lam / DELTA) ** 2 - 1.0, 0.0))  # λε⊥ = Δ 가 되는 ω_ce/ν_m
        rows.append({"p_mTorr": p, "lambda_eps_cm": round(lam * 100, 2), "w": round(w, 3),
                     "g_R": round(1 - w, 3), "B1_G": round(b1, 3), "B_for_lambda_perp_eq_Delta_G": round(x * b1, 2)})
    for r in rows:
        print(r)
    _write("presentation1_scales.csv", rows)
    for L in (0.06, 0.08, 0.10, 0.12):
        print(f"L = {L*100:.0f} cm: l = L/pi = {L/np.pi*100:.2f} cm, leak = exp(-pi*Delta/L) = {np.exp(-np.pi*DELTA/L):.3f}")
    print(f"p* = 119/Delta = {119/(DELTA*100):.1f} mTorr, g_R = 0.5 at {119*np.log(2)/(DELTA*100):.1f} mTorr")
    print(f"B_ECR(13.56 MHz) = {ME*2*np.pi*13.56e6/QE*1e4:.2f} G")
    te = TE_REF
    print(f"Te = {te} eV: K_iz = {m.k_iz(te):.3e}, K_ex = {m.k_ex(te):.3e}, K_el = {m.k_el(te):.3e} m^3/s, "
          f"e_c = {m.e_c(te):.1f} V, e_T = {m.e_c(te) + m.e_wall(te):.1f} V")


# ------------------------------------------------------------------ 위상 비교 (고정 밀도)
def _flux(pc, I, prm):
    r, dr = pc["r"], pc["dr"]
    fl = np.real((I @ pc["Et"]) * np.conj(I @ pc["Hr"])) * 2 * np.pi * r * dr
    return r, fl


def phase() -> None:
    prm = m.Params(**DESIGN)
    w = 2 * np.pi * prm.f
    M12 = m.mutual(prm.a1, prm.a2, 0.0)
    L1, L2 = m.loop_self(prm.a1, prm.wire_r), m.loop_self(prm.a2, prm.wire_r)
    # 코일 저항 R1, R2 는 KC20 값을 그대로 쓴다 (가정)
    print(f"L1 = {L1*1e9:.0f} nH, L2 = {L2*1e9:.0f} nH, M12 = {M12*1e9:.0f} nH, k_c = {M12/np.sqrt(L1*L2):.3f}, wM12 = {w*M12:.2f} ohm")
    rows = []
    # 비교 동작점: 중앙 영역 전력 몫 X_C (R ≈ 1 근처, jacobian()의 x_at_R1 = 0.11–0.22 참고)
    X_C = 0.20
    for n, Te, p in ((3e16, 2.5, 10), (3e16, 2.2, 20), (1e17, 2.5, 10), (1e17, 2.2, 20)):
        pc = m.plasma_coupling(n, Te, p, prm)
        dZ = pc["dZ"]
        for name, I in (("inner", np.array([1.0, 0])), ("outer", np.array([0, 1.0]))):
            r, fl = _flux(pc, I, prm)
            fc = fl[r <= prm.r_b].sum() / fl.sum()
            print(f"  n={n:.0e} p={p}: {name} coil alone -> center fraction {fc:.3f}")
        for phi in (0, 180):
            def f_center(kk, nn=n):
                pcc = pc if nn == n else m.plasma_coupling(nn, Te, p, prm)
                rr, ff = _flux(pcc, np.array([1.0, kk * np.exp(1j * np.deg2rad(phi))]), prm)
                return ff[rr <= prm.r_b].sum() / ff.sum()

            def ln_rpow(kk, nn=n):
                f_c = f_center(kk, nn)
                return np.log((f_c / prm.Vc) / ((1 - f_c) / prm.Ve))

            k = brentq(lambda kk: f_center(kk) - X_C, 0.05, 10.0)
            I = np.array([1.0, k * np.exp(1j * np.deg2rad(phi))])
            I90 = np.array([1.0, 1j * k])
            Pp = float(np.real(np.conj(I) @ dZ @ I))
            P90 = float(np.real(np.conj(I90) @ dZ @ I90))
            r, fl = _flux(pc, I, prm)
            band = (r > prm.r_b - 0.03) & (r < prm.r_b + 0.03)
            sens = (ln_rpow(k * 1.1) - ln_rpow(k / 1.1)) / (2 * np.log(1.1))
            dens = (ln_rpow(k, n * 1.1) - ln_rpow(k, n / 1.1)) / (2 * np.log(1.1))
            # 교환 전력의 상호 리액턴스는 코일 상호 인덕턴스 + 플라즈마 반사 상호 리액턴스 X'12 (2026-11-05 검토로 수정:
            # 처음 판은 ωM12만 써서 교환 전력을 2–4배 크게, 위상 허용 오차를 좁게 냈다)
            X12 = float(np.imag(dZ[0, 1]))
            x_mut = abs(w * M12 + X12)
            tol = np.degrees(np.arcsin(min(1.0, 0.1 * Pp / (x_mut * k))))
            # 효율은 두 코일 모두 정합기로 구동하는 구조라 바깥 코일도 R1(0.23 Ω, KC20 측정값)으로 둔다 (가정)
            eta = Pp / (Pp + prm.R1 * (1 + k**2))
            I1_300 = np.sqrt(P_REF / Pp)
            rows.append({"n_m3": n, "p_mTorr": p, "phi_deg": phi, "center_fraction": X_C, "k": round(k, 3),
                         "P_vs_90deg": round(Pp / P90, 3), "eta": round(eta, 3),
                         "band_fraction": round(fl[band].sum() / fl.sum(), 3),
                         "dlnRpow_dlnk": round(sens, 2), "dlnRpow_dlnn": round(dens, 3),
                         "X12_ohm": round(X12, 2), "phase_tol_deg": round(tol, 1),
                         "exch90_over_P90": round(x_mut * k / P90, 2),
                         "I1_A_at_300W": round(I1_300, 1), "I2_A_at_300W": round(k * I1_300, 1)})
    for r in rows:
        print(r)
    _write("presentation1_phase.csv", rows)


# ------------------------------------------------------------------ 플라즈마만의 응답 (영역 전력 직접 지정)
def _out(P, x, p, prm):
    Pc, Pe = m.bridge(x * P, (1 - x) * P, p, prm)
    z = m.solve_zones(Pc, Pe, p, prm)
    nbar = (z["nc"] * prm.Vc + z["ne"] * prm.Ve) / prm.V
    return np.log(nbar), np.log(z["nc"] / z["ne"]), z


def jacobian() -> None:
    rows = []
    for name, prm in (("design", m.Params(**DESIGN)), ("KC20", m.Params())):
        for p in (5, 10, 20, 30):
            P = 300.0
            try:
                xs = brentq(lambda x: _out(P, x, p, prm)[1], 0.02, 0.98, xtol=1e-4)
                x_note = round(xs, 3)
            except ValueError:
                xs, x_note = prm.Vc / prm.V, "unreachable"
            dP, dx = 0.05, 0.02
            a, b = _out(P * np.exp(dP), xs, p, prm), _out(P * np.exp(-dP), xs, p, prm)
            c, d = _out(P, xs + dx, p, prm), _out(P, xs - dx, p, prm)
            J = np.array([[(a[0] - b[0]) / (2 * dP), (c[0] - d[0]) / (2 * dx)],
                          [(a[1] - b[1]) / (2 * dP), (c[1] - d[1]) / (2 * dx)]])
            R_eq = np.exp(_out(P, prm.Vc / prm.V, p, prm)[1])   # 전력 밀도가 같을 때의 R
            rows.append({"geometry": name, "p_mTorr": p, "x_at_R1": x_note,
                         "J11": round(J[0, 0], 3), "J12": round(J[0, 1], 3), "J21": round(J[1, 0], 4), "J22": round(J[1, 1], 3),
                         "leak_x": round(abs(J[0, 1] / J[1, 1]), 3), "R_equal_power_density": round(R_eq, 2)})
    for r in rows:
        print(r)
    _write("presentation1_jacobian.csv", rows)


def r_range() -> None:
    prm = m.Params(**DESIGN)
    rows = []
    for p in (5, 10, 15, 20, 30):
        lo, hi = np.exp(_out(300.0, 0.02, p, prm)[1]), np.exp(_out(300.0, 0.98, p, prm)[1])
        row = {"p_mTorr": p, "R_min": round(lo, 2), "R_max": round(hi, 2)}
        # 코일 선택도를 넣은 하한: 중앙 몫이 X_SEL 아래로 내려가지 못한다 (2026-11-05 검토로 추가)
        for xs_ in X_SEL:
            row[f"R_min_x{xs_}"] = round(float(np.exp(_out(300.0, xs_, p, prm)[1])), 2)
        xs = {}
        for Rt in (0.8, 1.0, 1.2):
            try:
                xs[Rt] = brentq(lambda x: _out(300.0, x, p, prm)[1] - np.log(Rt), 0.02, 0.98, xtol=1e-4)
                row[f"x_R{Rt}"] = round(xs[Rt], 3)
            except ValueError:
                row[f"x_R{Rt}"] = ""
        if 0.8 in xs and 1.2 in xs:
            row["nbar_0.8_over_1.2"] = round(np.exp(_out(300.0, xs[0.8], p, prm)[0] - _out(300.0, xs[1.2], p, prm)[0]), 3)
        rows.append(row)
        print(row)
    _write("presentation1_r_range.csv", rows)


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in (("scales", scales), ("phase", phase), ("jacobian", jacobian), ("range", r_range)):
        if task in (name, "all"):
            print(f"== {name}")
            fn()
