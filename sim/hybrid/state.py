"""격자와 플라즈마 상태를 담는 자료 구조.

Grid        : 반경 셀(전자기장·수송 공통)과 z 셀(전자기장 전용)
PlasmaState : 수송 모델의 미지수. 반경별 중간 높이 밀도 n0(r) 와 전자온도 T_e(r)

나중에 2D 수송 검증 모듈을 붙일 때는 PlasmaState 와 같은 메서드
(`ne_rz`, `Te_rz`, `wafer_profile`)를 가진 2D 상태 클래스를 만들면
전자기장·지표·그림 모듈을 그대로 쓸 수 있다.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import physics as ph
from .config import Config


class Grid:
    """축대칭 반단면의 셀 중심 격자."""

    def __init__(self, cfg: Config):
        g, num = cfg.geom, cfg.num
        self.Nr = num.Nr
        self.dr = g.R / num.Nr
        self.r = (np.arange(num.Nr) + 0.5) * self.dr          # 셀 중심 반지름 [m]
        self.r_face = np.arange(num.Nr + 1) * self.dr         # 셀 경계면 반지름 [m]
        # 축대칭 고리 셀의 밑넓이 π(r_o² − r_i²) 와 경계면 둘레 2π r_f (단위 높이 기준)
        self.area = np.pi * (self.r_face[1:] ** 2 - self.r_face[:-1] ** 2)
        self.perim = 2 * np.pi * self.r_face
        # z 격자: 플라즈마(0 ~ L) + 위쪽(창·코일·공기, L ~ z_top)
        dz_p = g.L / num.Nz_plasma
        dz_u = (g.z_top - g.L) / num.Nz_upper
        self.dz = np.concatenate([np.full(num.Nz_plasma, dz_p), np.full(num.Nz_upper, dz_u)])
        z_face = np.concatenate([[0.0], np.cumsum(self.dz)])
        self.z = 0.5 * (z_face[1:] + z_face[:-1])             # 셀 중심 z [m]
        self.Nz = self.z.size
        self.Nzp = num.Nz_plasma                               # 플라즈마 영역 z 셀 수


@dataclass
class PlasmaState:
    """반경 1D 수송 모델의 상태."""
    n0: np.ndarray      # 중간 높이(z = L/2) 전자 밀도 [m^-3], 길이 Nr
    Te: np.ndarray      # 전자온도 [V], 길이 Nr (z 방향으로는 균일하다고 본다)

    def copy(self) -> "PlasmaState":
        return PlasmaState(self.n0.copy(), self.Te.copy())

    def ne_rz(self, z: np.ndarray, cfg: Config) -> np.ndarray:
        """2D 밀도 지도 n_e(r, z) = n0(r)·cos(k_z(r)(z − L/2)). 반환 모양 (len(z), Nr)."""
        x, _, _ = ph.axial_mode(self.Te, cfg)
        kz = 2 * x / cfg.geom.L
        return self.n0[None, :] * np.cos(kz[None, :] * (z[:, None] - 0.5 * cfg.geom.L))

    def Te_rz(self, z: np.ndarray) -> np.ndarray:
        """2D 전자온도 지도 (z 방향 균일). 반환 모양 (len(z), Nr)."""
        return np.repeat(self.Te[None, :], z.size, axis=0)

    def wafer_profile(self, cfg: Config) -> np.ndarray:
        """관측 높이 z_w 에서의 반경 방향 밀도 n_w(r) [m^-3]."""
        return self.ne_rz(np.array([cfg.geom.z_w]), cfg)[0]

    @staticmethod
    def from_zero_d(grid: Grid, cfg: Config) -> "PlasmaState":
        """0D 균형값을 모든 셀에 똑같이 깐 초기 상태 (발표 덱 8쪽 식 1)."""
        Te0, n_star = ph.zero_d_initial(cfg)
        return PlasmaState(np.full(grid.Nr, n_star), np.full(grid.Nr, Te0))
