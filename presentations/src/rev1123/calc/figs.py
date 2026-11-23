"""발표 근거 그림 (2026-11-23 개정판). 모델: sim/hybrid (기준 300 W, Ar 10 mTorr, 13.56 MHz)."""
import sys, json, numpy as np
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../sim"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, Circle
from hybrid.config import Config
from hybrid.coupled import solve_point
from hybrid.validate import solve_pair

OUT = sys.argv[1]
KR = "Noto Sans CJK KR"
plt.rcParams.update({"font.family": [KR, "DejaVu Sans"], "mathtext.fontset": "cm", "font.size": 10,
                     "axes.linewidth": 0.8, "axes.edgecolor": "#3B4658", "axes.labelcolor": "#222222",
                     "xtick.color": "#3B4658", "ytick.color": "#3B4658", "xtick.labelsize": 9, "ytick.labelsize": 9,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                     "legend.fontsize": 8.5, "axes.unicode_minus": False})
BLUE, ORANGE, NAVY, GRAY, INK = "#3366CC", "#D9622B", "#303399", "#8C93A3", "#222222"
BLUE_L, ORANGE_L = "#DCE6F7", "#F8E1D4"
base = Config(); G = base.geom
log = {}

def zones(ax, ymax, alpha=1.0):
    ax.axvspan(0, G.r_c * 100, color=BLUE_L, alpha=alpha, lw=0, zorder=0)
    ax.axvspan(G.r_1 * 100, G.r_2 * 100, color=ORANGE_L, alpha=alpha, lw=0, zorder=0)

def save(fig, name):
    fig.savefig(f"{OUT}/{name}.png", dpi=300, bbox_inches="tight", pad_inches=0.03, transparent=False, facecolor="white")
    plt.close(fig)

# ---------------------------------------------------------------- Fig. 1 챔버 반단면 (축척 일치)
def fig_chamber():
    fig, ax = plt.subplots(figsize=(4.3, 2.55))
    R, L, win, zc = G.R * 100, G.L * 100, G.window * 100, G.z_coil * 100
    ax.add_patch(Rectangle((0, 0), R, L, fc="#EEF0FA", ec="none"))
    ax.add_patch(Rectangle((0, L), R, win, fc="#D5DAE3", ec="none"))
    ax.plot([0, R, R], [0, 0, L + win], color=INK, lw=1.4)
    ax.plot([0, 0], [-0.2, zc + 1.1], color=GRAY, lw=0.8, ls=(0, (4, 3)))
    ax.text(0.3, zc + 0.75, "축 $r=0$", fontsize=8, color=GRAY, va="center")
    ax.add_patch(Rectangle((0, 0), G.R_w * 100, 0.25, fc="#5F6779", ec="none"))
    ax.text(7.5, 0.52, "웨이퍼 (300 mm)", ha="center", va="center", fontsize=7.5, color="#5F6779")
    ax.text(R / 2, L + win / 2, "유전체 창", ha="center", va="center", fontsize=8.5, color="#3B4658")
    ax.text(R - 0.4, L / 2 + 0.4, "플라즈마", ha="right", va="center", fontsize=9, color=NAVY)
    for r0 in G.r_in:
        ax.add_patch(Circle((r0 * 100, zc), 0.42, fc=BLUE, ec="white", lw=0.8))
    for r0 in G.r_out:
        ax.add_patch(Circle((r0 * 100, zc), 0.42, fc=ORANGE, ec="white", lw=0.8))
    ax.text(np.mean(G.r_in) * 100, zc + 0.75, "안쪽 코일", ha="center", fontsize=8.5, color=BLUE)
    ax.text(np.mean(G.r_out) * 100, zc + 0.75, "바깥쪽 코일", ha="center", fontsize=8.5, color=ORANGE)
    zw = G.z_w * 100
    ax.plot([0, G.R_w * 100], [zw, zw], color=INK, lw=0.8, ls=(0, (3, 2)))
    ax.text(G.R_w * 100 + 0.3, zw, "$z_w$ = 1 cm", va="center", fontsize=8)
    ax.add_patch(Rectangle((0, zw - 0.12), G.r_c * 100, 0.24, fc=BLUE, ec="none"))
    ax.add_patch(Rectangle((G.r_1 * 100, zw - 0.12), (G.r_2 - G.r_1) * 100, 0.24, fc=ORANGE, ec="none"))
    ax.text(G.r_c * 100 / 2, zw + 0.62, "$n_c$ (0–5 cm)", ha="center", fontsize=8.5, color=BLUE)
    ax.text((G.r_1 + G.r_2) * 50, zw + 0.62, "$n_\\mathrm{edge}$ (12–14.5 cm)", ha="center", fontsize=8.5, color=ORANGE)
    ax.set_xlim(-0.3, R + 0.3); ax.set_ylim(-0.4, zc + 1.4)
    ax.set_aspect("equal")
    ax.set_xticks([0, 5, 10, 15, 20]); ax.set_yticks([0, 2, 4, 6, 8])
    ax.set_xlabel("$r$ [cm]"); ax.set_ylabel("$z$ [cm]")
    save(fig, "fig_chamber")

