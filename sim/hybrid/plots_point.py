"""운전점 하나의 결과 그림과 외부 결과 비교 그림.

plot_point   : 장·가열·밀도 지도, 웨이퍼 높이 분포와 지표, T_e·가열 분포, 수렴 이력을 한 장에
plot_compare : 외부(COMSOL 등) 분포와의 겹쳐 그리기
한글 글꼴은 Noto Sans CJK KR 을 쓴다 (없으면 한글이 깨질 수 있다).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .coupled import Solution  # noqa: E402

plt.rcParams.update({"font.family": ["Noto Sans CJK KR", "DejaVu Sans"], "axes.unicode_minus": False,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": "#e3e2dd", "grid.linewidth": 0.6, "font.size": 10})
BLUE, ORANGE, INK, MUTED = "#2a78d6", "#eb6834", "#0b0b0b", "#8a8984"
CM = 100.0      # m → cm


def _map(ax, sol: Solution, data, z, title, unit, cmap):
    """(r, z) 지도 한 장. 코일 위치와 창 경계를 함께 표시한다."""
    g, geo = sol.grid, sol.cfg.geom
    im = ax.pcolormesh(g.r * CM, z * CM, data, shading="nearest", cmap=cmap, rasterized=True)
    plt.colorbar(im, ax=ax, pad=0.02).set_label(unit)
    if z.max() > geo.L * 1.01:                               # 전자기장 전체 영역 그림
        for zz in (geo.L, geo.L + geo.window):
            ax.axhline(zz * CM, color="white", lw=0.8, ls="--")
        ax.plot(np.array(geo.r_in) * CM, [geo.z_coil * CM] * len(geo.r_in), "o", color=BLUE, mec="white", ms=7)
        ax.plot(np.array(geo.r_out) * CM, [geo.z_coil * CM] * len(geo.r_out), "o", color=ORANGE, mec="white", ms=7)
        ax.text(0.4, (geo.L + geo.window / 2) * CM, "유전체 창", color="white", va="center", fontsize=8)
    ax.set(xlabel="r [cm]", ylabel="z [cm]", title=title)
    ax.grid(False)


def plot_point(sol: Solution, path: Path) -> None:
    cfg, g, st, heat, m = sol.cfg, sol.grid, sol.state, sol.heating, sol.metrics
    geo, op = cfg.geom, cfg.op
    k, phi = op.effective_k_phi()
    zp = g.z[: g.Nzp]
    fig, ax = plt.subplots(2, 3, figsize=(16, 8.6), constrained_layout=True)
    # --- 윗줄: 2D 지도 세 장
    _map(ax[0, 0], sol, np.abs(heat.E), g.z, "(a) 유도 전기장 |E_θ|  (● 안쪽 코일 ● 바깥쪽 코일)", "V/m", "viridis")
    _map(ax[0, 1], sol, heat.p_abs * 1e-3, zp, "(b) 흡수 전력 밀도 p_abs", "kW/m³", "inferno")
    two_d = cfg.num.transport == "full_2d"
    _map(ax[0, 2], sol, st.ne_rz(zp, cfg) * 1e-16, zp,
         "(c) 전자 밀도 n_e (2D 수송)" if two_d else "(c) 전자 밀도 n_e (z 방향은 기본 모드 가정)", "10¹⁶ m⁻³", "cividis")
    ax[0, 2].axhline(geo.z_w * CM, color="white", lw=1.0, ls="--")
    ax[0, 2].text(geo.R * CM * 0.98, geo.z_w * CM + 0.12, "관측면 z = z_w", color="white", ha="right", fontsize=8)
    # --- (d) 웨이퍼 높이 분포와 지표
    a = ax[1, 0]
    n_w = st.wafer_profile(cfg) * 1e-16
    a.axvspan(0, geo.r_c * CM, color=BLUE, alpha=0.13, lw=0)
    a.axvspan(geo.r_1 * CM, geo.r_2 * CM, color=ORANGE, alpha=0.16, lw=0)
    a.plot(g.r * CM, st.midplane(cfg) * 1e-16, color=MUTED, lw=1.2, ls="--", label="중간 높이 n0(r)")
    a.plot(g.r * CM, n_w, color=INK, lw=2.0, label="관측 높이 n_w(r)")
    a.hlines(m.n_c * 1e-16, 0, geo.r_c * CM, color=BLUE, lw=3)
    a.hlines(m.n_edge * 1e-16, geo.r_1 * CM, geo.r_2 * CM, color=ORANGE, lw=3)
    a.hlines(m.n_bar * 1e-16, 0, geo.R_w * CM, color=INK, lw=0.9, ls=":")
    a.text(geo.r_c * CM / 2, m.n_c * 1e-16 * 1.03, f"n_c = {m.n_c*1e-16:.2f}", color=BLUE, ha="center", fontsize=9)
    a.text(geo.r_2 * CM + 0.4, m.n_edge * 1e-16 * 1.06, f"n_edge = {m.n_edge*1e-16:.2f}",
           color="#b54a1e", ha="left", fontsize=9)
    a.set(xlabel="r [cm]", ylabel="전자 밀도 [10¹⁶ m⁻³]", xlim=(0, geo.R * CM), ylim=(0, None),
          title=f"(d) 웨이퍼 지표:  n̄_w = {m.n_bar*1e-16:.3f},  ρ = n_c/n_edge = {m.rho:.3f}")
    a.legend(loc="lower left", frameon=False, fontsize=9)
    # --- (e) 전자온도와 z 적분 가열
    a = ax[1, 1]
    a.plot(g.r * CM, st.Te_radial(), color=INK, lw=2.0)
    a.set(xlabel="r [cm]", ylabel="전자온도 T_e [V]", xlim=(0, geo.R * CM), title="(e) 전자온도(검정)와 z 적분 가열 S(주황)")
    b = a.twinx()
    b.fill_between(g.r * CM, heat.S * 1e-3, color=ORANGE, alpha=0.25, lw=0)
    b.plot(g.r * CM, heat.S * 1e-3, color=ORANGE, lw=1.4)
    b.set_ylabel("S = ∫p_abs dz [kW/m²]", color="#b54a1e")
    b.set_ylim(0, None); b.grid(False); b.spines["right"].set_visible(True)
    # --- (f) 수렴 이력
    a = ax[1, 2]
    it = [h["iter"] for h in sol.history]
    series = (("coupled_residual", "결합 잔차 max|F|", INK, "-"), ("d_ln_n", "갱신량 Δln n_e", BLUE, "-"),
              ("d_Te", "갱신량 ΔT_e/T_e", ORANGE, "-"), ("particle_error", "입자 수지 오차", BLUE, ":"),
              ("energy_error", "에너지 수지 오차", ORANGE, ":"))
    for key, label, color, ls in series:
        a.semilogy(it, np.maximum(np.abs([h[key] for h in sol.history]), 1e-16), color=color, ls=ls, marker="o", ms=3, label=label)
    a.axhline(cfg.num.outer_tol, color=MUTED, lw=0.8, ls="--")
    a.text(0, cfg.num.outer_tol * 0.25, "갱신량 허용치", color=MUTED, ha="left", fontsize=8)
    a.set(xlabel="바깥 반복 횟수", ylabel="크기 (무차원)",
          title=f"(f) 수렴 이력: {len(it)}회, {sol.timing['total']*1e3:.0f} ms")
    a.legend(frameon=False, fontsize=8, loc="upper right")
    mode = {"dual": "이중 코일", "single_series": "단일 코일(전 턴 직렬)", "single_inner": "단일 코일(안쪽만)"}[op.coil_mode]
    mode += " · 2D 수송" if two_d else " · 반경 1D 수송"
    fig.suptitle(f"{mode} · {op.p_mtorr:g} mTorr Ar · P_tot = {op.P_tot:g} W · k = {k:g} · φ = {np.degrees(phi):g}°"
                 f"   →   I_0 = {heat.I0:.2f} A,  P_abs = {heat.P_abs:.0f} W", fontsize=12, fontweight="bold")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_compare(cmp: dict, path: Path, label_ext: str = "외부 결과 (COMSOL)") -> None:
    """export.compare_radial 의 결과를 겹쳐 그린다. 왼쪽은 절대값, 오른쪽은 평균으로 나눈 모양."""
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    r = cmp["r"] * CM
    ax[0].plot(r, cmp["model"] * 1e-16, color=INK, lw=2, label="하이브리드 모델")
    ax[0].plot(r, cmp["external"] * 1e-16, color=ORANGE, lw=1.6, ls="--", label=label_ext)
    ax[0].set(xlabel="r [cm]", ylabel="n_w [10¹⁶ m⁻³]", ylim=(0, None),
              title=f"절대값: n̄_w 비 = {cmp['n_bar_ratio']:.3f}")
    ax[0].legend(frameon=False)
    ax[1].plot(r, cmp["model"] / cmp["n_bar_model"], color=INK, lw=2)
    ax[1].plot(r, cmp["external"] / cmp["n_bar_external"], color=ORANGE, lw=1.6, ls="--")
    ax[1].set(xlabel="r [cm]", ylabel="n_w / n̄_w", ylim=(0, None),
              title=f"모양: ρ 모델 {cmp['rho_model']:.3f} / 외부 {cmp['rho_external']:.3f}, 모양 RMS 차 {cmp['shape_rms']:.3f}")
    fig.savefig(path, dpi=150)
    plt.close(fig)
