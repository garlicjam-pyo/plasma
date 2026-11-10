"""슬라이드 3–7의 식 이미지 (기존 덱과 같은 글꼴·색·해상도)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
matplotlib.rcParams["mathtext.fontset"] = "cm"
EQ = {
    "n_avg":    r"$\langle n \rangle_S = \dfrac{1}{A_S}\int_S n(r, z_w)\,dA$",
    "n_rhotgt": r"$\rho \equiv n_c\,/\,n_\mathrm{edge}, \qquad \Delta\bar{n}_w = 0, \quad \Delta\rho \neq 0$",
    "n_pabs1":  r"$P_\mathrm{abs} = \frac{1}{2}\,|I_\mathrm{RF}|^2\;\mathrm{Re}\left(\dfrac{\omega^2M^2}{Z_p}\right)$",
    "n_ip":     r"$I_p = \dfrac{j\omega\,(M_{ip}\,I_\mathrm{in} + M_{op}\,I_\mathrm{out})}{Z_p}$",
    "n_pabs2":  r"$P_\mathrm{abs} = \frac{1}{2}R_p|I_p|^2 = \frac{\omega^2 R_p\, I_0^2}{2\,|Z_p|^2}\left[M_{ip}^2 + k^2M_{op}^2 + 2k\,M_{ip}M_{op}\cos\phi\right]$",
    "n_vin":    r"$V_\mathrm{in} = Z_{ii}\,I_\mathrm{in} + Z_{io}\,I_\mathrm{out}$",
    "n_vout":   r"$V_\mathrm{out} = Z_{oi}\,I_\mathrm{in} + Z_{oo}\,I_\mathrm{out}$",
    "n_zio":    r"$Z_{io} = Z_{oi} = j\omega M_{io} + \dfrac{\omega^2 M_{ip} M_{op}}{Z_p}$",
}
for k, tex in EQ.items():
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex, fontsize=20, color="#1F2340")
    fn = f"{k}.png"
    fig.savefig(fn, dpi=534, bbox_inches="tight", pad_inches=0.02, transparent=True)
    plt.close(fig)
    print(k, Image.open(fn).size)
