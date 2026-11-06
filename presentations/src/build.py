import sys, os, json, math, zipfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib
from lib import *
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_MARKER_STYLE, XL_TICK_LABEL_POSITION, XL_TICK_MARK, XL_AXIS_CROSSES

TEMPLATE = sys.argv[1]
OUT = sys.argv[2]
lib.EQ_DIR = os.path.join(HERE, 'eq')
lib.EQ_SIZES = json.load(open(os.path.join(HERE, 'eq', 'sizes.json')))

prs = Presentation(TEMPLATE)
lst = prs.slides._sldIdLst
for sid in list(lst):
    prs.part.drop_rel(sid.rId); lst.remove(sid)
LAY_TITLE, LAY_TONLY = prs.slide_layouts[0], prs.slide_layouts[5]

ORDER = ['cover', 'summary', 'task', 'criteria', 'chain', 'litmap', 'kc20', 'park', 'questions',
         'scales', 'geometry', 'model', 'predict', 'triangle', 'candidates', 'phase_why', 'phase_cmp',
         'arch', 'control', 'procedure', 'measure', 'verify', 'risks', 'decisions', 'conclusion', 'refs',
         'bk_div', 'bk_reactions', 'bk_field', 'bk_transient', 'bk_matching', 'bk_qmap']
NUM = {k: i + 1 for i, k in enumerate(ORDER)}
BK = {'bk_reactions': 'B1', 'bk_field': 'B2', 'bk_transient': 'B3', 'bk_matching': 'B4', 'bk_qmap': 'B5'}

def R(text):
    if isinstance(text, str):
        for k, v in NUM.items():
            text = text.replace(f'§{k}§', str(v))
    return text

_orig_write = lib.write
def _write_R(tf, paras, **kw):
    if isinstance(paras, str):
        paras = [paras]
    out = []
    for p in paras:
        if isinstance(p, str):
            out.append(R(p))
        else:
            d = dict(p)
            if 't' in d:
                d['t'] = R(d['t'])
            if 'paras' in d:
                d['paras'] = [dict(q, t=R(q['t'])) if isinstance(q, dict) else R(q) for q in d['paras']]
            out.append(d)
    return _orig_write(tf, out, **kw)
lib.write = _write_R
write = _write_R

SEC = {k: C['INDIGO'] for k in ('개요', 'Ⅰ', 'Ⅱ', 'Ⅲ', 'Ⅳ', 'Ⅴ', 'Ⅵ', '결론', '참고')}
SEC['백업'] = C['MUTED']
# 색의 뜻: 파랑 = 중앙·안쪽 코일, 주황 = 가장자리·바깥 코일, 남색 = 구조·선택, 호박색 = 한계·빈 곳·누설
QCOL = {'기준': C['MUTED'], 'Q1': C['INDIGO'], 'Q2': C['INDIGO'], 'Q3': C['INDIGO']}
QLIGHT = {'기준': C['PANEL'], 'Q1': C['INDIGO_L'], 'Q2': C['INDIGO_L'], 'Q3': C['INDIGO_L']}
KIND_FILL = {'o': C['ORANGE_L'], 'b': C['BLUE_L'], 'n': C['NAVY_L'], 'i': C['INDIGO_L'], 'g': C['PANEL'], 'a': C['AMBER_L'], 'w': 'FFFFFF'}
KIND_COL = {'o': C['ORANGE_D'], 'b': C['BLUE'], 'n': C['NAVY'], 'i': C['INDIGO'], 'g': C['INDIGO'], 'a': C['AMBER'], 'w': C['INDIGO']}
built = {}

def new(key, kicker, title, sec):
    s = prs.slides.add_slide(LAY_TONLY)
    t = s.shapes.title
    tf = t.text_frame
    p = tf.paragraphs[0]
    for txt, st in parse(R(title)):
        r = p.add_run(); r.text = txt; r.font.size = Pt(28)
        if st.get('baseline'):
            r._r.get_or_add_rPr().set('baseline', st['baseline'])
    tb(s, 0.47, 0.92, 9.0, 0.3, [R(kicker)], size=12, bold=True, color=SEC[sec], name='구분')
    slide_number(s, NUM[key])
    built[key] = s
    return s

def foot(s, text, y=6.6, h=0.3):
    tb(s, 0.5, y, 9.0, h, [R(text)], size=10, color=C['MUTED'], name='각주', line=1.0)

def take(s, x, y, w, h, text, kind='i', size=14, lead='→'):
    fill = KIND_FILL[kind]
    code = {'o': 'o', 'b': 'b', 'n': 'n', 'i': 'i', 'g': 'm', 'a': 'a'}[kind]
    return box(s, x, y, w, h, fill=fill, radius=0.08, paras=[f'[[{code}:{lead}]] ' + R(text) if lead else R(text)],
               size=size, anchor='m', margin=0.14, name='핵심 메시지')

def panel(s, x, y, w, h, head, body, kind='g', size=13, head_size=13, after=3, fill=None, line=None):
    fillc = fill or KIND_FILL[kind]
    hc = KIND_COL[kind]
    paras = [dict(t=R(head), bold=True, color=hc, size=head_size, after=4)] if head else []
    for b in body:
        d = b if isinstance(b, dict) else {'t': b}
        d = dict(d); d['t'] = R(d['t'])
        paras.append(d)
    return box(s, x, y, w, h, fill=fillc, line=line, radius=0.08, paras=paras, size=size, margin=0.13,
               space_after=after)

def chip(s, x, y, w, h, text, fill, color='FFFFFF', size=12, bold=True, radius=0.06):
    return box(s, x, y, w, h, fill=fill, radius=radius, paras=[R(text)], size=size, color=color, bold=bold,
               align='c', anchor='m', margin=0.03)

def band_behind(s, cx, cy, cw, chh, lay, vmin, vmax, lo, hi, fill=None):
    x0 = cx + cw * lay[0]; w = cw * lay[2]
    y0 = cy + chh * lay[1]; h = chh * lay[3]
    ytop = y0 + h * (vmax - hi) / (vmax - vmin)
    ybot = y0 + h * (vmax - lo) / (vmax - vmin)
    return box(s, x0, ytop, w, ybot - ytop, fill=fill or C['TARGET'], radius=None, name='목표 띠')

def style_chart(ch, size=11):
    ch.font.size = Pt(size); ch.font.name = 'Arial'; ch.font.color.rgb = rgb(C['TEXT'])
    chart_no_fill(ch)

def style_axis(ax, mn=None, mx=None, major=None, fmt=None, grid=False, size=11):
    if mn is not None: ax.minimum_scale = mn
    if mx is not None: ax.maximum_scale = mx
    if major is not None: ax.major_unit = major
    ax.has_major_gridlines = grid
    if grid:
        ax.major_gridlines.format.line.color.rgb = rgb('DDE1E8'); ax.major_gridlines.format.line.width = Pt(0.75)
    ax.format.line.color.rgb = rgb('9AA3B5')
    ax.tick_labels.font.size = Pt(size); ax.tick_labels.font.color.rgb = rgb(C['MUTED'])
    if fmt:
        ax.tick_labels.number_format = fmt; ax.tick_labels.number_format_is_linked = False
    ax.major_tick_mark = XL_TICK_MARK.NONE; ax.minor_tick_mark = XL_TICK_MARK.NONE

def label_point(pt, text, pos, size=11, color=None, bold=False):
    dl = pt.data_label
    dl.has_text_frame = True
    tf = dl.text_frame
    p = tf.paragraphs[0]
    for txt, st in parse(text):
        r = p.add_run(); r.text = txt
        style_run(r, size=size, bold=st.get('bold', bold), color=color or C['TEXT'], baseline=st.get('baseline'))
    dl.position = pos


# ---------------------------------------------------------------- v4: 이론 학습 중심
# 흐름: 주제와 학습 범위 → ICP 밀도 분포의 원리 → 조절 수단의 원리 → 측정 이론 → 주제와의 연결(2차 방향)
ORDER = ['cover', 'toc', 'topic', 'target', 'criteria',
         'chain', 'eh', 'f1', 'f2', 'f3', 'f4', 'f5', 'park', 'f6', 'f7',
         'knobs', 'lc', 'kc20', 'p_phase', 'field',
         'diag', 'measure',
         'simple', 'p_pressure', 'direction', 'plan',
         'conclusion', 'refs',
         'bk_div', 'arch', 'why', 'bk_drive', 'p_phase_cmp', 'control', 'procedure', 'verify', 'stages',
         'bk_reactions', 'bk_transient', 'bk_matching', 'bk_qmap']
NUM.clear(); NUM.update({k: i + 1 for i, k in enumerate(ORDER)})
BKCODE = {k: f'B{i + 1}' for i, k in enumerate(ORDER[ORDER.index('bk_div') + 1:])}
SEC.update({k: C['INDIGO'] for k in ('S1', 'S2', 'S3', 'S4', 'S5', '정리', '참고', '목차')})
SEC['백업'] = C['MUTED']
K1, K2, K3, K4, K5 = '1. 주제와 학습 범위', '2. ICP 밀도 분포의 원리', '3. 조절 수단의 원리', '4. 밀도비 측정 이론', '5. 주제와의 연결'

_R_page = R
def R(text):
    """§key§ → 쪽 번호, ¤key¤ → 백업 번호(B1…)."""
    text = _R_page(text)
    if isinstance(text, str):
        for k, v in BKCODE.items():
            text = text.replace(f'¤{k}¤', v)
    return text

def eqw(name, pt):
    s_ = lib.EQ_SIZES[name]
    return s_['w'] / 96 * pt / 30, s_['h'] / 96 * pt / 30

# 통일 규칙: 본문은 y 1.42–5.75 안, 핵심 메시지 한 줄은 5.88, 각주 한 줄은 6.47
BODY_Y, BODY_END, TAKE_Y, TAKE_H, FOOT_Y = 1.42, 5.75, 5.88, 0.55, 6.47

def msg(s, text, kind='i'):
    """슬라이드마다 하나뿐인 핵심 메시지 (한 줄, 13.5 pt, 색은 하나로 통일)."""
    shp = take(s, 0.5, TAKE_Y, 9.0, TAKE_H, text, kind='i', size=13.5)
    for p_ in shp.text_frame.paragraphs:
        for r_ in p_.runs:
            if r_.text.strip() == '→':
                r_.font.name = '맑은 고딕'
    return shp

def note(s, text):
    """출처·계산 조건만 담는 각주 (한 줄, 10 pt)."""
    return foot(s, text, y=FOOT_Y, h=0.3)

def tracker(s, active):
    tb(s, 5.9, 0.93, 1.3, 0.28, ['공식 사슬'], size=10.5, color=C['MUTED'], align='r', anchor='m')
    x0 = 7.38
    for i in range(1, 8):
        cx = x0 + (i - 1) * 0.31
        if i < 7:
            seg(s, cx + 0.12, 1.07, cx + 0.19, 1.07, color='C9CED8', w=1)
        on = (i == active)
        circle(s, cx, 1.07, 0.24, fill=C['INDIGO'] if on else C['PANEL'], line=None if on else 'C9CED8', lw=0.75,
               paras=[str(i)], size=10, color='FFFFFF' if on else C['MUTED'])

def fchip(s, x, y, n, w=0.6):
    return chip(s, x, y, w, 0.3, f'식 {n}', C['INDIGO'], size=12, radius=0.05)

def link(s, x, y, w, text, size=12):
    """앞뒤 식을 잇는 한 줄 (← 식 k / → 식 k)."""
    return tb(s, x, y, w, 0.3, [text], size=size, color=C['MUTED'], anchor='m')

# =================================================================== 1 cover
s = prs.slides.add_slide(LAY_TITLE)
built['cover'] = s
ph = {p.placeholder_format.idx: p for p in s.placeholders}
tf = ph[0].text_frame
for i, line in enumerate(['중앙·가장자리 밀도비의', '독립 제어']):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    r = p.add_run(); r.text = line; r.font.size = Pt(36)
write(ph[1].text_frame, [dict(t='플라즈마 전자공학 IC-PBL · 주제 3 · 1차 발표', size=18, bold=True, color=C['INDIGO'], after=8),
                         dict(t='2차 설계를 위한 이론 학습: 밀도 분포의 원리, 조절 수단, 측정', size=15, color=C['TEXT'], after=14),
                         dict(t='주제 3 팀 · 2026. 11.', size=14, color=C['MUTED'])], align='c')
notes(s, '인사 후 발표 범위를 한 줄로 말한다. 1차 발표는 2차 발표 주제인 “중앙·가장자리 밀도비의 독립 제어”를 설계하는 데 필요한 이론을 공부하고, 그 이론이 주제와 어떻게 이어지는지를 설명하는 자리다.\n'
         '수치 옆의 (계산)·(추정)·(가정) 표시는 값의 출처를 구분한 것이다.')

# =================================================================== 2 toc
s = new('toc', '발표 흐름 · 장마다 답하는 질문', '목차: 이론 학습에서 2차 설계 방향까지', '목차')
chapters = [('1', '주제와 학습 범위', '무엇을 맞추고, 무엇을 공부해야 하나?', '과제 · 목표 밀도비 R · 독립성 판정 J', '§topic§–§criteria§'),
            ('2', 'ICP 밀도 분포의 원리', '코일 전류가 어떤 원리로 밀도 분포가 되나?', '유도 결합 · 식 1–7 공식 사슬 · 선행 연구 [Pa17]', '§chain§–§f7§'),
            ('3', '조절 수단의 원리', '조절 수단 여섯 가지는 각각 무엇을 바꾸나?', '수단 개요 · LC 공진 · 선행 연구 KC20 · 위상 · 자기장', '§knobs§–§field§'),
            ('4', '밀도비 측정 이론', '밀도비와 그 변화를 어떻게 재나?', '진단 방법 비교 · FHP 배열과 전체/분포 분리', '§diag§–§measure§'),
            ('5', '주제와의 연결', '이론은 2차 설계에 무엇을 말해 주나?', '단순 제어의 한계 · 운전 압력 · 설계 방향 · 2차 계획', '§simple§–§plan§')]
y = 1.45
for n, head, q, cont, pg in chapters:
    box(s, 0.5, y, 9.0, 0.76, fill=C['PANEL'], radius=0.08)
    circle(s, 0.88, y + 0.38, 0.5, fill=C['INDIGO'], paras=[n], size=16, color='FFFFFF')
    tb(s, 1.3, y, 2.55, 0.76, [head], size=15, bold=True, color=C['INDIGO'], anchor='m')
    tb(s, 3.85, y + 0.06, 4.75, 0.66, [dict(t=q, size=13, after=2), dict(t=cont, size=12, color=C['MUTED'])], anchor='m', space_after=0)
    tb(s, 8.55, y, 0.85, 0.76, [pg + '쪽'], size=12, color=C['MUTED'], anchor='m', align='r')
    y += 0.86
tb(s, 0.5, 5.82, 9.0, 0.32, ['정리 §conclusion§쪽 · 참고문헌 §refs§쪽 · 백업 §bk_div§–§bk_qmap§쪽 (B1–B12)'], size=12, color=C['MUTED'], align='c', anchor='m')
notes(s, '1차 발표는 2차 발표 주제를 설계하는 데 필요한 이론을 공부하고, 그 이론이 주제와 어떻게 이어지는지 설명하는 순서로 간다.\n'
         '1장에서 과제와 목표, 독립성을 판정하는 기준을 정한다. 2장은 ICP에서 코일 전류가 밀도 분포가 되기까지의 원리를 유도 결합의 기초와 일곱 개의 식으로 따라간다. 3장은 주제안이 제시한 조절 수단 여섯 가지가 각각 어떤 원리로 무엇을 바꾸는지 본다. 4장은 밀도비와 그 변화를 재는 진단 이론이다. 5장에서 이 이론들이 2차 설계에 무엇을 말해 주는지, 즉 단순 제어의 한계와 설계 방향, 2차 발표 계획을 정리한다.\n'
         '2장 슬라이드 오른쪽 위의 “공식 사슬” 표시가 지금 어느 식을 보고 있는지 알려 준다.')

# =================================================================== 3 topic
s = new('topic', f'{K1} · 과제와 학습 범위', '주제 3: 중앙과 가장자리 밀도를 따로 조절한다', 'S1')
panel(s, 0.5, 1.42, 5.0, 1.6, '과제 (IC-PBL 주제안 3번)', [
    dict(t='하나의 챔버에서 중앙부와 가장자리의 플라즈마 밀도를 독립적으로 조절하는 소스를 설계한다', bullet=True),
    dict(t='배경: 코일 하나의 전력을 바꾸면 여러 위치의 밀도가 함께 변한다', bullet=True, color=C['DARK'])],
    kind='i', size=13, after=5)
box(s, 5.7, 1.42, 3.8, 1.6, fill=C['PANEL'], radius=0.08)
tb(s, 5.85, 1.5, 3.5, 0.3, ['제어 목표'], size=12.5, bold=True, color=C['INDIGO'])
eq(s, 'eq_R', 5.95, 1.88, pt=19)
rows = [['검토 사항', '질문 요지', '필요한 이론 (쪽)'],
        ['1', '어떤 조절 수단을 조합하고, 각 수단은 어디에 영향을 주나', '조절 수단의 원리 (§knobs§–§field§)'],
        ['2', '한 영역을 바꿀 때 다른 영역도 변하는 원인 (전자기 결합, 확산)', '밀도 분포의 원리 (§chain§–§f7§)'],
        ['3', '한 영역을 유지하며 다른 영역을 바꾸는 순서와 보상', '전력 균형과 응답 행렬 (§f4§–§f7§)'],
        ['4', '밀도비 확인, 전체 변화와 분포 변화의 구분', '측정·진단 이론 (§diag§–§measure§)']]
table(s, 0.5, 3.2, [1.05, 5.0, 2.95], rows, size=12.5, row_h=0.4, col_align=['c', 'l', 'l'],
      bold_cells={(i, 0) for i in range(1, 5)}, colors={(i, 0): C['INDIGO'] for i in range(1, 5)})
tb(s, 0.5, 5.32, 1.15, 0.36, ['2차 제출물'], size=12.5, bold=True, color=C['INDIGO'], align='c', anchor='m')
xx = 1.7
for code, txt, w_ in [('①', '소스·구동부 구성도', 2.05), ('②', '조작 변수와 밀도 응답', 2.25),
                      ('③', '조정 절차', 1.65), ('④', '측정 계획', 1.65)]:
    box(s, xx, 5.32, w_, 0.36, fill=C['INDIGO_L'], radius=0.06,
        paras=[f'[[i:{code}]] {txt}'], size=12, align='c', anchor='m', margin=0.02)
    xx += w_ + 0.05
msg(s, '1차 발표: 2차 설계에 필요한 이론(분포 원리·조절 수단·측정)을 공부하고 주제와 잇는다')
notes(s, '우리가 맡은 주제 3은 하나의 챔버에서 중앙부와 가장자리의 밀도를 독립적으로 조절하는 소스를 설계하는 것이다. 핵심은 두 영역을 함께 올리고 내리는 것이 아니라, 중앙/가장자리 밀도비를 원하는 값으로 맞추는 것이다. 이 설계와 제출물 네 가지는 2차 발표에서 낸다.\n'
         '1차 발표는 그 설계에 필요한 이론을 공부하는 자리다. 표는 검토 사항 네 가지에 답하려면 어떤 이론이 필요한지, 그 이론을 몇 쪽에서 다루는지 보여 준다. 상호 영향의 원인(검토 2)은 2장의 밀도 분포 원리, 조절 수단(검토 1)은 3장, 조작 순서와 보상(검토 3)은 2장 후반의 전력 균형과 응답 행렬, 측정(검토 4)은 4장의 진단 이론이 바탕이다.')

# =================================================================== 4 target
s = new('target', f'{K1} · 목표', '목표: 밀도가 아니라 밀도비 R을 맞춘다', 'S1')
cx, cy = 2.45, 3.5
sc = 0.086
tb(s, 0.5, 1.42, 3.9, 0.3, ['위에서 본 챔버와 웨이퍼'], size=12.5, bold=True, color=C['INDIGO'], align='c')
circle(s, cx, cy, 2 * 20 * sc, fill='F7F8FA', line=C['NAVY'], lw=1.5)
circle(s, cx, cy, 2 * 15 * sc, fill='E3E8F0', line='9AA3B5', lw=1.0)
box(s, cx - 14 * sc, cy - 14 * sc, 28 * sc, 28 * sc, fill=C['ORANGE'], shape=MSO_SHAPE.DONUT, radius=None, adj=[0.5 / 28 * 1.6], name='가장자리 띠')
circle(s, cx, cy, 2 * 2.5 * sc, fill=C['BLUE'])
tb(s, cx - 1.0, cy + 0.26, 2.0, 0.5, ['중앙', 'r ≤ 25 mm 평균'], size=12, bold=True, color=C['BLUE'], align='c', space_after=0)
box(s, cx - 1.05, cy - 14 * sc - 0.17, 2.1, 0.34, fill='FFFFFF', line=C['ORANGE'], lw=1, radius=0.06,
    paras=['가장자리 r = 135–140 mm'], size=12, bold=True, color=C['ORANGE_D'], align='c', anchor='m', margin=0.02)
tb(s, 0.5, 5.33, 3.9, 0.3, ['웨이퍼 300 mm · 측벽 r = 200 mm'], size=12, color=C['DARK'], align='c')
eq(s, 'eq_R', 4.85, 1.42, pt=22)
tb(s, 7.15, 1.5, 2.35, 0.7, ['측정 높이:', '웨이퍼 위 1–2 cm'], size=12.5, color=C['DARK'], anchor='m', space_after=0)
box(s, 4.85, 2.4, 4.65, 1.0, fill=C['INDIGO_L'], line=C['INDIGO'], lw=1.5, radius=0.08, paras=[
    dict(t='목표 (제안, 팀 합의)', bold=True, size=12.5, color=C['INDIGO'], after=3),
    dict(t='R 0.8–1.2를 연속 조정, 그동안 n̄ 변화 ±5% 안', size=14, bold=True)], margin=0.13, anchor='m')
