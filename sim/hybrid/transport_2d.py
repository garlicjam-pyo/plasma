"""(r, z) 2D 수송 모델: 반경 1D 축소의 오차를 재기 위한 검증판 (발표 덱 9·10쪽의 식 그대로).

    입자   : ∇·Γ = n_e n_g K_iz(T_e) ,                 Γ = −μ_i ∇(n_e T_e)
    에너지 : ∇·q = p_abs + J·E_a − P_coll ,            q = (5/2) e T_e Γ − κ_e ∇T_e

- 셀마다 n_e, T_e 를 미지수로 두는 유한체적법 (덱 부록 20쪽). 미지수 2·Nr·Nz 개.
- 경계: 축은 대칭, 바닥·창·측벽은 Bohm 유출 Γ·n̂ = n_w u_B, q·n̂ = e Γ (2 T_e + V_s).
- z 방향 분포와 T_e 의 z 변화를 가정하지 않고 직접 푼다. 그 밖의 닫힘(계수, 경계)은 1D 모델과 같다.
- 인터페이스는 RadialTransport 와 같아서 coupled.solve_point 가 그대로 쓴다.
"""
from __future__ import annotations

import numpy as np
import scipy.sparse as sp

from . import physics as ph
from .config import E_CHARGE as e, M_ELECTRON as me, Config
from .em_field import Heating
from .newton import damped_newton
from .state import Grid, PlasmaState, PlasmaState2D
from .transport_1d import RadialTransport, TransportResult


