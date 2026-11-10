"""이론 개정본(24쪽)의 수식. 이름은 문서 식 번호(e4_7 = 식 4.7). 번호 없는 식은 설명 이름.

    python mk.py && NODE_PATH=/opt/npm-tools/node_modules node render.js
"""
import json

E = {}


def e(name, src):
    E[name] = src


IN, OUT = r'\mathrm{in}', r'\mathrm{out}'
Ain, Aout = r'\mathcal A_{\mathrm{in}}', r'\mathcal A_{\mathrm{out}}'
PABS = r'p_{\mathrm{abs}}'

# 1장 ---------------------------------------------------------------
e('e1_1', r'\oint_{\mathcal C}\mathbf E\cdot d\boldsymbol\ell=-\frac{d}{dt}\int_{\mathcal S}\mathbf B\cdot d\mathbf S')
e('e1_2', r'2\pi rE_\theta=-\pi r^{2}\frac{dB_z}{dt}\quad\Longrightarrow\quad E_\theta=-\frac{r}{2}\frac{dB_z}{dt}')
e('e1_3', r'\tilde E_\theta(r,z)=-j\omega\tilde A_\theta(r,z)')
e('e1_4', r'E_\theta(r,z)=-j\omega I\mathcal A(r,z),\qquad ' + PABS + r'=\tfrac12\,\mathrm{Re}(\sigma_p)\,\omega^{2}|I|^{2}|\mathcal A|^{2}')
e('e1_5', r'\tilde E_\theta=-j\omega\left(I_{\mathrm{in}}' + Ain + r'+I_{\mathrm{out}}' + Aout + r'\right)')
e('e1_6', r'n_c=\frac{2}{r_c^{2}}\int_0^{r_c}n(r,z_w)\,r\,dr,\qquad r_c=5\ \mathrm{cm}')
e('e1_7', r'n_{\mathrm{edge}}=\frac{2}{r_2^{2}-r_1^{2}}\int_{r_1}^{r_2}n(r,z_w)\,r\,dr,\qquad (r_1,r_2)=(12,\,14.5)\ \mathrm{cm}')
e('e1_8', r'\rho=\frac{n_c}{n_{\mathrm{edge}}}')
e('nw', r'\bar n_w=\frac{2}{R_w^{2}}\int_0^{R_w}n(r,z_w)\,r\,dr')
e('target', r'\Delta\bar n_w=0,\qquad \Delta\rho\neq 0')
e('e1_9', r'\mathbf I=\begin{bmatrix}I_{\mathrm{in}}\\ I_{\mathrm{out}}\end{bmatrix}=I_0\underbrace{\begin{bmatrix}1\\ ke^{j\phi}\end{bmatrix}}_{\mathbf a(k,\phi)},\qquad k=\frac{|I_{\mathrm{out}}|}{|I_{\mathrm{in}}|},\qquad \phi=\arg I_{\mathrm{out}}-\arg I_{\mathrm{in}}')
e('e1_10', r'E_\theta=-j\omega I_0\left[' + Ain + r'(r,z)+ke^{j\phi}' + Aout + r'(r,z)\right]')
e('e1_11', r'\mathbf V=\mathbf Z(n)\,\mathbf I')
e('e1_12', r'P_{\mathrm{port}}=\tfrac12\,\mathrm{Re}\!\left(\mathbf I^{H}\mathbf V\right)=\tfrac12\,\mathrm{Re}\!\left(\mathbf I^{H}\mathbf Z\mathbf I\right)')
e('e1_13', r'P_{\mathrm{port}}=\frac{I_0^{2}}{2}\,\mathrm{Re}\!\left[\mathbf a^{H}\mathbf Z(n)\,\mathbf a\right],\qquad I_0=\sqrt{\frac{2P_{\mathrm{port}}}{\mathrm{Re}(\mathbf a^{H}\mathbf Z\mathbf a)}}')
e('ploss', r'P_{\mathrm{tot}}=P_{\mathrm{match,loss}}+P_{\mathrm{port}},\qquad P_{\mathrm{port}}=P_{\mathrm{coil,loss}}+P_{\mathrm{abs}}')
e('e1_14', r'P_{\mathrm{abs}}=e\,\varepsilon_T\,\dot N_{\mathrm{loss}}')

