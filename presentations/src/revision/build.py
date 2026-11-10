"""이론 개정본(24쪽) 기반 1차 발표 두 판.

  핵심 수식판 (core): 본편에는 판정에 필요한 핵심 식만 두고, 나머지 유도 전체는 숨긴 부록으로.
  전체 수식판 (full): 문서의 모든 식을 본편에 두고, 핵심 식에만 빨간 상자.
  빨간 상자의 식 = 핵심 수식판 본편에 남는 식(KEY).

    python presentations/src/revision/build.py
수식: eq/mk.py → NODE_PATH=/opt/npm-tools/node_modules node eq/render.js. 그림: fig/figs.py.
"""
import json, re, sys, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
import lib
from lib import I, tb, box, seg, table
from pptx import Presentation
from pptx.util import Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement

R = str(HERE)
SRC = str(ROOT / 'presentations' / '1차발표_이론배경판.pptx')
OUTS = {'core': str(ROOT / 'presentations' / '1차발표_개정본_핵심수식판.pptx'),
        'full': str(ROOT / 'presentations' / '1차발표_개정본_전체수식판.pptx')}
lib.EQ_DIR = R + '/eq'
lib.EQ_SIZES = json.load(open(R + '/eq/sizes.json'))

NAVY, TEXT, MUTED, MSG = '004680', '17263C', '4C5B72', '303399'
BLUE, ORANGE, ORANGE_D, GREEN = '3366CC', 'D9622B', 'B24A16', '2E7D4F'
BLUE_L, ORANGE_L, LINE, PANEL, GRAY = 'EEF3FB', 'FDF2EB', 'D8E1EB', 'F4F6FA', '8C93A3'
RED = 'D0021B'

KEY = {'e1_4', 'e1_8', 'target', 'e1_10', 'e1_13', 'e4_7', 'e4_11', 'e5_4', 'e5_6', 'e5_7', 'e6_5',
       'e6_11', 'e6_13', 'e7_2', 'e7_17', 'e7_19', 'e8_8', 'e8_11', 'e8_24', 'e8_28', 'e8_43',
       'e9_1', 'e9_2', 'e9_3'}

# 실행마다 바뀌는 상태
prs = OLD = LAYOUT = None
MARK = False
META = {}
WARN = []


# ------------------------------------------------------------------ 틀
def pnum(s, n):
    t = s.shapes.add_textbox(I(9.04), I(6.61), I(0.45), I(0.23))
    tf = t.text_frame
    for side in ('left', 'right', 'top', 'bottom'):
        setattr(tf, f'margin_{side}', 0)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT
    fld = OxmlElement('a:fld'); fld.set('id', '{' + str(uuid.uuid4()).upper() + '}'); fld.set('type', 'slidenum')
    rPr = OxmlElement('a:rPr'); rPr.set('lang', 'en-US'); rPr.set('sz', '1050')
    sf = OxmlElement('a:solidFill'); c = OxmlElement('a:srgbClr'); c.set('val', MUTED); sf.append(c); rPr.append(sf)
    la = OxmlElement('a:latin'); la.set('typeface', 'Arial'); rPr.append(la)
    fld.append(rPr)
    tt = OxmlElement('a:t'); tt.text = str(n); fld.append(tt)
    p._p.append(fld)
    t.name = '쪽 번호'


def set_title(s, text, size=None):
    if size is None:
        n = len(text)
        size = 28 if n <= 20 else 26 if n <= 23 else 24 if n <= 26 else 22 if n <= 29 else 20
    ph = s.shapes.title
    ph.text_frame.text = text
    for p in ph.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(size)


def frame(title, kicker, msg, foot):
    s = prs.slides.add_slide(LAYOUT)
    set_title(s, title)
    tb(s, 0.5, 1.05, 8.96, 0.31, kicker, size=12, bold=True, color=MUTED, name='소제목')
    if msg:
        box(s, 0.5, 5.92, 9.0, 0.0125, fill=MSG, radius=None, name='구분선')
        tb(s, 0.5, 6.01, 9.01, 0.5, msg, size=16, bold=True, color=MSG, anchor='m', name='핵심 메시지')
    if foot:
        tb(s, 0.5, 6.56, 8.45, 0.28, foot, size=10.5, color=MUTED, name='각주')
    return s


def label(s, x, y, w, text, size=12.5, color=MUTED, h=0.3, bold=False, align='l'):
    return tb(s, x, y, w, h, text, size=size, color=color, bold=bold, align=align)


def head(s, x, y, w, text, size=14.5, color=NAVY):
    return tb(s, x, y, w, 0.32, text, size=size, bold=True, color=color)


def arrow(s, x1, y1, x2, y2, color=GRAY, w=1.5):
    return seg(s, x1, y1, x2, y2, color=color, w=w, head=True)


def redbox(s, x, y, w, h):
    b = box(s, x - 0.06, y - 0.03, w + 0.12, h + 0.06, fill=None, line=RED, lw=2.0, radius=None, name='핵심 수식 표시')
    return b


def eqsize(name, pt):
    z = lib.EQ_SIZES[name]
    return z['w'] / 96 * pt / 30, z['h'] / 96 * pt / 30


def put(s, name, x, y, pt, maxw=None, center_w=None):
    w, h = eqsize(name, pt)
    if maxw and w > maxw:
        pt = pt * maxw / w
        w, h = eqsize(name, pt)
    if pt < 12.5:
        WARN.append(f'{name} {pt:.1f}pt')
    if center_w:
        x = x + (center_w - w) / 2
    lib.eq(s, name, x, y, pt=pt)
    if MARK and name in KEY:
        redbox(s, x, y, w, h)
    return x, w, h


def rows(s, items, y=1.47, x0=0.55, labw=1.62, xr=9.45, gap=0.12, ymax=5.86):
    """수식 행 쌓기. item: dict(eq, pt, lab, num, above, indent) 또는 dict(text, h, size)."""
    for it in items:
        if 'text' in it:
            h = it.get('h', 0.32)
            tb(s, x0, y, xr - x0, h, it['text'], size=it.get('size', 13), color=it.get('color', TEXT),
               bold=it.get('bold', False))
            y += h + it.get('gap', gap)
            continue
        name, pt, lab, num = it['eq'], it.get('pt', 16), it.get('lab'), it.get('num')
        right = xr - (0.66 if num else 0)
        if lab and it.get('above'):
            label(s, x0, y, right - x0, lab, size=12.5, color=NAVY, bold=True)
            y += 0.3
            xe = x0 + it.get('indent', 0.2)
        elif lab is not None:
            xe = x0 + labw
        else:
            xe = x0 + it.get('indent', 0.2)
        xx, w, h = put(s, name, xe, y, pt, maxw=right - xe - 0.08)
        if lab and not it.get('above'):
            tb(s, x0, y + h / 2 - 0.17, labw - 0.08, 0.34, lab, size=12.5, color=NAVY, bold=True, anchor='m')
        if num:
            tb(s, xr - 0.62, y + h / 2 - 0.14, 0.62, 0.28, num, size=12, color=MUTED, align='r')
        y += h + it.get('gap', gap)
    if y > ymax + 0.01:
        WARN.append(f'세로 넘침 {y:.2f}: {s.shapes.title.text_frame.text}')
    return y


def reg(s, key, secs, script, basis):
    META[id(s)] = dict(key=key, secs=secs, script=script.strip(), basis=basis.strip())


def chamber(s, x0, y0, sc=0.19, regions=True):
    """반단면: 왼쪽 끝이 축(r = 0), 오른쪽이 측벽(r = 21 cm)."""
    W = 21 * sc
    yc = y0 + 0.10
    wt = y0 + 0.24
    wb = wt + 2 * sc
    bt = wb + 6 * sc
    box(s, x0, wt, W, wb - wt, fill='D6E2F0', radius=None, name='석영 창')
    box(s, x0, wb, W, bt - wb, fill='F7F9FC', radius=None, name='플라즈마')
    box(s, x0, bt - 0.05, 15 * sc, 0.05, fill='5F6779', radius=None, name='웨이퍼')
    seg(s, x0 + W, wb, x0 + W, bt, color=TEXT, w=3.0)
    seg(s, x0, bt, x0 + W, bt, color=TEXT, w=2.0)
    seg(s, x0, y0 - 0.02, x0, bt, color=GRAY, w=1.0, dash=True)
    for r in (3, 6, 9):
        lib.circle(s, x0 + r * sc, yc, 0.15, fill=BLUE)
    for r in (12, 15, 18):
        lib.circle(s, x0 + r * sc, yc, 0.15, fill=ORANGE)
    if regions:
        zw = bt - 0.05 - 1 * sc
        box(s, x0, zw - 0.035, 5 * sc, 0.07, fill=BLUE, radius=None, name='중앙 영역')
        box(s, x0 + 12 * sc, zw - 0.035, 2.5 * sc, 0.07, fill=ORANGE, radius=None, name='가장자리 영역')
    return dict(W=W, yc=yc, wt=wt, wb=wb, bt=bt)


def chain_diagram(s, y):
    """ICP 가열 과정 (문서 그림 1)."""
    items = [('RF 코일', 'I_{RF}'), ('시변 자속', '∂_{t}Φ_{B}'), ('유도 전기장', 'E_{θ}'),
             ('전자 가열', 'p_{abs}'), ('충돌·이온화', 'G(r, z)')]
    w, gap, x = 1.56, 0.3, 0.55
    for i, (a, b) in enumerate(items):
        box(s, x, y, w, 0.72, fill=BLUE_L if i < 4 else ORANGE_L, line=None, radius=0.06, align='c', anchor='m',
            margin=0.04, paras=[{'t': a, 'bold': True, 'color': NAVY, 'after': 1}, {'t': b, 'color': TEXT}], size=13)
        if i < 4:
            arrow(s, x + w + 0.04, y + 0.36, x + w + gap - 0.04, y + 0.36, color=NAVY)
        x += w + gap


def coupling_diagram(s, y):
    """세 물리 과정 (문서 그림 4)."""
    items = [('전자기 결합', 'I → E_{θ} → p_{abs}'), ('전자 에너지 수송', 'p_{abs} → G'), ('입자 확산·벽 손실', 'G → n(r, z)')]
    w, gap, x0 = 2.62, 0.57, 0.55
    xs = []
    for i, (a, b) in enumerate(items):
        x = x0 + i * (w + gap)
        xs.append(x)
        box(s, x, y, w, 0.78, fill=BLUE_L, line=NAVY, lw=1.0, radius=0.06, align='c', anchor='m', margin=0.04,
            paras=[{'t': a, 'bold': True, 'color': NAVY, 'after': 2, 'size': 14}, {'t': b, 'color': TEXT}], size=13.5)
        if i < 2:
            arrow(s, x + w + 0.05, y + 0.39, x + w + gap - 0.05, y + 0.39, color=NAVY, w=1.8)
    yb = y + 0.78
    lib.path(s, [(xs[2] + w / 2, yb), (xs[2] + w / 2, yb + 0.3), (xs[0] + w / 2, yb + 0.3), (xs[0] + w / 2, yb + 0.02)],
             color=GREEN, w=1.6, head=True)
    label(s, xs[1] - 0.3, yb + 0.31, w + 0.6, '밀도 → 전도도 → 전자기장 되먹임', size=12.5, color=GREEN, align='c')
    return xs, w


def lr_diagram(s, x, y, w=4.1, h=1.55):
    """얇은 챔버에서 국소 생성원의 반경 방향 전달 (문서 그림 7)."""
    box(s, x, y, w, h, fill='F7F9FC', line=LINE, radius=None, name='챔버')
    seg(s, x, y, x + w, y, color=TEXT, w=2.0)
    seg(s, x, y + h, x + w, y + h, color=TEXT, w=2.0)
    cx, cy = x + 0.55, y + h * 0.6
    lib.circle(s, cx, cy, 0.28, fill='6FA8A0')
    label(s, x + 0.08, y + 0.03, 1.4, '국소 생성원', size=12, color=TEXT)
    arrow(s, cx + 0.2, cy + 0.02, x + w - 0.55, cy + 0.02, color=BLUE, w=1.8)
    label(s, cx + 0.35, cy + 0.05, 2.0, '반경 방향 확산', size=12, color=BLUE, bold=True)
    for xx in (x + 1.6, x + 2.75):
        arrow(s, xx, cy - 0.12, xx, y + 0.06, color=ORANGE_D, w=1.4)
        arrow(s, xx, cy + 0.14, xx, y + h - 0.04, color=ORANGE_D, w=1.4)
    label(s, x + 1.7, y - 0.33, 2.4, '위·아래 쉬스 손실', size=12, color=ORANGE_D, bold=True)
    label(s, x + w + 0.06, cy - 0.15, 0.4, 'L', size=13, color=MUTED)
    label(s, x + w - 1.3, y + 0.03, 1.25, '기본 모드 k_{z}', size=12, color=MUTED, align='r')


def bullets(s, x, y, w, h, items, size=13.5, after=5):
    return tb(s, x, y, w, h, [{'t': t, 'bullet': True, 'after': after} for t in items], size=size, color=TEXT)


def note_box(s, x, y, w, h, title, text, fill=PANEL, size=13):
    return box(s, x, y, w, h, fill=fill, radius=None, margin=0.12, anchor='m',
               paras=[{'t': f'**{title}**  ' + text}] if title else [{'t': text}], size=size, color=TEXT)


def card(s, x, y, w, h, title, items, size=13.5, topc=NAVY):
    box(s, x, y, w, h, fill=None, line=LINE, radius=None, margin=0.12, paras=[
        {'t': title, 'bold': True, 'color': topc, 'size': 14.5, 'after': 5}] +
        [{'t': t, 'bullet': True, 'after': 4} for t in items], size=size, color=TEXT)
    box(s, x, y, w, 0.04, fill=topc, radius=None)


ASSUME = [
    ['기하와 좌표', '원통형 축대칭, ∂_{θ} = 0', '반경·높이의 2D 벌크 영역'],
    ['방전 기체', 'Ar, 전자와 Ar⁺ 중심', '준안정종·다중 반응은 제외'],
    ['벌크 전하', '준중성 n_{e} ≃ n_{i}', '쉬스 내부는 따로 계산하지 않음'],
    ['RF 시간 의존', '단일 주파수 정상 조화장, e^{jωt}', '고조파·점화 과도는 별도 문제'],
    ['전자기장', '준정적·축대칭 유도장, A_{θ} 중심', '변위전류·자기화 효과 생략 범위 확인'],
    ['전자 운동', 'ν_{m} 기반 복소 전도도', '비국소 RF 전도도·이방성 제외'],
    ['전자온도', '0D의 대표 T_{e}로 수송계수 정의', 'T_{e}(r, z) 직접 해석은 제외'],
    ['EEDF·반응계수', 'K_{iz}(T_{e})에 쓴 EEDF 가정 명시', '비맥스웰 꼬리·단계 이온화는 불확실'],
    ['중성 기체', 'n_{g}와 기체 온도 균일', '중성 고갈·가스 가열 제외'],
    ['입자 수송', '벌크에서 양극성 확산 D_{a}', '수송계수의 공간 의존성은 검증 항목'],
    ['입자 손실', '체적 재결합 등 생략', '생성–벽 손실 우세의 정상상태'],
    ['벽 조건', '쉬스 경계 Bohm 유출 → Robin 조건', '벽에서 n = 0(Dirichlet)은 비교용'],
    ['이온 생성', '기본안 G ∝ p_{abs}', '비국소 에너지 이동은 별도 민감도 검증'],
    ['운전·제어', '코일 전류비·위상·총 공급 전력', '독립 전류 구동·매칭 실현성 별도 확인'],
    ['최종 관심값', 'n_{c}, n_{edge}, n̄_{w}, ρ', '시간 평균 전자 밀도(이온 선속과 구분)'],
]


def assume_table(s, rws, y=1.47, rh=0.4):
    data = [['항목', '기본 가정', '물리적 의미·제외 범위']] + rws
    table(s, 0.5, y, [1.55, 3.55, 3.9], data, size=12.5, header_size=12.5, row_h=rh, header_fill=NAVY,
          line_color=LINE, first_col_bold=True, colors={(i, 0): NAVY for i in range(1, len(data))})
    return y + rh * len(data)


# ================================================================== 공통 슬라이드
def s_title(mode):
    s = OLD[0]
    sub = next(x for x in s.shapes if x.shape_id == 3)
    ps = sub.text_frame.paragraphs
    ps[1].runs[0].text = '이론적 배경과 상세 수식 유도 · ' + ('핵심 수식판' if mode == 'core' else '전체 수식판')
    for r in ps[1].runs[1:]:
        r.text = ''
    for r in ps[2].runs:
        r.text = r.text.replace('6팀', '6조')
    reg(s, 'title', 20, """안녕하세요, 6조입니다. 저희 주제는 이중 코일 유도 결합 플라즈마에서 중앙과 가장자리의 전자 밀도를 따로 조절하는 것입니다. 오늘은 이 문제를 판정하기 위한 이론적 배경과 식을 순서대로 말씀드리겠습니다.""",
        """IC-PBL 주제 3. 근거 문서: 팀 이론 정리 「1차 발표: 이론적 배경과 상세 수식 유도」 개정본(24쪽). """ +
        ('핵심 수식판: 본편은 판정에 필요한 식만, 나머지 유도는 숨긴 부록.' if mode == 'core' else
         '전체 수식판: 문서의 식을 모두 본편에 두고 핵심 식에 빨간 상자. 빨간 상자의 식은 핵심 수식판 본편의 식과 같다.'))
    return s


