# sim — 모델링

조작 변수 → 밀도 응답 관계(제출 결과물 ②)를 계산하는 코드를 둔다.

## 실행 환경

```bash
python -m pip install -r requirements.txt   # 저장소 루트에서
python sim/scale_estimates.py                      # M0 스케일 추정
python sim/run_two_zone.py validate                # M1·M2a 검증 (KC20), sweep / jacobian / sensitivity 도 있음
python sim/presentation1_estimates.py scales       # λε, w, g_R, 확산 누설, 자기장 기준값, 속도 계수
python sim/presentation1_estimates.py phase        # 결정 5의 0°/180° 비교표 (X'12 포함)
python sim/presentation1_estimates.py jacobian     # 독립 전원의 J, 같은 전력 밀도에서의 R
python sim/presentation1_estimates.py range        # 압력별 R 범위 (코일 선택도 하한 포함)
python sim/two_source_phase.py                     # 두 전원 교환 전력·위상 허용 오차·정합 리액턴스 (phase 와 같은 ΔZ·동작점)
python sim/jacobian_fit.py                         # FHP 섭동 실험 → a0/a1 회귀 → J, 누설, κ, RGA (합성 데이터 시연)
python sim/presentation1_figures.py                # 1차 발표 그림 3종 (R 범위, 사슬, 구성도) → figures/*.png
python sim/theory_note_check.py                    # 팀 이론 정리 문서(11-09)의 압력별 수치 재현, 자화 수송 표(3 G 포함), 교차 성분별 거리
python sim/k_operating_point.py 20                 # 운전점(중앙 몫 x)에 따른 J 변화, R = 1의 J로 한 선형 예측 오차, 고정 J 반복과 도달 한계
python sim/feedback_demo.py                        # 바깥 루프 되먹임 예: 피드포워드 + 적분 보정, K̂ 오차 3경우 (조정절차 7절)
python sim/run_hybrid.py all                       # 전자기장 2D + 수송 반경 1D 자기일관 모델: 검산, 운전점, J_ctrl, 등평균 스캔, 지도, 타이밍 (sim/hybrid/README.md)
```

## 로드맵

| ID | 모델 | 입력 | 출력 | 답하는 질문 | 상태 |
|---|---|---|---|---|---|
| M0 | 스케일 추정 (`scale_estimates.py`) | 압력, 밀도, 챔버 크기 | $\lambda_i$, $D_a$, $\delta_p$, $\Lambda$, $\ell$ | 어떤 결합이 중요한 영역인가 | ✅ |
| M1 | 코일 회로 모델 (`two_zone_icp.py` 회로 모듈) | 코일 L·M, 커패시터, 플라즈마 반공간(Dodd–Deeds 해) | 코일별 전류, 효율, 영역별 흡수 전력 | 조작 변수 → 코일 전류 (회로 결합 C2~C3, 공진점 이동) | ✅ 수동 공진 안테나(후보 A), 공진 상태 재현은 미완 · 🔄 V1: 전원 2개·위상·다중 턴 |
| M1a | 두 전원 위상·정합 보조 (`two_source_phase.py`) | L1, L2, M12, M1의 반사 임피던스 ΔZ (또는 직접 입력) | P_exch, 위상 허용 오차, 효율, Z_in 변화 | 결정 4·5의 회로식 재현 | ✅ (단일 턴·고정 밀도, V1에서 다중 턴으로) |
| M2a | 2-영역 0D 모델 (`two_zone_icp.py`, `run_two_zone.py`, `presentation1_estimates.py`) | M1 의 영역별 전력, 압력 | $n_c$, $n_e$, $T_e$, $\bar n$, $R$, 응답 행렬 $J$, 압력별 R 범위 | 국소/비국소 가열(C6)·확산(C7)을 넣은 밀도비 응답, 가설 H1 | ✅ KC20 비공진 급전 전류 ±9% (공진 상태·절대 밀도는 못 맞춤) |
| M4 | 측정 처리 (`jacobian_fit.py`) | FHP 섭동 실험 CSV | a0/a1, J (ln I_tot, ln P 기준), 누설, κ(J), RGA | 측정에서 J (V3) | ✅ 회귀·J 산출, ☐ 섭동 시퀀스 생성 (B16) |
| M2 | 2D (r, z) 확산 모델 (V2) | 영역별 소스 분포, 간격 L 6–12 cm, 압력, 체적 손실 | $n(r,z)$, 확산 누설, 측정 위치 환산 계수 | 코일 전류 → 밀도 분포 (확산 결합 C7), 가설 H2·H5 | ☐ (COMSOL vs Python 유한차분 결정 후, B09) |
| M3a | 하이브리드 자기일관 모델 (`hybrid/`, `run_hybrid.py`): 전자기장 2D + 수송 반경 1D | 형상, 압력, (P_tot, k, φ) | $E_\theta(r,z)$, $p_{abs}$, $T_e(r)$, $n_e(r)$, $(\bar n_w, \rho)$, $J_{ctrl}$ | 1차 발표 덱 7–13쪽 계산 흐름의 구현, 제어 가능성 판정 | ✅ 검산 통과, 운전점 0.14 s. 2D 수송 검증판·COMSOL 비교는 ☐ |
| M3 | (선택) 2D 유체·전자기 결합 모델 | 챔버 형상, 코일 구성 | 자기일관 $E$, $T_e$, $n$ | 비국소 가열(C6), 표피 효과 비선형성(C3) | ☐ |

