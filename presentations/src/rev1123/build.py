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
    ("Ⅱ", "모델링 전략", "단일 코일은 r, 이중 코일은 전자기장만 (r, z) · 각 단계의 근거", "6–8"),
    ("Ⅲ", "지배 방정식과 계산 방법", "축대칭 유도장 · 입자·전자 에너지 보존식 · 자기일관 반복", "9–11"),
    ("Ⅳ", "독립 제어 판정과 검증 계획", "제어 Jacobian과 형상 이득 · COMSOL 교차 검증", "12–13"),
    ("Ⅴ", "결론", "", "14"),
]
y = 1.35
for rn, name, desc, pg in items:
    tb(s, 0.75, y, 0.75, 0.5, [{"t": rn + "."}], size=22, bold=True, color=NAVY, name="장 번호")
    tb(s, 1.5, y + 0.02, 6.6, 0.42, [{"t": name}], size=19, bold=True, color="1A1A1A", name="장 이름")
    if desc:
        tb(s, 1.5, y + 0.45, 6.9, 0.3, [{"t": desc}], size=12.5, color=MUTED, name="장 설명")
    tb(s, 8.3, y + 0.04, 1.0, 0.4, [{"t": pg}], size=13, color=MUTED, align="r", name="쪽")
    y += 0.92
foot(s, "부록 A1–A7: 0D 균형식, r 모델 유도, 2포트 전력 조건, 코일 간 결합, 웨이퍼 지표, 모델 가정, 근거 계산의 조건 (16쪽 이후)")
num(s, 2)
NOTES[2] = ("[대본 · 0:25–0:55 / 30초]\n발표는 다섯 부분입니다. 먼저 문제와 제어 목표, 그리고 왜 밀도비를 제어 출력으로 쓰는지 말씀드립니다. "
            "이어서 교수님 피드백에 따라 단일 코일은 반지름 r만으로, 이중 코일은 전자기장만 r과 z로 푸는 단계적 모델링 전략과 그 근거를 보이고, "
            "지배 방정식, 독립 제어 판정 기준과 COMSOL 검증 계획 순서로 진행하겠습니다.",
            "20분 녹화 발표. 쪽별 시간은 각 노트 머리에 적음. 합계 20:00.")

# ================================================================ 3 문제 정의
s = new_slide("Ⅰ. 서론 (1/3)")
header(s, "문제 정의와 제어 목표")
w, h = fig(s, "fig_chamber", 0.45, 1.5, w=4.5)
caption(s, 0.45, 1.5 + h + 0.03, 4.5, "Fig. 1. 이중 코일 ICP 반단면 (축척 일치)")
btable(s, 0.5, 4.5, [1.15, 3.25], [
    ["항목", "값"],
    ["챔버", "R = 21 cm, L = 6 cm, 유전체 창 두께 1.5 cm"],
    ["코일", "안쪽 r = 7.5·8.5 cm, 바깥쪽 r = 15.25·15.75 cm"],
    ["운전 조건", "Ar 10 mTorr, 13.56 MHz, 총 전력 300 W (기준)"],
], size=10.5, row_h=0.29, col_align=["l", "l"], name="형상 표")
bullets(s, 5.2, 1.45, 4.3, 1.2, [
    ("h", "문제 정의"),
    "하나의 챔버에서 중앙부와 가장자리의 플라즈마 밀도를 독립적으로 조절하는 소스를 설계한다.",
], size=13)
bullets(s, 5.2, 2.55, 4.3, 0.95, [
    ("h", "제어 목표"),
    "웨이퍼 위 평균 밀도 n̄_{w}는 [[r:유지]]하고, 밀도비 ρ만 원하는 값으로 [[r:옮긴다]].",
], size=13)
eqn(s, "rho", 5.45, 3.6, pt=19, red=True)
eqn(s, "avg", 7.05, 3.7, pt=11)
bullets(s, 5.2, 4.48, 4.3, 1.35, [
    "목표 범위: ρ = 0.8–1.2, 이때 n̄_{w} 변화 ±5% 이내",
    "제어 입력: 총 전력 P_{tot}, 전류비 k = |I_{out}|/|I_{in}|, 위상차 φ",
], size=12.5)
key(s, "목표는 밀도의 크기(n̄_{w})가 아니라 모양(ρ)을 따로 움직이는 것이다.")
foot(s, "n_{c}: r < 5 cm, n_{edge}: 12–14.5 cm, n̄_{w}: 웨이퍼 전체(R_{w} = 15 cm)의 면적 평균, 관측 높이 z_{w} = 웨이퍼 위 1 cm (부록 A5). "
        "형상은 [3]과 같은 R, L.")
num(s, 3)
NOTES[3] = ("[대본 · 0:55–2:20 / 85초]\n저희 과제는 하나의 챔버에서 중앙부와 가장자리의 플라즈마 밀도를 독립적으로 조절하는 소스를 설계하는 것입니다. "
            "그림 1은 반지름 21 cm, 높이 6 cm인 챔버의 반단면을 축척에 맞춰 그린 것으로, 유전체 창 위에 안쪽 코일과 바깥쪽 코일이 있습니다. "
            "웨이퍼 위 1 cm 높이에서 중앙 5 cm 안쪽의 평균 밀도를 n_c, 12에서 14.5 cm 고리의 평균 밀도를 n_edge라 하고, 그 비를 밀도비 ρ로 정의합니다. "
            "제어 목표는 웨이퍼 전체의 평균 밀도 n̄_w는 유지하면서 ρ만 원하는 값으로 옮기는 것입니다. 구체적으로는 평균 밀도 변화를 5% 안에 두고 ρ를 0.8에서 1.2 사이로 맞추는 것을 목표로 잡았습니다. "
            "조작할 수 있는 입력은 총 전력, 두 코일의 전류비 k, 그리고 위상차 φ입니다. 그렇다면 왜 하필 밀도비를 제어 출력으로 쓰는지가 첫 질문입니다.",
            "형상: 하이브리드 모델 config (R 0.21, L 0.06, 창 0.015, 코일 간격 0.005 m, r_in 7.5/8.5, r_out 15.25/15.75 cm). 목표 범위: 팀 1차 결정. [3] Zhao et al. 2026과 같은 R, L.")

