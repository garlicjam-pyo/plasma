"""반경 1D 수송 모델: 전자 에너지 식과 입자 식의 잔차와 Newton 풀이 (발표 덱 9·10쪽).

덱의 2D 식을 z 로 적분해 r 만의 식으로 줄인 것이다. z 방향 분포는 기본 모드
n(r, z) = n0(r)·cos(k_z(z − L/2)) 로 두고 T_e 는 z 방향으로 균일하다고 본다.
z 로 적분한 양 N(r) = ∫n dz = n0·ḡ·L [m^-2] 에 대해 셀마다 수지를 세운다.

    입자   : ∇_r·Γ̂ = (ν_iz − ν_L) N ,                      Γ̂ = −μ_i ∂(N T_e)/∂r
    에너지 : ∇_r·q̂ = S + (J·E)_r − e N [C(T_e) + ν_L·7.2 T_e] ,
             q̂ = (5/2) e T_e Γ̂ − κ̂_e ∂T_e/∂r

S(r) = ∫p_abs dz 는 전자기장 모듈이 준다. ν_L 은 위·아래 벽 손실 주파수,
C(T_e) 는 충돌 손실률, 7.2 T_e 는 벽으로 나가는 쌍 하나가 가져가는 에너지다.
측벽(r = R)에서는 Bohm 유출 Γ̂ = N_w u_B, q̂ = e Γ̂ (2 T_e + V_s) 를 쓴다.

미지수 벡터 x = [ln(n0/n_ref) (Nr 개), T_e (Nr 개)], 잔차 F(x) = 0 을 푼다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import physics as ph
from .config import E_CHARGE as e, M_ELECTRON as me, Config
from .state import Grid, PlasmaState


@dataclass
class TransportResult:
    state: PlasmaState
    iterations: int
    residual_history: list = field(default_factory=list)   # Newton 반복별 max|F|
    converged: bool = False


class RadialTransport:
    """z 평균 반경 수송 모델. `residual` 이 잔차 함수, `solve` 가 Newton 풀이."""

    def __init__(self, grid: Grid, cfg: Config):
        self.grid, self.cfg = grid, cfg
        self.mu_i = ph.ion_mobility(cfg)
        Te0, n_star = ph.zero_d_initial(cfg)
        _, nuL0, _ = ph.axial_mode(np.array([Te0]), cfg)
        # 잔차를 무차원으로 만드는 기준값 (0D 균형값으로 고정 → 잔차 크기를 운전점끼리 비교 가능)
        self.n_ref = n_star
        self.scale_n = grid.area * n_star * cfg.geom.L * nuL0[0]            # 입자 수지 [1/s]
        self.scale_e = self.scale_n * e * 50.0                              # 에너지 수지 [W] (쌍당 약 50 V)

    # ------------------------------------------------------------------ 변수 변환
    def pack(self, st: PlasmaState) -> np.ndarray:
        return np.concatenate([np.log(st.n0 / self.n_ref), st.Te])

    def unpack(self, x: np.ndarray) -> PlasmaState:
        N = self.grid.Nr
        return PlasmaState(self.n_ref * np.exp(x[:N]), x[N:].copy())

    # ------------------------------------------------------------------ 수지 항
    def terms(self, st: PlasmaState, S: np.ndarray) -> dict:
        """셀별 입자·에너지 수지의 각 항을 계산한다. 단위: 입자 [1/s], 에너지 [W]."""
        g, cfg = self.grid, self.cfg
        n0, Te, dr = st.n0, st.Te, g.dr
        _, nuL, gbar = ph.axial_mode(Te, cfg)
        N = n0 * gbar * cfg.geom.L                           # z 적분 밀도 [m^-2]
        NT = N * Te
        # --- 안쪽 경계면(셀 i 와 i+1 사이)의 선속
        Tf = 0.5 * (Te[1:] + Te[:-1])
        flux = -self.mu_i * (NT[1:] - NT[:-1]) / dr          # Γ̂ [1/(m s)]
        nu_m = cfg.op.n_gas * ph.K_el(Te)
        kappa = cfg.num.kappa_scale * 2.5 * N * e**2 * Te / (me * nu_m)   # z 적분 열전도도
        q = 2.5 * e * Tf * flux - 0.5 * (kappa[1:] + kappa[:-1]) * (Te[1:] - Te[:-1]) / dr
        dphi = Tf * np.log(N[1:] / N[:-1]) + (Te[1:] - Te[:-1])   # 이웃 셀 사이 전위차 [V]
        # --- 측벽: Bohm 경계 −D_a ∂N/∂r = N_w u_B
        uB = ph.bohm_speed(Te[-1])
        N_w = N[-1] / (1.0 + uB * dr / (2 * self.mu_i * Te[-1]))
        flux_w = N_w * uB
        q_w = e * flux_w * (2.0 + ph.V_SHEATH) * Te[-1]
        dphi_w = Te[-1] * np.log(N_w / N[-1])
        # --- 경계면 값에 둘레를 곱해 셀 밖으로 나가는 양으로 (축에서는 0)
        out_n = np.zeros(g.Nr + 1); out_e = np.zeros(g.Nr + 1); work_f = np.zeros(g.Nr + 1)
        out_n[1:-1] = g.perim[1:-1] * flux
        out_e[1:-1] = g.perim[1:-1] * q
        work_f[1:-1] = e * g.perim[1:-1] * flux * dphi       # 양극성 장이 전자에 하는 일 (보통 음수)
        out_n[-1] = g.perim[-1] * flux_w
        out_e[-1] = g.perim[-1] * q_w
        work = 0.5 * (work_f[1:] + work_f[:-1])              # 면의 일을 양쪽 셀에 반씩
        work[-1] += 0.5 * work_f[-1] + e * g.perim[-1] * flux_w * dphi_w
        return dict(
            gen=g.area * cfg.op.n_gas * ph.K_iz(Te) * N,     # 이온화 생성
            loss_axial=g.area * nuL * N,                     # 위·아래 벽 입자 손실
            div_n=out_n[1:] - out_n[:-1],                    # 반경 방향 순유출
            heat=g.area * S,                                 # RF 가열
            coll=g.area * e * N * ph.collision_loss_rate(Te, cfg.op.n_gas),
            wall_axial=g.area * e * N * nuL * ph.WALL_COEF * Te,
            div_e=out_e[1:] - out_e[:-1],
            work=work,
            wall_radial_n=out_n[-1], wall_radial_e=out_e[-1],
        )

    def residual(self, x: np.ndarray, S: np.ndarray) -> np.ndarray:
        """무차원 잔차 벡터 F(x) (길이 2 Nr). 앞 절반이 입자 수지, 뒤 절반이 에너지 수지."""
        t = self.terms(self.unpack(x), S)
        F_n = (t["div_n"] + t["loss_axial"] - t["gen"]) / self.scale_n
        F_e = (t["div_e"] + t["coll"] + t["wall_axial"] - t["heat"] - t["work"]) / self.scale_e
        return np.concatenate([F_n, F_e])

    def jacobian(self, x: np.ndarray, S: np.ndarray, F0: np.ndarray) -> np.ndarray:
        """유한차분 야코비안. 셀 i 의 잔차는 i−1, i, i+1 셀에만 의존하므로
        3칸 간격으로 묶어 한꺼번에 흔들면 잔차 계산 6번으로 전체 행렬이 나온다."""
        N = self.grid.Nr
        J = np.zeros((2 * N, 2 * N))
        cells = np.arange(N)
        for var in (0, 1):                                   # 0: ln n, 1: T_e
            for color in range(3):
                idx = cells[color::3] + var * N
                h = 1e-7 * np.maximum(1.0, np.abs(x[idx]))
                xp = x.copy(); xp[idx] += h
                dF = self.residual(xp, S) - F0
                for c, hc in zip(cells[color::3], h):        # 각 열을 해당 셀 주변 행에만 기록
                    rows = np.arange(max(c - 1, 0), min(c + 2, N))
                    rows = np.concatenate([rows, rows + N])
                    J[rows, c + var * N] = dF[rows] / hc
        return J

    # ------------------------------------------------------------------ Newton 풀이
    def solve(self, S: np.ndarray, guess: PlasmaState) -> TransportResult:
        """가열 S(r) 가 주어졌을 때 F(x) = 0 을 감쇠 Newton 법으로 푼다."""
        num, N = self.cfg.num, self.grid.Nr
        x = self.pack(guess)
        F = self.residual(x, S)
        hist = [float(np.max(np.abs(F)))]
        for it in range(1, num.newton_max + 1):
            if hist[-1] < num.newton_tol:
                return TransportResult(self.unpack(x), it - 1, hist, True)
            dx = np.linalg.solve(self.jacobian(x, S, F), -F)
            # 한 번에 너무 멀리 가지 않게 제한: ln n 은 1, T_e 는 30 %
            lim = np.concatenate([np.full(N, 1.0), 0.3 * x[N:]])
            dx *= min(1.0, 1.0 / np.max(np.abs(dx) / lim))
            lam = 1.0
            for _ in range(10):                              # 잔차가 줄 때까지 보폭을 반으로
                x_new = x + lam * dx
                F_new = self.residual(x_new, S)
                if np.all(np.isfinite(F_new)) and np.max(np.abs(F_new)) < hist[-1]:
                    break
                lam *= 0.5
            x, F = x_new, F_new
            hist.append(float(np.max(np.abs(F))))
        return TransportResult(self.unpack(x), num.newton_max, hist, hist[-1] < num.newton_tol)