def s_toc(mode, rows_, foot, msg):
    s = OLD[1]
    for sh in list(s.shapes):
        if sh.has_table:
            sh._element.getparent().remove(sh._element)
    sh = {x.shape_id: x for x in s.shapes}
    set_text(sh[51], '이론 정리 개정본의 1–10장 순서 · 가열 → 수송 → 밀도 → 판정')
    set_text(sh[54], msg)
    set_text(sh[55], foot)
    data = [['구간', '다루는 내용', '쪽']] + rows_
    table(s, 0.5, 1.5, [3.0, 5.2, 0.8], data, size=13, header_size=13, row_h=0.7, header_fill=NAVY,
          line_color=LINE, col_align=['l', 'l', 'c'], first_col_bold=True,
          colors={(i, 0): NAVY for i in range(1, len(data))},
          row_heights=[0.4] + [min(0.84, 4.25 / len(rows_))] * len(rows_))
    reg(s, 'toc', 25, """발표는 다섯 구간입니다. 먼저 문제를 정의하고, 모델의 가정과 구조를 세운 뒤, 코일에서 밀도까지 이어지는 세 물리 과정을 차례로 따라가겠습니다. 마지막으로 독립 제어를 무엇으로 판정할지와 2차 계획을 말씀드리겠습니다.""",
        """구간은 문서 장 순서와 같다: 1장(배경·문제), 2–4장(가정·구조·0D), 5–6장(전자기 결합), 7–8장(에너지 수송·확산), 9–10장(판정·2차).""")
    return s


def set_text(shape, text):
    ps = shape.text_frame.paragraphs
    ps[0].runs[0].text = text
    for r in ps[0].runs[1:]:
        r.text = ''
    for p in ps[1:]:
        p._p.getparent().remove(p._p)


def s_kc():
    s = OLD[7]
    sh = {x.shape_id: x for x in s.shapes}
    set_title(s, '추가 코일의 효과는 형상과 레벨로 다르게 나타난다', 26)
    set_text(sh[51], '선행연구  ·  Kim & Chung (2020), Ar ICP, RF 150 W, 바깥쪽 수동 공진 코일')
    for sid, (x, w) in ((54, (1.12, 3.13)), (55, (5.72, 3.13))):
        sh[sid].left, sh[sid].top, sh[sid].width, sh[sid].height = I(x), I(1.9), I(w), I(2.4)
    for sid in (56, 57):
        sh[sid].top = I(4.36)
    set_text(sh[56], '공진 시 밀도 최대 위치가\n바깥쪽으로 이동했다(형상 변화).')
    set_text(sh[57], '분포 형상은 비슷하지만\n최대 밀도가 약 1.4배 증가했다(레벨 변화).')
    set_text(sh[59], '코일이 주는 공간 자유도가 밀도 형상으로 얼마나 전달되는지는 따로 분석해야 한다.')
    sh[59].text_frame.paragraphs[0].runs[0].font.size = Pt(16)
    set_text(sh[60], 'Kim & Chung (2020), Fig. 8 전자 밀도 패널. 검정 비공진, 빨강 공진. 본 연구의 독립 전류 구동과는 장치가 다르다.')
    sh[61]._element.getparent().remove(sh[61]._element)
    box(s, 0.5, 5.12, 9.0, 0.68, fill=BLUE_L, radius=None, margin=0.1, anchor='m', paras=[
        {'t': '**Zhao et al. (2026)**  Cl_{2} 이중 코일 유체 계산도 상대 전류·위상의 제어 가능성을 보였지만, 전기음성 기체의 반응·수송을 Ar에 그대로 옮길 수는 없다.'}],
        size=12.5, color=TEXT)
    reg(s, 'kc', 50, """그렇다면 실제로 코일을 하나 더 두면 어떻게 될까요. Kim과 Chung의 실험은 바깥쪽 수동 공진 코일을 켰을 때의 전자 밀도를 보여 줍니다. 50 mTorr에서는 밀도 최대 위치가 바깥으로 옮겨 가 형상이 바뀌었습니다. 그런데 1 mTorr에서는 형상은 거의 그대로이고 최대 밀도만 약 1.4배 올랐습니다. 같은 조작이 조건에 따라 형상으로도, 레벨로도 나타난다는 뜻입니다. 그래서 저희는 코일이 주는 자유도가 최종 밀도 형상으로 얼마나 전달되는지를 따로 떼어 분석하려고 합니다.""",
        """Kim & Chung, Phys. Plasmas 27, 063511 (2020), Fig. 8, 150 W. 초록: 1 mTorr의 밀도 증가는 전력 전달 효율 증가로 설명된다. 같은 논문 식 (5)·그림 5의 λ_ε는 7장에서 다시 쓴다.
Zhao et al., J. Appl. Phys. 139, 043301 (2026): R 21 cm, 높이 6 cm, 코일 3·6·9 / 12·15·18 cm, Cl₂ 40 mTorr. 본 연구의 기준 형상은 이 기하를 따른다. 정량 예측의 근거로 쓰지 않는다.""")
    pass_through(s)
    return s


def pass_through(s):
    """기존 슬라이드의 노트·표시 상태 초기화는 순서 정리에서 한다."""
    return s


def s_refs():
    s = frame('참고문헌', '이론과 인용 그림의 출처', '', '')
    refs = [('교재와 이론', ['정진욱 (2026). 『플라즈마 전자공학』, 제4판. 교문사. ISBN 978-89-363-2773-6.',
                         'M. A. Lieberman & A. J. Lichtenberg (2005). Principles of Plasma Discharges and Materials Processing, 2nd ed. Wiley. DOI 10.1002/0471724254.']),
            ('전자 에너지 수송과 방전 모드', ['J.-H. Kim & C.-W. Chung (2020). Effect of electron kinetics on plasma density in inductively coupled plasmas using a passive resonant antenna. Physics of Plasmas 27, 063511. DOI 10.1063/5.0006698.',
                                     'I.-S. Park, H.-J. Kang, K.-H. Kim & C.-W. Chung (2017). Experimental investigation of edge-to-center density ratio in E-H mode transition of an inductively coupled plasma. Physics of Plasmas 24, 123506.']),
            ('이중 코일 ICP', ['M.-L. Zhao, X.-J. Wang, D.-Q. Wen, Y.-R. Zhang, F. Gao & Y.-N. Wang (2026). Improvement of the plasma uniformity via current amplitudes and phase shifts in dual-coil antenna driven inductively coupled electronegative chlorine discharges. Journal of Applied Physics 139, 043301. DOI 10.1063/5.0301391.'])]
    y = 1.45
    for headt, items in refs:
        head(s, 0.52, y, 8.9, headt)
        y += 0.36
        for it in items:
            n_lines = 1 + len(it) // 118
            tb(s, 0.52, y, 8.95, 0.25 * n_lines + 0.08, it, size=12, color=TEXT)
            y += 0.25 * n_lines + 0.14
        y += 0.08
    reg(s, 'refs', 0, '', """교재를 먼저 인용하고, 교재에 없는 내용(복소 전도도, 유체 에너지 방정식, 반응 계수)은 Lieberman을 쓴다. 근거 문서는 팀 이론 정리 개정본이다.""")
    return s


# ================================================================== 1장
def d_icp():
    s = frame('ICP는 코일 전류로 전자를 가열한다', '연구 배경  ·  유도 결합 방전의 가열 과정',
              '코일이 직접 바꾸는 것은 장과 흡수 분포이고, 밀도는 그 뒤의 수송을 거쳐 정해진다.',
              '정진욱 (2026) §2.3.4 pp.121–123, 식 (2.52). 식 (1.3)은 유도장 성분만의 관계다.')
    chain_diagram(s, 1.47)
    rows(s, [dict(eq='e1_1', pt=17, lab='패러데이 법칙', num='(1.1)'),
             dict(eq='e1_2', pt=16, lab='균일 B_{z} 가정', num='(1.2)'),
             dict(eq='e1_3', pt=17, lab='페이저 유도장', num='(1.3)')], y=2.42, gap=0.1)
    note_box(s, 0.5, 4.95, 9.0, 0.85, '연구 출발점', '코일이 직접 바꾸는 것은 RF 전류·유도장·흡수 전력의 공간 분포다. 최종 n_{e}(r, z)를 알려면 전자 에너지 수송과 입자 수송을 더 설명해야 한다.', size=13.5)
    reg(s, 'd_icp', 50, """ICP는 코일의 RF 전류가 만드는 시변 자기장으로 전자를 가열합니다. 패러데이 법칙에 따라 원주 방향의 유도 전기장이 생기고, 축방향 자속이 균일하다고 잠시 가정하면 그 크기는 반경에 비례합니다. 실제 코일장은 균일하지 않으므로 방위각 벡터 퍼텐셜로 쓰고, 유도장은 −jω A_θ가 됩니다. 이 전기장이 전자를 가열하고, 가열된 전자가 이온화를 일으킵니다. 여기서 중요한 점은 코일이 직접 바꾸는 것은 장과 흡수 분포까지라는 것입니다. 밀도는 그 뒤에 수송을 거쳐 정해집니다.""",
        """정진욱 (2026) §2.3.4 p.122 식 (2.52): 원통형 ICP에서 E_θ = −(r/2)dB_z/dt 꼴, 중심에서 0. 식 (1.3)은 유도장 성분의 관계이며 정전기장·쉬스 전기장은 포함하지 않는다. 그림은 문서 그림 1의 개념도.""")
    return s


def c_icp():
    s = frame('ICP는 코일 전류로 전자를 가열한다', '연구 배경  ·  유도 결합 방전의 가열 과정',
              '코일이 직접 바꾸는 것은 장과 흡수 분포이고, 밀도는 그 뒤의 수송을 거쳐 정해진다.',
              '정진욱 (2026) §2.3.4 pp.121–123, 식 (2.52). 유도: 부록 A1.')
    chain_diagram(s, 1.55)
    tb(s, 0.55, 2.55, 8.9, 1.9, [
        {'t': '**1**  RF 안테나에 전류 I_{RF}(t)가 흘러 시간에 따라 변하는 자기장 B(r, z, t)가 생긴다.', 'after': 7},
        {'t': '**2**  패러데이 법칙에 따라 원주 방향의 유도 전기장 E_{θ}가 생긴다.', 'after': 7},
        {'t': '**3**  전자는 E_{θ}에 반응해 RF 전류 J_{θ}를 만들며 에너지를 흡수한다.', 'after': 7},
        {'t': '**4**  전자–Ar 충돌로 이온화·여기가 일어나고, 생성 입자는 확산·벽 손실과 균형을 이룬다.'}],
       size=15, color=TEXT, space_after=0, line=1.15)
    note_box(s, 0.5, 4.75, 9.0, 0.95, '연구 출발점', '코일이 직접 바꾸는 것은 RF 전류·유도장·흡수 전력의 공간 분포다. 최종 n_{e}(r, z)를 알려면 전자 에너지 수송과 입자 수송을 더 설명해야 한다.', size=14)
    reg(s, 'c_icp', 45, """ICP는 코일의 RF 전류가 만드는 시변 자기장으로 전자를 가열합니다. 전류가 자기장을 만들고, 패러데이 법칙에 따라 원주 방향의 유도 전기장이 생기며, 전자는 이 장에서 에너지를 얻어 이온화를 일으킵니다. 여기서 짚고 싶은 점은 코일이 직접 바꾸는 것이 장과 흡수 분포까지라는 것입니다. 저희가 원하는 밀도는 그 뒤에 수송을 거쳐 정해집니다. 그러면 코일이 하나뿐일 때 이 분포를 얼마나 바꿀 수 있을까요?""",
        """정진욱 (2026) §2.3.4 p.122 식 (2.52): 원통형 ICP에서 E_θ = −(r/2)dB_z/dt 꼴, 중심에서 0. 개념도는 문서 그림 1. 식 (1.1)–(1.3)의 유도는 부록 A1.""")
    return s


def d_single():
    s = frame('코일 하나는 흡수의 크기만 바꾼다', '단일 코일의 한계  ·  형상 조절 자유도',
              '두 번째 코일은 공간 응답이 다른 장을 더하지만, 그것이 곧 독립 제어를 보장하지는 않는다.',
              '[유도] 전도도를 고정한 선형 장 문제. 균일 생성에서도 중앙이 높은 이유는 8장 식 (8.15)·(8.21).')
    rows(s, [dict(eq='e1_4', pt=18, lab='단일 코일', num='(1.4)')], y=1.5)
    bullets(s, 0.55, 2.2, 8.9, 1.25, [
        '전도도를 고정하면 |I|는 p_{abs}의 **크기**만 바꾸고, 정규화된 형상은 단위 전류 응답 |𝒜(r, z)|²가 정한다.',
        '전력을 올리면 밀도·전도도·표피 효과가 바뀌어 형상도 조금 바뀌지만, 중심과 가장자리를 **따로** 보정하는 직접 수단은 아니다.'], size=13.5)
    rows(s, [dict(eq='e1_5', pt=18, lab='이중 코일', num='(1.5)')], y=3.62)
    note_box(s, 0.5, 4.45, 9.0, 1.3, '추가 자유도 ≠ 독립 제어의 보장',
             '안쪽과 바깥쪽 코일을 나누면 공간 응답 𝒜_{in}, 𝒜_{out}을 조합할 수 있다. 그러나 전자기장 간섭, 전자 에너지 수송, 양극성 확산·벽 손실이 이 자유도를 다시 결합시킬 수 있다.', size=13.5)
    reg(s, 'd_single', 45, """코일이 하나라면 전도도를 고정했을 때 장은 전류에 비례하고, 흡수 전력은 전류 제곱에 비례합니다. 전류는 흡수의 크기만 바꾸고, 정규화된 형상은 단위 전류 응답 𝒜가 정합니다. 물론 전력을 올리면 밀도와 표피 효과가 바뀌어 형상도 조금 바뀌지만, 중심과 가장자리를 따로 보정하는 수단은 아닙니다. 코일을 안쪽과 바깥쪽으로 나누면 서로 다른 공간 응답 두 개를 조합할 수 있습니다. 다만 자유도가 늘었다는 사실이 곧 최종 밀도를 독립적으로 제어할 수 있다는 보장은 아닙니다.""",
        """식 (1.4): 같은 전도도에서 E_θ = −jωI𝒜, p_abs = ½Re(σ_p)ω²|I|²|𝒜|². 문서 1.2절: 생성이 균일해도 벽 확산 손실로 중앙이 높을 수 있으므로(8장) 단일 코일의 문제는 '항상 중앙이 높다'가 아니라 보정 패턴을 만들 수단이 제한된다는 것.""")
    return s


def c_single():
    s = frame('코일 하나는 흡수의 크기만 바꾼다', '단일 코일의 한계  ·  형상 조절 자유도',
              '단일 코일의 문제는 불균일성 자체가 아니라 형상을 조절할 자유도가 없다는 데 있다.',
              '[유도] 전도도를 고정한 선형 장 문제. 유도와 이중 코일 식 (1.5): 부록 A2.')
    put(s, 'e1_4', 0.55, 1.55, 20, center_w=8.9)
    card(s, 0.5, 2.5, 4.4, 1.75, '전도도를 고정하면', [
        '|I|는 p_{abs}의 **크기**만 바꾼다.',
        '정규화된 형상은 단위 전류 응답 |𝒜(r, z)|²가 정한다.'])
    card(s, 5.1, 2.5, 4.4, 1.75, '실제 장치에서는', [
        '전력이 밀도·전도도·표피 효과를 바꿔 형상도 조금 바뀐다.',
        '그러나 중심과 가장자리를 **따로** 보정하는 직접 수단은 아니다.'])
    note_box(s, 0.5, 4.5, 9.0, 1.2, None,
             '생성이 어디서나 같아도 벽으로의 확산 손실 때문에 밀도는 중앙이 높아질 수 있다. 그래서 문제는 "항상 중앙이 높다"가 아니라, **필요한 보정 패턴을 적극적으로 만들 수단이 없다**는 것이다.', size=13.5)
    reg(s, 'c_single', 45, """코일이 하나라면 어떨까요. 플라즈마 전도도를 고정하면 장은 전류에 비례하고 흡수 전력은 전류 제곱에 비례합니다. 그래서 전류는 흡수의 크기만 바꾸고, 정규화된 형상은 코일과 챔버가 만든 단위 전류 응답 𝒜가 정해 버립니다. 실제로는 전력을 올리면 밀도와 표피 효과가 바뀌어 형상도 조금 움직이지만, 중심과 가장자리를 따로 맞추는 수단은 아닙니다. 그래서 저희가 보는 문제는 밀도가 중앙에서 높다는 사실 자체가 아니라, 원하는 보정 패턴을 만들 자유도가 없다는 점입니다. 그 자유도를 더하는 방법이 코일을 둘로 나누는 것입니다.""",
        """식 (1.4) E_θ = −jωI𝒜, p_abs = ½Re(σ_p)ω²|I|²|𝒜|². 균일 생성에서도 중앙이 높아지는 이유는 8장 식 (8.15)·(8.28)에서 다룬다(본편 16쪽). 이중 코일 식 (1.5)와 '추가 자유도 ≠ 독립 제어' 논의는 부록 A2.""")
    return s