# ================================================================ 4 왜 밀도비인가
s = new_slide("Ⅰ. 서론 (2/3)")
header(s, "왜 밀도비 ρ를 제어 출력으로 쓰는가")
X0, XT = 0.5, 0.88
items4 = [
    ("1", "총량과 모양이 분리된다", 1.42,
     "전력은 모든 위치의 밀도를 거의 같은 배율로 바꾼다. 수준은 전력 평형(n_{0} ∝ P_{abs})이, 모양은 가열 위치가 정한다.",
     "scale", "단일 코일 100 → 1000 W: n̄_{w} 9.4배, ρ 1.40 → 1.15 (모델 계산)"),
    ("2", "측정의 공통 배율 오차가 상쇄된다", 2.8,
     "탐침 면적·보정 계수는 비에서 사라지고, 두 영역의 T_{e} 차이만 남는다 (기준점 약 2%).", "isat", None),
    ("3", "모델의 공통 오차에 덜 민감하다", 4.16,
     "축 방향 손실 처리를 바꾸면 n̄_{w}는 1.66배, ρ는 1.14배 변한다. 단, 분포 모양을 바꾸는 전자 열전도 가정은 ρ에 직접 영향 → 검증 대상 (Ⅳ)",
     None, None),
    ("4", "공정 지표와 일대일로 대응한다", 5.02,
     "n̄_{w}는 공정 속도(이온 선속), ρ는 균일도에 대응한다. 무차원이라 조건·장비 간 비교가 쉽고 ρ = 1이 균일이다.",
     None, None),
]
for n_, title, y0, body, eqname, small in items4:
    tb(s, X0, y0 - 0.02, 0.35, 0.34, [{"t": n_}], size=17, bold=True, color=NAVY, name="번호")
    tb(s, XT, y0, 4.9, 0.3, [{"t": title}], size=13.5, bold=True, color="1A1A1A", name="항목 제목")
    t = tb(s, XT, y0 + 0.29, 4.95, 0.45, [{"t": body, "line": 1.0}], size=11.5, color="222222", name="항목 본문")
    if eqname == "scale":
        eqn(s, "scale", XT, y0 + 0.75, pt=11.5)
        tb(s, XT, y0 + 1.06, 4.95, 0.22, [{"t": small}], size=10, color=MUTED, name="항목 주")
    elif eqname == "isat":
        eqn(s, "isat", XT, y0 + 0.72, pt=11)
w, h = fig(s, "fig_concept", 5.95, 1.45, w=3.55)
caption(s, 5.95, 1.45 + h + 0.02, 3.55, "Fig. 2. 크기와 모양의 분리 (개념도)", size=10.5)
tb(s, 5.95, 1.45 + h + 0.3, 3.55, 0.5, [{"t": "(a) 전력: n̄_{w}만 변화  (b) 분포: ρ만 변화", "line": 1.0}], size=10, color=MUTED,
   align="c", name="그림 설명")
key(s, "ρ는 전력이 정하는 총량과 분리된, 밀도 분포의 모양만 담는 양이다.")
foot(s, "[1] 식 (2.73) 전력 평형, 식 (5.5) 이온 포화 전류. 모델 계산: 300 W, Ar 10 mTorr, k = 1, φ = 0 (부록 A7).")
num(s, 4)
NOTES[4] = ("[대본 · 2:20–4:20 / 120초]\n밀도비를 고른 이유는 네 가지입니다. "
            "첫째, 총량과 모양이 분리됩니다. 전력을 바꾸면 모든 위치의 밀도가 거의 같은 배율로 바뀌므로, 공통 배율은 비에서 지워집니다. 교재의 전력 평형처럼 밀도 수준은 흡수 전력이 정하고, 분포의 모양은 그 전력을 어디에 넣느냐가 정합니다. "
            "실제로 저희 모델에서 단일 코일의 전력을 열 배 올리면 평균 밀도는 9.4배가 되지만 ρ는 1.40에서 1.15로 조금만 바뀝니다. 그림 2의 (a)가 이 경우이고, (b)는 평균은 같고 모양만 다른 경우입니다. 저희가 만들고 싶은 것이 바로 (b)입니다. "
            "둘째, 측정 오차가 상쇄됩니다. 탐침의 이온 포화 전류는 밀도에 탐침 면적과 보정 계수가 곱해진 값이라, 같은 방법으로 두 영역을 재서 나누면 이 공통 배율이 사라지고 두 영역의 전자온도 차이만 남습니다. 기준점에서는 약 2%입니다. "
            "셋째, 모델 오차에도 덜 민감합니다. 벽 손실을 다루는 가정을 바꾸면 평균 밀도는 1.66배 달라지지만 ρ는 1.14배로 훨씬 작게 바뀝니다. 다만 전자 열전도처럼 분포의 모양을 바꾸는 가정은 ρ에 직접 영향을 주므로 뒤에서 검증 대상으로 다룹니다. "
            "넷째, 평균 밀도는 공정 속도, ρ는 균일도에 그대로 대응하고, 무차원이라 조건이 달라도 비교할 수 있습니다.",
            "단일 코일(직렬) 100/300/1000 W: n̄ 1.77/5.22/16.7×10^16, ρ 1.400/1.268/1.153. T_e 중앙 3.135, 가장자리 3.277 V → sqrt 비 0.978. "
            "축 방향 닫힘 robin→h_factor: n̄ ×1.66, ρ ×1.135. κ_e×3: n̄ ×1.003, ρ 1.268→1.465. Fig. 2는 개념도(해석 함수).")

# ================================================================ 5 단일 코일의 한계
s = new_slide("Ⅰ. 서론 (3/3)")
header(s, "단일 코일의 한계와 공간 분포 모델의 필요성")
btable(s, 0.5, 1.45, [1.85, 1.3, 3.1, 2.75], [
    ["모델", "조절 입력", "계산되는 것", "ρ에 대한 결론"],
    ["0D, 단일 코일", "P_{tot}", "T_{e} (a), n_{0} ∝ P_{abs} (b)", "공간 정보가 없어 ρ를 정의할 수 없다"],
    ["0D, 이중 코일", "P_{tot}, k, φ", "세 입력이 P_{abs} 하나로 합쳐짐 (부록 A1)", "k, φ의 효과를 구분할 수 없다"],
    ["공간 모델, T_{e} 균일", "P_{tot}, k, φ", "확산 기본 모드 (c): 모양이 R, L로 고정", "ρ가 k, φ와 무관하다"],
    ["공간 모델, T_{e}(r)", "P_{tot}, k, φ", "가열 → T_{e}(r) → 이온화 → n(r)", "k, φ가 ρ를 바꿀 수 있다 → 채택"],
], size=11.5, row_h=0.34, col_align=["l", "l", "l", "l"], bold_rows=(4,), colors={(4, None): NAVY})
yE = 3.38
w1, h1 = eqn(s, "te", 0.6, yE, pt=13)
w2, h2 = eqn(s, "n0", 0.6 + w1 + 0.45, yE + 0.02, pt=13)
w3, h3 = eqn(s, "mode", 0.6 + w1 + w2 + 0.9, yE + 0.02, pt=12)
for x_, w_, t_ in ((0.6, w1, "(a) 입자 균형 [1] (2.70)"), (0.6 + w1 + 0.45, w2, "(b) 전력 균형 (2.73)"),
                   (0.6 + w1 + w2 + 0.9, w3, "(c) T_{e} 균일일 때 (1.76)–(1.83)")):
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
tb(s, xs + 2 * (bw + gap) - 0.4, yc + 0.68, 3.4, 0.5,
   [{"t": "T_{e} 6% 차이 → 이온화 계수 K_{iz} 41% 차이", "line": 1.0},
    {"t": "(기준점 3.10–3.28 V, 모델 계산)", "line": 1.0, "size": 9.5, "color": MUTED}],
   size=11, bold=True, color="B24A16", align="c", name="민감도 설명")