class Transport2D:
    def __init__(self, grid: Grid, cfg: Config):
        self.grid, self.cfg = grid, cfg
        self.mu_i = ph.ion_mobility(cfg)
        self.Nz, self.Nr = grid.Nzp, grid.Nr
        self.dz = grid.dz[0]
        self.zp = grid.z[: grid.Nzp]
        self.vol = grid.area[None, :] * self.dz * np.ones((self.Nz, 1))      # 고리 셀 부피 [m^3]
        self.face_r = grid.perim[None, :] * self.dz                          # 반경 방향 경계면 넓이 (Nr+1 개)
        self.face_z = grid.area[None, :]                                     # z 방향 경계면 넓이
        radial = RadialTransport(grid, cfg)                                  # 기준값은 1D 모델과 같게
        self.n_ref = radial.n_ref
        nu_ref = radial.scale_n[0] / (grid.area[0] * radial.n_ref * cfg.geom.L)
        self.scale_n = self.vol * radial.n_ref * nu_ref
        self.scale_e = self.scale_n * e * 50.0
        self._build_coloring()

    # ------------------------------------------------------------------ 상태와 벡터
    def initial_state(self, guess=None) -> PlasmaState2D:
        """출발 상태. 2D 해가 오면 그대로, 1D 해가 오면 펼쳐서, 없으면 1D 모델을 먼저 풀어 쓴다."""
        if isinstance(guess, PlasmaState2D):
            return guess.copy()
        if not isinstance(guess, PlasmaState):
            from .coupled import solve_point                                  # 순환 임포트를 피하려고 여기서 부른다
            guess = solve_point(self.cfg.with_num(transport="radial_1d")).state
        return PlasmaState2D.from_radial(guess, self.grid, self.cfg)

    def pack(self, st: PlasmaState2D) -> np.ndarray:
        return np.concatenate([np.log(st.n / self.n_ref).ravel(), st.Te.ravel()])

    def unpack(self, x: np.ndarray) -> PlasmaState2D:
        N = self.Nz * self.Nr
        shape = (self.Nz, self.Nr)
        return PlasmaState2D(self.n_ref * np.exp(x[:N]).reshape(shape), x[N:].reshape(shape).copy(), self.zp)

    # ------------------------------------------------------------------ 수지 항
    def _wall(self, n, Te, d):
        """벽에 붙은 셀에서 Bohm 경계의 (선속, 에너지 선속, 전위차). d 는 셀 중심–벽 거리의 두 배."""
        uB = ph.bohm_speed(Te)
        n_w = n / (1.0 + uB * d / (2 * self.mu_i * Te))
        flux = n_w * uB
        return flux, e * flux * (2.0 + ph.V_SHEATH) * Te, Te * np.log(n_w / n)

    def terms(self, st: PlasmaState2D, heat: Heating) -> dict:
        """셀별 입자·에너지 수지의 각 항. 단위: 입자 [1/s], 에너지 [W]. 배열 모양 (Nz, Nr)."""
        cfg, dr, dz, mu = self.cfg, self.grid.dr, self.dz, self.mu_i
        n, Te = st.n, st.Te
        nT = n * Te
        kappa = cfg.num.kappa_scale * 2.5 * n * e**2 * Te / (me * cfg.op.n_gas * ph.K_el(Te))
        out_n = np.zeros_like(n); out_e = np.zeros_like(n); work = np.zeros_like(n)

        def add_face(a, b, area, d):
            """이웃 셀 a → b 사이 면의 선속을 양쪽 셀 수지에 더한다 (a, b 는 배열 조각)."""
            Tf = 0.5 * (Te[a] + Te[b])
            flux = -mu * (nT[b] - nT[a]) / d
            q = 2.5 * e * Tf * flux - 0.5 * (kappa[a] + kappa[b]) * (Te[b] - Te[a]) / d
            w = e * area * flux * (Tf * np.log(n[b] / n[a]) + (Te[b] - Te[a]))   # 양극성 장이 전자에 하는 일
            out_n[a] += area * flux; out_n[b] -= area * flux
            out_e[a] += area * q;    out_e[b] -= area * q
            work[a] += 0.5 * w;      work[b] += 0.5 * w

        s = np.s_
        add_face(s[:, :-1], s[:, 1:], self.face_r[:, 1:-1], dr)              # 반경 방향 안쪽 면
        add_face(s[:-1, :], s[1:, :], self.face_z, dz)                       # z 방향 안쪽 면
        wall_n = {}; wall_e = {}
        for name, cell, area, d in (("side", s[:, -1], self.face_r[:, -1], dr),
                                    ("bottom", s[0, :], self.face_z[0], dz), ("top", s[-1, :], self.face_z[0], dz)):
            flux, q, dphi = self._wall(n[cell], Te[cell], d)
            out_n[cell] += area * flux
            out_e[cell] += area * q
            work[cell] += e * area * flux * dphi
            wall_n[name] = np.sum(area * flux); wall_e[name] = np.sum(area * q)
        return dict(
            gen=self.vol * cfg.op.n_gas * ph.K_iz(Te) * n, div_n=out_n,
            heat=self.vol * heat.p_abs, coll=self.vol * e * n * ph.collision_loss_rate(Te, cfg.op.n_gas),
            div_e=out_e, work=work,
            loss_axial=np.array(wall_n["bottom"] + wall_n["top"]), wall_radial_n=wall_n["side"],
            wall_axial=np.array(wall_e["bottom"] + wall_e["top"]), wall_radial_e=wall_e["side"])

    def residual(self, x: np.ndarray, heat: Heating) -> np.ndarray:
        """무차원 잔차 벡터 (길이 2·Nz·Nr). 앞 절반이 입자 수지, 뒤 절반이 에너지 수지."""
        t = self.terms(self.unpack(x), heat)
        F_n = (t["div_n"] - t["gen"]) / self.scale_n
        F_e = (t["div_e"] + t["coll"] - t["heat"] - t["work"]) / self.scale_e
        return np.concatenate([F_n.ravel(), F_e.ravel()])

    # ------------------------------------------------------------------ 희소 야코비안
    def _build_coloring(self) -> None:
        """한 셀의 잔차는 자기와 상하좌우 셀에만 의존한다. (i + 2j) mod 5 로 색을 나누면
        같은 색 셀끼리는 서로의 잔차에 겹치지 않으므로, 색 5개 × 변수 2종 = 잔차 계산 10번으로 행렬이 나온다."""
        Nz, Nr = self.Nz, self.Nr
        jj, ii = np.meshgrid(np.arange(Nz), np.arange(Nr), indexing="ij")
        color = (ii + 2 * jj) % 5
        self._colors = []
        for c in range(5):
            cj, ci = jj[color == c], ii[color == c]
            rows, cols = [], []
            for dj, di in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):        # 흔든 셀과 그 이웃의 잔차
                rj, ri = cj + dj, ci + di
                ok = (rj >= 0) & (rj < Nz) & (ri >= 0) & (ri < Nr)
                rows.append(rj[ok] * Nr + ri[ok]); cols.append(cj[ok] * Nr + ci[ok])
            self._colors.append((cj * Nr + ci, np.concatenate(rows), np.concatenate(cols)))

    def jacobian(self, x: np.ndarray, heat: Heating, F0: np.ndarray) -> sp.csc_matrix:
        N = self.Nz * self.Nr
        R, C, V = [], [], []
        for var in (0, 1):                                                   # 0: ln n, 1: T_e
            for cells, rows, cols in self._colors:
                idx = cells + var * N
                h = 1e-7 * np.maximum(1.0, np.abs(x))
                xp = x.copy(); xp[idx] += h[idx]
                dF = self.residual(xp, heat) - F0
                for blk in (0, 1):                                           # 입자 잔차 블록, 에너지 잔차 블록
                    R.append(rows + blk * N); C.append(cols + var * N)
                    V.append(dF[rows + blk * N] / h[cols + var * N])
        return sp.csc_matrix((np.concatenate(V), (np.concatenate(R), np.concatenate(C))), shape=(2 * N, 2 * N))

    def solve(self, heat: Heating, guess: PlasmaState2D) -> TransportResult:
        num = self.cfg.num
        res = damped_newton(lambda x: self.residual(x, heat), lambda x, F: self.jacobian(x, heat, F),
                            self.pack(guess), num.newton_tol, num.newton_max)
        return TransportResult(self.unpack(res.x), res.iterations, res.residual_history, res.converged)
