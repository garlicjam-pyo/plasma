import json
E = {}
def e(name, src): E[name] = src
# S3 problem definition
e('rho_def', r'\rho\equiv\frac{n_c}{n_{\mathrm{edge}}},\qquad n_c=\frac{1}{\pi r_c^{2}}\int_{0}^{r_c}\! n(r,z_w)\,2\pi r\,dr,\qquad n_{\mathrm{edge}}=\frac{1}{\pi(r_2^{2}-r_1^{2})}\int_{r_1}^{r_2}\! n(r,z_w)\,2\pi r\,dr')
# S4 ICP heating
e('faraday', r'\oint \mathbf{E}\cdot d\boldsymbol{\ell}=-\frac{d\Phi_B}{dt}\;\;\Rightarrow\;\; E_\theta(r)=-\frac{r}{2}\,\frac{dB_z}{dt},\qquad E_\theta(0)=0')
e('skin', r'|E_\theta|\propto e^{-z/\delta},\qquad p_{\mathrm{abs}}\propto|E_\theta|^{2}\propto e^{-2z/\delta},\qquad \delta\simeq\frac{c}{\omega_{pe}}\approx 2\ \mathrm{cm}')
# S5 diffusion
e('da', r'\Gamma=-D_a\nabla n,\qquad D_a=\frac{\mu_i D_e+\mu_e D_i}{\mu_i+\mu_e}\approx\mu_i T_e')
e('slab_eq', r'D_a\frac{d^{2}n}{dz^{2}}+G_0=0,\qquad \left.\frac{dn}{dz}\right|_{0}=0,\qquad -D_a\left.\frac{dn}{dz}\right|_{L/2}=u_B\,n\!\left(\tfrac{L}{2}\right)')
e('slab_sol', r'n(z)=\frac{G_0}{2D_a}\left(\frac{L^{2}}{4}-z^{2}\right)+\frac{G_0L}{2u_B}')
e('slab_ratio', r'\frac{n(0)}{n(L/2)}=1+\frac{u_B L}{4D_a}\approx 1.8\qquad(D_a/u_B\approx 2\ \mathrm{cm})')
e('caseB', r'G=\nu_{iz}n\;\Rightarrow\;n\propto J_0\!\left(\frac{2.405\,r}{R}\right)\cos\frac{\pi z}{L}')
# S6 single coil
e('single', r'I\to aI\;\Rightarrow\;E_\theta\to aE_\theta\;\Rightarrow\;p_{\mathrm{abs}}\to a^{2}p_{\mathrm{abs}}\;\Rightarrow\;G\to a^{2}G\;\Rightarrow\;n\to a^{2}n')
e('single2', r'\Delta\ln n_c=\Delta\ln n_{\mathrm{edge}}=2\,\Delta\ln a\quad\Rightarrow\quad\Delta\ln\rho=0')
# S13 0D
e('pb', r'\underbrace{n_gK_{iz}(T_e)\,n_0V}_{\text{체적 생성}}=\underbrace{n_0\,u_B(T_e)\,A_{\mathrm{eff}}}_{\text{벽 손실}}\;\;\Rightarrow\;\;\frac{K_{iz}(T_e)}{u_B(T_e)}=\frac{1}{n_g\,d_{\mathrm{eff}}},\quad d_{\mathrm{eff}}=\frac{V}{A_{\mathrm{eff}}}')
e('eb', r'P_{\mathrm{abs}}=e\,\varepsilon_T\,n_0u_BA_{\mathrm{eff}}\;\;\Rightarrow\;\;n_0=\frac{P_{\mathrm{abs}}}{e\,u_B\,\varepsilon_T\,A_{\mathrm{eff}}},\qquad \varepsilon_T=\varepsilon_c+2T_e+5.2T_e')
e('aeff', r'A_{\mathrm{eff}}=2\pi R^{2}h_L+2\pi RL\,h_R,\qquad u_B=\sqrt{eT_e/M}')
# S14 absorption
e('sigma', r'm\frac{d\mathbf v}{dt}=-e\mathbf E-m\nu_m\mathbf v\;\;\Rightarrow\;\;\sigma_p=\frac{ne^{2}}{m(\nu_m+j\omega)},\qquad p_{\mathrm{abs}}=\tfrac12\,\mathrm{Re}\,\sigma_p\,|E_\theta|^{2}')
e('efield', r'E_\theta=-j\omega\left(I_{\mathrm{in}}A_{\mathrm{in}}+I_{\mathrm{out}}A_{\mathrm{out}}\right)')
e('e2', r'|E_\theta|^{2}=\omega^{2}\Big(|I_{\mathrm{in}}|^{2}|A_{\mathrm{in}}|^{2}+|I_{\mathrm{out}}|^{2}|A_{\mathrm{out}}|^{2}+2\,\mathrm{Re}\{I_{\mathrm{in}}A_{\mathrm{in}}\,I_{\mathrm{out}}^{*}A_{\mathrm{out}}^{*}\}\Big)')
e('cross', r'2\,\mathrm{Re}\{\cdots\}=2\,|I_{\mathrm{in}}||I_{\mathrm{out}}|\,|A_{\mathrm{in}}||A_{\mathrm{out}}|\cos(\varphi+\psi),\qquad \varphi\equiv\arg\frac{I_{\mathrm{out}}}{I_{\mathrm{in}}},\;\;\psi\equiv\arg\frac{A_{\mathrm{out}}}{A_{\mathrm{in}}}')
e('pabs3', r'p_{\mathrm{abs}}=|I_{\mathrm{in}}|^{2}p_{\mathrm{in}}+|I_{\mathrm{out}}|^{2}p_{\mathrm{out}}+2\,|I_{\mathrm{in}}||I_{\mathrm{out}}|\,p_{\times}(\varphi)')
e('pdefs', r'p_j\equiv\tfrac{\omega^{2}}{2}\mathrm{Re}\,\sigma_p|A_j|^{2},\qquad p_\times\equiv\tfrac{\omega^{2}}{2}\mathrm{Re}\,\sigma_p|A_{\mathrm{in}}||A_{\mathrm{out}}|\cos(\varphi+\psi)')
# S15 generation & diffusion
e('gen', r'G(\mathbf r)=\frac{p_{\mathrm{abs}}(\mathbf r)}{e\,\varepsilon_T}')
e('diff2d', r'\nabla\!\cdot\!(D_a\nabla n)+G=0,\qquad -D_a\frac{\partial n}{\partial\hat{\mathbf n}}=u_B\,n\ \ (\text{벽}),\qquad \left.\frac{\partial n}{\partial r}\right|_{r=0}=0')
e('green', r'n(\mathbf r)=\int\mathcal G(\mathbf r,\mathbf r^{\prime})\,G(\mathbf r^{\prime})\,dV^{\prime}')
e('ni', r'n_i=\int h_i(\mathbf r^{\prime})\,p_{\mathrm{abs}}(\mathbf r^{\prime})\,dV^{\prime},\qquad h_i(\mathbf r^{\prime})\equiv\frac{1}{e\,\varepsilon_T}\Big\langle\mathcal G(\mathbf r,\mathbf r^{\prime})\Big\rangle_{\mathbf r\,\in\,\text{영역 }i,\;z=z_w}')
e('quad', r'n_i=\alpha_i|I_{\mathrm{in}}|^{2}+\beta_i|I_{\mathrm{out}}|^{2}+2\gamma_i(\varphi)\,|I_{\mathrm{in}}||I_{\mathrm{out}}|')
e('coef', r'\alpha_i=\!\int\! h_i\,p_{\mathrm{in}}\,dV,\qquad \beta_i=\!\int\! h_i\,p_{\mathrm{out}}\,dV,\qquad \gamma_i(\varphi)=\!\int\! h_i\,p_{\times}\,dV')
# S16 ratio & matrix
e('rho_k', r'\rho=\frac{n_c}{n_{\mathrm{edge}}}=\frac{\alpha_c+2\gamma_c\,k+\beta_c\,k^{2}}{\alpha_{\mathrm{edge}}+2\gamma_{\mathrm{edge}}\,k+\beta_{\mathrm{edge}}\,k^{2}},\qquad k\equiv\frac{|I_{\mathrm{out}}|}{|I_{\mathrm{in}}|}')
e('kdef', r'\begin{bmatrix}\Delta\ln n_c\\ \Delta\ln n_{\mathrm{edge}}\end{bmatrix}=K\begin{bmatrix}\Delta\ln|I_{\mathrm{in}}|\\ \Delta\ln|I_{\mathrm{out}}|\end{bmatrix},\qquad K_{ij}\equiv\frac{\partial\ln n_i}{\partial\ln|I_j|}\ \ (\varphi\ \text{고정})')
e('kel', r'K_{i,\mathrm{in}}=\frac{2\big(\alpha_i|I_{\mathrm{in}}|^{2}+\gamma_i|I_{\mathrm{in}}||I_{\mathrm{out}}|\big)}{n_i},\qquad K_{i,\mathrm{out}}=\frac{2\big(\beta_i|I_{\mathrm{out}}|^{2}+\gamma_i|I_{\mathrm{in}}||I_{\mathrm{out}}|\big)}{n_i}')
e('euler', r'K_{i,\mathrm{in}}+K_{i,\mathrm{out}}=2')
e('fdef', r'f_i\equiv\frac{\beta_i|I_{\mathrm{out}}|^{2}+\gamma_i|I_{\mathrm{in}}||I_{\mathrm{out}}|}{n_i}')
e('kmat', r'K=2\begin{bmatrix}1-f_c & f_c\\ 1-f_{\mathrm{edge}} & f_{\mathrm{edge}}\end{bmatrix},\qquad \det K=4\,(f_{\mathrm{edge}}-f_c)')
# S17 interpretation
e('level', r'\Delta\ln|I_{\mathrm{in}}|=\Delta\ln|I_{\mathrm{out}}|=\Delta\ln a\;\Rightarrow\;\Delta\ln n_c=\Delta\ln n_{\mathrm{edge}}=2\,\Delta\ln a,\;\;\Delta\ln\rho=0')
e('shape', r'\Delta\ln|I_{\mathrm{in}}|=0,\ \Delta\ln|I_{\mathrm{out}}|=\Delta\ln k\;\Rightarrow\;\Delta\ln\rho=-2\,(f_{\mathrm{edge}}-f_c)\,\Delta\ln k')
e('kappa', r'K\begin{bmatrix}1\\1\end{bmatrix}=\begin{bmatrix}2\\2\end{bmatrix}\Rightarrow\sigma_{\max}\ge 2,\quad \sigma_{\max}\sigma_{\min}=|\det K|\;\Rightarrow\;\kappa(K)=\frac{\sigma_{\max}}{\sigma_{\min}}\ge\frac{1}{|f_{\mathrm{edge}}-f_c|}')
# S18 plan
e('sc', r'n=F(n;\,I)\;\Rightarrow\;\delta n=(\mathbb 1-F_n)^{-1}F_I\,\delta I')
e('relax', r'n^{(k+1)}=(1-\alpha)\,n^{(k)}+\alpha\,n_{\mathrm{calc}}')
# Appendix
e('kz', r'k_z\tan\!\left(\frac{k_zL}{2}\right)=\frac{u_B}{D_a},\qquad \frac{1}{r}\frac{d}{dr}\!\left(r\frac{df}{dr}\right)-k_z^{2}f=-\frac{g(r)}{D_a},\qquad \ell_r\equiv\frac{1}{k_z}')
e('jlp', r'\begin{bmatrix}\Delta\ln n_{\mathrm{avg}}\\ \Delta\ln\rho\end{bmatrix}=\begin{bmatrix}1 & 2(f_{\mathrm{avg}}-f_P)\\ 0 & -2(f_{\mathrm{edge}}-f_c)\end{bmatrix}\begin{bmatrix}\Delta\ln P_{\mathrm{abs}}\\ \Delta\ln k\end{bmatrix}')
e('jlp2', r'\Delta\ln n_i=2\,\Delta\ln a+2f_i\,\Delta\ln k,\qquad \Delta\ln P_{\mathrm{abs}}=2\,\Delta\ln a+2f_P\,\Delta\ln k')
e('flux', r'\Gamma_i=n_s\,u_B=h\,n\,u_B,\qquad u_B=\sqrt{\frac{e\,T_e}{M}}')
e('fluxratio', r'\rho_\Gamma\equiv\frac{\Gamma_{c}}{\Gamma_{\mathrm{edge}}}=\frac{h_c}{h_{\mathrm{edge}}}\cdot\rho\cdot\sqrt{\frac{T_{e,c}}{T_{e,\mathrm{edge}}}}')