key(s, "ρ를 다루려면 위치마다 다른 가열과 전자온도를 푸는 공간 모델이 필요하다.")
foot(s, "[1] §2.4 식 (2.70), (2.73), §1.10 식 (1.76)–(1.83). 0D 식과 이중 코일 흡수 전력의 세부는 부록 A1.")
num(s, 5)
NOTES[5] = ("[대본 · 4:20–5:50 / 90초]\n그렇다면 단일 코일로는 왜 안 되는지, 그리고 어떤 모델이 필요한지를 한 장으로 정리했습니다. "
            "가장 단순한 0D 모델에서는 입자 균형이 전자온도를, 전력 균형이 밀도를 정합니다. 출력이 밀도 하나뿐이라 공간 분포가 없고, 따라서 ρ를 정의할 수조차 없습니다. "
            "코일을 둘로 나눠 입력을 셋으로 늘려도, 0D에서는 세 입력이 흡수 전력 하나로 합쳐져 k와 φ의 효과를 구분할 수 없습니다. "
            "공간 분포를 넣더라도 전자온도를 균일하다고 두면, 밀도 분포는 용기 크기만으로 정해지는 확산 기본 모드가 되어 코일을 어떻게 구동해도 ρ가 바뀌지 않습니다. "
            "결국 아래 사슬처럼, 코일 전류가 가열 분포를 바꾸고, 가열 분포가 전자온도 분포를 바꾸고, 그것이 이온화와 밀도 분포를 거쳐 ρ까지 이어져야 합니다. "
            "핵심은 전자온도입니다. 기준점에서 전자온도의 반지름 방향 차이는 6% 정도지만, 이온화 계수는 전자온도에 지수적으로 민감해서 41% 차이가 납니다. "
            "그래서 위치마다 다른 가열과 전자온도를 푸는 공간 모델이 필요합니다. 다음은 이 모델을 어떻게 세웠는지입니다.",
            "K_iz(3.278)/K_iz(3.096) = 1.41 (physics.K_iz). 0D 세부는 부록 A1. 교재 식 번호는 docs/11 교재 대응표 기준.")

# ================================================================ 6 단계적 모델
s = new_slide("Ⅱ. 모델링 전략 (1/3)")
header(s, "단계적 모델: 단일 코일은 r, 이중 코일은 전자기장만 (r, z)")
for px, ttl, col, rows_, fb in (
        (0.5, "1단계 · 단일 코일: 모든 식을 r로", NAVY,
         [("가열 모양 S(r)\n모양 고정, 크기 ∝ P_{tot}", "F2F4F8", "C9CED8"), ("수송 (r)\nn(r), T_{e}(r)", "FBEDE4", "D9622B"),
          ("n̄_{w}, ρ", "ECECF7", NAVY)],
         ["입력은 P_{tot} 하나: 가열의 크기만 바뀐다", "비선형 미지수 2N_{r} = 120개", "확인: 가열 모양 → T_{e}(r) → ρ 경로, T_{e} 균일 극한의 해석해"]),
        (5.15, "2단계 · 이중 코일: 전자기장만 (r, z)", "7A3FA0",
         [("전자기장 (r, z)\n코일별 A_{in}, A_{out}", "EEF3FB", "3366CC"), ("가열 S(r; k, φ)\n= ∫p_{abs} dz", "F2F4F8", "C9CED8"),
          ("수송 (r)\n1단계와 같음", "FBEDE4", "D9622B")],
         ["k, φ가 가열 모양 자체를 바꾼다", "전자기장(미지수 3,360개)은 선형: 행렬 분해 한 번으로 두 코일의 해", "수송은 r 그대로 (2,880 → 120개)"])):
    box(s, px, 1.47, 4.35, 2.75, fill="FFFFFF", line="C9CED8", lw=0.9, radius=None, name="단계 틀")
    tb(s, px + 0.15, 1.55, 4.1, 0.32, [{"t": ttl}], size=13.5, bold=True, color=col, name="단계 제목")
    bw_, gap_ = 1.17, 0.27
    for i, (t_, f_, l_) in enumerate(rows_):
        flow_box(s, px + 0.15 + i * (bw_ + gap_), 1.98, bw_, 0.72, t_, fill=f_, line=l_, size=10.5)
        if i < len(rows_) - 1:
            arrow(s, px + 0.15 + i * (bw_ + gap_) + bw_ + 0.02, 2.34, px + 0.15 + (i + 1) * (bw_ + gap_) - 0.02, 2.34)
    if px > 1:
        seg(s, px + 0.15 + 2 * (bw_ + gap_) + bw_ / 2, 2.72, px + 0.15 + 2 * (bw_ + gap_) + bw_ / 2, 2.86, color="D9622B", w=1.0, dash=True)
        seg(s, px + 0.15 + 2 * (bw_ + gap_) + bw_ / 2, 2.86, px + 0.15 + bw_ / 2, 2.86, color="D9622B", w=1.0, dash=True)
        arrow(s, px + 0.15 + bw_ / 2, 2.86, px + 0.15 + bw_ / 2, 2.73, color="D9622B", w=1.0)
        tb(s, px + 1.3, 2.9, 2.3, 0.2, [{"t": "σ_{p}(n_{e}, T_{e}) 갱신"}], size=9, color="B24A16", align="c", name="되먹임")
    bullets(s, px + 0.12, 3.18, 4.15, 1.0, fb, size=12, after=3)
