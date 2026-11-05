# sim — 모델링

조작 변수 → 밀도 응답 관계(제출 결과물 ②)를 계산하는 코드를 둔다.

## 실행 환경

```bash
python -m pip install -r requirements.txt   # 저장소 루트에서
python sim/scale_estimates.py
```

## 로드맵

| ID | 모델 | 입력 | 출력 | 답하는 질문 | 상태 |
|---|---|---|---|---|---|
| M0 | 스케일 추정 (`scale_estimates.py`) | 압력, 밀도, 챔버 크기 | $\lambda_i$, $D_a$, $\delta_p$, $\Lambda$, $\ell$ | 어떤 결합이 중요한 영역인가 | ✅ |
| M1 | 코일 회로 모델 (`two_zone_icp.py` 회로 모듈) | 코일 L·M, 커패시터, 플라즈마 반공간(Dodd–Deeds 해) | 코일별 전류, 효율, 영역별 흡수 전력 | 조작 변수 → 코일 전류 (회로 결합 C2~C3, 공진점 이동) | ✅ 수동 공진 안테나(후보 A) |
| M2a | 2-영역 0D 모델 (`two_zone_icp.py`, `run_two_zone.py`) | M1 의 영역별 전력, 압력 | $n_c$, $n_e$, $T_e$, $\bar n$, $R$, 응답 행렬 $J$ | 국소/비국소 가열(C6)·확산(C7)을 넣은 밀도비 응답, 가설 H1 | ✅ KC20 측정값으로 검증 |
| M2 | 2D (r, z) 확산 모델 | 영역별 소스 분포, 간격 L, 압력, 체적 손실 | $n(r,z)$, 응답 행렬 $J$, 조건수 | 코일 전류 → 밀도 분포 (확산 결합 C7), 가설 H1·H2 | ☐ |
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

## 규칙

- 매개변수는 파일 상단에 모으고, 단위를 주석으로 적는다.
- 그림을 만드는 스크립트는 결과를 `figures/`에 저장한다.
- 문서에 옮긴 수치는 어느 스크립트·매개변수에서 나왔는지 함께 적는다.
