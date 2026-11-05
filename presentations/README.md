# presentations

발표 자료. 이 프로젝트의 PPT는 모두 `template/발표양식_4x3.pptx`(수업 양식, 4:3)로 만든다.

| 파일 | 내용 |
| --- | --- |
| `1차발표_최종.pptx` | 1차 발표 최종본 (본편 26장 + 백업 6장, 발표자 노트 포함) |
| `template/발표양식_4x3.pptx` | 수업 발표 양식 (제목·제목만 레이아웃, 바닥글 로고) |
| `src/build.py`, `src/lib.py` | 양식 위에 슬라이드를 만드는 스크립트 (python-pptx) |
| `src/eq/` | 수식 이미지와 원본 LaTeX (`eqs.json`, KaTeX로 렌더링하는 `render.js`) |

## 다시 만들기

```bash
python -m pip install python-pptx
python presentations/src/build.py presentations/template/발표양식_4x3.pptx presentations/1차발표_최종.pptx
```

수식을 고치면 `src/eq/eqs.json`을 바꾸고 `node render.js`로 PNG와 `sizes.json`을 다시 만든다 (katex, playwright 필요).

## 양식 사용 규칙 (1차 발표에서 정한 것)

- 레이아웃: 표지는 `제목 슬라이드`, 본문은 `제목만`. 제목은 한 줄(28 pt), 제목 아래 파란 선 밑에 구분 줄(12 pt)을 둔다.
- 본문 글자는 12 pt 이상, 각주만 10 pt. 쪽 번호는 바닥글 오른쪽.
- 색: 제목 남색(333399), 질문별 색 Q1 주황(압력·물리), Q2 파랑(구동·회로), Q3 진남(조정·측정).
- 차트는 PowerPoint 기본 차트로 넣어 편집할 수 있게 한다. 목표 범위(R 0.8–1.2)는 옅은 주황 띠로 통일.
- 수치 옆 표시: (문헌) / (계산) / (추정) / (가정).