btable(s, 0.5, 4.45, [3.6, 1.35, 1.55, 2.5], [
    ["계산 구성", "수송 미지수", "운전점 1개", "웨이퍼 위 ρ (차이)"],
    ["전자기장 (r, z) + 수송 r  [채택]", "120", "0.15 s", "1.268 (0.3%)"],
    ["전자기장 (r, z) + 수송 (r, z)", "2,880", "0.38 s", "1.272 (기준)"],
], size=12, row_h=0.36, col_align=["l", "r", "r", "r"], bold_rows=(1,), colors={(1, None): NAVY})
key(s, "z는 꼭 필요한 곳(이중 코일의 전자기장)에만 쓰고, 비선형 수송은 r로 푼다.")
foot(s, "격자 N_{r} 60 × N_{z} 56 (플라즈마 24층). 계산 시간은 전자기장 포함 운전점 1개, Ar 10 mTorr, 300 W (모델 계산).")
num(s, 6)
NOTES[6] = ("[대본 · 5:50–7:20 / 90초]\n여기서부터가 교수님 피드백을 반영한 모델링 전략입니다. 피드백은 두 가지였습니다. 반지름 r만 변수로 해서 단일 코일부터 풀 것, 그리고 다중 코일이면 z축을 고려할 것. "
            "그래서 모델을 두 단계로 나눴습니다. 1단계 단일 코일은 모든 식을 r로 풉니다. 가열 분포의 모양은 고정되고 크기만 전력에 따라 바뀌므로, 미지수는 반지름별 밀도와 전자온도 120개뿐입니다. "
            "이 단계에서 가열 모양이 전자온도 분포를 거쳐 ρ를 정하는 경로를 확인하고, 해석해와 대조합니다. "
            "2단계 이중 코일에서는 k와 φ가 가열의 모양 자체를 바꿉니다. 이 모양을 구하려면 각 코일의 전자기장을 r과 z로 풀어야 합니다. 다만 전자기장은 선형 문제라 행렬을 한 번 분해하면 두 코일의 해를 모두 얻고, 비선형인 수송은 1단계와 같은 r 모델을 그대로 씁니다. "
            "아래 표처럼, 수송까지 r과 z로 풀면 미지수가 2,880개로 늘고 계산 시간이 두 배 반이 되지만, ρ는 0.3%밖에 차이 나지 않습니다. 다음 두 장에서 각 단계의 근거를 보이겠습니다.",
            "fig_log transport_pairs 10 mTorr: ρ 1.2682 (r) / 1.2722 (r,z), 시간 0.154 / 0.379 s (전자기장 포함). 미지수: 수송 2×60, 2×60×24. 전자기장 60×56.")

# ================================================================ 7 1단계 근거
s = new_slide("Ⅱ. 모델링 전략 (2/3)")
header(s, "1단계 근거: 단일 코일은 r만으로 충분하다")
bullets(s, 0.5, 1.45, 9.0, 0.6, [
    "가열 모양이 고정된다: 100–1000 W, 5–50 mTorr에서 S(r) 모양 차이 [[r:9% 이하]] (Fig. 3a) → 바뀌는 것은 크기뿐",
    "축 방향 구조가 먼저 정착한다: 축 방향 확산 길이가 반경보다 훨씬 짧아 기본 모드로 두고 z로 적분한다",
], size=12.5, after=3)
eqn(s, "axial", 0.8, 2.06, pt=12)
bullets(s, 0.5, 2.55, 9.0, 0.62, [
    "전자온도는 축 방향으로 거의 균일하다: 에너지 완화 길이 λ_{ε} ≈ 12 cm > L = 6 cm (Ar 10 mTorr) [2, 4]",
    "결과: r 모델과 (r, z) 모델의 ρ 차이 [[r:0.3%]] (10 mTorr), 3.0% (50 mTorr) (Fig. 3b)",
], size=12.5, after=3)
w, h = fig(s, "fig_single", 0.75, 3.2, w=8.5)
caption(s, 0.5, 3.2 + h + 0.02, 9.0, "Fig. 3. (a) 단일 코일 가열 모양 S(r)의 운전 조건 의존성, (b) 웨이퍼 위 밀도: r 모델(실선)과 (r, z) 모델(점선)")
key(s, "단일 코일은 가열 모양이 고정되고 축 방향 구조가 빨리 정착하므로, 미지수를 n(r), T_{e}(r)로 줄일 수 있다.")
foot(s, "모양 차이 = ½∫|s_{1} − s_{2}| dA (s: 면적 적분이 1이 되게 정규화한 S(r)). 고압일수록 축소 오차가 커진다 (50 mTorr n̄_{w} 11%). "
        "유도: 부록 A2, 조건·값: 부록 A7.")
num(s, 7)
NOTES[7] = ("[대본 · 7:20–9:00 / 100초]\n먼저 단일 코일을 r만으로 풀어도 되는 근거입니다. 세 가지입니다. "
            "첫째, 가열의 모양이 고정됩니다. 그림 3의 (a)는 전력을 100에서 1000 W로, 압력을 5에서 50 mTorr로 바꾸면서 z로 적분한 가열 분포 S(r)의 모양을 겹쳐 그린 것입니다. 모양 차이는 9% 이하이고, 바뀌는 것은 거의 크기뿐입니다. "
            "둘째, 축 방향 구조가 먼저 정착합니다. 축 방향 확산 길이는 L/π, 약 1.9 cm로 반지름 21 cm보다 훨씬 짧습니다. 그래서 z 방향 분포는 기본 모드 코사인 모양으로 빨리 자리를 잡고, 이 모양을 가정해 z로 적분하면 r만의 식이 됩니다. "
            "셋째, 에너지 완화 길이가 약 12 cm로 챔버 높이 6 cm보다 길어서, 전자온도는 높이 방향으로 거의 같다고 볼 수 있습니다. "
            "실제로 같은 식을 r과 z로 모두 푼 결과와 비교하면, 그림 3의 (b)처럼 10 mTorr에서 웨이퍼 위 밀도 분포가 거의 겹치고 ρ 차이는 0.3%입니다. 50 mTorr에서는 축소 오차가 커져 ρ 3%, 평균 밀도 11%까지 벌어지므로, 고압에서는 r, z 수송으로 확인이 필요합니다.",
            "fig_log single_shape_tv_max 0.0857 (1000 W), 100 W 0.069, 5/20/50 mTorr 0.013/0.015/0.028. 축소: ρ 1.2682/1.2722, 0.681/0.702; n̄ 5.22/5.16, 11.59/10.41 ×10^16. "
            "λ_ε ≈ 119/p[mTorr] cm (팀 1차 정리, KC20 비교)")