M2의 첫 버전은 "가열 위치 = 이온화 위치(국소)"와 "전자 온도 균일(비국소)"의 두 극한을 모두 계산해, 실제 장비가 두 극한 사이 어디쯤인지에 따라 독립성이 어떻게 달라지는지를 보여 주는 것을 목표로 한다. M3는 COMSOL 등 학교 도구 사용 가능 여부에 따라 결정한다.

## M1 + M2a 실행

```bash
python sim/run_two_zone.py validate     # KC20 측정값 비교 → figures/two_zone_validation.csv
python sim/run_two_zone.py sweep        # 압력 × C 제어 지도 → figures/two_zone_sweep*.csv, two_zone_control.png
python sim/run_two_zone.py jacobian     # 응답 행렬 → figures/two_zone_jacobian.csv
python sim/run_two_zone.py sensitivity  # 가정별 민감도 → figures/two_zone_sensitivity.csv
```

동작점 하나는 2코어 기준 약 4초, 전체 실행은 30분 안팎이다. 모델 설명·근거·검증은
claude.ai 문서 "2-영역 0D ICP 챔버 모델"에 정리되어 있다. 보정 파라미터는 κ_ν (확률적 가열 배수) 하나이고,
150 W, 1 mTorr, 비공진의 급전 전류 8.5 A 에 맞췄다 (`calibrate_nu_factor`).
검증 범위는 비공진 급전 전류(보정 밖 3점 ±9%)뿐이다. 공진 급전 전류는 74–85% 높게, 절대 밀도는 1.4–18배 높게 나오고,
R 변화 폭은 경향만 맞는다 (`docs/07_검토결과_2026-11-05.md`).

## 1차 발표 수치 (`presentation1_estimates.py`, `two_source_phase.py`)

- `phase`와 `two_source_phase.py`는 같은 반사 임피던스 ΔZ(단일 턴, 균일 반공간, 고정 밀도)와 같은 동작점(중앙 전력 몫 0.20)을 쓴다.
  `two_source_phase.py`는 결과를 `figures/presentation1_phase.csv`와 비교해 차이를 출력한다.
- 위상 비교 결과 (n = 3×10¹⁶–10¹⁷ m⁻³, 10–20 mTorr): 위상 허용 오차 0° ±19–38°, 180° ±4–12°, 90° 교환 전력은 흡수 전력의 0.2–0.7배, η 0.95–0.96 (0°) vs 0.85–0.91 (180°).
- 정합 리액턴스 변화(안쪽 코일)는 X′₁₂를 넣어 0° +13–24%, 180° −7–10%이고, 바깥 코일은 +1–2% / −3–6%다. 문서의 주 수치는 이 값이다. 코일 상호 인덕턴스 항만 쓰면 안쪽 +47–51% / −20–25%, 바깥 +5% / −10–13%로, 처음 문서의 +48% / −22%가 이 값이었다. 180°가 작다는 방향은 같다.
- `range`의 `R_min_x0.05`, `R_min_x0.07`은 코일 선택도(바깥 코일만 켜도 중앙에 5–7%가 떨어짐)를 넣은 R 하한이다.

## 규칙

- 매개변수는 파일 상단에 모으고, 단위를 주석으로 적는다.
- 그림을 만드는 스크립트는 결과를 `figures/`에 저장한다.
- 문서에 옮긴 수치는 어느 스크립트·매개변수에서 나왔는지 함께 적는다 (스크립트 이름과 부명령).
- 그림 목록은 `figures/README.md`, 보고서 수치의 재현 순서는 `docs/06_상세설계보고서.md` 부록 E.
