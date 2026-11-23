"""1차 발표 수정본 (2026-11-23, 교수님 피드백 반영).

사용: python build.py <원본.pptx> <출력.pptx> <수식 폴더> <그림 폴더> <lib.py 폴더>

- 원본 덱의 양식(4:3 수업 양식, 마스터·레이아웃)과 표지를 그대로 쓰고, 나머지 쪽은 새로 만든다.
- 학회 발표 형식: 제목 = 장 번호와 장 이름, 그 아래 ❖ 소제목 = 이 쪽의 주제, 그림은 Fig. n 캡션,
  핵심 식은 빨간 상자, 아래쪽에 핵심 메시지 한 줄과 출처·계산 조건 각주.
- 색: 파랑 = 안쪽 코일·중앙, 주황 = 바깥쪽 코일·가장자리, 남색 = 구조·결론, 빨강 = 강조.
"""
import json
import sys

SRC, OUT, EQD, FIGD, LIBD = sys.argv[1:6]
sys.path.insert(0, LIBD)
import lib  # noqa: E402
from lib import I, C, tb, box, seg, pic, write  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.util import Pt  # noqa: E402
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.oxml.ns import qn  # noqa: E402
from pptx.oxml.xmlchemy import OxmlElement  # noqa: E402
from PIL import Image  # noqa: E402

lib.EQ_DIR = EQD
lib.EQ_SIZES = json.load(open(f"{EQD}/sizes.json"))
RED, INK, NAVY, MUTED = "C00000", "1F2340", "303399", "5F6779"
C.update(RED=RED)
lib.CMAP.update({"r": "RED"})

prs = Presentation(SRC)
# ---------------------------------------------------------------- 표지만 남기고 지운다
lst = prs.slides._sldIdLst
for sid in list(lst)[1:]:
    rid = sid.rId
    lst.remove(sid)
    prs.part.drop_rel(rid)
TITLE_ONLY = [l for l in prs.slide_layouts if l.name == "제목만"][0]

# 표지: 제목 둘째 줄만 바꾼다 (서식 유지)
cover = prs.slides[0]
for sh in cover.shapes:
    if sh.has_text_frame:
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if r.text == "중앙·가장자리 플라즈마 밀도":
                    pass
                elif r.text == "독립 제어의 이론적 배경":
                    r.text = "독립 제어를 위한 모델링 전략"


# ---------------------------------------------------------------- 공통 요소
def new_slide(title, size=24):
    s = prs.slides.add_slide(TITLE_ONLY)
    tf = s.shapes.title.text_frame
    tf.text = title
    for r in tf.paragraphs[0].runs:
        r.font.size = Pt(size)
    return s


def diamond(p):
    """참고 발표 자료의 ❖ 글머리 (Wingdings v)."""
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(I(0.3)))
    pPr.set("indent", str(-I(0.3)))
    for tag in ("a:buNone", "a:buChar", "a:buFont", "a:buClr"):
        for e in pPr.findall(qn(tag)):
            pPr.remove(e)
    clr = OxmlElement("a:buClr"); c = OxmlElement("a:srgbClr"); c.set("val", INK); clr.append(c); pPr.append(clr)
    f = OxmlElement("a:buFont"); f.set("typeface", "Wingdings"); f.set("pitchFamily", "2"); f.set("charset", "2"); pPr.append(f)
    b = OxmlElement("a:buChar"); b.set("char", "v"); pPr.append(b)


def header(s, text, y=0.98, size=17):
    t = tb(s, 0.5, y, 9.0, 0.42, [{"t": text}], size=size, bold=True, color="1A1A1A", name="소제목")
    diamond(t.text_frame.paragraphs[0])
    return t


def dpara(s, x, y, w, h, items, size=15, after=10, line=1.08, name=None):
    """❖ 문단들 (결론처럼 ❖만 쓰는 쪽)."""
    t = tb(s, x, y, w, h, [{"t": it, "after": after, "line": line} for it in items], size=size, bold=True,
           color="1A1A1A", name=name)
    for p in t.text_frame.paragraphs:
        diamond(p)
    return t


def bullets(s, x, y, w, h, items, size=13, after=5, line=1.05, name=None):
    """items: str = • 항목, ('-', str) = – 아래 항목, ('h', str) = 굵은 소항목 (글머리 없음)."""
    paras = []
    for it in items:
        if isinstance(it, tuple) and it[0] == "-":
            paras.append({"t": it[1], "bullet": True, "char": "–", "indent": 0.2, "size": size - 1, "after": after,
                          "color": "3B4658"})
        elif isinstance(it, tuple) and it[0] == "h":
            paras.append({"t": it[1], "bold": True, "size": size + 1, "after": 3, "color": NAVY,
                          "before": it[2] if len(it) > 2 else 0})
        else:
            paras.append({"t": it, "bullet": True, "after": after})
    t = tb(s, x, y, w, h, paras, size=size, line=line, name=name)
    for p, it in zip(t.text_frame.paragraphs, items):
        if isinstance(it, tuple) and it[0] == "-":
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(I(0.42))); pPr.set("indent", str(-I(0.18)))
    return t


def key(s, text, y=5.93):
    seg(s, 0.5, y, 9.5, y, color=NAVY, w=1.0, name="핵심 메시지 선")
    tb(s, 0.5, y + 0.06, 9.0, 0.42, [{"t": text}], size=14, bold=True, color=NAVY, anchor="m", name="핵심 메시지")


def foot(s, text, y=6.43, h=0.36):
    tb(s, 0.5, y, 8.45, h, [{"t": text, "line": 1.0}], size=9, color=MUTED, name="각주")


def num(s, n):
    lib.slide_number(s, n, x=9.0, y=6.6, w=0.48, h=0.24, size=10)


def caption(s, x, y, w, text, size=10.5, align="c"):
    return tb(s, x, y, w, 0.3, [{"t": text}], size=size, bold=True, color="1A1A1A", align=align, name="그림 캡션")


def fig(s, name, x, y, w=None, h=None):
    path = f"{FIGD}/{name}.png"
    im = Image.open(path)
    ar = im.height / im.width
    if w is not None and h is None:
        h = w * ar
    elif h is not None and w is None:
        w = h / ar
    pic(s, path, x, y, w=w, h=h, name=f"그림 {name}")
    return w, h


def eqn(s, name, x, y, pt=16, align="l", box_w=None, red=False, pad=0.06):
    shp, w, h = lib.eq(s, name, x, y, pt=pt, align=align, box_w=box_w)
    if red:
        b = box(s, shp.left / 914400 - pad, y - pad, w + 2 * pad, h + 2 * pad, fill=None, line=RED, lw=1.5, radius=None,
                name=f"강조 상자 {name}")
        # 상자를 식 뒤로
        sp = s.shapes._spTree
        sp.remove(b._element)
        sp.insert(sp.index(shp._element), b._element)
    return w, h


def eqno(s, text, y, h, x=9.0):
    tb(s, x, y, 0.5, h, [{"t": text}], size=12, color="3B4658", align="r", anchor="m", name="식 번호")


def label(s, x, y, w, text, size=12, color=NAVY, bold=True, h=0.3, align="l"):
    return tb(s, x, y, w, h, [{"t": text}], size=size, bold=bold, color=color, align=align, name="라벨")