# ================================================================ 8 2단계 근거
s = new_slide("Ⅱ. 모델링 전략 (3/3)")
header(s, "2단계 근거: 이중 코일은 전자기장을 (r, z)로 풀어야 한다")
bullets(s, 0.5, 1.45, 9.0, 1.3, [
    "가열 모양 자체가 제어 대상이다: k = 0.5–2, φ = 0–180°에서 S(r) 모양 차이 [[r:7–43%]] (단일 코일 ≤ 9%)",
    "그 모양은 각 코일의 장이 코일 면에서 플라즈마까지 z 방향으로 퍼지는 정도가 정한다 (Fig. 4a)",
    "코일–플라즈마 거리 d = 2.0 → 4.5 cm: 두 코일 가열의 겹침 [[r:0.19 → 0.39]] (Fig. 4b), 단일 코일 ρ는 5%만 변화",
    "깊이 방향은 분리된다: p_{abs}(r, z) ≈ S(r)·w(z) (첫 특이값 비중 ≥ 99.7%) → 수송은 r 유지",
], size=12.5, after=3)
w, h = fig(s, "fig_dual", 0.7, 2.9, w=8.6)
caption(s, 0.5, 2.9 + h + 0.03, 9.0, "Fig. 4. (a) 코일별 1 A 장의 (r, z) 분포, (b) 코일–플라즈마 거리 d에 따른 코일별 가열 모양 (z 적분)")
key(s, "z가 필요한 것은 두 코일 장의 겹침을 계산하는 전자기장 단계이며, 수송은 r로 충분하다.")
foot(s, "겹침 O = ∫min(s_{in}, s_{out}) dA (0: 분리, 1: 같음). 모델 계산: 300 W, Ar 10 mTorr, d = 창 1.5 cm + 코일 간격. 정의와 전체 값: 부록 A7.")
num(s, 8)
NOTES[8] = ("[대본 · 9:00–10:50 / 110초]\n다음은 이중 코일에서 z가 필요한 이유입니다. "
            "이중 코일에서는 가열의 모양 자체가 제어 대상입니다. 전류비를 0.5에서 2로, 위상차를 0에서 180도로 바꾸면 가열 분포의 모양이 7%에서 최대 43%까지 바뀝니다. "
            "그런데 이 모양은 각 코일의 장이 코일 면에서 출발해 유전체 창을 지나 플라즈마까지 z 방향으로 얼마나 퍼지는지가 정합니다. 그림 4의 (a)가 안쪽과 바깥쪽 코일에 각각 1 A를 흘렸을 때의 장을 r, z 단면에 그린 것입니다. 코일에서 멀어질수록 장이 옆으로 퍼지고, 두 코일의 장이 겹치는 영역이 생깁니다. "
            "이 퍼짐을 정하는 것이 코일과 플라즈마 사이 거리 d입니다. 그림 4의 (b)처럼 d를 2 cm에서 4.5 cm로 늘리면 두 코일 가열의 겹침이 0.19에서 0.39로 두 배가 되고, 안쪽 코일이 가장자리에 주는 몫도 6%에서 12%로 늘어납니다. 두 코일이 서로 닮아질수록 따로 제어하기 어려워지는 것입니다. 반면 단일 코일은 같은 변화에 ρ가 5%만 바뀝니다. "
            "즉 z는 두 코일 장의 겹침을 계산하는 전자기장 단계에 꼭 필요합니다. 반면 깊이 방향의 분포는 가열 분포의 첫 특이값이 99.7% 이상을 차지할 만큼 분리가 잘 되어, z로 적분한 S(r)만 수송에 넘겨도 됩니다. 그래서 수송은 1단계와 같은 r 모델을 씁니다.",
            "why_z.py: 이중 코일 TV (기준 k=1 φ=0) k0.5 0.217, k2 0.178, φ90 0.072, φ−90 0.091, φ180 0.287, k2 φ180 0.434. "
            "겹침 d 2.0/3.0/4.5: 0.192/0.272/0.393, 안쪽 코일 가장자리 몫 0.061/0.084/0.116. 단일 코일 ρ 1.268/1.295/1.332. η1 0.9971–0.9988. "
            "참고: ψ(r,z)는 r에 따라 −10.7~+10.4°, 깊이에 따라서는 1.5° 이하로 변함 → z가 필요한 이유는 ψ의 깊이 변화가 아니라 장의 퍼짐(겹침).")

# ================================================================ 9 전자기장
s = new_slide("Ⅲ. 지배 방정식과 계산 방법 (1/3)")
header(s, "전자기장: 축대칭 유도장과 흡수 전력 (r, z)")
rows9 = [
    ("A", 11.5, 1.48, "(1)", "축대칭 → A_{θ} 한 성분. 축·금속 벽 A_{θ} = 0, 변위 전류 무시 (λ_{0} ≈ 22 m)"),
    ("sigma", 12.5, 2.2, "(2)", "국소 복소 전도도: n_{e}, T_{e}가 전자기장에 들어가는 자리"),
    ("super", 12.5, 2.98, "(3)", "σ_{p} 고정 시 선형 → 단위 전류 해 2개로 모든 (k, φ)"),
    ("pabs", 12, 3.55, "(4)", "파랑: 안쪽 코일, 주황: 바깥쪽 코일, 남색: 간섭항. ψ = arg(A_{out}/A_{in})"),
    ("S_I0", 12, 4.2, "(5)", "수송으로 넘기는 값 S(r). 전류 진폭 I_{0}는 포트 전력 조건 (부록 A3)"),
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
        "ψ는 플라즈마의 유도 전류가 만드는 위상차로, 진공(σ_{p} = 0)에서는 0 (모델에서 확인).")
num(s, 9)
NOTES[9] = ("[대본 · 10:50–12:30 / 100초]\n이제 지배 방정식입니다. 먼저 전자기장입니다. "
            "챔버와 코일이 축대칭이고 코일 전류가 원주 방향으로만 흐르므로, 벡터 퍼텐셜의 방위각 성분 하나만 풀면 됩니다. 식 (1)이 r과 z에 대한 유도장 방정식이고, 플라즈마는 식 (2)의 국소 복소 전도도로 들어갑니다. 밀도와 전자온도가 전자기장에 들어가는 자리가 바로 이 전도도입니다. "
            "전도도를 고정하면 식이 전류에 선형이므로, 안쪽과 바깥쪽 코일에 각각 1 A를 흘린 해 두 개만 구해 두면 식 (3)처럼 어떤 전류비와 위상차든 중첩으로 만들 수 있습니다. "
            "흡수 전력 밀도는 식 (4)입니다. 파란 항은 안쪽 코일, 주황 항은 바깥쪽 코일이 혼자 주는 몫이고, 남색 항이 두 코일의 간섭입니다. k는 바깥쪽 항과 간섭항의 크기를, φ는 간섭항의 부호와 크기를 바꿉니다. "
            "마지막으로 식 (5)처럼 흡수 전력 밀도를 z로 적분한 S(r)을 수송 단계로 넘기고, 전류의 절대 크기 I_0는 공급 전력 조건으로 정합니다.",
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
    ["①", "전자 에너지 선속의 발산", "q_{r} = 엔탈피 대류 선속 (5/2)eT_{e}Γ_{r} + Fourier 열전도 선속 −κ_{e}dT_{e}/dr (식 8)"],
    ["②", "옴 가열", "주기 평균 흡수 전력 밀도의 z 적분 S = ∫p_{abs} dz (식 5)"],
    ["③", "양극성 전기장에 대한 일", "J_{r} = −eΓ_{r}: 전자가 양극성 전위를 거슬러 벽으로 갈 때 잃는 에너지 (보통 음수)"],
    ["④", "충돌 에너지 손실", "C = n_{g}[K_{iz}ε_{iz} + K_{ex}ε_{ex} + K_{el}(3m_{e}/M)T_{e}]: 이온화 15.76 eV, 여기 12.14 eV, 탄성"],
    ["⑤", "축 방향 벽 에너지 손실", "쉬스를 지나 나가는 전자–이온 쌍마다 ε_{w}T_{e} ≈ (2 + 5.2)T_{e} [1] (2.65)"],
], size=10.5, row_h=0.265, col_align=["c", "l", "l"], header_size=11)
key(s, "전자 에너지 보존식은 옴 가열과 네 가지 에너지 이동·손실의 균형이며, 전자온도 분포 T_{e}(r)를 정한다.")
foot(s, "경계: r = 0 대칭 (Γ_{r} = q_{r} = 0), r = R Bohm 유출 Γ_{r} = N_{w}u_{B}, q_{r} = eΓ_{r}(2T_{e} + V_{s}). 국소 Maxwellian 분포로 K_{j} = K_{j}(T_{e}) [2]. "
        "ν_{L}: 축 방향 기본 모드의 벽 손실 주파수 (부록 A2). [1] §1.10 (1.67)–(1.72), §2.4 (2.63)–(2.65).", h=0.4)