# 3장 ---------------------------------------------------------------
e('e3_1', PABS + r'=\tfrac12\,\mathrm{Re}(\sigma_p)\,|E_\theta|^{2},\qquad |E_\theta|^{2}\propto\left|' + Ain + r'+ke^{j\phi}' + Aout + r'\right|^{2}')

# 4장 ---------------------------------------------------------------
e('e4_1', r'G_{iz}=n_e\,n_g\,K_{iz}(T_e)\qquad[\mathrm{m^{-3}\,s^{-1}}]')
e('e4_2', r'\dot N_{\mathrm{gen}}=\int_V n_e n_g K_{iz}\,dV=\dot N_{\mathrm{wall}}=\oint_{\partial V}n_s\,u_B\,dA')
e('e4_3', r'u_B=\sqrt{\frac{eT_e}{M_{\mathrm{Ar}}}}')
e('e4_4', r'\bar n_V=h_V\,n_*,\qquad \oint_{\partial V}n_s\,dA=n_*\,A_{\mathrm{eff},*}')
e('e4_5', r'A_{\mathrm{eff},*}=2\pi R^{2}h_L+2\pi RL\,h_R')
e('e4_6', r'h_L=\frac{1}{2\pi R^{2}n_*}\int_{\mathrm{top+bottom}}n_s\,dA,\qquad h_R=\frac{1}{2\pi RLn_*}\int_{\mathrm{side}}n_s\,dA')
e('e4_7', r'\frac{K_{iz}(T_e)}{u_B(T_e)}=\frac{A_{\mathrm{eff},*}}{h_V\,n_g\,V},\qquad V=\pi R^{2}L')
e('e4_8', r'\varepsilon_c=\varepsilon_{iz}+\sum_q\frac{K_{ex,q}}{K_{iz}}\,\varepsilon_{ex,q}+\frac{K_{el}}{K_{iz}}\frac{3m_e}{M_{\mathrm{Ar}}}\,T_e')
e('e4_9', r'\varepsilon_T=\varepsilon_c+\varepsilon_{e,\mathrm{wall}}+\varepsilon_{i,\mathrm{wall}}')
e('e4_10', r'P_{\mathrm{abs}}=e\,\varepsilon_T\,\dot N_{\mathrm{wall}}=e\,\varepsilon_T\,n_*\,u_B\,A_{\mathrm{eff},*}')
e('e4_11', r'n_*=\frac{P_{\mathrm{abs}}}{e\,\varepsilon_T\,u_B\,A_{\mathrm{eff},*}}')

# 5장 ---------------------------------------------------------------
e('e5_1', r'm_e\frac{d\mathbf v_e}{dt}=-e\mathbf E-m_e\nu_m\mathbf v_e')
e('phasor', r'\mathbf E=\mathrm{Re}\{\tilde{\mathbf E}e^{j\omega t}\},\qquad \mathbf v=\mathrm{Re}\{\tilde{\mathbf v}e^{j\omega t}\}')
e('e5_2', r'm_e(j\omega+\nu_m)\,\tilde{\mathbf v}_e=-e\tilde{\mathbf E}')
e('e5_3', r'\tilde{\mathbf J}_e=-en_e\tilde{\mathbf v}_e=\frac{n_ee^{2}}{m_e(\nu_m+j\omega)}\,\tilde{\mathbf E}')
e('e5_4', r'\sigma_p(r,z)=\frac{n_e(r,z)\,e^{2}}{m_e(\nu_m+j\omega)},\qquad \mathrm{Re}\,\sigma_p=\frac{n_ee^{2}\nu_m}{m_e(\nu_m^{2}+\omega^{2})}')
e('e5_5', r'\langle\mathbf J\cdot\mathbf E\rangle=\tfrac12\,\mathrm{Re}\!\left(\tilde{\mathbf J}\cdot\tilde{\mathbf E}^{*}\right)')
e('e5_6', PABS + r'(r,z)=\tfrac12\,\mathrm{Re}\,\sigma_p(r,z)\,|E_\theta(r,z)|^{2}')
e('e5_7', r'\left[\frac{\partial}{\partial r}\frac{1}{r}\frac{\partial(r\,\cdot)}{\partial r}+\frac{\partial^{2}}{\partial z^{2}}-j\omega\mu_0\,\sigma_p(r,z)\right]A_\theta=-\mu_0J_{\mathrm{coil},\theta}')
e('e5_8', r'|E|\sim e^{-z/\delta},\qquad \delta\sim\frac{c}{\omega_{pe}},\qquad \omega_{pe}=\sqrt{\frac{n_ee^{2}}{m_e\varepsilon_0}}')