def d_chamber():
    s = frame('중앙과 가장자리의 면적 평균 밀도를 비교한다', '연구 대상 챔버와 밀도 평가 영역',
              '목표는 평균 밀도 n̄_{w}의 변화를 억제하면서 형상 ρ를 움직이는 것이다.',
              '기준 형상: Zhao et al. (2026)의 기하. 반단면 축척 일치, 설치 높이는 개념적. R_{w}는 관측 영역에 맞춰 정한다.')
    x0 = 0.6
    g = chamber(s, x0, 1.72, sc=0.19)
    label(s, x0 + 0.05, 1.42, 1.6, '안쪽 3·6·9 cm', size=12, color=BLUE, bold=True)
    label(s, x0 + 2.2, 1.42, 1.8, '바깥 12·15·18 cm', size=12, color=ORANGE_D, bold=True)
    label(s, x0 + 0.05, g['wb'] + 0.04, 2.0, 'Ar 플라즈마 L = 6 cm', size=12, color=MUTED)
    label(s, x0 + 0.02, g['bt'] - 0.55, 1.0, 'n_{c}', size=12.5, color=BLUE, bold=True)
    label(s, x0 + 12 * 0.19 - 0.05, g['bt'] - 0.55, 1.0, 'n_{edge}', size=12.5, color=ORANGE_D, bold=True)
    label(s, x0, g['bt'] + 0.04, 4.1, '축(r = 0)부터 측벽(R = 21 cm)까지 반단면', size=12)
    put(s, 'e1_8', 5.0, 1.45, 19)
    label(s, 6.45, 1.6, 3.0, '(1.8)', size=12, color=MUTED, align='r')
    tb(s, 6.95, 1.68, 2.5, 0.7, [{'t': 'ρ > 1  중앙 볼록', 'after': 2}, {'t': 'ρ < 1  가장자리 상대 우세'}], size=12.5, color=TEXT)
    head(s, 5.0, 2.55, 4.4, '제어 목표', size=13.5)
    put(s, 'target', 5.0, 2.88, 16)
    rows(s, [dict(eq='e1_6', pt=14, num='(1.6)', indent=0.05),
             dict(eq='e1_7', pt=14, num='(1.7)', indent=0.05),
             dict(eq='nw', pt=14, num='', indent=0.05)], y=3.88, gap=0.04)
    reg(s, 'd_chamber', 50, """기준 장치는 반경 21 cm, 높이 6 cm의 원통형 Ar ICP이고, 안쪽 코일은 3, 6, 9 cm, 바깥쪽 코일은 12, 15, 18 cm에 있습니다. 웨이퍼 위 평가면에서 반경 5 cm 안쪽의 면적 평균을 n_c, 12에서 14.5 cm 고리의 면적 평균을 n_edge로 정의하고, 그 비를 ρ라 하겠습니다. 전체 레벨은 관측 반경 안의 면적 평균 n̄_w로 봅니다. 저희의 목표는 n̄_w의 변화를 억제하면서 ρ를 움직이는 것입니다. 한 영역을 완전히 고정하고 다른 영역만 바꾸는 목표와는 구분합니다.""",
        """기하: Zhao et al., J. Appl. Phys. 139, 043301 (2026) — R 21 cm, 플라즈마 높이 6 cm, 창 2 cm, 코일 3·6·9 / 12·15·18 cm. 평가면 z = z_w는 웨이퍼 상부. R_w는 챔버 반경과 다르며 관측 영역에 맞춰 정한다(팀 결정 사항). 목표 범위·허용 오차는 팀 결정 사항.""")
    return s


def c_chamber():
    s = frame('중앙과 가장자리의 면적 평균 밀도를 비교한다', '연구 대상 챔버와 밀도 평가 영역',
              '목표는 평균 밀도 n̄_{w}의 변화를 억제하면서 형상 ρ를 움직이는 것이다.',
              '기준 형상: Zhao et al. (2026)의 기하. 면적 평균의 정의식 (1.6)·(1.7)과 n̄_{w}: 부록 A3.')
    x0 = 0.6
    g = chamber(s, x0, 2.1, sc=0.2)
    label(s, x0 + 0.05, 1.8, 1.6, '안쪽 3·6·9 cm', size=12, color=BLUE, bold=True)
    label(s, x0 + 2.3, 1.8, 1.8, '바깥 12·15·18 cm', size=12, color=ORANGE_D, bold=True)
    label(s, x0 + 0.05, g['wb'] + 0.04, 2.0, 'Ar 플라즈마 L = 6 cm', size=12, color=MUTED)
    label(s, x0 + 0.02, g['bt'] - 0.55, 1.0, 'n_{c}', size=12.5, color=BLUE, bold=True)
    label(s, x0 + 12 * 0.2 - 0.05, g['bt'] - 0.55, 1.0, 'n_{edge}', size=12.5, color=ORANGE_D, bold=True)
    label(s, x0, g['bt'] + 0.06, 4.2, '축(r = 0)부터 측벽(R = 21 cm)까지 반단면', size=12.5)
    put(s, 'e1_8', 5.05, 1.55, 24)
    tb(s, 5.05, 2.45, 4.4, 1.6, [
        {'t': 'n_{c}: 웨이퍼 위 r < 5 cm의 면적 평균', 'bullet': True, 'after': 4},
        {'t': 'n_{edge}: 12–14.5 cm 고리의 면적 평균', 'bullet': True, 'after': 4},
        {'t': 'ρ > 1 중앙 볼록, ρ < 1 가장자리 상대 우세', 'bullet': True, 'after': 4},
        {'t': 'n̄_{w}: 관측 반경 R_{w} 안의 면적 평균(전체 레벨)', 'bullet': True}], size=13.5, color=TEXT)
    box(s, 5.0, 4.25, 4.5, 1.5, fill=BLUE_L, radius=None, margin=0.12)
    head(s, 5.15, 4.33, 4.2, '제어 목표', size=14)
    put(s, 'target', 5.15, 4.72, 19)
    label(s, 5.15, 5.28, 4.3, '한 영역을 고정하고 다른 영역만 바꾸는 목표와 구분', size=12, color=MUTED)
    reg(s, 'c_chamber', 50, """그렇다면 무엇을 비교할지 먼저 정하겠습니다. 기준 장치는 반경 21 cm, 높이 6 cm의 원통형 Ar ICP이고, 안쪽 코일은 3, 6, 9 cm, 바깥쪽 코일은 12, 15, 18 cm에 있습니다. 웨이퍼 위에서 반경 5 cm 안쪽의 면적 평균을 n_c, 12에서 14.5 cm 고리의 평균을 n_edge라 하고, 그 비를 ρ라 하겠습니다. 전체 레벨은 관측 영역의 평균 n̄_w로 봅니다. 그러면 저희 목표는 한 줄로 쓸 수 있습니다. n̄_w는 그대로 두고 ρ만 움직이는 것입니다.""",
        """기하: Zhao et al., J. Appl. Phys. 139, 043301 (2026). 식 (1.6) n_c = (2/r_c²)∫₀^{r_c} n r dr, 식 (1.7) n_edge = 2/(r₂² − r₁²)∫ n r dr, n̄_w = (2/R_w²)∫₀^{R_w} n r dr. 이 목표 식은 9장 판정식 (9.3)과 같다. R_w·목표 범위·허용 오차는 팀 결정 사항.""")
    return s


def d_knob1():
    s = frame('상대 진폭과 상대 위상은 복소 전류의 두 자유도다', '제어 노브 1  ·  전류 페이저와 단위 전류 응답',
              'k와 φ는 흡수 분포의 구성을 바꾸는 두 자유도다.', '[유도] 공통 위상을 시간 원점으로 제거. 절대 RF 위상은 시간 평균 흡수에 영향이 없다.')
    rows(s, [dict(eq='e1_9', pt=16, lab='두 코일 전류를 피크 페이저로 쓰고 공통 위상을 제거하면', above=True, num='(1.9)'),
             dict(eq='e1_10', pt=18, lab='같은 플라즈마 상태에서 단위 전류 응답 𝒜_{in}, 𝒜_{out}을 쓰면', above=True, num='(1.10)')],
         y=1.47, gap=0.16)
    bullets(s, 0.55, 3.95, 8.9, 1.85, [
        '독립인 실질 자유도는 **(I_{0}, k, φ)**이다.',
        'k는 두 코일의 상대 가열 기여를, φ는 서로 겹친 전기장의 간섭을 바꾼다.',
        '단위 전류장에 공간적인 복소 위상이 들어 있으므로, φ = π에서 항상 최적 상쇄나 최적 분리가 일어난다고 단정할 수 없다.'], size=13.5)
    reg(s, 'd_knob1', 40, """두 코일 전류를 피크 페이저로 쓰고 공통 위상을 시간 원점으로 지우면, 안쪽 전류 크기 I_0와 상대 진폭 k, 상대 위상 φ만 남습니다. 이것을 단위 전류 응답과 결합하면 전기장은 𝒜_in 더하기 k e^{jφ} 𝒜_out에 비례합니다. k는 두 코일의 상대 가열 기여를, φ는 겹친 장의 간섭을 바꿉니다. 다만 단위 전류장 자체에 공간적 위상이 있으므로 φ = π라고 해서 항상 최적 분리가 되는 것은 아닙니다.""",
        """식 (1.9) I = I₀[1, ke^{jφ}]ᵀ, k = |I_out|/|I_in|, φ = arg I_out − arg I_in. 식 (1.10) E_θ = −jωI₀[𝒜_in + ke^{jφ}𝒜_out]. 단위 전류 응답의 위상 ψ(r, z)는 6장 식 (6.5).""")
    return s


def d_knob2():
    s = frame('전체 크기는 총 공급 전력으로 정한다', '제어 노브 2  ·  왜 I_{0} 대신 P_{tot}인가',
              'k·φ는 분포의 구성을, P_{tot}은 전체 구동 규모를 정하지만 밀도 응답에서는 결합할 수 있다.',
              '[유도] 2포트 페이저 전력. 전력 균형: 정진욱 (2026) §2.4 식 (2.66)–(2.68).')
    y = rows(s, [dict(eq='e1_11', pt=16, lab='2포트 단자', num='(1.11)'),
                 dict(eq='e1_12', pt=16, lab='포트 전력', num='(1.12)'),
                 dict(eq='e1_13', pt=16, lab='(1.9) 대입', num='(1.13)')], y=1.45, gap=0.1)
    tb(s, 0.55, y, 8.9, 0.5, '분모가 양수이고 k, φ를 구동기에서 실현할 수 있으면 전력으로 I_{0}를 정할 수 있다. Z가 n(r, z)에 의존하므로 실제 전류도 플라즈마 상태와 결합된다.', size=12.5, color=TEXT)
    rows(s, [dict(eq='ploss', pt=15, lab='전력의 세 위치'),
             dict(eq='e1_14', pt=16, lab='플라즈마 관점', num='(1.14)')], y=y + 0.62, gap=0.1)
    reg(s, 'd_knob2', 50, """상대 관계만 정하면 전류의 전체 크기가 정해지지 않으므로 세 번째 조건이 필요합니다. 코일 2포트의 임피던스 행렬로 포트 전력을 쓰고 앞의 전류 페이저를 대입하면, 포트 전력이 I_0 제곱과 aᴴZa의 실수부의 곱이 됩니다. 그래서 전력을 지정하면 I_0가 정해집니다. 다만 Z가 밀도에 의존하므로 전류도 플라즈마와 결합됩니다. 또 발전기 전력, 코일 단자 전력, 플라즈마 흡수 전력은 서로 다르고, 효율을 상수로 두지 않습니다. 플라즈마 쪽에서 보면 흡수 전력은 쌍당 비용 곱하기 손실률이므로 주로 밀도 레벨을 정합니다.""",
        """식 (1.13) P_port = (I₀²/2)Re[aᴴZ(n)a], I₀ = √(2P_port/Re(aᴴZa)). P_tot = P_match,loss + P_port, P_port = P_coil,loss + P_abs. 식 (1.14) P_abs = eε_T Ṅ_loss는 4장 식 (4.10)과 같다. 세 노브가 실제로 결합하는 정도는 9장의 J 비대각 원소로 나타난다.""")
    return s


def c_knob():
    s = frame('두 코일 전류는 세 개의 실질 자유도를 준다', '제어 노브  ·  상대 진폭 k, 상대 위상 φ, 총 전력 P_{tot}',
              'k·φ는 흡수 분포의 구성을, P_{tot}은 전체 구동 규모를 정한다.',
              '[유도] 공통 위상 제거와 2포트 페이저 전력. 전류 페이저 (1.9)와 전력의 세 위치: 부록 A4–A5.')
    put(s, 'e1_10', 0.55, 1.5, 20, center_w=8.9)
    xs = [0.5, 3.55, 6.6]
    for x, (t, d, c) in zip(xs, [('상대 진폭 k = |I_{out}|/|I_{in}|', '두 코일의 상대 가열 기여', BLUE),
                                 ('상대 위상 φ', '겹친 전기장의 간섭(보강·상쇄)', ORANGE_D),
                                 ('총 전력 P_{tot}', '전체 구동 규모, I_{0}를 정함', NAVY)]):
        box(s, x, 2.38, 2.9, 0.95, fill=None, line=LINE, radius=None, margin=0.1, anchor='m', align='c', paras=[
            {'t': t, 'bold': True, 'color': c, 'size': 13.5, 'after': 3}, {'t': d, 'size': 13}], color=TEXT)
        box(s, x, 2.38, 2.9, 0.04, fill=c, radius=None)
    head(s, 0.55, 3.55, 8.9, '전력이 전류 크기를 정한다')
    put(s, 'e1_13', 0.75, 3.95, 18)
    tb(s, 0.55, 4.9, 8.9, 0.85, [
        {'t': 'Z가 밀도에 의존하므로 실제 전류도 플라즈마 상태와 결합된다.', 'bullet': True, 'after': 3},
        {'t': '발전기의 P_{tot}, 코일 단자의 P_{port}, 플라즈마의 P_{abs}는 서로 다르며 효율을 상수로 두지 않는다.', 'bullet': True}],
       size=13, color=TEXT)
    reg(s, 'c_knob', 55, """두 코일을 독립 전원으로 구동하면 전기장은 이렇게 쓸 수 있습니다. 공통 위상을 지우고 나면 상대 진폭 k는 두 코일의 상대 가열 기여를, 상대 위상 φ는 겹친 장의 간섭을 바꿉니다. 그런데 상대 관계만으로는 전류의 전체 크기가 정해지지 않습니다. 그래서 세 번째 노브로 총 전력을 씁니다. 포트 전력은 I_0 제곱에 비례하므로 전력을 지정하면 I_0가 정해집니다. 정리하면 k와 φ는 분포의 구성을, 전력은 전체 규모를 맡습니다. 다만 개념적으로는 나뉘어도 실제 밀도 응답에서는 서로 얽힐 수 있고, 그 얽힘을 마지막에 행렬로 판정하겠습니다.""",
        """식 (1.10) E_θ = −jωI₀[𝒜_in + ke^{jφ}𝒜_out], 식 (1.13) P_port = (I₀²/2)Re[aᴴZ(n)a], a = [1, ke^{jφ}]ᵀ. 'k, φ와 P_tot은 완전히 독립인가'라는 질문의 답: 개념적으로는 분리되지만 Z(n)과 밀도 되먹임으로 결합한다. 이 결합은 9장 J의 비대각 원소 ∂_k n̄_w, ∂_P ρ로 나타난다(본편 18쪽). 전류 페이저 식 (1.9)와 P_tot = P_match,loss + P_port, P_port = P_coil,loss + P_abs는 부록 A4–A5.""")
    return s


# ================================================================== 2·3장
def d_assume(part):
    rws = ASSUME[:7] if part == 1 else ASSUME[7:]
    s = frame('기본 모델의 가정과 적용 범위' + (' (1/2)' if part == 1 else ' (2/2)'),
              '모델링 가정  ·  ' + ('기하, 전하, 시간, 장, 전자' if part == 1 else '반응, 수송, 벽, 생성, 운전'),
              'T_{e}는 대표 상수, G는 흡수 분포를 따른다는 두 가정이 이후 식의 출발점이다.',
              '구현·검증되지 않은 세부는 문서에서 "계획" 또는 "검증 필요"로 표기했다.')
    y = assume_table(s, rws, rh=0.44 if part == 1 else 0.4)
    if part == 2:
        note_box(s, 0.5, 5.15, 9.0, 0.65, '중요한 한계', 'T_{e}를 상수로 두면서 G ∝ p_{abs}(r, z)로 두는 혼합 모델이다. 전자 에너지 수송까지 자기일관적으로 푼 것이 아니다.', fill=ORANGE_L, size=12.5)
    reg(s, f'd_assume{part}', 35,
        """이제 식을 세우기 전에 가정을 모아 두겠습니다. 장치는 원통형 축대칭으로 반경과 높이의 2D 벌크만 보고, 준중성과 단일 주파수 정상 조화장을 가정합니다. 장은 방위각 벡터 퍼텐셜 중심의 준정적 유도장이고, 전자 응답은 충돌 주파수 기반의 복소 전도도로 씁니다. 전자온도는 0D에서 구한 대표값 하나를 씁니다.""" if part == 1 else
        """나머지 가정입니다. 수송은 양극성 확산, 손실은 벽 손실만 두고, 벽은 Bohm 유출을 Robin 조건으로 근사합니다. 이온 생성의 기본안은 흡수 전력을 따른다는 것입니다. 여기서 가장 중요한 한계는 전자온도를 상수로 두면서 생성은 흡수 분포를 따르게 한 혼합 모델이라는 점입니다. 이 한계가 7장에서 다시 문제가 됩니다.""",
        """문서 2장 표 전체. 특히 '대표 T_e'와 'G ∝ p_abs'의 조합이 7장(국소 생성 대 균일 EEDF)과 9장(J의 형상 행)의 핵심 쟁점이다.""")
    return s


def c_assume():
    s = frame('기본 모델의 가정과 적용 범위', '모델링 가정  ·  2D 축대칭 벌크, 대표 T_{e}, 양극성 확산',
              'T_{e}는 대표 상수, G는 흡수 분포를 따른다는 두 가정이 이후 식의 출발점이다.',
              '전체 15항목: 부록 A6–A7. 구현·검증되지 않은 세부는 "계획" 또는 "검증 필요"로 표기했다.')
    pick = [0, 2, 3, 5, 6, 9, 11, 12]
    assume_table(s, [ASSUME[i] for i in pick], rh=0.4)
    note_box(s, 0.5, 5.12, 9.0, 0.68, '중요한 한계', 'T_{e}를 상수로 두면서 G ∝ p_{abs}(r, z)로 두는 혼합 모델이다. 전자 에너지 수송까지 자기일관적으로 푼 것이 아니다.', fill=ORANGE_L, size=13)
    reg(s, 'c_assume', 45, """여기서 이 구조를 식으로 옮기기 위한 가정을 정리하겠습니다. 원통형 축대칭의 2D 벌크만 보고, 준중성과 단일 주파수 정상 조화장을 가정합니다. 전자는 복소 전도도로, 입자 수송은 양극성 확산으로, 벽은 Bohm 유출로 다룹니다. 이 가운데 두 가지를 기억해 주십시오. 전자온도는 0D에서 구한 대표값 하나이고, 이온 생성은 흡수 분포를 따른다고 둡니다. 이 둘을 함께 쓰는 것이 저희 모델의 가장 중요한 한계이고, 뒤에서 이 가정을 어디까지 믿을 수 있는지 다시 확인하겠습니다.""",
        """문서 2장 표에서 8항목을 골랐다(방전 기체, 전자기장, EEDF·반응계수, 중성 기체, 입자 손실, 운전·제어, 최종 관심값은 부록 A6–A7). 이 혼합 모델의 타당 범위는 7장 식 (7.17)·(7.19)의 두 극한으로 확인한다(본편 15쪽).""")
    return s