num(s, 10)
NOTES[10] = ("[대본 · 12:30–14:40 / 130초]\n다음은 수송입니다. 1단계와 2단계가 공통으로 쓰는 반지름 방향 식이며, 앞에서 말씀드린 기본 모드를 가정해 z로 적분한 정상상태 식입니다. "
             "식 (6)은 입자 보존입니다. 반지름 방향 양극성 선속의 발산이 이온화 생성에서 위아래 벽 손실을 뺀 것과 같습니다. 선속에는 밀도와 전자온도의 곱의 기울기가 들어가므로, 밀도 구배뿐 아니라 전자온도 구배도 입자를 움직입니다. "
             "식 (7)이 전자 에너지 보존식입니다. 피드백에 따라 각 항을 정확한 용어로 정리했습니다. "
             "①은 전자 에너지 선속의 발산입니다. 선속 q는 식 (8)처럼 입자의 흐름이 실어 나르는 엔탈피 대류 선속과, 온도 구배에 비례하는 Fourier 열전도 선속의 합입니다. 이전 자료에서 '에너지 수송'이라고 뭉뚱그려 쓴 부분이 바로 이 항입니다. "
             "②는 전자기장 단계에서 받은 옴 가열입니다. ③은 양극성 전기장에 대한 일로, 전자가 양극성 전위를 거슬러 벽 쪽으로 이동하면서 잃는 에너지이며 보통 음수입니다. "
             "④는 충돌 에너지 손실로, 이온화와 여기의 비탄성 손실과 탄성 충돌의 에너지 전달을 합한 것입니다. ⑤는 위아래 벽으로 쉬스를 지나 나가는 전자–이온 쌍이 가져가는 에너지로, 교재의 2T_e 더하기 5.2T_e와 같습니다. "
             "이 다섯 항의 균형이 전자온도 분포를 정하고, 전자온도가 다시 식 (6)의 이온화를 통해 밀도 분포를 정합니다.",
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
    "유한체적: 셀마다 입자·에너지 수지 → 전체 보존이 계산 오차 없이 성립",
    ("h", "풀이", 4),
    "미지수 [ln n, T_{e}]: 밀도가 항상 양수",
    "이웃 셀끼리만 결합 → 잔차 6번으로 야코비안",
    ("h", "수렴 판정", 4),
    "갱신량, 결합 잔차, 입자·에너지 수지 세 가지가 모두 작을 때",
    ("h", "검산 (모델 계산)", 4),
    "포인팅 정리 3 × 10^{−16}, 입자 수지 10^{−14}, 에너지 수지 5 × 10^{−10}",
    "T_{e} 균일 극한의 해석해(J_{0}) 대비 0.01%",
    "운전점당 0.15 s, 바깥 반복 5–10회",
], size=11.5, after=2)
key(s, "전자기장과 수송을 번갈아 풀어, n_{e}·T_{e}와 가열 분포가 서로 맞을 때까지 반복한다.")
foot(s, "수치 수렴은 채택한 식을 정확히 풀었다는 뜻이며, 모델 가정의 타당성은 Ⅳ의 교차 검증으로 확인한다.")
num(s, 11)
NOTES[11] = ("[대본 · 14:40–16:00 / 80초]\n두 단계를 어떻게 함께 푸는지입니다. 운전 조건을 정하고 0D 균형으로 초기값을 깐 뒤, 현재의 밀도와 전자온도로 전도도를 구하고, r–z 전자기장을 풀어 가열 분포를 얻습니다. "
             "그 가열을 넣어 r 수송을 Newton 법으로 풀면 새 밀도와 전자온도가 나오는데, 이것이 다시 전도도를 바꾸므로 수렴할 때까지 반복합니다. 보통 5에서 10번이면 수렴합니다. "
             "공간은 셀마다 입자와 에너지의 수지를 세우는 유한체적법으로 나눠서, 전체의 보존이 계산 오차 없이 성립합니다. 수렴 판정은 갱신량, 결합 잔차, 보존 오차 세 가지를 함께 봅니다. "
             "검산으로 포인팅 정리와 보존 오차, 그리고 전자온도가 균일한 극한에서의 해석해를 확인했습니다. 다만 이것은 식을 정확히 풀었다는 뜻이지, 식 자체가 실제 챔버와 맞는다는 뜻은 아닙니다. 그 확인이 다음 장의 검증 계획입니다.",
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
arrow(s, pk[0], pk[1], OX - 0.02, pk[1], color="3B4658", w=1.1, dash=True)
arrow(s, OX + 0.05, OY, OX + 0.05, pk[1], color=RED, w=2.25)
tb(s, OX + 0.12, OY + 0.75, 1.95, 0.5, [{"t": "g_{k}Δln k", "bold": True, "color": RED}, {"t": "평균 유지, ρ만 변화", "size": 9.5, "color": RED}],
   size=11, name="벡터 이름")
tb(s, 6.55, pk[1] + 0.02, 1.2, 0.25, [{"t": "전력 보정 (10)"}], size=9, color="3B4658", align="c", name="벡터 이름")
caption(s, 5.85, 4.42, 3.65, "Fig. 5. 판정의 기하적 의미 (개념도)", size=10)
btable(s, 0.5, 4.88, [1.3, 2.75, 4.95], [
    ["판정 항목", "기준", "의미"],
    ["계수", "rank J = 2", "두 출력을 다른 방향으로 움직일 수 있다 (단일 코일: J는 2×1, rank 1)"],
    ["형상 이득", "g_{k} ≠ 0, 필요한 Δln k가 구동 범위 안", "평균을 유지하며 ρ를 목표 범위로 옮길 수 있다 (식 12)"],
], size=10.5, row_h=0.3, col_align=["l", "l", "l"])
key(s, "평균을 맞춘 뒤에도 전류비가 밀도비를 바꾸면(g_{k} ≠ 0), 형상만 바꾸는 독립 제어가 가능하다.")
foot(s, "정적 국소 감도 (시간 응답 제외). 조건수 κ(J)는 측정·모델 오차가 보정량에서 커지는 배율. J, g_{k}의 값과 도달 가능한 ρ 범위는 2차 발표에서 제시한다.")
num(s, 12)
NOTES[12] = ("[대본 · 16:00–17:40 / 100초]\n모델을 풀 수 있게 되면, 독립 제어가 가능한지를 어떻게 판정할지가 남습니다. "
             "식 (9)처럼 세 입력의 로그 변화에 대한 평균 밀도와 밀도비의 로그 변화를 2×3 행렬로 묶은 것이 제어 Jacobian입니다. 수렴한 해들 사이의 중앙 차분으로 구합니다. "
             "독립 제어의 뜻은 평균은 그대로 두고 ρ만 바꾸는 것이므로, 식 (10)처럼 전류비를 바꿀 때 평균이 변하지 않도록 전력을 함께 보정하는 조건을 겁니다. 이 조건에서 남는 ρ의 변화율이 식 (11)의 평균 유지 형상 이득 g_k입니다. "
             "그림 5가 그 기하적 의미입니다. 전력은 주로 가로 방향, 즉 평균만 움직이고, 전류비는 주로 세로 방향으로 ρ를 움직이지만 평균도 조금 바꿉니다. 그 평균 변화를 전력으로 되돌리면 빨간 화살표처럼 ρ만 바뀌는 방향이 남습니다. "
             "판정 기준은 두 가지입니다. Jacobian의 계수가 2여서 두 출력을 다른 방향으로 움직일 수 있어야 하고, g_k가 0이 아니면서 목표까지 필요한 전류비 변화가 구동 범위 안에 있어야 합니다. 예를 들어 ρ를 1.2에서 0.8로 옮기려면 식 (12)만큼 전류비를 바꿔야 합니다. "
             "단일 코일은 입력이 하나라 행렬이 2×1이고 계수가 1이므로, 이 기준으로 독립 제어가 불가능함이 바로 나옵니다.",
             "control.py control_jacobian (rel_P 0.02, d_k 0.02, d_phi 2°). 그림 5는 개념도(축척 임의, 방향만 의미). 값은 2차 발표로 미룸(사용자 결정 2026-11-23).")

# ================================================================ 13 검증 계획
s = new_slide("Ⅳ. 독립 제어 판정과 검증 계획 (2/2)")
header(s, "검증 계획: COMSOL 교차 검증과 모델 가정 점검")
label(s, 0.5, 1.42, 4.3, "단계별 교차 검증 (COMSOL 2D 축대칭)", size=12.5)
steps13 = [("1", "전자기장 단독 비교", "같은 σ_{p} 분포에서 A_{θ}, p_{abs}(r, z), S(r), 코일 임피던스 (선형 문제, 차이 1% 이하 목표)"),
           ("2", "단일 코일 자기일관 해", "n(r, z_{w}), T_{e}(r), n̄_{w}, ρ (300 W, Ar 10 mTorr)"),
           ("3", "이중 코일 k, φ 변화", "S(r)와 ρ 변화의 방향·크기, J와 g_{k}"),
           ("4", "측정 대조 (가능 시)", "탐침으로 n_{c}, n_{edge} [5]")]
yy = 1.78
for n_, t_, d_ in steps13:
    tb(s, 0.5, yy, 0.32, 0.32, [{"t": n_}], size=15, bold=True, color=NAVY, name="번호")
    tb(s, 0.85, yy + 0.01, 3.95, 0.28, [{"t": t_}], size=12, bold=True, color="1A1A1A", name="단계 제목")
    tb(s, 0.85, yy + 0.29, 3.95, 0.55, [{"t": d_, "line": 1.0}], size=10.5, color="3B4658", name="단계 설명")
    yy += 0.9
label(s, 5.05, 1.42, 4.45, "점검할 모델 가정", size=12.5)
btable(s, 5.05, 1.78, [1.42, 1.58, 1.45], [
    ["가정", "영향 (모델 계산)", "점검 방법"],
    ["국소 전자 열전도 κ_{e}", "κ_{e} × 3 → ρ +16%, n̄_{w} 0.3%", "COMSOL 전자 에너지식, 비국소 효과 [4]"],
    ["축 방향 손실 닫힘", "n̄_{w} 1.66배, ρ 1.14배", "(r, z) 수송, COMSOL"],
    ["국소 Maxwellian EEDF", "K_{iz}(T_{e})의 지수 민감도", "문헌 EEDF [4], 탐침"],
    ["충돌 없는 가열, 축전 결합", "저압 효율, 코일 전압 1–3 kV", "COMSOL 전자기 해석"],
], size=10, row_h=0.62, col_align=["l", "l", "l"], header_size=10.5, row_heights=[0.32, 0.72, 0.62, 0.62, 0.62])
key(s, "COMSOL로 전자기장 → 단일 코일 → 이중 코일 순서로 대조해, ρ를 좌우하는 가정을 가린다.")
foot(s, "연구실 COMSOL 라이선스 사용. 비교용 반경 분포 입출력(CSV)은 모델 코드에 구현됨. 영향 값: 300 W, Ar 10 mTorr, k = 1, φ = 0.")
num(s, 13)
NOTES[13] = ("[대본 · 17:40–19:05 / 85초]\n지금까지의 계산은 세운 식을 정확히 풀었다는 것까지만 보장합니다. 그래서 교수님께서 추천해 주신 COMSOL 시뮬레이션으로 단계별 교차 검증을 하겠습니다. "
             "먼저 같은 전도도 분포를 넣고 전자기장만 비교합니다. 선형 문제라 1% 이하로 맞아야 합니다. 다음으로 단일 코일의 자기일관 해, 그다음 이중 코일에서 k와 φ를 바꿨을 때의 변화를 비교하고, 가능하면 탐침 측정과도 대조합니다. "
             "오른쪽은 점검할 가정입니다. 가장 중요한 것은 전자 열전도입니다. 열전도도를 세 배로 하면 평균 밀도는 거의 그대로인데 ρ는 16% 바뀝니다. ρ가 전자온도 분포에 의해 정해지기 때문입니다. "
             "축 방향 손실 처리는 평균 밀도를 크게 바꾸지만 ρ에는 덜 영향을 주고, 국소 맥스웰 분포 가정과 충돌 없는 가열, 축전 결합도 함께 확인하겠습니다.",
             "κ_e×3: ρ 1.268→1.465, n̄ ×1.003. 닫힘 변경: n̄ ×1.66, ρ ×1.135. 코일 전압: port_drive 0.5–2.9 kV (300 W). export.py compare 구현.")

# ================================================================ 14 결론
s = new_slide("Ⅴ. 결론")
paras = [
    "제어 목표를 [[r:평균 밀도 n̄_{w} 유지 + 밀도비 ρ 조절]]로 정의했다. ρ는 전력이 정하는 총량과 분리된 분포 모양을 담고, 측정·모델의 공통 배율 오차가 상쇄된다.",
    "단일 코일은 전력 하나로 총량만 바꾸므로 ρ를 따로 제어할 수 없다. 이중 코일의 k, φ는 [[r:가열 분포 → 전자온도 분포 → 이온화 분포]]를 거쳐 ρ를 바꾼다.",
    "모델은 단계적으로 세운다: [[r:단일 코일은 r만으로, 이중 코일은 전자기장만 (r, z)로]] 풀고 수송은 r로 유지한다. 근거: 가열 모양 고정(차이 ≤ 9%), r–(r, z) 수송의 ρ 차이 0.3%, 코일–플라즈마 거리가 두 코일 가열의 겹침을 두 배로 바꿈.",
    "전자 에너지 보존식은 옴 가열, 에너지 선속(엔탈피 대류 + 열전도), 양극성 전기장에 대한 일, 충돌·벽 손실의 균형으로 정리했다.",
    "독립 제어는 [[r:제어 Jacobian의 계수와 평균 유지 형상 이득 g_{k}]]로 판정하고, COMSOL 교차 검증으로 모델 가정을 점검한다.",
]
t = dpara(s, 0.5, 1.1, 9.0, 3.9, paras, size=14, after=9, line=1.08)
for p in t.text_frame.paragraphs:
    for r in p.runs:
        if r.font.color.rgb != lib.rgb(RED):
            r.font.bold = False
box(s, 0.5, 4.7, 9.0, 0.85, fill="F2F4F8", line=None, radius=None, margin=0.12,
    paras=[{"t": "2차 발표 계획", "bold": True, "color": NAVY, "size": 12.5, "after": 2},
           {"t": "1단계 단일 코일 결과 (T_{e}(r), n(r), 해석해 대조) → 2단계 이중 코일 판정 (J, g_{k}, 도달 가능한 ρ 범위) → COMSOL 대조", "size": 12}],
    size=12, color="222222", name="다음 단계")
num(s, 14)
NOTES[14] = ("[대본 · 19:05–20:00 / 55초]\n정리하겠습니다. 저희는 제어 목표를 평균 밀도 유지와 밀도비 조절로 정의했고, 밀도비는 총량과 분리된 모양만 담는 양입니다. "
             "단일 코일로는 밀도비를 따로 제어할 수 없고, 이중 코일의 k와 φ가 가열, 전자온도, 이온화 분포를 거쳐 밀도비를 바꿉니다. "
             "모델은 교수님 피드백대로 단일 코일은 r만으로, 이중 코일은 전자기장만 r과 z로 풀고, 수송은 r로 유지합니다. 독립 제어는 제어 Jacobian과 평균 유지 형상 이득으로 판정하고, COMSOL로 검증하겠습니다. "
             "2차 발표에서는 1단계 단일 코일 결과와 2단계 이중 코일의 판정 결과를 보여드리겠습니다. 감사합니다.",
             "각 결론의 근거 쪽: 1 → 3–4쪽, 2 → 5쪽, 3 → 6–8쪽, 4 → 10쪽, 5 → 12–13쪽.")

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
    "R′_{in}, R′_{out}: 각 코일의 플라즈마 부하 저항, R′_{×}: 교차 저항. 상반성 Z_{io} = Z_{oi}이므로 R′_{×}는 실수 (위상 오프셋 없음)",
    "0D 식에서 k, φ, P_{tot}가 들어갈 자리는 P_{abs}뿐이다 → 같은 P_{abs}면 같은 n_{0}, T_{e}는 불변",
], size=12)
key(s, "0D 균형은 T_{e}와 밀도 수준을 정하지만 분포의 모양은 정하지 않는다.")
foot(s, "[1] §2.4 pp.133–138, 식 (2.63)–(2.73). 반복 계산의 초기값(T_{e0}, n_{*})으로만 쓴다.")
num(s, 17)
NOTES[17] = ("[부록 A1] 5쪽 표의 0D 두 행의 세부. 0D 초기값은 11쪽 계산 흐름의 출발점.", None)

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
foot(s, "본문 식 (5)의 P_{port} = ½I_{0}^{2}a^{H}Re(Z)a와 같은 식. em_field.port_drive로 전원별 전력과 코일 전압을 계산한다.")
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
key(s, "가정의 타당성은 아직 검증된 결과가 아니며, 4개 항목을 COMSOL 대조로 점검한다 (13쪽).")
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
    ["코일별 가열 겹침 O", "d = 2.0 / 3.0 / 4.5 cm", "0.19 / 0.27 / 0.39"],
    ["단일 코일 ρ의 거리 의존", "d = 2.0 / 3.0 / 4.5 cm", "1.268 / 1.295 / 1.332"],
    ["간섭 위상 ψ", "진공 (σ_{p} = 0) / 플라즈마", "0 / −10.7° ~ +10.4° (깊이 변화 ≤ 1.5°)"],
], size=10, row_h=0.4, col_align=["l", "l", "l"], header_size=10.5)
key(s, "모든 값은 같은 모델 코드와 같은 기준 조건에서 계산했다.")
foot(s, "기준: 300 W, Ar 10 mTorr, 13.56 MHz, k = 1, φ = 0, 격자 60 × 56. 코드: 저장소 sim/hybrid (팀 GitHub), 그림: presentations/src/rev1123.")
num(s, 23)
NOTES[23] = ("[부록 A7] sep.py, why_z.py, zgeom.py, nums.py, figs.py (presentations/src/rev1123/calc).", None)

# ---------------------------------------------------------------- 노트
for i, sl in enumerate(prs.slides, start=1):
    if i in NOTES:
        notes(sl, *NOTES[i])
cover_note = ("[대본 · 0:00–0:25 / 25초]\n안녕하세요, 6조입니다. 저희 주제는 이중 코일 유도 결합 플라즈마에서 중앙과 가장자리의 전자 밀도를 따로 조절하는 것입니다. "
              "오늘은 그 이론적 배경과, 교수님 피드백을 반영해 다시 세운 모델링 전략을 말씀드리겠습니다.")
notes(prs.slides[0], cover_note, "20분 녹화 발표 (2026-11-23 수정본). 교수님 피드백: 밀도비의 이유, 에너지 수송 용어, 앞부분 축소, 단일 코일 r 먼저, 다중 코일 z, COMSOL 검증.")

prs.core_properties.last_modified_by = "주제 3 팀"
prs.core_properties.author = "주제 3 팀"
prs.core_properties.title = "중앙·가장자리 플라즈마 밀도 독립 제어를 위한 모델링 전략"
prs.save(OUT)
print("saved", OUT, len(prs.slides))