# 6장 ---------------------------------------------------------------
e('e6_1', r'A_\theta=I_0\left(' + Ain + r'+ke^{j\phi}' + Aout + r'\right)')
e('e6_2', r'E_\theta=-j\omega I_0\left(' + Ain + r'+ke^{j\phi}' + Aout + r'\right)')
e('e6_3', r'\frac{|E_\theta|^{2}}{\omega^{2}I_0^{2}}=\left(' + Ain + r'+ke^{j\phi}' + Aout + r'\right)\left(\mathcal A^{*}_{\mathrm{in}}+ke^{-j\phi}\mathcal A^{*}_{\mathrm{out}}\right)')
e('e6_4', r'\phantom{\frac{|E_\theta|^{2}}{\omega^{2}I_0^{2}}}=|' + Ain + r'|^{2}+k^{2}|' + Aout + r'|^{2}+2k\,\mathrm{Re}\{' + Ain + r'\mathcal A^{*}_{\mathrm{out}}e^{-j\phi}\}')
e('polar', Ain + r'=|' + Ain + r'|e^{j\alpha_{\mathrm{in}}},\qquad ' + Aout + r'=|' + Aout + r'|e^{j\alpha_{\mathrm{out}}},\qquad \psi(r,z)=\alpha_{\mathrm{out}}-\alpha_{\mathrm{in}}')
e('e6_5', r'\frac{|E_\theta|^{2}}{\omega^{2}I_0^{2}}=|' + Ain + r'|^{2}+k^{2}|' + Aout + r'|^{2}+2k\,|' + Ain + r'||' + Aout + r'|\cos\!\left[\phi+\psi(r,z)\right]')
e('cancel', r'|' + Ain + r'|=k\,|' + Aout + r'|\quad\text{그리고}\quad \phi+\psi=\pi\ \ (\mathrm{mod}\ 2\pi)')
e('e6_6', r'V_{\mathrm{RF}}=(R_a+j\omega L_a)\,I_{\mathrm{RF}}-j\omega M\,I_p')
e('e6_7', r'0=-j\omega M\,I_{\mathrm{RF}}+Z_p\,I_p,\qquad Z_p=R_p+j\omega(L_g+L_p)')
e('e6_8', r'V_{\mathrm{RF}}=\left(R_a+j\omega L_a+\frac{\omega^{2}M^{2}}{Z_p}\right)I_{\mathrm{RF}}')
e('e6_9', r'Z_{\mathrm{in}}=R_a+j\omega L_a+\frac{\omega^{2}M^{2}}{R_p+j\omega(L_g+L_p)}')
e('e6_10', r'\mathrm{Re}\!\left(\frac{\omega^{2}M^{2}}{Z_p}\right)=\frac{\omega^{2}M^{2}R_p}{R_p^{2}+\omega^{2}(L_g+L_p)^{2}}>0')
e('e6_11', r'\begin{bmatrix}V_{\mathrm{in}}\\ V_{\mathrm{out}}\end{bmatrix}=\underbrace{\begin{bmatrix}Z_{ii}&Z_{io}\\ Z_{oi}&Z_{oo}\end{bmatrix}}_{\mathbf Z[n(r,z)]}\begin{bmatrix}I_{\mathrm{in}}\\ I_{\mathrm{out}}\end{bmatrix}')
e('e6_12', r'Z_{io}\simeq j\omega M_{io}+\frac{\omega^{2}M_{ip}M_{op}}{Z_p}')
e('e6_13', r'n_e(r,z)\longrightarrow\sigma_p(r,z)\longrightarrow E_\theta(r,z)\longrightarrow ' + PABS + r'(r,z)\longrightarrow G(r,z)\longrightarrow n_e(r,z)')

