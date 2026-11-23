import sys, numpy as np
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../sim"))
from hybrid.config import Config
from hybrid.coupled import solve_point
from hybrid.metrics import ring_average
base = Config()
a = solve_point(base); b = solve_point(base.with_num(axial_closure="h_factor"))
print(f"robin  : n̄={a.metrics.n_bar:.3e} ρ={a.metrics.rho:.3f}")
print(f"h_factor: n̄={b.metrics.n_bar:.3e} ρ={b.metrics.rho:.3f}  n̄비={b.metrics.n_bar/a.metrics.n_bar:.2f}  ρ비={b.metrics.rho/a.metrics.rho:.3f}")
for ks in (3.0,):
    c = solve_point(base.with_num(kappa_scale=ks)); print(f"kappa×{ks}: n̄비={c.metrics.n_bar/a.metrics.n_bar:.3f} ρ={c.metrics.rho:.3f}")
g = a.grid; Te = a.state.Te
import inspect
print(inspect.signature(ring_average))
Tc = ring_average(Te, g, 0, base.geom.r_c); Te_ = ring_average(Te, g, base.geom.r_1, base.geom.r_2)
print(f"T_e 중앙 {Tc:.3f} V, 가장자리 {Te_:.3f} V, sqrt 비 {np.sqrt(Tc/Te_):.4f}")
