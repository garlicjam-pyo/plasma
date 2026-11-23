import sys, numpy as np
import os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../sim"))
from hybrid.config import Config
from hybrid.coupled import solve_point
base = Config()
def heat_map(cfg):
    s = solve_point(cfg)
    g = s.grid; p = s.heating.p_abs          # (Nzp, Nr)
    Nzp = p.shape[0]
    z = g.z[:Nzp]; dz = g.dz[:Nzp]
    return s, g, p, z, dz
def sep_metric(p, g, dz):
    W = p * np.sqrt(g.area)[None, :] * np.sqrt(dz)[:, None]
    sv = np.linalg.svd(W, compute_uv=False)
    return sv[0]**2 / (sv**2).sum()
L = base.geom.L
for name, cfg in [("single_series", base.with_op(coil_mode="single_series")),
                  ("single_inner", base.with_op(coil_mode="single_inner")),
                  ("dual k1 phi0", base.with_op(k=1.0, phi=0.0)),
                  ("dual k1 phi90", base.with_op(k=1.0, phi=np.pi/2)),
                  ("dual k1 phi180", base.with_op(k=1.0, phi=np.pi)),
                  ("dual k2 phi180", base.with_op(k=2.0, phi=np.pi)),
                  ("dual k0.5 phi180", base.with_op(k=0.5, phi=np.pi))]:
    s, g, p, z, dz = heat_map(cfg)
    m = sep_metric(p, g, dz)
    # 깊이별 정규화 반경 분포 (면적 가중 합 = 1)
    depth = L - z
    S = (p * dz[:, None]).sum(0)
    sN = S / (S * g.area).sum()
    errs = []
    for d0 in (0.5e-2, 1e-2, 2e-2, 3e-2):
        j = np.argmin(abs(depth - d0)); pz = p[j]
        pzN = pz / (pz * g.area).sum()
        errs.append(np.abs(pzN - sN).dot(g.area) / 2)   # 총변동 거리 (0 ~ 1)
    wz = (p * g.area[None, :]).sum(1) * dz; wz /= wz.sum()
    tv = sum(wz[j] * np.abs(p[j] / (p[j] * g.area).sum() - sN).dot(g.area) / 2 for j in range(len(z)))
    print(f"{name:18s} rank1={m:.4f}  TV(d=0.5,1,2,3cm)={np.round(errs,3)}  가열가중TV={tv:.3f}  rho={s.metrics.rho:.3f} conv={s.converged}")
# ψ(r,z) = arg(A_out/A_in) 의 깊이 변화
s = solve_point(base)
g = s.grid; Ai, Ao = s.unit.A_in, s.unit.A_out
Nzp = s.heating.p_abs.shape[0]; z = g.z[:Nzp]; depth = L - z
psi = np.degrees(np.angle(Ao[:Nzp] / Ai[:Nzp]))
print("z grid (cm) near window:", np.round(depth[-8:]*100, 2), " Nzp", Nzp, "Nz", g.Nz)
for rr in (0.03, 0.06, 0.09, 0.12, 0.135, 0.15, 0.18):
    i = np.argmin(abs(g.r - rr))
    row = [psi[np.argmin(abs(depth - d)), i] for d in (0.25e-2, 1e-2, 2e-2, 3e-2, 4e-2)]
    print(f"r={g.r[i]*100:5.1f} cm  psi(d=0.25,1,2,3,4 cm) = {np.round(row,1)}")
print("psi at window plane (within dielectric?) row:", np.round(np.degrees(np.angle(Ao[Nzp]/Ai[Nzp]))[::6],1))