# ---------------------------------------------------------------- Fig. 2 개념도: 크기 vs 모양
def fig_concept():
    r = np.linspace(0, 15, 400)
    def mean(n): return np.trapezoid(n * r, r) / np.trapezoid(r, r)
    def rho(n):
        c = (r <= 5); e = (r >= 12) & (r <= 14.5)
        return np.trapezoid((n * r)[c], r[c]) / np.trapezoid(r[c], r[c]) / (np.trapezoid((n * r)[e], r[e]) / np.trapezoid(r[e], r[e]))
    a = 1.0 - 0.30 * (r / 15) ** 2 - 0.05 * (r / 15) ** 6
    b = 0.86 + 0.26 * np.exp(-((r - 12.2) / 3.6) ** 2)
    a /= mean(a); b /= mean(b)
    fig, axs = plt.subplots(2, 1, figsize=(3.7, 3.45), sharex=True)
    ax = axs[0]; zones(ax, 2)
    ax.plot(r, a, color=NAVY, lw=1.8, label="$P$")
    ax.plot(r, 1.6 * a, color=NAVY, lw=1.8, ls=(0, (4, 2)), label="$1.6P$")
    ax.text(0.02, 0.97, "(a)", transform=ax.transAxes, fontsize=10, fontweight="bold", va="top")
    ax.text(0.98, 0.04, f"$\\bar n_w$ 1.6배, $\\rho$ = {rho(a):.2f} 그대로", transform=ax.transAxes, ha="right", fontsize=8.5)
    ax.legend(loc="upper right", ncol=2, handlelength=2.0); ax.set_ylim(0, 2.3); ax.set_ylabel("$n_w(r)$ (상대값)")
    ax = axs[1]; zones(ax, 2)
    ax.plot(r, a, color=NAVY, lw=1.8, label=f"$\\rho$ = {rho(a):.2f}")
    ax.plot(r, b, color="#7A3FA0", lw=1.8, ls=(0, (4, 2)), label=f"$\\rho$ = {rho(b):.2f}")
    ax.text(0.02, 0.97, "(b)", transform=ax.transAxes, fontsize=10, fontweight="bold", va="top")
    ax.text(0.98, 0.04, "$\\bar n_w$ 그대로, $\\rho$만 변화", transform=ax.transAxes, ha="right", fontsize=8.5)
    ax.legend(loc="upper right", ncol=2, handlelength=2.0); ax.set_ylim(0, 1.6); ax.set_ylabel("$n_w(r)$ (상대값)")
    ax.set_xlabel("$r$ [cm]"); ax.set_xlim(0, 15)
    fig.tight_layout(h_pad=0.5)
    log["concept_rho"] = [rho(a), rho(b)]
    save(fig, "fig_concept")

# ---------------------------------------------------------------- Fig. 3 단일 코일: r만으로
def norm_shape(S, g):
    return S / ((S * g.area).sum() / g.area.sum())

