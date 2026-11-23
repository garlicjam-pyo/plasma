import sys, numpy as np
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../sim"))
from hybrid.config import Config
from hybrid.coupled import solve_point
from hybrid.em_field import EMSolver
from hybrid.state import PlasmaState
base = Config()
s0 = solve_point(base); g = s0.grid
def shape(S): return S / (S * g.area).sum()
def tv(a, b): return 0.5 * np.abs(shape(a) - shape(b)).dot(g.area)
# (1) 진공(σ=0)에서의 ψ: 플라즈마 밀도를 거의 0 으로
em = EMSolver(g, base)
vac = PlasmaState(np.full(g.Nr, 1e6), np.full(g.Nr, 3.0))
u = em.solve_unit(vac)
print("vacuum psi range (deg):", np.round(np.degrees(np.angle(u.A_out / u.A_in)).min(), 4), np.round(np.degrees(np.angle(u.A_out / u.A_in)).max(), 4))
print("plasma psi range (deg):", np.round(np.degrees(np.angle(s0.unit.A_out[:24] / s0.unit.A_in[:24])).min(),2), np.round(np.degrees(np.angle(s0.unit.A_out[:24] / s0.unit.A_in[:24])).max(),2))
# (2) 단일 코일: 운전 조건이 바뀌어도 가열 모양 S(r)이 유지되는가
ref = solve_point(base.with_op(coil_mode="single_series"))
print("\n단일 코일(직렬) 가열 모양 변화 (TV 거리, 기준 300 W 10 mTorr):")
for P in (100, 1000):
    s = solve_point(base.with_op(coil_mode="single_series", P_tot=P)); print(f"  P={P} W: TV={tv(s.heating.S, ref.heating.S):.3f}  rho={s.metrics.rho:.3f}")
for p in (5, 20, 50):
    s = solve_point(base.with_op(coil_mode="single_series", p_mtorr=p)); print(f"  p={p} mTorr: TV={tv(s.heating.S, ref.heating.S):.3f}  rho={s.metrics.rho:.3f}")
# (3) 이중 코일: k, φ 에 따른 가열 모양 변화
print("\n이중 코일 가열 모양 변화 (기준 k=1, φ=0):")
for k, ph in ((0.5, 0), (2, 0), (1, 90), (1, -90), (1, 180), (2, 180)):
    s = solve_point(base.with_op(k=k, phi=np.radians(ph))); print(f"  k={k} φ={ph:4d}: TV={tv(s.heating.S, s0.heating.S):.3f}  rho={s.metrics.rho:.3f}  P_abs={s.heating.P_abs:.0f}")
# (4) ψ 의 역할: ψ 를 0 으로 둔(국소 근사) 간섭항으로 가열을 다시 만들면 ρ 가 어떻게 되나
from hybrid.coupled import make_transport
print("\nψ(r,z)를 0으로 둔 가열(=두 장이 같은 위상으로만 겹친다고 가정)과 실제의 비교 (k=1):")
for ph in (90, -90, 180):
    cfg = base.with_op(k=1.0, phi=np.radians(ph))
    s = solve_point(cfg)
    Ai, Ao = s.unit.A_in, s.unit.A_out
    Nzp = s.heating.p_abs.shape[0]
    w = 2*np.pi*base.op.freq
    Ein = w*np.abs(Ai[:Nzp]); Eout = w*np.abs(Ao[:Nzp])
    I0 = s.heating.I0
    p_true = 0.5*s.unit.re_sigma*np.abs(w*I0*(Ai[:Nzp] + np.exp(1j*np.radians(ph))*Ao[:Nzp]))**2
    p_loc = 0.5*s.unit.re_sigma*(I0**2)*(Ein**2 + Eout**2 + 2*Ein*Eout*np.cos(np.radians(ph)))
    dz = g.dz[:Nzp]
    St = (p_true*dz[:,None]).sum(0); Sl = (p_loc*dz[:,None]).sum(0)
    print(f"  φ={ph:4d}: check |p_true-heat|={np.abs(St-s.heating.S).max()/s.heating.S.max():.1e}  TV(true vs ψ=0)={tv(St,Sl):.3f}  P_true={(St*g.area).sum():.0f} W P_ψ0={(Sl*g.area).sum():.0f} W")