# --- 본편용 짧은 식 (11-09 2차 정리)
e('rho_main', r'\rho\equiv\frac{n_c}{n_{\mathrm{edge}}}')
e('faraday_s', r'E_\theta(r)=-\frac{r}{2}\,\frac{dB_z}{dt}\quad\Rightarrow\quad E_\theta(0)=0')
e('skin_s', r'p_{\mathrm{abs}}\propto|E_\theta|^{2}\propto e^{-2z/\delta},\qquad \delta\approx 2\ \mathrm{cm}')
e('single_s', r'I\to aI\;\Rightarrow\;p_{\mathrm{abs}}\to a^{2}p_{\mathrm{abs}}\;\Rightarrow\;n\to a^{2}n\;\Rightarrow\;\rho=\frac{n_c}{n_{\mathrm{edge}}}\ \text{그대로}')
e('te_s', r'\frac{K_{iz}(T_e)}{u_B(T_e)}=\frac{1}{n_g\,d_{\mathrm{eff}}}')
e('n0_s', r'n_0=\frac{P_{\mathrm{abs}}}{e\,u_B\,\varepsilon_T\,A_{\mathrm{eff}}}')
e('pcross_s', r'p_\times\propto|A_{\mathrm{in}}||A_{\mathrm{out}}|\cos(\varphi+\psi)')
e('chain15', r'G=\frac{p_{\mathrm{abs}}}{e\,\varepsilon_T}\;\;\xrightarrow{\ \ \text{선형 확산}\ \ }\;\;n_i=\int h_i\,p_{\mathrm{abs}}\,dV')
e('shape_s', r'\Delta\ln\rho=-2\,(f_{\mathrm{edge}}-f_c)\,\Delta\ln k')
e('det_s', r'\det K\neq 0\;\Longleftrightarrow\;f_{\mathrm{edge}}\neq f_c')
e('kappa_s', r'\kappa(K)\ \ge\ \frac{1}{|f_{\mathrm{edge}}-f_c|}')
e('slab_step1', r'n(z)=C-\frac{G_0}{2D_a}\,z^{2}\qquad(\text{두 번 적분},\ n^{\prime}(0)=0)')
e('slab_step2', r'-D_a\,n^{\prime}(L/2)=\frac{G_0L}{2}=u_B\,n(L/2)\;\;\Rightarrow\;\;n(L/2)=\frac{G_0L}{2u_B}')
json.dump([{'name': k, 'src': v} for k, v in E.items()], open('eqs.json', 'w'), ensure_ascii=False)
print(len(E))
