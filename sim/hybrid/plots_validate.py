"""1D–2D 수송 비교 그림 (validate.validation_study 의 결과를 그린다).

(a) 2D 해 ÷ 1D 해의 밀도 지도      : 기본 모드 가정이 어디서 어긋나는지
(b) 2D 해의 T_e(r, z)              : 1D 는 z 균일로 가정한 양
(c) z 방향 밀도 분포               : 세 반지름에서 2D(실선)와 1D 의 cos 모드(점선)
(d) 웨이퍼 높이 분포               : k = 0.5, 1, 2 에서 2D(실선)와 1D(점선)
(e) J_ctrl 성분                    : 1D 와 2D 를 나란히
(f) 운전점별 n̄_w, ρ 의 차          : 1D ÷ 2D − 1
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .plots_point import BLUE, CM, INK, MUTED, ORANGE

GREEN = "#2f8f6b"


def plot_validation(study: dict, path: Path) -> None:
    s1, s2 = study["pairs"]["기준 (k=1, φ=0°)"]
    cfg, g = s1.cfg, s1.grid
    geo = cfg.geom
    zp = g.z[: g.Nzp]
    fig, ax = plt.subplots(2, 3, figsize=(16, 9), constrained_layout=True)
    # --- (a) 밀도 비 지도
    ratio = s2.state.ne_rz(zp, cfg) / s1.state.ne_rz(zp, cfg)
    span = max(abs(ratio.min() - 1), abs(ratio.max() - 1))
    im = ax[0, 0].pcolormesh(g.r * CM, zp * CM, ratio, cmap="RdBu_r", vmin=1 - span, vmax=1 + span, shading="nearest", rasterized=True)
    fig.colorbar(im, ax=ax[0, 0], pad=0.02).set_label("n_e(2D) / n_e(1D)")
    ax[0, 0].axhline(geo.z_w * CM, color=INK, lw=0.9, ls="--")
    ax[0, 0].text(0.4, geo.z_w * CM + 0.12, "관측면 z_w", fontsize=8)
    ax[0, 0].set(xlabel="r [cm]", ylabel="z [cm]", title="(a) 밀도 비: 2D 해 ÷ 1D 해 (기준점)")
    ax[0, 0].grid(False)
    # --- (b) 2D 전자온도
    im = ax[0, 1].pcolormesh(g.r * CM, zp * CM, s2.state.Te, cmap="magma", shading="nearest", rasterized=True)
    fig.colorbar(im, ax=ax[0, 1], pad=0.02).set_label("T_e [V]")
    spread = float(np.max(np.ptp(s2.state.Te, axis=0)))
    ax[0, 1].set(xlabel="r [cm]", ylabel="z [cm]", title=f"(b) 2D 해의 T_e: z 방향 차 최대 {spread:.2f} V (1D 는 0 으로 가정)")
    ax[0, 1].grid(False)
    # --- (c) z 방향 분포
    a = ax[0, 2]
    for r0, col in ((0.025, BLUE), (0.08, GREEN), (0.155, ORANGE)):
        i = int(np.argmin(np.abs(g.r - r0)))
        n2, n1 = s2.state.n[:, i], s1.state.ne_rz(zp, cfg)[:, i]
        a.plot(n2 / n2.max(), zp * CM, color=col, lw=2, label=f"r = {r0*CM:g} cm")
        a.plot(n1 / n1.max(), zp * CM, color=col, lw=1.2, ls="--")
    a.set(xlabel="n_e(z) / 최대값", ylabel="z [cm]", ylim=(0, geo.L * CM), title="(c) z 방향 분포: 2D(실선), 1D 의 cos 모드(점선)")
    a.legend(frameon=False, fontsize=9, loc="lower left")
    # --- (d) 웨이퍼 높이 분포
    a = ax[1, 0]
    a.axvspan(0, geo.r_c * CM, color=BLUE, alpha=0.10, lw=0)
    a.axvspan(geo.r_1 * CM, geo.r_2 * CM, color=ORANGE, alpha=0.13, lw=0)
    for name, col in (("k=0.5, φ=0°", BLUE), ("기준 (k=1, φ=0°)", INK), ("k=2, φ=0°", ORANGE)):
        p1, p2 = study["pairs"][name]
        a.plot(g.r * CM, p2.state.wafer_profile(cfg) * 1e-16, color=col, lw=2, label=name.replace("기준 (", "").replace(")", ""))
        a.plot(g.r * CM, p1.state.wafer_profile(cfg) * 1e-16, color=col, lw=1.2, ls="--")
    a.set(xlabel="r [cm]", ylabel="n_w [10¹⁶ m⁻³]", xlim=(0, geo.R * CM), ylim=(0, None),
          title="(d) 웨이퍼 높이 분포: 2D(실선), 1D(점선)")
    a.legend(frameon=False, fontsize=9)
    # --- (e) J_ctrl 성분 비교
    a = ax[1, 1]
    j1, j2 = study["jac_1d"], study["jac_2d"]
    labels = [f"∂{o}/∂{i}" for o in ("n̄", "ρ") for i in ("P", "k", "φ")]
    x = np.arange(6)
    a.bar(x - 0.2, j1.J_norm.ravel(), 0.4, color=MUTED, label=f"1D ({j1.seconds:.1f} s)")
    a.bar(x + 0.2, j2.J_norm.ravel(), 0.4, color=BLUE, label=f"2D ({j2.seconds:.1f} s)")
    a.axhline(0, color=INK, lw=0.8)
    a.set_xticks(x, labels)
    a.set(ylabel="무차원 감도", title=f"(e) J_ctrl 성분: 최대 차 {study['err_J']:.4f}")
    a.legend(frameon=False)
    # --- (f) 운전점별 차
    a = ax[1, 2]
    rows = study["rows"]
    y = np.arange(len(rows))[::-1]
    a.barh(y + 0.2, [100 * r["err_n_bar"] for r in rows], 0.4, color=INK, label="n̄_w")
    a.barh(y - 0.2, [100 * r["err_rho"] for r in rows], 0.4, color=ORANGE, label="ρ")
    a.axvline(0, color=INK, lw=0.8)
    a.set_yticks(y, [r["case"] for r in rows])
    a.set(xlabel="1D ÷ 2D − 1 [%]", title="(f) 운전점별 1D 축소 오차")
    a.legend(frameon=False, loc="upper right")
    base = rows[0]
    fig.suptitle(f"반경 1D 수송과 (r, z) 2D 수송의 비교  ·  기준점 오차: n̄_w {100*base['err_n_bar']:+.1f} %, ρ {100*base['err_rho']:+.1f} %"
                 f"  ·  계산 시간 {base['t_1d_s']*1e3:.0f} ms 대 {base['t_2d_s']*1e3:.0f} ms(1D 해에서 출발)",
                 fontsize=12, fontweight="bold")
    fig.savefig(path, dpi=150)
    plt.close(fig)
