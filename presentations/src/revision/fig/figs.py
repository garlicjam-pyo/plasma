"""개정본 발표용 개념 그림. 모두 정성 설명용이며 계산 결과가 아니다.

    python figs.py
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

for f in font_manager.findSystemFonts():
    if 'NotoSansCJK' in f and 'Regular' in f:
        font_manager.fontManager.addfont(f)
plt.rcParams.update({
    'font.family': 'Noto Sans CJK KR', 'font.size': 12.5, 'axes.linewidth': 0.9,
    'axes.edgecolor': '#4C5B72', 'xtick.color': '#4C5B72', 'ytick.color': '#4C5B72',
    'axes.labelcolor': '#17263C', 'mathtext.fontset': 'dejavusans', 'axes.unicode_minus': False,
})
BLUE, ORANGE, NAVY, GRAY, GREEN = '#3366CC', '#D9622B', '#004680', '#8C93A3', '#2E7D4F'


def clean(ax):
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


# F1 간섭: 단위 전류 응답과 |E|² (ψ = 0, k = 1 가정의 개념 곡선)
r = np.linspace(0, 21, 400)
a_in = np.exp(-((r - 6.0) / 3.6) ** 2)
a_out = np.exp(-((r - 15.0) / 3.6) ** 2)
fig, ax = plt.subplots(figsize=(4.3, 2.75), dpi=220)
ax.plot(r, a_in ** 2 + a_out ** 2 + 2 * a_in * a_out, color=NAVY, lw=2.2, label=r'$\phi+\psi=0$ (보강)')
ax.plot(r, a_in ** 2 + a_out ** 2 - 2 * a_in * a_out, color=NAVY, lw=2.2, ls='--', label=r'$\phi+\psi=\pi$ (상쇄)')
ax.plot(r, a_in ** 2, color=BLUE, lw=1.3, alpha=0.8, label=r'$|\mathcal{A}_{in}|^2$')
ax.plot(r, a_out ** 2, color=ORANGE, lw=1.3, alpha=0.8, label=r'$|\mathcal{A}_{out}|^2$')
ax.axvspan(9, 12, color='#EEF3FB', zorder=0)
ax.text(10.5, 0.55, '겹침', ha='center', color=NAVY, fontsize=12)
ax.set_xlim(0, 21); ax.set_ylim(0, 1.95)
ax.set_xlabel('반경 r (cm, 개념 좌표)'); ax.set_ylabel(r'$|E_\theta|^2/\omega^2I_0^2$')
ax.set_yticks([0, 0.5, 1])
ax.legend(fontsize=10.5, frameon=False, loc='upper center', ncol=2, columnspacing=0.8, handlelength=1.6, bbox_to_anchor=(0.5, 1.04))
clean(ax); fig.tight_layout(pad=0.3)
fig.savefig('interf.png', transparent=True); plt.close(fig)

# F2 전자 에너지 수송: 좁은 가열 영역과 넓어진 생성 (문서 그림 5와 같은 개념)
x = np.linspace(-3, 3, 400)
p = np.exp(-x ** 2 / (2 * 0.55 ** 2))
g = 0.8 * np.exp(-x ** 2 / (2 * 1.2 ** 2))
fig, ax = plt.subplots(figsize=(4.2, 2.65), dpi=220)
ax.plot(x, p, color=NAVY, lw=2.2, label=r'$p_{abs}$: 좁은 가열 영역')
ax.plot(x, g, color=GREEN, lw=2.2, ls='--', label=r'$G$: 수송으로 넓어진 생성')
ax.annotate('', xy=(2.15, 0.05), xytext=(0.62, 0.05), arrowprops=dict(arrowstyle='<->', color=GRAY, lw=1.2))
ax.text(1.38, 0.08, r'$\sim\lambda_\varepsilon$', ha='center', color='#4C5B72', fontsize=12.5)
ax.set_xlim(-3, 3); ax.set_ylim(0, 1.42)
ax.set_xlabel('반경 방향 위치 (개념 좌표)'); ax.set_ylabel('정규화 세기')
ax.set_yticks([0, 0.5, 1])
ax.legend(fontsize=11, frameon=False, loc='upper left')
clean(ax); fig.tight_layout(pad=0.3)
fig.savefig('energy.png', transparent=True); plt.close(fig)

# F3 평판: Dirichlet (8.15)와 Robin (8.28), 중심값으로 정규화
z = np.linspace(-0.5, 0.5, 300)              # z/L
c = 0.77                                     # u_B L/(4 D_a) 예시
dir_ = (0.25 - z ** 2) / 0.25
rob = (0.25 - z ** 2 + 0.25 / c) / (0.25 + 0.25 / c)
fig, ax = plt.subplots(figsize=(3.7, 2.7), dpi=220)
ax.axhline(1, color=GRAY, lw=1.0, ls=':')
ax.text(0.0, 1.04, r'균일 생성 $G_0$', ha='center', color=GRAY, fontsize=11)
ax.plot(z, dir_, color=NAVY, lw=2.0, ls='--', label='Dirichlet (8.15)')
ax.plot(z, rob, color=ORANGE, lw=2.2, label='Robin (8.28)')
ax.annotate(r'$n_s>0$', xy=(0.5, rob[-1]), xytext=(0.3, 0.88), color=ORANGE, fontsize=12,
            arrowprops=dict(arrowstyle='->', color=ORANGE, lw=1.0))
ax.set_xlim(-0.5, 0.5); ax.set_ylim(0, 1.15)
ax.set_xticks([-0.5, 0, 0.5]); ax.set_xticklabels(['−L/2', '0', 'L/2'])
ax.set_yticks([0, 0.5, 1])
ax.set_xlabel('높이 z'); ax.set_ylabel(r'$n(z)/n(0)$')
ax.legend(fontsize=10.5, frameon=False, loc='lower center')
clean(ax); fig.tight_layout(pad=0.3)
fig.savefig('slab.png', transparent=True); plt.close(fig)

# F4 무한 원통: 균일 생성과 포물선 해 (문서 그림 6)
rr = np.linspace(0, 1, 200)
fig, ax = plt.subplots(figsize=(3.6, 2.6), dpi=220)
ax.plot(rr, np.ones_like(rr), color=GRAY, lw=1.6, ls='--', label=r'균일 생성률 $G_0$')
ax.plot(rr, 1 - rr ** 2, color=NAVY, lw=2.2, label=r'밀도 $n(r)/n(0)$')
ax.set_xlim(0, 1); ax.set_ylim(0, 1.12)
ax.set_xticks([0, 0.5, 1]); ax.set_yticks([0, 0.5, 1])
ax.set_xlabel(r'$r/R$'); ax.set_ylabel(r'정규화된 $G,\ n$')
ax.legend(fontsize=11, frameon=False, loc='lower left')
clean(ax); fig.tight_layout(pad=0.3)
fig.savefig('cyl.png', transparent=True); plt.close(fig)
print('ok')
