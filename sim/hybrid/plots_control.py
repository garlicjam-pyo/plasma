"""제어 가능성 판정 결과의 그림: J_ctrl, 등평균 스캔, 응답 지도, 타이밍.

plot_jacobian : J_ctrl 숫자표 + "출력 평면에서 각 입력이 미는 방향" 화살표 (단일 코일과 나란히)
plot_iso_scan : 평균 밀도를 유지한 채 k 를 바꿨을 때의 ρ, 필요한 P_tot, 분포 모양
plot_map      : (k, φ) 평면의 ρ 지도와 n̄_w 등고선
plot_timing   : 격자별 계산 시간·마진과 격자 오차
plot_margin   : 이득 불일치 λ 에 따른 위상 여유 곡선과 시나리오별 위치
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from . import loop as lp
from . import timing as tm
from .control import ControlJacobian
from .plots_point import BLUE, CM, INK, MUTED, ORANGE

GREEN = "#2f8f6b"
IN_LABEL = {"P_tot": "P_tot", "k": "k", "phi": "φ"}
IN_COLOR = {"P_tot": INK, "k": BLUE, "phi": ORANGE}


def _matrix(ax, jc: ControlJacobian, title: str) -> None:
    """무차원 J_ctrl 을 색과 숫자로 보여 준다."""
    J = jc.J_norm
    lim = max(1.0, np.max(np.abs(J)))
    ax.imshow(J, cmap="RdBu_r", vmin=-lim, vmax=lim, aspect="auto")
    for i in range(J.shape[0]):
        for j in range(J.shape[1]):
            ax.text(j, i, f"{J[i, j]:+.3f}", ha="center", va="center", fontsize=12,
                    color="white" if abs(J[i, j]) > 0.6 * lim else INK)
    unit = {"P_tot": "입력 1 % → 출력 %", "k": "입력 1 % → 출력 %", "phi": "1 rad → 출력 비율"}
    ax.set_xticks(range(J.shape[1]), [f"{IN_LABEL[n]}  ({unit[n]})" for n in jc.inputs])
    ax.set_yticks(range(2), ["평균 밀도 n̄_w", "밀도비 ρ"])
    ax.set_title(title, fontsize=11)
    ax.grid(False)


def _arrows(ax, jc: ControlJacobian, title: str) -> None:
    """출력 평면 (Δn̄/n̄, Δρ/ρ) 에서 각 입력이 미는 방향. 화살표가 한 직선 위에 없으면 독립 제어 가능."""
    lim = 1.15 * max(0.3, np.max(np.abs(jc.J_norm)))
    ax.axhline(0, color=MUTED, lw=0.8); ax.axvline(0, color=MUTED, lw=0.8)
    for j, name in enumerate(jc.inputs):
        dx, dy = jc.J_norm[:, j]
        ax.annotate("", xy=(dx, dy), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color=IN_COLOR[name], lw=2.2))
        norm = max(np.hypot(dx, dy), 1e-9)                   # 글자는 화살표 끝에서 같은 방향으로 조금 더 바깥에
        ax.text(dx + 0.11 * lim * dx / norm, dy + 0.11 * lim * dy / norm, IN_LABEL[name], color=IN_COLOR[name],
                fontsize=12, fontweight="bold", ha="center", va="center")
    ax.set(xlim=(-lim, lim), ylim=(-lim, lim), xlabel="평균 밀도 변화  Δn̄_w / n̄_w", ylabel="밀도비 변화  Δρ / ρ", title=title)
    ax.set_aspect("equal")


def plot_jacobian(dual: ControlJacobian, single: ControlJacobian, path: Path) -> None:
    fig, ax = plt.subplots(2, 2, figsize=(12.5, 9), constrained_layout=True,
                           gridspec_kw={"height_ratios": [1, 1.6]})
    op = dual.base.cfg.op
    _matrix(ax[0, 0], dual, f"이중 코일 J_ctrl (무차원)  ·  계수 {dual.rank},  조건수 {dual.condition:.2f}")
    _matrix(ax[0, 1], single, f"단일 코일 J_ctrl (무차원)  ·  계수 {single.rank}")
    gain = ",  ".join(f"{IN_LABEL[n]}: {v:+.3f}" for n, v in dual.shape_gain.items())
    _arrows(ax[1, 0], dual, f"이중 코일: 화살표 방향이 서로 다름 → 독립 제어 가능\n평균 고정 시 형상 감도  {gain}")
    _arrows(ax[1, 1], single, "단일 코일: 화살표 하나 → 평균과 비가 묶여 움직임")
    fig.suptitle(f"제어 민감도 행렬 J_ctrl  ·  기준점 P_tot = {op.P_tot:g} W, k = {op.k:g}, φ = {np.degrees(op.phi):g}°, "
                 f"{op.p_mtorr:g} mTorr  ·  계산 {dual.seconds:.1f} s", fontsize=12, fontweight="bold")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_iso_scan(scans: list, path: Path) -> None:
    """scans: control.iso_mean_scan 결과 목록 (위상별)."""
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6), constrained_layout=True)
    colors = (BLUE, GREEN, ORANGE, INK)
    for sc, col in zip(scans, colors):
        lab = f"φ = {np.degrees(sc['phi']):g}°"
        ax[0].plot(sc["k"], sc["rho"], "o-", color=col, ms=4, label=lab)
        ax[1].plot(sc["k"], sc["P_tot"], "o-", color=col, ms=4, label=lab)
    ax[0].axhline(1.0, color=MUTED, lw=0.9, ls="--")
    ax[0].text(scans[0]["k"][-1], 1.02, "ρ = 1 (중앙 = 가장자리)", color=MUTED, ha="right", fontsize=8)
    dev = max(np.max(np.abs(sc["n_bar"] / sc["target"] - 1)) for sc in scans)
    ax[0].set(xlabel="전류 크기비 k", ylabel="밀도비 ρ",
              title=f"(a) 평균 밀도를 유지한 채 얻는 ρ\nn̄_w = {scans[0]['target']*1e-16:.2f}×10¹⁶ m⁻³ 고정 (편차 {dev:.0e} 이하)")
    ax[0].legend(frameon=False)
    ax[1].set(xlabel="전류 크기비 k", ylabel="필요한 P_tot [W]", title="(b) 평균을 유지하려고 보정한 전력")
    # (c) 첫 스캔(보통 φ = 0)의 분포 모양 변화
    sc = scans[0]
    geo = sc["solutions"][0].cfg.geom
    ax[2].axvspan(0, geo.r_c * CM, color=BLUE, alpha=0.12, lw=0)
    ax[2].axvspan(geo.r_1 * CM, geo.r_2 * CM, color=ORANGE, alpha=0.15, lw=0)
    cmap = plt.get_cmap("viridis")
    for i, sol in enumerate(sc["solutions"]):
        c = cmap(i / max(1, len(sc["solutions"]) - 1))
        ax[2].plot(sol.grid.r * CM, sol.state.wafer_profile(sol.cfg) / sol.metrics.n_bar, color=c, lw=1.6,
                   label=f"k = {sc['k'][i]:.2f}" if i in (0, len(sc["solutions"]) - 1) else None)
    ax[2].set(xlabel="r [cm]", ylabel="n_w(r) / n̄_w", xlim=(0, geo.R * CM), ylim=(0, None),
              title=f"(c) 분포 모양 (φ = {np.degrees(sc['phi']):g}°, 색: k 작음 → 큼)")
    ax[2].legend(frameon=False, fontsize=9)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_map(mp: dict, cfg, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5.4), constrained_layout=True)
    phi_deg = np.degrees(mp["phi"])
    cf = ax.contourf(mp["k"], phi_deg, mp["rho"], levels=16, cmap="viridis")
    fig.colorbar(cf, ax=ax).set_label("밀도비 ρ")
    cs = ax.contour(mp["k"], phi_deg, mp["n_bar"] * 1e-16, levels=8, colors="white", linewidths=1.0)
    ax.clabel(cs, fmt="%.2f", fontsize=8)
    ax.set(xlabel="전류 크기비 k", ylabel="위상차 φ [deg]",
           title=f"ρ 지도(색)와 n̄_w 등고선(흰 선, 10¹⁶ m⁻³)  ·  P_tot = {cfg.op.P_tot:g} W 고정\n"
                 "흰 선을 따라가면 평균은 그대로이고 색(ρ)만 변한다")
    ax.grid(False)
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_timing(study: dict, path: Path) -> None:
    rows = study["rows"]
    x = [r["em_unknowns"] for r in rows]
    lab = [f"{r['Nr']}×{r['Nz']}" for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.4), constrained_layout=True)
    for key, budget, col, name in (("t_point_s", tm.BUDGET_POINT_S, BLUE, "운전점 1개"),
                                   ("t_jacobian_s", tm.BUDGET_JACOBIAN_S, ORANGE, "J_ctrl 1개 (7회 수렴)")):
        ax[0].loglog(x, [r[key] for r in rows], "o-", color=col, label=name)
        ax[0].axhline(budget, color=col, lw=0.9, ls="--")
        ax[0].axhline(budget / tm.MIN_MARGIN, color=col, lw=0.9, ls=":")
        ax[0].text(x[0], budget * 1.12, f"예산 {budget:g} s", color=col, fontsize=8)
        ax[0].text(x[0], budget / tm.MIN_MARGIN * 1.12, f"설계 목표 (마진 {tm.MIN_MARGIN:g}배)", color=col, fontsize=8)
    ax[0].set_xticks(x, lab); ax[0].minorticks_off()
    ax[0].set(xlabel="격자 (Nr × Nz)", ylabel="계산 시간 [s]", title="(a) 계산 시간과 예산")
    ax[0].legend(frameon=False, loc="lower right")
    for key, col, name in (("err_n_bar", INK, "n̄_w"), ("err_rho", BLUE, "ρ"), ("err_J", ORANGE, "J_ctrl 성분(절대 차)")):
        ax[1].loglog(x, [max(r[key], 1e-7) for r in rows], "o-", color=col, label=name)
    ax[1].axhline(tm.MAX_GRID_ERROR, color=MUTED, lw=0.9, ls="--")
    ax[1].text(x[-1], tm.MAX_GRID_ERROR * 1.15, f"허용 오차 {tm.MAX_GRID_ERROR:.1%}", color=MUTED, ha="right", fontsize=8)
    ax[1].set_xticks(x, lab); ax[1].minorticks_off()
    ref = study["reference"]["grid"]
    ax[1].set(xlabel="격자 (Nr × Nz)", ylabel=f"기준 격자({ref[0]}×{ref[1]+ref[2]}) 대비 차",
              title="(b) 격자 오차")
    ax[1].legend(frameon=False)
    rec = study["recommended"]
    if rec:
        fig.suptitle(f"추천 격자 {rec['Nr']}×{rec['Nz']}: 운전점 {rec['t_point_s']*1e3:.0f} ms (마진 {rec['margin_point']:.0f}배), "
                     f"J_ctrl {rec['t_jacobian_s']:.2f} s (마진 {rec['margin_jacobian']:.0f}배)", fontsize=12, fontweight="bold")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_margin(rows: list, path: Path) -> None:
    """가로축: 실제 이득 ÷ 제어기가 믿는 이득(가장 큰 고유값). 세로축: 위상 여유."""
    fig, ax = plt.subplots(figsize=(10.5, 5.6), constrained_layout=True)
    lam = np.linspace(0.15, 4.0, 300)
    for T_d, col in zip(lp.T_DELAY, (BLUE, ORANGE)):
        ax.plot(lam, [lp.margins(complex(l), T_d)["pm"] for l in lam], color=col, lw=2, label=f"측정 지연 T_d = {T_d:g} s")
    for level, text in ((60, "설계 목표 60°"), (30, "최소 30°"), (0, "불안정 경계")):
        ax.axhline(level, color=MUTED, lw=0.8, ls="--")
        ax.text(3.98, level + 1.5, text, color=MUTED, ha="right", fontsize=8)
    T_worst = max(lp.T_DELAY)
    near_one = [r for r in rows if r["lam_max"] <= 1.1]      # 이득이 거의 그대로인 경우는 한데 묶어 표시
    for r in rows:
        pm = lp.margins(complex(r["lam_max"]), T_worst)["pm"]
        ax.plot(r["lam_max"], pm, "o", color=INK, ms=5)
        if r["lam_max"] > 1.1:
            ax.annotate(r["scenario"], (r["lam_max"], pm), xytext=(8, 10), textcoords="offset points", fontsize=9)
    if near_one:
        slow = max(near_one, key=lambda r: r["settle_s"])
        ax.annotate(f"그 밖의 {len(near_one)}가지: λ_max ≈ 1 (여유는 그대로,\n대신 느려짐. 최대 설정 시간 {slow['settle_s']:.0f} s: {slow['scenario']})",
                    (1.0, lp.margins(1 + 0j, T_worst)["pm"]), xytext=(-150, -70), textcoords="offset points", fontsize=9,
                    arrowprops=dict(arrowstyle="-", color=MUTED))
    ax.set(xlabel="이득 불일치 λ_max = 실제 이득 ÷ 제어기가 믿는 이득", ylabel="위상 여유 [deg]", ylim=(-20, 95), xlim=(0, 4),
           title=f"바깥 루프의 위상 여유 (적분 제어, ω_c = {lp.OMEGA_C:g} rad/s, 구동기 지연 {lp.TAU_ACT:g} s)\n"
                 f"점: 기준점 J 를 그대로 쓸 때 각 경우의 위치 (T_d = {T_worst:g} s 곡선 위)")
    ax.legend(frameon=False, loc="lower left")
    fig.savefig(path, dpi=150)
    plt.close(fig)