for j, (head, body) in enumerate([('운전 조건', 'Ar, 13.56 MHz, 5–30 mTorr, 유도 결합(H) 모드'),
                                  ('분석 범위', '정상 상태에서 R 설정값을 바꾸는 준정적 문제 (과도 상황은 백업 ¤bk_transient¤)')]):
    panel(s, 4.85, 3.55 + j * 1.1, 4.65, 0.98, head, [body], kind='g', size=13, head_size=12.5)
msg(s, '출력은 n̄와 R 두 개다. R만 보면 전체 밀도가 함께 움직여도 놓친다')
note(s, '수치 옆 표시: (계산) 모델·스크립트 값 · (추정) 차수 어림 · (가정) 근거 없이 둔 값')
notes(s, '과제 문장을 “밀도비를 원하는 값으로 조정”으로 읽었다. 그래서 목표는 밀도를 올리고 내리는 것이 아니라 R = n_center / n_edge를 맞추는 것이다.\n'
         '출력은 평균 밀도 n̄와 R 두 개로 잡는다. R만 보면 두 영역이 같이 올라가도 모르기 때문이다. 중앙은 반지름 25 mm 안의 평균, 가장자리는 135–140 mm 띠로 정의했고, 웨이퍼 위 1–2 cm에서 잰다.\n'
         '목표 R 0.8–1.2와 n̄ ±5%는 제안값이라 팀 합의가 필요하다.')

# =================================================================== 5 criteria
s = new('criteria', f'{K1} · 판정 기준', '독립성은 응답 행렬 J의 모양으로 판정한다', 'S1')
eq(s, 'eq_J', 0.55, 1.42, pt=19)
tb(s, 5.75, 1.45, 3.75, 1.05, ['P_{tot}: 총 흡수 전력, x: 중앙 전력 몫 P_{c}/P_{tot}',
                               '로그를 쓰면 원소가 상대 변화의 비 → 압력·전력이 달라도 같은 기준으로 비교'], size=12.5, space_after=4)
cards = [('L0', '동반 변화', '두 영역이 함께 오르내린다', ['판정: J의 두 열이', '거의 평행 (조건수 매우 큼)'], C['GRAY'], C['PANEL'], None),
         ('L1', '보상 가능한 독립', '조작은 섞이지만 보상하면 한쪽을 유지', ['판정: J 가역,', '조건수가 측정 오차에 비해 작음'], C['NAVY'], C['NAVY_L'], '최소 요구'),
         ('L2', '구조적 독립', '한 조작이 다른 출력을 거의 안 움직임', ['판정: 열마다', '비대각/대각 ≤ 0.1'], C['INDIGO'], C['INDIGO_L'], '목표')]
x = 0.5
Y0 = 2.62
for lv, name, mean, crit, col, light, tag in cards:
    w = 2.88
    box(s, x, Y0, w, 3.05, fill=light, line=col if tag else None, lw=1.5, radius=0.1)
    if tag:
        chip(s, x + 0.1, Y0 + 0.1, 0.95, 0.3, tag, col, size=12, radius=0.05)
    mx, my, cs = x + w / 2 - 0.42, Y0 + 0.17, 0.38
    shades = {'L0': [[col, col], ['B8BECB', 'B8BECB']], 'L1': [[col, '8FA9C9'], ['8FA9C9', col]], 'L2': [[col, None], [None, col]]}[lv]
    for i in range(2):
        for j in range(2):
            f = shades[i][j]
            box(s, mx + j * (cs + 0.06), my + i * (cs + 0.06), cs, cs, fill=f, line=None if f else 'B8BECB', lw=1, radius=0.04)
    tb(s, x + 0.15, Y0 + 1.1, w - 0.3, 0.4, [f'{lv} {name}'], size=16, bold=True, color=col if lv != 'L0' else C['DARK'], align='c')
    tb(s, x + 0.18, Y0 + 1.57, w - 0.36, 0.7, [mean], size=13.5, align='c')
    box(s, x + 0.15, Y0 + 2.28, w - 0.3, 0.62, fill='FFFFFF', radius=0.06, paras=[dict(t=c_, after=0) for c_ in crit], size=12.5, anchor='m', align='c', margin=0.06)
    x += w + 0.18
msg(s, '과제의 “독립”은 최소 L1, 목표는 L2로 읽는다. J의 실제 값은 식 7에서 계산한다')
note(s, '기준 0.1은 측정 불확도(ln R_{Γ} 1.1%, R 3.7%, 24쪽)보다 충분히 큰 값으로 고른 제안값')
notes(s, '독립성을 말로만 하지 않기 위해 응답 행렬 J로 정의했다. 조작은 총 흡수 전력과 중앙 전력 몫 x, 출력은 ln n̄와 ln R이다. 로그를 쓰면 J의 원소가 상대 변화의 비가 된다.\n'
         'L0은 두 열이 거의 평행해 어떤 조합으로도 한쪽만 움직일 수 없는 상태, L1은 섞이지만 역행렬로 보상하면 한쪽을 유지할 수 있는 상태, L2는 한 조작이 다른 출력을 거의 건드리지 않는 상태다. 과제는 최소 L1, 가능하면 L2를 요구한다고 해석했다. 기준 0.1은 측정 불확도보다 충분히 큰 값으로 고른 제안값이다.\n'
         '이 J의 실제 값은 다음 장에서 공식을 이어 계산하고, 2장 마지막(식 7)에 다시 보여 준다.')

# =================================================================== chain
s = new('chain', f'{K2} · 전체 사슬 · 검토 사항 2', '조작에서 밀도비까지: 공식 일곱 개의 사슬', 'S2')
stages = [('회로·장', '1', 'V = Z·I', '코일 전류 → 영역 전력', ['상호 인덕턴스', '공통 전원', '플라즈마 2차측', '장 중첩', '창 축전 결합'], 'n', '구동부가 정함'),
          ('가열', '2', 'λ_{ε} ∝ 1/p', '흡수 위치 → 이온화 위치', ['비국소 가열'], 'a', '압력이 정함'),
          ('생성·손실', '3–5', 'n_{k} ∝ P_{k}/A_{eff,k}', '영역 전력 → 영역 밀도', ['측벽 손실 비대칭 (가장자리만)'], 'g', '총 전력으로 보상'),
          ('확산', '6', 'ℓ = L/π', '영역 밀도 → 측정 위치', ['영역 간 확산'], 'a', '형상이 정함'),
          ('응답', '7', 'Δy = J·Δu', '조작 → (n̄, R)', ['L0 / L1 / L2 판정'], 'i', '판정')]
w, gap = 1.56, 0.3
for i, (nm, fn, ftxt, sub, leaks, k, tag) in enumerate(stages):
    x = 0.5 + i * (w + gap)
    col = {'n': C['NAVY'], 'a': C['AMBER'], 'g': C['GRAY'], 'i': C['INDIGO']}[k]
    box(s, x, 1.45, w, 1.7, fill='FFFFFF', line=col, lw=2, radius=0.08)
    tb(s, x, 1.52, w, 0.3, [nm], size=14, bold=True, color=col if k != 'g' else C['DARK'], align='c')
    chip(s, x + w / 2 - 0.38, 1.86, 0.76, 0.3, f'식 {fn}', C['INDIGO'], size=12, radius=0.05)
    tb(s, x + 0.04, 2.18, w - 0.08, 0.32, [ftxt], size=13, bold=True, align='c')
    tb(s, x + 0.04, 2.52, w - 0.08, 0.58, [sub], size=12, color=C['DARK'], align='c')
    if i < 4:
        seg(s, x + w + 0.03, 2.3, x + w + gap - 0.03, 2.3, color=C['NAVY'], w=2, head=True)
    tb(s, x + 0.02, 3.62, w - 0.02, 1.4, [dict(t=l, size=12, after=4) for l in leaks], size=12, bullet=True, bullet_color=col)
    chip(s, x + 0.08, 5.15, w - 0.16, 0.34, tag, {'n': C['NAVY'], 'a': C['AMBER'], 'g': C['GRAY'], 'i': C['INDIGO']}[k], size=12, radius=0.05)
tb(s, 0.5, 3.25, 9.0, 0.3, ['▼ 단계마다 한 영역의 조작이 다른 영역으로 새는 경로'], size=12, bold=True, color=C['MUTED'])
msg(s, '결합이 없다면 R = 전력비 × 손실 비대칭(식 3–5). 실제로는 식 1, 2, 6이 이를 흐린다')
notes(s, '검토 사항 2, 한 영역을 바꿀 때 다른 영역도 변하는 원인을 공식 사슬로 정리했다. 코일 전류는 회로·장 단계(식 1)에서 영역 흡수 전력이 되고, 가열 단계(식 2)에서 실제 이온화 위치가 정해지고, 생성·손실 균형(식 3–5)에서 영역 밀도가 되고, 확산(식 6)을 거쳐 측정 위치의 밀도비가 된다. 마지막 식 7이 이 사슬 전체를 응답 행렬로 요약한다.\n'
         '단계마다 한 영역의 조작이 다른 영역으로 새는 경로가 있다. 남색은 구동부 설계가 정하는 결합, 호박색은 압력과 형상이 정하는 결합이다. 측벽 손실 비대칭은 피할 수는 없지만 총 전력으로 보상할 수 있다. E–H 전이 같은 비선형·이력은 모든 단계에 걸친다.\n'
         '이상적인 경우 R은 전력비로 정해진다. 그런데 식 1, 2, 6이 그 관계를 흐리고, 이것이 5장에서 정리할 “단순 제어의 한계”의 뿌리다. 먼저 유도 결합의 기초를 보고, 사슬 순서대로 식 하나씩 본다.')

# =================================================================== eh
s = new('eh', f'{K2} · 유도 결합의 기초', '유도 결합의 기초: 표피 깊이와 E–H 모드', 'S2')
tracker(s, 0)
chip(s, 0.5, 1.55, 0.6, 0.3, '기초', C['INDIGO'], size=12, radius=0.05)
eq(s, 'eq_skin', 1.2, 1.36, pt=12.5)
tb(s, 4.2, 1.4, 5.3, 0.75, ['n_{e} = 3×10^{10}–10^{11} cm^{−3} → δ_{p} ≈ 1.7–3.1 cm (계산)',
                            '전력은 창 아래 이 얇은 층에서 흡수 → 가열 위치는 코일 반지름이 정한다 (식 1)'],
   size=12, color=C['DARK'], space_after=3)
box(s, 0.5, 2.3, 4.15, 1.62, fill=C['PANEL'], line='B8BECB', radius=0.08, paras=[
    dict(t='E 모드 (축전 결합)', bold=True, size=13.5, color=C['DARK'], after=3),
    dict(t='저전력·저밀도에서 코일 전압이 창을 통해 축전 결합한다', size=12.5, bullet=True, after=2),
    dict(t='분포가 축전 결합을 따라 h-factor 이론과 어긋난다 [Pa17]', size=12.5, bullet=True)], margin=0.13)
box(s, 5.35, 2.3, 4.15, 1.62, fill=C['NAVY_L'], line=C['NAVY'], radius=0.08, paras=[
    dict(t='H 모드 (유도 결합)', bold=True, size=13.5, color=C['NAVY'], after=3),
    dict(t='코일 전류가 만든 유도 전기장 E_{θ}로 가열, 밀도가 크게 뛴다', size=12.5, bullet=True, after=2),
    dict(t='h-factor 이론이 측정과 맞는다 → 2-영역 모델의 전제', size=12.5, bullet=True)], margin=0.13)
seg(s, 4.7, 3.11, 5.3, 3.11, color=C['NAVY'], w=2, head=True)
tb(s, 4.6, 2.7, 0.8, 0.36, ['전력 ↑'], size=12, color=C['MUTED'], align='c', anchor='m')
tb(s, 4.6, 3.18, 0.8, 0.36, ['(이력)'], size=12, color=C['MUTED'], align='c', anchor='m')
box(s, 0.5, 4.1, 9.0, 1.38, fill='FFFFFF', line='C9CED8', radius=0.08)
tb(s, 0.65, 4.17, 8.7, 0.3, ['동작점은 흡수 전력과 손실 전력이 같아지는 밀도다'], size=12.5, bold=True, color=C['INDIGO'])
eq(s, 'eq_pabs', 0.75, 4.55, pt=13)
tb(s, 0.65, 5.0, 8.7, 0.6, ['R_{p}: 코일이 보는 플라즈마 저항. 흡수 곡선과 손실 직선(식 4)의 교점이 여럿이면 E–H 전이에 이력이 생긴다'],
   size=12, color=C['DARK'])
msg(s, '공식 사슬(식 1–7)은 H 모드에서 성립한다 → H 모드를 확인한 뒤 분배를 조절한다')
note(s, 'δ_{p}: 무충돌 표피 깊이 (충돌이 있으면 조금 길어진다). [Pa17] 조건: E 모드 ≈ 20 W, H 모드 ≥ 40 W')
notes(s, '공식 사슬에 들어가기 전에 유도 결합 플라즈마(ICP)의 기초를 짚는다. 코일 전류가 만든 시간 변화 자기장이 창 아래에 유도 전기장을 만들고, 이 장은 표피 깊이 δ만큼만 플라즈마로 들어간다. 무충돌 표피 깊이는 c/ω_pe이고, 우리 밀도 범위에서 약 2–3 cm다. 그래서 전력은 창 바로 아래 얇은 층에서, 코일이 놓인 반지름 근처에서 흡수된다. 가열 위치를 코일 배치로 정할 수 있는 이유다.\n'
         '전력이 낮으면 코일 전압이 창을 통해 축전 결합하는 E 모드이고, 전력을 올리면 유도 결합인 H 모드로 넘어가며 밀도가 크게 뛴다. 동작점은 흡수 전력과 손실 전력이 같아지는 밀도인데, 두 곡선의 교점이 여럿이면 전이에 이력이 생긴다.\n'
         '주제와의 연관: 제공받은 Park 2017 논문은 E 모드에서는 분포가 축전 결합을 따라 h-factor 이론과 어긋나고, H 모드에서는 맞는다는 것을 보였다. 그래서 이 뒤의 공식 사슬은 H 모드를 전제로 하고, 운전에서도 H 모드를 확인한 뒤 분배를 조절해야 한다. 한쪽 코일 전력을 너무 낮추면 그 영역이 E 모드 쪽으로 기울 수 있다는 점도 주의한다.')

# =================================================================== f1
s = new('f1', f'{K2} · 식 1 회로', '식 1: 두 코일은 회로로 묶여 있다', 'S2')
tracker(s, 1)
fchip(s, 0.5, 1.5, '1a')
_, ew, eh = eq(s, 'eq_Z', 1.2, 1.4, pt=13)
tb(s, 7.0, 1.42, 2.5, 0.6, ['Z_{12} ≠ 0: 한 코일 전류가 다른 코일 전압에 들어간다'], size=12, color=C['DARK'], anchor='m')
fchip(s, 0.5, 2.15, '1b')
eq(s, 'eq_Pp', 1.2, 2.07, pt=13)
tb(s, 7.0, 2.05, 2.5, 0.6, ['영역 전력은 전류비 k = I_{2}/I_{1}와 위상 φ로 정해진다'], size=12, color=C['DARK'], anchor='m')
fchip(s, 0.5, 2.78, '1c')
eq(s, 'eq_phase', 1.2, 2.7, pt=13)
tb(s, 7.0, 2.68, 2.5, 0.6, ['같은 주파수면 두 전원이 전력을 주고받는다'], size=12, color=C['DARK'], anchor='m')
# schematic
box(s, 0.6, 3.55, 1.6, 0.6, fill=C['BLUE_L'], line=C['BLUE'], lw=1.75, radius=0.08, paras=[dict(t='안쪽 코일 I_{1}', bold=True, color=C['BLUE'], align='c')], size=12.5, anchor='m')
box(s, 2.75, 3.55, 1.6, 0.6, fill=C['ORANGE_L'], line=C['ORANGE'], lw=1.75, radius=0.08, paras=[dict(t='바깥 코일 I_{2}', bold=True, color=C['ORANGE_D'], align='c')], size=12.5, anchor='m')
seg(s, 2.24, 3.85, 2.71, 3.85, color=C['NAVY'], w=2, head=True, tail=True)
tb(s, 2.05, 3.27, 0.85, 0.28, ['M_{12}'], size=12.5, bold=True, color=C['NAVY'], align='c')
box(s, 0.6, 4.75, 3.75, 0.62, fill=C['PANEL'], line='9AA3B5', lw=1.25, radius=0.08, paras=[dict(t='플라즈마: 두 코일의 공통 2차측 (ΔZ)', bold=True, align='c')], size=12.5, anchor='m')
seg(s, 1.4, 4.17, 1.4, 4.73, color=C['GRAY'], w=1.5, head=True, tail=True)
seg(s, 3.55, 4.17, 3.55, 4.73, color=C['GRAY'], w=1.5, head=True, tail=True)
panel(s, 4.6, 3.45, 4.9, 1.95, '설계 형상에서 계산한 값', [
    dict(t='ωM_{12} = 7.8 Ω (결합 계수 0.16)', bullet=True),
    dict(t='플라즈마 상호 리액턴스 X′_{12} ≈ −4 ~ −6 Ω', bullet=True),
    dict(t='코일 선택도: 안쪽만 켜면 흡수의 0.91–0.95가 중앙, 바깥만 켜면 0.93–0.95가 가장자리', bullet=True),
    dict(t='→ 분배는 중앙 몫 약 0.07–0.93 사이에서만 가능', bullet=False, color=C['DARK'])], kind='g', size=12.5, after=4)
msg(s, '“코일 전력 = 영역 전력”은 Z_{12}와 위상 φ 때문에 깨진다 → 3장 LC 공진·위상')
note(s, '단일 턴 코일, 균일 반공간 근사 [DD68], 밀도 3×10^{10}–10^{11} cm^{−3}, 10–20 mTorr (계산)')
notes(s, '사슬의 첫 고리는 회로다. 두 코일은 상호 인덕턴스 M₁₂와 플라즈마라는 공통 2차측으로 묶여 있어서, 결합 회로 행렬의 비대각 항 Z₁₂가 0이 아니다. 그래서 한 코일의 전류가 다른 코일의 전압과 전력을 바꾼다.\n'
         '플라즈마가 흡수하는 전력은 전류비 k와 위상 φ로 정해지고(식 1b), 두 전원이 같은 주파수면 sin φ에 비례하는 교환 전력이 생긴다(식 1c).\n'
         '설계 형상으로 계산하면 결합 계수는 0.16이고, 한 코일만 켜도 흡수 전력의 5–9%는 다른 영역에 떨어진다. 그래서 분배는 중앙 몫 약 0.07–0.93 사이에서만 조절할 수 있다.\n'
         '정리하면, 단순 제어의 첫 가정인 “코일 전력이 곧 영역 전력”은 회로 결합 때문에 성립하지 않는다. 이것이 3장의 LC 공진과 위상·진폭 조절로 이어진다.')

# =================================================================== f2
s = new('f2', f'{K2} · 식 2 가열', '식 2: 이온화는 λ_{ε}만큼 퍼진다', 'S2')
tracker(s, 2)
cd = XyChartData()
s1 = cd.add_series('g_R')
for k_ in range(2, 61):
    p_ = k_ / 2
    s1.add_data_point(p_, 1 - math.exp(-7.5 * p_ / 119))
s2 = cd.add_series('표시점')
for p_ in [1, 5, 10, 20, 30]:
    s2.add_data_point(p_, 1 - math.exp(-7.5 * p_ / 119))
s3 = cd.add_series('p*')
s3.add_data_point(15.87, 0.0); s3.add_data_point(15.87, 1 - math.exp(-1))
gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_SMOOTH_NO_MARKERS, I(0.5), I(1.4), I(5.0), I(4.25), cd)
gf.name = 'g_R 압력 그래프'
ch = gf.chart; style_chart(ch, size=12); ch.has_legend = False
ser = ch.plots[0].series
ser[0].format.line.color.rgb = rgb(C['INDIGO']); ser[0].format.line.width = Pt(2.75); ser[0].smooth = True
sr = ser[1]; sr.smooth = False; sr.format.line.fill.background()
sr.marker.style = XL_MARKER_STYLE.CIRCLE; sr.marker.size = 9
sr.marker.format.fill.solid(); sr.marker.format.fill.fore_color.rgb = rgb(C['INDIGO']); sr.marker.format.line.color.rgb = rgb('FFFFFF')
sr = ser[2]; sr.smooth = False
sr.format.line.color.rgb = rgb(C['AMBER']); sr.format.line.width = Pt(1.75); sr.format.line.dash_style = MSO_LINE.DASH
sr.marker.style = XL_MARKER_STYLE.NONE
style_axis(ch.category_axis, 0, 30, 5, '0', grid=False, size=12)
style_axis(ch.value_axis, 0, 1.0, 0.2, '0.0', grid=True, size=12)
axis_title(ch.category_axis, '압력 p (mTorr)', size=12); axis_title(ch.value_axis, 'g_{R}', size=12)
lay = (0.14, 0.04, 0.82, 0.78)
plot_layout(ch, *lay)
gx0, gw = 0.5 + 5.0 * lay[0], 5.0 * lay[2]
gy0, gh = 1.4 + 4.25 * lay[1], 4.25 * lay[3]
tb(s, gx0 + gw * 16.6 / 30, gy0 + gh * 0.5, 1.9, 0.56, ['p* ≈ 16 mTorr', '(λ_{ε} = Δ)'], size=12, bold=True, color=C['AMBER'], space_after=0)
fchip(s, 5.7, 1.42, '2a')
eq(s, 'eq_lamdef', 5.7, 1.75, pt=12.5)
eq(s, 'eq_lambda', 5.75, 2.38, pt=13.5)
fchip(s, 5.7, 3.12, '2b')
eq(s, 'eq_wg', 6.35, 3.07, pt=14)
tb(s, 5.7, 3.55, 3.8, 0.8, ['식 1의 영역 전력 중 몫 w는 다른 영역에서 이온화 → g_{R}: 분배가 R을 움직이는 힘 (식 4, 7로)'], size=12, color=C['DARK'])
table(s, 5.7, 4.6, [1.0, 0.56, 0.56, 0.56, 0.56, 0.56], [
    ['p (mTorr)', '1', '5', '10', '20', '30'],
    ['λ_{ε} (cm)', '119', '24', '12', '6.0', '4.0'],
    ['g_{R}', '0.06', '0.27', '0.47', '0.72', '0.85']], size=12, row_h=0.32, col_align=['l', 'c', 'c', 'c', 'c', 'c'],
    bold_cells={(2, j) for j in range(6)}, colors={(2, j): C['INDIGO'] for j in range(6)})