def couplings(with_eq):
    s = frame('최종 밀도 형상은 세 물리 과정이 함께 정한다', '모델의 구조  ·  전자기 결합, 전자 에너지 수송, 입자 확산·벽 손실',
              '흡수 분포를 바꿀 수 있다는 것과 밀도 형상을 바꿀 수 있다는 것은 다른 질문이다.',
              '개념도: 문서 그림 4. 각 화살표를 지배하는 식은 4–8장에서 유도한다.')
    xs, w = coupling_diagram(s, 1.5)
    txt = [('두 장의 합은 흡수에서 간섭항이 된다', '흡수는 |E_{θ}|²를 따르므로 두 장의 복소 위상 관계가 중요하다.'),
           ('가열 위치와 이온화 위치는 다를 수 있다', '흡수된 에너지는 전자의 이동·충돌로 퍼진다.'),
           ('생성 위치와 최종 밀도는 다르다', '생성 입자는 함께 확산하고 벽에서 손실된다.')]
    for x, (a, b) in zip(xs, txt):
        tb(s, x, 2.97, w, 1.2, [{'t': a, 'bold': True, 'color': NAVY, 'after': 4, 'size': 13.5}, {'t': b, 'size': 13}], color=TEXT)
    if with_eq:
        rows(s, [dict(eq='e3_1', pt=16, lab='전자기 결합', num='(3.1)')], y=4.2)
        yb = 4.85
    else:
        yb = 4.5
    note_box(s, 0.5, yb, 9.0, 5.8 - yb, '연구 문제의 정확한 표현',
             '전력 흡수 분포의 형상 제어 가능성과, 전자 에너지·입자 수송을 거친 최종 밀도 형상의 제어 가능성은 다른 질문이다.', size=13.5)
    reg(s, 'couplings', 50 if not with_eq else 45, """가정 위에서 모델의 뼈대를 그리면 이렇습니다. 코일 전류가 장과 흡수 분포를 만드는 전자기 결합, 흡수된 에너지가 이온 생성으로 옮겨 가는 전자 에너지 수송, 생성된 입자가 확산하고 벽에서 사라지는 과정입니다. 그리고 밀도가 다시 전도도를 바꿔 장을 바꾸는 되먹임이 있습니다. 이 그림이 말하는 것은 흡수 분포를 바꿀 수 있다는 것과 최종 밀도 형상을 바꿀 수 있다는 것이 다른 질문이라는 점입니다. 이제 이 화살표들을 하나씩 식으로 따라가겠습니다. 출발점은 형상이 없는 0D 균형입니다.""",
        """문서 3장. 식 (3.1) p_abs = ½Re(σ_p)|E_θ|², |E_θ|² ∝ |𝒜_in + ke^{jφ}𝒜_out|²는 5장 (5.6)과 6장 (6.5)에서 다시 유도한다. 되먹임 고리는 6장 식 (6.13).""")
    return s


# ================================================================== 4장
def d_0d1():
    s = frame('0D 입자 균형: 체적 생성 = 벽 손실', '0D 글로벌 모델 1  ·  이온화율과 Bohm 유출',
              '체적 생성과 벽 손실의 균형이 0D 모델의 첫 식이다.', '정진욱 (2026) §2.4 pp.133–138, 식 (2.69)–(2.70); Bohm 속도 §1.7.1 식 (1.42).')
    rows(s, [dict(eq='e4_1', pt=18, lab='이온화율', num='(4.1)'),
             dict(eq='e4_2', pt=17, lab='입자 수 보존', num='(4.2)'),
             dict(eq='e4_3', pt=18, lab='Bohm 속도', num='(4.3)')], y=1.6, gap=0.25)
    bullets(s, 0.55, 4.25, 8.9, 1.5, [
        'Ar의 대표적인 단일 단계 이온화 e + Ar → 2e + Ar⁺, 대표 전자온도의 반응속도계수 K_{iz}(T_{e})',
        '단일 양이온과 단순 Bohm 근사. T_{e}는 eV 단위의 수치로 쓴다.'], size=13.5)
    reg(s, 'd_0d1', 35, """0D 모델은 챔버 전체의 균형입니다. 체적 이온화율은 전자 밀도, 중성 밀도, 이온화 반응속도계수의 곱이고, 이것을 체적에 적분한 생성률이 벽 면적에서 Bohm 속도로 빠져나가는 손실률과 같다고 놓습니다.""",
        """정진욱 (2026) §2.4 식 (2.69)–(2.70) 입자 균형, §1.7.1 p.50 식 (1.42) Bohm 기준. 반응 계수: L&L (2005) 표 3.3 피팅식.""")
    return s


def d_0d2():
    s = frame('밀도 기준을 맞추면 전자온도 조건이 나온다', '0D 글로벌 모델 2  ·  기준 밀도와 유효 면적',
              '입자 균형에서 밀도가 약분되어 대표 전자온도가 정해진다.', '정진욱 (2026) §2.4 식 (2.70)–(2.73). 기준 밀도 n_{*}와 h_{V}는 문서의 기준 정정.')
    y = rows(s, [dict(eq='e4_4', pt=16, lab='밀도 기준', num='(4.4)'),
                 dict(eq='e4_5', pt=16, lab='유효 면적', num='(4.5)'),
                 dict(eq='e4_6', pt=15, lab='벽/중심 비', num='(4.6)'),
                 dict(eq='e4_7', pt=18, lab='n_{*} 약분', num='(4.7)')], y=1.45, gap=0.12)
    bullets(s, 0.55, y + 0.05, 8.9, 5.82 - y, [
        '왼쪽은 T_{e}에 크게 의존하고, 오른쪽은 n_{g}·기하·손실 형상 계수가 정한다 → T_{e}를 먼저 구한다.',
        '전력이 h 인자, 중성 밀도, EEDF, 가스 온도를 바꾸면 조건도 달라진다. T_{e}가 전력과 무관하다는 법칙은 아니다.'], size=13)
    reg(s, 'd_0d2', 45, """밀도의 기준을 맞춰야 합니다. 중심 기준 밀도 n_*로 벽 앞 밀도를 h 인자로 쓰면 유효 면적이 나오고, 체적 생성에는 체적 평균과의 비 h_V가 들어갑니다. T_e, n_g, K_iz를 대표 상수로 두면 양변의 n_*가 약분되어 K_iz/u_B가 기하와 중성 밀도로만 정해집니다. 왼쪽은 T_e에 매우 민감하므로 이 식이 대표 전자온도를 정합니다. 다만 모든 ICP에서 T_e가 전력과 무관하다는 법칙은 아닙니다.""",
        """정진욱 (2026) §2.4 식 (2.70) d_eff, (2.71)–(2.73) h_L, h_R, A_eff. 문서의 기준 정정: 벽 손실을 중심 기준 n_*로 쓰면 체적 생성에 h_V가 필요하다. 10 mTorr 예시(저장소 sim/theory_note_check.py): T_e 2.73 eV.""")
    return s


def d_0d3():
    s = frame('전력 균형이 밀도 규모를 정한다', '0D 글로벌 모델 3  ·  이온 쌍의 에너지 비용',
              '0D는 대표 값과 계수를 주지만, 중심·가장자리 형상은 주지 않는다.', '정진욱 (2026) §2.4 식 (2.63)–(2.68). 벽 손실 계수는 쉬스 조건·벽 전위 가정에 따른다.')
    y = rows(s, [dict(eq='e4_8', pt=17, lab='충돌 비용', num='(4.8)'),
                 dict(eq='e4_9', pt=17, lab='전역 비용', num='(4.9)'),
                 dict(eq='e4_10', pt=17, lab='전력 균형', num='(4.10)'),
                 dict(eq='e4_11', pt=19, lab='기준 밀도', num='(4.11)')], y=1.45, gap=0.14)
    bullets(s, 0.55, y + 0.05, 8.9, 5.82 - y, [
        'ε는 eV/쌍 단위이므로 J로 바꿀 때 e를 곱한다.',
        'T_{e}, ε_{T}, u_{B}, A_{eff}가 크게 변하지 않으면 n_{*}는 P_{abs}에 비례한다. 최종 n(r, z)는 2D 수송과 경계조건이 정한다.'], size=13)
    reg(s, 'd_0d3', 45, """이온 하나를 만드는 데는 이온화 문턱보다 많은 에너지가 듭니다. 들뜸과 탄성 손실을 더한 것이 충돌 비용 ε_c이고, 벽으로 빠지는 전자와 이온의 에너지를 더한 것이 전역 비용 ε_T입니다. 흡수 전력은 ε_T 곱하기 벽 손실률이므로, 기준 밀도는 흡수 전력에 비례합니다. 그런데 이 식에는 r도 z도 없습니다. 0D는 레벨은 주지만 형상은 주지 않습니다.""",
        """정진욱 (2026) §2.4 식 (2.63) ε_c, (2.64)–(2.65) ε_T = ε_c + 2T_e + 5.2T_e(교재 근사), (2.66)–(2.68) 전력 균형. 10 mTorr 예시: ε_c 70 V, ε_T 90 V, n₀ 8.3×10¹⁶ m⁻³(흡수 225 W 가정).""")
    return s


def c_0d():
    s = frame('0D 균형은 전자온도와 밀도 규모를 정한다', '0D 글로벌 모델  ·  입자 균형과 전력 균형',
              '0D는 대표 값과 계수를 주지만, 중심·가장자리 형상은 주지 않는다.',
              '정진욱 (2026) §2.4 pp.133–138, 식 (2.63)–(2.73). 유도 (4.1)–(4.10): 부록 A8–A10.')
    for x, t, sub, name, pt in ((0.5, '입자 균형', '체적 생성 = 벽 손실 → n_{*}가 약분된다', 'e4_7', 17),
                                (5.1, '전력 균형', '흡수 전력 = 쌍당 비용 × 벽 손실률', 'e4_11', 19)):
        box(s, x, 1.5, 4.4, 2.35, fill=None, line=LINE, radius=None)
        box(s, x, 1.5, 4.4, 0.04, fill=NAVY, radius=None)
        head(s, x + 0.12, 1.6, 4.1, t, size=15)
        label(s, x + 0.12, 1.98, 4.2, sub, size=13, color=TEXT)
        w, h = eqsize(name, pt)
        put(s, name, x + 0.1, 2.5, pt, maxw=4.2, center_w=4.2)
    label(s, 0.62, 3.42, 4.2, '→ 대표 전자온도 T_{e}를 정한다', size=13.5, color=NAVY, bold=True)
    label(s, 5.22, 3.42, 4.2, '→ 밀도 규모는 P_{abs}에 비례한다', size=13.5, color=NAVY, bold=True)
    tb(s, 0.55, 4.1, 8.9, 1.7, [
        {'t': 'ε_{T} = ε_{c} + ε_{e,wall} + ε_{i,wall}: 충돌 비용에 벽으로 나가는 전자·이온 에너지를 더한 전역 비용', 'bullet': True, 'after': 5},
        {'t': '왼쪽 K_{iz}/u_{B}는 T_{e}에 크게 의존하고 오른쪽은 기하·중성 밀도가 정하므로 T_{e}를 먼저 구한다. 전력과 무관하다는 법칙은 아니다.', 'bullet': True, 'after': 5},
        {'t': '두 식 어디에도 r, z가 없다. 최종 n(r, z)는 2D 수송과 경계조건이 정한다.', 'bullet': True}], size=13.5, color=TEXT)
    reg(s, 'c_0d', 60, """첫 단계는 챔버 전체의 균형입니다. 체적에서 생기는 이온과 벽으로 빠지는 이온이 같다고 놓으면 양변의 밀도가 약분되어, 이 식은 대표 전자온도를 정하는 조건이 됩니다. 다음으로 흡수 전력이 이온 쌍 하나의 전역 비용 ε_T와 벽 손실률의 곱과 같다고 놓으면 기준 밀도가 나오고, 흡수 전력에 비례합니다. 그런데 두 식 어디에도 r과 z가 없습니다. 0D는 레벨은 정해 주지만 중앙과 가장자리의 형상은 말해 주지 않습니다. 그렇다면 흡수 전력은 공간적으로 어떻게 분포할까요?""",
        """정진욱 (2026) §2.4: 식 (2.63) ε_c, (2.64)–(2.65) ε_T, (2.66)–(2.68) 전력 균형, (2.69)–(2.70) 입자 균형과 d_eff, (2.71)–(2.73) h_L, h_R, A_eff. 문서 식 (4.7) K_iz/u_B = A_eff,*/(h_V n_g V), (4.11) n_* = P_abs/(eε_T u_B A_eff,*). 10 mTorr 예시: T_e 2.73 eV, ε_T 90 V, n₀ 8.3×10¹⁶ m⁻³(저장소 sim/theory_note_check.py, 흡수 225 W 가정).""")
    return s


# ================================================================== 5장
def d_em1():
    s = frame('전자 운동 방정식에서 복소 전도도가 나온다', '전자기 결합 1  ·  충돌이 있는 전자의 RF 응답',
              '전도도는 밀도에 비례하고, 충돌과 주파수가 그 위상을 정한다.', 'L&L (2005) §4.2. 등방성 국소 유체 전도도 모델.')
    rows(s, [dict(eq='e5_1', pt=18, lab='운동 방정식', num='(5.1)'),
             dict(eq='phasor', pt=16, lab='페이저'),
             dict(eq='e5_2', pt=18, lab='대입', num='(5.2)'),
             dict(eq='e5_3', pt=18, lab='전류 밀도', num='(5.3)'),
             dict(eq='e5_4', pt=17, lab='복소 전도도', num='(5.4)')], y=1.45, gap=0.13)
    tb(s, 0.55, 5.22, 8.9, 0.55, 'EEDF나 비국소 RF 전도도 자체를 계산한 것은 아니다.', size=13, color=MUTED)
    reg(s, 'd_em1', 40, """흡수 분포를 쓰려면 먼저 전자가 장에 어떻게 반응하는지 알아야 합니다. 전자가 중성 기체와 충돌 주파수 ν_m으로 운동량을 잃는다고 두고 페이저를 대입하면 전자 속도가 장에 비례하고, 전류 밀도에서 복소 전도도가 나옵니다. 전도도는 밀도에 비례하고, 실수부는 충돌과 주파수의 비가 정합니다.""",
        """L&L (2005) §4.2: σ_p = e²n/(m(ν_m + jω)). 교재에는 이 유도가 없어 L&L을 인용한다. 10 mTorr: ν_m = 3.6×10⁷ s⁻¹, ω = 8.5×10⁷ s⁻¹.""")
    return s


def d_em2():
    s = frame('흡수 전력은 전도도와 유도장이 함께 정한다', '전자기 결합 2  ·  흡수 전력 밀도와 2D 유도장 방정식',
              '전도도는 밀도를 따르므로, 흡수 분포는 플라즈마 상태와 함께 바뀐다.',
              '[유도] 맥스웰 방정식의 축대칭 준정적 형태. δ: 정진욱 (2026) §2.3.4 식 (2.53).')
    y = rows(s, [dict(eq='e5_5', pt=17, lab='주기 평균', num='(5.5)'),
                 dict(eq='e5_6', pt=18, lab='흡수 전력', num='(5.6)'),
                 dict(eq='e5_7', pt=15.5, lab='2D 유도장', num='(5.7)'),
                 dict(eq='e5_8', pt=16, lab='표피 침투', num='(5.8)')], y=1.45, gap=0.14)
    bullets(s, 0.55, y + 0.02, 8.9, 5.82 - y, [
        'n_{e} → σ_{p} → 장 차폐 → E_{θ} → p_{abs}: p_{abs} ∝ n_{e} 같은 단순 비례로는 되먹임을 설명할 수 없다.',
        '표피 침투는 창에서 내려가는 깊이 방향 효과이고, 두 코일 장의 중첩은 반경 방향 효과다.'], size=13)
    reg(s, 'd_em2', 45, """전류와 장의 주기 평균 곱이 흡수 전력이므로, 흡수 전력 밀도는 전도도의 실수부 곱하기 장의 제곱입니다. 그런데 장은 다시 전도도를 포함한 2D 유도장 방정식의 해입니다. 밀도가 전도도를 바꾸고, 전도도가 장의 차폐를 바꾸고, 장이 흡수를 바꿉니다. 표피 침투는 창에서 아래로 내려가는 깊이 방향의 효과이고, 두 코일의 반경 방향 중첩과는 다른 현상입니다.""",
        """식 (5.7): B = ∇×A, Ẽ_θ = −jωA_θ, 창·진공 영역에서는 σ_p = 0. 정진욱 (2026) §2.3.4 pp.122–123 식 (2.53): δ_p = c/ω_pe(저압). 10 mTorr, n ≈ 8×10¹⁶ m⁻³에서 일반 분산식 δ ≈ 2.0 cm.""")
    return s


