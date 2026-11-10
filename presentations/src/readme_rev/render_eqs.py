"""슬라이드 3–7의 식 이미지 (기존 덱과 같은 글꼴·색·해상도)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
matplotlib.rcParams["mathtext.fontset"] = "cm"
EQ = {
    "n_avg":    r"$\langle n \rangle_S = \dfrac{1}{A_S}\int_S n(r, z_w)\,dA$",
    "n_rhotgt": r"$\rho \equiv n_c\,/\,n_\mathrm{edge}, \qquad \Delta\bar{n}_w = 0, \quad \Delta\rho \neq 0$",
    # 교재 식 (2.31)–(2.32): 흡수 옴전력 (J = sigma_p E, 피크 페이저)
    "n_pe":     r"$p_e = \frac{1}{2}\,\mathrm{Re}(\sigma_p)\,|E_\theta|^2$",
    # 교재 식 (2.70), (2.73)
    "n_te":     r"$\dfrac{K_{iz}(T_e)}{u_B(T_e)} = \dfrac{1}{n_g\, d_\mathrm{eff}}$",
    "n_n0":     r"$n_0 = \dfrac{P_\mathrm{abs}}{e\,u_B\,\varepsilon_T\,A_\mathrm{eff}}$",
    # 두 코일 장의 중첩 (전도도 고정)
    "n_esup":   r"$E_\theta(r,z) = I_0\left[\tilde{E}_\mathrm{in}(r,z) + k\,e^{j\phi}\,\tilde{E}_\mathrm{out}(r,z)\right]$",
    "n_pe2":    r"$p_e = \frac{1}{2}\mathrm{Re}(\sigma_p)\,I_0^2\left[\,|\tilde{E}_\mathrm{in}|^2 + k^2|\tilde{E}_\mathrm{out}|^2 + 2k\,|\tilde{E}_\mathrm{in}||\tilde{E}_\mathrm{out}|\cos(\phi + \psi)\right]$",
    # 교재 식 (1.76)의 정상 상태, 기본 모드 (1.79)·(1.83)
    "n_diff":   r"$-D_a \nabla^2 n = \nu_{iz}\, n$",
    "n_mode":   r"$n \propto J_0\!\left(\dfrac{\chi_{01}\, r}{R}\right)\cos\dfrac{\pi z}{L}$",
}
for k, tex in EQ.items():
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, tex, fontsize=20, color="#1F2340")
    fn = f"{k}.png"
    fig.savefig(fn, dpi=534, bbox_inches="tight", pad_inches=0.02, transparent=True)
    plt.close(fig)
    print(k, Image.open(fn).size)
