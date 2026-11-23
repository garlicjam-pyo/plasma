"""단일 코일에서 가열 모양을 기준점에 고정하면 ρ가 어떻게 되는가 (발표 7쪽 근거, 2026-11-23).

수송 식은 밀도에 대해 1차 동차(N² 항 없음)이므로, 가열 모양이 같으면 밀도만 같은 배율로 바뀌고 ρ는 그대로다.
따라서 단일 코일에서 전력·압력이 ρ를 바꾸는 것은 전부 가열 모양 변화(전도도·표피 깊이의 밀도 의존) 때문이다.
"""
import dataclasses, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../sim"))
from hybrid.config import Config
from hybrid.coupled import solve_point, make_transport
from hybrid.state import Grid
from hybrid.metrics import wafer_metrics

base = Config()
ref = solve_point(base.with_op(coil_mode="single_series"))
shape = ref.heating.S / ref.heating.P_abs
print(f"기준 300 W, 10 mTorr: rho {ref.metrics.rho:.4f}")
for lab, kw in [("100 W", dict(P_tot=100)), ("1000 W", dict(P_tot=1000)), ("5 mTorr", dict(p_mtorr=5)), ("20 mTorr", dict(p_mtorr=20))]:
    cfg = base.with_op(coil_mode="single_series", **kw)
    sc = solve_point(cfg, guess=ref.state)                          # 자기일관: 가열을 반복마다 갱신
    grid = Grid(cfg); tr = make_transport(grid, cfg)
    heat = dataclasses.replace(sc.heating, S=shape * sc.heating.P_abs)  # 모양만 기준점으로 고정, 총량은 같게
    res = tr.solve(heat, tr.initial_state(sc.state))
    m = wafer_metrics(res.state, grid, cfg)
    print(f"{lab:8s} 자기일관 rho {sc.metrics.rho:.4f} | 모양 고정 rho {m.rho:.4f} ({100 * (m.rho / sc.metrics.rho - 1):+.1f}%)")