def c_em():
    s = frame('흡수 전력은 전도도와 유도장이 함께 정한다', '전자기 결합  ·  복소 전도도, 흡수 전력, 2D 유도장 방정식',
              '전도도는 밀도를 따르므로, 흡수 분포는 플라즈마 상태와 함께 바뀐다.',
              'σ_{p}: L&L (2005) §4.2. (5.7): 맥스웰 방정식의 축대칭 준정적 형태 [유도]. 유도와 표피 깊이: 부록 A11–A12.')
    y = rows(s, [dict(eq='e5_4', pt=18, lab='복소 전도도', num='(5.4)'),
                 dict(eq='e5_6', pt=19, lab='흡수 전력', num='(5.6)'),
                 dict(eq='e5_7', pt=16, lab='2D 유도장', num='(5.7)')], y=1.5, gap=0.22)
    tb(s, 0.55, y + 0.08, 8.9, 5.8 - y, [
        {'t': '밀도가 전도도를 바꾸고, 전도도가 장의 차폐를 바꾸고, 장이 다시 흡수를 바꾼다. p_{abs} ∝ n_{e} 같은 단순 비례로는 이 되먹임을 설명할 수 없다.', 'bullet': True, 'after': 6},
        {'t': '표피 침투(δ ∼ c/ω_{pe})는 창에서 내려가는 **깊이 방향**, 두 코일 장의 중첩은 **반경 방향** 효과다.', 'bullet': True}],
       size=13.5, color=TEXT)
    reg(s, 'c_em', 60, """0D가 주지 못한 공간 분포는 장에서 시작합니다. 전자가 충돌하며 장에 반응한다고 두면 복소 전도도가 나오고, 이것은 밀도에 비례합니다. 흡수 전력 밀도는 전도도의 실수부와 장의 제곱의 곱입니다. 그런데 그 장은 전도도를 포함한 2D 유도장 방정식의 해입니다. 그래서 밀도가 전도도를, 전도도가 장의 차폐를, 장이 흡수를 바꾸는 고리가 생깁니다. 하나 구분할 점은 표피 침투는 창 아래로 내려가는 깊이 방향의 효과이고, 저희가 조절하려는 것은 반경 방향의 분포라는 것입니다. 그 반경 분포를 두 코일이 어떻게 만드는지 보겠습니다.""",
        """L&L (2005) §4.2: σ_p = n e²/(m(ν_m + jω)), Re σ_p = ne²ν_m/(m(ν_m² + ω²)). 운동 방정식에서의 유도 (5.1)–(5.3), 주기 평균 (5.5), 표피 깊이 (5.8)은 부록 A11–A12. 정진욱 (2026) §2.3.4 식 (2.53): 저압 δ_p = c/ω_pe. 10 mTorr, n ≈ 8×10¹⁶ m⁻³에서 δ ≈ 2.0 cm(일반 분산식).""")
    return s


# ================================================================== 6장
def d_tc1(with31=False):
    s = frame('두 코일 장의 제곱은 세 항으로 전개된다', '두 코일의 장 중첩 1  ·  단위 전류 해의 중첩',
              '흡수 전력의 세 번째 항이 두 코일의 간섭항이다.', '[유도] 한 순간의 고정된 σ_{p}에서 식 (5.7)은 코일 전류에 선형이다.')
    items = []
    if with31:
        items.append(dict(eq='e3_1', pt=15.5, lab='출발 (3.1)', num='(3.1)'))
    items += [dict(eq='e6_1', pt=17, lab='벡터 퍼텐셜', num='(6.1)'),
              dict(eq='e6_2', pt=17, lab='유도장', num='(6.2)'),
              dict(eq='e6_3', pt=15.5, lab='제곱', num='(6.3)'),
              dict(eq='e6_4', pt=15.5, lab='', num='(6.4)'),
              dict(eq='polar', pt=15, lab='위상 표기')]
    rows(s, items, y=1.45, gap=0.12)
    reg(s, 'd_tc1', 35, """전도도를 한 순간 고정하면 유도장 방정식은 코일 전류에 선형이므로, 두 코일에 각각 단위 전류를 흘린 해를 더하면 됩니다. 장의 제곱을 전개하면 안쪽 코일 항, 바깥 코일 항, 그리고 두 장의 곱으로 된 간섭항이 나옵니다. 각 단위 응답을 크기와 위상으로 쓰고 두 위상의 차를 ψ로 정의합니다.""",
        """식 (6.3)–(6.4) 전개: |a + b|² = |a|² + |b|² + 2Re(ab*). ψ(r, z) = α_out − α_in. 진공장에서는 ψ = 0이고 플라즈마에서는 위치에 따라 회전한다(10 mTorr 1D 분산식에서 δ당 약 12°).""")
    return s


def interf(core):
    title = '두 코일 장의 합은 흡수에서 간섭항을 만든다'
    s = frame(title, '두 코일의 장 중첩' + ('' if core else ' 2') + '  ·  상대 진폭과 위상 간섭',
              '간섭은 두 장이 함께 큰 곳에서만 작동하고, 그 위상은 φ + ψ(r, z)가 정한다.',
              '[유도] 식 (6.1)–(6.4)의 전개' + (': 부록 A13.' if core else '.') + ' 그림은 ψ = 0, k = 1을 가정한 개념 곡선.')
    rows(s, [dict(eq='e6_5', pt=17 if core else 16.5, lab=None, num='(6.5)', indent=0.05)], y=1.5)
    lib.pic(s, R + '/fig/interf.png', 5.2, 2.35, w=4.3)
    bullets(s, 0.55, 2.4, 4.5, 1.75, [
        'k: 두 코일 항의 상대 크기',
        'φ + ψ(r, z): 겹침 영역의 보강·상쇄',
        'ψ는 플라즈마 밀도와 위치에 따라 달라진다.'], size=13.5)
    box(s, 0.5, 4.25, 4.55, 1.55, fill=ORANGE_L, radius=None, margin=0.1)
    head(s, 0.62, 4.32, 4.3, '완전 상쇄에는 두 조건이 동시에 필요', size=13.5, color=ORANGE_D)
    put(s, 'cancel', 0.62, 4.72, 14.5, maxw=4.3)
    label(s, 0.62, 5.2, 4.35, 'φ = π로 두는 것만으로 최적 분리가 보장되지 않는다.', size=12.5, color=TEXT, h=0.5)
    key = 'c_interf' if core else 'd_tc2'
    reg(s, key, 55 if core else 45, """두 코일이 있으면 장은 두 단위 응답의 합입니다. 흡수 전력은 장의 제곱을 따르므로 펼치면 세 항이 됩니다. 안쪽 코일 항, k 제곱이 붙은 바깥 코일 항, 그리고 두 장의 곱에 cos(φ + ψ)가 붙은 간섭항입니다. 그림처럼 간섭항은 두 장이 함께 큰 겹침 영역에서만 의미가 있고, 위상에 따라 그곳의 흡수를 키우거나 줄입니다. 그런데 이 위상에는 우리가 정하는 φ뿐 아니라 플라즈마가 정하는 ψ도 들어 있습니다. 그래서 어느 위치를 완전히 상쇄하려면 진폭과 위상 조건이 동시에 맞아야 하고, φ를 π로 두는 것만으로 최적 분리가 보장되지는 않습니다.""",
        """식 (6.5): |E_θ|²/(ω²I₀²) = |𝒜_in|² + k²|𝒜_out|² + 2k|𝒜_in||𝒜_out|cos[φ + ψ(r, z)]. 완전 상쇄: |𝒜_in| = k|𝒜_out|이고 φ + ψ = π (mod 2π). 개념 그림은 ψ = 0, k = 1, 단위 응답을 6·15 cm 중심 가우스로 둔 정성 곡선이며 계산 결과가 아니다. 10 mTorr 1D 분산식에서 ψ는 깊이 δ당 약 12° 회전.""")
    return s


def d_tc3():
    s = frame('변압기 모델에서 플라즈마는 저항성 부하로 보인다', '두 코일의 장 중첩 3  ·  반사 임피던스',
              '플라즈마에 전달된 전력은 코일 포트에서 반사 임피던스의 실수부로 보인다.', '정진욱 (2026) §2.3.4 pp.123–125, 식 (2.54)–(2.57).')
    y = rows(s, [dict(eq='e6_6', pt=17, lab='1차 회로', num='(6.6)'),
                 dict(eq='e6_7', pt=17, lab='2차 회로', num='(6.7)'),
                 dict(eq='e6_8', pt=17, lab='I_{p} 소거', num='(6.8)'),
                 dict(eq='e6_9', pt=17, lab='입력 임피던스', num='(6.9)'),
                 dict(eq='e6_10', pt=17, lab='실수부', num='(6.10)')], y=1.45, gap=0.13)
    tb(s, 0.55, y + 0.02, 8.9, 5.8 - y, '방위각 방향 플라즈마 유도전류를 등가 2차 회로로 보는 단순 모델이다. 연속 플라즈마가 실제 권선이라는 뜻은 아니다.', size=13, color=MUTED)
    reg(s, 'd_tc3', 40, """코일과 플라즈마를 변압기로 보면, 코일이 1차 회로이고 방위각 방향의 플라즈마 전류가 2차 회로입니다. 두 번째 식에서 플라즈마 전류를 구해 첫 번째 식에 넣으면 코일 입력 임피던스에 ω²M²/Z_p가 더해집니다. 이 반사 임피던스의 실수부는 양수이므로, 플라즈마에 전달된 전력은 코일 포트에서 저항성 부하로 관측됩니다.""",
        """정진욱 (2026) §2.3.4 pp.123–125, 식 (2.54)–(2.57): 변압기 등가모델, R_p, L_p(플라즈마 인덕턴스), L_g(기하 인덕턴스). 부호 관례는 권선 방향과 상호인덕턴스 정의에 따른다.""")
    return s


def d_tc4():
    s = frame('코일 포트와 밀도는 서로를 바꾼다', '두 코일의 장 중첩 4  ·  임피던스 행렬과 자기일관 되먹임',
              'k와 φ는 장을 바꾸지만, 플라즈마가 바뀌면 장과 포트 전류도 함께 바뀐다.',
              '[유도] 식 (6.9)의 두 코일 확장. 등가회로이므로 공간 분포까지 나타내지는 않는다.')
    y = rows(s, [dict(eq='e6_11', pt=16, lab='단자 관계', num='(6.11)'),
                 dict(eq='e6_12', pt=17, lab='교차 성분', num='(6.12)'),
                 dict(eq='e6_13', pt=14, lab='되먹임 고리', above=True, num='(6.13)')], y=1.45, gap=0.14)
    bullets(s, 0.55, y + 0.02, 8.9, 5.8 - y, [
        '전압 구동: 한쪽 포트의 조건 변화가 다른 쪽 전류를 바꾼다. 전류 구동: 요구 전압과 총 전력이 변한다.',
        '되먹임이 항상 양은 아니다. 밀도가 늘면 흡수 증가와 표피 차폐 증가가 경쟁한다.',
        'k는 두 코일의 흡수 전력 비율이 아니다.'], size=13)
    reg(s, 'd_tc4', 45, """두 코일이면 이 관계가 2×2 임피던스 행렬이 됩니다. 비대각 성분은 두 코일의 직접 자기 결합과 공유하는 플라즈마를 매개로 한 결합을 나타냅니다. 그래서 한쪽 조건을 바꾸면 다른 쪽 전류나 요구 전압이 바뀝니다. 또 흡수에는 전도도와 장이 함께 들어 있으므로 밀도에서 시작해 다시 밀도로 돌아오는 고리가 생깁니다. 결국 k는 두 코일의 흡수 전력 비율이 아니고, 최종 교차 영향은 따로 평가해야 합니다.""",
        """식 (6.12) Z_io ≃ jωM_io + ω²M_ipM_op/Z_p는 한 부호 관례의 등가 고리 모형. 실제 하드웨어에서는 매칭기와 포트 간 결합을 함께 고려한다. 되먹임 경쟁: 밀도 증가 → 전도도 증가(흡수 증가) 대 표피 차폐 증가·재분배.""")
    return s


def c_port():
    s = frame('코일 포트와 밀도는 서로를 바꾼다', '전자기 결합  ·  임피던스 행렬과 자기일관 되먹임',
              'k와 φ는 장을 바꾸지만, 플라즈마가 바뀌면 장과 포트 전류도 함께 바뀐다.',
              '정진욱 (2026) §2.3.4 식 (2.54)–(2.57)의 두 코일 확장 [유도]. 변압기 모델 (6.6)–(6.10), (6.12): 부록 A14–A15.')
    put(s, 'e6_11', 0.6, 1.5, 17)
    bullets(s, 4.75, 1.5, 4.75, 1.6, [
        '비대각 Z_{io}, Z_{oi}: 직접 자기 결합 + 공유 플라즈마를 매개로 한 결합',
        '한쪽 포트의 조건이 다른 쪽 전류나 요구 전압을 바꾼다.'], size=13.5)
    head(s, 0.55, 3.2, 8.9, '자기일관 되먹임')
    put(s, 'e6_13', 0.6, 3.6, 15, maxw=8.8)
    tb(s, 0.55, 4.3, 8.9, 0.55, '되먹임이 항상 양은 아니다. 밀도가 늘면 흡수 증가와 표피 차폐 증가가 경쟁한다.', size=13.5, color=TEXT)
    note_box(s, 0.5, 4.95, 9.0, 0.85, '전자기 결합의 결론', 'k는 두 코일의 흡수 전력 비율이 아니다. 최종 밀도의 교차 영향은 따로 평가해야 한다.', size=13.5)
    reg(s, 'c_port', 50, """그런데 두 코일은 서로 독립적이지 않습니다. 코일 단자 관계를 쓰면 2×2 임피던스 행렬이 되고, 비대각 성분은 두 코일의 직접 결합과 같은 플라즈마를 공유해서 생기는 결합을 나타냅니다. 그래서 한쪽을 바꾸면 다른 쪽 전류나 전압이 바뀝니다. 또 앞에서 본 것처럼 밀도가 전도도를, 전도도가 장을, 장이 흡수를 바꾸고, 흡수가 다시 밀도를 만듭니다. 그러니 k는 단순히 두 코일의 흡수 전력 비율이 아닙니다. 여기까지가 흡수 분포를 정하는 단계입니다. 이제 흡수된 에너지가 정말 그 자리에서 이온을 만드는지 보겠습니다.""",
        """식 (6.11) V = Z[n(r, z)]I. 변압기 모델: 정진욱 (2026) §2.3.4 pp.123–125 식 (2.54)–(2.57), Z_in = R_a + jωL_a + ω²M²/Z_p, Re(ω²M²/Z_p) > 0(부록 A14). 교차 성분 Z_io ≃ jωM_io + ω²M_ipM_op/Z_p(부록 A15).""")
    return s


# ================================================================== 7장
def energy_slide(core):
    s = frame('가열 위치와 이온 생성 위치는 어긋날 수 있다', '전자 에너지 수송' + ('' if core else ' 1') + '  ·  에너지 완화 길이',
              '흡수 분포의 봉우리가 곧 이온 생성의 봉우리라고 일반화할 수 없다.',
              'Kim & Chung (2020) 식 (5). 그림은 임의의 정규화 개념 곡선이며 Ar 챔버의 계산 결과가 아니다.' + (' 유도: 부록 A16.' if core else ''))
    if core:
        put(s, 'e7_2', 0.6, 1.5, 21)
        yb0 = 2.95
    else:
        yb0 = rows(s, [dict(eq='e7_1', pt=16, lab='충돌 횟수', num='(7.1)'),
                       dict(eq='e7_2', pt=16, lab='rms 변위', above=True, num='(7.2)')],
                   y=1.42, xr=5.2, labw=1.15, gap=0.04) + 0.02
    lib.pic(s, R + '/fig/energy.png', 5.3, 1.45, w=4.2)
    bullets(s, 0.55, yb0, 4.65, 4.7 - yb0, [
        '탄성 충돌로 방향만 바꾸다가 비탄성 충돌에서 에너지를 내려놓는다.',
        '두 자유행로가 압력에 반비례하면 λ_{ε} ∝ 1/p.',
        '정확한 궤적이 아니라 확산적 수송을 가정한 길이 척도다.'], size=13.5)
    note_box(s, 0.5, 4.75, 9.0, 1.05, None, '수송 길이가 길수록 가열과 생성의 차이가 커질 수 있다. 그러나 그 크기와 방향은 경계조건·EEDF·비탄성 손실에 달려 있어, **길이 비교만으로 최종 밀도의 독립성을 판정할 수는 없다**.', size=13.5)
    key = 'c_energy' if core else 'd_et1'
    reg(s, key, 55 if core else 45, """흡수된 에너지는 그 자리에 머물지 않습니다. 전자는 아르곤과 탄성 충돌할 때 방향은 자주 바꾸지만 에너지는 조금만 잃습니다. 그래서 비탄성 충돌로 에너지를 내려놓기 전까지 여러 번 방향을 바꾸며 이동하고, 그 거리가 무작위 보행으로 이 정도입니다. 두 자유행로가 압력에 반비례하면 이 길이도 압력에 반비례합니다. 그림처럼 좁게 가열되어도 이온 생성은 더 넓게 퍼질 수 있습니다. 다만 이 길이 하나로 독립 제어 여부를 판정할 수는 없습니다. 그래서 생성 모델을 어떻게 둘지가 중요해집니다.""",
        """Kim & Chung (2020) 식 (5): λ_ε = √(λ_m λ_inel/3), 15.7 eV 전자에서 1 mTorr 119 cm, 50 mTorr 2.3 cm(그림 5). 1/p 환산 10 mTorr 약 12 cm, 유체 추정 √(κ_e/α_ε) 10.3 cm(저장소 sim/theory_note_check.py). 비교 잣대: 평가 영역 사이 간격 7 cm(경계), 약 10 cm(무게중심). 문서는 특정 압력 계산을 본문에서 뺐으므로 수치는 질의응답용.""")
    return s


def d_et2():
    s = frame('전자 에너지 보존식은 흡수와 충돌 손실의 균형이다', '전자 에너지 수송 2  ·  유체 에너지 방정식',
              '흡수된 에너지는 열전도로 퍼지면서 충돌로 소모된다.', 'L&L (2005) §2.3의 유체 에너지 방정식. ε_{c}: 정진욱 (2026) 식 (2.63).')
    y = rows(s, [dict(eq='e7_3', pt=18, lab='에너지 밀도', num='(7.3)'),
                 dict(eq='e7_4', pt=17, lab='에너지 선속', num='(7.4)'),
                 dict(eq='e7_5', pt=18, lab='에너지 보존', num='(7.5)'),
                 dict(eq='e7_6', pt=18, lab='충돌 손실', num='(7.6)')], y=1.5, gap=0.18)
    bullets(s, 0.55, y + 0.05, 8.9, 5.8 - y, [
        'P_{coll}: 단위 체적당 이온화·여기·탄성 손실. 벽으로 나가는 전자 에너지는 경계항에 들어간다.',
        'ε_{c}는 체적 충돌 비용, ε_{T}는 벽 손실을 포함한 전역 비용으로 서로 다르다.'], size=13)
    reg(s, 'd_et2', 40, """이 수송을 유체 근사로 쓰면, 전자 에너지 밀도는 3/2 n T이고 에너지 선속은 대류항과 열전도항으로 이루어집니다. 정상상태 에너지 보존은 선속의 발산이 흡수 전력에서 충돌 손실을 뺀 것과 같다는 식입니다. 충돌 손실은 국소 충돌 비용 ε_c로 쓰며, 벽 손실까지 포함한 ε_T와는 다릅니다.""",
        """L&L (2005) §2.3: 거시 에너지 보존과 열선속 q = −κ∇T. κ_e ≃ (5/2)en_eD_e. 체적 적분하면 ∫p_abs dV = ∫P_coll dV + ∮q_ε·dA → 4장 식 (4.9)–(4.10)이 된다(경계항이 ε_e,wall).""")
    return s


