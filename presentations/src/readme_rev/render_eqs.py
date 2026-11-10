import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
matplotlib.rcParams['mathtext.fontset'] = 'cm'
EQ = {
 'n_nc':     r'$n_c = \dfrac{2}{r_c^2}\int_0^{r_c} n(r,z_w)\,r\,dr$',
 'n_nedge':  r'$n_\mathrm{edge} = \dfrac{2}{r_2^2-r_1^2}\int_{r_1}^{r_2} n(r,z_w)\,r\,dr$',
 'n_rhotgt': r'$\rho \equiv n_c\,/\,n_\mathrm{edge}, \qquad \Delta\bar{n}_w = 0, \quad \Delta\rho \neq 0$',
 'n_pabs1':  r'$P_\mathrm{abs} = \frac{1}{2}\,|I_\mathrm{RF}|^2\;\mathrm{Re}\left(\dfrac{\omega^2M^2}{Z_p}\right)$',
 'n_nw':     r'$\bar{n}_w = \dfrac{2}{R_w^2}\int_0^{R_w} n(r,z_w)\,r\,dr$',
 'n_zp':     r'$Z_p = R_p + j\omega\,(L_g + L_p)$',
 'n_single': r'$\Delta\bar{n}_w = \frac{d\bar{n}_w}{dP}\,\Delta P = 0 \;\;\Rightarrow\;\; \Delta P = 0 \;\;\Rightarrow\;\; \Delta\rho = \frac{d\rho}{dP}\,\Delta P = 0$',
 'n_sec':    r'$0 = -j\omega\left(M_{ip}\,I_\mathrm{in} + M_{op}\,I_\mathrm{out}\right) + Z_p\,I_p$',
 'n_cur':    r'$I_\mathrm{in} = I_0, \qquad I_\mathrm{out} = k\,e^{j\phi} I_0$',
 'n_pabs2':  r'$P_\mathrm{abs} = \frac{1}{2}R_p|I_p|^2 = \frac{\omega^2 R_p\, I_0^2}{2\,|Z_p|^2}\left[M_{ip}^2 + k^2M_{op}^2 + 2k\,M_{ip}M_{op}\cos\phi\right]$',
 'n_port':   r'$V_\mathrm{in} = Z_{ii}\,I_\mathrm{in} + Z_{io}\,I_\mathrm{out}, \qquad V_\mathrm{out} = Z_{oi}\,I_\mathrm{in} + Z_{oo}\,I_\mathrm{out}$',
 'n_zmat':   r'$Z_{ii} = R_i + j\omega L_i + \frac{\omega^2M_{ip}^2}{Z_p}, \qquad Z_{io} = Z_{oi} = j\omega M_{io} + \frac{\omega^2M_{ip}M_{op}}{Z_p}$',
}
from PIL import Image
for k, tex in EQ.items():
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex, fontsize=20, color='#1F2340')
    fn = f'{k}.png'
    fig.savefig(fn, dpi=534, bbox_inches='tight', pad_inches=0.02, transparent=True)
    plt.close(fig)
    print(k, Image.open(fn).size)
