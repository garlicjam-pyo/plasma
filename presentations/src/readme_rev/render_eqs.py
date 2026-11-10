"""슬라이드 3–7의 식·도식 이미지 (기존 덱과 같은 글꼴·색). 한글 설명은 슬라이드 글상자로 둔다."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
from PIL import Image
matplotlib.rcParams["mathtext.fontset"] = "cm"
INK, BLUE, ORANGE, NAVY = "#1F2340", "#3366CC", "#D9622B", "#303399"

EQ = {
    "n_rho":    r"$\rho \equiv \dfrac{n_c}{n_\mathrm{edge}}$",
    "n_avg":    r"$\langle n \rangle_S = \dfrac{1}{A_S}\int_S n(r, z_w)\,dA$",
    # 교재 식 (2.31)–(2.32)에서: p_e = (1/2)Re(sigma_p)|E|^2, E = I x (단위 전류 장)
    "n_pelhs":  r"$p_e(r,z) \;=$",
    "n_i2":     r"$|I|^2$",
    "n_f":      r"$f(r,z)$",
    # 교재 식 (2.70), (2.73)
    "n_te":     r"$\dfrac{K_{iz}(T_e)}{u_B(T_e)} = \dfrac{1}{n_g\, d_\mathrm{eff}}$",
    "n_n0k":    r"$n_0 = \dfrac{P_\mathrm{abs}(k,\,\phi,\,P_\mathrm{tot})}{e\,u_B\,\varepsilon_T\,A_\mathrm{eff}}$",
    "n_n0":     r"$n_0 = \dfrac{P_\mathrm{abs}}{e\,u_B\,\varepsilon_T\,A_\mathrm{eff}}$",
    # 교재 식 (1.76)의 정상 상태와 기본 모드 (1.79)·(1.83)
    "n_diffmode": r"$-D_a \nabla^2 n = \nu_{iz}\, n \;\;\Longrightarrow\;\; n \propto J_0\!\left(\dfrac{\chi_{01}\, r}{R}\right)\cos\dfrac{\pi z}{L}$",
}
for k, tex in EQ.items():
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex, fontsize=20, color=INK)
    fig.savefig(f"{k}.png", dpi=534, bbox_inches="tight", pad_inches=0.02, transparent=True)
    plt.close(fig)

def colored(name, parts):
    """색으로 항을 구분한 식. 항별 가로 위치(0–1)를 함께 돌려준다."""
    fig = plt.figure(figsize=(14, 1.2), dpi=534)
    r = fig.canvas.get_renderer()
    wpx = fig.get_size_inches()[0] * fig.dpi
    x, spans = 0.01, []
    for tex, col, key in parts:
        big = tex.strip("$").strip("\\, ") in ("[", "]")
        t = fig.text(x, 0.4 - (0.06 if big else 0), tex, fontsize=27 if big else 20, color=col, va="baseline")
        bb = t.get_window_extent(r)
        spans.append((key, bb.x0, bb.x1))
        x = bb.x1 / wpx + 0.002
    x0, x1 = spans[0][1], spans[-1][2]
    fig.savefig(f"{name}.png", dpi=534, bbox_inches="tight", pad_inches=0.02, transparent=True)
    plt.close(fig)
    return {k: [float((a - x0) / (x1 - x0)), float((b - x0) / (x1 - x0))] for k, a, b in spans if k}


SPANS = {}
# 7쪽: 흡수 옴전력 밀도의 세 항 (위치마다 다른 psi(r, z))
SPANS["pe3"] = colored("n_pe3", [
    (r"$p_e = \frac{1}{2}\,\mathrm{Re}(\sigma_p)\,I_0^2\;$", INK, None), (r"$[\,$", INK, None),
    (r"$|\tilde{E}_\mathrm{in}|^2$", BLUE, "in"), (r"$\;+\;$", INK, None),
    (r"$k^2|\tilde{E}_\mathrm{out}|^2$", ORANGE, "out"), (r"$\;+\;$", INK, None),
    (r"$2k\,|\tilde{E}_\mathrm{in}||\tilde{E}_\mathrm{out}|\cos(\phi+\psi)$", NAVY, "x"), (r"$\,]$", INK, None)])
# 5쪽: 부피 적분한 흡수 전력 (0D에서는 상수 계수 R', psi_0만 남는다)
SPANS["pabs"] = colored("n_pabs3", [
    (r"$P_\mathrm{abs} = \frac{1}{2}\,$", INK, None), (r"$I_0^{\,2}$", INK, "i0"), (r"$\;[\,$", INK, None),
    (r"$R^{\prime}_\mathrm{in}$", BLUE, "in"), (r"$\;+\;$", INK, None),
    (r"$k^2 R^{\prime}_\mathrm{out}$", ORANGE, "out"), (r"$\;+\;$", INK, None),
    (r"$2k\,R^{\prime}_{x}\cos(\phi+\psi_0)$", NAVY, "x"), (r"$\,]$", INK, None)])
json.dump(SPANS, open("spans.json", "w"))
frac = SPANS


def arrow(ax, p0, p1, col, lw=2.6):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, mutation_scale=22, shrinkA=0, shrinkB=0))


# 5쪽: 두 코일 전류의 페이저 (크기비 k, 위상차 phi)
fig, ax = plt.subplots(figsize=(3.6, 2.6), dpi=300)
phi = np.deg2rad(52)
a, b = np.array([1.0, 0.0]), 0.72 * np.array([np.cos(phi), np.sin(phi)])
ax.plot([-0.05, 1.12], [0, 0], color="#B8BECB", lw=0.9, zorder=0)
arrow(ax, (0, 0), a, BLUE)
arrow(ax, (0, 0), b, ORANGE)
ax.add_patch(Arc((0, 0), 0.5, 0.5, theta1=0, theta2=np.rad2deg(phi), color=INK, lw=1.2))
ax.text(0.31, 0.12, r"$\phi$", fontsize=20, color=INK)
ax.text(0.80, -0.16, r"$I_\mathrm{in}$", fontsize=20, color=BLUE)
ax.text(b[0] - 0.02, b[1] + 0.05, r"$I_\mathrm{out}$", fontsize=20, color=ORANGE)
ax.set_xlim(-0.08, 1.15); ax.set_ylim(-0.22, 0.75); ax.set_aspect("equal"); ax.axis("off")
fig.savefig("fig_phasor.png", dpi=300, bbox_inches="tight", pad_inches=0.03, transparent=True)
plt.close(fig)

# 6쪽: 한 위치에서 두 코일 장의 합 (사이 각 phi + psi)
fig, ax = plt.subplots(figsize=(4.4, 2.8), dpi=300)
th = np.deg2rad(58)
a = np.array([1.0, 0.0]); b = 0.8 * np.array([np.cos(th), np.sin(th)]); c = a + b
ax.plot([1.0, 1.42], [0, 0], color="#8C93A3", lw=1.0, ls=(0, (4, 3)), zorder=0)
arrow(ax, (0, 0), a, BLUE)
arrow(ax, a, c, ORANGE)
arrow(ax, (0, 0), c, NAVY, lw=3.2)
ax.add_patch(Arc(a, 0.46, 0.46, theta1=0, theta2=np.rad2deg(th), color=INK, lw=1.2))
ax.text(1.27, 0.10, r"$\phi+\psi$", fontsize=18, color=INK)
ax.text(0.30, -0.17, r"$I_0\,\tilde{E}_\mathrm{in}$", fontsize=18, color=BLUE)
ax.text(1.50, 0.44, r"$k\,e^{j\phi}I_0\,\tilde{E}_\mathrm{out}$", fontsize=18, color=ORANGE)
ax.text(0.42, 0.47, r"$E_\theta$", fontsize=20, color=NAVY)
ax.set_xlim(-0.05, 2.25); ax.set_ylim(-0.24, 0.8); ax.set_aspect("equal"); ax.axis("off")
fig.savefig("fig_sum.png", dpi=300, bbox_inches="tight", pad_inches=0.03, transparent=True)
plt.close(fig)

import glob
for f in sorted(glob.glob("*.png")):
    print(f, Image.open(f).size)
print(frac)
