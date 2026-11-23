import sys, numpy as np
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../sim"))
from hybrid.config import Config
from hybrid.coupled import solve_point
from hybrid import physics as ph
base = Config()
for P in (100, 300, 1000):
    s = solve_point(base.with_op(coil_mode="single_series", P_tot=P)); print(f"single P={P}: nbar={s.metrics.n_bar:.3e} rho={s.metrics.rho:.3f}")
print("Kiz ratio 3.28/3.10:", ph.K_iz(3.28)/ph.K_iz(3.10), " 3.277/3.135:", ph.K_iz(3.277)/ph.K_iz(3.135))
s=solve_point(base); print("Te min/max", s.state.Te.min(), s.state.Te.max(), "Kiz max/min", ph.K_iz(s.state.Te.max())/ph.K_iz(s.state.Te.min()))
# 코일별 가열 발자국 겹침 (단위 전류 응답의 |A|^2 Re σ 를 z 적분)
def footprints(cfg):
    s = solve_point(cfg); g = s.grid; Nzp = s.heating.p_abs.shape[0]; dz = g.dz[:Nzp]
    w = 2*np.pi*cfg.op.freq
    Si = (0.5*s.unit.re_sigma*(w*np.abs(s.unit.A_in[:Nzp]))**2*dz[:,None]).sum(0)
    So = (0.5*s.unit.re_sigma*(w*np.abs(s.unit.A_out[:Nzp]))**2*dz[:,None]).sum(0)
    si = Si/(Si*g.area).sum(); so = So/(So*g.area).sum()
    ov = (np.minimum(si, so)*g.area).sum()
    # 중앙(0–5 cm)과 가장자리(12–14.5) 가열 몫
    r = g.r
    fc_i = (si*g.area)[r < 0.05].sum(); fe_i = (si*g.area)[(r>0.12)&(r<0.145)].sum()
    fc_o = (so*g.area)[r < 0.05].sum(); fe_o = (so*g.area)[(r>0.12)&(r<0.145)].sum()
    return ov, fc_i, fe_i, fc_o, fe_o
for gap in (0.005, 0.015, 0.03):
    ov, a, b, c, d = footprints(base.with_geom(coil_gap=gap))
    print(f"d={100*(gap+0.015):.1f} cm overlap={ov:.3f}  inner: center {a:.3f} edge {b:.3f}  outer: center {c:.3f} edge {d:.3f}")