msg(s, '저압에서는 어느 코일에 넣어도 R이 거의 같다 → 운전 압력이 먼저 정해진다 (5장)')
note(s, 'Δ = 7.5 cm: 두 코일 간격. λ_{ε} 기준값 119 cm (1 mTorr, KC20 Fig. 5 계산값). w = e^{−Δ/λε}의 꼴은 가정 → 가설 H1')
notes(s, '두 번째 고리는 가열이다. 코일 아래에서 가열된 전자는 에너지를 잃기 전에 λε만큼 움직인다. λε는 운동량 전달 평균 자유 행로와 에너지 손실 길이의 기하 평균이라 압력에 반비례하고, 1 mTorr에서 119 cm다.\n'
         '식 1이 정한 영역 전력 중 몫 w = e^(−Δ/λε)는 다른 영역에서 이온화된다고 두면, 분배를 바꿨을 때 R이 움직이는 힘은 g_R = 1 − w다. 이 꼴은 가정이고 가설 H1로 확인한다.\n'
         '그래프에서 1 mTorr의 g_R은 0.06이라 어느 코일에 전력을 넣어도 R이 거의 안 바뀐다. λε가 코일 간격 7.5 cm와 같아지는 압력이 약 16 mTorr다. 단순 제어가 가장 먼저 막히는 곳이 바로 여기, 압력이다.')

# =================================================================== f3
s = new('f3', f'{K2} · 식 3 입자 균형', '식 3: T_{e}는 전력이 아니라 기체와 크기가 정한다', 'S2')
tracker(s, 3)
fchip(s, 0.5, 1.55, '3')
ew3, eh3 = eqw('eq_pb', 17)
eq(s, 'eq_pb', 1.2, 1.4, pt=17)
tb(s, 1.2 + ew3 + 0.15, 1.42, 9.5 - (1.2 + ew3 + 0.15), 0.75, ['생성 = 벽 손실', '양변이 T_{e}만의 함수'], size=12.5, color=C['DARK'], anchor='m', space_after=0)
by = 2.55
box(s, 0.5, by, 2.2, 0.72, fill=C['PANEL'], radius=0.08, paras=[dict(t='압력 p', bold=True, align='c', after=0), dict(t='→ 기체 밀도 n_{g}', size=12, align='c')], size=13, anchor='m')
box(s, 0.5, by + 0.85, 2.2, 0.72, fill=C['PANEL'], radius=0.08, paras=[dict(t='형상 R, L, h', bold=True, align='c', after=0), dict(t='→ 유효 길이 d_{eff}', size=12, align='c')], size=13, anchor='m')
path(s, [(2.72, by + 0.36), (2.95, by + 0.36), (2.95, by + 0.78), (3.18, by + 0.78)], color=C['NAVY'], w=1.75)
path(s, [(2.72, by + 1.21), (2.95, by + 1.21), (2.95, by + 0.78), (3.18, by + 0.78)], color=C['NAVY'], w=1.75, head=False)
box(s, 3.2, by + 0.38, 1.6, 0.8, fill=C['INDIGO'], radius=0.08, paras=[dict(t='식 3 풀기', bold=True, color='FFFFFF', align='c')], size=13.5, anchor='m')
seg(s, 4.82, by + 0.78, 5.18, by + 0.78, color=C['NAVY'], w=2, head=True)
box(s, 5.2, by + 0.38, 1.85, 0.8, fill=C['INDIGO_L'], line=C['INDIGO'], lw=1.5, radius=0.08, paras=[dict(t='T_{e} ≈ 2.5 eV', bold=True, color=C['INDIGO'], align='c', after=0), dict(t='(20 mTorr, 계산)', size=12, align='c')], size=14, anchor='m')
seg(s, 7.07, by + 0.78, 7.43, by + 0.78, color=C['NAVY'], w=2, head=True)
box(s, 7.45, by + 0.38, 2.05, 0.8, fill=C['PANEL'], radius=0.08, paras=[dict(t='u_{B}, ε_{T} 고정', bold=True, align='c', after=0), dict(t='→ 식 4로', size=12, color=C['INDIGO'], align='c')], size=13, anchor='m')
box(s, 3.2, by + 1.35, 3.85, 0.5, fill=C['AMBER_L'], radius=0.06, paras=[dict(t='전력 P는 이 식에 없다', bold=True, color=C['AMBER'], align='c')], size=13.5, anchor='m')
eq(s, 'eq_deff', 0.6, 4.5, pt=14)
tb(s, 3.7, 4.55, 5.8, 0.6, ['h_{L}, h_{R}: 벽 쪽 밀도 비율 (식 5)'], size=12, color=C['DARK'], anchor='m')
msg(s, '총 전력을 바꿔도 T_{e}는 그대로 → 두 영역이 같은 비율로 변한다 → J_{21} = 0 (식 7)')
note(s, 'H 모드 가정. KC20 비공진은 50 → 150 W에서 |J_{21}| ≈ 0.16–0.25 (단일 급전, 50 W는 E–H 전이 근처) → 가설 H4')
notes(s, '세 번째 고리, 입자 균형이다. 정상 상태에서 이온화로 생기는 입자 수와 벽으로 잃는 입자 수가 같아야 한다. 이 식의 양변은 T_e만의 함수라서, 기체 밀도(압력)와 유효 길이(형상)가 정해지면 T_e가 하나로 정해진다. 20 mTorr 설계 형상에서 약 2.5 eV다.\n'
         '중요한 점은 전력이 이 식에 들어 있지 않다는 것이다. 그래서 총 전력을 바꿔도 T_e는 그대로이고, 두 영역의 밀도는 같은 비율로 변한다. 이것이 식 7에서 J₂₁ = 0이 나오는 이유다.\n'
         '다만 이것은 유도 결합(H) 모드에서의 가정이다. 실제로는 T_e가 밀도에 의존한다. KC20의 비공진 데이터에서 전력을 50 W에서 150 W로 올리면 R이 움직여 |J₂₁|이 0.16–0.25로, L2 기준 0.1보다 크다. 다만 코일 하나로 급전했고 50 W는 E–H 전이에 가까운 조건이다. 그래서 가설 H4로 확인한다.')

# =================================================================== f4
s = new('f4', f'{K2} · 식 4 전력 균형', '식 4: 영역 밀도는 영역 전력에 비례한다', 'S2')
tracker(s, 4)
fchip(s, 0.5, 1.52, '4a')
ew4, _ = eqw('eq_pw', 15)
eq(s, 'eq_pw', 1.2, 1.4, pt=15)
link(s, 1.2 + ew4 + 0.15, 1.45, 9.5 - (1.2 + ew4 + 0.15), '← 식 3의 T_{e}', size=12)
tb(s, 1.2, 1.98, 8.0, 0.3, ['ε_{T}: 이온 하나를 만드는 데 드는 총 에너지 ≈ 99 V (T_{e} = 2.5 eV, 계산)'], size=12, color=C['DARK'])
seg(s, 5.0, 2.32, 5.0, 2.6, color=C['NAVY'], w=2, head=True)
tb(s, 5.15, 2.3, 3.5, 0.3, ['두 영역에 쓰고 나누면'], size=12, color=C['MUTED'])
fchip(s, 0.5, 2.95, '4b')
ewl, ehl = eqw('eq_lnR', 17)
xl_ = 5.0 - ewl / 2
eq(s, 'eq_lnR', xl_, 2.62, pt=17)
by = 2.62 + ehl + 0.12
box(s, 1.0, by, 3.8, 0.75, fill=C['NAVY_L'], line=C['NAVY'], lw=1.5, radius=0.08, paras=[
    dict(t='조작 1: 분배 x = P_{c}/P_{tot}', bold=True, color=C['NAVY'], after=1), dict(t='→ R을 움직인다 (J_{22})', size=12.5)], size=13, anchor='m', margin=0.12)
box(s, 5.2, by, 3.8, 0.75, fill=C['PANEL'], line=C['GRAY'], lw=1.25, radius=0.08, paras=[
    dict(t='손실 비대칭', bold=True, color=C['DARK'], after=1), dict(t='→ 가장자리만 측벽 손실 (식 5)', size=12.5)], size=13, anchor='m', margin=0.12)
box(s, 1.0, by + 0.88, 8.0, 0.55, fill=C['NAVY_L'], line=C['NAVY'], lw=1.5, radius=0.08, paras=[
    dict(t='조작 2: 총 전력 P_{tot} → 두 n_{k}가 같은 비율로 → n̄만 움직인다 (J_{11})', bold=True, color=C['NAVY'])], size=13, anchor='m', margin=0.12)
msg(s, '단순 제어의 근거: “가장자리 밀도는 가장자리 전력으로.” 이상적이면 J는 대각이다')
note(s, 'n_{k}, P_{k}, A_{eff,k}: 영역 k(중앙 c, 가장자리 e)의 밀도, 흡수 전력, 유효 손실 면적. u_{B}: 봄 속도')
notes(s, '네 번째 고리, 전력 균형이다. 흡수 전력은 이온-전자 쌍을 만들고 벽으로 잃는 데 쓰이므로, 영역 밀도는 그 영역의 흡수 전력을 (봄 속도 × 쌍당 에너지 × 유효 손실 면적)으로 나눈 값이다. 식 3에서 T_e가 정해지면 u_B와 ε_T도 정해지므로 밀도는 전력에 비례한다.\n'
         '두 영역에 이 식을 쓰고 나누면 ln R은 전력 분배 항과 손실 비대칭 항의 합이 된다. 분배를 바꾸면 R이 움직이고, 총 전력을 바꾸면 두 영역이 같은 비율로 움직여 n̄만 바뀐다.\n'
         '이것이 단순 제어의 근거다. “가장자리 밀도를 올리려면 가장자리 전력을 올리면 된다.” 이상적이라면 J가 대각 행렬이 된다. 다음 장에서 볼 손실 비대칭과, 앞의 식 1·2, 뒤의 식 6이 이 이상을 깬다.')

# =================================================================== f5
s = new('f5', f'{K2} · 식 5 벽 손실', '식 5: 가장자리는 측벽으로 더 잃는다', 'S2')
tracker(s, 5)
fchip(s, 0.5, 1.48, '5a')
eq(s, 'eq_Aeff', 1.2, 1.42, pt=13)
fchip(s, 0.5, 2.05, '5b')
eq(s, 'eq_h', 1.2, 1.92, pt=12.5)
tb(s, 0.5, 2.62, 9.0, 0.3, ['r_{b}: 영역 경계 (12 cm), λ_{i}: 이온 평균 자유 행로 ∝ 1/p. 가장자리 영역에만 측벽 면적 2πRL이 붙는다'], size=12, color=C['DARK'])
# cross-section (half), axis at left
x0d, xs = 0.75, 0.19  # inch per cm
yt, yb = 3.25, 5.15
box(s, x0d, yt, 12 * xs, yb - yt, fill=C['BLUE_L'], radius=None)
box(s, x0d + 12 * xs, yt, 8 * xs, yb - yt, fill=C['ORANGE_L'], radius=None)
seg(s, x0d, yt, x0d + 20 * xs, yt, color=C['NAVY'], w=2)
seg(s, x0d, yb, x0d + 20 * xs, yb, color=C['NAVY'], w=2)
seg(s, x0d + 20 * xs, yt, x0d + 20 * xs, yb, color=C['NAVY'], w=2.5)
seg(s, x0d, yt - 0.1, x0d, yb + 0.1, color=C['MUTED'], w=1, dash=True)
seg(s, x0d + 12 * xs, yt, x0d + 12 * xs, yb, color=C['MUTED'], w=1, dash=True)
for xx in (x0d + 3 * xs, x0d + 8 * xs, x0d + 15.5 * xs):
    seg(s, xx, yt + 0.32, xx, yt + 0.04, color=C['NAVY'], w=1.75, head=True)
    seg(s, xx, yb - 0.32, xx, yb - 0.04, color=C['NAVY'], w=1.75, head=True)
for yy in (yt + 0.55, yt + 0.95, yt + 1.35):
    seg(s, x0d + 20 * xs - 0.45, yy, x0d + 20 * xs - 0.04, yy, color=C['ORANGE_D'], w=2.25, head=True)
tb(s, x0d + 0.1, yt + 0.7, 2.1, 0.3, ['중앙: h_{L}만'], size=12.5, bold=True, color=C['BLUE'])
tb(s, x0d + 12 * xs + 0.06, yt + 0.95, 1.0, 0.5, ['가장자리:', 'h_{L} + h_{R}'], size=12, bold=True, color=C['ORANGE_D'], space_after=0)
tb(s, x0d - 0.25, yb + 0.1, 0.5, 0.28, ['축'], size=12, color=C['MUTED'], align='c')
tb(s, x0d + 12 * xs - 0.6, yb + 0.1, 1.2, 0.28, ['경계 12 cm'], size=12, color=C['MUTED'], align='c')
tb(s, x0d + 20 * xs - 1.15, yb + 0.1, 1.2, 0.28, ['측벽 20 cm'], size=12, color=C['MUTED'], align='r')
panel(s, 4.85, 3.15, 4.65, 2.3, '결과 (설계 형상, 계산)', [
    dict(t='같은 전력 밀도면 R = 1.36–1.47 → R = 1에는 중앙 몫 0.11–0.22: 운전은 늘 가장자리에 전력을 더 준다', bullet=True),
    dict(t='분배를 바꾸면 n̄도 움직인다: J_{12}/J_{22} ≈ 0.10 (식 7)', bullet=True),
    dict(t='근거: H 모드에서 h-factor 비는 측정과 맞는다 ([Pa17], 다음 쪽)', bullet=True, color=C['DARK'])], kind='g', size=12.5, after=5)
msg(s, '손실 비대칭은 없앨 수 없지만, 크기를 알면 총 전력으로 보상할 수 있다 (식 7)')
note(s, 'A_{eff}: 벽 쪽 밀도 비율 h를 곱한 유효 손실 면적 (식 4의 분모)')
notes(s, '다섯 번째 고리, 벽 손실이다. 식 4의 분모인 유효 손실 면적은 벽 쪽 밀도 비율 h를 곱한 면적이다. 중앙 영역은 위아래 판으로만 잃지만, 가장자리 영역은 위아래 판에 측벽까지 더해서 잃는다.\n'
         '그래서 두 영역에 같은 전력 밀도를 주면 중앙 밀도가 더 높아 R은 1.36–1.47이 된다. R = 1을 만들려면 중앙 몫을 0.11–0.22로 낮춰야 하고, 운전은 항상 가장자리에 전력을 더 주는 쪽에서 이뤄진다.\n'
         '또 분배를 바꾸면 손실 면적이 다른 영역으로 전력이 옮겨 가므로 평균 밀도도 조금 움직인다(J₁₂/J₂₂ ≈ 0.10). 이것은 피할 수 없지만 크기를 알기 때문에 총 전력으로 보상한다. Park 2017은 H 모드에서 이 h-factor 비가 측정과 맞는다는 것을 보였다.')

# =================================================================== park
s = new('park', f'{K2} · 선행 연구 1 · 식 5의 실험 근거', 'Park 2017: H 모드에서는 h-factor 이론이 맞는다', 'S2')
panel(s, 0.5, 1.42, 4.0, 2.35, '무엇을 했나', [
    dict(t='ICP의 E–H 전이를 따라 가장자리/중앙 밀도비를 재고 h-factor 이론값과 비교', bullet=True),
    dict(t='부유 고조파 탐침 (FHP: 1 cm, 1 V, 5 kHz)', bullet=True),
    dict(t='E 모드 20 W, H 모드 40 W 이상', bullet=True)], kind='g', size=13.5, after=6)
tb(s, 4.75, 1.42, 4.75, 0.3, ['무엇을 보였나'], size=13, bold=True, color=C['INDIGO'])
box(s, 4.75, 1.8, 4.75, 0.85, fill=C['PANEL'], line='B8BECB', radius=0.08,
    paras=[dict(t='E 모드 (≈ 20 W)', bold=True, size=13.5, color=C['DARK'], after=2),
           dict(t='이론과 크게 어긋남 — 분포가 축전 결합을 따른다', size=13)], margin=0.12, anchor='m')
box(s, 4.75, 2.92, 4.75, 0.85, fill=C['NAVY_L'], line=C['NAVY'], radius=0.08,
    paras=[dict(t='H 모드 (≥ 40 W)', bold=True, size=13.5, color=C['NAVY'], after=2),
           dict(t='이론 h-factor 비가 측정과 맞음 (25–100 mTorr 포함)', size=13)], margin=0.12, anchor='m')
seg(s, 7.12, 2.66, 7.12, 2.9, color=C['NAVY'], w=2, head=True)
tb(s, 7.25, 2.645, 1.5, 0.26, ['전력 ↑'], size=12, color=C['MUTED'], anchor='m')
tb(s, 0.5, 3.92, 9.0, 0.3, ['주제 3과의 연관'], size=13.5, bold=True, color=C['INDIGO'])
cards = [('모델', 'H 모드에서는 영역마다 h-factor로 벽 손실을 쓰는 2-영역 모델이 정당화된다'),
         ('운전', '점화 후 H 모드를 확인하고 나서 바깥 루프를 닫는다'),
         ('측정', '같은 부유 고조파 탐침을 웨이퍼 배열로 써서 밀도비를 잰다')]
x = 0.5
for head, body in cards:
    panel(s, x, 4.3, 2.9, 1.42, head, [body], kind='i', size=13, head_size=13.5)
    x += 3.05
msg(s, 'H 모드에서는 h-factor 2-영역 모델이 맞는다 → 공식 사슬(식 3–5)의 전제')
note(s, '같은 논문의 λ_{ε} 값(3–50 mTorr)은 계산값이라 λ_{ε} 식의 독립 검증으로 쓰지 않는다')
notes(s, '제공받은 논문 Park 2017이다. ICP에서 전력을 올려 E 모드에서 H 모드로 넘어갈 때 가장자리/중앙 밀도비가 어떻게 바뀌는지를 부유 고조파 탐침으로 재고, h-factor 이론과 비교했다.\n'
         '결론은 모드에 따라 갈린다. H 모드에서는 고압(25–100 mTorr)까지 포함해 이론 h-factor 비가 측정과 맞는다. E 모드에서는 분포가 축전 결합을 따라가서 이론이 크게 어긋난다. 저압 3, 10 mTorr에서 보이는 절대값 차이는 탐침 위치 때문이라고 설명한다.\n'
         '우리 설계에 가져온 것은 세 가지다. H 모드라면 영역마다 h-factor로 벽 손실을 쓰는 2-영역 모델이 정당화된다. 운전에서는 점화 후 H 모드를 확인한 다음에야 바깥 루프를 닫는다. 측정에서는 같은 부유 고조파 탐침을 웨이퍼 배열로 써서 밀도비를 잰다.\n'
         '주의: 이 논문의 압력별 λε 값은 계산값이라, 우리 λε 식과 맞는다는 것을 독립 검증이라고 말하지 않는다.')

# =================================================================== f6
s = new('f6', f'{K2} · 식 6 확산과 형상', '식 6: 경계는 L/π만큼 흐려진다 → 형상', 'S2')
tracker(s, 6)
fchip(s, 0.5, 1.45, '6')
eq(s, 'eq_diff', 1.2, 1.38, pt=14)
tb(s, 5.0, 1.36, 4.5, 0.62, ['L = 10 cm → 퍼짐 길이 ℓ ≈ 3.2 cm', 'Δ = 7.5 cm → 누설 ≈ 0.10 (Δ ≈ 2.4ℓ)'], size=12, color=C['DARK'], space_after=0)
ax_x, k = 5.0, 0.14
wy = 2.72
L_in = 10 * k
wf_y = wy + L_in
box(s, ax_x - 12 * k, wy, 24 * k, L_in, fill=C['BLUE_L'], radius=None)
box(s, ax_x - 20 * k, wy, 8 * k, L_in, fill=C['ORANGE_L'], radius=None)
box(s, ax_x + 12 * k, wy, 8 * k, L_in, fill=C['ORANGE_L'], radius=None)
box(s, ax_x - 20 * k - 0.06, wy - 0.12, 40 * k + 0.12, 0.12, fill='C7D3E6', line='9AA3B5', lw=0.75, radius=None, name='유전체 창')
box(s, ax_x - 20 * k - 0.06, wy - 0.12, 0.06, L_in + 0.2, fill=C['NAVY'], radius=None)
box(s, ax_x + 20 * k, wy - 0.12, 0.06, L_in + 0.2, fill=C['NAVY'], radius=None)
box(s, ax_x - 15 * k, wf_y, 30 * k, 0.07, fill='5F6779', radius=None, name='웨이퍼')
box(s, ax_x - 20 * k - 0.06, wf_y + 0.08, 40 * k + 0.12, 0.06, fill=C['NAVY'], radius=None)
for sx in (-1, 1):
    seg(s, ax_x + sx * 12 * k, wy, ax_x + sx * 12 * k, wf_y, color=C['MUTED'], w=1, dash=True)
    for r_ in (7.6, 8.4):
        circle(s, ax_x + sx * r_ * k, wy - 0.24, 0.15, fill=C['BLUE'])
    circle(s, ax_x + sx * 15.5 * k, wy - 0.24, 0.15, fill=C['ORANGE'])
