"""1차 발표(이론적 배경판)에 녹화용 필수 수정을 최소한으로 반영한다.
사용: python3 edit_deck.py 입력.pptx timed.json 출력.pptx"""
import sys, copy, json
from pptx import Presentation
from pptx.util import Pt

src, timed, dst = sys.argv[1:4]
p = Presentation(src)
S = lambda n: p.slides[n - 1]

def shape(slide, sid):
    for sh in slide.shapes:
        if sh.shape_id == sid:
            return sh
    raise KeyError(sid)

def set_runs(para, text):
    """첫 run의 서식을 유지하고 문단 글자를 text로 바꾼다(나머지 run 삭제)."""
    rs = para.runs
    rs[0].text = text
    for r in rs[1:]:
        r._r.getparent().remove(r._r)

def replace_in_runs(para, old, new):
    for r in para.runs:
        if old in r.text:
            r.text = r.text.replace(old, new)
            return
    raise ValueError(old)

# ---- 2쪽: 교수님 코멘트 → 반영
items = [
    ("핵심만 요약", "본문은 0D의 한계 → 2D 모델 → 제어 가능성 판단의 흐름만, 세부는 부록"),
    ("왜 밀도비가 좋은가", "3쪽: 평균과 모양을 나눠 다루고, 공통 배율 오차가 비에서 지워짐"),
    ("에너지 수송 용어", "10쪽: 에너지 식 항 이름 정리 (에너지 선속 = 엔탈피 대류 + 열전도)"),
    ("r만 변수로 단일 코일 먼저", "2차 1단계: 단일 코일, 입자·전자 에너지 식을 r만으로 풀이"),
    ("다중 코일이면 z 고려", "2차 2단계: 두 코일 장의 퍼짐·겹침을 (r, z) 전자기장으로, 수송은 r"),
    ("COMSOL 검증", "치수가 비슷한 챔버의 실측 논문과 대조, COMSOL은 가능해지면 추가"),
]
tf = shape(S(2), 3).text_frame
paras = tf.paragraphs
for extra in paras[1:]:
    extra._p.getparent().remove(extra._p)
first = paras[0]
for r in list(first.runs):
    r._r.getparent().remove(r._r)
for i, (c, a) in enumerate(items):
    para = first if i == 0 else tf.add_paragraph()
    r1 = para.add_run(); r1.text = f"- {c}"; r1.font.bold = True; r1.font.size = Pt(17)
    para.add_line_break()
    r2 = para.add_run(); r2.text = f"   → {a}"; r2.font.size = Pt(15)
    para.space_after = Pt(9)

# ---- 3쪽: 밀도비를 쓰는 이유 한 줄
tb = shape(S(3), 7).text_frame
newp = copy.deepcopy(tb.paragraphs[1]._p)
tb.paragraphs[1]._p.addnext(newp)
np_ = tb.paragraphs[2]
np_.runs[0].text = "왜 밀도비"
np_.runs[1].text = "  평균과 모양(균일도)을 나눠 다루고, 공통 배율 오차가 비에서 지워진다."

# ---- 7쪽: 간섭 서술
set_runs(shape(S(7), 34).text_frame.paragraphs[1],
         "두 장의 세기와 사이 각 φ + ψ(r, z)가 위치마다 달라, 간섭으로 더해지거나 빠지는 가열이 위치마다 다르다.")

# ---- 8쪽: 에너지 용어
replace_in_runs(shape(S(8), 6).text_frame.paragraphs[0], "유체 수송 근사", "국소 열전도 근사")
tbl = shape(S(8), 8).table
set_runs(tbl.cell(3, 1).text_frame.paragraphs[0], "국소 열전도로 닫은 전자 에너지 보존식")

# ---- 10쪽: 에너지 식 항 이름
s10 = S(10)
set_runs(shape(s10, 21).text_frame.paragraphs[0], "옴 가열")
set_runs(shape(s10, 25).text_frame.paragraphs[0], "에너지 선속의 발산")
set_runs(shape(s10, 26).text_frame.paragraphs[0], "엔탈피 대류 + 열전도")
set_runs(shape(s10, 30).text_frame.paragraphs[0], "양극성 장에 대한 일")
set_runs(shape(s10, 35).text_frame.paragraphs[0], "충돌 에너지 손실")
replace_in_runs(shape(s10, 42).text_frame.paragraphs[1], "수송항", "선속항")

# ---- 16쪽(2차 연구 방향): 단계 순서와 용어
s16 = S(16)
replace_in_runs(shape(s16, 2).text_frame.paragraphs[0], "APPENDIX  · ", "")
set_runs(shape(s16, 8).text_frame.paragraphs[0], "단일 코일, r만 변수")
set_runs(shape(s16, 9).text_frame.paragraphs[0], "반경 방향 입자·전자 에너지 보존식으로 계산 알고리즘과 수지 검증")
set_runs(shape(s16, 12).text_frame.paragraphs[0], "이중 코일, z 고려")
set_runs(shape(s16, 13).text_frame.paragraphs[0], "두 코일 장의 퍼짐·겹침을 (r, z) 전자기장으로 계산, 수송은 r 유지")
set_runs(shape(s16, 16).text_frame.paragraphs[0], "z 적분과 축 방향 손실 닫힘")
set_runs(shape(s16, 17).text_frame.paragraphs[0], "(r, z) 식을 z로 적분해 r 식으로 축소, 상·하부 벽 손실 반영 방식 확인")
replace_in_runs(shape(s16, 28).text_frame.paragraphs[1], "유체 에너지 수송 근사", "국소 열전도 근사")
replace_in_runs(shape(s16, 30).text_frame.paragraphs[1], " 지도 → 웨이퍼 밀도비", " 반경 분포 → 웨이퍼 밀도비")

# ---- 쪽 번호: 본문 8–14, 옮길 슬라이드 15, 부록 17–22
for n in range(8, 15):
    set_runs(shape(S(n), 7).text_frame.paragraphs[0], str(n))
set_runs(shape(s16, 33).text_frame.paragraphs[0], "15")
pn = shape(s16, 33); pn.left, pn.top = 8266176, 6044184  # 본문 쪽 번호 위치에 맞춤
for n, sid in zip(range(17, 23), [35, 34, 42, 9, 80, 61]):
    set_runs(shape(S(n), sid).text_frame.paragraphs[0], str(n))

# ---- 발표자 노트: 녹화 대본
def mm(s): return f"{s//60}:{s%60:02d}"
T = json.load(open(timed))
slide_for = {n: S(n) for n in range(1, 15)}
slide_for[15] = s16
for n, title, s0, a, txt in T:
    slide_for[n].notes_slide.notes_text_frame.text = f"[대본 · {mm(s0)}–{mm(s0+a)} / {a}초]\n{txt}"

# ---- 순서: 2차 연구 방향(16번째)을 END(15번째) 앞으로
lst = p.slides._sldIdLst
ids = list(lst)
el = ids[15]
lst.remove(el)
lst.insert(14, el)

p.core_properties.last_modified_by = "주제 3 팀"
p.save(dst)
print("saved", dst)