def d_et3():
    s = frame('에너지 식을 기준상태 주위에서 선형화한다', '전자 에너지 수송 3  ·  정상상태와 손실항의 선형화',
              '선형화하면 가열 섭동과 온도 섭동이 "확산 − 손실 = −소스" 꼴로 이어진다.', '[유도] 정상상태, 엔탈피 수송항 생략, 균일 κ_{e}.')
    y = rows(s, [dict(eq='e7_7', pt=16, lab='정상상태', num='(7.7)'),
                 dict(eq='e7_8', pt=17, lab='손실 선형화', num='(7.8)'),
                 dict(eq='e7_9', pt=17, lab='손실 민감도', num='(7.9)'),
                 dict(eq='e7_10', pt=19, lab='섭동 방정식', num='(7.10)')], y=1.5, gap=0.2)
    tb(s, 0.55, y + 0.05, 8.9, 0.6, '기준상태 T_{e0}, p_{0} 주위에서 T_{e} = T_{e0} + δT_{e}, p_{abs} = p_{0} + δp. n_{e}, n_{g} 변화는 일단 고정하고 기준상태 식을 뺀다.', size=13, color=TEXT)
    reg(s, 'd_et3', 35, """에너지가 얼마나 멀리 퍼지는지 보려고 정상상태에서 대류항을 생략하고 열전도만 남깁니다. 기준상태 주위에서 온도와 흡수 전력을 조금 바꾸고 충돌 손실을 1차까지 펼치면, 손실의 온도 민감도 α_ε가 나옵니다. 기준상태 식을 빼면 온도 섭동이 가열 섭동에 대해 확산 빼기 손실 꼴의 식을 만족합니다.""",
        """식 (7.10) κ_e∇²δT_e − α_εδT_e = −δp는 차폐 푸아송(헬름홀츠형) 식이다. 그린 함수가 exp(−|x − x′|/λ)/(2λ)이므로 δT_e는 δp를 폭 λ_ε 커널로 평활화한 것과 같다(δT_e = (1/α_ε)·커널 ∗ δp).""")
    return s


def d_et4():
    s = frame('에너지 완화 길이는 열전도와 충돌 손실의 비다', '전자 에너지 수송 4  ·  유체 완화 길이',
              'κ_{e}가 크면 에너지가 더 멀리 퍼지고, α_{ε}가 크면 더 짧게 퍼진다.', '[유도] κ_{e} ≃ (5/2)en_{e}D_{e}를 대입하고 P_{coll}의 미분에서 n_{e}, n_{g}를 고정.')
    y = rows(s, [dict(eq='e7_11', pt=18, lab='가열 없는 1D', num='(7.11)'),
                 dict(eq='e7_12', pt=18, lab='해', num='(7.12)'),
                 dict(eq='e7_13', pt=19, lab='완화 길이', num='(7.13)'),
                 dict(eq='e7_14', pt=16, lab='대입', num='(7.14)')], y=1.45, gap=0.12)
    note_box(s, 0.5, max(y + 0.05, 5.0), 9.0, 0.8, '두 길이를 동의어로 쓰지 않는다',
             '무작위 보행의 운동론적 길이 (7.2)와 유체 선형화의 √(κ_{e}/α_{ε})는 서로 다른 근사에서 정의된다.', size=13)
    reg(s, 'd_et4', 40, """가열이 없는 1차원 영역에서는 온도 섭동이 지수적으로 감쇠하고, 그 길이가 열전도도와 손실 민감도의 비의 제곱근입니다. 열전도도를 대입하면 밀도가 약분되어 길이는 확산계수와 반응계수의 온도 미분으로 정해지고, 압력에 반비례합니다. 다만 이 유체 길이와 앞의 무작위 보행 길이는 서로 다른 근사이므로 같은 값이라고 보면 안 됩니다.""",
        """κ_e와 α_ε가 모두 n_e에 비례해 λ_ε는 밀도와 무관하고, D_e ∝ 1/n_g이므로 ∝ 1/p. 10 mTorr: 유체 10.3 cm, Kim & Chung 환산 11.9 cm. 5 mTorr에서는 15.4 대 23.8 cm로 차이가 커진다.""")
    return s


def d_et5():
    s = frame('국소 생성 모델은 흡수 전력을 비용으로 나눈다', '전자 에너지 수송 5  ·  국소 생성과 전역 에너지 비용',
              '기본 모델의 생성항은 전역 비용으로 흡수 전력을 나눈 현상론적 소스다.', '정진욱 (2026) §2.4 식 (2.63)–(2.65)의 ε_{c}, ε_{T}.')
    y = rows(s, [dict(eq='e7_15', pt=18, lab='국소 균형', num='(7.15)'),
                 dict(eq='e7_16', pt=19, lab='국소 생성', num='(7.16)'),
                 dict(eq='e7_17', pt=20, lab='기본 모델', num='(7.17)')], y=1.5, gap=0.2)
    bullets(s, 0.55, y + 0.08, 8.9, 5.8 - y, [
        '전자 에너지의 공간 수송이 충분히 작고, 흡수된 전력이 대부분 그 자리의 충돌 손실에 쓰인다고 가정한다.',
        'ε_{T}에는 전역 벽 손실 비용이 들어 있다. (7.17)은 국소 해가 아니라 전역 유지 비용을 흡수 전력에 배분한 모형이다.',
        'ε_{c}/ε_{T}가 일정하면 두 선택은 전체 진폭만 바꾸고 정규화된 공간 형상은 같다.'], size=13)
    reg(s, 'd_et5', 40, """에너지 수송이 충분히 작다면, 흡수된 전력이 그 자리의 충돌 손실과 같으므로 국소 생성률은 흡수 전력을 충돌 비용으로 나눈 것입니다. 기본 모델은 여기서 ε_c 대신 벽 손실을 포함한 ε_T를 씁니다. 그래서 이것은 정확한 국소 해가 아니라 전역 유지 비용을 흡수 분포에 나눠 준 현상론적 소스입니다. 비용의 비가 일정하면 두 선택은 크기만 다르고 형상은 같습니다.""",
        """∫G_model dV = P_abs/(eε_T) = Ṅ_wall(4장 식 4.10)로 입자 수지가 맞는다. ∫G_local dV = P_abs/(eε_c) > Ṅ_wall은 식 (7.15)가 경계 에너지 유출을 버렸기 때문이다. 이 모델에서는 흡수 형상이 G로 그대로 전달된다(독립 제어의 낙관적 극한).""")
    return s


def extremes_table(s, y):
    data = [['구분', '국소·지정 소스 G(r, z)', '균일 이온화 주파수 G = ν_{iz}n'],
            ['기본 방정식', '−D_{a}∇²n = G_{given}', '−D_{a}∇²n = ν_{iz}n'],
            ['수학적 성격', '비동차 푸아송형 문제', '동차 고유값 문제'],
            ['형상 응답', '소스의 공간 성분이 밀도에 전달됨', '기본 모드가 형상을 고정'],
            ['주의점', '국소 생성 가정이 과도할 수 있음', '실제 비국소 상태의 보편 해가 아님']]
    table(s, 0.5, y, [1.6, 3.7, 3.7], data, size=12.5, header_size=12.5, row_h=0.36, header_fill=NAVY,
          line_color=LINE, first_col_bold=True, colors={(i, 0): NAVY for i in range(1, 5)})


def d_et6():
    s = frame('균일 EEDF 극한은 고유값 문제다', '전자 에너지 수송 6  ·  소스를 단순히 평탄화한 모델이 아니다',
              '균일 EEDF에서는 기본 고유모드가 형상을 정하고, 전력은 진폭만 정한다.', '정진욱 (2026) §1.10 식 (1.83): 밀도 비례 이온화의 고유모드.')
    rows(s, [dict(eq='e7_18', pt=17, lab='균일 EEDF', num='(7.18)'),
             dict(eq='e7_19', pt=18, lab='확산식 대입', num='(7.19)')], y=1.5, gap=0.18)
    extremes_table(s, 2.75)
    note_box(s, 0.5, 4.75, 9.0, 1.05, '핵심 구분', 'G ≈ const로 만드는 넓은 평활화와 G = ν_{iz}n은 다른 방정식이다. 대표 T_{e}가 같다는 사실만으로 EEDF의 고에너지 꼬리와 이온화율이 같아지지도 않는다.', size=13)
    reg(s, 'd_et6', 45, """반대 극한은 전자온도뿐 아니라 EEDF 전체가 어디서나 같은 경우입니다. 그러면 생성률은 밀도에 비례하고, 확산식에 넣으면 소스가 외부에서 지정되지 않는 고유값 문제가 됩니다. 이때 정상 해가 존재하려면 ν_iz/D_a가 경계조건과 맞아야 하고, 형상은 기본 고유모드로 고정되며 전력은 진폭만 정합니다. 표처럼 두 극한은 수학적 성격부터 다릅니다.""",
        """정진욱 (2026) §1.10 pp.62–66 식 (1.80)–(1.83): 원통에서 이온화가 밀도에 비례할 때의 베셀 고유모드. 고유값 조건은 4장 (4.7)처럼 n이 아니라 T_e(곧 ν_iz)를 정한다. 이 극한에서는 k, φ가 형상을 바꾸지 못한다(9장 J의 형상 행 → 0).""")
    return s


def c_extremes():
    s = frame('생성 모델은 두 극한 사이에 있다', '전자 에너지 수송  ·  국소 생성 모델과 균일 EEDF 극한',
              '국소 생성이면 흡수 형상이 밀도로 전달되고, 균일 EEDF면 형상은 기본 모드로 고정된다.',
              'ε_{c}, ε_{T}: 정진욱 (2026) §2.4. 고유모드: §1.10 식 (1.83). 에너지 방정식과 국소 모델 유도: 부록 A17–A21.')
    for x, t, sub, name, pt in ((0.5, '국소 생성 (기본 모델)', '에너지 수송이 작을 때', 'e7_17', 20),
                                (5.1, '균일 EEDF 극한', 'EEDF·반응계수가 어디서나 같을 때', 'e7_19', 17)):
        box(s, x, 1.5, 4.4, 1.62, fill=None, line=LINE, radius=None)
        box(s, x, 1.5, 4.4, 0.04, fill=NAVY, radius=None)
        head(s, x + 0.12, 1.58, 4.1, t, size=14.5)
        label(s, x + 0.12, 1.92, 4.2, sub, size=12.5, color=MUTED)
        put(s, name, x + 0.1, 2.3, pt, maxw=4.2, center_w=4.2)
    tb(s, 0.55, 3.2, 4.3, 0.6, 'ε_{T}는 벽 손실 포함 전역 비용: 전역 유지 비용을 흡수 분포에 나눈 현상론적 소스', size=12.5, color=TEXT)
    tb(s, 5.15, 3.2, 4.3, 0.6, '고유값 문제: 기본 고유모드가 형상, 전력 균형이 진폭', size=12.5, color=TEXT)
    extremes_table(s, 3.95)
    reg(s, 'c_extremes', 55, """그래서 생성을 어떻게 모델링할지가 결정적입니다. 한쪽 극한은 에너지 수송이 작아서 흡수된 전력이 그 자리에서 이온을 만드는 경우입니다. 저희 기본 모델이 이것이고, 흡수 전력을 벽 손실까지 포함한 비용 ε_T로 나눕니다. 이 경우 흡수 형상이 생성 형상으로 그대로 전달됩니다. 반대 극한은 EEDF가 어디서나 같아서 생성이 밀도에 비례하는 경우입니다. 그러면 확산식이 고유값 문제가 되어, 형상은 기본 고유모드로 고정되고 전력은 크기만 바꿉니다. 이때는 코일로 형상을 바꿀 수 없습니다. 실제 플라즈마는 이 둘 사이에 있습니다. 이제 생성된 입자가 어떻게 밀도 분포가 되는지 보겠습니다.""",
        """식 (7.17) G_model = p_abs/(eε_T): ∫G dV = P_abs/(eε_T) = Ṅ_wall(식 4.10)로 입자 수지가 맞는다. 국소 균형의 정확한 분모는 ε_c(식 7.16)이며, ε_c/ε_T가 일정하면 형상은 같다. 식 (7.19)의 고유값 조건 ν_iz/D_a = (χ01/R)² + (π/L)²(식 8.34)는 4장 (4.7)처럼 T_e를 정한다. 어느 극한에 가까운지는 λ_ε와 영역 간격의 비가 정한다(10 mTorr에서 λ_ε 10–12 cm 대 간격 7–10 cm).""")
    return s


# ================================================================== 8장
def d_df1():
    s = frame('전자와 이온은 내부 전기장으로 함께 확산한다', '양극성 확산 1  ·  준중성 선속 조건',
              '먼저 빠져나가는 전자가 만든 전기장이 전자를 붙잡고 이온을 민다.', '정진욱 (2026) §1.10 pp.59–61, 식 (1.63)–(1.66).')
    rows(s, [dict(eq='e8_1', pt=18, lab='전자 선속', num='(8.1)'),
             dict(eq='e8_2', pt=18, lab='이온 선속', num='(8.2)'),
             dict(eq='e8_3', pt=18, lab='Γ_{e} = Γ_{i}', num='(8.3)'),
             dict(eq='e8_4', pt=18, lab='정리', num='(8.4)'),
             dict(eq='e8_5', pt=19, lab='양극성 전기장', num='(8.5)')], y=1.5, gap=0.17)
    reg(s, 'd_df1', 35, """준중성 벌크에서 전자는 이온보다 훨씬 빨리 확산하려 합니다. 전자가 먼저 빠져나가면 전하 분리로 내부 전기장이 생기고, 이 장이 전자를 붙잡으며 이온을 가속합니다. 두 선속을 드리프트와 확산으로 쓰고 같다고 놓으면 그 전기장을 밀도 기울기로 쓸 수 있습니다.""",
        """정진욱 (2026) §1.10 pp.59–61 식 (1.63)–(1.66): 전자·이온 선속과 양극성 전기장. 이동도 μ_e, μ_i > 0의 크기로 정의.""")
    return s


def d_df2():
    s = frame('양극성 확산계수는 이온 이동도가 제한한다', '양극성 확산 2  ·  D_{a}의 유도',
              '전자와 이온은 함께 움직이지만, 수송 규모는 주로 이온 이동도가 정한다.', '정진욱 (2026) §1.10 pp.60–61, 식 (1.67)–(1.68).')
    y = rows(s, [dict(eq='e8_6', pt=18, lab='(8.2)에 대입', num='(8.6)'),
                 dict(eq='e8_7', pt=18, lab='', num='(8.7)'),
                 dict(eq='e8_8', pt=19, lab='양극성 확산', num='(8.8)'),
                 dict(eq='e8_9', pt=18, lab='아인슈타인 관계', num='(8.9)')], y=1.5, gap=0.17)
    tb(s, 0.55, y + 0.05, 8.9, 0.6, 'D_{e} = μ_{e}T_{e}, D_{i} = μ_{i}T_{i}(eV 단위). T_{e} ≫ T_{i}이면 D_{a} ≃ μ_{i}T_{e}.', size=13.5, color=TEXT)
    reg(s, 'd_df2', 35, """그 전기장을 이온 선속에 넣으면 이온도 밀도 기울기에 비례하는 확산 선속이 되고, 그 계수가 양극성 확산계수입니다. 아인슈타인 관계를 쓰면 전자 이동도가 훨씬 클 때 D_a는 이온 이동도에 전자온도를 곱한 것이 됩니다. 함께 움직이지만 속도는 느린 쪽인 이온이 정합니다.""",
        """정진욱 (2026) §1.10 식 (1.67)–(1.68): D_a = (μ_iD_e + μ_eD_i)/(μ_i + μ_e) ≈ μ_iT_e. 10 mTorr 예시: D_a ≈ 50 m²/s(D_a = eT_e/(Mν_in), λ_i = 1/(330p[Torr]) cm).""")
    return s


def d_df3():
    s = frame('입자 보존에서 2D 확산 방정식을 얻는다', '양극성 확산 3  ·  연속 방정식과 축대칭 형태',
              'G를 지정하고 경계 손실 조건을 주면 밀도 분포가 수학적으로 결정된다.', '정진욱 (2026) §1.10 pp.62–63, 식 (1.73)–(1.75).')
    y = rows(s, [dict(eq='e8_10', pt=19, lab='입자 보존', num='(8.10)'),
                 dict(eq='e8_11', pt=20, lab='정상상태', num='(8.11)'),
                 dict(eq='e8_12', pt=17, lab='축대칭, D_{a} 일정', num='(8.12)')], y=1.5, gap=0.25)
    bullets(s, 0.55, y + 0.05, 8.9, 5.8 - y, [
        '정상상태 ∂_{t}n = 0, 체적 재결합 등 L_{vol} ≃ 0, Γ = −D_{a}∇n',
        '축 r = 0에서 ∂_{r}n = 0의 대칭 조건'], size=13.5)
    reg(s, 'd_df3', 35, """국소 입자 보존에 정상상태, 체적 손실 무시, 양극성 확산 선속을 넣으면 확산 연산자와 생성항의 균형식이 됩니다. 축대칭이고 D_a가 일정하면 원통 좌표의 식이 되고, 축에서는 대칭 조건을 씁니다. 생성 분포와 벽 조건을 주면 밀도 분포가 정해집니다.""",
        """정진욱 (2026) §1.10 pp.62–63 식 (1.73)–(1.75): 확산 방정식. 식 (8.11)을 체적 적분하고 Robin 경계 (8.24)를 넣으면 4장 식 (4.2) ∫G dV = ∮u_B n_s dA가 된다. 0D는 2D의 적분이다.""")
    return s


