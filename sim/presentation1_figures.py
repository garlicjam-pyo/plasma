"""1차 발표 그림 3종을 다시 그리는 스크립트 (2026-11-05 검토 반영).

    python sim/presentation1_figures.py            # 세 그림 모두
    python sim/presentation1_figures.py range      # figures/presentation1_R_range_by_pressure.png
    python sim/presentation1_figures.py chain      # figures/presentation1_chain_C1-C8.png
    python sim/presentation1_figures.py arch       # figures/presentation1_drive_architecture_B.png

- R 범위: figures/presentation1_r_range.csv (presentation1_estimates.py range)의 코일 선택도 하한
  R_min_x0.05, R_min_x0.07 을 쓰고, 상한(중앙 몫 0.93)과 같은 전력 밀도의 R 은 같은 2-영역 0D 모델로 계산한다.
  처음 판(번들)은 코일 선택도 없이 중앙 몫 2–98% 범위를 그렸고 15 mTorr를 충분한 압력으로 표시했다.
- 사슬: ② 장 상자의 "E_θ ∝ r (2.52)"는 솔레노이드형 식이라 "축 위 E_θ = 0"으로 고쳤다.
- 구성도: 바깥 루프 대역폭 표기를 ω_c ≤ 0.2 rad/s ≈ 0.03 Hz 로 고쳤다.
한글 글꼴은 Noto Sans CJK KR 을 쓴다 (없으면 기본 글꼴로 그려지고 한글이 깨질 수 있다).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

FIG = Path(__file__).resolve().parent.parent / "figures"
plt.rcParams.update({"font.family": ["Noto Sans CJK KR", "DejaVu Sans"], "axes.unicode_minus": False})

INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#d9d8d3"
BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#a3a29c"
BLUE_BG, ORANGE_BG, GRAY_BG, BOX_EDGE = "#e6f0fb", "#fdece4", "#eeeeeb", "#c9c8c0"
X_SEL_HI = 0.93     # 안쪽 코일만 켰을 때 중앙 몫 0.91–0.95 → 분배 상한 (보수적으로 0.93)


# ------------------------------------------------------------------ 압력별 R 범위
def r_range_figure() -> None:
    import presentation1_estimates as pe
    import two_zone_icp as m

    prm = m.Params(**pe.DESIGN)
    with open(FIG / "presentation1_r_range.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    p = [int(r["p_mTorr"]) for r in rows]
    lo05 = np.array([float(r["R_min_x0.05"]) for r in rows])
    lo07 = np.array([float(r["R_min_x0.07"]) for r in rows])
    hi = np.array([np.exp(pe._out(300.0, X_SEL_HI, pp, prm)[1]) for pp in p])
    req = np.array([np.exp(pe._out(300.0, prm.Vc / prm.V, pp, prm)[1]) for pp in p])

    fig, ax = plt.subplots(figsize=(11.5, 6.4), dpi=120)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.78, bottom=0.10)
    xs = np.arange(len(p))
    ax.axhspan(0.8, 1.2, color="#ecebe7", zorder=0)
    ax.text(-0.55, 0.83, "목표 R 0.8–1.2", ha="left", va="bottom", color=INK2, fontsize=10)
    ax.axhline(0.8, color=MUTED, lw=0.8, ls=(0, (3, 3)), zorder=1)
    for i in xs:
        if lo07[i] < 0.8:
            col, cat = BLUE, "margin"
        elif lo05[i] <= 0.8:
            col, cat = ORANGE, "border"
        else:
            col, cat = GRAY, "short"
        ax.plot([i, i], [lo07[i], hi[i]], color=col, lw=2.2, solid_capstyle="butt", zorder=3)
        ax.plot([i - 0.09, i + 0.09], [hi[i], hi[i]], color=col, lw=2.2, zorder=3)
        ax.plot([i - 0.09, i + 0.09], [lo07[i], lo07[i]], color=col, lw=2.2, zorder=3)
        # 하한 범위 (중앙 몫 0.05–0.07)
        ax.plot([i, i], [lo05[i], lo07[i]], color=col, lw=6, alpha=0.45, solid_capstyle="butt", zorder=2)
        ax.scatter([i], [req[i]], s=70, color=col, edgecolor="white", linewidth=1.5, zorder=4)
        ax.text(i + 0.13, req[i], f"{req[i]:.2f}", va="center", fontsize=10, color=INK2)
        ax.text(i, hi[i] * 1.07, f"{hi[i]:.2f}", ha="center", va="bottom", fontsize=10, color=INK2)
        ax.text(i, lo05[i] * 0.93, f"{lo05[i]:.2f}–{lo07[i]:.2f}", ha="center", va="top", fontsize=11,
                color=INK, fontweight="bold" if cat != "short" else "normal")
    ax.set_yscale("log")
    ax.set_ylim(0.4, 8)
    ax.set_yticks([0.5, 0.8, 1, 1.2, 2, 5])
    ax.set_yticklabels(["0.5", "0.8", "1", "1.2", "2", "5"])
    ax.minorticks_off()
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{pp} mTorr" for pp in p], fontsize=11)
    ax.set_xlim(-0.6, len(p) - 0.4)
    ax.set_ylabel("R = n_c / n_e (로그 축)", color=INK2, fontsize=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(BOX_EDGE)
    ax.tick_params(colors=INK2, length=0)
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)

    fig.text(0.08, 0.95, "R 0.8–1.2 전 범위는 20 mTorr 이상에서 여유, 15 mTorr는 경계", fontsize=15,
             fontweight="bold", color=INK)
    fig.text(0.08, 0.905, "수염: 코일 선택도 안에서 낼 수 있는 R (중앙 전력 몫 0.07–0.93) · 굵은 아래끝과 숫자: 하한 "
             "(중앙 몫 0.05–0.07) · 점: 두 영역 전력 밀도가 같을 때의 R", fontsize=10, color=INK2)
    fig.text(0.08, 0.87, "독립 전원(B), 설계 형상(R 20 cm, L 10 cm, r_b 12 cm), 흡수 전력 300 W, 2-영역 0D 계산 · "
             "sim/presentation1_estimates.py range (절대 범위는 검증 전)", fontsize=10, color=INK2)
    handles = [plt.Line2D([], [], color=BLUE, lw=2.2, label="여유: 하한 < 0.8"),
               plt.Line2D([], [], color=ORANGE, lw=2.2, label="경계: 하한이 0.8에 걸침"),
               plt.Line2D([], [], color=GRAY, lw=2.2, label="부족: 하한 > 0.8 (자기장 보조 검토)")]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.075, 0.855), ncol=3, frameon=False,
               fontsize=10, labelcolor=INK2)
    out = FIG / "presentation1_R_range_by_pressure.png"
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    print(f"-> figures/{out.name}  (상한 R(0.93) = {np.round(hi, 2)}, 같은 전력 밀도 R = {np.round(req, 2)})")


# ------------------------------------------------------------------ 상자 그림 도구
def _box(ax, x, y, w, h, title, sub="", face="white", edge=BOX_EDGE, lw=1.4, title_size=12.5,
         sub_size=11, align="left", title_weight="bold"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=10", fc=face, ec=edge, lw=lw))
    if align == "left":
        tx, ha = x + 22, "left"
    else:
        tx, ha = x + w / 2, "center"
    if sub:
        ax.text(tx, y + h * 0.36, title, ha=ha, va="center", fontsize=title_size, fontweight=title_weight, color=INK)
        ax.text(tx, y + h * 0.68, sub, ha=ha, va="center", fontsize=sub_size, color=INK2, linespacing=1.5)
    else:
        ax.text(tx, y + h / 2, title, ha=ha, va="center", fontsize=title_size, fontweight=title_weight, color=INK)


def _arrow(ax, p0, p1, color=MUTED, ls="-", lw=1.3, head=True):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>,head_length=6,head_width=3.5" if head else "-",
                                 color=color, lw=lw, ls=ls, shrinkA=0, shrinkB=0, mutation_scale=1.6))


def _canvas(w, h, dpi=100):
    fig = plt.figure(figsize=(w / dpi, h / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    ax.axis("off")
    return fig, ax


# ------------------------------------------------------------------ 밀도 분포 사슬
def chain_figure() -> None:
    W, H = 1340, 1010
    fig, ax = _canvas(W, H)
    ax.text(42, 50, "한 영역의 조작은 다섯 단계 어디서든 다른 영역으로 샌다", fontsize=17, fontweight="bold", color=INK, va="center")
    ax.add_patch(FancyBboxPatch((42, 92), 22, 22, boxstyle="round,pad=0,rounding_size=4", fc=BLUE_BG, ec=BLUE, lw=1.8))
    ax.text(76, 103, "구동부 설계로 줄이는 결합 (C1–C5)", fontsize=12.5, color=INK2, va="center")
    ax.add_patch(FancyBboxPatch((530, 92), 22, 22, boxstyle="round,pad=0,rounding_size=4", fc=ORANGE_BG, ec=ORANGE, lw=1.8))
    ax.text(564, 103, "압력·형상으로 정해지는 결합 (C6, C7)", fontsize=12.5, color=INK2, va="center")

    left = [("① 회로: 코일 전류 I₁, I₂", "변압기 모델 (2.54)–(2.57), 효율 η"),
            ("② 장: 유도 전기장 E_θ와 표피층", "축 위 E_θ = 0 (2.52), δ (2.53), δ_p ≈ 1.7 cm"),
            ("③ 가열: 전자 에너지 수송", "λε ≈ 119 cm × (1 mTorr / p) (KC20)"),
            ("④ 수송: 이온화 → 양극성 확산", "(1.76), cos(πz/L) (1.79) → ℓ = L/π"),
            ("⑤ 손실: 벽 손실 → 영역 밀도", "h_L, h_R (2.71), n_k ∝ P_k / A_eff,k (2.73)")]
    right = [("C1–C3 회로 결합", "공통 전원·M₁₂·공통 2차측: 분배가 밀도를 따름", BLUE_BG, BLUE),
             ("C4 장 중첩 · C5 축전 결합", "코일 사이 E 교차항(위상 의존), 코일 전압 수백 V", BLUE_BG, BLUE),
             ("C6 비국소 가열: w = e^(−Δ/λε)", "w = 0.94 (1 mTorr) · 0.53 (10) · 0.15 (30)", ORANGE_BG, ORANGE),
             ("C7 확산: 누설 ≈ e^(−πΔ/L)", "L = 6 / 10 / 12 cm → 0.02 / 0.10 / 0.14", ORANGE_BG, ORANGE),
             ("구조적 손실 비대칭", "가장자리만 측벽 손실 → 같은 전력 밀도면 R ≈ 1.4", ORANGE_BG, ORANGE)]
    y0, bh, gap = 163, 98, 44
    for i, ((lt, ls), (rt, rs, rf, re)) in enumerate(zip(left, right)):
        y = y0 + i * (bh + gap)
        _box(ax, 42, y, 600, bh, lt, ls)
        _box(ax, 714, y, 586, bh, rt, rs, face=rf, edge=re, lw=2.2)
        ax.plot([642, 714], [y + bh / 2, y + bh / 2], color=BOX_EDGE, lw=1.2, ls=(0, (5, 4)))
        if i < 4:
            _arrow(ax, (342, y + bh), (342, y + bh + gap))
    y = y0 + 5 * (bh + gap) - 2
    _box(ax, 42, y, 1258, bh, "C8 비선형·이력: 모든 단계의 기울기가 동작점에 따라 바뀐다",
         "E–H 전이(교재 그림 2.44)에서 h_R 급변, R′_p ∝ n_e 또는 1/√n_e (그림 2.35)", face=GRAY_BG)
    out = FIG / "presentation1_chain_C1-C8.png"
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    print(f"-> figures/{out.name}")


# ------------------------------------------------------------------ 구동부 구성도 (구조 B)
def arch_figure() -> None:
    W, H = 1340, 700
    fig, ax = _canvas(W, H)
    ax.text(42, 48, "전원 두 대가 위상을 맞춰 코일을 하나씩 맡는다", fontsize=17, fontweight="bold", color=INK, va="center")
    ax.text(42, 86, "구조 B · 안쪽 루프는 코일 전류, 바깥 루프는 웨이퍼 측정", fontsize=12, color=INK2, va="center")

    _box(ax, 42, 178, 176, 268, "공통 발진기", "위상 고정\n0° 기준\n180° 비교", face=BLUE_BG, edge=BLUE, lw=2.4,
         align="center", title_size=14, sub_size=12)
    cols = [(248, "RF 전원 {i}", "13.56 MHz"), (446, "정합기 {i}", "자동 정합"), (644, "센서 {i}", "I{s} 크기·위상"),
            (842, None, None)]
    rows = [(178, 1, "₁", "안쪽 코일", "r 8 cm, 2턴"), (348, 2, "₂", "바깥 코일", "r 15.5 cm, 1–2턴")]
    bw, bh = 170, 98
    for y, i, s, coil, coil_sub in rows:
        for x, t, sub in cols:
            if t is None:
                _box(ax, x, y, bw, bh, coil, coil_sub, align="center", title_size=13, sub_size=11.5)
            else:
                _box(ax, x, y, bw, bh, t.format(i=i), sub.format(s=s), align="center", title_size=13, sub_size=11.5)
        for x0 in (248, 446, 644, 842):
            _arrow(ax, (x0 + bw, y + bh / 2), (x0 + bw + 28, y + bh / 2))
        _arrow(ax, (218, y + bh / 2), (248, y + bh / 2))
    _box(ax, 1040, 178, 196, 268, "플라즈마", "R 20 cm, L 10 cm\n중앙 r < 12 cm\n가장자리 12–20 cm",
         align="center", title_size=14, sub_size=11.5)
    # 안쪽 루프 (센서 → 전원), 점선
    for ytop, ylab, va in ((178, 130, "bottom"), (446, 494, "top")):
        yy = ytop - 32 if ytop == 178 else ytop + 32
        ax.plot([729, 729], [ytop, yy], color=MUTED, lw=1.2, ls=(0, (4, 3)))
        ax.plot([729, 333], [yy, yy], color=MUTED, lw=1.2, ls=(0, (4, 3)))
        _arrow(ax, (333, yy), (333, ytop), ls=(0, (4, 3)))
        ax.text(531, yy + (-8 if va == "bottom" else 8), "안쪽 루프: 코일 전류·위상 (ms 이하)", ha="center", va=va,
                fontsize=11.5, color=INK2)
    # 플라즈마 → FHP → 제어기 → 전원
    _box(ax, 1040, 530, 196, 98, "웨이퍼 FHP", "13–17점, ≈ 1 s 갱신", align="center", title_size=13, sub_size=11.5)
    _arrow(ax, (1138, 446), (1138, 530))
    _box(ax, 42, 530, 814, 128, "제어기 (바깥 루프, ω_c ≤ 0.2 rad/s ≈ 0.03 Hz)",
         "FHP 배열 → n̄, R_Γ 추정 (R은 T_e로 환산 보고) · J⁻¹ 피드포워드 + 적분 보정\n"
         "출력: I₁, I₂ 크기 설정값 (위상은 고정값)", title_size=13, sub_size=11.5)
    _arrow(ax, (1040, 579), (856, 579))
    ax.text(948, 568, "Γ_i(r), T_e(r)", ha="center", va="bottom", fontsize=11.5, color=INK2)
    ax.plot([284, 284], [530, 470], color=MUTED, lw=1.3)
    _arrow(ax, (284, 470), (284, 446))
    ax.text(270, 500, "설정값", ha="right", va="center", fontsize=11.5, color=INK2)
    out = FIG / "presentation1_drive_architecture_B.png"
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    print(f"-> figures/{out.name}")


if __name__ == "__main__":
    task = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in (("range", r_range_figure), ("chain", chain_figure), ("arch", arch_figure)):
        if task in (name, "all"):
            fn()