seg(s, ax_x, wy - 0.4, ax_x, wf_y + 0.14, color=C['MUTED'], w=1, dash=True)
tb(s, ax_x + 0.06, wy + 0.06, 1.5, 0.28, ['축 (E_{θ} = 0)'], size=12, color=C['DARK'])
tb(s, ax_x - 8 * k - 0.95, wy - 0.68, 1.9, 0.28, ['[[b:안쪽 코일]] r ≈ 8 cm, 2턴'], size=12, align='c')
tb(s, 0.5, wy - 0.74, 1.45, 0.75, ['[[o:바깥 코일]]', 'r ≈ 15.5 cm', '1–2턴'], size=12, space_after=0, align='r')
seg(s, 2.0, wy - 0.24, ax_x - 15.5 * k - 0.1, wy - 0.24, color=C['ORANGE'], w=1)
yd = wy - 0.55
seg(s, ax_x + 8 * k, yd, ax_x + 15.5 * k, yd, color=C['TEXT'], w=1.25, head=True, tail=True)
tb(s, ax_x + 15.5 * k + 0.12, yd - 0.15, 1.4, 0.3, ['Δ = 7.5 cm'], size=13, bold=True, color=C['INDIGO'], anchor='m')
xl = ax_x + 18.6 * k
seg(s, xl, wy + 0.02, xl, wf_y - 0.02, color=C['TEXT'], w=1.25, head=True, tail=True)
tb(s, xl + 0.36, wy + L_in / 2 - 0.15, 1.2, 0.3, ['L = 10 cm'], size=12.5, bold=True, anchor='m')
tb(s, ax_x - 12 * k + 0.06, wy + 0.06, 1.4, 0.3, ['경계 12 cm'], size=12, color=C['DARK'])
tb(s, ax_x - 1.75, wy + 0.72, 1.6, 0.3, ['중앙 영역'], size=13, bold=True, color=C['BLUE'], align='r')
tb(s, ax_x + 12.5 * k, wy + 0.5, 0.95, 0.3, ['가장자리'], size=13, bold=True, color=C['ORANGE_D'])
rows = [['항목', '값', '이유 (식)'],
        ['창–웨이퍼 간격 L', '10 cm', 'L을 줄이면 누설은 줄지만 균일도·창 결합이 나빠진다 (식 6)'],
        ['안쪽 코일', 'r ≈ 8 cm, 2턴', '축 위 E_{θ} = 0 → 축에서 띄워야 가열이 된다 (식 1)'],
        ['바깥 코일', 'r ≈ 15.5 cm, 1–2턴', '측벽과 4.5 cm → 측벽 손실 전에 이온화 (식 2, 5)']]
table(s, 0.5, 4.42, [1.75, 1.85, 5.4], rows, size=12, row_h=0.32, first_col_bold=True)
msg(s, '코일 간격 Δ와 높이 L이 누설(≈ 0.10)과 p*(≈ 16 mTorr, 식 2)를 함께 정한다')
notes(s, '여섯 번째 고리, 확산이다. 축 방향 기본 모드가 cos(πz/L)이면 고리 모양으로 생긴 플라즈마는 반경 방향으로 L/π만큼 퍼지고, 다른 영역으로 새는 몫은 약 e^(−πΔ/L)이다. L = 10 cm에서 퍼짐 길이는 약 3.2 cm, 누설은 약 0.10으로 L2 경계에 있다.\n'
         '그래서 형상은 이 길이들로 정했다. 코일 간격 Δ = 7.5 cm는 퍼짐 길이의 2.4배라 확산만으로는 크게 섞이지 않고, 식 2의 p*도 정한다. L을 6 cm로 줄이면 누설은 0.02로 줄지만 영역 안 균일도와 창–웨이퍼 축전 결합이 나빠진다.\n'
         '안쪽 코일은 축 위에서 유도 전기장이 0이라 축에 붙이지 않고 반지름 8 cm에 두었고, 바깥 코일은 측벽에서 4.5 cm 띄워 가열된 전자가 측벽에 빠지기 전에 이온화하게 했다.')

# =================================================================== f7
s = new('f7', f'{K2} · 식 7 응답 행렬', '식 7: 공식을 이으면 J는 삼각형이다', 'S2')
tracker(s, 7)
tb(s, 0.5, 1.4, 4.3, 0.3, ['설계 형상, 20 mTorr, 영역 전력 직접 지정 (계산)'], size=12, color=C['MUTED'])
mx, my, cs = 1.75, 2.15, 1.2
tb(s, mx, my - 0.42, cs, 0.35, ['Δln P_{tot}'], size=13, bold=True, align='c', color=C['NAVY'])
tb(s, mx + cs + 0.1, my - 0.42, cs, 0.35, ['Δx (중앙 몫)'], size=13, bold=True, align='c', color=C['NAVY'])
tb(s, 0.5, my + 0.4, 1.15, 0.4, ['Δln n̄'], size=13, bold=True, align='r', color=C['NAVY'])
tb(s, 0.5, my + cs + 0.5, 1.15, 0.4, ['Δln R'], size=13, bold=True, align='r', color=C['NAVY'])
cells = [(0, 0, '1.00', C['NAVY_L'], None, C['TEXT']), (0, 1, '0.25', C['AMBER_L'], None, C['AMBER']),
         (1, 0, '0', 'FFFFFF', C['AMBER'], C['AMBER']), (1, 1, '2.44', C['NAVY'], None, 'FFFFFF')]
for i, j, v, f, ln, tc in cells:
    box(s, mx + j * (cs + 0.1), my + i * (cs + 0.1), cs, cs, fill=f, line=ln, lw=2.25, dash=bool(ln), radius=0.08,
        paras=[v], size=26, bold=True, color=tc, align='c', anchor='m')
rows = [['원소', '값', '이 값을 정한 식'],
        ['J_{11}', '1.00', '식 4: 밀도 ∝ 전력'],
        ['J_{21}', '0', '식 3: T_{e}가 전력과 무관'],
        ['J_{22}', '2.44', '식 4 × 식 2: 분배 × g_{R}'],
        ['J_{12}', '0.25', '식 5: 손실 비대칭, J_{12}/J_{22} ≈ 0.10']]
table(s, 4.75, 1.42, [0.8, 0.7, 3.25], rows, size=12.5, row_h=0.46, col_align=['c', 'c', 'l'], first_col_bold=True,
      fills={(4, j): C['AMBER_L'] for j in range(3)})
panel(s, 4.75, 3.95, 4.75, 1.1, '남는 누설은 어디서 오나', [
    dict(t='식 1 회로 결합 → 구동 방식이 정한다', bullet=True),
    dict(t='식 2 가열, 식 6 확산 → 압력과 형상이 정한다', bullet=True)], kind='a', size=13, after=4)
msg(s, '플라즈마 단계만 보면 거의 L2. 단순 제어는 회로(식 1)와 압력·형상(식 2, 6)에서 깨진다')
note(s, '2-영역 0D(식 2–6). 회로(식 1)는 KC20 대조: 급전 전류 ±9%, 절대 밀도 1.4–18배 차이 → 판정은 비로만')
notes(s, '일곱 번째, 사슬 전체를 응답 행렬로 요약한다. 영역 전력을 직접 지정하고 식 2–6을 2-영역 0D 모델로 풀어 20 mTorr 설계 형상에서 J를 계산했다. 식 1의 회로 모델은 KC20 급전 전류와 따로 대조했다.\n'
         'J₁₁ ≈ 1은 식 4의 “밀도는 전력에 비례”, J₂₁ = 0은 식 3의 “T_e는 전력과 무관”, J₂₂ ≈ 2.44는 식 4의 분배 효과에 식 2의 g_R이 곱해진 것, J₁₂ ≈ 0.25는 식 5의 손실 비대칭에서 나온다. J₁₂/J₂₂ ≈ 0.10이라 분배 열은 L2 경계에 있다. 이 표가 제출물 ②(조작 변수와 밀도 응답의 관계)다.\n'
         '결론적으로 플라즈마 단계만 보면 거의 구조적 독립에 가깝다. 단순 제어가 깨지는 곳은 회로 결합(식 1)과 압력·형상(식 2, 6)이고, 3장의 조절 수단과 5장의 정리에서 이 두 곳을 다룬다.\n'
         '모델의 한계: 비공진 급전 전류는 ±9% 안으로 맞았지만 절대 밀도는 1.4–18배 차이 나므로, 판정은 절대값이 아니라 비로만 쓴다.')

# =================================================================== knobs
s = new('knobs', f'{K3} · 수단 여섯 가지 · 검토 사항 1', '조절 수단 여섯 가지: 공식의 어느 항을 바꾸나', 'S3')
rows = [['후보', '수단 [근거]', '바꾸는 항 (식)', '주로 바뀌는 곳', '한계'],
        ['', '다중 코일 + 단일 전원 [P1][P2]', '전원 하나가 I_{2}/I_{1}을 나눔 (식 1)', '각 코일 아래', '분배가 부하에 끌려감'],
        ['A', 'LC 공진 코일 [KC20][J1]', 'Z_{22}의 1/(jωC) (식 1)', '공진 코일 쪽', '공진점 이동, 급경사'],
        ['B', '독립 전원 + 위상·진폭 [P3]', 'k, φ를 직접 지정 (식 1b, 1c)', '코일 아래와 사이', '교환 전력 ∝ sin φ'],
        ['', '다중 영역·이중 주파수 [J2][C3]', '주파수 분리로 Z_{12} 효과 제거', '각 소스 아래', '전원·필터 2벌'],
        ['', '페라이트 [C3]', 'E ∝ ωμI, M_{12} 감소 (식 1)', '페라이트 주변', '13.56 MHz 손실·발열'],
        ['C', '정자기장 [P4][C5][C6]', 'λ_{ε⊥}, D_{⊥} 감소 (식 2, 6)', '반경 방향 수송', '이온 선속·에너지 분포 변화']]
fills = {(2, 0): C['NAVY_L'], (3, 0): C['NAVY_L'], (6, 0): C['NAVY_L']}
table(s, 0.5, 1.42, [0.55, 2.45, 2.35, 1.45, 2.2], rows, size=12.5, row_h=0.6, col_align=['c', 'l', 'l', 'l', 'l'],
      fills=fills, colors={(2, 0): C['NAVY'], (3, 0): C['NAVY'], (6, 0): C['NAVY']}, bold_cells={(2, 0), (3, 0), (6, 0)})
msg(s, '수단 대부분은 식 1(회로)을 바꾼다. 식 2·6(가열·확산)을 바꾸는 것은 자기장뿐이다')
note(s, '[P1]–[P4]·[KC20]은 본문 확인, [J]·[C]는 초록만 확인. 후보 A·B·C의 구동 방식 비교는 백업 ¤bk_drive¤')
notes(s, '검토 사항 1, 어떤 조절 수단을 조합하고 각 수단이 어디에 영향을 주는지를 공식으로 정리했다. 표의 세 번째 열이 그 수단이 공식 사슬의 어느 항을 바꾸는지다.\n'
         '다중 코일, LC 공진, 위상·진폭, 이중 주파수, 페라이트는 모두 식 1, 회로의 항을 바꾼다. 그래서 이들 사이의 차이는 결국 회로 누설이 얼마나 남는가의 차이다. 반면 식 2(가열)와 식 6(확산)을 바꾸는 수단은 정자기장뿐이다. 즉 압력 때문에 분포가 안 움직이는 문제는 구동 방식으로는 풀 수 없다.\n'
         '이어서 LC 공진, 위상·진폭 조절, 자기장·페라이트의 원리를 차례로 보고, 각각이 주제와 어떻게 이어지는지 본다.')

# =================================================================== lc
s = new('lc', f'{K3} · LC 공진', 'LC 공진: 커패시터 하나로 바깥 전류를 키운다', 'S3')
fchip(s, 0.5, 1.6, '1')
eq(s, 'eq_res', 1.2, 1.38, pt=13)
tb(s, 4.95, 1.42, 4.55, 0.85, ['바깥 코일을 전원 없이 C로 닫으면, 분모의 리액턴스가 0에 가까울 때 I_{2}가 커진다',
                              '분모의 ΔZ_{22}는 플라즈마 밀도에 따라 변한다'], size=12, color=C['DARK'], bullet=True, space_after=4)
cards = [('공진 조건', ['ωL_{2} + X′_{22} = 1/(ωC)일 때 바깥 전류가 가장 크다', '빈 챔버 기준 C ≈ 160 pF (L_{2} ≈ 863 nH, 계산)'], 'g'),
         ('장점: 범위', ['전원 하나로 바깥 쪽 가열을 크게 키운다', 'KC20: 50 mTorr에서 R 2.54 → 0.39 (다음 쪽)'], 'n'),
         ('한계: 독립성', ['밀도가 바뀌면 ΔZ_{22}가 공진점을 옮긴다', '공진 근처는 기울기가 가파르다 → 분배가 밀도에 끌린다'], 'a')]
x = 0.5
for head, body, k in cards:
    panel(s, x, 2.42, 2.9, 1.85, head, [dict(t=b_, bullet=True) for b_ in body], kind=k, size=12.5, after=4)
    x += 3.05
stats = [('약 350 V', '공진 코일 전압 (5 A, 계산)', C['NAVY']),
         ('ΔC + ΔP', 'R을 바꾸며 n̄를 지키려면 C와 전력을 함께 (+14.8 pF, +3.5%)', C['NAVY']),
         ('L1', '커패시터 하나가 n̄와 R을 함께 움직인다', C['AMBER'])]
x = 0.5
for big, small, col in stats:
    box(s, x, 4.42, 2.9, 1.3, fill=C['PANEL'], radius=0.08, paras=[
        dict(t=big, size=22, bold=True, color=col, after=2), dict(t=small, size=12)], margin=0.13, anchor='m')
    x += 3.05
msg(s, 'LC 공진은 R 범위를 넓히지만, 분배가 밀도에 끌려 독립성은 L1에 머문다')
note(s, 'ΔC, ΔP, 코일 전압은 0D 모델 계산. 모델이 공진 상태를 재현하지 못하므로 경향으로만 읽는다')
notes(s, 'LC 공진은 주제안이 제시한 조절 수단 중 하나다. 바깥 코일을 전원 없이 가변 커패시터로 닫으면, 식 1의 결합 회로에서 바깥 코일 전류는 이 식으로 정해진다. 분모의 리액턴스 합이 0에 가까워지는 공진 근처에서 바깥 전류가 커지고, 그만큼 바깥 쪽 가열이 늘어 분포가 가장자리로 옮겨 간다. 우리 설계 형상의 바깥 코일이면 빈 챔버 기준 약 160 pF에서 공진한다.\n'
         '장점은 전원 하나로 넓은 범위를 낼 수 있다는 것이다. 다음 쪽의 KC20은 50 mTorr에서 공진만으로 R을 0.39까지 내렸다.\n'
         '한계는 독립성이다. 분모의 ΔZ₂₂가 플라즈마 밀도에 따라 변하므로 밀도가 바뀌면 공진점이 움직이고, 공진 근처에서는 기울기가 가파르다. 커패시터 하나가 평균 밀도와 밀도비를 함께 움직이므로, 우리 판정 기준으로는 보상 가능한 독립(L1)에 머문다. 공진 코일에는 수백 V의 전압이 걸린다는 점도 설계에서 고려해야 한다.')

# =================================================================== kc20
s = new('kc20', f'{K3} · 선행 연구 2 · LC 공진과 비국소 가열', 'KC20: 고압에서는 공진 코일이 분포를 뒤집는다', 'S3')
cx_, cy_, cw_, ch_ = 0.5, 1.38, 5.3, 3.2
lay = (0.12, 0.13, 0.85, 0.68)
band_behind(s, cx_, cy_, cw_, ch_, lay, 0, 3.5, 0.8, 1.2)
cd = CategoryChartData()
cd.categories = ['1 mTorr\n150 W', '1 mTorr\n50 W', '50 mTorr\n150 W', '50 mTorr\n50 W']
cd.add_series('비공진', (1.81, 1.51, 2.54, 3.33))
cd.add_series('공진', (1.22, 1.31, 0.39, 1.05))
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, I(cx_), I(cy_), I(cw_), I(ch_), cd)
gf.name = 'KC20 R 막대그래프'
ch = gf.chart; style_chart(ch, size=12)
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.TOP; ch.legend.include_in_layout = False
ch.legend.font.size = Pt(12)
plot = ch.plots[0]; plot.gap_width = 70; plot.overlap = -5
for ser, col in zip(plot.series, ('8C9AB5', C['ORANGE'])):
    ser.format.fill.solid(); ser.format.fill.fore_color.rgb = rgb(col)
plot.has_data_labels = True
dl = plot.data_labels; dl.number_format = '0.00'; dl.number_format_is_linked = False
dl.position = XL_LABEL_POSITION.OUTSIDE_END; dl.font.size = Pt(12)
style_axis(ch.value_axis, 0, 3.5, 1.0, '0.0', grid=True, size=12)
axis_title(ch.value_axis, 'R (면적 평균)', size=12)
style_axis(ch.category_axis, size=12)
plot_layout(ch, *lay)
# 분포 반전 표시: 50 mTorr 150 W 쌍
px0, pw = cx_ + cw_ * lay[0], cw_ * lay[2]
py0, ph = cy_ + ch_ * lay[1], ch_ * lay[3]
xc3 = px0 + pw * (2.5 / 4)
yv7 = lambda v: py0 + ph * (3.5 - v) / 3.5
seg(s, xc3 + 0.02, yv7(2.54) + 0.08, xc3 + 0.2, yv7(0.39) - 0.38, color=C['ORANGE_D'], w=2.25, head=True)
tb(s, xc3 - 1.6, 1.84, 1.8, 0.28, ['공진 → 분포 반전'], size=12, bold=True, color=C['ORANGE_D'], align='r')
tb(s, 0.62, 4.56, 5.1, 0.28, ['옅은 보라 띠: 이 과제의 목표 R 0.8–1.2'], size=12, color=C['MUTED'])
panel(s, 6.0, 1.42, 3.5, 3.35, '실험 구성', [
    dict(t='챔버 r 19 cm, 높이 10 cm', bullet=True),
    dict(t='급전 코일 r 9.5 cm + 수동 공진 코일 r 17.5 cm (가변 C, 공진 139 pF)', bullet=True),
    dict(t='λ_{ε}: 1 mTorr 119 cm (논문 계산값), 50 mTorr 약 2.4 cm (1/p 환산)', bullet=True)], kind='g', size=13.5, after=8)
cards = [('저압 (1 mTorr)', 'λ_{ε}가 챔버보다 길어 R 변화가 작다', 'g'),
         ('고압 (50 mTorr)', '공진만으로 R < 1까지 내려간다', 'g'),
         ('남은 빈 곳', '두 끝 상태뿐 → 연속 조정은 미확인', 'a')]
x = 0.5
for head, body, k in cards:
    panel(s, x, 4.92, 2.9, 0.83, head, [body], kind=k, size=12.5, head_size=13, after=2)
    x += 3.05
msg(s, '고압에서만 공진 코일이 분포를 뒤집는다 → λ_{ε}(식 2)가 LC 공진의 효과를 정한다')
note(s, 'R: 탐침 반경 분포를 경계 13.5 cm로 면적 평균 (팀 디지타이즈, Fig. 3, 8). FHP 지도로도 공진 때 R ≈ 0.4–0.7')
notes(s, '제공받은 논문 KC20이다. 안쪽 코일은 전원으로 급전하고, 바깥 코일은 전원 없이 가변 커패시터로 닫아 공진시키는 구조다. 공진에 가까워지면 바깥 코일 전류가 커지고, 같은 전력에서 급전 전류가 줄어 중앙 가열도 줄어든다.\n'
         '핵심 결과는 압력에 따라 반응이 완전히 다르다는 것이다. 1 mTorr에서는 λε가 119 cm로 챔버보다 길어, 가열 위치를 바꿔도 R이 1.81에서 1.22로 조금만 변한다. 50 mTorr에서는 λε가 약 2.4 cm로 짧아 공진 코일 아래에서 국소적으로 이온화가 일어나고, 밀도 봉우리가 반지름 15 cm 쪽으로 옮겨 가 R이 0.39까지 내려간다. 웨이퍼 FHP 지도에서도 같은 경향이 보인다.\n'
         '배운 것 세 가지. 첫째, 분포를 움직일 수 있는지는 구동 방식보다 압력(λε)이 먼저 정한다. 둘째, 수동 공진도 고압에서는 R < 1을 만들 수 있다. 우리 초기 모델은 이것을 재현하지 못했고, 그래서 “수동 공진은 R = 1에 못 닿는다”던 초기 판단을 고쳤다. 셋째, 논문은 비공진과 공진 두 끝 상태만 보여 준다. 중간값을 연속으로, 밀도가 바뀌어도 흔들리지 않게 맞출 수 있는지는 답하지 않는다. 이것이 우리 과제가 채워야 할 부분이다.')

# =================================================================== p_phase
s = new('p_phase', f'{K3} · 위상·진폭 조절', '위상·진폭: 교환 전력 ∝ sin φ → 0°나 180°', 'S3')
fchip(s, 0.5, 1.52, '1c')
eq(s, 'eq_phase', 1.2, 1.5, pt=15)
tb(s, 5.15, 1.4, 4.35, 0.62, ['진폭(전류비 k)은 분배를, 위상 φ는 두 전원 사이의 전력 교환을 바꾼다'], size=13, anchor='m')
cx_, cy_, cw_, ch_ = 0.5, 2.1, 5.6, 3.3
lay = (0.15, 0.05, 0.81, 0.72)
px0, pw = cx_ + cw_ * lay[0], cw_ * lay[2]
py0, ph = cy_ + ch_ * lay[1], ch_ * lay[3]
def xb(a, b, col):
    box(s, px0 + pw * a / 360, py0, pw * (b - a) / 360, ph, fill=col, radius=None, name='위상 허용 띠')
xb(0, 19, C['NAVY_L']); xb(341, 360, C['NAVY_L']); xb(176, 184, C['AMBER_L'])
cd = XyChartData()
sa = cd.add_series('sin')
for d in range(0, 361, 5):
    sa.add_data_point(d, math.sin(math.radians(d)))
sb = cd.add_series('고정점')
for d in (0, 180, 360):
    sb.add_data_point(d, 0.0)
gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_SMOOTH_NO_MARKERS, I(cx_), I(cy_), I(cw_), I(ch_), cd)
gf.name = '교환 전력 위상 그래프'
ch = gf.chart; style_chart(ch, size=12); ch.has_legend = False
sr = ch.plots[0].series
sr[0].format.line.color.rgb = rgb(C['NAVY']); sr[0].format.line.width = Pt(2.75); sr[0].smooth = True
sr[1].smooth = False; sr[1].format.line.fill.background()
sr[1].marker.style = XL_MARKER_STYLE.CIRCLE; sr[1].marker.size = 11
sr[1].marker.format.fill.solid(); sr[1].marker.format.fill.fore_color.rgb = rgb(C['INDIGO'])
sr[1].marker.format.line.color.rgb = rgb('FFFFFF')
for k_ in (0, 2):
    sr[1].points[k_].marker.style = XL_MARKER_STYLE.NONE
def yv(v):
    return py0 + ph * (1 - v) / 2
tb(s, px0 + pw * 6 / 360, yv(-0.06), 1.2, 0.28, ['0° 동상'], size=12.5, bold=True, color=C['NAVY'])
tb(s, px0 + pw * 186 / 360, yv(0.3), 1.2, 0.28, ['180° 역상'], size=12.5, bold=True, color=C['AMBER'])
style_axis(ch.category_axis, 0, 360, 90, '0', grid=False, size=12)
style_axis(ch.value_axis, -1, 1, 0.5, '0.0', grid=True, size=12)
ch.value_axis.crosses = XL_AXIS_CROSSES.MINIMUM
axis_title(ch.category_axis, '위상차 φ (°)', size=12); axis_title(ch.value_axis, '교환 전력 (90°의 값 = 1)', size=12)
plot_layout(ch, *lay)
tb(s, 0.6, 5.42, 5.5, 0.3, ['띠: 교환 전력 ≤ 흡수의 10%인 위상 (보수적 값)'], size=12, color=C['MUTED'])
stats = [('0.2–0.7배', 'φ = 90°의 교환 전력 ÷ 흡수 전력 → 연속 손잡이로 쓰기엔 크다', C['INDIGO']),
         ('±19–38°', '0°의 위상 허용 오차', C['NAVY']),
         ('±4–12°', '180°의 위상 허용 오차 (전류가 커서 좁다)', C['AMBER'])]
y = 2.15
for big, small, col in stats:
    box(s, 6.3, y, 3.2, 1.1, fill=C['PANEL'], radius=0.08, paras=[
        dict(t=big, size=24, bold=True, color=col, after=2), dict(t=small, size=12.5)], margin=0.14, anchor='m')
    y += 1.2
msg(s, '같은 주파수의 두 전원은 sin φ만큼 전력을 주고받는다 → 위상은 0°나 180°에 고정한다')
note(s, 'ωM_{12} = 7.8 Ω, X′_{12} ≈ −4 ~ −6 Ω. 단일 턴, 균일 반공간, 밀도 고정 3×10^{10}–10^{11} cm^{−3} (계산)')
notes(s, '위상·진폭 조절의 원리다. 진폭, 즉 두 코일의 전류비 k는 분배를 정하고, 위상은 두 전원 사이의 전력 교환을 정한다. 식 1c에 따르면 같은 주파수의 두 전원은 상호 인덕턴스를 통해 서로 전력을 밀어 넣고, 그 크기는 sin φ에 비례한다. 플라즈마 상호 리액턴스가 일부 상쇄해도 90°에서 흡수 전력의 0.2–0.7배라, 위상을 연속 손잡이로 쓰기에는 크다.\n그래서 해결 방안은 위상을 교환 전력이 사라지는 0°나 180° 근처에 고정하는 것이다. 교환 전력을 흡수의 10% 안으로 묶으려면 0°에서는 ±19–38°, 180°에서는 ±4–12°의 여유가 있다. 180°는 같은 전력에 코일 전류가 커서 여유가 좁다. 0°와 180°의 자세한 비교는 백업에 두었고, 2차 발표에서 같은 기준으로 다시 비교한다.')

# =================================================================== field
s = new('field', f'{K3} · 자기장·페라이트', '자기장·페라이트: 수송과 결합을 바꾸는 보조 수단', 'S3')
box(s, 0.5, 1.42, 4.4, 4.33, fill=C['NAVY_L'], radius=0.08)
tb(s, 0.65, 1.5, 4.1, 0.3, ['약한 축 방향 정자기장'], size=13.5, bold=True, color=C['NAVY'])
eq(s, 'eq_dperp', 0.65, 1.9, pt=11)
tb(s, 0.65, 2.55, 4.15, 3.15, [
    dict(t='ω_{ce}/ν_{m}이 커지면 반경 방향 확산(식 6)과 λ_{ε}(식 2)가 줄어 가열·이온화가 코일 아래에 머문다', after=5),
    dict(t='λ_{ε⊥} = Δ가 되는 자기장: 1 / 5 / 10 mTorr에서 2.9 / 2.7 / 2.2 G (추정)', after=5),
    dict(t='ECR 4.84 G 아래지만 ω_{ce}/ω ≈ 0.46–0.59 → 파동 전파가 먼저 바뀐다', after=5),
    dict(t='대가: h_{R}이 줄어 R 기준값이 바뀌고, 웨이퍼 위 자기장은 대전 손상 위험')], size=12.5, bullet=True, bullet_color=C['NAVY'])
panel(s, 5.1, 1.42, 4.4, 2.6, '페라이트', [
    dict(t='E_{θ} ∝ ωμI: 자속을 모아 같은 E를 더 작은 전류로', bold=True, after=4),
    dict(t='400 kHz, μ ≈ 2000이면 전류 약 1/60, 효율 약 99% (대신 점화가 어렵다)', bullet=True, after=3),
    dict(t='13.56 MHz에서는 코어 손실이 커질 것 (추정) → 코일 뒤 요크로 M_{12}와 장 중첩을 줄이는 보조 (식 1)', bullet=True)], kind='g', size=12.5)
panel(s, 5.1, 4.15, 4.4, 1.6, '주제 3과의 연관', [
    dict(t='자기장은 식 2·6을 직접 바꾸는 유일한 수단 → 15 mTorr 아래 운전 때만 의미', bullet=True, after=3),
    dict(t='페라이트는 코일 간 결합(식 1)을 줄이는 보조', bullet=True)], kind='i', size=12.5)
msg(s, '자기장은 저압에서 분배의 효과를 되살리고, 페라이트는 코일 간 결합을 줄인다')
note(s, 'ν_{m} = n_{g}K_{el}, T_{e} ≈ 2.5 eV. 자기장 값은 λ_{ε⊥} = Δ 조건의 추정 (D_{⊥} 식 [LL05]). 선행 사례: GEC 2025 초록')
notes(s, '나머지 두 조절 수단, 자기장과 페라이트의 원리다. 약한 축 방향 정자기장을 걸면 전자가 자기력선을 따라 감기면서 반경 방향 확산 계수가 1/(1 + (ω_ce/ν_m)²)배로 줄고, 에너지 이완 길이도 같은 비율의 제곱근으로 줄어든다고 둘 수 있다. 그러면 저압에서도 가열과 이온화가 코일 아래에 머물러, 분배가 다시 밀도비를 움직일 수 있다. 5 mTorr에서 약 2.7 G면 λε가 코일 간격과 같아진다.\n'
         '다만 ECR 자기장 4.84 G보다 작아도 ω_ce/ω가 0.5 정도라 파동 전파가 먼저 바뀌고, 측벽 손실 비율 h_R이 줄어 밀도비의 기준값도 바뀐다. 웨이퍼 위 자기장은 대전 손상 위험이 있다.\n'
         '페라이트는 자속을 모아 같은 유도 전기장을 더 작은 전류로 만든다. 400 kHz에서는 효과가 크지만 13.56 MHz에서는 코어 손실이 커질 것으로 보여, 코일 뒤 요크로 두 코일 사이의 결합과 장 중첩을 줄이는 보조로만 본다.\n'
         '주제와의 연관: 공식 사슬에서 식 2와 식 6을 직접 바꾸는 수단은 자기장뿐이다. 그래서 15 mTorr 아래로 운전해야 할 때만 의미가 있다.')

# =================================================================== diag
s = new('diag', f'{K4} · 진단 방법 · 검토 사항 4', '밀도비를 재는 진단: 각 방법이 재는 것', 'S4')
rows = [['진단', '재는 물리량', '원리', '주제 3에서의 쓰임'],
        ['랭뮤어 탐침', 'I–V 곡선 → T_{e}, n, EEPF', '전자 영역 기울기 → T_{e}, 2차 미분 → EEPF', 'λ_{ε} 가설(국소/비국소) 확인 (식 2)'],
        ['[[n:부유 고조파 탐침 (FHP)]]', '이온 선속 n u_{B}, T_{e}', '부유 전위에 작은 사인파 → 고조파 전류비', '웨이퍼 배열로 밀도비 R_{Γ} (주 센서)'],
        ['컷오프 탐침', '전자 밀도 절대값', '투과 스펙트럼의 차단 주파수 f_{p} ∝ √n_{e}', 'n̄ 절대값 교정'],
        ['VI 프로브', '코일 전압·전류·위상', 'P = VI cos θ, ΔP/P = tan θ·Δθ', '전력보다 코일 전류를 제어 기준으로'],
        ['광 방출 분석 (OES)', '선 세기 (시선 적분)', '방출 ∝ n_{e} n_{g} K_{exc}(T_{e})', '공간 분해가 약해 보조 감시'],
        ['B-dot 탐침', 'RF 자기장 분포', '유도 기전력 ∝ dB/dt', '표피 깊이·코일 장 확인 (식 1)']]
table(s, 0.5, 1.42, [1.75, 2.0, 2.65, 2.6], rows, size=12, row_h=0.6, col_align=['l', 'l', 'l', 'l'],
      row_heights=[0.38] + [0.64] * 6, first_col_bold=True, fills={(2, j): C['NAVY_L'] for j in range(4)})
msg(s, '밀도비는 위치마다, 실시간으로, 교란 없이 재야 한다 → 웨이퍼 FHP 배열을 주 센서로')
note(s, '컷오프: n_{e} = 4π²ε_{0} m f_{p}²/e². ICP 안테나는 θ ≈ 89.4° (tan θ ≈ 100) → 위상 0.1° 오차에 전력 17%')
notes(s, '검토 사항 4, 밀도비가 목표를 따르는지 어떻게 판단할지에 필요한 진단 이론이다. 각 방법이 실제로 재는 물리량이 무엇인지가 핵심이다.\n'
         '랭뮤어 탐침은 I–V 곡선에서 전자 온도와 밀도, 2차 미분으로 전자 에너지 분포(EEPF)를 준다. 플라즈마에 삽입해 교란이 있으므로, 운전 중 센서보다는 식 2의 국소/비국소 가열 가설을 확인하는 데 쓴다. 부유 고조파 탐침(FHP)은 부유 전위에 작은 사인파를 걸어 고조파 전류의 비로 전자 온도를, 이온 포화 전류로 이온 선속을 구한다. 부유 상태라 교란이 작고 웨이퍼에 여러 개를 배열할 수 있어 밀도비의 주 센서로 고른다. 컷오프 탐침은 차단 주파수로 전자 밀도의 절대값을 주므로 평균 밀도 교정용이다.\n'
         'VI 프로브는 코일 쪽 전력을 재지만, ICP 안테나는 거의 순수 리액턴스라 위상 0.1° 오차가 전력 17% 오차가 된다. 그래서 제어 기준은 전력이 아니라 코일 전류로 잡는다. OES는 시선 적분이라 위치별 밀도비에는 약하고, B-dot 탐침은 표피 깊이와 코일 장 분포를 확인하는 데 쓴다.')

# =================================================================== measure
s = new('measure', f'{K4} · FHP 배열과 밀도비', '웨이퍼 FHP 배열이 약 1초마다 n̄와 R_{Γ}를 준다', 'S4')
wcx, wcy, wd = 1.95, 2.8, 2.7
sc = wd / 300
circle(s, wcx, wcy, wd, fill='EEF1F6', line='9AA3B5', lw=1.25)
def dots(rmm, n, col, phase=0.0):
    for k_ in range(n):
        a = 2 * math.pi * k_ / n + phase
        circle(s, wcx + rmm * sc * math.cos(a), wcy + rmm * sc * math.sin(a), 0.14, fill=col)
circle(s, wcx, wcy, 0.14, fill=C['BLUE'])
dots(25, 4, C['BLUE'], math.pi / 4)
dots(75, 4, C['GRAY'])
dots(140, 8, C['ORANGE'], math.pi / 8)
for i, (col, txt) in enumerate([(C['BLUE'], '중앙 5점: 0, 25 mm'), (C['GRAY'], '모양 4점: 75 mm'), (C['ORANGE'], '가장자리 8점: 140 mm')]):
    yy = 4.3 + i * 0.28
    circle(s, 0.72, yy + 0.14, 0.13, fill=col)
    tb(s, 0.88, yy, 2.8, 0.28, [txt], size=12, anchor='m')
tb(s, 0.5, 5.2, 3.2, 0.5, ['ψ = +½ (중앙), −½ (가장자리)', '75 mm 4점은 모양 확인용'], size=12, color=C['MUTED'], anchor='m', space_after=0)
box(s, 3.75, 1.42, 5.75, 2.55, fill=C['NAVY_L'], radius=0.08)
tb(s, 3.9, 1.5, 5.5, 0.3, ['부유 고조파 탐침(FHP)의 원리'], size=12.5, bold=True, color=C['NAVY'])
tb(s, 3.9, 1.86, 5.5, 2.05, [
    dict(t='부유 탐침에 작은 사인파 v_{0}를 걸면 시스의 비선형성으로 고조파 전류가 생긴다', after=4),
    dict(t='T_{e} = (v_{0}/4)·I_{ω}/I_{2ω} (1차·2차 고조파 전류비)', after=4),
    dict(t='이온 포화 전류 I_{is} = 0.61 e n u_{B} A_{p} → 선속 n u_{B}', after=4),
    dict(t='부유 상태라 교란이 작고, 웨이퍼에 여러 개를 배열할 수 있다')], size=12, bullet=True, bullet_color=C['NAVY'])
box(s, 3.75, 4.12, 5.75, 1.63, fill=C['PANEL'], radius=0.08)
tb(s, 3.9, 4.18, 5.5, 0.3, ['점별 로그 변화를 둘로 나눈다'], size=12.5, bold=True, color=C['INDIGO'])
eq(s, 'eq_split', 3.95, 4.55, pt=15)
tb(s, 3.9, 4.98, 5.5, 0.75, [
    dict(t='[[n:a_{0}]] 전체 변화, [[n:a_{1}]] 분포 변화. a_{1}이 2% 안이면 전체 변화만', after=2),
    dict(t='점별 잡음 2%(가정) → ln R_{Γ} ±1.1%, R ±3.7% (T_{e} 5% 가정)')], size=12)
msg(s, '전체 변화(a_{0})와 분포 변화(a_{1})를 나눠 본다. 제어 출력은 R_{Γ}, R은 환산 보고')
note(s, 'FHP가 재는 것은 선속비 R_{Γ} = R·√(T_{e,c}/T_{e,e}). 탐침 조건 예: 1 cm, 1 V, 5 kHz [Pa17]')
notes(s, '앞 쪽에서 주 센서로 고른 부유 고조파 탐침(FHP)의 원리와, 그것으로 밀도비를 재는 방법이다. 2차 발표의 측정 계획(제출물 ④)의 바탕이 된다. 측정은 바깥 루프 주기 안에 n̄와 R을 잴 수 있는가, 전체 변화와 분포 변화를 구분할 수 있는가, 공식 사슬의 중간 단계를 확인할 수 있는가에 답해야 한다.\n주 센서는 웨이퍼형 부유 고조파 탐침(FHP) 배열이다. 1차·2차 고조파 전류의 비로 T_e를, 이온 포화 전류로 n u_B를 구한다. 그래서 FHP가 재는 것은 밀도가 아니라 이온 선속이고, 선속비 R_Γ = R·√(T_e,c/T_e,e)다. T_e 상대 오차 5%(가정)면 R의 불확도는 약 3.7%로 커지므로 제어 출력은 R_Γ로 두고 R은 환산해 보고하자고 제안한다.\n전체/분포 변화 구분은 점별 로그 변화를 a₀ + a₁ψ + ε로 최소제곱 분해한다. a₁이 불확도의 2배(약 2%) 안이면 전체 변화만 있었다고 본다. 랭뮤어 탐침은 EEPF로 식 2의 λε 가설을, B-dot 탐침은 식 1의 장 계산을 확인하는 데 쓴다.')

# =================================================================== simple
s = new('simple', f'{K5} · 단순 제어의 한계', '이론으로 본 단순 제어의 한계 다섯 가지', 'S5')
rows = [['문제', '단순한 방법', '어긋나는 이론', '생기는 문제', '해결 방향', '근거'],
        ['1 압력', '아무 압력에서나 운전한다', '식 2 λ_{ε}', '저압에선 λ_{ε} > 코일 간격 → 분배가 R을 못 움직임', '20–30 mTorr, 저압이면 자기장', '§f2§쪽'],
        ['2 공진', '전원 하나 + 공진 C로 가장자리 전류를 키운다', '식 1 공진 전류', '공진점이 플라즈마 부하로 이동 → 분배가 밀도에 끌려감', '독립 전원 2대로 분배를 설정값으로', '§lc§쪽'],
        ['3 위상', '두 전원을 따로 켠다', '식 1c 교환 전력', '위상이 흔들리면 전원끼리 전력을 주고받음 (∝ sin φ)', '공통 발진기로 위상 0° 고정', '§p_phase§쪽'],
        ['4 동반', '가장자리 전력만 올린다', '식 5 손실 비대칭', '평균 밀도도 같이 변함 (J_{12}/J_{22} ≈ 0.10)', '분배와 총 전력을 J^{−1}로 동시에', '§f5§쪽'],
        ['5 신호', '전력계 값과 탐침 한 점으로 맞춘다', 'ΔP/P = tan θ_{Z}·Δθ', '위상 0.1°에 전력 17% 오차, 한 점으론 전체/분포 구분 불가', '코일 전류 기준 + FHP 배열', '§diag§쪽']]
rows = [[R(c) for c in r] for r in rows]
table(s, 0.5, 1.42, [0.8, 1.95, 1.35, 2.35, 1.85, 0.7], rows, size=12, row_h=0.8, col_align=['c', 'l', 'l', 'l', 'l', 'c'],
      row_heights=[0.4] + [0.78] * 5, bold_cells={(i, 0) for i in range(1, 6)} | {(i, 4) for i in range(1, 6)},
      colors={**{(i, 0): C['INDIGO'] for i in range(1, 6)}, **{(i, 2): C['AMBER'] for i in range(1, 6)}, **{(i, 4): C['NAVY'] for i in range(1, 6)}})
msg(s, '문제 1–3은 구조·운전 조건으로, 4–5는 운용·측정으로 → 2차 발표에서 설계한다')
notes(s, '2장의 결론대로라면 가장자리 밀도를 올리려면 가장자리 전력을 올리면 된다. 그런데 이것을 단순하게 구현하면 다섯 곳에서 어긋난다. 표의 세 번째 열이 그 문제를 예고하는 공식이다.\n'
         '문제 1, 압력: 저압에서는 식 2의 λε가 코일 간격보다 길어 분배가 R을 움직이지 못한다. 문제 2, 공진: 전원 하나에 공진 커패시터로 가장자리 전류를 키우면 식 1의 공진점이 플라즈마 부하에 따라 움직인다. 문제 3, 위상: 두 전원을 따로 켜면 식 1c의 교환 전력이 생긴다. 문제 4, 동반 변화: 식 5의 손실 비대칭 때문에 가장자리 전력만 올리면 평균 밀도도 따라 움직인다. 문제 5, 신호: ICP 안테나는 거의 순수 리액턴스라 전력계 값은 위상 0.1° 오차에 17% 틀리고, 탐침 한 점으로는 전체 변화와 분포 변화를 구분하지 못한다.\n'
         '문제 1–3은 구조와 운전 조건으로, 문제 4–5는 운용과 측정으로 푼다. 이 해결 방향을 구체적인 설계로 만드는 것이 2차 발표다. 먼저 문제 1의 운전 압력을 계산으로 본다.')

# =================================================================== p_pressure
s = new('p_pressure', f'{K5} · 운전 압력', '문제 1 압력: 20 mTorr 이상이어야 R 0.8에 닿는다', 'S5')
data = [(5, 1.07, 1.97, 1.10, 1.11), (10, 0.88, 2.81, 0.92, 0.94), (15, 0.73, 3.68, 0.78, 0.81),
        (20, 0.62, 4.52, 0.68, 0.72), (30, 0.49, 5.97, 0.55, 0.60)]
VMIN, VMAX = 0.4, 1.6
cx_, cy_, cw_, ch_ = 0.5, 1.42, 5.4, 4.3
lay = (0.13, 0.04, 0.84, 0.80)
band_behind(s, cx_, cy_, cw_, ch_, lay, VMIN, VMAX, 0.8, 1.2)
cd = CategoryChartData()
cd.categories = [str(d[0]) for d in data]
cd.add_series('하한 아래', [d[1] for d in data])
cd.add_series('선택도로 막힘', [d[4] - d[1] for d in data])
cd.add_series('낼 수 있는 R', [VMAX - d[4] for d in data])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_STACKED, I(cx_), I(cy_), I(cw_), I(ch_), cd)
gf.name = '압력별 R 범위 그래프'
ch = gf.chart; style_chart(ch, size=12); ch.has_legend = False
plot = ch.plots[0]; plot.gap_width = 45; plot.overlap = 100
sr = plot.series
sr[0].format.fill.background(); sr[0].format.line.fill.background()
sr[1].format.fill.solid(); sr[1].format.fill.fore_color.rgb = rgb('C3D0EA')
sr[2].format.fill.solid(); sr[2].format.fill.fore_color.rgb = rgb(C['NAVY'])
lab_col = [C['DARK'], C['DARK'], C['AMBER'], C['NAVY'], C['NAVY']]
for i, d in enumerate(data):
    label_point(sr[0].points[i], f'{d[3]:.2f}–{d[4]:.2f}', XL_LABEL_POSITION.INSIDE_END, size=12, color=lab_col[i], bold=True)
