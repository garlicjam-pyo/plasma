import sys, numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'sim'))
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import theory_note_check as tc
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False
NAVY, BLUE, ORANGE, ORANGE_D, MUTED, TEXT = '#004680', '#3366CC', '#D9622B', '#B24A16', '#4C5B72', '#17263C'
OUT = str(Path(__file__).resolve().parent) + '/'

# ---------- Fig A: radial strip (S9)
fig, ax = plt.subplots(figsize=(9.0, 2.6), dpi=300)
ax.set_xlim(-0.6, 23.6); ax.set_ylim(-3.35, 2.5); ax.axis('off')
# regions band
ax.add_patch(plt.Rectangle((0, 0), 5, 0.42, color=BLUE, alpha=0.18, lw=0))
ax.add_patch(plt.Rectangle((12, 0), 2.5, 0.42, color=ORANGE, alpha=0.22, lw=0))
ax.plot([0, 21], [0, 0], color=MUTED, lw=1.2)
for x in range(0, 22, 3):
    ax.plot([x, x], [-0.08, 0.08], color=MUTED, lw=1)
    ax.text(x, -0.42, f'{x}', ha='center', va='top', fontsize=12.5, color=MUTED)
ax.text(21.9, -0.42, 'r [cm]', ha='left', va='top', fontsize=12.5, color=MUTED)
ax.plot([21, 21], [-0.35, 1.9], color=TEXT, lw=3)
ax.text(21.3, 1.55, '측벽', ha='left', va='center', fontsize=13, color=TEXT)
ax.text(2.5, 0.21, '중앙 영역', ha='center', va='center', fontsize=13, color=NAVY, weight='bold')
ax.text(13.25, 0.21, '가장자리', ha='center', va='center', fontsize=13, color=ORANGE_D, weight='bold')
# coils
for x in (3, 6, 9):
    ax.plot(x, 1.5, 'o', ms=9, color=BLUE)
for x in (12, 15, 18):
    ax.plot(x, 1.5, 'o', ms=9, color=ORANGE)
ax.text(6, 2.12, '안쪽 코일', ha='center', va='center', fontsize=13, color=BLUE, weight='bold')
ax.text(15, 2.12, '바깥 코일', ha='center', va='center', fontsize=13, color=ORANGE_D, weight='bold')
# distances
def dim(x1, x2, y, label, col):
    ax.annotate('', xy=(x2, y), xytext=(x1, y), arrowprops=dict(arrowstyle='<->', color=col, lw=1.4))
    ax.text((x1 + x2) / 2 - (1.2 if x1 == 5 else 0), y + 0.08, label, ha='center', va='bottom', fontsize=13, color=col, weight='bold')
dim(9, 12, 0.7, '3 cm', BLUE)
dim(5, 12, 1.12, '7 cm', ORANGE_D)
ax.plot([9, 9], [1.35, 0.6], color=BLUE, lw=0.8, ls=':'); ax.plot([12, 12], [1.35, 0.25], color=ORANGE, lw=0.8, ls=':')
ax.plot([5, 5], [0.25, 1.0], color=ORANGE, lw=0.8, ls=':')
# reach bars from inner coil's last turn (9 cm)
bars = [('장의 반경 번짐  2–3 cm', 2.3, '#7F8BA0'), (r'입자 확산 $\ell_r$  2–3 cm', 3.0, ORANGE), (r'에너지 수송 $\lambda_\varepsilon$  10–12 cm', 12.0, NAVY)]
for k, (lab, L, col) in enumerate(bars):
    y = -1.25 - 0.68 * k
    ax.add_patch(plt.Rectangle((9, y - 0.16), min(L, 12.0), 0.32, color=col, alpha=0.85, lw=0))
    ax.text(8.7, y, lab, ha='right', va='center', fontsize=13, color=TEXT)
ax.text(9.1, -3.33, '↑ 안쪽 코일 마지막 턴(9 cm)에서 잰 길이 · 10 mTorr', ha='left', va='bottom', fontsize=12, color=MUTED)
plt.subplots_adjust(0, 0, 1, 1)
fig.savefig(OUT + 'strip.png', transparent=True)

# ---------- Fig B: lengths vs pressure (S11)
ps = np.arange(5, 41, 1.0)
st = [tc.state(p) for p in ps]
lam_kc = 119.0 / ps
lam_fl = np.array([s['lam_fluid'] for s in st]) * 100
lr = np.array([s['lr'] for s in st]) * 100
dl = np.array([s['delta'] for s in st]) * 100
fig, ax = plt.subplots(figsize=(5.3, 3.8), dpi=300)
ax.fill_between(ps, np.minimum(lam_kc, lam_fl), np.maximum(lam_kc, lam_fl), color=NAVY, alpha=0.12, lw=0)
ax.plot(ps, lam_kc, color=NAVY, lw=2.2, label=r'$\lambda_\varepsilon$ (Kim–Chung 값 1/p 환산)')
ax.plot(ps, lam_fl, color=NAVY, lw=1.5, ls='--', label=r'$\lambda_\varepsilon$ (유체 추정)')
ax.plot(ps, lr, color=ORANGE, lw=2.2, label=r'$\ell_r$ (Bohm 벽 확산)')
ax.plot(ps, dl, color='#8C93A3', lw=1.8, label='δ (표피 깊이)')
ax.axhline(6 / np.pi, color=ORANGE, lw=0.9, ls=':')
ax.text(40.5, 6 / np.pi, 'L/π', fontsize=11.5, color=ORANGE_D, va='center', ha='left')
for y, lab, x0 in ((7, '7 cm  바깥 코일 → 중앙', 22.5), (3, '3 cm  안쪽 코일 → 가장자리', 11.5)):
    ax.axhline(y, color=TEXT, lw=1.0, ls=(0, (4, 3)))
    ax.text(x0, y * 1.04, lab, fontsize=11.5, color=TEXT, va='bottom')
ax.plot([17], [7], 'o', color=NAVY, ms=6); ax.annotate('17 mTorr', (17, 7), (10.5, 4.6), fontsize=11.5, color=NAVY, arrowprops=dict(arrowstyle='-', color=NAVY, lw=0.8))
ax.plot([39.7], [3], 'o', color=NAVY, ms=6); ax.annotate('약 40 mTorr', (39.7, 3), (29, 1.22), fontsize=11.5, color=NAVY, arrowprops=dict(arrowstyle='-', color=NAVY, lw=0.8))
ax.set_yscale('log'); ax.set_ylim(1.0, 30); ax.set_xlim(5, 40)
ax.set_yticks([1, 2, 3, 5, 7, 10, 20, 30]); ax.set_yticklabels(['1', '2', '3', '5', '7', '10', '20', '30'])
ax.set_xlabel('압력 [mTorr]', fontsize=12, color=MUTED); ax.set_ylabel('길이 [cm]', fontsize=12, color=MUTED)
ax.tick_params(labelsize=11.5, colors=MUTED)
for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
for sp in ('left', 'bottom'): ax.spines[sp].set_color('#B8BFCC')
ax.legend(fontsize=11, frameon=False, loc='upper right', handlelength=1.6)
plt.tight_layout(pad=0.3)
fig.savefig(OUT + 'pressure.png', transparent=True)
print('ok', lam_fl[[0,5,15,25,35]], lr[[0,5,15,25,35]])