def btable(s, x, y, col_w, rows, size=11.5, row_h=0.3, col_align=None, bold_rows=(), colors=None, fills=None,
           header_size=None, name="표", row_heights=None):
    """booktabs 형식 표: 머리 채움 없음, 위·아래 굵은 선, 머리 아래 가는 선."""
    nr, nc = len(rows), len(col_w)
    gf = s.shapes.add_table(nr, nc, I(x), I(y), I(sum(col_w)), I(row_h * nr))
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    sid = tblPr.find(qn("a:tableStyleId"))
    if sid is None:
        sid = OxmlElement("a:tableStyleId"); tblPr.append(sid)
    sid.text = lib.NO_STYLE
    tblPr.set("firstRow", "0"); tblPr.set("bandRow", "0")
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = I(cw)
    for i in range(nr):
        tbl.rows[i].height = I(row_heights[i] if row_heights else row_h)
    for i, row in enumerate(rows):
        for j in range(nc):
            cell = tbl.cell(i, j)
            cell.margin_left = I(0.06); cell.margin_right = I(0.06)
            cell.margin_top = I(0.03); cell.margin_bottom = I(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            f = (fills or {}).get((i, j)) or (fills or {}).get((i, None))
            if f:
                cell.fill.solid(); cell.fill.fore_color.rgb = lib.rgb(f)
            else:
                cell.fill.background()
            al = col_align[j] if col_align else "l"
            hdr = i == 0
            col = (colors or {}).get((i, j)) or (colors or {}).get((i, None)) or ("1A1A1A" if hdr else "222222")
            write(cell.text_frame, [{"t": str(row[j])}], size=(header_size or size) if hdr else size, color=col,
                  bold=hdr or i in bold_rows, align=al, space_after=0, line=1.0)
            top = ("1A1A1A", 1.5) if i == 0 else None
            bot = ("1A1A1A", 0.9) if i == 0 else (("1A1A1A", 1.5) if i == nr - 1 else ("D0D4DC", 0.5))
            lib.cell_borders(cell, T=top, B=bot)
    gf.name = name
    return gf


def flow_box(s, x, y, w, h, text, fill="F2F4F8", line="C9CED8", color="1A1A1A", size=11.5, bold=False, name="상자"):
    return box(s, x, y, w, h, fill=fill, line=line, lw=0.9, radius=0.05,
               paras=[{"t": t_, "line": 1.0, "after": 0} for t_ in text.split("\n")], size=size,
               color=color, bold=bold, align="c", anchor="m", margin=0.05, name=name)


def arrow(s, x1, y1, x2, y2, color="3B4658", w=1.25, dash=False):
    return seg(s, x1, y1, x2, y2, color=color, w=w, head=True, dash=dash, name="화살표")


def notes(s, script, basis=None):
    text = script if basis is None else f"{script}\n\n[근거(읽지 않음)]\n{basis}"
    s.notes_slide.notes_text_frame.text = text


NOTES = {}

# ================================================================ 2 목차
s = new_slide("목차")
items = [
    ("Ⅰ", "서론", "문제 정의와 제어 목표 · 왜 밀도비인가 · 단일 코일의 한계", "3–5"),
    ("Ⅱ", "모델링 전략", "수송은 r, z는 전자기장에만 · 단일 → 이중 코일 · 각 단계의 근거", "6–8"),
    ("Ⅲ", "지배 방정식과 계산 방법", "축대칭 유도장 · 입자·전자 에너지 보존식 · 자기일관 반복", "9–11"),
    ("Ⅳ", "독립 제어 판정과 검증 계획", "제어 Jacobian과 형상 이득 · COMSOL 교차 검증", "12–13"),
    ("Ⅴ", "결론", "과제 검토 사항 대응 · 한계 · 2차 계획", "14"),
]
y = 1.35
for rn, name, desc, pg in items:
    tb(s, 0.75, y, 0.75, 0.5, [{"t": rn + "."}], size=22, bold=True, color=NAVY, name="장 번호")
    tb(s, 1.5, y + 0.02, 6.6, 0.42, [{"t": name}], size=19, bold=True, color="1A1A1A", name="장 이름")
    if desc:
        tb(s, 1.5, y + 0.45, 6.9, 0.3, [{"t": desc}], size=12.5, color=MUTED, name="장 설명")
    tb(s, 8.3, y + 0.04, 1.0, 0.4, [{"t": pg}], size=13, color=MUTED, align="r", name="쪽")
    y += 0.92
foot(s, "부록 A1–A8 (17쪽부터): 0D 균형식, r 모델 유도, 2포트 전력 조건, 코일 간 결합, 웨이퍼 지표, 모델 가정, 근거 계산의 조건, 구동 수단 선택")
num(s, 2)
NOTES[2] = (None,
            "20분 녹화 발표. 쪽별 시간은 각 노트 머리에 적음. 합계 20:00.")

# ================================================================ 3 문제 정의
s = new_slide("Ⅰ. 서론 (1/3)")
header(s, "문제 정의와 제어 목표")
w, h = fig(s, "fig_chamber", 0.45, 1.5, w=4.5)
caption(s, 0.45, 1.5 + h + 0.03, 4.5, "Fig. 1. 이중 코일 ICP 반단면 (축척 일치)")
btable(s, 0.5, 4.5, [1.15, 3.25], [
    ["항목", "값"],
    ["챔버", "R = 21 cm, L = 6 cm, 유전체 창 두께 1.5 cm"],
    ["코일", "안쪽 r = 7.5, 8.5 cm, 바깥쪽 r = 15.25, 15.75 cm (각 2턴)"],
    ["운전 조건", "Ar 10 mTorr, 13.56 MHz, 총 전력 300 W (기준)"],
], size=10.5, row_h=0.29, col_align=["l", "l"], name="형상 표")
bullets(s, 5.2, 1.42, 4.3, 1.45, [
    ("h", "문제 정의 (과제)"),
    "하나의 챔버에서 중앙부·가장자리 밀도를 독립적으로 조절하는 소스를 설계하고, 밀도비 n_{c}/n_{edge}를 원하는 값으로 조정한다.",
    "검토 사항 4: 전체 밀도 변화와 공간 분포 변화를 구분한다.",
], size=12, after=3)
bullets(s, 5.2, 2.9, 4.3, 0.7, [
    ("h", "제어 목표"),
    "평균 밀도 n̄_{w}는 [[r:유지]]하고, 밀도비 ρ만 [[r:옮긴다]].",
], size=12)
eqn(s, "rho", 5.45, 3.62, pt=18, red=True)
eqn(s, "avg", 7.0, 3.72, pt=11)
bullets(s, 5.2, 4.45, 4.3, 1.4, [
    "목표: ρ = 0.8–1.2 (기준점 1.27), n̄_{w} 변화 ±5% 이내",
    "입력: 총 전력 P_{tot}, 전류비 k = |I_{out}|/|I_{in}|, 위상차 φ",
], size=12)
key(s, "목표는 밀도의 크기(n̄_{w})가 아니라 모양(ρ)을 따로 움직이는 것이다.")
foot(s, "n̄_{w}: 웨이퍼(R_{w} = 15 cm) 면적 평균 (부록 A5). 챔버 R, L은 [3]과 같음. 기준점: 두 코일 직렬 (모델 계산).")
num(s, 3)
NOTES[3] = (None,
            "형상: 하이브리드 모델 config (R 0.21, L 0.06, 창 0.015, 코일 간격 0.005 m, r_in 7.5/8.5, r_out 15.25/15.75 cm). 목표 범위: 팀 1차 결정. [3] Zhao et al. 2026과 같은 R, L.")

# ================================================================ 4 왜 밀도비인가
s = new_slide("Ⅰ. 서론 (2/3)")
header(s, "왜 밀도비 ρ를 제어 출력으로 쓰는가")
box(s, 0.5, 1.42, 9.0, 0.5, fill="F2F4F8", line=None, radius=None, margin=0.1, anchor="m",
    paras=[{"t": "출력은 (n̄_{w}, ρ) 두 개: 공정 속도와 균일도에 대응하며, (n_{c}, n_{edge})와 정보량은 같다.", "line": 1.0}],
    size=11, color="1A1A1A", name="틀")
X0, XT, TW = 0.5, 0.88, 5.05
LH = 0.205
items4 = [
    ("1", "입력과 출력의 짝이 맞는다", 1.99, 3,
     "수준은 전력 평형(n_{0} ∝ P_{abs})이, 모양은 가열 위치가 정한다 → 전력은 n̄_{w}에, 전류비는 ρ에 짝지어 대각에 가깝게 한다. (n_{c}, n_{edge})는 두 코일 모두에 함께 반응한다 (8쪽).",
     "scale", "단일 코일 100 → 1000 W: n̄_{w} 9.4배, ρ 1.40 → 1.15 (7쪽)"),
    ("2", "측정의 공통 배율 오차가 상쇄된다", 3.62, 2,
     "탐침 면적·보정 계수는 비에서 사라지고 T_{e} 차이만 남는다 (기준점 약 2%).", "isat", None),
    ("3", "모델의 공통 오차에 덜 민감하다", 4.98, 2,
     "축 방향 손실 처리를 바꾸면 n̄_{w} 1.66배, ρ 1.14배. 단, 열전도처럼 모양을 바꾸는 가정은 남는다 (13쪽).", None, None),
]
for n_, title, y0, nl, body, eqname, small in items4:
    tb(s, X0, y0 - 0.02, 0.35, 0.34, [{"t": n_}], size=17, bold=True, color=NAVY, name="번호")
    tb(s, XT, y0, TW, 0.3, [{"t": title}], size=13.5, bold=True, color="1A1A1A", name="항목 제목")
    tb(s, XT, y0 + 0.29, TW, LH * nl, [{"t": body, "line": 1.0}], size=11.5, color="222222", name="항목 본문")
    yb = y0 + 0.29 + LH * nl
    if eqname == "scale":
        eqn(s, "scale", XT, yb + 0.04, pt=11)
        tb(s, XT, yb + 0.33, TW, 0.22, [{"t": small}], size=10, color=MUTED, name="항목 주")
    elif eqname == "isat":
        eqn(s, "isat", XT, yb + 0.02, pt=9.5)
w, h = fig(s, "fig_concept", 6.15, 2.02, w=3.35)
caption(s, 6.15, 2.02 + h + 0.02, 3.35, "Fig. 2. 크기와 모양의 분리 (개념도)", size=10.5)
key(s, "(n̄_{w}, ρ)는 전력과 전류비의 작용에 맞춘 좌표이고, ρ는 분포의 모양만 담는다.")
foot(s, "[1] 식 (2.73) 전력 평형, 식 (5.5) 이온 포화 전류. 수치는 기준점 모델 계산 (부록 A7).")
num(s, 4)

# ================================================================ 5 단일 코일의 한계
s = new_slide("Ⅰ. 서론 (3/3)")
header(s, "단일 코일의 한계와 공간 분포 모델의 필요성")
btable(s, 0.5, 1.45, [1.85, 1.3, 3.1, 2.75], [
    ["모델", "조절 입력", "계산되는 것", "ρ에 대한 결론"],
    ["0D, 단일 코일", "P_{tot}", "T_{e} (a), n_{0} ∝ P_{abs} (b)", "ρ를 정의할 수 없다"],
    ["0D, 이중 코일", "P_{tot}, k, φ", "세 입력이 P_{abs} 하나로 합쳐짐 (부록 A1)", "k, φ의 효과를 구분할 수 없다"],
    ["공간 모델, T_{e} 균일", "P_{tot}, k, φ", "확산 기본 모드 (c): 모양이 R, L로 고정", "ρ가 k, φ와 무관하다"],
    ["공간 모델, T_{e}(r)", "P_{tot}, k, φ", "가열 → T_{e}(r) → 이온화 → n(r)", "k, φ가 ρ를 바꿀 수 있다 → 채택"],
], size=11.5, row_h=0.34, col_align=["l", "l", "l", "l"], bold_rows=(4,), colors={(4, None): NAVY})
yE = 3.38
w1, h1 = eqn(s, "te", 0.6, yE, pt=13)
w2, h2 = eqn(s, "n0", 0.6 + w1 + 0.35, yE + 0.02, pt=13)
w3, h3 = eqn(s, "mode", 0.6 + w1 + w2 + 0.65, yE + 0.04, pt=10.5)
for x_, w_, t_ in ((0.6, w1, "(a) 입자 균형 [1] (2.70)"), (0.6 + w1 + 0.35, w2, "(b) 전력 균형 (2.73)"),
                   (0.6 + w1 + w2 + 0.65, w3, "(c) T_{e} 균일일 때 (1.76)–(1.83)")):
    tb(s, x_, yE + 0.62, max(w_, 1.9), 0.25, [{"t": t_}], size=10, color=MUTED, name="식 설명")
# 계산 사슬
chain = [("코일 전류\nk, φ", "EEF3FB", "3366CC"), ("가열\np_{abs}(r, z)", "F2F4F8", "C9CED8"),
         ("전자온도\nT_{e}(r)", "FBEDE4", "D9622B"), ("이온화\nG = n_{g}K_{iz}(T_{e}) n", "F2F4F8", "C9CED8"),
         ("밀도\nn(r)", "F2F4F8", "C9CED8"), ("밀도비\nρ", "ECECF7", NAVY)]
xs, bw, gap, yc = 0.5, 1.22, 0.336, 4.45
for i, (t_, f_, l_) in enumerate(chain):
    flow_box(s, xs + i * (bw + gap), yc, bw, 0.62, t_.replace("\n", "\n"), fill=f_, line=l_, size=11)
    if i < len(chain) - 1:
        arrow(s, xs + i * (bw + gap) + bw + 0.03, yc + 0.31, xs + (i + 1) * (bw + gap) - 0.03, yc + 0.31)
tb(s, 1.72, yc + 0.68, 5.0, 0.62,
   [{"t": "T_{e} 6% 차이 → 이온화 계수 K_{iz} 41% 차이", "line": 1.0},
    {"t": "(기준점 3.10–3.28 V) · 크기는 가열 국소성과 열전도의 경쟁이 정함 (13쪽)", "line": 1.0, "size": 9.5, "color": MUTED}],
   size=11, bold=True, color="B24A16", align="c", name="민감도 설명")
key(s, "ρ를 다루려면 위치마다 다른 가열과 전자온도를 푸는 공간 모델이 필요하다.")
foot(s, "[1] §2.4 (2.70), (2.73), §1.10 (1.76)–(1.83). z는 웨이퍼 쪽 벽에서 잰다. 0D 세부: 부록 A1.")
num(s, 5)

# ================================================================ 6 단계적 모델
s = new_slide("Ⅱ. 모델링 전략 (1/3)")
header(s, "단계적 모델: 수송은 r로 풀고, z는 전자기장에만 쓴다")
for px, ttl, col, rows_, fb in (
        (0.5, "1단계 · 단일 코일: 미지수는 r만", NAVY,
         [("전자기장 (r, z)\n코일 장 하나", "EEF3FB", "3366CC"), ("가열 S(r)\n= ∫p_{abs} dz", "F2F4F8", "C9CED8"),
          ("수송 (r)\nn(r), T_{e}(r)", "FBEDE4", "D9622B")],
         ["단일 코일 = 두 코일 직렬 (k = 1, φ = 0)", "입력은 P_{tot} 하나, 가열 모양은 σ_{p}로만 변함", "비선형 미지수 2N_{r} = 120개 (수송)"]),
        (5.15, "2단계 · 이중 코일: 두 장의 겹침까지", "7A3FA0",
         [("전자기장 (r, z)\n코일별 A_{in}, A_{out}", "EEF3FB", "3366CC"), ("가열 S(r; k, φ)\n= ∫p_{abs} dz", "F2F4F8", "C9CED8"),
          ("수송 (r)\n1단계와 같음", "FBEDE4", "D9622B")],
         ["k, φ가 가열 모양 자체를 바꾼다", "전자기장은 선형: 분해 한 번에 두 코일 해", "수송은 1단계와 같은 r 모델"])):
    box(s, px, 1.47, 4.35, 2.95, fill="FFFFFF", line="C9CED8", lw=0.9, radius=None, name="단계 틀")
    tb(s, px + 0.15, 1.55, 4.1, 0.32, [{"t": ttl}], size=13.5, bold=True, color=col, name="단계 제목")
    bw_, gap_ = 1.17, 0.27
    for i, (t_, f_, l_) in enumerate(rows_):
        flow_box(s, px + 0.15 + i * (bw_ + gap_), 1.98, bw_, 0.72, t_, fill=f_, line=l_, size=10.5)
        if i < len(rows_) - 1:
            arrow(s, px + 0.15 + i * (bw_ + gap_) + bw_ + 0.02, 2.34, px + 0.15 + (i + 1) * (bw_ + gap_) - 0.02, 2.34)
    if True:
        seg(s, px + 0.15 + 2 * (bw_ + gap_) + bw_ / 2, 2.72, px + 0.15 + 2 * (bw_ + gap_) + bw_ / 2, 2.86, color="D9622B", w=1.0, dash=True)
        seg(s, px + 0.15 + 2 * (bw_ + gap_) + bw_ / 2, 2.86, px + 0.15 + bw_ / 2, 2.86, color="D9622B", w=1.0, dash=True)
        arrow(s, px + 0.15 + bw_ / 2, 2.86, px + 0.15 + bw_ / 2, 2.73, color="D9622B", w=1.0)
        tb(s, px + 1.3, 2.9, 2.3, 0.2, [{"t": "σ_{p}(n_{e}, T_{e}) 갱신"}], size=9, color="B24A16", align="c", name="되먹임")
    bullets(s, px + 0.12, 3.15, 4.15, 1.25, fb, size=11.5, after=2)
btable(s, 0.5, 4.62, [3.6, 1.35, 1.55, 2.5], [
    ["계산 구성", "수송 미지수", "운전점 1개", "웨이퍼 위 ρ (차이)"],
    ["전자기장 (r, z) + 수송 r  [채택]", "120", "0.15 s", "1.268 (0.3%)"],
    ["전자기장 (r, z) + 수송 (r, z)", "2,880", "≈ 0.3 s", "1.272 (기준)"],
], size=12, row_h=0.33, col_align=["l", "r", "r", "r"], bold_rows=(1,), colors={(1, None): NAVY})
key(s, "z는 선형 전자기장에만 쓰고, 비선형 수송은 두 단계 모두 r로 푼다.")
foot(s, "격자 60 × 56 (플라즈마 24층), 300 W, Ar 10 mTorr, 시간은 전자기장 포함 (모델 계산). 가열까지 r만으로 구하는 표면 임피던스 근사는 2차 검토.", h=0.4)
num(s, 6)
NOTES[6] = (None,
            "fig_log transport_pairs 10 mTorr: ρ 1.2682 (r) / 1.2722 (r,z), 시간 0.154 / 0.379 s (전자기장 포함; 재실행마다 (r, z) 0.27–0.38 s → 표에는 ≈ 0.3 s). 미지수: 수송 2×60, 2×60×24. 전자기장 60×56.")

# ================================================================ 7 1단계 근거
s = new_slide("Ⅱ. 모델링 전략 (2/3)")
header(s, "1단계 근거: 단일 코일의 수송은 r만으로 충분하다")
bullets(s, 0.5, 1.42, 9.0, 0.28, [
    "축 방향 구조가 먼저 정착한다: 손실률이 반경 방향의 약 21배 → 기본 모드로 두고 z로 적분",
], size=11.5, after=2)
eqn(s, "axial", 0.75, 1.73, pt=10.5)
bullets(s, 0.5, 2.17, 9.0, 1.38, [
    "T_{e}는 축 방향으로 거의 균일하다: λ_{ε} ≈ 12 cm > L = 6 cm (10 mTorr) [2, 4]",
    ("-", "λ_{ε}는 중앙–가장자리 거리(≈ 10 cm)와도 비슷 → [[r:제어 권한은 열전도 가정에 달림]] (13쪽)"),
    "결과: r 모델과 (r, z) 모델의 ρ 차이 [[r:0.3%]] (10 mTorr), 3.0% (50 mTorr) (Fig. 3b)",
    "단, [[r:가열은 갱신한다]]: S(r) 모양 차이 ≤ 9% (100–1000 W, 5–50 mTorr, Fig. 3a)",
    ("-", "이 모델에서 ρ의 전력 의존성은 이 변화에서만 온다 (수송 식이 밀도에 1차 동차)"),
], size=11.5, after=2)
w, h = fig(s, "fig_single", 1.2, 3.55, w=7.6)
caption(s, 0.5, 3.55 + h + 0.02, 9.0, "Fig. 3. (a) 단일 코일 가열 모양 S(r)의 조건 의존성, (b) 웨이퍼 위 밀도: r 모델(실선)과 (r, z) 모델(점선)")
key(s, "단일 코일은 미지수를 n(r), T_{e}(r)로 줄이고, 가열 모양만 전자기장에서 갱신하면 된다.")
foot(s, "모양 차이 = ½∫|s_{1} − s_{2}| dA. 1차 동차는 중성 밀도 고정·한 단계 이온화 가정의 결과 (13쪽). 유도: 부록 A2, 값: 부록 A7.")
num(s, 7)

# ================================================================ 8 2단계 근거
s = new_slide("Ⅱ. 모델링 전략 (3/3)")
header(s, "2단계 근거: 이중 코일은 전자기장을 (r, z)로 풀어야 한다")
bullets(s, 0.5, 1.42, 9.0, 1.6, [
    "가열 모양 자체가 제어 대상이다: k = 0.5–2, φ = 0–180°에서 S(r) 모양 차이 [[r:7–43%]] (단일 코일 ≤ 9%)",
    ("-", "선행 계산 [3]은 Cl_{2} 40 mTorr(λ_{ε}가 짧음)라 Ar 저압에 그대로 옮길 수 없다"),
    "그 모양은 각 코일의 장이 z 방향으로 퍼지는 정도가 정하며, 전도도가 r에 따라 달라 (r, z)를 함께 풀어야 한다 (Fig. 4a)",
    "코일–플라즈마 거리 d = 2.0 → 4.5 cm: 두 코일 가열의 겹침 [[r:0.19 → 0.39]] (Fig. 4b), 단일 코일 ρ는 5%만 변화",
    "깊이 방향은 분리된다: p_{abs}(r, z) ≈ S(r)·w(z) (첫 특이값 비중 ≥ 99.7%) → 수송은 r 유지",
], size=12, after=2)
w, h = fig(s, "fig_dual", 0.6, 2.7, w=8.8)
caption(s, 0.5, 2.7 + h + 0.04, 9.0, "Fig. 4. (a) 코일별 1 A 장의 (r, z) 분포, (b) 거리 d에 따른 코일별 가열 모양 (z 적분)")
key(s, "z가 필요한 것은 두 코일 장의 겹침을 계산하는 전자기장 단계이며, 수송은 r로 충분하다.")
foot(s, "겹침 O = ∫min(s_{in}, s_{out}) dA (0: 분리, 1: 같음). d = 창 두께 + 코일 간격. 값: 부록 A7.")
num(s, 8)

# ================================================================ 9 전자기장
s = new_slide("Ⅲ. 지배 방정식과 계산 방법 (1/3)")
header(s, "전자기장: 축대칭 유도장과 흡수 전력 (r, z)")
rows9 = [
    ("A", 11.5, 1.48, "(1)", "축대칭 → A_{θ} 한 성분. 축·금속 벽 A_{θ} = 0, 변위 전류 무시 (λ_{0} ≈ 22 m)"),
    ("sigma", 12.5, 2.2, "(2)", "국소 복소 전도도: n_{e}, T_{e}가 전자기장에 들어가는 자리"),
    ("super", 12.5, 2.98, "(3)", "σ_{p} 고정 시 선형 → 단위 전류 해 2개로 모든 (k, φ)"),
    ("pabs", 12, 3.55, "(4)", "파랑: 안쪽 코일, 주황: 바깥쪽 코일, 남색: 간섭항. ψ = arg(A_{out}/A_{in})"),
    ("S", 12, 4.2, "(5)", "수송으로 넘기는 값 S(r). 전류 진폭 I_{0}는 포트 전력 조건 (부록 A3)"),
]
for name, pt, y0, no, note in rows9:
    w_, h_ = eqn(s, name, 0.6, y0, pt=pt, red=(name == "pabs"))
    eqno(s, no, y0, h_, x=6.25)
    tb(s, 6.85, y0 + h_ / 2 - 0.24, 2.65, 0.5, [{"t": note, "line": 1.0}], size=10.5, color="3B4658", anchor="m", name="식 설명")
box(s, 0.5, 5.0, 9.0, 0.72, fill="F2F4F8", line=None, radius=None,
    paras=[{"t": "받는 값  n_{e}(r), T_{e}(r) (현재 반복)      →      전자기장 단계      →      넘기는 값  S(r) = ∫p_{abs} dz,  I_{0},  P_{abs}"}],
    size=12.5, color="1A1A1A", bold=True, align="c", anchor="m", name="입출력")
key(s, "전자기장 단계의 출력은 수송이 받는 반경 방향 가열 분포 S(r)이다.")
foot(s, "[1] §2.3.4 식 (2.52)–(2.53) 유도 전기장·표피 깊이, 식 (2.31)–(2.32) 흡수 전력; σ_{p}는 [2]. "
        "ψ: 플라즈마 유도 전류가 만드는 위상차 (진공에서 0). 위치마다 부호가 바뀌어 전체 전력에서는 상쇄 (부록 A1).")
num(s, 9)
NOTES[9] = (None,
            "em_field.py. 진공 ψ: σ_p≈0에서 A_in, A_out 실수 → ψ = 0 (why_z.py). 플라즈마에서 ψ −10.7~+10.4°.")

# ================================================================ 10 수송
s = new_slide("Ⅲ. 지배 방정식과 계산 방법 (2/3)")
header(s, "수송: 반경 방향 입자·전자 에너지 보존식 (z 적분, 정상상태)")
label(s, 0.5, 1.4, 3.0, "입자 보존", size=12.5)
w_, h_ = eqn(s, "part", 0.6, 1.66, pt=11.5)
eqno(s, "(6)", 1.66, h_)
label(s, 0.5, 2.2, 3.0, "전자 에너지 보존", size=12.5)
w_, h_ = eqn(s, "energy", 0.6, 2.54, pt=13, red=True)
eqno(s, "(7)", 2.54, h_)
w_, h_ = eqn(s, "q", 0.6, 3.48, pt=11)
eqno(s, "(8)", 3.48, h_)
btable(s, 0.5, 4.2, [0.42, 2.15, 6.43], [
    ["항", "명칭", "정의와 물리적 의미"],
    ["①", "전자 에너지 선속의 발산", "엔탈피 대류 (5/2)eT_{e}Γ_{r} + Fourier 열전도 −κ_{e}dT_{e}/dr (식 8)"],
    ["②", "옴 가열", "흡수 전력 밀도의 z 적분 S (식 5)"],
    ["③", "양극성 전기장에 대한 일", "J_{e,r} = −eΓ_{r} (전자 전류 밀도): 반경 방향 양극성 전위를 거스르며 잃는 에너지"],
    ["④", "충돌 에너지 손실", "C = n_{g}[K_{iz}ε_{iz} + K_{ex}ε_{ex} + K_{el}(3m_{e}/M)T_{e}]: 이온화·여기·탄성"],
    ["⑤", "축 방향 벽 에너지 손실", "쌍마다 (2 + 5.2)T_{e}: 전자 2T_{e} + 이온이 축 방향 프리쉬스·쉬스 전위에서 얻는 에너지 [1] (2.65)"],
], size=10.5, row_h=0.265, col_align=["c", "l", "l"], header_size=11)
key(s, "전자 에너지 보존식은 옴 가열과 네 가지 에너지 이동·손실의 균형이며, 전자온도 분포 T_{e}(r)를 정한다.")
foot(s, "경계: 축 대칭, 옆 벽 Bohm 유출 q_{r} = eΓ_{r}(2T_{e} + V_{s}). K_{j}(T_{e})는 국소 Maxwellian [2]. [1] §1.10, §2.4 (2.63)–(2.65).", h=0.4)
num(s, 10)
NOTES[10] = (None,
             "transport_1d.py docstring과 terms(): div_e + coll + wall_axial − heat − work = 0, q = 2.5 e T Γ − κ dT/dr, κ = 2.5 N e² T/(m ν_m). "
             "EPS_IZ 15.76, EPS_EX 12.14, WALL_COEF = 2 + V_s + 0.5 ≈ 7.2 (V_s = ½ln(M/2πm) ≈ 4.68).")

# ================================================================ 11 자기일관 계산
s = new_slide("Ⅲ. 지배 방정식과 계산 방법 (3/3)")
header(s, "자기일관 계산: 유한체적 이산화와 반복 풀이")
FX, FW = 1.05, 4.3
steps = [("운전 조건  p, P_{tot}, k, φ", "FFFFFF", "C9CED8", False),
         ("0D 초기값  T_{e0}, n_{*}  (부록 A1)", "FFFFFF", "C9CED8", False),
         ("① 전도도 σ_{p}(n_{e}, T_{e})  (식 2)", "F2F4F8", "C9CED8", False),
         ("② 전자기장 (r, z): A_{in}, A_{out}  (식 1)", "EEF3FB", "3366CC", False),
         ("③ 전류 진폭 I_{0}, 가열 S(r)  (식 4–5)", "F2F4F8", "C9CED8", False),
         ("④ 수송 (r): Newton으로 n(r), T_{e}(r)  (식 6–8)", "FBEDE4", "D9622B", False),
         ("⑤ 수렴 판정", "FFFFFF", NAVY, True),
         ("결과  n̄_{w}, ρ", "ECECF7", NAVY, True)]
yy = 1.45
ys = []
for t_, f_, l_, b_ in steps:
    flow_box(s, FX, yy, FW, 0.4, t_, fill=f_, line=l_, size=11, bold=b_)
    ys.append(yy)
    yy += 0.54
for i in range(len(steps) - 1):
    arrow(s, FX + FW / 2, ys[i] + 0.41, FX + FW / 2, ys[i + 1] - 0.01)
tb(s, FX + FW / 2 + 0.12, ys[6] + 0.39, 0.6, 0.2, [{"t": "예"}], size=9.5, color=NAVY, bold=True, name="예")
# 되먹임 (⑤ → ①)
xl = FX - 0.32
seg(s, FX, ys[6] + 0.2, xl, ys[6] + 0.2, color="D9622B", w=1.25, dash=True)
seg(s, xl, ys[6] + 0.2, xl, ys[2] + 0.2, color="D9622B", w=1.25, dash=True)
arrow(s, xl, ys[2] + 0.2, FX - 0.01, ys[2] + 0.2, color="D9622B")
tb(s, 0.2, ys[6] + 0.22, 0.75, 0.22, [{"t": "아니오"}], size=9.5, color="B24A16", bold=True, align="c", name="되먹임 글")
tb(s, 0.2, ys[3], 0.5, 0.9, [{"t": "바깥", "after": 0}, {"t": "반복", "after": 0}], size=9.5, color="5F6779", align="c", anchor="m", name="반복 이름")
box(s, FX - 0.12, ys[2] - 0.1, FW + 0.24, ys[6] - ys[2] + 0.6, fill=None, line="8C93A3", lw=0.75, radius=None, dash=True,
    name="반복 영역")
bullets(s, 5.75, 1.42, 3.75, 4.45, [
    ("h", "이산화"),
    "유한체적: 셀마다 수지를 맞춰 전체 보존이 성립",
    ("h", "풀이", 4),
    "미지수 [ln n, T_{e}]: 밀도가 항상 양수, Newton 반복",
    ("h", "수렴 판정", 4),
    "갱신량, 결합 잔차, 입자·에너지 수지 세 가지가 모두 작을 때",
    ("h", "검산 (모델 계산)", 4),
    "포인팅 정리 3 × 10^{−16}, 입자 수지 10^{−14}, 에너지 수지 5 × 10^{−10}",
    "T_{e} 균일 극한의 해석해(J_{0}) 대비 0.01%",
    "다른 초기값 40쌍에서 같은 해 (차이 ≤ 2 × 10^{−7})",
    "운전점당 0.15 s, 바깥 반복 5–10회",
], size=11.5, after=2)
key(s, "전자기장과 수송을 번갈아 풀어, n_{e}·T_{e}와 가열 분포가 서로 맞을 때까지 반복한다.")
foot(s, "수치 수렴은 채택한 식을 정확히 풀었다는 뜻이며, 모델 가정의 타당성은 Ⅳ의 교차 검증으로 확인한다.")
num(s, 11)
NOTES[11] = (None,
             "verify.py 11항목 통과(2026-11-13). Newton 야코비안: 3색 × 2변수 = 잔차 6번.")

# ================================================================ 12 판정 기준
s = new_slide("Ⅳ. 독립 제어 판정과 검증 계획 (1/2)")
header(s, "독립 제어 판정: 제어 Jacobian과 평균 유지 형상 이득")
w_, h_ = eqn(s, "J", 0.6, 1.5, pt=12.5)
eqno(s, "(9)", 1.5, h_, x=5.0)
tb(s, 0.6, 1.5 + h_ + 0.02, 4.9, 0.25, [{"t": "수렴해의 중앙 차분 (전력·전류비 ±2%, 위상 ±2°)"}], size=10, color=MUTED, name="식 설명")
tb(s, 0.6, 2.45, 4.9, 0.28, [{"t": "평균 밀도 유지 조건"}], size=12, bold=True, color=NAVY, name="라벨")
w_, h_ = eqn(s, "hold", 0.6, 2.73, pt=10.5)
eqno(s, "(10)", 2.73, h_, x=5.0)
tb(s, 0.6, 3.3, 4.9, 0.28, [{"t": "평균 유지 형상 이득"}], size=12, bold=True, color=NAVY, name="라벨")
w_, h_ = eqn(s, "gk", 0.75, 3.62, pt=14, red=True)
eqno(s, "(11)", 3.62, h_, x=5.0)
w_, h_ = eqn(s, "need", 0.6, 4.4, pt=10.5)
eqno(s, "(12)", 4.4, h_, x=5.0)
# 개념도: (Δln n̄, Δln ρ) 평면
OX, OY, U = 7.45, 2.45, 1.0
seg(s, 5.85, OY, 9.4, OY, color="B8BECA", w=0.9, head=True, name="가로축")
seg(s, OX, 4.35, OX, 1.45, color="B8BECA", w=0.9, head=True, name="세로축")
tb(s, 8.65, OY - 0.3, 0.85, 0.25, [{"t": "Δln n̄_{w}"}], size=10, color=MUTED, align="r", name="축 이름")
tb(s, OX + 0.06, 1.42, 0.9, 0.25, [{"t": "Δln ρ"}], size=10, color=MUTED, name="축 이름")
pk = (OX - 0.30 * U, OY + 1.25 * U)
arrow(s, OX, OY, OX + 1.55 * U, OY + 0.16 * U, color="3B4658", w=1.75)
tb(s, OX + 0.5, OY + 0.2, 1.6, 0.3, [{"t": "전력 P_{tot}"}], size=10.5, color="3B4658", bold=True, name="벡터 이름")
arrow(s, OX, OY, pk[0], pk[1], color="B24A16", w=1.75)
tb(s, 5.85, OY + 0.95, 1.3, 0.3, [{"t": "전류비 k"}], size=10.5, color="B24A16", bold=True, align="r", name="벡터 이름")
pc = pk[1] + 0.30 * 0.16 / 1.55   # 전력 보정은 전력 화살표와 평행 (식 10)
arrow(s, pk[0], pk[1], OX - 0.02, pc, color="3B4658", w=1.1, dash=True)
arrow(s, OX + 0.05, OY, OX + 0.05, pc, color=RED, w=2.25)
tb(s, OX + 0.12, OY + 0.75, 1.95, 0.5, [{"t": "g_{k}Δln k", "bold": True, "color": RED}, {"t": "평균 유지, ρ만 변화", "size": 9.5, "color": RED}],
   size=11, name="벡터 이름")
tb(s, 6.55, pk[1] + 0.02, 1.2, 0.25, [{"t": "전력 보정 (10)"}], size=9, color="3B4658", align="c", name="벡터 이름")
caption(s, 5.85, 4.42, 3.65, "Fig. 5. 판정의 기하적 의미 (개념도)", size=10)
btable(s, 0.5, 4.88, [1.3, 2.75, 4.95], [
    ["판정 항목", "기준", "의미"],
    ["랭크", "rank J = 2", "두 출력을 다른 방향으로 움직일 수 있다 (단일 코일: J는 2×1, rank 1)"],
    ["형상 이득", "g_{k} ≠ 0, 필요한 Δln k가 구동 범위 안", "평균을 유지하며 ρ를 목표 범위로 옮길 수 있다 (식 12)"],
], size=10.5, row_h=0.3, col_align=["l", "l", "l"])
key(s, "평균을 맞춘 뒤에도 전류비가 밀도비를 바꾸면(g_{k} ≠ 0), 형상만 바꾸는 독립 제어가 가능하다.")
foot(s, "식 (12)는 국소 감도로 낸 1차 어림이고, 실제 도달은 k 전 범위 탐색으로 확인한다 (φ = 180°에서 ρ(k)는 단조가 아님). φ도 같은 방식의 g_{φ}로 본다. 값은 2차 발표에서 제시.", h=0.4)
num(s, 12)
NOTES[12] = (None,
             "control.py control_jacobian (rel_P 0.02, d_k 0.02, d_phi 2°). 그림 5는 개념도(축척 임의, 방향만 의미). 값은 2차 발표로 미룸(팀 결정 11-23).")

# ================================================================ 13 검증 계획
s = new_slide("Ⅳ. 독립 제어 판정과 검증 계획 (2/2)")
header(s, "검증 계획: COMSOL 교차 검증과 모델 가정 점검")
label(s, 0.5, 1.42, 4.3, "단계별 교차 검증 (COMSOL 2D 축대칭)", size=12.5)
steps13 = [("1", "전자기장 단독 비교", "같은 σ_{p}에서 S(r), 코일 임피던스 · 합격: 1% 이내"),
           ("2", "단일 코일 자기일관 해", "n(r, z_{w}), T_{e}(r), ρ · 합격(안): ρ 5% 이내"),
           ("3", "이중 코일 k, φ 변화", "ρ 변화의 방향·크기, g_{k} · 합격(안): 부호 일치, g_{k} 30% 이내"),
           ("4", "측정 대조 (가능 시)", "탐침으로 n_{c}, n_{edge} [5]")]
yy = 1.78
for n_, t_, d_ in steps13:
    tb(s, 0.5, yy, 0.32, 0.32, [{"t": n_}], size=15, bold=True, color=NAVY, name="번호")
    tb(s, 0.85, yy + 0.01, 3.95, 0.28, [{"t": t_}], size=12, bold=True, color="1A1A1A", name="단계 제목")
    tb(s, 0.85, yy + 0.29, 3.95, 0.55, [{"t": d_, "line": 1.0}], size=10.5, color="3B4658", name="단계 설명")
    yy += 1.0
label(s, 5.05, 1.42, 4.45, "점검할 모델 가정", size=12.5)
btable(s, 5.05, 1.78, [1.42, 1.58, 1.45], [
    ["가정", "영향 (모델 계산)", "점검 방법"],
    ["전자 열전도 κ_{e} (제어 권한의 핵심)", "κ_{e} × 3 → ρ +16%, n̄_{w} 0.3%", "COMSOL, 비국소 효과 [4]"],
    ["축 방향 손실 닫힘", "n̄_{w} 1.66배, ρ 1.14배", "(r, z) 수송, COMSOL"],
    ["국소 Maxwellian EEDF", "K_{iz}(T_{e})의 지수 민감도", "문헌 EEDF [4], 탐침"],
    ["충돌 없는 가열, 축전 결합", "저압 효율, 코일 전압 1–3 kV", "COMSOL 전자기"],
    ["밀도 의존 과정: 다단계 이온화, 중성 고갈", "ρ의 전력 의존성 (7쪽)", "COMSOL 반응 모델"],
], size=10, row_h=0.55, col_align=["l", "l", "l"], header_size=10.5, row_heights=[0.34, 0.72, 0.62, 0.62, 0.62, 0.72])
key(s, "COMSOL로 전자기장 → 단일 → 이중 코일 순서로 대조하고, 열전도 가정부터 가린다.")
foot(s, "영향 값은 기준점 모델 계산, 합격 기준 (안)은 팀 제안값.")
num(s, 13)

# ================================================================ 14 결론
s = new_slide("Ⅴ. 결론")
paras = [
    "과제의 밀도비 목표를 [[r:n̄_{w} 유지 + ρ 조절]]의 두 출력으로 정의하고, 전력은 n̄_{w}에, 전류비는 ρ에 짝지었다. 실제 분리 정도는 2차에서 J로 확인한다.",
    "이중 코일의 k, φ는 [[r:가열 → T_{e}(r) → 이온화 분포]]를 거쳐 ρ를 바꾼다. 모델은 수송을 r로, 전자기장을 (r, z)로 풀며 단일에서 이중 코일로 확장한다.",
    "한계와 부작용: 제어 권한은 [[r:T_{e}(r) 비균일(전자 열전도)]]에 달려 COMSOL 검증 1순위이고, φ ≠ 0이면 두 전원 사이에 전력이 오간다 (부록 A3).",
]
t = dpara(s, 0.5, 1.05, 9.0, 1.8, paras, size=13.5, after=6, line=1.05)
for p in t.text_frame.paragraphs:
    for r in p.runs:
        if r.font.color.rgb != lib.rgb(RED):
            r.font.bold = False
label(s, 0.5, 2.88, 9.0, "과제 검토 사항 대응", size=12.5)
btable(s, 0.5, 3.18, [2.25, 4.0, 2.75], [
    ["검토 사항 (과제)", "이번 발표", "2차 발표"],
    ["1 수단 선택과 영향 영역", "독립 전원 2대 + 동심 코일 (부록 A8), 코일별 가열 영역 (Fig. 4)", "구동부 구성도, 대안 비교"],
    ["2 상호 영향의 원인", "장의 겹침 (8쪽, 부록 A4), 입자·에너지 확산 (10쪽)", "결합의 크기 (J의 비대각)"],
    ["3 한쪽 유지 보상", "전력 보정 조건 식 (10), 형상 이득 g_{k} (12쪽)", "조정 절차, 도달 가능한 ρ 범위"],
    ["4 측정과 검증", "(n̄_{w}, ρ) 분리, 탐침 비 측정 (4쪽), COMSOL (13쪽)", "측정 배치와 오차 예산"],
], size=11, row_h=0.46, col_align=["l", "l", "l"], header_size=11.5)
key(s, "평균을 유지한 채 ρ를 옮기는 원리와 판정·검증 방법을 세웠고, 2차 발표에서 결과로 답한다.")
num(s, 14)

# ================================================================ 15 참고문헌
s = new_slide("참고문헌")
refs = [
    "[1]  정진욱, 『플라즈마 전자공학』, 제4판, 교문사, 2026.",
    "[2]  M. A. Lieberman and A. J. Lichtenberg, Principles of Plasma Discharges and Materials Processing, 2nd ed., Wiley, 2005.",
    "[3]  M.-L. Zhao, X.-J. Wang, D.-Q. Wen, Y.-R. Zhang, F. Gao, and Y.-N. Wang, \"Improvement of the plasma uniformity via current amplitudes and phase shifts in dual-coil antenna driven inductively coupled electronegative chlorine discharges,\" J. Appl. Phys. 139, 043301 (2026).",
    "[4]  J.-H. Kim and C.-W. Chung, \"Effect of electron kinetics on plasma density in inductively coupled plasmas using a passive resonant antenna,\" Phys. Plasmas 27, 063511 (2020).",
    "[5]  I.-S. Park, H.-J. Kang, K.-H. Kim, and C.-W. Chung, \"Experimental investigation of edge-to-center density ratio in E-H mode transition of an inductively coupled plasma,\" Phys. Plasmas 24, 123506 (2017).",
]
t = tb(s, 0.6, 1.15, 8.8, 4.6, [{"t": r_, "after": 10, "line": 1.05} for r_ in refs], size=12, color="222222", name="참고문헌")
for p in t.text_frame.paragraphs:
    pPr = p._p.get_or_add_pPr(); pPr.set("marL", str(I(0.45))); pPr.set("indent", str(-I(0.45)))
foot(s, "교재 [1]을 먼저 인용하고, 교재에 없는 내용(국소 전도도, 반응 계수, 에너지 완화 길이)에 [2]를 쓴다. 근거 계산은 팀 모델 코드 (부록 A7).")
num(s, 15)
NOTES[15] = ("[참고문헌]", None)

# ================================================================ 16 END
s = prs.slides.add_slide(TITLE_ONLY)
t = s.shapes.title
t.left, t.top, t.width, t.height = I(0.47), I(3.04), I(9.06), I(0.71)
t.text_frame.text = "END"
t.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
for r in t.text_frame.paragraphs[0].runs:
    r.font.size = Pt(28)
NOTES[16] = ("[끝]", None)

# ================================================================ 부록
def appendix(n_, title, head):
    s = new_slide(f"부록 A{n_} · {title}", size=22)
    header(s, head)
    return s


# A1 0D
s = appendix(1, "0D 균형식", "0D에서 본 단일·이중 코일: 입력이 늘어도 출력은 n_{0} 하나")
label(s, 0.5, 1.45, 4.3, "입자 균형 → T_{e}  [1] (2.70)")
eqn(s, "te", 0.7, 1.8, pt=15)
bullets(s, 0.5, 2.6, 4.3, 0.7, ["T_{e}는 압력과 용기 크기(d_{eff})가 정하고 전력과 무관하다"], size=12)
label(s, 5.1, 1.45, 4.4, "전력 균형 → n_{0}  [1] (2.73)")
eqn(s, "n0", 5.3, 1.8, pt=15)
bullets(s, 5.1, 2.6, 4.4, 0.7, ["n_{0}은 흡수 전력에 비례한다. ε_{T} = ε_{c} + 2T_{e} + 5.2T_{e} (2.65)"], size=12)
label(s, 0.5, 3.35, 9.0, "이중 코일의 흡수 전력: 세 입력이 하나로 합쳐진다")
eqn(s, "pabs0", 0.7, 3.7, pt=15, red=True)
bullets(s, 0.5, 4.45, 9.0, 1.3, [
    "R′_{in}, R′_{out}: 각 코일의 플라즈마 부하 저항, R′_{×}: 교차 저항. 상반성 Z_{io} = Z_{oi} 때문에 전체 전력의 간섭항은 cos φ: 국소 위상 ψ(r, z)(9쪽)는 부피 적분에서 상쇄된다",
    "0D 식에서 k, φ, P_{tot}가 들어갈 자리는 P_{abs}뿐이다 → 같은 P_{abs}면 같은 n_{0}, T_{e}는 불변",
], size=12)
key(s, "0D 균형은 T_{e}와 밀도 수준을 정하지만 분포의 모양은 정하지 않는다.")
foot(s, "[1] §2.4 pp.133–138, 식 (2.63)–(2.73). 반복 계산의 초기값(T_{e0}, n_{*})으로만 쓴다.")
num(s, 17)
NOTES[17] = ("[부록 A1] 5쪽 표의 0D 두 행의 세부. 0D 초기값은 11쪽 계산 흐름의 출발점. 기준점 R_pl 교차항 1.074 Ω, 위상 ~1e-16°(실수), 국소 ψ −10.7~+10.4°.", None)

# A2 r 모델 유도
s = appendix(2, "r 모델 유도", "축 방향 기본 모드와 z 적분: (r, z) 식을 r만의 식으로")
bullets(s, 0.5, 1.45, 9.0, 0.6, ["축 방향 분포를 기본 모드로 두고 위·아래 벽에서 Bohm 유출 조건을 걸면 모드의 위상각 x가 정해진다"], size=12.5)
eqn(s, "axial", 0.8, 1.88, pt=12)
w_, h_ = eqn(s, "ax1", 0.8, 2.48, pt=12.5)
eqno(s, "(A1)", 2.48, h_)
w_, h_ = eqn(s, "ax2", 0.8, 3.15, pt=12.5)
eqno(s, "(A2)", 3.15, h_)
bullets(s, 0.5, 3.85, 9.0, 0.55, ["N(r): z로 적분한 밀도, ν_{L}: 위·아래 벽으로의 입자 손실 주파수 → 본문 식 (6), (7)의 ν_{L}N, ν_{L}ε_{w}T_{e}N 항"], size=12)
label(s, 0.5, 4.42, 9.0, "민감도 점검용 다른 닫힘: 교재의 축 방향 가장자리 밀도비 h_{L}을 쓰는 방식  [1] (2.71)", size=12)
w_, h_ = eqn(s, "ax3", 0.8, 4.78, pt=12.5)
eqno(s, "(A3)", 4.78, h_)
key(s, "T_{e}가 축 방향으로 균일하고 축 방향 구조가 기본 모드로 정착하면, z는 ν_{L} 하나로 요약된다.")
foot(s, "기본 닫힘 (A1)은 (r, z) 수송 검증판과 같은 경계식이어서 두 결과의 차이가 순수한 축소 오차가 된다. (A3)으로 바꾸면 n̄_{w} 1.66배, ρ 1.14배 (모델 계산).")
num(s, 18)
NOTES[18] = ("[부록 A2] physics.axial_mode. robin: x tan x = u_B L/(2D_a), ν_L = D_a k_z^2, ḡ = sin x / x. h_factor: cos x = h_L.", None)

# A3 2포트
s = appendix(3, "2포트 전력 조건", "2포트 임피던스와 전류 진폭 I_{0}")
w_, h_ = eqn(s, "port", 0.7, 1.5, pt=13)
eqno(s, "(A4)", 1.5, h_)
bullets(s, 0.5, 2.25, 9.0, 0.6, ["Z = Z[n_{e}, T_{e}]: 단위 전류 해(본문 식 3)에서 계산하고 반복마다 갱신. 상반성으로 Z_{io} = Z_{oi}"], size=12)
w_, h_ = eqn(s, "I0", 0.7, 2.78, pt=13, red=True)
eqno(s, "(A5)", 2.78, h_)
bullets(s, 0.5, 3.65, 9.0, 0.6, ["k, φ는 상대 진폭·위상, I_{0}는 포트 전력 P_{port}에 맞춘 절대 크기. 세 전력 P_{tot}, P_{port}, P_{abs}는 정합기·코일 손실만큼 다르다"], size=12)
w_, h_ = eqn(s, "Pa", 0.7, 4.3, pt=13)
eqno(s, "(A6)", 4.3, h_)
bullets(s, 0.5, 4.85, 9.0, 0.9, ["전원별 전력 P_{a}: 위상차 φ ≠ 0이면 상호 결합으로 한쪽 전원의 전력이 음수가 될 수 있다 → 독립 전원 2대 구성에서는 φ 범위를 함께 검토 (2차)"], size=12)
key(s, "k, φ는 가열 분포의 모양을, I_{0}는 그 크기를 정한다.")
foot(s, "a = [1, k e^{jφ}]^{T}: 전류비·위상차 벡터. em_field.port_drive로 전원별 전력과 코일 전압을 계산한다.")
num(s, 19)
NOTES[19] = ("[부록 A3] 기준점 R_pl 대각 1.69/3.02 Ω, 교차 1.07 Ω. φ=90°에서 안쪽 전원 −416 W (300 W, k=1). 상세는 docs/23 4.4절.", None)

# A4 변압기 모델
s = appendix(4, "코일 간 결합", "코일 간 상호결합: 변압기 모델로 본 결합 구조")
label(s, 0.5, 1.45, 9.0, "교재 변압기 모델: 코일 1개 + 플라즈마 (2차 권선)  [1] (2.54)–(2.57)")
w_, h_ = eqn(s, "tr1", 0.7, 1.8, pt=11.5)
eqno(s, "(A7)", 1.8, h_)
w_, h_ = eqn(s, "tr2", 0.7, 2.3, pt=12.5)
eqno(s, "(A8)", 2.3, h_)
bullets(s, 0.5, 3.05, 9.0, 0.7, ["R: 코일 쪽에서 본 부하 저항, 흡수 효율 η = (R − R_{a})/R. 플라즈마 전류가 코일 자속을 일부 상쇄해 L < L_{a} (렌츠 법칙)"], size=12)
label(s, 0.5, 3.75, 9.0, "코일이 둘이면: 플라즈마 고리를 소거한 상호 임피던스 (직관용 단순화)")
w_, h_ = eqn(s, "zio", 0.7, 4.1, pt=12.5)
eqno(s, "(A9)", 4.1, h_, x=3.75)
bullets(s, 4.5, 4.2, 5.0, 1.5, [
    "두 코일은 직접 자기 결합과, 같은 플라즈마를 거친 결합으로 이어진다",
    "실제 계산은 2D 장 해에서 Z[n_{e}, T_{e}]를 직접 구한다 (부록 A3)",
], size=11.5)
key(s, "두 코일은 플라즈마를 통해서도 결합하므로, 한 코일의 전류가 다른 코일의 가열에 영향을 준다.")
foot(s, "M_{ip}, M_{op}: 각 코일과 플라즈마 고리의 상호 인덕턴스, M_{io}: 코일끼리. [1] pp.123–126, 그림 2.34–2.35.")
num(s, 20)
NOTES[20] = ("[부록 A4] 이전 판 18쪽을 같은 양식으로 정리.", None)

# A5 웨이퍼 지표
s = appendix(5, "웨이퍼 지표", "웨이퍼 지표 계산: 면적 가중 평균")
cx, cy, R0 = 2.35, 3.55, 1.85
for rr_, f_, l_ in ((15.0, "F2F4F8", "8C93A3"), (14.5, "F8E1D4", None), (12.0, "FFFFFF", None), (5.0, "DCE6F7", "3366CC")):
    d_ = 2 * R0 * rr_ / 15.0
    box(s, cx - d_ / 2, cy - d_ / 2, d_, d_, fill=f_, line=l_, lw=0.9, shape=MSO_SHAPE.OVAL, radius=None, name="고리")
tb(s, cx - 0.6, cy - 0.15, 1.2, 0.3, [{"t": "n_{c}: 0–5 cm"}], size=10.5, bold=True, color="3366CC", align="c", name="고리 이름")
tb(s, cx - 1.2, cy - R0 - 0.27, 2.4, 0.25, [{"t": "n_{edge}: 12–14.5 cm (주황 고리)"}], size=10.5, bold=True, color="B24A16", align="c", name="고리 이름")
caption(s, 0.5, cy + R0 + 0.08, 3.7, "Fig. A1. 관측면 z = z_{w} 평면도 (축척 일치)", size=10)
label(s, 4.45, 1.45, 5.0, "① 면적 가중 평균 (고리 면적 2πr dr로 가중)")
eqn(s, "ring", 4.55, 1.8, pt=11.5)
label(s, 4.45, 2.6, 5.0, "② 구간만 바꿔 적용")
eqn(s, "ring2", 4.55, 2.95, pt=10.5)
eqn(s, "rho", 4.6, 3.4, pt=15)
bullets(s, 4.45, 4.25, 5.05, 1.5, [
    "같은 폭 dr이라도 고리 면적 ∝ r: r = 13 cm 고리는 r = 3 cm 고리의 약 4.3배",
    "단순 산술평균은 바깥 고리의 큰 면적을 반영하지 못한다",
    "T_{e}는 지표에 직접 쓰지 않는다 (영향은 이미 n에 반영)",
], size=11.5)
key(s, "지표는 수렴한 밀도 분포의 웨이퍼 위 단면에서, 새 방정식 없이 면적 가중 평균으로 계산한다.")
foot(s, "r_{c} = 5 cm, (r_{1}, r_{2}) = (12, 14.5) cm, R_{w} = 15 cm, z_{w} = 1 cm. metrics.py ring_average.")
num(s, 21)
NOTES[21] = ("[부록 A5] 이전 판 19쪽을 같은 양식으로 정리.", None)

# A6 가정
s = appendix(6, "모델 가정", "모델 가정과 검증 대상")
btable(s, 0.5, 1.45, [1.25, 3.25, 2.95, 1.55], [
    ["구분", "채택한 가정", "제외 또는 추가 검증 대상", "적용 식"],
    ["기하·시간", "축대칭 (r, z), 정상상태, 단일 RF 주파수", "3D 급전부, 고조파", "전체"],
    ["입자종", "Ar, 전자와 Ar⁺, 준중성 벌크", "준안정종, 다단계 이온화, 체적 재결합", "(6)"],
    ["RF 전류", "국소 복소 전도도", "비국소 전도도, 충돌 없는 가열, 축전 결합", "(1)–(4)"],
    ["전자 에너지", "유체 에너지 보존식: 엔탈피 대류 + Fourier 열전도", "운동론적(비국소) 에너지 수송", "(7)–(8)"],
    ["전자 에너지 분포", "국소 Maxwellian, T_{e} = T_{e}(r)", "비Maxwellian 고에너지 꼬리", "(6)–(7)"],
    ["입자 수송", "냉이온 양극성 선속, 벽 Bohm 유출", "이온 관성, 상세 쉬스", "(6), 경계"],
    ["축 방향", "기본 모드, T_{e} 축 방향 균일 (부록 A2)", "고압, 높은 챔버 → (r, z) 수송으로 확인", "(6)–(7)"],
    ["중성기체", "균일 n_{g}, T_{g} = 300 K", "중성 고갈, 기체 가열", "(6)"],
], size=10.5, row_h=0.43, col_align=["l", "l", "l", "l"], header_size=11)
key(s, "가정의 타당성은 아직 검증된 결과가 아니며, 5개 항목을 COMSOL 대조로 점검한다 (13쪽).")
foot(s, "약 10 mTorr에서는 압력만으로 국소 Maxwellian·유체형 에너지 수송 근사의 타당성을 결론 낼 수 없다 → 2차 연구의 검증 항목.")
num(s, 22)
NOTES[22] = ("[부록 A6] 이전 판 20쪽 표를 본문 식 번호와 공학 용어로 고침.", None)

# A7 근거 계산
s = appendix(7, "근거 계산", "근거 계산의 지표 정의와 값 (모델 계산)")
eqn(s, "defs", 0.7, 1.45, pt=11.5)
tb(s, 0.5, 2.0, 9.0, 0.28, [{"t": "s: 면적 적분이 1이 되도록 정규화한 가열 분포, σ_{i}: 면적 가중 가열 행렬 p_{abs}(r, z)의 특이값"}], size=10, color=MUTED, name="정의 설명")
btable(s, 0.5, 2.35, [3.0, 3.0, 3.0], [
    ["비교", "조건", "값"],
    ["단일 코일 가열 모양 TV (기준 300 W, 10 mTorr)", "100 / 1000 W;  5 / 20 / 50 mTorr", "0.069 / 0.086;  0.013 / 0.015 / 0.028"],
    ["이중 코일 가열 모양 TV (기준 k = 1, φ = 0)", "k 0.5 / 2;  φ 90 / −90 / 180°;  k 2, φ 180°", "0.22 / 0.18;  0.07 / 0.09 / 0.29;  0.43"],
    ["가열 분리 η_{1}", "단일 코일 2종, 이중 코일 5종", "0.9971 – 0.9988"],
    ["수송 축소: ρ 차이 / n̄_{w} 차이", "10 / 50 mTorr (단일 코일)", "0.3% / 3.0%;  1.2% / 11%"],
    ["가열 모양 고정 시 ρ (자기일관 대비)", "100 / 1000 W;  20 mTorr (단일 코일)", "−9.4% / +10.0%;  +4.4%"],
    ["코일별 가열 겹침 O", "d = 2.0 / 3.0 / 4.5 cm", "0.19 / 0.27 / 0.39"],
    ["단일 코일 ρ의 거리 의존", "d = 2.0 / 3.0 / 4.5 cm", "1.268 / 1.295 / 1.332"],
    ["간섭 위상 ψ", "진공 (σ_{p} = 0) / 플라즈마", "0 / −10.7° ~ +10.4° (깊이 변화 ≤ 1.5°)"],
], size=10, row_h=0.37, col_align=["l", "l", "l"], header_size=10.5)
key(s, "모든 값은 같은 모델 코드와 같은 기준 조건에서 계산했다.")
foot(s, "기준: 300 W, Ar 10 mTorr, 13.56 MHz, k = 1, φ = 0, 격자 60 × 56. 코드: 저장소 sim/hybrid (팀 GitHub), 그림: presentations/src/rev1123.")
num(s, 23)
NOTES[23] = ("[부록 A7] sep.py, why_z.py, zgeom.py, nums.py, figs.py (presentations/src/rev1123/calc).", None)

# A8 구동 수단
s = appendix(8, "구동 수단 선택", "검토 사항 1: 구동 수단의 비교와 선택 (1차 결정, 11-05)")
btable(s, 0.5, 1.45, [1.3, 2.4, 2.65, 2.65], [
    ["기준", "A 수동 공진 (전원 1 + 가변 C)", "B 독립 전원 2대 (채택)", "C 자기장·페라이트 보조"],
    ["구성", "코일 2개, 한쪽에 가변 커패시터", "코일마다 RF 전원·정합기, 공통 발진기로 위상 고정", "A 또는 B에 약한 축 방향 자기장, 또는 코일 뒤 페라이트"],
    ["조작 변수", "P, C", "P_{tot}, k, φ", "+ 자석 전류"],
    ["독립성", "커패시터 하나가 n̄_{w}와 ρ를 함께 움직이고, 공진점이 부하에 따라 이동", "전력은 n̄_{w}, 전류비는 ρ를 주로 움직임", "저압에서 반경 방향 전자 수송을 줄여 분배 효과를 키움 (추정)"],
    ["n̄_{w} 유지 보상", "P와 C를 동시에 조정", "총 전력만 보정 (식 10)", "B와 같음 + 측벽 손실 변화 보정"],
    ["부작용", "공진 코일 고전압, 공진 근처 급경사", "두 정합기의 상호 영향, 위상 고정 필요, φ ≠ 0이면 전원 간 전력 교환", "ECR 면(4.84 G) 접근, 웨이퍼 위 자기장, 13.56 MHz에서 페라이트 손실"],
    ["하드웨어", "전원 1, 정합기 1, 가변 C 1", "전원 2, 정합기 2, 공통 발진기", "+ 전자석·전원, 또는 페라이트 요크"],
], size=10, row_h=0.5, col_align=["l", "l", "l", "l"], header_size=10.5,
   colors={(0, 2): NAVY}, fills={(i, 2): "EEF3FB" for i in range(1, 7)},
   row_heights=[0.34, 0.62, 0.34, 0.8, 0.5, 0.8, 0.5])
key(s, "독립성 기준으로 B를 택하고, A는 전원 1대일 때의 대안, C는 저압 운전용 보조로 둔다.")
foot(s, "팀 1차 결정 보고서 (2026-11-05) 결정 4. 페라이트: [1] 식 (2.62). 13.56 MHz의 전자 사이클로트론 공명 자기장 4.84 G.")
num(s, 24)
NOTES[24] = ("[부록 A8] 검토 사항 1. docs/05 결정 4 비교표에서 정성 항목만 옮김 (수치는 이전 모델 기준이라 제외).", None)

# 근거 노트 갱신 (읽지 않음)
NOTES[4] = (None, "과제 원문(docs/00): 제어 목표 n_c/n_edge, 검토 사항 4. 좌표 비교 수치(조건수 1.7 vs 3.9, 5 mTorr 9.5)는 docs/25 1.2절, 발표에서는 정성적으로만. "
                  "단일 코일 100/300/1000 W: ρ 1.400/1.268/1.153. T_e 중앙 3.135, 가장자리 3.277 V → sqrt 비 0.978(약 2%). 축 방향 닫힘 변경: n̄ ×1.66, ρ ×1.135.")
NOTES[5] = (None, "K_iz(3.278)/K_iz(3.096) = 1.41. T_e(r) 차이와 열전도: docs/23 남은 위험 1 (κ×3, ×10에서 형상 이득 −0.59 → −0.33, −0.13; 발표에서는 수치 제외).")
NOTES[7] = (None, "가열 모양 고정 시험(calc/fixshape.py): 100/1000 W에서 ρ 1.268 고정 (자기일관 1.400/1.153), 20 mTorr 0.997 (0.954). single_shape_tv_max 0.0857. Λ_z = L/π = 1.91 cm, Λ_r = R/2.405 = 8.73 cm, 비의 제곱 20.9. λ_ε ≈ 119/p[mTorr] cm. "
                  "축소: ρ 1.2682/1.2722, 0.681/0.702; n̄ 5.22/5.16, 11.59/10.41 ×10^16.")
NOTES[8] = (None, "why_z.py, zgeom.py: TV, 겹침 0.192/0.272/0.393, 단일 코일 ρ 1.268/1.295/1.332, η1 0.9971–0.9988. [3] Zhao 2026은 Cl2 40 mTorr (docs/13 대조).")
NOTES[13] = (None, "κ_e×3: ρ 1.268→1.465, n̄ ×1.003. 합격 기준 2·3단계는 팀 제안값(확정 필요). export.py compare 구현. "
                    "밀도 의존 과정: 모델에 없음 (n_g = p/k_BT_g 고정, 한 단계 K_iz, ν_m은 전자–중성만) → 수송 식이 N에 1차 동차.")
NOTES[14] = (None, "검토 사항 원문: docs/00. 한계: docs/23 남은 위험 1. 부작용: 부록 A3 (φ = 90°에서 한쪽 전원 음의 전력).")

# ---------------------------------------------------------------- 노트
# 대본(1–14쪽)은 같은 폴더의 script.py 하나에서 관리한다 (문서판 대본과 같은 글).
import importlib.util  # noqa: E402
import os  # noqa: E402
_sp = importlib.util.spec_from_file_location("script", os.path.join(os.path.dirname(os.path.abspath(__file__)), "script.py"))
SCRIPT = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(SCRIPT)
NOTES[1] = (None, "20분 녹화 발표 (2026-11-23 수정본). 교수님 피드백: 밀도비의 이유, 에너지 수송 용어, 앞부분 축소, "
                  "단일 코일 r 먼저, 다중 코일 z, COMSOL 검증. 예상 질문의 답을 설명 속에 넣음 (문서판 대본의 마지막 표).")
for i, sl in enumerate(prs.slides, start=1):
    if i in NOTES:
        script_text, basis = NOTES[i]
        if i in SCRIPT.S:
            script_text = SCRIPT.note_text(i)
        notes(sl, script_text, basis)

prs.core_properties.last_modified_by = "주제 3 팀"
prs.core_properties.author = "주제 3 팀"
prs.core_properties.title = "중앙·가장자리 플라즈마 밀도 독립 제어를 위한 모델링 전략"
prs.save(OUT)
print("saved", OUT, len(prs.slides))
