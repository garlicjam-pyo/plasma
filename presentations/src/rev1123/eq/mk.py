import json
E = []
def e(name, src): E.append(dict(name=name, src=src))
B, O, N = r'\color{#3366CC}', r'\color{#B24A16}', r'\color{#303399}'
# 3 문제 정의
e('rho', r'\rho\equiv\dfrac{n_c}{n_{\mathrm{edge}}}')
e('avg', r'n_X=\dfrac{1}{A_X}\displaystyle\int_{A_X} n(r,z_w)\,2\pi r\,dr')
# 4 왜 밀도비
e('scale', r'n(r)\to a\,n(r)\;\Rightarrow\;\Delta\ln n_c=\Delta\ln n_{\mathrm{edge}}\;\Rightarrow\;\Delta\ln\rho=0')
e('isat', r'I_{\mathrm{sat}}=0.61\,e\,n\,u_B A_p\;\Rightarrow\;\dfrac{I_{\mathrm{sat},c}}{I_{\mathrm{sat,edge}}}=\rho\sqrt{\dfrac{T_{e,c}}{T_{e,\mathrm{edge}}}}')
# 5 단일 코일 한계
e('te', r'\dfrac{K_{iz}(T_e)}{u_B(T_e)}=\dfrac{1}{n_g\,d_{\mathrm{eff}}}')
e('n0', r'n_0=\dfrac{P_{\mathrm{abs}}}{e\,u_B\,\varepsilon_T\,A_{\mathrm{eff}}}')
e('mode', r'-D_a\nabla^2 n=\nu_{iz}\,n\;\Rightarrow\;n\propto J_0\!\left(\dfrac{2.405\,r}{R}\right)\cos\dfrac{\pi z}{L}')
# 7 1단계 근거
e('axial', r'n(r,z)\simeq n_0(r)\cos\!\big[k_z\big(z-\tfrac{L}{2}\big)\big],\qquad k_z^{-1}\approx\dfrac{L}{\pi}\approx 1.9\ \mathrm{cm}\ \ll\ R=21\ \mathrm{cm}')
e('sep', r'p_{\mathrm{abs}}(r,z)\simeq S(r)\,w(z),\qquad S(r)=\displaystyle\int_0^L p_{\mathrm{abs}}\,dz')
# 9 전자기장
e('A', r'\dfrac{\partial}{\partial r}\!\left[\dfrac{1}{r}\dfrac{\partial (rA_\theta)}{\partial r}\right]+\dfrac{\partial^2 A_\theta}{\partial z^2}-j\omega\mu_0\sigma_pA_\theta=-\mu_0J_{\theta,\mathrm{coil}},\qquad E_\theta=-j\omega A_\theta')
e('sigma', r'\sigma_p=\dfrac{n_e\,e^2}{m_e\big(\nu_m(T_e)+j\omega\big)}')
e('super', r'A_\theta=I_0\big(A_{\mathrm{in}}+k\,e^{j\varphi}A_{\mathrm{out}}\big)')
e('pabs', r'p_{\mathrm{abs}}=\tfrac12\,\mathrm{Re}(\sigma_p)\,\omega^2I_0^2\Big[\textcolor{#3366CC}{|A_{\mathrm{in}}|^2}+\textcolor{#B24A16}{k^2|A_{\mathrm{out}}|^2}+\textcolor{#303399}{2k\,|A_{\mathrm{in}}||A_{\mathrm{out}}|\cos(\varphi+\psi)}\Big]')
e('S_I0', r'S(r)=\displaystyle\int_0^L p_{\mathrm{abs}}\,dz,\qquad P_{\mathrm{port}}=\tfrac12\,I_0^2\,\mathbf a^{\mathsf H}\,\mathrm{Re}(\mathbf Z)\,\mathbf a,\quad \mathbf a=\begin{bmatrix}1\\ k\,e^{j\varphi}\end{bmatrix}')
# 10 수송
e('part', r'\dfrac{1}{r}\dfrac{d}{dr}\big(r\,\Gamma_r\big)=n_gK_{iz}(T_e)\,N-\nu_LN,\qquad \Gamma_r=-\mu_i\dfrac{d\,(NT_e)}{dr},\qquad N(r)=\displaystyle\int_0^Ln\,dz')
e('energy', r'\underbrace{\dfrac{1}{r}\dfrac{d}{dr}\big(r\,q_r\big)}_{\rule{0pt}{0.62em}\text{①}}=\underbrace{\ S\vphantom{\dfrac{1}{r}}\ }_{\rule{0pt}{0.62em}\text{②}}+\underbrace{J_rE_a\vphantom{\dfrac{1}{r}}}_{\rule{0pt}{0.62em}\text{③}}-\underbrace{e\,N\,C(T_e)\vphantom{\dfrac{1}{r}}}_{\rule{0pt}{0.62em}\text{④}}-\underbrace{e\,N\nu_L\,\varepsilon_wT_e\vphantom{\dfrac{1}{r}}}_{\rule{0pt}{0.62em}\text{⑤}}')
e('q', r'q_r=\underbrace{\tfrac52\,e\,T_e\,\Gamma_r}_{\text{엔탈피 대류}}\ \underbrace{-\ \kappa_e\dfrac{dT_e}{dr}}_{\text{열전도}},\qquad \kappa_e=\tfrac52\,e\,N D_e,\quad D_e=\dfrac{e\,T_e}{m_e\nu_m}')
e('C', r'C(T_e)=n_g\Big[K_{iz}\varepsilon_{iz}+K_{ex}\varepsilon_{ex}+K_{el}\dfrac{3m_e}{M}T_e\Big]')
e('bc', r'r=0:\ \Gamma_r=q_r=0,\qquad r=R:\ \Gamma_r=N_wu_B,\ \ q_r=e\,\Gamma_r\,(2T_e+V_s)')
# 12 판정
e('J', r'J\equiv\dfrac{\partial(\ln\bar n_w,\ \ln\rho)}{\partial(\ln P_{\mathrm{tot}},\ \ln k,\ \varphi)}=\begin{bmatrix}J_{11}&J_{12}&J_{13}\\ J_{21}&J_{22}&J_{23}\end{bmatrix}')
e('hold', r'J_{11}\,\Delta\ln P_{\mathrm{tot}}+J_{12}\,\Delta\ln k=0\;\;\Rightarrow\;\;\Delta\ln P_{\mathrm{tot}}=-\dfrac{J_{12}}{J_{11}}\,\Delta\ln k')
e('gk', r'g_k\equiv\left.\dfrac{\partial\ln\rho}{\partial\ln k}\right|_{\bar n_w}=J_{22}-\dfrac{J_{21}\,J_{12}}{J_{11}}')
e('need', r'\rho:\ 1.2\to0.8\;\;\Rightarrow\;\;\Delta\ln k=\dfrac{\ln(0.8/1.2)}{g_k}=-\dfrac{0.405}{g_k}')
# 부록
e('pabs0', r'P_{\mathrm{abs}}=\tfrac12\,I_0^2\Big[R^{\prime}_{\mathrm{in}}+k^2R^{\prime}_{\mathrm{out}}+2k\,R^{\prime}_{\times}\cos\varphi\Big]')
e('ax1', r'-D_a\dfrac{\partial n}{\partial z}\Big|_{\text{벽}}=u_B\,n\;\;\Rightarrow\;\;x\tan x=\dfrac{u_BL}{2D_a},\qquad x\equiv\dfrac{k_zL}{2}')
e('ax2', r'N=\displaystyle\int_0^Ln\,dz=n_0\,\bar g\,L,\quad \bar g=\dfrac{\sin x}{x},\qquad \nu_L=D_a\,k_z^2')
e('ax3', r'\cos x=h_L,\qquad \nu_L=\dfrac{2\,h_L\,u_B}{\bar g\,L}')
e('port', r'\begin{bmatrix}V_{\mathrm{in}}\\ V_{\mathrm{out}}\end{bmatrix}=\begin{bmatrix}Z_{ii}&Z_{io}\\ Z_{oi}&Z_{oo}\end{bmatrix}\begin{bmatrix}I_{\mathrm{in}}\\ I_{\mathrm{out}}\end{bmatrix},\qquad Z_{io}=Z_{oi}')
e('I0', r'I_0=\sqrt{\dfrac{2P_{\mathrm{port}}}{\mathbf a^{\mathsf H}\,\mathrm{Re}(\mathbf Z)\,\mathbf a}},\qquad P_{\mathrm{tot}}\ \ge\ P_{\mathrm{port}}\ \ge\ P_{\mathrm{abs}}')
e('Pa', r'P_a=\tfrac12\,\mathrm{Re}\big(V_aI_a^{*}\big),\qquad P_{\mathrm{in}}+P_{\mathrm{out}}=P_{\mathrm{port}}')
e('tr1', r'V_{RF}=(R_a+j\omega L_a)\,I_{RF}-j\omega M\,I_p,\qquad 0=-j\omega M\,I_{RF}+(R_p+j\omega L_p)\,I_p')
e('tr2', r'R=R_a+\dfrac{\omega^2M^2R_p}{R_p^2+\omega^2L_p^2},\qquad L=L_a-\dfrac{\omega^2M^2L_p}{R_p^2+\omega^2L_p^2}')
e('zio', r'Z_{io}=\underbrace{j\omega M_{io}}_{\text{직접 결합}}+\underbrace{\dfrac{\omega^2M_{ip}M_{op}}{R_p+j\omega L_p}}_{\text{플라즈마 매개 결합}}')
e('ring', r'\langle n\rangle_{[a,b]}=\dfrac{\int_a^b n_w(r)\,2\pi r\,dr}{\int_a^b 2\pi r\,dr}=\dfrac{2}{b^2-a^2}\displaystyle\int_a^b n_w(r)\,r\,dr')
e('ring2', r'n_c=\langle n\rangle_{[0,\,r_c]},\quad n_{\mathrm{edge}}=\langle n\rangle_{[r_1,\,r_2]},\quad \bar n_w=\langle n\rangle_{[0,\,R_w]}')
e('defs', r'\mathrm{TV}=\tfrac12\displaystyle\int|s_1-s_2|\,dA,\qquad O=\displaystyle\int\min(s_{\mathrm{in}},s_{\mathrm{out}})\,dA,\qquad \eta_1=\dfrac{\sigma_1^2}{\sum_i\sigma_i^2}')
json.dump(E, open('eqs.json', 'w'), ensure_ascii=False, indent=0)
print(len(E))
