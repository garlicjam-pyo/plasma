import sys, numpy as np
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../sim"))
from hybrid.config import Config
from hybrid.coupled import solve_point
from hybrid.control import solve_for_mean
base = Config()
print("geom:", base.geom)
for gap in (0.005, 0.015, 0.03):
    cfg = base.with_geom(coil_gap=gap)
    s1 = solve_point(cfg.with_op(coil_mode="single_series"))
    # 평균 밀도 5e16 고정, k 범위 끝에서의 ρ
    lo = solve_for_mean(cfg.with_op(k=0.3), 5e16); hi = solve_for_mean(cfg.with_op(k=3.0), 5e16)
    print(f"coil_gap={gap*100:.1f} cm (코일–플라즈마 {100*(gap+cfg.geom.window):.1f} cm): 단일 코일 ρ={s1.metrics.rho:.3f}, "
          f"이중 코일 ρ(k=0.3)={lo.metrics.rho:.3f}, ρ(k=3)={hi.metrics.rho:.3f}, 범위비={lo.metrics.rho/hi.metrics.rho:.2f}, P(k=0.3)={lo.cfg.op.P_tot:.0f} W")