style_axis(ch.value_axis, VMIN, VMAX, 0.2, '0.0', grid=True, size=12)
style_axis(ch.category_axis, size=12.5)
axis_title(ch.value_axis, '밀도비 R', size=12); axis_title(ch.category_axis, '압력 (mTorr)', size=12)
plot_layout(ch, *lay)
px0, pw = cx_ + cw_ * lay[0], cw_ * lay[2]
py0 = cy_ + ch_ * lay[1]
lx = 6.1
items = [(C['NAVY'], '코일 선택도 한계 안에서 낼 수 있는 R'),
         ('C3D0EA', '중앙 몫을 2%까지 줄여야 닿는 부분'),
         (C['TARGET'], '목표 R 0.8–1.2')]
for i, (col, txt) in enumerate(items):
    yy = 1.42 + i * 0.4
    box(s, lx, yy + 0.06, 0.26, 0.26, fill=col, radius=0.03)
    tb(s, lx + 0.36, yy, 3.04, 0.38, [txt], size=12, anchor='m')
tb(s, lx, 2.64, 3.4, 0.6, ['막대 아래 숫자 = 낼 수 있는 R의 하한', '막대는 1.6 위로 계속된다 (최대 2.0–6.0)'], size=12, color=C['DARK'], space_after=2)
rows = [['압력', '판정'],
        ['5, 10 mTorr', '0.8에 못 닿음'],
        ['15 mTorr', '[[a:경계]]'],
        ['20, 30 mTorr', '[[n:여유]]']]
table(s, lx, 3.3, [1.6, 1.8], rows, size=13, row_h=0.35, col_align=['l', 'c'])
box(s, lx, 4.8, 3.4, 0.95, fill=C['PANEL'], radius=0.06, paras=[
    dict(t='실험 근거: KC20 공진 코일의 R', bold=True, size=12, color=C['INDIGO'], after=1),
    dict(t='1 mTorr: 1.81 → 1.22 (조금)', size=12, after=0),
    dict(t='50 mTorr: 2.54 → 0.39 (반전)', size=12)], margin=0.1, anchor='m')
msg(s, '운전 압력은 20–30 mTorr. 15 mTorr 아래로 내려야 하면 자기장 보조 (§field§쪽)')
note(s, '2-영역 0D, 300 W, 영역 전력 직접 지정 (계산). 모델이 KC20 공진을 과소평가 → 절대 범위는 V1·V2에서 재확인')
notes(s, '이론을 주제에 적용한 첫 결과, 운전 압력이다. 식 2(가열)와 식 6(확산)을 포함해 두 영역 모델로 계산하면, 압력별로 낼 수 있는 R의 범위가 이 그래프다. 영역 전력을 직접 지정한 계산이라 어떤 구동 방식이든 분배를 마음대로 정할 수 있을 때의 범위다.\n옅은 막대는 중앙 몫을 2%까지 줄여야 닿는 부분인데, 실제 코일은 바깥 코일만 켜도 흡수의 5–7%가 중앙에 떨어진다(식 1의 코일 선택도). 이것을 넣은 하한이 막대 아래 숫자다.\n그러면 R = 0.8은 15 mTorr에서 겨우 닿고 20 mTorr부터 여유가 생긴다. 10 mTorr는 약 0.9–1.2, 5 mTorr는 1.1 위만 가능하다. 그래서 해결 방안은 운전 압력을 20–30 mTorr로 두는 것이고, 15 mTorr 아래로 내려야 하면 자기장으로 λε를 줄이는 보조 수단을 검토한다.\nKC20도 같은 구조가 1 mTorr와 50 mTorr에서 전혀 다르게 반응함을 보였다. 다만 같은 모델이 KC20의 고압 공진 측정을 과소평가했으므로 절대 범위는 V1·V2에서 다시 확인한다.')

# =================================================================== direction
s = new('direction', f'{K5} · 2차 설계 방향 (예고)', '이론이 가리키는 방향: 독립 전원 2대 + 위상 고정', 'S5')
rows = [['설계 요소', '이론 근거', '방향', '2차 발표에서 확인'],
        ['운전 압력', '식 2: λ_{ε} < Δ여야 분배가 R을 움직인다', '20–30 mTorr (15는 경계)', 'R 범위의 절대값'],
        ['구동 방식', 'LC 공진은 공진점이 밀도에 끌린다 (식 1)', '독립 RF 전원 2대 → 분배를 설정값으로', '정합기 상호작용'],
        ['위상', '식 1c: 교환 전력 ∝ sin φ', '공통 발진기로 고정, 0° 우선', '0° vs 180° (H6)'],
        ['보상', '식 3–5, 7: J가 삼각형', '분배로 R, 총 전력으로 n̄', '조정 절차'],
        ['측정·제어 신호', 'ΔP/P = tan θ·Δθ, FHP 원리', '코일 전류 기준 + FHP 배열', '측정 계획'],
        ['대안', '조절 수단 비교 (3장)', '전원 1대면 LC 공진, 15 mTorr 아래면 자기장', '선택이 바뀌는 조건']]
table(s, 0.5, 1.42, [1.45, 2.85, 2.6, 2.1], rows, size=12, row_h=0.6, col_align=['l', 'l', 'l', 'l'],
      row_heights=[0.38] + [0.64] * 6, first_col_bold=True, fills={(i, 2): C['NAVY_L'] for i in range(1, 7)},
      bold_cells={(i, 2) for i in range(1, 7)}, colors={(i, 2): C['NAVY'] for i in range(1, 7)})
msg(s, '이론은 구조를 좁힌다. 구성도·조정 절차·측정 계획은 2차 발표에서 완성한다')
note(s, '후보 구성도·선택 이유·운용 루프·조정 절차의 초안은 백업 ¤arch¤–¤procedure¤')
notes(s, '지금까지 공부한 이론이 2차 설계에 무엇을 말해 주는지 정리한 표다. 아직 설계를 확정하는 단계가 아니라, 이론으로 후보를 좁힌 결과다.\n'
         '운전 압력은 식 2 때문에 20–30 mTorr로 좁혀진다. 구동 방식은 LC 공진의 한계 때문에 독립 RF 전원 두 대로 분배를 직접 정하는 쪽이 유력하고, 같은 주파수의 두 전원은 교환 전력 때문에 공통 발진기로 위상을 고정해야 한다. J가 삼각형이라는 것은 분배로 밀도비를, 총 전력으로 평균 밀도를 맞추는 보상 방법을 가리키고, 진단 이론은 코일 전류 기준 제어와 FHP 배열을 가리킨다.\n'
         '오른쪽 열이 2차 발표에서 계산과 비교로 확인할 것이다. 후보 구성도와 운용 방식의 초안은 백업에 두었다.')

# =================================================================== plan
s = new('plan', f'{K5} · 2차 발표 계획', '2차 발표 계획: 좁힌 구조를 응답 행렬 J로 검증한다', 'S5')
tb(s, 0.5, 1.42, 4.4, 0.3, ['2차 제출물과 바탕이 되는 이론'], size=13, bold=True, color=C['INDIGO'])
items = [('①', '소스·구동부 구성도', '식 1, 조절 수단 (2–3장)'),
         ('②', '조작 변수–밀도 응답 J(p, φ)', '식 1–7 (2장)'),
         ('③', '목표 밀도비 조정 절차', '식 7의 J^{−1} (2장)'),
         ('④', '측정 계획', '진단 이론 (4장)')]
y = 1.8
for code, name, base in items:
    box(s, 0.5, y, 4.4, 0.62, fill=C['PANEL'], radius=0.06)
    chip(s, 0.5, y, 0.5, 0.62, code, C['INDIGO'], size=14, radius=0.06)
    tb(s, 1.12, y + 0.04, 3.7, 0.56, [dict(t=name, bold=True, size=13, after=0), dict(t=base, size=12, color=C['MUTED'])],
       anchor='m', space_after=0)
    y += 0.7
tb(s, 5.1, 1.42, 4.4, 0.3, ['검증 단계'], size=13, bold=True, color=C['INDIGO'])
phases = [('V1 다음 2주', '회로 모델에 전원 2·위상·다중 턴, KC20 대조 → 압력·위상별 J (H1·H3·H4·H6·H7 1차)', C['NAVY'], 'FFFFFF'),
          ('V2 2D 계산', '축대칭 확산·장 → 측정 위치 환산 (H2, H5)', C['NAVY_L'], C['TEXT']),
          ('V3 측정', '장비가 있으면 실제 J·EEPF로 최종 판정', C['NAVY_L'], C['TEXT'])]
y = 1.8
for head, body, f, tc in phases:
    box(s, 5.1, y, 4.4, 0.86 if head.startswith('V1') else 0.62, fill=f, radius=0.06, paras=[
        dict(t=head, bold=True, size=13, color=tc, after=1), dict(t=body, size=12, color=tc)], margin=0.12, anchor='m')
    y += (0.94 if head.startswith('V1') else 0.7)
panel(s, 0.5, 4.75, 9.0, 1.0, '팀 결정 필요', [
    '위상 기준 (원안 180° → 제안 0°) · 운전 압력 20–30 mTorr · 목표 R 0.8–1.2, n̄ ±5% · 제어 출력 R_{Γ} · 장비 (전원 2대, 공통 발진기, FHP)'],
    kind='a', size=12.5)
msg(s, '2차 발표: 압력·위상별 J로 구성도·조정 절차·측정 계획을 완성한다')
note(s, '가설 H1–H7과 판정 기준은 백업 ¤verify¤, 결정을 바꿀 수 있는 가정은 백업 ¤stages¤')
notes(s, '2차 발표에서 할 일이다. 주제안이 요구하는 제출물 네 가지를 내는데, 각각 오늘 공부한 이론이 바탕이다. 구성도는 식 1과 조절 수단의 원리, 조작 변수와 밀도 응답의 관계는 공식 사슬 전체, 조정 절차는 응답 행렬의 역행렬, 측정 계획은 진단 이론에서 나온다.\n'
         '검증은 세 단계로 간다. 다음 2주의 V1에서 회로 모델에 전원 두 대와 위상, 다중 턴을 넣고 KC20 데이터와 대조해 압력·위상별 J를 만든다. V2는 축대칭 2D 확산·장 계산, V3는 장비가 있으면 실제 J와 EEPF를 잰다.\n'
         '그 전에 팀에서 정할 것이 있다. 위상 기준, 운전 압력, 목표 수치, 제어 출력, 그리고 전원 두 대와 FHP 같은 장비를 쓸 수 있는지다.')

# =================================================================== conclusion
s = new('conclusion', '정리', '정리: 학습한 이론과 주제 3의 연결', '정리')
rows_ = [('ICP 기초', '표피 깊이·E–H 모드', '공식 사슬은 H 모드에서 성립 → H 모드 확인 후 운전'),
         ('식 1 결합 회로', 'Z_{12}, 교환 전력 ∝ sin φ', '코일 전력 ≠ 영역 전력 → 구동 방식이 결합을 정한다'),
         ('식 2 비국소 가열', 'λ_{ε} ∝ 1/p', '압력이 분배의 효과를 정한다 → 20–30 mTorr'),
         ('식 3–5 균형·손실', 'n_{k} ∝ P_{k}/A_{eff,k}', 'R = 전력비 × 손실 비대칭 → n̄ 동반 변화는 보상'),
         ('식 6–7 확산·응답', 'ℓ = L/π, J', '형상이 경계 누설을, J가 독립성(L1/L2)을 판정'),
         ('조절 수단·진단', 'LC 공진, 위상, 자기장, FHP', '수단 대부분은 식 1을 바꾼다, 측정은 FHP 배열')]
y = 1.42
for p_, f_, sol in rows_:
    box(s, 0.5, y, 9.0, 0.6, fill=C['PANEL'], radius=0.06)
    chip(s, 0.5, y, 1.95, 0.6, p_, C['INDIGO'], size=12.5, radius=0.06)
    tb(s, 2.55, y, 2.25, 0.6, [f_], size=12.5, color=C['AMBER'], bold=True, anchor='m')
    seg(s, 4.8, y + 0.3, 5.15, y + 0.3, color=C['NAVY'], w=2, head=True)
    tb(s, 5.25, y, 4.2, 0.6, [sol], size=12.5, bold=True, color=C['NAVY'], anchor='m')
    y += 0.68
msg(s, '이론이 가리키는 구조: 독립 전원 2대 + 공통 발진기(0°) + 20–30 mTorr → 2차에서 검증')
notes(s, '정리한다. 1차 발표에서는 2차 설계에 필요한 이론을 공부했다. 유도 결합의 기초에서 공식 사슬이 H 모드를 전제로 한다는 것을, 결합 회로에서 코일 전력이 곧 영역 전력이 아니라는 것을, 비국소 가열에서 압력이 분배의 효과를 정한다는 것을 배웠다. 입자·전력 균형과 벽 손실은 밀도비가 전력비와 손실 비대칭으로 정해진다는 것을, 확산과 응답 행렬은 형상과 독립성 판정을 알려 준다. 조절 수단 대부분은 회로 항을 바꾸고, 측정은 FHP 배열이 맞다.\n'
         '이 이론들이 가리키는 구조는 독립 RF 전원 두 대와 공통 발진기, 위상 0°, 20–30 mTorr 운전이다. 2차 발표에서 압력·위상별 J로 이것을 검증하고 제출물 네 가지를 낸다. 질문 받겠다.')

# =================================================================== refs
s = new('refs', '참고문헌', '근거 자료와 확인 수준', '참고')
left = [dict(t='학술지·단행본 (본문 확인)', bold=True, color=C['INDIGO'], size=12.5, after=3),
        '[KC20] J.-H. Kim, C.-W. Chung, Phys. Plasmas 27, 063511 (2020)',
        '[Pa17] I.-S. Park et al., Phys. Plasmas 24, 123506 (2017)',
        '[LL05] M. A. Lieberman, A. J. Lichtenberg, Principles of Plasma Discharges and Materials Processing, 2nd ed. (2005)',
        '[LL95] C. Lee, M. A. Lieberman, J. Vac. Sci. Technol. A 13, 368 (1995)',
        '[KG95] V. I. Kolobov, V. A. Godyak, IEEE Trans. Plasma Sci. 23, 503 (1995)',
        '[DD68] C. V. Dodd, W. E. Deeds, J. Appl. Phys. 39, 2829 (1968)',
        dict(t='[Br66] E. H. Bristol, IEEE Trans. Autom. Control 11, 133 (1966)', after=8)]
right = [dict(t='특허 (본문 확인)', bold=True, color=C['INDIGO'], size=12.5, after=3),
         '[P1] US 6,164,241 이중 코일, 단일 전원 분배',
         '[P2] US 9,305,750 LC 탱크로 전류비 범위 확대',
         '[P3] US 9,161,428 코일별 RF 위상의 독립 제어',
         dict(t='[P4] US 2003/0150562 영구자석으로 반경 손실 감소', after=8),
         dict(t='초록만 확인 (주장 근거로 쓰지 않음)', bold=True, color=C['MUTED'], size=12.5, after=3),
         '[J1] D. Lee et al., Plasma Sources Sci. Technol. 13, 701 (2004)',
         '[J2] 이중 주파수 ICP 2D 유체 계산, Phys. Plasmas 22 (2015)',
         '[C1]–[C6] GEC 2009–2025 학회 초록 (위상 고정 이중 코일, 페라이트 + 평판, 자기장)']
tb(s, 0.5, 1.42, 4.4, 5.1, left, size=13, space_after=5)
tb(s, 5.1, 1.42, 4.4, 5.1, right, size=13, space_after=5)
notes(s, '참고문헌은 확인 수준에 따라 나눴다. 주장의 근거는 본문을 확인한 학술지·단행본·특허로만 대고, 초록만 확인한 자료는 선행 사례 소개에만 쓴다.')

# =================================================================== bk_div
s = new('bk_div', '백업', '백업 슬라이드', '백업')
items = [('arch', '구조 후보 구성도'), ('why', '구조 선택 이유'), ('bk_drive', '구동 방식 비교 (A·B·C)'),
         ('p_phase_cmp', '위상 기준 0° vs 180°'), ('control', '운용 루프'), ('procedure', '조정 절차'),
         ('verify', '가설 H1–H7과 판정 기준'), ('stages', '검증 단계와 가정'), ('bk_reactions', '반응 테이블'),
         ('bk_transient', '과도 상황'), ('bk_matching', '정합기 상호작용'), ('bk_qmap', '질문 대응표')]
for i, (k_, t_) in enumerate(items):
    x = 0.5 if i < 6 else 5.1
    y = 1.42 + (i % 6) * 0.7
    box(s, x, y, 4.4, 0.6, fill=C['PANEL'], radius=0.08)
    chip(s, x, y, 0.75, 0.6, f'¤{k_}¤', C['GRAY'], size=13, radius=0.08)
    tb(s, x + 0.9, y, 2.8, 0.6, [t_], size=13, bold=True, color=C['TEXT'], anchor='m')
    tb(s, x + 3.55, y, 0.75, 0.6, [f'{NUM[k_]}쪽'], size=12, color=C['MUTED'], anchor='m', align='r')
notes(s, '질의응답용 백업 슬라이드다. 2차 설계의 초안(구성도, 운용, 조정 절차, 가설)과 보조 자료를 모았다. 질문 번호로 해당 쪽을 찾으려면 마지막 대응표를 연다.')

# =================================================================== arch
s = new('arch', '백업 ¤arch¤ · 구조 후보 구성도 (제출물 ① 초안)', '구조 후보: 독립 전원 2대 + 공통 발진기 위상 0°', '백업')
def blk(x, y, w, h, text, fill, line, tc=C['TEXT'], size=13, bold=False):
    return box(s, x, y, w, h, fill=fill, line=line, lw=1.75, radius=0.08, paras=text, size=size, color=tc,
               bold=bold, align='c', anchor='m', margin=0.05)
y1, y2, bh = 1.5, 3.62, 0.64
oy, oh = 2.38, 0.98
blk(0.5, oy, 1.35, oh, [dict(t='공통 발진기', bold=True, color='FFFFFF', size=13, align='c', after=0), dict(t='13.56 MHz', size=12, color='FFFFFF', align='c')], C['NAVY'], None)
blk(2.25, y1, 1.35, bh, ['[[n:RF 전원 1]]'], 'FFFFFF', C['NAVY'])
blk(3.9, y1, 1.15, bh, ['정합기 1'], 'FFFFFF', C['GRAY'])
blk(5.35, y1, 1.7, bh, [dict(t='안쪽 코일', bold=True, color=C['BLUE'], align='c', after=0), dict(t='r 8 cm', size=12, align='c')], C['BLUE_L'], C['BLUE'])
blk(2.25, y2, 1.35, bh, ['[[n:RF 전원 2]]'], 'FFFFFF', C['NAVY'])
blk(3.9, y2, 1.15, bh, ['정합기 2'], 'FFFFFF', C['GRAY'])
blk(5.35, y2, 1.7, bh, [dict(t='바깥 코일', bold=True, color=C['ORANGE_D'], align='c', after=0), dict(t='r 15.5 cm', size=12, align='c')], C['ORANGE_L'], C['ORANGE'])
box(s, 7.45, y1, 2.05, y2 + bh - y1, fill='FFFFFF', line=C['NAVY'], lw=2, radius=0.1,
    paras=[dict(t='챔버 + 플라즈마', bold=True, size=13.5, color=C['NAVY'], align='c', after=2), dict(t='R 20 cm, L 10 cm', size=12, align='c')],
    anchor='m', margin=0.08)
blk(7.6, y2 + bh - 0.6, 1.75, 0.48, ['웨이퍼 FHP 배열'], C['PANEL'], C['GRAY'], size=12)
path(s, [(1.85, oy + 0.25), (2.05, oy + 0.25), (2.05, y1 + bh / 2), (2.23, y1 + bh / 2)], color=C['NAVY'], w=1.75)
path(s, [(1.85, oy + oh - 0.25), (2.05, oy + oh - 0.25), (2.05, y2 + bh / 2), (2.23, y2 + bh / 2)], color=C['NAVY'], w=1.75)
for yy in (y1 + bh / 2, y2 + bh / 2):
    seg(s, 3.6, yy, 3.88, yy, color=C['NAVY'], w=1.75, head=True)
    seg(s, 5.05, yy, 5.33, yy, color=C['NAVY'], w=1.75, head=True)
    seg(s, 7.05, yy, 7.43, yy, color=C['NAVY'], w=1.75, head=True)
# inner loop (gray)
box(s, 2.25, oy, 3.0, oh, fill=C['PANEL'], line=C['MUTED'], lw=1.5, dash=True, radius=0.1,
    paras=[dict(t='안쪽 루프 (≤ ms)', bold=True, size=13, color=C['DARK'], align='c', after=2),
           dict(t='코일 전류의 크기·위상을 직접 재서 맞춘다', size=12, align='c')], anchor='m', margin=0.08)
seg(s, 2.75, oy, 2.75, y1 + bh + 0.02, color=C['MUTED'], w=1.75, dash=True, head=True)
seg(s, 2.75, oy + oh, 2.75, y2 - 0.02, color=C['MUTED'], w=1.75, dash=True, head=True)
path(s, [(6.2, y1 + bh), (6.2, oy + 0.25), (5.27, oy + 0.25)], color=C['MUTED'], w=1.75, dash=True)
path(s, [(6.2, y2), (6.2, oy + oh - 0.25), (5.27, oy + oh - 0.25)], color=C['MUTED'], w=1.75, dash=True)
tb(s, 6.3, oy + 0.06, 1.1, 0.5, ['전류·위상', '센서'], size=12, color=C['DARK'], space_after=0)
chip(s, 6.27, oy + 0.6, 1.12, 0.3, '문제 5 해결', C['INDIGO'], size=12, radius=0.05)
# outer loop (indigo)
oly = 4.6
box(s, 2.25, oly, 5.0, 0.8, fill=C['INDIGO_L'], line=C['INDIGO'], lw=1.5, dash=True, radius=0.1,
    paras=[dict(t='바깥 루프 (≈ 1 s): FHP → n̄, R_{Γ} → J^{−1} 피드포워드 + 적분', bold=True, size=12.5, color=C['INDIGO'], align='c', after=0),
           dict(t='두 코일 전류의 설정값(총량, 비 k)을 안쪽 루프에 준다', size=12, align='c')], anchor='m', margin=0.06)