# 7장 ---------------------------------------------------------------
e('e7_1', r'N\sim\frac{\lambda_{\mathrm{inel}}}{\lambda_m}')
e('e7_2', r'\lambda_{\varepsilon,\mathrm{rw}}\sim\lambda_m\sqrt{\frac{N}{3}}\sim\sqrt{\frac{\lambda_m\lambda_{\mathrm{inel}}}{3}}')
e('e7_3', r'w_e=\tfrac32\,e\,n_eT_e')
e('e7_4', r'\mathbf q_\varepsilon=\tfrac52\,eT_e\boldsymbol\Gamma_e-\kappa_e\nabla T_e,\qquad \kappa_e\simeq\tfrac52\,e\,n_eD_e')
e('e7_5', r'\frac{\partial w_e}{\partial t}+\nabla\cdot\mathbf q_\varepsilon=' + PABS + r'-P_{\mathrm{coll}}')
e('e7_6', r'P_{\mathrm{coll}}\simeq e\,n_en_gK_{iz}(T_e)\,\varepsilon_c(T_e)')
e('e7_7', r'-\kappa_e\nabla^{2}T_e=' + PABS + r'-P_{\mathrm{coll}}\quad\Longleftrightarrow\quad \kappa_e\nabla^{2}T_e-P_{\mathrm{coll}}=-' + PABS)
e('e7_8', r'P_{\mathrm{coll}}(T_{e0}+\delta T_e)\simeq P_{\mathrm{coll}}(T_{e0})+\alpha_\varepsilon\,\delta T_e')
e('e7_9', r'\alpha_\varepsilon\equiv\left.\frac{\partial P_{\mathrm{coll}}}{\partial T_e}\right|_{T_{e0}}>0')
e('e7_10', r'\kappa_e\nabla^{2}\delta T_e-\alpha_\varepsilon\,\delta T_e=-\delta p')
e('e7_11', r'\frac{d^{2}\delta T_e}{dx^{2}}-\frac{\alpha_\varepsilon}{\kappa_e}\,\delta T_e=0')
e('e7_12', r'\delta T_e(x)\propto\exp\!\left(-x/\lambda_{\varepsilon,\mathrm{fluid}}\right)')
e('e7_13', r'\lambda_{\varepsilon,\mathrm{fluid}}=\sqrt{\frac{\kappa_e}{\alpha_\varepsilon}}')
e('e7_14', r'\lambda_{\varepsilon,\mathrm{fluid}}\simeq\sqrt{\frac{(5/2)\,D_e}{n_g\,\dfrac{\partial}{\partial T_e}\big[K_{iz}(T_e)\,\varepsilon_c(T_e)\big]}}')
e('e7_15', PABS + r'\simeq P_{\mathrm{coll}}=e\,n_en_gK_{iz}\,\varepsilon_c')
e('e7_16', r'G_{\mathrm{local}}=n_en_gK_{iz}\simeq\frac{' + PABS + r'}{e\,\varepsilon_c}')
e('e7_17', r'G_{\mathrm{model}}(r,z)=\frac{' + PABS + r'(r,z)}{e\,\varepsilon_T}')
e('e7_18', r'G(r,z)=n_e(r,z)\,n_gK_{iz}\equiv\nu_{iz}\,n(r,z),\qquad \nu_{iz}=n_gK_{iz}')
e('e7_19', r'D_a\nabla^{2}n+\nu_{iz}n=0\quad\Longleftrightarrow\quad -\nabla^{2}n=\frac{\nu_{iz}}{D_a}\,n')

