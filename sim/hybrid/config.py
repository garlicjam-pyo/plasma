"""하이브리드 ICP 모델의 설정값 모음.

모든 치수·운전 조건·수치 옵션을 이 파일의 dataclass 에 모은다.
다른 모듈은 여기서 만든 객체만 받아 쓰므로, 형상이나 조건을 바꿀 때는
이 파일의 기본값을 고치거나 `dataclasses.replace(cfg, ...)` 로 복사본을 만든다.
COMSOL 모델과 비교할 때도 이 파일의 값과 COMSOL 매개변수를 1:1 로 맞추면 된다.

단위는 모두 SI (m, s, kg, A, V, W, Pa). 전자온도 T_e 만 볼트(수치상 eV)로 쓴다.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Tuple

import numpy as np

# ------------------------------------------------------------------ 물리 상수
E_CHARGE = 1.602176634e-19      # 기본 전하 e [C]
M_ELECTRON = 9.1093837e-31      # 전자 질량 m_e [kg]
M_ARGON = 39.948 * 1.66053907e-27   # Ar 이온 질량 M [kg]
K_BOLTZ = 1.380649e-23          # 볼츠만 상수 k_B [J/K]
MU0 = 4e-7 * np.pi              # 진공 투자율 μ0 [H/m]


@dataclass(frozen=True)
class Geometry:
    """챔버와 코일 형상 (축대칭, 반단면 r–z).

    z = 0 이 웨이퍼(바닥), z = L 이 유전체 창의 아랫면이다.
    기본값은 팀 이론 정리 문서의 기준 형상(R 21 cm, L 6 cm)과
    1차 결정보고서의 코일 배치(안쪽 7–9 cm 띠, 바깥쪽 15–16 cm 띠)다.
    """
    R: float = 0.21                 # 챔버(플라즈마) 반지름 [m]
    L: float = 0.06                 # 플라즈마 높이 = 웨이퍼–창 간격 [m]
    window: float = 0.015           # 유전체 창 두께 [m]
    coil_gap: float = 0.005         # 창 윗면에서 코일 중심까지 높이 [m]
    top_gap: float = 0.06           # 코일 위쪽 금속 덮개까지 거리 [m]
    r_in: Tuple[float, ...] = (0.075, 0.085)      # 안쪽 코일 각 턴의 반지름 [m]
    r_out: Tuple[float, ...] = (0.1525, 0.1575)   # 바깥쪽 코일 각 턴의 반지름 [m]
    # 평가 영역 (발표 덱 2·12쪽): 중앙 0–5 cm, 가장자리 12–14.5 cm
    r_c: float = 0.05               # 중앙 영역 바깥 경계 [m]
    r_1: float = 0.12               # 가장자리 고리 안쪽 경계 [m]
    r_2: float = 0.145              # 가장자리 고리 바깥쪽 경계 [m]
    R_w: float = 0.15               # 웨이퍼 관측면 평가 반지름 [m]
    z_w: float = 0.01               # 관측 높이 (웨이퍼 위) [m]

    @property
    def z_coil(self) -> float:
        """코일 중심의 z 좌표 [m]."""
        return self.L + self.window + self.coil_gap

    @property
    def z_top(self) -> float:
        """전자기장 계산 영역의 위쪽 끝(금속 덮개) z 좌표 [m]."""
        return self.z_coil + self.top_gap


@dataclass(frozen=True)
class Operating:
    """운전 조건. 제어 입력은 (P_tot, k, phi) 세 개다."""
    p_mtorr: float = 10.0           # 기체 압력 [mTorr]
    T_gas: float = 300.0            # 중성 기체(=이온) 온도 [K]
    freq: float = 13.56e6           # RF 주파수 [Hz]
    P_tot: float = 300.0            # 총 공급 전력 [W]
    k: float = 1.0                  # 전류 크기비 |I_out| / |I_in|
    phi: float = 0.0                # 전류 위상차 [rad]
    coil_mode: str = "dual"         # "dual" | "single_series" | "single_inner"
    eta_match: float = 1.0          # 정합기·배선 효율 (P_port = eta_match · P_tot)
    R_coil_in: float = 0.10         # 안쪽 코일 직렬 저항 [Ω]
    R_coil_out: float = 0.15        # 바깥쪽 코일 직렬 저항 [Ω]

    @property
    def omega(self) -> float:
        return 2 * np.pi * self.freq

    @property
    def n_gas(self) -> float:
        """중성 기체 밀도 n_g = p / (k_B T_g) [m^-3]."""
        return self.p_mtorr * 1e-3 * 133.322 / (K_BOLTZ * self.T_gas)

    def effective_k_phi(self) -> Tuple[float, float]:
        """코일 구성에 따라 실제로 쓰는 (k, phi).

        - dual: 입력 그대로 (안쪽·바깥쪽을 따로 구동)
        - single_series: 모든 턴을 직렬로 묶은 코일 하나 → k = 1, phi = 0 고정
        - single_inner: 안쪽 코일만 구동 → k = 0
        """
        if self.coil_mode == "single_series":
            return 1.0, 0.0
        if self.coil_mode == "single_inner":
            return 0.0, 0.0
        return self.k, self.phi


@dataclass(frozen=True)
class Numerics:
    """격자와 반복 옵션."""
    Nr: int = 60                    # 반경 방향 셀 수 (전자기장·수송 공통)
    Nz_plasma: int = 24             # 플라즈마 영역 z 셀 수 (전자기장만 사용)
    Nz_upper: int = 32              # 창 + 코일 + 위쪽 공간 z 셀 수
    transport: str = "radial_1d"    # 수송 모델: "radial_1d"(z 적분 반경 1D) | "full_2d"(검증용 (r, z) 2D)
    axial_closure: str = "robin"    # 축 방향 손실 닫힘: "robin"(유체 Bohm 경계) | "h_factor"(교재 h_L)
    kappa_scale: float = 1.0        # 전자 열전도도 배수 (모델 민감도용. 아주 크게 주면 T_e 균일 극한)
    # --- 수송 Newton 반복
    newton_tol: float = 1e-10       # 무차원 잔차의 최대값 허용치
    newton_max: int = 40
    # --- 전자기장–수송 바깥 반복
    outer_tol: float = 1e-7         # 연속 반복 사이 상대 갱신량 허용치
    outer_max: int = 60
    relax: float = 1.0              # 바깥 반복 완화 계수 (1 = 완화 없음)


@dataclass(frozen=True)
class Config:
    """모델 전체 설정 묶음."""
    geom: Geometry = field(default_factory=Geometry)
    op: Operating = field(default_factory=Operating)
    num: Numerics = field(default_factory=Numerics)

    def with_op(self, **kw) -> "Config":
        """운전 조건만 바꾼 복사본 (예: cfg.with_op(k=1.5, phi=np.pi))."""
        return replace(self, op=replace(self.op, **kw))

    def with_num(self, **kw) -> "Config":
        return replace(self, num=replace(self.num, **kw))

    def with_geom(self, **kw) -> "Config":
        return replace(self, geom=replace(self.geom, **kw))