path(s, [(8.475, y2 + bh + 0.02), (8.475, oly + 0.4), (7.27, oly + 0.4)], color=C['INDIGO'], w=1.75, dash=True)
seg(s, 3.75, oly, 3.75, oy + oh + 0.02, color=C['INDIGO'], w=1.75, dash=True, head=True)
tb(s, 3.82, y2 + bh + 0.02, 1.0, 0.28, ['설정값'], size=12, bold=True, color=C['INDIGO'])
chip(s, 0.5, 1.67, 1.35, 0.3, '문제 2 해결', C['INDIGO'], size=12, radius=0.05)
chip(s, 0.5, oy + oh + 0.1, 1.35, 0.3, '문제 3 해결', C['INDIGO'], size=12, radius=0.05)
chip(s, 7.55, 1.62, 1.85, 0.3, '문제 1: 20–30 mTorr', C['INDIGO'], size=12, radius=0.05)
chip(s, 7.55, oly + 0.52, 1.85, 0.3, '문제 4: J^{−1} 보상', C['INDIGO'], size=12, radius=0.05)
msg(s, '분배는 두 전원이, 위상은 공통 발진기가, n̄ 보상은 바깥 루프가 맡는다')
note(s, 'R_{Γ}: FHP가 재는 이온 선속비 (≈ R). 칩: 그 부품이 푸는 단순 제어의 한계 (§simple§쪽)')
notes(s, '이론이 가리키는 구조 후보의 초안, 2차 제출물 ① 영역별 소스·구동부 구성도다. 같은 주파수의 RF 전원 두 대가 각자 정합기를 거쳐 안쪽·바깥 코일을 구동하고, 공통 발진기가 두 전원의 위상을 0°로 묶는다. 회색 점선이 안쪽 루프로 코일 전류의 크기와 위상을 직접 재서 맞추고, 보라 점선이 바깥 루프로 웨이퍼 FHP 배열로 n̄와 R_Γ를 재서 두 코일 전류의 설정값을 정한다.\n칩은 각 부품이 단순 제어의 한계(23쪽) 중 어느 문제를 푸는지 표시한 것이다. 독립 전원 두 대가 문제 2(공진점의 부하 의존)를, 공통 발진기가 문제 3(교환 전력)을, 20–30 mTorr 운전이 문제 1(압력)을, 바깥 루프의 J⁻¹ 보상이 문제 4(평균 밀도 동반 변화)를, 전류·위상 센서와 FHP 배열이 문제 5(측정 신호)를 푼다.\n질문 2-1(전원 수와 배치), 2-2(코일 2개면 충분한가)도 여기서 답한다. 독립으로 다룰 수 있는 영역 수는 반경 폭 약 11 cm를 max(λε, ℓ)로 나눈 값 정도라 20 mTorr에서 약 2개이고, 출력이 중앙·가장자리 둘인 이 과제에는 코일 2개가 최소이자 충분하다.')

# =================================================================== why
s = new('why', '백업 ¤why¤ · 구조 선택 이유', '왜 이 구조인가: 공식이 고른 세 가지 이유', '백업')
reasons = [('1', '분배를 설정값으로 정한다', '식 1: 두 전원이 k와 φ를 직접 정한다 → 공진점이 없어 밀도가 바뀌어도 분배 변화 ≤ 0.10 (0°)', '문제 2·3'),
           ('2', 'J가 삼각형이라 루프 둘로 나뉜다', '식 3·4: 총 전력 → n̄, 분배 → R. 상대 이득 λ_{11} ≈ 1 → 단일 루프 둘', '문제 4'),
           ('3', '공식으로 바로 검증된다', '식 1 회로 모델에 전원 하나만 더하면 압력·위상별 J를 계산할 수 있다 (다음 2주, V1)', '검증')]
y = 1.42
for n_, head, body, tag in reasons:
    box(s, 0.5, y, 5.4, 1.25, fill=C['PANEL'], radius=0.08)
    circle(s, 0.9, y + 0.62, 0.5, fill=C['INDIGO'], paras=[n_], size=16, color='FFFFFF')
    tb(s, 1.3, y + 0.08, 3.5, 0.4, [head], size=14, bold=True, color=C['INDIGO'])
    chip(s, 4.8, y + 0.12, 1.0, 0.3, tag, C['NAVY'], size=12, radius=0.05)
    tb(s, 1.3, y + 0.5, 4.5, 0.72, [body], size=12.5)
    y += 1.37
panel(s, 6.1, 1.42, 3.4, 1.95, '대가', [
    dict(t='전원·정합기 2벌, 공통 발진기, 전류·위상 센서', bullet=True),
    dict(t='정합기 상호작용: 바깥 전류를 바꾸면 안쪽 리액턴스 +13–24% (백업 ¤bk_matching¤)', bullet=True)], kind='a', size=12.5, after=5)
panel(s, 6.1, 3.5, 3.4, 1.91, '선택이 바뀌는 조건', [
    dict(t='전원 1대뿐 → 수동 공진 (L1 감수)', bullet=True),
    dict(t='15 mTorr 아래 운전 → 자기장 보조', bullet=True),
    dict(t='경계 분리가 우선이고 위상 유지가 되면 → 180°', bullet=True)], kind='g', size=12.5, after=5)
msg(s, '세 이유 모두 공식에서 나온다: 분배는 설정값으로(식 1), 루프는 둘로(식 3·4), 검증은 바로')
notes(s, '이 구조를 고른 이유를 공식으로 정리하면 세 가지다.\n'
         '첫째, 식 1에서 두 전원이 전류비와 위상을 직접 정하므로 공진점이 없다. 그래서 플라즈마 밀도가 바뀌어도 분배가 거의 그대로다(0°에서 0.10 이하). 이것이 문제 2와 3의 답이다.\n'
         '둘째, 식 3과 4 때문에 J가 삼각형이다. 총 전력은 평균 밀도만, 분배는 밀도비를 주로 움직이므로 제어 루프를 두 개의 단일 루프로 나눌 수 있다. 문제 4의 보상도 이 구조에서 총 전력 하나로 된다.\n'
         '셋째, 기존 회로 모델에 전원 하나만 더하면 바로 계산할 수 있어서 검증 경로가 짧다.\n'
         '대가는 전원·정합기 두 벌과 센서, 그리고 정합기끼리의 상호작용이다. 전원이 1대뿐이거나 저압 운전이 필요하면 선택이 바뀐다.')

# =================================================================== bk_drive
s = new('bk_drive', '백업 ¤bk_drive¤ · 구동 방식 비교 (질문 2-1, 2-4)', '세 구동 방식 비교: B만 분배를 설정값으로 정한다', '백업')
hdr = ['기준', dict(paras=[dict(t='A 수동 공진', bold=True, size=13, color='FFFFFF', align='c', after=0), dict(t='전원 1 + 가변 C', size=12, color='FFFFFF', align='c')]),
       dict(paras=[dict(t='B 독립 전원 2대 ✓', bold=True, size=13, color='FFFFFF', align='c', after=0), dict(t='위상 고정', size=12, color='FFFFFF', align='c')]),
       dict(paras=[dict(t='C 자기장 보조', bold=True, size=13, color='FFFFFF', align='c', after=0), dict(t='B에 추가', size=12, color='FFFFFF', align='c')])]
rows = [hdr,
        ['R 범위', '0.39까지 (50 mTorr 측정), 연속 조정은 미확인', '0.8–1.2 (20–30 mTorr, 모델)', '저압까지 넓힘 (추정)'],
        ['[[n:분배의 밀도 의존]]', '공진점 이동 → [[a:L1]]', '0°에서 ≤ 0.10 → [[n:L2 경계]]', 'B와 같음'],
        ['n̄ 유지 보상', 'P와 C를 동시에 (ΔC +14.8 pF, ΔP +3.5%)', '총 전력만 (Δln P +2.1%)', 'B + h_{R} 변화 보정'],
        ['부작용·비용', '공진 코일 약 350 V (5 A)', '전원·정합기 2벌, 정합기 상호 영향', '파동·ECR, 웨이퍼 자기장']]
fills = {(i, 2): C['NAVY_L'] for i in range(1, 5)}
fills.update({(0, 2): C['INDIGO']})
table(s, 0.5, 1.42, [1.55, 2.5, 2.55, 2.4], rows, size=12, row_h=0.58, first_col_bold=True, fills=fills,
      row_heights=[0.58, 0.62, 0.55, 0.62, 0.58])
msg(s, '선택 B: 분배를 공진점이 아니라 설정값으로 정한다. A는 전원 1대일 때, C는 저압일 때')
note(s, 'A의 수치(ΔC, ΔP, 코일 전압)는 0D 모델 계산. 모델이 공진 상태를 재현하지 못하므로 경향으로만 읽는다')
notes(s, '주제안의 조절 수단에서 뽑은 구동 방식 후보 세 가지의 비교다. 수동 공진 코일의 전류는 식 1의 공진 전류 식으로 정해지는데, 분모의 ΔZ₂₂가 플라즈마 밀도에 따라 변한다. 그래서 밀도가 바뀌면 공진점이 움직이고, 공진 근처에서는 기울기가 가파르다. 커패시터 하나가 n̄와 R을 함께 움직이므로 L1에 머문다.\n'
         '범위만 보면 A도 된다. KC20은 50 mTorr에서 공진만으로 R을 0.39까지 내렸다. 그래서 A를 버리는 이유는 범위가 아니라 독립성이다.\n'
         'B는 두 전원이 전류비 k를 직접 정하므로 공진점이 없고, 0°에서 분배의 밀도 의존이 0.10 이하다. C(약한 축 자기장)는 15 mTorr 아래에서 운전해야 할 때만 B에 더한다. 전원을 1대만 쓸 수 있으면 L1을 감수하고 A로 간다.')

# =================================================================== p_phase_cmp
s = new('p_phase_cmp', '백업 ¤p_phase_cmp¤ · 위상 기준 비교 (질문 2-2)', '0°는 독립성, 180°는 이득이 낫다 → 기준 0°', '백업')
B0 = '[[n:0°]]'; B1 = '[[a:180°]]'
rows = [['항목', 'φ = 0° (동상)', 'φ = 180° (역상)', '유리'],
        ['[[i:분배의 밀도 의존]] ∂ln(P_{c}/P_{e})/∂ln n', '−0.10 ~ −0.01', '+0.41 ~ +0.73', B0],
        ['위상 허용 오차 (교환 ≤ 10%)', '±19–38°', '±4–12°', B0],
        ['필요한 코일 전류 I_{1} / I_{2}', '3.4 / 6.6–7.3 A', '8–12 / 8–10 A', B0],
        ['효율 η = R_{p}/(R_{p} + R_{coil})', '0.95–0.96', '0.85–0.91', B0],
        ['분배 이득 ∂ln(P_{c}/P_{e})/∂ln k', '−0.8 ~ −1.0', '−2.9 ~ −4.0', B1],
        ['경계 ±3 cm 띠에 흡수되는 몫', '0.34–0.35', '0.20–0.22', B1],
        ['안쪽 정합 리액턴스 변화 (X′_{12} 포함)', '+13–24%', '−7–10%', B1]]
fills = {(1, j): C['INDIGO_L'] for j in range(4)}
fills.update({(i, 3): C['NAVY_L'] for i in range(1, 5)}); fills.update({(i, 3): C['AMBER_L'] for i in range(5, 8)})
table(s, 0.5, 1.42, [4.0, 1.9, 1.9, 1.2], rows, size=13, row_h=0.44, col_align=['l', 'c', 'c', 'c'], fills=fills)
box(s, 0.5, 5.08, 9.0, 0.67, fill=C['AMBER_L'], radius=0.08, paras=[
    dict(t='180°의 큰 분배 이득은 전류비 오차도 키운다 → H6에서 같은 기준으로 비교 (원안 180° → 0°는 팀 합의)', size=12.5)],
    margin=0.14, anchor='m')
msg(s, '기준 0°: 밀도가 바뀌어도 분배가 그대로다(독립성). 전류·효율·위상 여유도 낫다')
note(s, '중앙 몫 0.20, 300 W, 10–20 mTorr, 단일 턴·밀도 고정, 코일 저항 0.23 Ω 가정 (계산) → V1에서 다중 턴으로 재계산')
notes(s, '0°와 180° 중 무엇을 기준으로 할지는 공식으로 계산한 비교다. 이 과제의 핵심 기준은 독립성이므로 첫 줄, 분배의 밀도 의존을 가장 무겁게 본다. 0°에서는 밀도가 바뀌어도 분배가 거의 그대로이고(−0.10 ~ −0.01), 180°에서는 0.4–0.7이나 움직인다.\n0°는 같은 300 W에 필요한 코일 전류가 훨씬 작아 코일 손실이 작고, 효율 η = R_p/(R_p + R_coil)과 위상 여유도 낫다.\n180°는 코일 사이에서 장이 상쇄되어 경계 띠 흡수가 줄고, 전류비에 대한 분배 이득이 3–4배 크며, 안쪽 정합이 덜 흔들린다. 다만 분배 이득이 크다는 것은 같은 전류비 오차가 더 큰 분배 오차가 된다는 뜻이기도 하다.\n그래서 0°를 기준으로 제안하고 180°는 가설 H6에서 같은 기준으로 비교한다. 팀 원안이 180°였으므로 기준 변경은 팀 합의 사항이다.')

# =================================================================== control
s = new('control', '백업 ¤control¤ · 운용 루프 (질문 2-5, 4-2)', '플라즈마가 가장 빠르다 → 세 겹 루프로 나눈다', '백업')
X0, X1, LMIN, LMAX = 3.0, 9.3, -8, 4
def xt(t):
    return X0 + (X1 - X0) * (math.log10(t) - LMIN) / (LMAX - LMIN)
rows_ = [('RF 주기', 7.4e-8, None, 'p', '74 ns'),
         ('확산 감쇠', 2e-5, None, 'p', '20 μs'),
         ('입자 손실 τ_{p}', 9e-5, 2e-4, 'p', '0.1–0.2 ms'),
         ('코일 전류 루프', 1e-3, None, 'c', '≤ 1 ms'),
         ('자동 정합', 0.1, 1.0, 'c', '0.1–1 s'),
         ('FHP 갱신', 1.0, None, 'c', '≈ 1 s'),
         ('창·벽 상태 변화', 60, 3600, 'd', '분–시간')]
y0, rh = 1.45, 0.33
# group backgrounds
box(s, 0.5, y0 - 0.04, 9.0, 3 * rh + 0.04, fill=C['INDIGO_L'], radius=0.06, name='플라즈마 행')
box(s, 0.5, y0 + 3 * rh + 0.08, 9.0, 3 * rh, fill=C['NAVY_L'], radius=0.06, name='제어 행')
# decade grid
for e in range(LMIN, LMAX + 1, 2):
    x = xt(10 ** e)
    seg(s, x, y0 - 0.02, x, y0 + 7 * rh + 0.16, color='C9CED8', w=0.75)
for e, lab in [(-8, '10 ns'), (-6, '1 μs'), (-4, '100 μs'), (-2, '10 ms'), (0, '1 s'), (2, '100 s'), (4, '10^{4} s')]:
    x = xt(10 ** e)
    tb(s, x - 0.45, y0 + 7 * rh + 0.18, 0.9, 0.26, [lab], size=12, color=C['MUTED'], align='c')
for i, (nm, t0, t1, g, val) in enumerate(rows_):
    yy = y0 + i * rh + (0.12 if i >= 3 else 0) + (0.04 if i == 6 else 0)
    col = {'p': C['INDIGO'], 'c': C['NAVY'], 'd': C['GRAY']}[g]
    tb(s, 0.6, yy, 2.3, rh, [nm], size=12.5, bold=True, color=col, anchor='m', align='r')
    if t1:
        box(s, xt(t0), yy + rh / 2 - 0.07, xt(t1) - xt(t0), 0.14, fill=col, radius=0.03)
        xe = xt(t1)
    else:
        circle(s, xt(t0), yy + rh / 2, 0.16, fill=col)
        xe = xt(t0) + 0.08
    if g == 'd':
        tb(s, xt(t0) - 1.38, yy, 1.3, rh, [val], size=12, color=col, anchor='m', align='r')
    else:
        tb(s, xe + 0.08, yy, 1.3, rh, [val], size=12, color=col, anchor='m')
# gap annotation
ya = y0 + 3 * rh + 0.04
seg(s, xt(2e-4), ya, xt(0.1), ya, color=C['AMBER'], w=1.75, head=True, tail=True)
tb(s, xt(0.1) + 0.06, ya - 0.14, 2.3, 0.28, ['약 3자릿수 차이'], size=12, bold=True, color=C['AMBER'], anchor='m')
loops = [('안쪽 (≤ ms)', '코일 전류의 크기·위상', '전력 대신 전류 기준 (문제 5): ΔP/P = tan θ_{Z}·Δθ, 위상 0.1°에 17%'),
         ('가운데 (0.1–1 s)', '자동 정합', '정합 위치를 전류비 k의 함수로 미리 옮기는 피드포워드'),
         ('바깥 (≈ 1 s 측정)', 'FHP로 n̄, R_{Γ}', 'J^{−1} 피드포워드 + 적분. 지연 한계 π/(6T_{d}) ≈ 0.5 rad/s, 정합보다 느리게 0.2 rad/s')]
x = 0.5
for head, what, body in loops:
    box(s, x, 4.3, 2.9, 1.45, fill='FFFFFF', line=C['NAVY'], lw=1.25, radius=0.08, paras=[
        dict(t=head, bold=True, size=13.5, color=C['NAVY'], after=1), dict(t=what, bold=True, size=12.5, after=3),
        dict(t=body, size=12, color=C['TEXT'])], margin=0.12)
    x += 3.05
msg(s, '세 루프는 시간으로 갈라지고, J가 삼각형이라 바깥 루프도 단일 루프 둘로 나뉜다')
note(s, '상대 이득 λ_{11} ≈ 1 → 단일 루프 둘 (RGA [Br66]), J_{12}는 피드포워드로 보상. T_{d}: FHP 갱신 ≈ 1 s')
notes(s, '구조 후보를 어떻게 운용할지의 초안이다. 플라즈마 밀도 응답은 0.1–0.2 ms이고 센서와 정합기는 0.1–1 s라 세 자릿수 차이가 난다. 그래서 제어 설계에서는 플라즈마를 정적 이득 J로 다뤄도 되고, 정상 상태 공식 사슬이 그대로 제어 모델이 된다.\n루프는 바깥으로 갈수록 느리게 잡는다. 전류 루프(≤ 1 ms)와 정합(0.1–1 s)은 백 배 이상 떨어져 있고, 바깥 루프는 정합보다 약 5배 느리게 둔다. 안쪽 루프를 전력이 아니라 코일 전류로 잡는 이유는 문제 5다. ICP 안테나는 거의 순수 리액턴스라 tan θ_Z ≈ 100이고, 전압·전류로 잰 전력은 위상 0.1° 오차에 17%가 틀린다.\n바깥 루프 대역폭은 측정 지연이 정한다. 적분기와 지연만 있는 루프에서 위상 여유 60°를 지키려면 ω_c ≤ π/(6 T_d)이고, 정합기보다 5배 느리게 두면 0.2 rad/s, 설정 시간 약 20 s다. 두 채널은 J₂₁ ≈ 0이라 상대 이득 λ₁₁ ≈ 1이고 단일 루프 둘로 나눠도 된다.')

# =================================================================== procedure
s = new('procedure', '백업 ¤procedure¤ · 조정 절차 (제출물 ③ 초안)', '조정 절차: 분배로 R, 총 전력으로 n̄', '백업')
steps = [('점화', '안쪽으로 점화 → H 모드 확인 → 바깥 전원·위상 고정'),
         ('동작점', '압력별 J 표에서 J_{11}, J_{12}, J_{22} 읽기'),
         ('피드포워드', 'Δx와 Δln P를 동시에 설정'),
         ('전류 루프·정합', '(x, P) → (k, I) 변환(식 1b), 정합은 k별 위치표'),
         ('바깥 루프', 'FHP로 a_{0}(전체)·a_{1}(분포) → 남은 오차 적분'),
         ('판정', '|Δln R_{Γ}| ≤ 0.02, n̄ ±5% → 완료')]
y = 1.42
for i, (head, body) in enumerate(steps):
    circle(s, 0.75, y + 0.3, 0.46, fill=C['NAVY'], paras=[str(i + 1)], size=15, color='FFFFFF')
    tb(s, 1.15, y + 0.02, 4.45, 0.7, [dict(t=head, bold=True, size=14, color=C['NAVY'], after=0), dict(t=body, size=13)], line=1.0, space_after=0)
    if i < 5:
        seg(s, 0.75, y + 0.55, 0.75, y + 0.78, color='9AA3B5', w=1.25)
    y += 0.73
box(s, 5.75, 1.42, 3.75, 4.33, fill=C['PANEL'], radius=0.1)
tb(s, 5.95, 1.52, 3.4, 0.6, [dict(t='계산 예 (20 mTorr)', bold=True, size=14, color=C['NAVY'], after=2),
                             dict(t='R을 ln으로 0.2(약 18%) 낮추고 n̄ 유지', size=13)])