def d_df4():
    s = frame('균일 생성 평판: 벽 손실만으로 중앙이 높다', '확산 해 1  ·  1D 평판, Dirichlet 벽',
              '모든 위치에서 같게 생성해도 벽으로의 손실 때문에 중심 밀도가 높다.', '정진욱 (2026) §1.10 pp.63–64, 식 (1.76)–(1.79). 벽 z = ±L/2, G_{0}·D_{a} 일정.')
    rows(s, [dict(eq='e8_13', pt=18, lab='평판 방정식', num='(8.13)'),
             dict(eq='e8_14', pt=18, lab='두 번 적분', num='(8.14)'),
             dict(eq='bc_dir', pt=17, lab='대칭·벽 조건'),
             dict(eq='e8_15', pt=20, lab='해', num='(8.15)'),
             dict(text='중심에서 이온화가 더 일어난다는 가정은 필요하지 않다.', size=13.5, h=0.4)], y=1.45, gap=0.16)
    reg(s, 'd_df4', 30, """가장 간단한 경우로, 균일 생성과 일정한 D_a, 벽에서 밀도 0인 평판을 봅니다. 두 번 적분하고 중심 대칭과 벽 조건을 쓰면 포물선 해가 나옵니다. 생성이 어디서나 같아도 벽으로 손실되기 때문에 중심이 높습니다.""",
        """정진욱 (2026) §1.10 식 (1.76)–(1.79): 평판의 cos·포물선 분포. Dirichlet(n = 0)은 비교용 이상화(2장 가정표).""")
    return s


def d_df5():
    s = frame('무한 원통에서도 반경 방향 포물선이 된다', '확산 해 2  ·  무한 원통, 균일 생성, Dirichlet 측벽',
              '축대칭 원통에서도 균일 생성의 밀도는 중앙이 높은 포물선이다.', '정진욱 (2026) §1.10 pp.64–66. 이상 조건의 해석 곡선이며 유한 높이 챔버의 계산 결과가 아니다.')
    rows(s, [dict(eq='e8_16', pt=15.5, lab=None, num='(8.16)'),
             dict(eq='e8_17', pt=15.5, lab=None, num='(8.17)'),
             dict(eq='e8_18', pt=15.5, lab=None, num='(8.18)'),
             dict(eq='e8_19', pt=15.5, lab=None, num='(8.19)'),
             dict(eq='e8_20', pt=15.5, lab=None, num='(8.20)'),
             dict(eq='e8_21', pt=17, lab=None, num='(8.21)')], y=1.42, x0=0.55, xr=5.3, gap=0.05)
    lib.pic(s, R + '/fig/cyl.png', 5.55, 1.6, w=3.9)
    tb(s, 5.6, 4.5, 3.9, 1.2, [{'t': 'r = 0에서 발산하지 않으므로 C_{1} = 0', 'after': 4},
                              {'t': 'n(R) = 0에서 C_{2} = G_{0}R²/(4D_{a})'}], size=13, color=TEXT)
    reg(s, 'd_df5', 35, """반경 방향도 같습니다. z 의존성을 지운 무한 원통에서 양변에 r을 곱해 적분하고, 축에서 발산하지 않는 조건과 측벽 조건을 쓰면 R² − r² 꼴의 포물선이 됩니다. 다만 이것은 위아래 손실이 없는 무한 원통의 이상 해입니다.""",
        """질의응답용: R 21 cm, L 6 cm의 얇은 챔버에서는 위·아래 손실이 대부분이라((π/L)² = 2742 대 (χ01/R)² = 131 m⁻²) 균일 생성의 ρ가 무한 원통 1.62와 달리 약 1.06이다(10 mTorr, 높이 기본 모드 근사, 저장소 sim/ch7_9_links.py). 이 기하의 반경 형상은 8.7–8.8절의 ℓ_r이 정한다.""")
    return s


def d_df6():
    s = frame('벽에서 밀도를 0으로 둘 필요는 없다', 'Bohm Robin 조건  ·  확산 선속 = 쉬스 경계 유출',
              '확산 선속과 Bohm 유출을 같게 두면 Robin 경계조건이 된다.', '정진욱 (2026) §1.7.1 p.50, 식 (1.42)의 Bohm 기준. Robin 형태 [유도].')
    y = rows(s, [dict(eq='e8_22', pt=19, lab='확산 선속', num='(8.22)'),
                 dict(eq='e8_23', pt=19, lab='Bohm 유출', num='(8.23)'),
                 dict(eq='e8_24', pt=21, lab='Robin 조건', num='(8.24)')], y=1.6, gap=0.3)
    bullets(s, 0.55, y + 0.1, 8.9, 5.8 - y, [
        'n̂: 플라즈마 영역의 바깥쪽 법선, n_{s}: 벌크–쉬스 경계의 밀도',
        '실제 물리 벽과 벌크–쉬스 경계를 같게 보는 것은 추가 근사다.'], size=13.5)
    reg(s, 'd_df6', 30, """실제 벌크의 끝은 쉬스 경계이고, 이온은 그곳에서 Bohm 속도 규모로 빠져나갑니다. 벌크에서 오는 확산 선속과 이 유출을 같게 놓으면, 밀도의 기울기와 경계 밀도를 잇는 Robin 조건이 됩니다.""",
        """정진욱 (2026) §1.7.1 p.50 식 (1.42): Bohm 기준 u_B = √(eT_e/M). 4장 h 인자 (4.6)는 이 경계 밀도 n_s와 중심 밀도의 비다. 상수 D_a Robin과 교재 h_L은 10 mTorr에서 0.57 대 0.24로 다르다(가변 이동도 효과, 2D에서 보정).""")
    return s


def d_df7():
    s = frame('Robin 경계에서는 벽 밀도가 남는다', '확산 해 3  ·  평판에 Robin 경계 적용',
              'Robin 해는 Dirichlet 해에 양의 상수를 더해 정규화 형상이 달라진다.', '[유도] 대칭으로 C_{1} = 0인 n(z) = −(G_{0}/2D_{a})z² + C_{2}에서 출발. 그림의 u_{B}L/(4D_{a}) = 0.77은 예시.')
    rows(s, [dict(eq='e8_25', pt=16, lab=None, num='(8.25)'),
             dict(eq='e8_26', pt=16, lab=None, num='(8.26)'),
             dict(eq='e8_27', pt=16, lab=None, num='(8.27)'),
             dict(eq='e8_28', pt=16, lab=None, num='(8.28)')], y=1.5, xr=5.6, gap=0.17)
    lib.pic(s, R + '/fig/slab.png', 5.8, 1.45, w=3.65)
    tb(s, 5.85, 4.25, 3.6, 1.5, '벽 밀도 n_{s} = G_{0}L/(2u_{B}) > 0. 일정한 G_{0}, D_{a}, u_{B}에서 Dirichlet 해에 양의 상수가 더해진다.', size=13, color=TEXT)
    reg(s, 'd_df7', 35, """같은 평판에 Robin 조건을 쓰면 벽에서의 확산 선속 G_0L/2가 u_B 곱하기 벽 밀도와 같아야 합니다. 이것으로 적분 상수를 정하면 포물선에 G_0L/2u_B라는 양의 상수가 더해집니다. 벽 밀도가 0이 아니므로 정규화한 형상도 Dirichlet과 달라집니다.""",
        """n(0)/n(L/2) = 1 + u_B L/(4D_a). 10 mTorr 예시: D_a/u_B = 1.95 cm, L = 6 cm → 1.77. 그림은 u_B L/(4D_a) = 0.77로 그린 정성 곡선.""")
    return s


def d_df8():
    s = frame('원통 측벽에서도 같은 상수가 더해진다', '확산 해 4  ·  무한 원통의 측벽 Robin 조건',
              '벽 손실은 중심–가장자리 상대 밀도비를 바꾸는 형상 제어의 핵심 요소다.', '[유도] n(r) = −(G_{0}/4D_{a})r² + C_{2}를 측벽에 적용.')
    rows(s, [dict(eq='e8_29', pt=19, lab='측벽 조건', num='(8.29)'),
             dict(eq='e8_30', pt=20, lab='해', num='(8.30)')], y=1.7, gap=0.35)
    note_box(s, 0.5, 3.6, 9.0, 1.6, '경계조건의 의미', '중앙 볼록형은 균일 생성에서도 나타날 수 있다. 다만 실제 경계에서 밀도가 0이 아니면 포물선에 상수 성분이 더해지고, 중심–가장자리의 상대 밀도비까지 달라진다. 벽 손실은 형상 제어 문제의 핵심 요소다.', size=14)
    reg(s, 'd_df8', 30, """원통 측벽에도 같은 조건을 쓰면 반경 포물선에 G_0R/2u_B가 더해집니다. 즉 균일 생성에서도 중앙이 볼록할 수 있지만, 벽에서의 밀도가 그 볼록한 정도, 다시 말해 중심과 가장자리의 비를 바꿉니다. 벽 손실이 형상 문제의 핵심인 이유입니다.""",
        """식 (8.30) n(r) = (G₀/4D_a)(R² − r²) + G₀R/(2u_B). 10 mTorr에서 무한 원통 Robin 해의 ρ는 1.48(Dirichlet 1.62). 얇은 챔버에서는 약 1.06(저장소 sim/ch7_9_links.py).""")
    return s


def d_df9():
    s = frame('균일 생성과 균일 이온화 주파수는 다른 문제다', '확산 해 5  ·  Case A(지정 소스)와 Case B(G = ν_{iz}n)',
              'Case A는 소스를 평활화해 전달하고, Case B는 고유모드로 형상을 고정한다.',
              '정진욱 (2026) §1.10 pp.64–66, 식 (1.80)–(1.83). 고유값은 문서의 λ_{m}을 7.1절 λ_{m}(평균자유행로)과 구분해 Λ_{m}으로 썼다.')
    y = rows(s, [dict(eq='e8_31', pt=17, lab='Case A', num='(8.31)'),
                 dict(eq='modal', pt=15, lab='모드 응답'),
                 dict(eq='e8_32', pt=17, lab='Case B', num='(8.32)'),
                 dict(eq='e8_33', pt=15.5, lab='기본 고유함수', num='(8.33)'),
                 dict(eq='e8_34', pt=16, lab='고유값', num='(8.34)')], y=1.45, gap=0.1)
    note_box(s, 0.5, max(y + 0.02, 4.95), 9.0, 0.85, '모델의 성격', 'G = G_{0}는 체적당 생성이 같다는 뜻이고, G = ν_{iz}n은 전자 하나당 이온화 빈도가 같다는 뜻이다. 후자의 총 생성은 밀도가 높은 중앙에서 더 크다.', size=12.5)
    reg(s, 'd_df9', 45, """여기서 두 종류의 '균일'을 구분해야 합니다. Case A는 생성항을 외부에서 지정하는 문제로, 생성항을 고유함수로 펼치면 공간적으로 빠르게 변하는 성분일수록 더 강하게 평활화됩니다. Case B는 이온화 주파수가 위치와 무관한 경우로, 7장의 균일 EEDF 극한과 같습니다. Dirichlet 원통에서 해는 J_0와 cos의 기본 고유함수이고, 고유값 조건이 ν_iz/D_a를 정합니다. 이때 진폭은 전력 균형이 정합니다.""",
        """(8.34)에서 R 21 cm, L 6 cm: (χ01/R)² = 131 m⁻², (π/L)² = 2742 m⁻² → 손실의 약 95%가 위·아래 벽. 고유값 조건은 4장 (4.7)과 같은 역할(T_e 결정). 모드 응답 n_m = G_m/(D_aΛ_m)은 저역 통과 필터로 읽을 수 있다.""")
    return s


def d_df10():
    s = frame('높이 방향 기본 모드는 Robin 경계가 정한다', '반경 혼합 길이 1  ·  높이 방향 고유모드',
              '높이 기본 모드의 파수 k_{z}는 L과 u_{B}/D_{a}로 정해진다.', '[유도] 정진욱 (2026) §1.10의 확산식과 §1.7.1의 Bohm 경계.')
    y = rows(s, [dict(eq='e8_35', pt=19, lab='높이 모드', num='(8.35)'),
                 dict(eq='e8_36', pt=19, lab='z = L/2 Robin', num='(8.36)'),
                 dict(eq='e8_37', pt=21, lab='기본 모드', num='(8.37)')], y=1.6, gap=0.3)
    bullets(s, 0.55, y + 0.1, 8.9, 5.8 - y, [
        '가장 작은 양의 근이 기본 모드다.',
        '벽 손실이 강한 Dirichlet 극한에서는 k_{z} → π/L이다.',
        '얇은 원통에서 반경 방향 생성 패턴이 얼마나 멀리 전달되는지 보려고 높이 기본 모드만 남긴다.'], size=13.5)
    reg(s, 'd_df10', 30, """얇은 원통에서 반경 방향 생성 패턴이 얼마나 멀리 전달되는지 보려고 높이 방향 기본 모드만 남깁니다. cos(k_z z)에 위쪽 벽의 Robin 조건을 쓰면 k_z tan(k_z L/2) = u_B/D_a가 되고, 그 가장 작은 근이 기본 모드입니다. 벽 손실이 강하면 k_z는 π/L로 갑니다.""",
        """10 mTorr: u_B/D_a = 51 m⁻¹, L = 6 cm → k_z ≈ 33 m⁻¹. 높은 차수의 높이 모드는 반경 방향으로 더 빨리 감쇠하므로 생성원에서 떨어진 곳은 기본 모드가 정한다.""")
    return s


def d_df11():
    s = frame('분리변수로 반경 방향 식을 얻는다', '반경 혼합 길이 2  ·  높이 모드 성분의 분리',
              '높이 방향 손실이 반경 식에 −k_{z}²f 항으로 들어온다.', '[유도] n(r, z) ≃ f(r)cos(k_{z}z), G(r, z) ≃ g(r)cos(k_{z}z)를 식 (8.12)에 대입.')
    y = rows(s, [dict(eq='e8_38', pt=14.5, lab='(8.12)에 대입', above=True, num='(8.38)'),
                 dict(eq='e8_39', pt=19, lab='정리', num='(8.39)'),
                 dict(eq='e8_40', pt=19, lab='생성원 밖', num='(8.40)')], y=1.5, gap=0.25)
    tb(s, 0.55, y + 0.1, 8.9, 0.6, 'd²/dz² cos(k_{z}z) = −k_{z}² cos(k_{z}z)를 쓰면 cos(k_{z}z)가 약분된다. 생성원에서 떨어진 영역은 g(r) = 0이다.', size=13.5, color=TEXT)
    reg(s, 'd_df11', 30, """밀도와 생성항을 높이 기본 모드 성분으로 두고 축대칭 확산식에 넣으면, z 미분이 −k_z²을 만들어 cos가 약분됩니다. 남는 반경 식에는 위아래 손실이 −k_z² f라는 손실항으로 들어옵니다. 생성원에서 떨어진 곳에서는 우변이 0입니다.""",
        """식 (8.39)는 7장 식 (7.10)과 같은 '확산 − 선형 손실 = −소스' 꼴이다. 퍼짐 계수 D_a, 손실률 D_a k_z²(위·아래 벽 손실), 길이 √(D_a/D_a k_z²) = 1/k_z.""")
    return s


def lr_slide(core):
    s = frame('얇은 챔버에서는 반경 방향 전달 거리가 짧다' if core else '생성원의 영향은 높이 모드 파수의 역수만큼 퍼진다',
              '반경 혼합 길이' + ('' if core else ' 3') + '  ·  수정 베셀 해와 감쇠 길이',
              '위·아래 쉬스 손실이 국소 생성원의 영향이 반경 방향으로 전달되는 거리를 ℓ_{r}로 제한한다.',
              '[유도] 확산식(정진욱 §1.10)과 Bohm 경계(§1.7.1).' + (' Case A/B, 높이 모드, 분리변수 유도: 부록 A30–A33.' if core else ' 그림은 문서 그림 7의 개념도.'))
    if core:
        put(s, 'e8_43', 0.6, 1.45, 20, maxw=8.8, center_w=8.8)
        lr_diagram(s, 5.15, 2.85, w=4.0, h=1.4)
        bullets(s, 0.55, 2.5, 4.45, 2.1, [
            '높이 기본 모드 cos(k_{z}z)만 남기면 반경 식에 −k_{z}²f 손실항이 생긴다.',
            '생성원 밖의 해는 수정 베셀 함수, K_{0}(x) ∼ e^{−x} → 감쇠 길이 1/k_{z}',
            '벽 손실이 강한 극한에서 k_{z} → π/L'], size=13.5)
        yb = 4.65
    else:
        rows(s, [dict(eq='e8_41', pt=17, lab='일반해', num='(8.41)'),
                 dict(eq='e8_42', pt=17, lab='점근 형태', num='(8.42)'),
                 dict(eq='e8_43', pt=17, lab='감쇠 길이', num='(8.43)')], y=1.42, xr=9.45, gap=0.1)
        lr_diagram(s, 0.75, 3.92, w=4.2, h=1.0)
        tb(s, 5.4, 3.65, 4.1, 1.2, '(8.40)은 0차 수정 베셀 방정식이다. 반경이 커질 때 K_{0}가 e^{−x}로 줄어 국소 생성원의 영향이 1/k_{z} 거리로 감쇠한다.', size=13, color=TEXT)
        yb = 5.02
    note_box(s, 0.5, yb, 9.0, 5.8 - yb, '유효 길이의 한계', 'ℓ_{r}은 높이 기본 모드·일정 D_{a}·단순 Robin 경계의 반경 응답 길이다. 밀도가 정확히 exp(−|r − r_{0}|/ℓ_{r})이라는 뜻은 아니며, 완전한 해에는 수정 베셀 함수의 조합과 경계 Green 함수가 필요하다.', fill=ORANGE_L, size=12.5 if core else 12)
    key = 'c_lr' if core else 'd_df12'
    reg(s, key, 50 if core else 40, """그렇다면 생성된 입자는 반경 방향으로 얼마나 멀리 퍼질까요. 저희 챔버는 반경 21 cm에 높이 6 cm로 아주 납작합니다. 높이 방향 기본 모드만 남기면 반경 식에 위아래 쉬스로 빠지는 손실항이 생기고, 생성원에서 떨어진 곳의 해는 수정 베셀 함수가 되어 1/k_z 거리로 감쇠합니다. 이 길이를 반경 혼합 길이 ℓ_r이라 부르겠습니다. 즉 입자는 반경 방향으로 멀리 가기 전에 위아래로 빠집니다. 정확한 지수 꼴은 아니지만, 국소 생성원의 영향이 전달되는 거리의 척도입니다.""" if core else
        """생성원 밖의 반경 식은 0차 수정 베셀 방정식이고, 해는 I_0와 K_0의 조합입니다. K_0는 큰 인수에서 e^{−x}로 줄기 때문에 국소 생성원의 영향은 1/k_z 거리로 감쇠합니다. 이 길이가 반경 혼합 길이 ℓ_r입니다. 다만 이것은 단일 모드 근사의 응답 길이이고, 정확한 지수 꼴이라는 뜻은 아닙니다.""",
        """식 (8.43) ℓ_r = 1/k_z, k_z tan(k_zL/2) = u_B/D_a. 10 mTorr 예시: ℓ_r ≈ 3.0 cm, Dirichlet 하한 L/π = 1.9 cm(벽 손실을 교재 h 인자에 맞추면 이쪽으로 준다). 영역 간격 7–10 cm보다 작으므로 확산은 중앙·가장자리를 거의 섞지 않는다. 같은 압력의 λ_ε(10–12 cm)는 간격과 비슷하므로, 10 mTorr에서 두 영역을 섞는 병목은 7장의 에너지 수송이다(저장소 docs/14_개정본_7-9장_연결.md). 단일 모드 근사에서 cos(k_z z)는 ρ에서 약분된다.""")
    return s