# 8장 ---------------------------------------------------------------
e('e8_1', r'\boldsymbol\Gamma_e=-\mu_e n\mathbf E-D_e\nabla n')
e('e8_2', r'\boldsymbol\Gamma_i=+\mu_i n\mathbf E-D_i\nabla n')
e('e8_3', r'-\mu_e n\mathbf E-D_e\nabla n=\mu_i n\mathbf E-D_i\nabla n')
e('e8_4', r'-(\mu_e+\mu_i)\,n\mathbf E=(D_e-D_i)\nabla n')
e('e8_5', r'\mathbf E=\frac{D_i-D_e}{\mu_e+\mu_i}\,\frac{\nabla n}{n}')
e('e8_6', r'\boldsymbol\Gamma_i=\left[\frac{\mu_i(D_i-D_e)}{\mu_e+\mu_i}-D_i\right]\nabla n')
e('e8_7', r'\phantom{\boldsymbol\Gamma_i}=-\frac{\mu_iD_e+\mu_eD_i}{\mu_e+\mu_i}\,\nabla n')
e('e8_8', r'\boldsymbol\Gamma=-D_a\nabla n,\qquad D_a=\frac{\mu_iD_e+\mu_eD_i}{\mu_e+\mu_i}')
e('e8_9', r'D_a\simeq\mu_i(T_e+T_i)=D_i\left(1+\frac{T_e}{T_i}\right)\qquad(\mu_e\gg\mu_i)')
e('e8_10', r'\frac{\partial n}{\partial t}+\nabla\cdot\boldsymbol\Gamma=G-L_{\mathrm{vol}}')
e('e8_11', r'\nabla\cdot(D_a\nabla n)+G(r,z)=0')
e('e8_12', r'D_a\left[\frac{1}{r}\frac{\partial}{\partial r}\left(r\frac{\partial n}{\partial r}\right)+\frac{\partial^{2}n}{\partial z^{2}}\right]+G(r,z)=0')
e('e8_13', r'D_a\frac{d^{2}n}{dz^{2}}+G_0=0\quad\Longrightarrow\quad \frac{d^{2}n}{dz^{2}}=-\frac{G_0}{D_a}')
e('e8_14', r'n(z)=-\frac{G_0}{2D_a}z^{2}+C_1z+C_2')
e('bc_dir', r"n'(0)=0\ \Rightarrow\ C_1=0,\qquad n(L/2)=0\ \Rightarrow\ C_2=\frac{G_0L^{2}}{8D_a}")
e('e8_15', r'n(z)=\frac{G_0}{2D_a}\left(\frac{L^{2}}{4}-z^{2}\right)')
e('e8_16', r'\frac{1}{r}\frac{d}{dr}\left(r\frac{dn}{dr}\right)=-\frac{G_0}{D_a}')
e('e8_17', r'\frac{d}{dr}\left(r\frac{dn}{dr}\right)=-\frac{G_0}{D_a}\,r')
e('e8_18', r'r\frac{dn}{dr}=-\frac{G_0}{2D_a}\,r^{2}+C_1')
e('e8_19', r'\frac{dn}{dr}=-\frac{G_0}{2D_a}\,r+\frac{C_1}{r}')
e('e8_20', r'n(r)=-\frac{G_0}{4D_a}\,r^{2}+C_2')
e('e8_21', r'n(r)=\frac{G_0}{4D_a}\left(R^{2}-r^{2}\right)')
e('e8_22', r'\Gamma_{\mathrm{diff},\perp}=-D_a\frac{\partial n}{\partial\hat n}')
e('e8_23', r'\Gamma_{\mathrm{Bohm}}\simeq u_B\,n_s')
e('e8_24', r'-D_a\frac{\partial n}{\partial\hat n}=u_B\,n_s')
e('e8_25', r"-D_a\,n'(L/2)=\frac{G_0L}{2}")
e('e8_26', r'u_B\,n(L/2)=u_B\left(-\frac{G_0L^{2}}{8D_a}+C_2\right)')
e('e8_27', r'C_2=\frac{G_0L^{2}}{8D_a}+\frac{G_0L}{2u_B}')
e('e8_28', r'n(z)=\frac{G_0}{2D_a}\left(\frac{L^{2}}{4}-z^{2}\right)+\frac{G_0L}{2u_B}')
e('e8_29', r"-D_a\,n'(R)=\frac{G_0R}{2}=u_B\,n(R)")
e('e8_30', r'n(r)=\frac{G_0}{4D_a}\left(R^{2}-r^{2}\right)+\frac{G_0R}{2u_B}')
e('e8_31', r'-D_a\nabla^{2}n=G_{\mathrm{given}}(r,z)')
e('modal', r'G=\sum_m G_m\varphi_m,\quad -\nabla^{2}\varphi_m=\Lambda_m\varphi_m\quad\Longrightarrow\quad n_m=\frac{G_m}{D_a\Lambda_m}')
e('e8_32', r'-D_a\nabla^{2}n=\nu_{iz}\,n')
e('e8_33', r'n(r,z)=n_*\,J_0\!\left(\frac{\chi_{01}r}{R}\right)\cos\!\left(\frac{\pi z}{L}\right),\qquad \chi_{01}\approx 2.4048')
e('e8_34', r'\frac{\nu_{iz}}{D_a}=\left(\frac{\chi_{01}}{R}\right)^{2}+\left(\frac{\pi}{L}\right)^{2}')
e('e8_35', r"Z(z)=\cos(k_zz),\qquad Z'(z)=-k_z\sin(k_zz)")
e('e8_36', r'D_a\,k_z\sin(k_zL/2)=u_B\cos(k_zL/2)')
e('e8_37', r'k_z\tan\!\left(\frac{k_zL}{2}\right)=\frac{u_B}{D_a}')
e('e8_38', r'D_a\left[\cos(k_zz)\,\frac{1}{r}\frac{d}{dr}\left(r\frac{df}{dr}\right)+f(r)\,\frac{d^{2}}{dz^{2}}\cos(k_zz)\right]+g(r)\cos(k_zz)=0')
e('e8_39', r'\frac{1}{r}\frac{d}{dr}\left(r\frac{df}{dr}\right)-k_z^{2}f=-\frac{g(r)}{D_a}')
e('e8_40', r'\frac{d^{2}f}{dr^{2}}+\frac{1}{r}\frac{df}{dr}-k_z^{2}f=0')
e('e8_41', r'f(r)=C_1I_0(k_zr)+C_2K_0(k_zr)')
e('e8_42', r'K_0(x)\sim\sqrt{\frac{\pi}{2x}}\,e^{-x},\qquad x\gg 1')
e('e8_43', r'\ell_r\equiv\frac{1}{k_z},\qquad k_z\tan\!\left(\frac{k_zL}{2}\right)=\frac{u_B}{D_a}')

# 9장 ---------------------------------------------------------------
e('e9_1', r'(p,\ P_{\mathrm{tot}},\ k,\ \phi)\ \xrightarrow{\ \ \text{물리 모델}\ \ }\ (\bar n_w,\ \rho)')
e('uy', r'\mathbf u=(P_{\mathrm{tot}},\,k,\,\phi)^{\mathsf T},\qquad \mathbf y=(\bar n_w,\,\rho)^{\mathsf T}')
e('e9_2', r'\Delta\mathbf y\simeq\mathbf J\,\Delta\mathbf u,\qquad \mathbf J=\begin{bmatrix}\partial_P\bar n_w&\partial_k\bar n_w&\partial_\phi\bar n_w\\ \partial_P\rho&\partial_k\rho&\partial_\phi\rho\end{bmatrix}_{\mathbf u_0,\,p_0}')
e('e9_3', r'\Delta\bar n_w=0,\qquad \Delta\rho\neq 0')

json.dump([{'name': k, 'src': v} for k, v in E.items()], open('eqs.json', 'w'), ensure_ascii=False)
print(len(E))