def fig_single():
    fig, axs = plt.subplots(1, 2, figsize=(8.6, 2.55))
    ax = axs[0]; zones(ax, 3)
    ref = solve_point(base.with_op(coil_mode="single_series")); g = ref.grid; rr = g.r * 100
    s_ref = norm_shape(ref.heating.S, g)
    cases = [("300 W, 10 mTorr (기준)", dict(), NAVY, "-", 2.0),
             ("100 W", dict(P_tot=100), NAVY, (0, (1, 1.5)), 1.4), ("1000 W", dict(P_tot=1000), NAVY, (0, (5, 2)), 1.4),
             ("5 mTorr", dict(p_mtorr=5), "#7A3FA0", (0, (1, 1.5)), 1.4), ("50 mTorr", dict(p_mtorr=50), "#7A3FA0", (0, (5, 2)), 1.4)]
    tvs = []
    for lab, kw, col, ls, lw in cases:
        s = solve_point(base.with_op(coil_mode="single_series", **kw)) if kw else ref
        sh = norm_shape(s.heating.S, g)
        tvs.append(0.5 * np.abs(sh / g.area.sum() * 1 - s_ref / g.area.sum()).dot(g.area))
        ax.plot(rr, sh, color=col, ls=ls, lw=lw, label=lab)
    ax.set_xlim(0, 21)
    ax.set_xlabel("$r$ [cm]"); ax.set_ylabel("$S(r)\\,/\\,\\langle S\\rangle$")
    ax.text(-0.02, 1.02, "(a)", transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")
    ax.set_ylim(0, 3.05)
    hs, ls_ = ax.get_legend_handles_labels()
    from matplotlib.lines import Line2D
    blank = Line2D([], [], alpha=0)
    order = [(hs[0], ls_[0]), (blank, " "), (hs[1], ls_[1]), (hs[2], ls_[2]), (hs[3], ls_[3]), (hs[4], ls_[4])]
    ax.legend([h for h, _ in order], [l for _, l in order], loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=3,
              fontsize=7.2, handlelength=2.2, columnspacing=1.0, labelspacing=0.2)
    log["single_shape_tv_max"] = float(max(tvs))
    ax = axs[1]; zones(ax, 3)
    rows = []
    for p, col in ((10, NAVY), (50, "#7A3FA0")):
        s1, s2 = solve_pair(base.with_op(coil_mode="single_series", p_mtorr=p))
        g1 = s1.grid
        w1 = s1.state.wafer_profile(s1.cfg); w2 = s2.state.wafer_profile(s2.cfg)
        ax.plot(g1.r * 100, w1 / 1e16, color=col, lw=2.0)
        ax.plot(g1.r * 100, w2 / 1e16, color=col, lw=1.3, ls=(0, (4, 2)))
        rows.append(dict(p=p, rho1=s1.metrics.rho, rho2=s2.metrics.rho, nbar1=s1.metrics.n_bar, nbar2=s2.metrics.n_bar,
                         t1=s1.timing["total"], t2=s2.timing["total"]))
    ax.plot([], [], color="#3B4658", lw=2.0, label="$r$ 모델")
    ax.plot([], [], color="#3B4658", lw=1.3, ls=(0, (4, 2)), label="$(r,z)$ 모델")
    ax.text(12.8, 1.5, "10 mTorr", color=NAVY, fontsize=8.5)
    ax.text(10.4, 13.9, "50 mTorr", color="#7A3FA0", fontsize=8.5, ha="center")
    ax.set_xlim(0, 21); ax.set_ylim(0, 15.5)
    ax.set_xlabel("$r$ [cm]"); ax.set_ylabel("$n(r, z_w)$ [$10^{16}$ m$^{-3}$]")
    ax.text(-0.02, 1.02, "(b)", transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")
    ax.legend(loc="lower left", bbox_to_anchor=(0.03, 0.02), fontsize=7.8, handlelength=2.6)
    log["transport_pairs"] = rows
    fig.tight_layout(w_pad=2.0)
    save(fig, "fig_single")

# ---------------------------------------------------------------- Fig. 4 이중 코일: 전자기장에 z
def fig_dual():
    fig = plt.figure(figsize=(8.6, 2.45))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1.0], wspace=0.28)
    ax = fig.add_subplot(gs[0])
    s = solve_point(base); g = s.grid
    R, L, win, zc = G.R * 100, G.L * 100, G.window * 100, G.z_coil * 100
    Ai, Ao = np.abs(s.unit.A_in), np.abs(s.unit.A_out)
    zz = g.z * 100; rr = g.r * 100
    Ri, Zi = np.meshgrid(rr, zz)
    mask = zz <= zc + 0.01
    for A, col in ((Ai, BLUE), (Ao, ORANGE)):
        a = A / A[mask].max()
        cs = ax.contour(Ri, Zi, a, levels=[0.1, 0.2, 0.4, 0.7], colors=col, linewidths=[0.8, 1.0, 1.2, 1.4])
    ax.add_patch(Rectangle((0, L), R, win, fc="#D5DAE3", ec="none", zorder=0))
    ax.add_patch(Rectangle((0, 0), R, L, fc="#F3F4FA", ec="none", zorder=0))
    ax.axhline(L, color="#5F6779", lw=0.6); ax.axhline(L + win, color="#5F6779", lw=0.6)
    for r0 in G.r_in: ax.add_patch(Circle((r0 * 100, zc), 0.35, fc=BLUE, ec="white", lw=0.6, zorder=3))
    for r0 in G.r_out: ax.add_patch(Circle((r0 * 100, zc), 0.35, fc=ORANGE, ec="white", lw=0.6, zorder=3))
    ax.text(0.4, L + win / 2, "창", va="center", fontsize=8, color="#3B4658")
    ax.text(0.4, 4.9, "플라즈마", fontsize=8, color=NAVY)
    ax.annotate("", xy=(19.6, L), xytext=(19.6, zc), arrowprops=dict(arrowstyle="<->", color=INK, lw=0.8))
    ax.text(19.9, (L + zc) / 2, "$d$", fontsize=9, va="center")
    ax.set_xlim(0, R); ax.set_ylim(0, zc + 1.0); ax.set_aspect("equal")
    ax.set_xlabel("$r$ [cm]"); ax.set_ylabel("$z$ [cm]")
    ax.text(-0.02, 1.02, "(a)", transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")
    ax.plot([], [], color=BLUE, label="안쪽 코일 1 A"); ax.plot([], [], color=ORANGE, label="바깥쪽 코일 1 A")
    ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.0), fontsize=7.6)
    ax.text(0.4, 1.3, "등고선: 각 코일 장의 최댓값 대비 0.1, 0.2, 0.4, 0.7", fontsize=7.2, color="#5F6779")
    ax = fig.add_subplot(gs[1]); zones(ax, 3); ax.set_box_aspect((zc + 1.0) / R * 1.25)
    rows = []
    for gap, ls, lw in ((0.005, "-", 2.0), (0.03, (0, (4, 2)), 1.4)):
        cfg = base.with_geom(coil_gap=gap); s = solve_point(cfg); g = s.grid
        Nzp = s.heating.p_abs.shape[0]; dz = g.dz[:Nzp]; w = cfg.op.omega
        Si = (0.5 * s.unit.re_sigma * (w * np.abs(s.unit.A_in[:Nzp])) ** 2 * dz[:, None]).sum(0)
        So = (0.5 * s.unit.re_sigma * (w * np.abs(s.unit.A_out[:Nzp])) ** 2 * dz[:, None]).sum(0)
        si = Si / (Si * g.area).sum(); so = So / (So * g.area).sum()
        d = (gap + G.window) * 100
        ax.plot(g.r * 100, si / si.max(), color=BLUE, ls=ls, lw=lw)
        ax.plot(g.r * 100, so / so.max(), color=ORANGE, ls=ls, lw=lw)
        ax.plot([], [], color="#3B4658", ls=ls, lw=lw, label=f"$d$ = {d:.1f} cm")
        rows.append(dict(d_cm=d, overlap=float((np.minimum(si, so) * g.area).sum()),
                         inner_edge_share=float((si * g.area)[(g.r > G.r_1) & (g.r < G.r_2)].sum())))
    ax.set_xlim(0, 21); ax.set_ylim(0, 1.45)
    ax.text(7.7, 1.1, "안쪽 코일", ha="center", fontsize=8.5, color=BLUE)
    ax.text(15.3, 1.1, "바깥쪽 코일", ha="center", fontsize=8.5, color=ORANGE)
    ax.set_xlabel("$r$ [cm]"); ax.set_ylabel("코일별 가열 (최댓값 1)")
    ax.text(-0.02, 1.02, "(b)", transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.02), ncol=2, fontsize=7.4, handlelength=2.6, columnspacing=1.2)
    log["footprints"] = rows
    save(fig, "fig_dual")

fig_chamber(); fig_concept(); fig_single(); fig_dual()
json.dump(log, open(f"{OUT}/fig_log.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(log, indent=1, ensure_ascii=False))
