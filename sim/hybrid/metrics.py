"""웨이퍼 관측면 지표: 면적 가중 평균 n_c, n_edge, n̄_w 와 밀도비 ρ (발표 덱 2·12쪽, 부록 18쪽).

    ⟨n⟩_[a,b] = ∫_a^b n_w(r) 2πr dr / (π (b² − a²))

셀 안에서 밀도가 일정하다고 보고, 구간 [a, b] 와 각 고리 셀이 겹치는 넓이로 가중한다.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Config
from .state import Grid, PlasmaState


def ring_average(values: np.ndarray, grid: Grid, a: float, b: float) -> float:
    """반경 구간 [a, b] 의 면적 가중 평균."""
    lo = np.clip(grid.r_face[:-1], a, b)
    hi = np.clip(grid.r_face[1:], a, b)
    w = hi**2 - lo**2                       # 겹치는 고리 넓이 (π 는 약분)
    return float(np.sum(values * w) / (b**2 - a**2))


@dataclass
class WaferMetrics:
    n_c: float          # 중앙 영역(0 ~ r_c) 평균 밀도 [m^-3]
    n_edge: float       # 가장자리 고리(r_1 ~ r_2) 평균 밀도 [m^-3]
    n_bar: float        # 관측면 전체(0 ~ R_w) 평균 밀도 [m^-3]
    rho: float          # 밀도비 n_c / n_edge

    def as_vector(self) -> np.ndarray:
        """제어 출력 벡터 y = (n̄_w, ρ)."""
        return np.array([self.n_bar, self.rho])


def wafer_metrics(state: PlasmaState, grid: Grid, cfg: Config) -> WaferMetrics:
    g = cfg.geom
    n_w = state.wafer_profile(cfg)
    n_c = ring_average(n_w, grid, 0.0, g.r_c)
    n_edge = ring_average(n_w, grid, g.r_1, g.r_2)
    return WaferMetrics(n_c, n_edge, ring_average(n_w, grid, 0.0, g.R_w), n_c / n_edge)
