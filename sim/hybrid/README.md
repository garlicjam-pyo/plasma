# hybrid — 전자기장 2D + 수송 반경 1D 자기일관 모델

세 입력 (P_tot, k, φ) 에서 웨이퍼 지표 (n̄_w, ρ) 를 계산하고, 제어 민감도 행렬 J_ctrl (2×3) 을 구한다.
1차 발표 덱 7–13쪽의 계산 흐름을 그대로 따르되, 수송(n_e, T_e)만 z 로 적분해 r 의 1D 식으로 줄였다.

## 모델

| 단계 | 푸는 식 | 차원 | 파일 |
| --- | --- | --- | --- |
| 초기값 | 0D 입자·전력 균형 (교재 식 2.70, 2.73) | 0D | `physics.py` |
| 전도도·RF 장 | σ_p (식 2.26), A_θ 방정식, 단위 전류 응답 중첩, 포트 전력으로 I_0 | 2D (r, z) | `em_field.py` |
| 수송 | 전자 에너지 + 입자 식의 잔차 F(x) = 0, 감쇠 Newton | 1D (r) | `transport_1d.py` |
| 자기일관 반복 | 장 → 가열 → 수송 → 장 … , 수렴 판정 3종 | | `coupled.py` |
| 지표 | 면적 가중 평균 n_c, n_edge, n̄_w, ρ | | `metrics.py` |
| 제어 판정 | J_ctrl (중심 차분), 등평균 스캔, (k, φ) 지도 | | `control.py` |

수송을 1D 로 줄인 방법: z 방향 분포를 기본 모드 n(r, z) = n0(r)·cos(k_z(z − L/2)) 로 두고 T_e 는 z 로 균일하다고 본다.
위·아래 벽 손실은 손실 주파수 ν_L 로, 벽으로 나가는 에너지는 쌍당 7.2 T_e 로 식에 들어간다.
전자기장은 평판 코일의 장이 창에서 z 방향으로 감쇠하므로 2D 로 푼다(선형이라 한 번에 십수 ms).

## 실행

```bash
python sim/run_hybrid.py check       # 자체 검산
python sim/run_hybrid.py point       # 운전점 1개 (--P --k --phi --p --mode 로 조건 지정)
python sim/run_hybrid.py jacobian    # J_ctrl: 이중 코일 2×3, 단일 코일 2×1
python sim/run_hybrid.py iso         # 평균 밀도 유지 + k 스캔
python sim/run_hybrid.py map         # (k, φ) 평면의 ρ·n̄_w 지도
python sim/run_hybrid.py timing      # 격자별 시간·마진·오차
python sim/run_hybrid.py all
```

결과는 `figures/hybrid/` 에 그림(png)과 데이터(csv, json)로 함께 저장된다.
형상·운전 조건·격자의 기본값은 `config.py` 한 곳에 있다.

코일 구성(`--mode`): `dual`(안쪽·바깥쪽 따로 구동, 입력 3개), `single_series`(모든 턴 직렬, 입력은 P_tot 하나),
`single_inner`(안쪽 코일만).

## 검산 (`check`)

| 항목 | 결과 |
| --- | --- |
| 포인팅 검산 Re(Z) − R_coil = R_pl | 10⁻¹⁶ |
| 상반성 Z_io = Z_oi | 10⁻¹⁶ |
| 입자·에너지 수지 | 10⁻¹⁴, 10⁻¹⁰ |
| T_e 균일 극한(열전도 10⁵배)의 ρ 대 해석해 J_0(κr) | 차 0.01 % |
| 같은 극한에서 k 에 따른 ρ 변동 | 0.002 % |

수치를 제대로 풀었다는 확인이다. 국소 Maxwellian·유체 수송 가정의 검증은 아니다.

## 계산 시간 (기준 격자 60×56, 2코어)

운전점 1개 약 0.14 s(예산 1 s, 마진 7배), J_ctrl 1개 약 0.7 s(예산 10 s, 마진 15배).
격자 오차는 가장 촘촘한 격자 대비 0.03 % 이하. 예산과 마진 기준은 `timing.py` 상단에 있다.

## 모델 가정에 대한 민감도

격자 오차보다 닫힘 가정의 영향이 훨씬 크다. 기준점(300 W, k = 1, φ = 0, 10 mTorr)에서:

| 바꾼 것 | ρ | 평균 고정 시 k 의 형상 감도 |
| --- | --- | --- |
| 기준 | 1.27 | −0.59 |
| 전자 열전도도 3배 (`kappa_scale=3`) | 1.47 | −0.33 |
| 전자 열전도도 10배 | 1.59 | −0.13 |
| 축 방향 닫힘을 교재 h_L 로 (`axial_closure="h_factor"`) | 1.44 | −0.33 |

저압에서 전자 에너지 수송이 유체 식보다 비국소적이면 실제 제어 여유는 이 표의 아래쪽에 가까워진다.

## COMSOL 과 비교할 때

1. `config.py` 의 형상·압력·주파수·코일 위치를 COMSOL 매개변수와 맞춘다.
2. COMSOL 에서 웨이퍼 높이(z = z_w) 절단선의 전자 밀도를 "r, 값" 텍스트로 내보낸다.
3. `python sim/run_hybrid.py compare 파일 --r-scale 0.01 --n-scale 1e6` (cm, cm⁻³ 인 경우).
   n̄_w 비, ρ 차, 분포 모양의 RMS 차와 겹쳐 그린 그림이 나온다.
4. 2D 양(|E_θ|, p_abs, n_e, T_e)은 `*_field_rz.csv` 가 COMSOL 격자 내보내기와 같은 긴 표(r, z, 값) 형식이다.
   포트 임피던스 Z 와 플라즈마 부하 저항은 `*_summary.json` 에 있다.

비교 순서는 전자기장(같은 σ 에서 Z, |E_θ|) → 가열 분포 → T_e → n_e 를 권한다. 앞 단계가 맞아야 뒤 단계의 차이를 해석할 수 있다.

## 2D 수송 검증 모듈을 붙일 자리

`coupled.solve_point` 는 수송 모델에 `residual`, `solve`, `terms` 만 요구하고, 상태 객체에는
`ne_rz`, `Te_rz`, `wafer_profile` 만 요구한다. 2D 수송은 같은 메서드를 가진 `Transport2D` 와 2D 상태 클래스를
만들어 `solve_point` 에서 바꿔 끼우면 전자기장·지표·제어·그림·내보내기 모듈을 그대로 쓴다.