def c_diff():
    s = frame('균일하게 생성해도 벽 손실이 형상을 만든다', '양극성 확산과 벽 손실  ·  2D 확산식과 Bohm 경계',
              '최종 밀도는 소스 G와 확산·벽 손실 연산자가 함께 정한다.',
              '정진욱 (2026) §1.10 식 (1.63)–(1.83), §1.7.1 식 (1.42). 그림 예시 u_{B}L/(4D_{a}) = 0.77. 유도: 부록 A22–A29.')
    y = rows(s, [dict(eq='e8_8', pt=15.5, lab='양극성 확산', above=True, num='(8.8)', indent=0.1),
                 dict(eq='e8_11', pt=17, lab='정상상태 확산식', above=True, num='(8.11)', indent=0.1),
                 dict(eq='e8_24', pt=17, lab='벽: 확산 선속 = Bohm 유출', above=True, num='(8.24)', indent=0.1),
                 dict(eq='e8_28', pt=16, lab='균일 생성 평판 해', above=True, num='(8.28)', indent=0.1)],
             y=1.42, xr=5.75, gap=0.07)
    lib.pic(s, R + '/fig/slab.png', 5.85, 1.5, w=3.65)
    tb(s, 5.9, 4.25, 3.6, 1.55, [
        {'t': '중심에서 이온화가 더 일어나지 않아도 중앙이 높다.', 'bullet': True, 'after': 4},
        {'t': '벽 밀도 n_{s} = G_{0}L/2u_{B} > 0이 정규화 형상을 바꾼다.', 'bullet': True}], size=13, color=TEXT)
    reg(s, 'c_diff', 60, """생성된 전자와 이온은 각자 움직이지 않습니다. 빠른 전자가 먼저 빠져나가며 만든 전기장이 둘을 묶어 함께 확산시키고, 그 속도는 이온 이동도가 정합니다. 정상상태에서는 이 확산과 생성이 균형을 이루고, 벽에서는 확산으로 온 선속이 Bohm 속도로 빠져나가는 선속과 같아야 합니다. 가장 간단한 평판에 균일 생성을 넣고 풀면 포물선에 벽 밀도만큼의 상수가 더해진 해가 나옵니다. 중심에서 이온화가 더 일어나지 않아도 벽 손실 때문에 중앙이 높아지고, 벽 밀도의 크기가 형상비를 바꿉니다. 그런데 저희 챔버는 납작합니다. 그러면 반경 방향으로는 어떨까요?""",
        """정진욱 (2026) §1.10 pp.59–61 식 (1.63)–(1.68): D_a = (μ_iD_e + μ_eD_i)/(μ_i + μ_e) ≈ μ_iT_e. pp.62–66 식 (1.73)–(1.83): 확산식, 평판 해, 원통 베셀 해. §1.7.1 p.50 식 (1.42) Bohm. 식 (8.11)을 체적 적분하고 (8.24)를 넣으면 4장 식 (4.2)가 된다(0D는 2D의 적분). 10 mTorr: n(0)/n(L/2) = 1 + u_BL/(4D_a) = 1.77. 무한 원통 해 (8.21)·(8.30)은 부록 A26·A29: 얇은 챔버에서는 위·아래 손실이 커서 반경 볼록이 약하다(균일 생성 ρ ≈ 1.06).""")
    return s


# ================================================================== 9·10장
def judge():
    s = frame('독립 제어는 2×3 Jacobian으로 판정한다', '판정 방법  ·  입력–출력 관계와 정적 소신호 민감도',
              '노브로 ρ가 변하는 것과, n̄_{w}를 지킨 채 원하는 ρ를 만드는 것은 다르다.',
              '[유도] 판정 수학의 정의. 독립 제어가 가능하다는 수치 결론은 아직 얻지 않았다.')
    y = rows(s, [dict(eq='e9_1', pt=17, lab='입출력 관계', num='(9.1)'),
                 dict(eq='uy', pt=15, lab='압력 p 고정'),
                 dict(eq='e9_2', pt=16, lab='국소 민감도', num='(9.2)'),
                 dict(eq='e9_3', pt=17, lab='목표 조건', num='(9.3)')], y=1.42, gap=0.1)
    yy = y + 0.04
    hh = 5.82 - yy
    box(s, 0.5, yy, 4.4, hh, fill=PANEL, radius=None, margin=0.1, anchor='m', paras=[
        {'t': '동작점 탐색과 국소 민감도는 다른 질문', 'bold': True, 'color': NAVY, 'after': 3},
        {'t': '지도: 여러 k, φ에서 ρ가 어떻게 변하나', 'bullet': True, 'after': 2},
        {'t': 'J: 고른 기준점 주위의 미소 변경 응답', 'bullet': True}], size=12.5, color=TEXT)
    box(s, 5.1, yy, 4.4, hh, fill=ORANGE_L, radius=None, margin=0.1, anchor='m', paras=[
        {'t': '판정 기준', 'bold': True, 'color': ORANGE_D, 'after': 3},
        {'t': 'J 첫 행 = 0인 입력 조합에서 둘째 행이 ρ를 움직이는가', 'bullet': True, 'after': 2},
        {'t': '정규화한 J의 rank·특이값·입력 한계로 본다(2×3이므로 역행렬·행렬식 아님).', 'bullet': True}], size=12.5, color=TEXT)
    reg(s, 'judge', 60 if MARK else 60, """이제 처음 질문으로 돌아가겠습니다. 압력을 운전 조건으로 두면, 전력·전류비·위상이라는 세 노브에서 평균 밀도와 밀도비라는 두 출력으로 가는 관계를 지금까지의 물리 모델이 정합니다. 기준 동작점 주위에서 이 관계를 선형화하면 2×3 Jacobian이 됩니다. 저희 목표는 평균 밀도의 변화는 0으로, 밀도비의 변화는 0이 아니게 만드는 것이므로, 첫 행이 0이 되는 입력 조합에서 둘째 행이 ρ를 실제로 움직일 수 있는지를 봅니다. 행렬이 정사각이 아니므로 역행렬이나 행렬식이 아니라 rank와 특이값, 그리고 실제 입력 한계로 판정합니다. 여러 운전점에서 ρ가 어떻게 변하는지 보는 지도와, 한 점 주위의 이 민감도는 서로 다른 질문이라는 점도 구분하겠습니다.""",
        """식 (9.2) J = [[∂_P n̄_w, ∂_k n̄_w, ∂_φ n̄_w], [∂_P ρ, ∂_k ρ, ∂_φ ρ]]. 각 장과의 연결: 레벨 행은 4장 (4.11) n_* ∝ P_abs와 1.7절의 P_tot ≠ P_abs(결합 효율)에서, 형상 행은 6장 간섭(6.5)이 7장 λ_ε와 8장 ℓ_r을 거쳐 남은 정도에서 온다. 7장 (7.19)의 균일 EEDF 극한에서는 형상 행이 0 → rank 1. 플라즈마 상태를 고정한 선형 사슬에서는 ∂ln n̄_w/∂ln P = 1, ∂ρ/∂P = 0이고, ∂ρ/∂P ≠ 0은 6.4절 되먹임에서 생긴다. φ 열은 sin(φ + ψ)에 비례해 φ + ψ ≈ 0, π에서 1차로 사라진다(저장소 docs/14_개정본_7-9장_연결.md 4절).""")
    return s


def plan():
    s = frame('2차 발표에서는 판정 수학을 계산으로 채운다', '2차 연구 방향',
              '1차는 판정할 질문과 식을 정의했고, 2차는 그 답을 계산한다.',
              '2차 연구는 수행 예정 항목이며, 실제 계산을 완료했다는 진술이 아니다.')
    items = [('1', '물리 모델 연결', '0D 입자·전력 균형과 2D 유도장·생성·양극성 확산을 연결해 최종 n(r, z)의 정상상태를 분석한다.'),
             ('2', '운전 영역 탐색', 'p, P_{tot}, k, φ를 바꾸며 n̄_{w}와 ρ의 운전점 지도를 작성한다.'),
             ('3', '독립성 검증', '선택한 동작점에서 정적 Jacobian을 구하고, 평균 밀도 유지 조건의 형상 감도를 비교한다. 국소 생성 근사와 비국소 수송 근사의 차이도 함께 평가한다.')]
    y = 1.55
    for n, t, d in items:
        box(s, 0.5, y, 9.0, 1.28, fill=None, line=LINE, radius=None)
        tb(s, 0.65, y + 0.12, 0.5, 0.6, n, size=26, bold=True, color=NAVY)
        tb(s, 1.25, y + 0.14, 8.1, 0.35, t, size=15, bold=True, color=NAVY)
        tb(s, 1.25, y + 0.52, 8.1, 0.72, d, size=13.5, color=TEXT)
        y += 1.4
    reg(s, 'plan', 35, """2차에서는 이 판정 수학을 실제 계산으로 채우겠습니다. 먼저 0D 균형과 2D 장, 생성, 확산을 연결해 정상상태 밀도 분포를 구합니다. 다음으로 압력, 전력, 전류비, 위상을 바꾸며 평균 밀도와 밀도비의 지도를 만들고, 마지막으로 고른 동작점에서 Jacobian을 구해 평균 밀도를 지키면서 형상을 움직일 수 있는지, 그리고 그 결론이 국소 생성 근사와 비국소 근사에서 어떻게 달라지는지 확인하겠습니다. 감사합니다.""",
        """문서 10장. 각 항목과 앞 장의 대응: 1 → 4–8장의 식, 2 → 9.2절 동작점 지도, 3 → 식 (9.2)–(9.3)과 7장 두 극한. 저장소의 2-영역 0D 모델과 응답 행렬 계산(sim/)은 3번의 예비 도구다.""")
    return s


# ================================================================== 조립
def build(mode):
    global prs, OLD, LAYOUT, MARK, META, WARN
    prs = Presentation(SRC)
    OLD = list(prs.slides)
    LAYOUT = next(l for l in prs.slide_layouts if l.name == '제목만')
    MARK = mode == 'full'
    META, WARN = {}, []
    core = mode == 'core'

    title = s_title(mode)
    if core:
        toc_rows = [['1  연구 배경과 문제 정의', 'ICP 가열, 단일 코일의 한계, 평가 영역과 목표, 선행연구, 제어 노브', '3–7'],
                    ['2  모델의 가정과 구조', '기본 가정, 세 물리 과정, 0D 입자·전력 균형', '8–10'],
                    ['3  전자기 결합', '복소 전도도와 흡수, 두 코일 간섭, 포트 결합과 되먹임', '11–13'],
                    ['4  에너지 수송과 확산', '에너지 완화 길이, 생성 모델의 두 극한, 확산·벽 손실, 반경 혼합 길이', '14–17'],
                    ['5  판정과 2차 방향', '2×3 Jacobian 판정, 2차 연구 계획', '18–19']]
        toc = s_toc(mode, toc_rows, '질의응답 4분. 참고문헌 20쪽, 부록 A1–A33(21쪽부터): 본편에서 뺀 유도 전체.',
                    '흡수 분포에서 최종 밀도까지 따라간 뒤, 독립 제어의 판정 기준을 세운다.')
        main = [title, toc, c_icp(), c_single(), c_chamber(), s_kc(), c_knob(), c_assume(), couplings(False),
                c_0d(), c_em(), interf(True), c_port(), energy_slide(True), c_extremes(), c_diff(), lr_slide(True),
                judge(), plan(), s_refs()]
        apx = [d_icp(), d_single(), d_chamber(), d_knob1(), d_knob2(), d_assume(1), d_assume(2),
               d_0d1(), d_0d2(), d_0d3(), d_em1(), d_em2(), d_tc1(with31=True), d_tc3(), d_tc4(),
               energy_slide(False), d_et2(), d_et3(), d_et4(), d_et5(), d_et6(),
               d_df1(), d_df2(), d_df3(), d_df4(), d_df5(), d_df6(), d_df7(), d_df8(), d_df9(),
               d_df10(), d_df11(), lr_slide(False)]
    else:
        toc_rows = [['1  연구 배경과 문제 정의', 'ICP 가열, 단일 코일, 평가 영역, 선행연구, 제어 노브 (1장)', '3–8'],
                    ['2  모델의 가정과 0D', '가정, 세 물리 과정, 입자·전력 균형 (2–4장)', '9–14'],
                    ['3  전자기 결합', '복소 전도도, 흡수, 간섭, 반사 임피던스, 되먹임 (5–6장)', '15–20'],
                    ['4  전자 에너지 수송', '완화 길이, 에너지 보존, 국소 생성, 균일 EEDF (7장)', '21–26'],
                    ['5  확산과 벽 손실', '양극성 확산, 평판·원통 해, Robin, 반경 혼합 길이 (8장)', '27–38'],
                    ['6  판정과 2차 방향', '2×3 Jacobian, 2차 연구 계획 (9–10장)', '39–40']]
        toc = s_toc(mode, toc_rows, '빨간 상자: 핵심 수식(핵심 수식판 본편의 식). 식 번호는 문서와 같다. 참고문헌 41쪽.',
                    '문서의 모든 식을 순서대로 유도하고, 판정에 필요한 식을 빨간 상자로 표시했다.')
        main = [title, toc, d_icp(), d_single(), d_chamber(), s_kc(), d_knob1(), d_knob2(), d_assume(1), d_assume(2),
                couplings(True), d_0d1(), d_0d2(), d_0d3(), d_em1(), d_em2(), d_tc1(), interf(False), d_tc3(), d_tc4(),
                energy_slide(False), d_et2(), d_et3(), d_et4(), d_et5(), d_et6(),
                d_df1(), d_df2(), d_df3(), d_df4(), d_df5(), d_df6(), d_df7(), d_df8(), d_df9(), d_df10(), d_df11(),
                lr_slide(False), judge(), plan(), s_refs()]
        apx = []

    # 부록 제목·소제목
    for i, s in enumerate(apx, 1):
        t = s.shapes.title.text_frame.text
        full = f'부록 A{i} · {t}'
        set_title(s, full, 22 if len(full) <= 27 else 20 if len(full) <= 31 else 18)
        for sh in s.shapes:
            if sh.name == '소제목':
                sh.text_frame.paragraphs[0].runs[0].text = '부록  ·  ' + sh.text_frame.paragraphs[0].runs[0].text
    order = main + apx

    # 순서 정리
    keep = {id(x) for x in order}
    lst = prs.slides._sldIdLst
    id_of = {id(sl): sid for sl, sid in zip(prs.slides, list(lst))}
    for sl, sid in list(zip(prs.slides, list(lst))):
        if id(sl) not in keep:
            prs.part.drop_rel(sid.get(qn('r:id')))
            lst.remove(sid)
    for sid in list(lst):
        lst.remove(sid)
    for sl in order:
        lst.append(id_of[id(sl)])

    # 쪽 번호, 표시, 노트
    t = 0
    for n, sl in enumerate(order, 1):
        is_apx = n > len(main)
        if n > 2 and not any(x.name == '쪽 번호' for x in sl.shapes):
            pnum(sl, n)
        if is_apx:
            sl._element.set('show', '0')
        elif sl._element.get('show') == '0':
            del sl._element.attrib['show']
        m = META[id(sl)]
        if is_apx:
            txt = f'[부록 A{n - len(main)} · 질의응답용]\n{m["script"]}\n\n[근거(읽지 않음)]\n{m["basis"]}'
        elif m['secs'] == 0:
            txt = f'[참고문헌]\n{m["basis"]}'
        else:
            a, b = t, t + m['secs']
            txt = f'[대본 · {a // 60}:{a % 60:02d}–{b // 60}:{b % 60:02d} / {m["secs"]}초]\n{m["script"]}\n\n[근거(읽지 않음)]\n{m["basis"]}'
            t = b
        txt = re.sub(r'_\{([^}]*)\}', r'_\1', txt)
        txt = re.sub(r'\^\{([^}]*)\}', r'^(\1)', txt)
        sl.notes_slide.notes_text_frame.text = txt
    prs.core_properties.author = '주제 3 팀'
    prs.core_properties.last_modified_by = '주제 3 팀'
    prs.core_properties.title = '중앙·가장자리 플라즈마 밀도 독립 제어의 이론적 배경'
    prs.save(OUTS[mode])
    print(mode, 'saved', len(order), 'slides, main', len(main), f'talk {t // 60}:{t % 60:02d}')
    for w in WARN:
        print('  WARN', w)


if __name__ == '__main__':
    for mode in (sys.argv[1:] or ['core', 'full']):
        build(mode)
