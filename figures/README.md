# figures

그림과 스크립트 산출 CSV. 그림을 만드는 코드는 `sim/`에 둔다. 2026-11-05 검토(`docs/07_검토결과_2026-11-05.md`)를 반영한 판이다.

## 1차 발표 그림

| 파일 | 내용 | 만드는 곳 |
|---|---|---|
| `presentation1_chain_C1-C8.png` | 밀도 분포 사슬 5단계와 결합 경로 C1–C8 (보고서 「핵심 물리 근거」). ② 장 상자는 "축 위 E_θ = 0"으로 표기 (E_θ ∝ r은 솔레노이드형 식) | `sim/presentation1_figures.py chain` (수치: `01_배경이론.md`, `presentation1_estimates.py scales`) |
| `presentation1_drive_architecture_B.png` | 선택 구조 B의 구동부 구성도 — 제출물 ①. 바깥 루프 ω_c ≤ 0.2 rad/s ≈ 0.03 Hz | `sim/presentation1_figures.py arch` |
| `presentation1_R_range_by_pressure.png` | 압력별 R 범위와 목표대 0.8–1.2. 수염은 코일 선택도 안(중앙 몫 0.07–0.93), 하한은 중앙 몫 0.05–0.07, 점은 같은 전력 밀도의 R. 20 mTorr 이상 여유, 15 mTorr 경계 | `sim/presentation1_figures.py range` (`presentation1_r_range.csv`의 `R_min_x0.05`, `R_min_x0.07` + 같은 2-영역 0D 모델) |
| `schedule_W0-W6.png` | 일정 제안 W0–W6 (W0 = 2026-11-05), H6 위상 판정 11/25 | claude.ai 원본 문서의 그림 (`docs/03_작업계획.md` 4절과 같은 내용) |

## 스크립트 산출 CSV·그림

| 파일 | 내용 | 만드는 곳 |
|---|---|---|
| `presentation1_scales.csv` | 압력별 λε, w, g_R, 자기장 기준값 | `sim/presentation1_estimates.py scales` |
| `presentation1_phase.csv` | 위상 0°/180° 비교 (X′₁₂ 포함, 4개 동작점) | `sim/presentation1_estimates.py phase` |
| `presentation1_jacobian.csv` | 영역 전력을 직접 지정할 때의 J, 같은 전력 밀도의 R | `sim/presentation1_estimates.py jacobian` |
| `presentation1_r_range.csv` | 압력별 R 범위 (중앙 몫 2–98%, 코일 선택도 하한 `R_min_x0.05`, `R_min_x0.07`) | `sim/presentation1_estimates.py range` |
| `two_source_phase.csv` | 위상 스윙에서 P_plasma, P_exch, P1, P2 (\|I1\|² = 1 A² 당, 네 동작점, 0° 동작점의 k 고정) | `sim/two_source_phase.py` |
| `two_zone_validation.csv` | 앞선 2-영역 모델의 KC20 측정값 비교 | `sim/run_two_zone.py validate` |
| `two_zone_sweep.csv`, `two_zone_sweep_summary.csv`, `two_zone_control.png` | 수동 공진 구조의 압력 × C 제어 지도 | `sim/run_two_zone.py sweep` |
| `two_zone_jacobian.csv` | 수동 공진 구조의 응답 행렬 | `sim/run_two_zone.py jacobian` |
| `two_zone_sensitivity.csv` | 가정별 민감도 | `sim/run_two_zone.py sensitivity` |

그림의 수치를 바꾸면 해당 스크립트를 다시 실행해 PNG와 CSV를 함께 갱신한다. 일정 그림은 일정을 바꿀 때 다시 내보낸다.

## 하이브리드 자기일관 모델 (`hybrid/`)

전자기장 2D + 수송 반경 1D 모델의 결과. 모두 `python sim/run_hybrid.py <부명령>` 으로 다시 만든다 (설명: `sim/hybrid/README.md`).

| 파일 | 내용 | 부명령 |
|---|---|---|
| `hybrid/check.csv` | 자체 검산 8항목 (포인팅, 상반성, 수지, T_e 균일 극한의 해석해) | `check` |
| `hybrid/point_dual_P300_k1_phi0.png`, `_summary.json`, `_radial.csv`, `_field_rz.csv`, `_convergence.csv` | 기준 운전점의 장·가열·밀도 지도, 웨이퍼 지표, 수렴 이력과 그 데이터 | `point` |
| `hybrid/jacobian_P300_k1_phi0.png`, `.csv`, `_dual.json`, `_single.json` | J_ctrl (이중 코일 2×3, 단일 코일 2×1), 특이값, 형상 감도 | `jacobian` |
| `hybrid/iso_mean_scan.png`, `.csv` | n̄_w 를 고정하고 k 를 훑었을 때의 ρ, 필요한 P_tot, 분포 모양 (φ = 0, 90, 180°) | `iso` |
| `hybrid/response_map.png`, `.csv` | P_tot 고정, (k, φ) 평면의 ρ 지도와 n̄_w 등고선 | `map` |
| `hybrid/timing.png`, `.csv` | 격자별 계산 시간, 예산 대비 마진, 격자 오차 | `timing` |
| `hybrid/loop_margin.png`, `.csv` | 기준점 J 를 제어기에 넣었을 때 시나리오별 이득 불일치 λ, 위상 여유, 설정 시간 | `margin` |
| `hybrid/validate2d.png`, `.csv` | 반경 1D 수송과 (r, z) 2D 수송의 비교: 밀도 비 지도, 2D T_e, z 분포, 웨이퍼 분포, J_ctrl, 운전점별 차 | `validate2d` |
| `hybrid/point_dual_P300_k1_phi0_2d.png` 와 같은 이름의 데이터 | 2D 수송으로 푼 기준 운전점 | `point --transport 2d` |