eq(s, 'eq_step1', 5.95, 2.22, pt=16)
eq(s, 'eq_step2', 5.95, 2.86, pt=16)
tb(s, 5.95, 3.52, 3.4, 0.3, ['J_{11} = 1, J_{12} = 0.25, J_{22} = 2.44'], size=12.5, color=C['DARK'])
box(s, 5.95, 3.9, 3.35, 0.56, fill='FFFFFF', radius=0.06, paras=[dict(t='Δx = −0.082', size=20, bold=True, color=C['NAVY'], align='c')], anchor='m')
box(s, 5.95, 4.54, 3.35, 0.56, fill='FFFFFF', radius=0.06, paras=[dict(t='Δln P = +2.1%', size=20, bold=True, color=C['NAVY'], align='c')], anchor='m')
tb(s, 5.95, 5.2, 3.4, 0.4, ['보상하지 않으면 n̄ −2.1%'], size=12.5, color=C['TEXT'], anchor='m')
msg(s, '분배로 R을 옮기고, 그때 움직인 n̄는 총 전력으로 되돌린다 (J^{−1}로 동시에)')
note(s, 'x: 중앙 전력 몫, P: 총 흡수 전력. 분배가 한계(중앙 몫 약 0.07 / 0.93)에 닿으면 압력을 올리거나 자기장 보조')
notes(s, '검토 사항 3(한 영역을 유지하며 다른 영역을 바꾸는 조작 순서와 보상)에 대한 초안(2차 제출물 ③)이고, 문제 4의 해결 방향이다. 식 7의 J가 삼각형이므로 분배로 R을 맞추고, 그때 식 5의 손실 비대칭 때문에 생기는 n̄ 변화(J₁₂ 몫)를 총 전력으로 되돌린다. 실제로는 두 조작을 J⁻¹로 동시에 내보내고, 순서 규칙은 피드포워드가 틀렸을 때의 수동 절차로 쓴다.\n숫자 예: 20 mTorr에서 R을 ln 기준 0.2(약 18%) 낮추려면 중앙 몫을 0.082 줄이고 총 전력을 2.1% 올린다. 보상하지 않으면 n̄가 2.1% 내려간다. 같은 변경을 수동 공진으로 하면 커패시터와 전력을 함께 움직여야 했다.\n분배가 코일 선택도 한계(중앙 몫 약 0.07 또는 0.93)에 닿으면 그 압력에서는 목표에 닿지 못하는 것이므로 압력을 올리거나 자기장 보조를 검토한다. 판정 기준은 FHP가 직접 재는 R_Γ로 |Δln R_Γ| ≤ 0.02다.')

# =================================================================== verify
s = new('verify', '백업 ¤verify¤ · 가설과 판정 기준', '가설 7개: 5개는 다음 2주(V1)에 1차 판정한다', '백업')
rows = [['가설', '예측 (수식)', '판정 기준', '단계'],
        ['**H1** 압력이 높을수록 분배가 R을 움직이는 힘이 크다', '식 2: g_{R} = 0.5 → p ≈ 11 mTorr', '반값 압력 5.5–22 mTorr', 'V1·V3'],
        ['**H2** L이 작을수록 확산 누설이 작다', '식 6: e^{−πΔ/L} = 0.02–0.14', '2D 누설이 식의 0.5–2배', 'V2'],
        ['**H3** 저압 동반 변화 = 비국소 가열·회로 결합', '전류 고정 시 남는 결합 ≈ 1 − g_{R}', '식과 ±30% 안', 'V1'],
        ['**H4** 코일 전류(총량, 비 k)로 조작해도 J가 삼각형', 'J_{21} = 0 (식 3), 회로 포함 0°: 약 0.1 이하', 'J_{21}/J_{11} ≤ 0.1 (L2)', 'V1·V3'],
        ['**H5** 약한 축 자기장이 저압 독립성을 높인다', '5 mTorr, 약 2.7 G에서 λ_{ε⊥} = Δ', '5 mTorr에서 g_{R} ≥ 0.5', 'V2'],
        ['**H6** 0°가 더 독립적, 180°는 이득이 크다', '위상 비교표 (§p_phase_cmp§쪽)', '180° 채택: 이득 ×2 이상, 밀도 의존 ≤ 0.2', 'V1'],
        ['**H7** 20–30 mTorr에서 R 0.8–1.2, n̄ ±5%', 'R 범위 예측 (§p_pressure§쪽)', '|Δln R_{Γ}| ≤ 0.02, n̄ ±5%', 'V1']]
rows = [[R(c) for c in r] for r in rows]
table(s, 0.5, 1.42, [3.45, 2.65, 2.2, 0.7], rows, size=12.5, row_h=0.56, col_align=['l', 'l', 'l', 'c'],
      row_heights=[0.4] + [0.55] * 7, bold_cells={(i, 3) for i in range(1, 8)},
      colors={(i, 3): ('FFFFFF' if rows[i][3].startswith('V1') else C['MUTED']) for i in range(1, 8)},
      fills={(i, 3): (C['NAVY'] if rows[i][3].startswith('V1') else C['PANEL']) for i in range(1, 8)})
msg(s, '예측은 모두 공식 사슬에서 나온다. 판정은 절대 밀도가 아니라 비(R, g_{R}, 누설)로')
note(s, 'V1: 회로 모델 확장·KC20 대조, V2: 축대칭 2D, V3: 측정. H1·H4의 가열·T_{e} 가정 자체는 V3(EEPF)로 확인')
notes(s, '2차 발표에서 쓸 검증 계획의 초안이다. 오늘 말한 주장을 모두 “공식 → 예측값 → 판정 기준”으로 바꿔 두었다. 예측은 공식 사슬의 각 식에서 나온다. H1은 식 2(가열 위치), H2는 식 6(확산), H4는 식 3(T_e가 전력과 무관)의 측정 확인이고, H6은 식 1c를 포함한 위상 비교, H7이 과제 목표 자체의 판정이다.\n판정 범위(예측의 0.5–2배, ±30%)는 0D 근사의 정확도를 고려한 제안값이다. 판정은 절대 밀도가 아니라 비로 한다. 일곱 개 중 다섯 개는 다음 2주의 V1(회로 모델 확장)로 판정할 수 있다.')

# =================================================================== stages
s = new('stages', '백업 ¤stages¤ · 검증 단계와 가정', '검증 단계와 결정을 바꿀 수 있는 가정', '백업')
phases = [('V0 이번 발표', '식과 단발 계산', C['GRAY_L'], C['TEXT']),
          ('V1 다음 2주', '회로에 전원 2·위상·다중 턴 → 압력·위상별 J, H1·H3·H4·H6·H7', C['NAVY'], 'FFFFFF'),
          ('V2 2D 계산', '축대칭 확산·장, 측정 위치 환산 → H2, H5', C['NAVY_L'], C['TEXT']),
          ('V3 측정', '장비가 있으면 실제 J·EEPF로 최종 판정', C['NAVY_L'], C['TEXT'])]
x = 0.5
for (head, body, f, tc), w in zip(phases, [1.55, 3.05, 2.3, 2.0]):
    shp = box(s, x, 1.42, w + 0.15, 1.3, fill=f, shape=MSO_SHAPE.CHEVRON if x > 0.5 else MSO_SHAPE.PENTAGON, radius=None,
              adj=[0.14], paras=[dict(t=head, bold=True, size=13, color=tc, after=3), dict(t=body, size=12, color=tc)], margin=0.08, anchor='m')
    shp.text_frame.margin_left = I(0.3 if x > 0.5 else 0.12); shp.text_frame.margin_right = I(0.22)
    x += w + 0.03
risks = [('λ_{ε} 브리지 w = e^{−Δ/λε} (식 2)', '운전 압력 범위와 p*', 'V3 위치별 EEPF (랭뮤어 탐침)'),
         ('0D 모델이 고압 공진을 재현 못함', 'R 범위의 절대값', 'V1·V2에서 재계산'),
         ('단일 턴·균일 반공간·밀도 고정 (식 1)', '0°/180° 수치 (sin φ 결론은 유지)', 'V1 다중 턴·자기일관 밀도'),
         ('장비: 전원 2대, 공통 발진기, FHP', '구조 자체 (없으면 수동 공진)', '즉시 확인')]
pos = [(0.5, 2.92), (5.1, 2.92), (0.5, 4.38), (5.1, 4.38)]
for i, ((a, d, chk), (x, y)) in enumerate(zip(risks, pos)):
    box(s, x, y, 4.4, 1.36, fill=C['PANEL'], radius=0.08)
    circle(s, x + 0.32, y + 0.31, 0.4, fill=C['INDIGO'], paras=[str(i + 1)], size=13, color='FFFFFF')
    tb(s, x + 0.62, y + 0.1, 3.7, 0.42, [a], size=13, bold=True, color=C['INDIGO'], anchor='m')
    tb(s, x + 0.2, y + 0.56, 4.05, 0.36, ['[[m:걸린 결정]] ' + d], size=12.5)
    tb(s, x + 0.2, y + 0.92, 4.05, 0.36, ['[[n:확인]] ' + chk], size=12.5)
msg(s, '장비(전원 2대·공통 발진기·FHP 배열)부터 확인한다. 없으면 구조 자체가 바뀐다')
note(s, '나머지 가정(맥스웰 분포, 코일 저항, 확산 원거리 근사)은 수치를 옮기지만 방향은 바꾸지 않는다')
notes(s, '검증은 네 단계다. V0가 오늘 발표한 식과 단발 계산이고, 다음 2주의 일이 V1이다. 회로 모델을 전원 2개·위상·다중 턴으로 확장해 압력·위상별 J를 만들고 H1, H3, H4, H6, H7을 판정한다. V2는 축대칭 2D 확산·장 계산, V3는 장비가 있으면 실제 J를 잰다.\n'
         '결정을 뒤집을 수 있는 가정은 네 가지다. λε 브리지는 운전 압력 범위가 걸린 가정이라 H1과 위치별 EEPF로 확인한다. 0D 모델은 고압 공진을 재현하지 못했으므로 R 범위의 절대값은 아직 확정이 아니다. 위상 비교는 단일 턴·밀도 고정 계산이라 다시 해야 하지만 교환 전력이 sin φ에 비례한다는 결론은 유지된다. 장비가 없으면 구조 자체를 바꿔야 하므로 가장 먼저 확인한다.')

# =================================================================== bk_reactions
s = new('bk_reactions', '백업 ¤bk_reactions¤ · 반응 테이블 (질문 1-7)', '1차 모델은 Ar 반응 다섯 개로 충분하다', '백업')
rows = [['반응', '문턱 (eV)', '모델에서의 역할'],
        ['R1 이온화 e + Ar → Ar^{+} + 2e', '15.76', '입자 균형 → T_{e} (식 3)'],
        ['R2 여기(합산) e + Ar → Ar* + e', '12.14', '충돌 에너지 손실 ε_{c} → ε_{T} (식 4)'],
        ['R3 탄성 e + Ar → e + Ar', '–', 'ε_{c}의 탄성 항, ν_{m} (표피 깊이, 자화 조건)'],
        ['R4 이온-중성 (전하 교환 포함)', '–', 'h-factor (식 5), 양극성 확산 (식 6)'],
        ['W1 벽 재결합', '–', '입자·에너지 손실 (식 3, 4)']]
table(s, 0.5, 1.42, [3.6, 1.0, 4.4], rows, size=12, row_h=0.4, col_align=['l', 'c', 'l'])
tb(s, 0.5, 3.92, 9.0, 0.55, ['속도 계수: 맥스웰 분포 평균 [LL05]. T_{e} = 2.5 eV에서 K_{iz} ≈ 3.8×10^{−17}, K_{ex} ≈ 2.0×10^{−16}, K_{el} ≈ 9.8×10^{−14} m^{3}/s, ε_{c} ≈ 81 V, ε_{T} ≈ 99 V (계산)'],
   size=12, color=C['TEXT'])
rows = [['확장 후보', '왜 중요한가', '넣는 기준'],
        ['준안정 Ar^{m}, 단계 이온화', '밀도가 전력에 비선형 → J_{21} ≠ 0', '단계 이온화 비중 > 10%'],
        ['기체 가열·중성 고갈', 'n_{g} 감소 → λ_{ε} 증가 → g_{R} 감소', '고전력 기체 온도 추정 뒤'],
        ['공정 기체 (Cl_{2}, CF_{4}, O_{2})', '음이온이 T_{e}를 전력 의존으로 (식 3이 깨짐)', '과제를 공정 기체로 넓힐 때']]
table(s, 0.5, 4.55, [2.7, 3.6, 2.7], rows, size=12, row_h=0.4, header_fill=C['GRAY'])
note(s, '맥스웰 가정 점검: 비국소 영역(약 10 mTorr 아래)은 랭뮤어 EEPF를 적분한 속도 계수와 비교')
notes(s, '5–30 mTorr Ar에서 T_e와 에너지 손실을 정하는 것은 R1–R3이고 이온 수송을 정하는 것은 R4다. 이 범위에서는 식 3대로 T_e가 전력과 무관해 J₂₁ = 0이 성립한다. 확장 후보는 모두 이 결론을 깨는 방향으로 작용하므로, 넣을지를 판정 기준과 함께 정해 두었다. ε_T = ε_c + 2T_e + 5.2T_e ≈ 99 V다.')

# =================================================================== bk_transient
s = new('bk_transient', '백업 ¤bk_transient¤ · 과도 상황 (질문 4-3)', '과도는 점화, 레시피 변경, 위상 드리프트에서', '백업')
rows = [['상황', '무엇이 바뀌나', '대응'],
        ['점화와 E→H 전이', 'E 모드에선 분포가 축전 결합을 따르고 전이 때 h_{R} 급변, 흡수·손실 곡선의 교점이 둘이라 이력', '안쪽 코일로 점화, H 모드 확인 뒤 바깥 전원, 그 뒤 바깥 루프'],
        ['레시피 변경', '압력·기체가 바뀌면 λ_{ε}, h, T_{e}가 바뀌어 J 자체가 바뀐다 (g_{R} 0.27 → 0.85)', '압력별 J 표로 이득 스케줄링, 압력 안정 뒤 루프 재개'],
        ['한쪽 전원 변경', 'M_{12}로 다른 쪽 정합이 틀어져 반사 전력이 잠시 는다', '전류 루프가 먼저 잡고 정합기는 위치표로'],
        ['위상 드리프트', '정합 상태에 따라 코일 전류 위상이 움직여 교환 전력이 생긴다', '코일 전류 위상을 직접 재서 보정 (0°에서 약 ±20° 안)'],
        ['분배를 극단으로', '약한 쪽 영역의 가열이 축전 결합 쪽으로 기울 수 있다', '분배 하한을 실험으로 정함 (추정)'],
        ['느린 드리프트', '창 가열, 벽 증착으로 h와 코일 저항이 변한다', '바깥 루프의 적분 동작']]
table(s, 0.5, 1.42, [1.7, 4.0, 3.3], rows, size=12, row_h=0.6, first_col_bold=True, row_heights=[0.38] + [0.7] * 6)
note(s, 'H 모드 유지에는 최소 코일 전류가 있다. 레시피 단계가 수 초 이하이거나 펄스 운전이면 피드포워드 표 정확도가 성능을 정한다')
notes(s, '레시피 단계가 수십 초 이상이면 느린 바깥 루프로 손해가 없다. 단계가 수 초 이하이거나 펄스 운전이면 바깥 루프는 따라가지 못하고, 피드포워드 표의 정확도가 성능을 정한다.')

# =================================================================== bk_matching
s = new('bk_matching', '백업 ¤bk_matching¤ · 정합기 상호작용 (식 1)', '바깥 전류를 바꾸면 안쪽 정합이 가장 많이 움직인다', '백업')
tb(s, 0.5, 1.42, 9.0, 0.6, ['전원 1이 보는 임피던스 = 자기 임피던스 + (jωM_{12} + ΔZ_{12})·I_{2}/I_{1}', dict(t='단일 턴, 네 동작점 범위, 플라즈마 상호 리액턴스 X′_{12} 포함 (계산)', size=12, color=C['MUTED'])], size=13)
rows = [['동작점', '안쪽 코일 리액턴스 (ωL_{1} = 32 Ω)', '바깥 코일 리액턴스 (ωL_{2} = 74 Ω)'],
        ['φ = 0°, k ≈ 2', '+4–8 Ω ([[a:+13–24%]]) · 코일 항만 +47–51%', '약 +1 Ω (+1–2%) · 코일 항만 +5%'],
        ['φ = 180°, k ≈ 0.8–1.0', '−2–3 Ω (−7–10%) · 코일 항만 −20–25%', '−2–4 Ω (−3–6%) · 코일 항만 −10–13%']]
table(s, 0.5, 2.05, [2.4, 3.3, 3.3], rows, size=12.5, row_h=0.45, col_align=['l', 'c', 'c'])
cards = [('피드포워드 위치표', '정합기 가변 C의 위치를 k의 함수로 미리 표로 두고 함께 옮긴다. 표는 압력·전력별로 V1에서 계산'),
         ('순차 변경 규칙', '바깥 전류를 먼저 바꾸고 안쪽 정합이 잡힌 뒤 안쪽 전류. k는 10% 단위로 나눠 옮긴다'),
         ('M 상쇄 커패시터', '공통 귀환 가지에 1/(ωC_{d}) = ωM_{12}인 C_{d} ≈ 1.5 nF. 플라즈마를 통한 ΔZ_{12}는 남는다 (추정)')]
x = 0.5
for head, body in cards:
    panel(s, x, 3.6, 2.9, 1.6, head, [body], kind='n', size=13, head_size=13.5)
    x += 3.05
note(s, 'L_{1} ≈ 379 nH, L_{2} ≈ 863 nH, M_{12} ≈ 91 nH (결합 계수 0.16), 단일 턴 (계산). 전원 사양: 반사 전력 내성, 외부 기준 클록 입력')
notes(s, '독립 전원 구조의 대가 중 하나다. 분배를 바꾸면 상대 코일의 전류가 상호 인덕턴스를 통해 입력 임피던스를 바꾼다. 0°에서 R ≈ 1을 만드는 k ≈ 2 동작점에서는 안쪽 코일 리액턴스가 13–24% 늘어난다(플라즈마 상호 리액턴스 포함. 코일 항만이면 +47–51%이고 플라즈마 쪽이 일부 상쇄한다). 그래서 바깥 전류를 바꿀 때 안쪽 정합이 가장 많이 움직인다. 반대 방향은 작다.\n'
         '대책 세 가지는 V1에서 효과를 계산한 뒤 고른다. 전원은 상대 전원이 밀어 넣는 교환 전력을 과도 상태에서 견뎌야 하므로 반사 전력 내성과 외부 기준 클록 입력이 사양에 들어간다.')

# =================================================================== bk_qmap
s = new('bk_qmap', '백업 ¤bk_qmap¤ · 질문 대응표', '질문·검토 사항·제출물이 답해지는 곳', '백업')
q = [['팀 질문', '쪽'],
     ['1-1 – 1-4 챔버 모델 (2D, 0D, 영역 분할)', '§chain§–§f7§'],
     ['1-5 안테나 수·배치, 챔버 크기', '§f6§'],
     ['1-6 밀도 측정', '§diag§, §measure§'],
     ['1-7 반응 테이블', '§bk_reactions§'],
     ['2-1 단일 vs 다중 코일, 전원 수', '§knobs§, §lc§, §arch§'],
     ['2-2 코일 2개의 이점, 180° 위상', '§p_phase§, §p_phase_cmp§'],
     ['2-3 턴 수와 간격', '§f6§'],
     ['2-4 독립 전원 vs 가변 C, 보조 수단', '§lc§, §field§, §bk_drive§'],
     ['2-5 세부 구조, 위상 여유', '§p_phase§, §control§'],
     ['3-1 – 3-3 보조 루프, 최종 구조', '§field§, §direction§, §arch§'],
     ['4-1 / 4-2 / 4-3 상황, 과도', '§target§ / §control§ / §bk_transient§']]
t = [['과제 항목', '쪽'],
     ['검토 1 수단 조합과 영향 영역', '§knobs§–§field§'],
     ['검토 2 상호 영향의 원인', '§chain§–§f7§'],
     ['검토 3 조작 순서와 보상', '§f7§, §procedure§'],
     ['검토 4 비율 확인, 전체/분포 구분', '§diag§, §measure§'],
     ['제출물 ① 소스·구동부 구성도', '§direction§, §arch§'],
     ['제출물 ② 조작 변수 → 밀도 응답', '§f7§'],
     ['제출물 ③ 목표 비율 조정 절차', '§procedure§'],
     ['제출물 ④ 측정 계획', '§measure§, §plan§'],
     ['공통: 가정·대안·부작용·검증', '§simple§, §plan§, §verify§, §stages§']]
q = [[R(c) for c in r] for r in q]; t = [[R(c) for c in r] for r in t]
table(s, 0.5, 1.42, [3.3, 1.15], q, size=12, row_h=0.4, col_align=['l', 'c'])
table(s, 5.0, 1.42, [3.25, 1.25], t, size=12, row_h=0.4, col_align=['l', 'c'])
note(s, '팀 질문 번호는 「프로젝트에 대한 생각」, 과제 항목은 IC-PBL 주제안 3번')
notes(s, '질의응답 때 질문 번호로 바로 해당 슬라이드를 찾아갈 수 있게 만든 표다.')
# =================================================================== finish
assert [k for k in ORDER] == list(built.keys()), (list(built.keys()))
cp = prs.core_properties
cp.title = '중앙·가장자리 밀도비의 독립 제어 — 1차 발표 (이론 학습)'
cp.author = '주제 3 팀'; cp.last_modified_by = '주제 3 팀'; cp.subject = '플라즈마 전자공학 IC-PBL 주제 3'
cp.keywords = ''; cp.comments = ''; cp.category = ''
cp.revision = 1
import datetime
cp.created = datetime.datetime(2026, 11, 5, 12, 0, 0); cp.modified = datetime.datetime(2026, 11, 6, 12, 0, 0)
prs.save(OUT + '.tmp.pptx')

APP = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
       '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
       'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
       '<TotalTime>0</TotalTime><Words>0</Words><Application>Microsoft Office PowerPoint</Application>'
       '<PresentationFormat>화면 슬라이드 쇼(4:3)</PresentationFormat><Paragraphs>0</Paragraphs>'
       f'<Slides>{len(ORDER)}</Slides><Notes>{len(ORDER)}</Notes><HiddenSlides>0</HiddenSlides><MMClips>0</MMClips>'
       '<ScaleCrop>false</ScaleCrop><LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc>'
       '<HyperlinksChanged>false</HyperlinksChanged><AppVersion>16.0000</AppVersion></Properties>')
with zipfile.ZipFile(OUT + '.tmp.pptx') as zin, zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == 'docProps/app.xml':
            data = APP.encode('utf-8')
        zout.writestr(item, data)
os.remove(OUT + '.tmp.pptx')
print('saved', OUT, len(ORDER), 'slides')
