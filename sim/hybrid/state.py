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

    def midplane(self, cfg: Config) -> np.ndarray:
        """중간 높이(z = L/2) 밀도 [m^-3]."""
        return self.n0

    def Te_radial(self) -> np.ndarray:
        """반경별 대표 전자온도 [V]."""
        return self.Te

    def column(self, cfg: Config, grid: Grid) -> dict:
        """z 로 적분한 양: 면밀도 N [m^-2], 이온화 G [1/(m^2 s)], 위·아래 벽 손실 주파수 ν_L [1/s]."""
        _, nuL, gbar = ph.axial_mode(self.Te, cfg)
        N = self.n0 * gbar * cfg.geom.L
        return dict(N=N, G=cfg.op.n_gas * ph.K_iz(self.Te) * N, nuL=nuL)

    @staticmethod
    def from_zero_d(grid: Grid, cfg: Config) -> "PlasmaState":
        """0D 균형값을 모든 셀에 똑같이 깐 초기 상태 (발표 덱 8쪽 식 1)."""
        Te0, n_star = ph.zero_d_initial(cfg)
        return PlasmaState(np.full(grid.Nr, n_star), np.full(grid.Nr, Te0))


@dataclass
class PlasmaState2D:
    """(r, z) 2D 수송 모델의 상태. 배열 모양은 (Nz_plasma, Nr) 이고 z 격자는 Grid 의 플라즈마 셀과 같다."""
    n: np.ndarray       # 전자 밀도 [m^-3]
    Te: np.ndarray      # 전자온도 [V]
    z: np.ndarray       # 셀 중심 z [m], 길이 Nz_plasma

    def copy(self) -> "PlasmaState2D":
        return PlasmaState2D(self.n.copy(), self.Te.copy(), self.z)

    def _at(self, field: np.ndarray, z: np.ndarray) -> np.ndarray:
        """z 방향 선형 보간 (요청한 z 가 격자와 같으면 그대로 돌려준다)."""
        if z.shape == self.z.shape and np.allclose(z, self.z):
            return field
        return np.array([[np.interp(zz, self.z, field[:, i]) for i in range(field.shape[1])] for zz in z])

    def ne_rz(self, z: np.ndarray, cfg: Config) -> np.ndarray:
        return self._at(self.n, z)

    def Te_rz(self, z: np.ndarray) -> np.ndarray:
        return self._at(self.Te, z)

    def wafer_profile(self, cfg: Config) -> np.ndarray:
        return self.ne_rz(np.array([cfg.geom.z_w]), cfg)[0]

    def midplane(self, cfg: Config) -> np.ndarray:
        return self.ne_rz(np.array([0.5 * cfg.geom.L]), cfg)[0]

    def Te_radial(self) -> np.ndarray:
        """밀도로 가중한 z 평균 전자온도 [V]."""
        return np.sum(self.n * self.Te, axis=0) / np.sum(self.n, axis=0)

    def column(self, cfg: Config, grid: Grid) -> dict:
        dz = grid.dz[: grid.Nzp, None]
        N = np.sum(self.n * dz, axis=0)
        G = np.sum(cfg.op.n_gas * ph.K_iz(self.Te) * self.n * dz, axis=0)
        mu = ph.ion_mobility(cfg)
        loss = 0.0
        for row in (0, -1):                                   # 바닥과 창 쪽 벽의 Bohm 유출
            uB = ph.bohm_speed(self.Te[row])
            loss = loss + self.n[row] / (1.0 + uB * grid.dz[0] / (2 * mu * self.Te[row])) * uB
        return dict(N=N, G=G, nuL=loss / N)

    @staticmethod
    def from_radial(st: PlasmaState, grid: Grid, cfg: Config) -> "PlasmaState2D":
        """반경 1D 해를 기본 모드 가정으로 펼쳐 2D 초기 상태를 만든다."""
        zp = grid.z[: grid.Nzp]
        return PlasmaState2D(st.ne_rz(zp, cfg).copy(), st.Te_rz(zp).copy(), zp)

