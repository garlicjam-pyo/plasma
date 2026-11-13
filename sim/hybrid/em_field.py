"""2D (r, z) 축대칭 RF 유도장 풀이 (발표 덱 8쪽).

    [∂/∂r (1/r) ∂(r·)/∂r + ∂²/∂z² − jωμ0 σ_p] A_θ = −μ0 J_coil,θ ,   E_θ = −jω A_θ

- 셀 중심 유한차분. 축(r = 0)과 바깥 금속 경계(측벽·바닥·덮개)에서 A_θ = 0.
- σ_p 가 고정이면 식이 전류에 선형이다. 그래서 안쪽·바깥쪽 코일에 1 A 씩 흘린
  단위 응답 A_in, A_out 을 한 번씩만 풀고, (k, φ) 는 중첩으로 처리한다.
- 전류 진폭 I_0 는 포트 전력 조건으로 정한다 (덱 부록 16쪽).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu

from . import physics as ph
from .config import MU0, Config
from .state import Grid, PlasmaState


@dataclass
class UnitFields:
    """현재 플라즈마 상태에서의 단위 전류(1 A) 응답."""
    A_in: np.ndarray        # 안쪽 코일 1 A 의 A_θ [Wb/m], 모양 (Nz, Nr), 복소
    A_out: np.ndarray       # 바깥쪽 코일 1 A 의 A_θ
    re_sigma: np.ndarray    # 플라즈마 영역의 Re(σ_p) [S/m], 모양 (Nzp, Nr)
    R_pl: np.ndarray        # 2×2 플라즈마 부하 저항 행렬 [Ω] (P_abs = ½ I0² aᴴ R a)
    Z_port: np.ndarray      # 2×2 포트 임피던스 [Ω] (코일 저항 포함, 유도 전압으로 계산)


@dataclass
class Heating:
    """한 운전점 (P_tot, k, φ) 의 장과 가열."""
    I0: float               # 공통 전류 진폭 = 안쪽 코일 전류 크기(피크) [A]
    E: np.ndarray           # E_θ(r, z) [V/m], 모양 (Nz, Nr), 복소
    p_abs: np.ndarray       # 흡수 전력 밀도 [W/m^3], 모양 (Nzp, Nr)
    S: np.ndarray           # z 로 적분한 가열 ∫p_abs dz [W/m^2], 길이 Nr
    P_abs: float            # 플라즈마 총 흡수 전력 [W]
    P_coil: float           # 코일 저항 손실 [W]
    P_port: float           # 코일 단자 전력 [W]


class EMSolver:
    """격자·코일이 고정된 전자기장 풀이기. 상수 연산자는 한 번만 만든다."""

    def __init__(self, grid: Grid, cfg: Config):
        self.grid, self.cfg = grid, cfg
        Nr, Nz, dr = grid.Nr, grid.Nz, grid.dr
        r, rf, dz = grid.r, grid.r_face, grid.dz
        # --- 반경 연산자 ∂/∂r[(1/r) ∂(rA)/∂r] (삼중대각)
        up = np.zeros(Nr); lo = np.zeros(Nr); di = np.zeros(Nr)
        up[:-1] = r[1:] / (rf[1:-1] * dr**2)             # A_{i+1} 계수
        lo[1:] = r[:-1] / (rf[1:-1] * dr**2)             # A_{i-1} 계수
        di[:-1] -= r[:-1] / (rf[1:-1] * dr**2)           # 바깥쪽 면에서 A_i 계수
        di[1:] -= r[1:] / (rf[1:-1] * dr**2)             # 안쪽 면에서 A_i 계수
        di[0] -= 4.0 / dr**2                             # 축: A ∝ r 이므로 (1/r)∂(rA)/∂r = 4A_0/dr
        di[-1] -= 2.0 * r[-1] / (rf[-1] * dr**2)         # 측벽: A = 0
        Dr = sp.diags([lo[1:], di, up[:-1]], [-1, 0, 1])
        # --- z 연산자 ∂²/∂z² (셀 크기가 달라도 되도록 면 간격을 따로 계산)
        h = 0.5 * (dz[1:] + dz[:-1])                     # 이웃 셀 중심 사이 거리
        upz = np.zeros(Nz); loz = np.zeros(Nz); diz = np.zeros(Nz)
        upz[:-1] = 1.0 / (h * dz[:-1]); loz[1:] = 1.0 / (h * dz[1:])
        diz[:-1] -= upz[:-1]; diz[1:] -= loz[1:]
        diz[0] -= 2.0 / dz[0] ** 2                       # 바닥(웨이퍼): A = 0
        diz[-1] -= 2.0 / dz[-1] ** 2                     # 덮개: A = 0
        Dz = sp.diags([loz[1:], diz, upz[:-1]], [-1, 0, 1])
        self.lap = (sp.kron(Dz, sp.identity(Nr)) + sp.kron(sp.identity(Nz), Dr)).tocsc()
        # --- 코일 전류 분배 가중치 (1 A 가 흐를 때 각 셀이 받는 전류 몫)
        self.w_in = self._coil_weights(cfg.geom.r_in)
        self.w_out = self._coil_weights(cfg.geom.r_out)
        self.cell_vol = (grid.area[None, :] * dz[:, None])       # 고리 셀 부피 [m^3]

    def _coil_weights(self, radii) -> np.ndarray:
        """각 턴의 전류를 가까운 네 셀에 거리 비례(쌍선형)로 나눠 준다. 모양 (Nz, Nr)."""
        g = self.grid
        w = np.zeros((g.Nz, g.Nr))
        zc = self.cfg.geom.z_coil
        j = int(np.clip(np.searchsorted(g.z, zc) - 1, 0, g.Nz - 2))
        tz = (zc - g.z[j]) / (g.z[j + 1] - g.z[j])
        for rt in radii:
            i = int(np.clip(np.floor(rt / g.dr - 0.5), 0, g.Nr - 2))
            tr = rt / g.dr - 0.5 - i
            for jj, wz in ((j, 1 - tz), (j + 1, tz)):
                for ii, wr in ((i, 1 - tr), (i + 1, tr)):
                    w[jj, ii] += wz * wr
        return w

    def solve_unit(self, state: PlasmaState) -> UnitFields:
        """현재 n_e, T_e 로 σ_p 를 만들고 단위 전류 응답 두 개를 푼다."""
        g, cfg = self.grid, self.cfg
        omega = cfg.op.omega
        zp = g.z[: g.Nzp]
        sigma = ph.conductivity(state.ne_rz(zp, cfg), state.Te_rz(zp), cfg)   # (Nzp, Nr)
        diag = np.zeros((g.Nz, g.Nr), dtype=complex)
        diag[: g.Nzp] = -1j * omega * MU0 * sigma            # 창·공기 영역은 σ = 0
        lu = splu((self.lap + sp.diags(diag.ravel())).tocsc())
        cell_area = g.dr * g.dz[:, None]                     # r–z 단면에서 셀 넓이
        sol = []
        for w in (self.w_in, self.w_out):
            rhs = (-MU0 * w / cell_area).astype(complex).ravel()   # −μ0 J_coil (1 A)
            sol.append(lu.solve(rhs).reshape(g.Nz, g.Nr))
        A_in, A_out = sol
        re_sig = sigma.real
        # 플라즈마 부하 저항 행렬 R_ab = ω² ∫ Re(σ) A_a* A_b dV
        vol = self.cell_vol[: g.Nzp]
        pair = (A_in[: g.Nzp], A_out[: g.Nzp])
        R_pl = np.array([[omega**2 * np.sum(re_sig * np.conj(a) * b * vol) for b in pair] for a in pair])
        # 포트 임피던스 Z_ab = jω × (코일 a 의 턴들을 꿰는 자속, 코일 b 에 1 A)
        link = lambda w, A: np.sum(w * 2 * np.pi * g.r[None, :] * A)
        Z = 1j * omega * np.array([[link(self.w_in, A_in), link(self.w_in, A_out)],
                                   [link(self.w_out, A_in), link(self.w_out, A_out)]])
        Z += np.diag([cfg.op.R_coil_in, cfg.op.R_coil_out])
        return UnitFields(A_in, A_out, re_sig, R_pl, Z)

    def heating(self, unit: UnitFields, cfg: Config | None = None) -> Heating:
        """단위 응답을 (k, φ) 로 중첩하고 포트 전력 조건으로 I_0 를 정한다."""
        cfg = cfg or self.cfg
        g, op = self.grid, cfg.op
        k, phi = op.effective_k_phi()
        a = np.array([1.0, k * np.exp(1j * phi)])            # 전류 페이저 (안쪽 기준)
        R_eff = float(np.real(np.conj(a) @ unit.R_pl @ a))   # 플라즈마가 보이는 등가 저항
        R_c = op.R_coil_in + k**2 * op.R_coil_out            # 코일 저항 손실 몫
        P_port = op.eta_match * op.P_tot
        I0 = np.sqrt(2 * P_port / (R_eff + R_c))
        A = I0 * (a[0] * unit.A_in + a[1] * unit.A_out)
        E = -1j * op.omega * A
        p_abs = 0.5 * unit.re_sigma * np.abs(E[: g.Nzp]) ** 2
        S = np.sum(p_abs * g.dz[: g.Nzp, None], axis=0)
        return Heating(I0, E, p_abs, S, 0.5 * I0**2 * R_eff, 0.5 * I0**2 * R_c, P_port)


def port_drive(unit: UnitFields, heat: Heating, cfg: Config) -> dict:
    """코일 단자에서 본 구동 조건: 코일별 전압 진폭 [V] 과 각 전원이 내야 하는 유효 전력 [W].

    V = Z_port·I,  P_a = ½ Re(V_a I_a*).  두 값의 합은 포트 전력 P_port 와 같다.
    한쪽이 음수이면 그 전원은 전력을 흡수해야 한다는 뜻이다(상호 결합으로 다른 코일에서 넘어오는 전력).
    독립 전원 2대로는 만들 수 없는 조건이고, 전원 1대 + 무효 소자 분배기라면 합만 맞으면 된다.
    """
    k, phi = cfg.op.effective_k_phi()
    I = heat.I0 * np.array([1.0, k * np.exp(1j * phi)])
    V = unit.Z_port @ I
    P = 0.5 * np.real(V * np.conj(I))
    return dict(P_in=float(P[0]), P_out=float(P[1]), V_in=float(abs(V[0])), V_out=float(abs(V[1])),
                V_series=float(abs(V[0] + V[1])))            # 두 코일을 직렬로 묶었을 때의 단자 전압

