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

# =================================================================== 1 cover
s = prs.slides.add_slide(LAY_TITLE)
built['cover'] = s
ph = {p.placeholder_format.idx: p for p in s.placeholders}
tf = ph[0].text_frame
for i, line in enumerate(['중앙·가장자리 밀도비의', '독립 제어']):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    r = p.add_run(); r.text = line; r.font.size = Pt(36)
tf2 = ph[1].text_frame
write(tf2, [dict(t='플라즈마 전자공학 IC-PBL · 주제 3 · 1차 발표', size=18, bold=True, color=C['INDIGO'], after=10),
            dict(t='기존 연구 분석, 물리 근거, 설계 방향과 검증 계획', size=16, color=C['TEXT'], after=14),
            dict(t='주제 3 팀 · 2026. 11.', size=14, color=C['MUTED'])], align='c')
notes(s, '인사 후 발표 범위를 한 줄로 말한다. 오늘은 시뮬레이션 검증 전 단계로, 기존 연구에서 무엇을 배웠는지, 그 위에 어떤 물리 근거로 설계 방향을 정했는지, 그리고 그것을 어떻게 검증할지를 다룬다.\n'
         '수치 옆의 (문헌)·(계산)·(추정)·(가정) 표시는 값의 출처를 구분한 것이라고 미리 알려 둔다. 다음 장에서 결론부터 보여 주고, 나머지는 그 결론의 근거 순서로 간다.')

# =================================================================== 2 summary
s = new('summary', '개요', '결론 먼저: 세 질문에 대한 답', '개요')
rows = [
    ('기준', '독립 제어의 판정', '응답 행렬 J로 판정한다', '조작 2개(총 전력, 분배) → 출력 2개(평균 밀도 n̄, 밀도비 R). 한 조작이 다른 출력을 10% 넘게 움직이지 않으면 구조적 독립', '§criteria§쪽'),
    ('Q1', '어느 압력에서?', '20–30 mTorr (15 mTorr는 경계)', '가열된 전자가 에너지를 잃는 거리가 코일 간격 7.5 cm보다 짧아야 분배가 밀도비를 움직인다', '§scales§–§predict§쪽'),
    ('Q2', '어떤 구동으로?', '독립 RF 전원 2대 + 위상 0° 고정', '분배를 공진점이 아니라 설정값으로 정하므로 밀도가 바뀌어도 분배가 거의 그대로다 (변화 ≤ 10%)', '§triangle§–§arch§쪽\n제출물 ① ②'),
    ('Q3', '어떻게 맞추고 확인?', '분배로 R, 총 전력으로 n̄', '웨이퍼형 부유 고조파 탐침(FHP) 배열로 전체 변화와 분포 변화를 갈라 확인한다', '§control§–§measure§쪽\n제출물 ③ ④'),
]
y = 1.42
for tag, q, ans, why, ref in rows:
    h = 1.13
    box(s, 0.5, y, 9.0, h, fill=C['PANEL'], radius=0.08)
    chip(s, 0.5, y, 0.8, h, tag, QCOL[tag], size=16, radius=0.08)
    tb(s, 1.45, y, 1.75, h, [q], size=13.5, bold=True, color=C['DARK'], anchor='m')
    tb(s, 3.2, y + 0.06, 5.0, h - 0.12, [dict(t=R(ans), size=16, bold=True, color=C['INDIGO'], after=3), dict(t=R(why), size=12.5, color=C['DARK'])],
       anchor='m', line=1.0)
    tb(s, 8.25, y, 1.15, h, [R(ref)], size=11, color=C['MUTED'], anchor='m', align='r')
    y += h + 0.14
foot(s, '수치는 2-영역 0D·회로 모델 계산이다. 가설 H1–H7과 판정 기준은 §verify§쪽.', y=6.58)
notes(s, '결론부터 말한다. 독립 제어의 판정 기준은 응답 행렬 J로 정했고, 그 위에서 세 질문에 답한다.\n'
         'Q1 압력: 분배를 바꿔 R을 움직이려면 가열된 전자가 에너지를 잃는 거리 λε가 두 코일 간격보다 짧아야 한다. 그래서 20–30 mTorr를 1차 운전 범위로 제안하고 15 mTorr는 경계로 본다.\n'
         'Q2 구동: 같은 주파수의 독립 전원 두 대로 두 코일을 따로 구동하고 공통 발진기로 위상을 0°에 고정한다. 분배를 공진점이 아니라 설정값으로 정하기 때문에 밀도가 바뀌어도 분배가 거의 그대로다.\n'
         'Q3 조정과 확인: 분배로 R을, 총 전력으로 평균 밀도를 맞추고, 웨이퍼형 부유 고조파 탐침 배열로 전체 변화와 분포 변화를 갈라 본다.\n'
         '이 수치들은 모두 모델 계산이며, 마지막에 가설 H1–H7과 판정 기준으로 정리했다. 이제 이 결론에 이른 순서대로 설명한다.')

# =================================================================== 3 task
s = new('task', '1. 문제 정의 · 과제 3', '목표: 밀도가 아니라 밀도비 R을 맞춘다', 'Ⅰ')
cx, cy = 2.45, 3.7
sc = 0.092  # inch per cm
tb(s, 0.5, 1.38, 3.9, 0.3, ['위에서 본 챔버와 웨이퍼'], size=12.5, bold=True, color=C['INDIGO'], align='c')
circle(s, cx, cy, 2 * 20 * sc, fill='F7F8FA', line=C['NAVY'], lw=1.5)
circle(s, cx, cy, 2 * 15 * sc, fill='E3E8F0', line='9AA3B5', lw=1.0)
box(s, cx - 14 * sc, cy - 14 * sc, 28 * sc, 28 * sc, fill=C['ORANGE'], shape=MSO_SHAPE.DONUT, radius=None,
    adj=[0.5 / 28 * 1.6], name='가장자리 띠')
circle(s, cx, cy, 2 * 2.5 * sc, fill=C['BLUE'])
tb(s, cx + 0.3, cy - 0.14, 1.2, 0.3, ['중앙'], size=13, bold=True, color=C['BLUE'])
tb(s, cx - 0.6, cy - 14 * sc - 0.36, 1.2, 0.3, ['가장자리'], size=13, bold=True, color=C['ORANGE_D'], align='c')
lg_y = 5.72
for i, (col, txt) in enumerate([(C['BLUE'], '중앙: r ≤ 25 mm 평균'), (C['ORANGE'], '가장자리: r = 135–140 mm'),
                                ('9AA3B5', '웨이퍼 300 mm · 측벽 r = 200 mm')]):
    yy = lg_y + i * 0.28
    box(s, 0.75, yy + 0.07, 0.14, 0.14, fill=col, radius=None)
    tb(s, 0.98, yy, 3.4, 0.28, [txt], size=12.5, color=C['TEXT'])
eq(s, 'eq_R', 4.85, 1.38, pt=22)
tb(s, 7.15, 1.45, 2.35, 0.7, ['측정 높이:', '웨이퍼 위 1–2 cm'], size=12.5, color=C['DARK'], anchor='m', space_after=0)
box(s, 4.85, 2.32, 4.65, 1.0, fill=C['INDIGO_L'], line=C['INDIGO'], lw=1.5, radius=0.08, paras=[
    dict(t='목표 (제안, 팀 합의)', bold=True, size=12.5, color=C['INDIGO'], after=3),
    dict(t='R 0.8–1.2를 연속 조정, 그동안 n̄ 변화 ±5% 안', size=14, bold=True, color=C['TEXT'])], margin=0.13, anchor='m')
blocks = [
    ('출력은 두 개', '평균 밀도 n̄와 밀도비 R. R만 보면 전체 밀도가 같이 움직여도 모른다'),
    ('운전 조건', 'Ar, 13.56 MHz, 5–30 mTorr, H 모드'),
    ('분석 상황 (질문 4-1)', '정상 상태에서 R 설정값을 바꾸는 준정적 문제. 과도는 백업 B3'),
]
y = 3.45
for head, body in blocks:
    panel(s, 4.85, y, 4.65, 0.88, head, [body], kind='g', size=13, head_size=12)
    y += 0.98
foot(s, '수치 옆 표시: (문헌) 출처 값 · (계산) 모델·스크립트 값 · (추정) 차수 어림 · (가정) 근거 없이 둔 값', y=6.62)
notes(s, '과제 문장은 “밀도비를 원하는 값으로 조정”이다. 그래서 목표를 밀도를 올리고 내리는 것이 아니라 R = n_center / n_edge를 맞추는 것으로 읽었다.\n'
         '출력은 평균 밀도 n̄와 R 두 개로 잡는다. R만 보면 두 영역이 같이 올라가도 모르기 때문이다.\n'
         '중앙은 반지름 25 mm 안의 평균, 가장자리는 135–140 mm 띠로 정의했고, 측정은 웨이퍼 위 1–2 cm에서 한다. 목표 R 0.8–1.2와 n̄ ±5%는 제안값이라 팀 합의가 필요하다.\n'
         '분석 상황(질문 4-1)은 정상 상태에서 R 설정값을 바꾸는 준정적 문제로 한정했고, 점화·레시피 변경 같은 과도 상황은 백업 B3에 정리했다.')

# =================================================================== 4 criteria
s = new('criteria', '1. 문제 정의 · 판정 기준', '독립성은 응답 행렬 J의 모양으로 판정한다', 'Ⅰ')
eq(s, 'eq_J', 0.55, 1.42, pt=19)
tb(s, 5.75, 1.45, 3.75, 1.05, ['P_{tot}: 총 흡수 전력, x: 중앙 전력 몫 P_{c}/P_{tot}',
                               '로그를 쓰면 원소가 상대 변화의 비 → 압력·전력이 달라도 같은 기준으로 비교'],
   size=12.5, color=C['TEXT'], space_after=4)
cards = [
    ('L0', '동반 변화', '두 영역이 함께 오르내린다', ['판정: J의 두 열이', '거의 평행 (조건수 매우 큼)'], 'L0', C['GRAY'], C['PANEL'], None),
    ('L1', '보상 가능한 독립', '조작은 섞이지만 보상하면 한쪽을 유지', ['판정: J 가역,', '조건수가 측정 오차에 비해 작음'], 'L1', C['NAVY'], C['NAVY_L'], '최소 요구'),
    ('L2', '구조적 독립', '한 조작이 다른 출력을 거의 안 움직임', ['판정: 열마다', '비대각/대각 ≤ 0.1'], 'L2', C['INDIGO'], C['INDIGO_L'], '목표'),
]
x = 0.5
for lv, name, mean, crit, pat, col, light, tag in cards:
    w = 2.88
    box(s, x, 2.75, w, 3.05, fill=light, line=col if tag else None, lw=1.5, radius=0.1)
    if tag:
        chip(s, x + w - 1.05, 2.85, 0.95, 0.3, tag, col, size=11, radius=0.05)
    mx, my, cs = x + w / 2 - 0.42, 2.92, 0.38
    shades = {'L0': [[col, col], ['B8BECB', 'B8BECB']],
              'L1': [[col, '8FA9C9'], ['8FA9C9', col]],
              'L2': [[col, None], [None, col]]}[pat]
    for i in range(2):
        for j in range(2):
            f = shades[i][j]
            box(s, mx + j * (cs + 0.06), my + i * (cs + 0.06), cs, cs, fill=f, line=None if f else 'B8BECB', lw=1, radius=0.04)
    tb(s, x + 0.15, 3.85, w - 0.3, 0.4, [f'{lv} {name}'], size=16, bold=True, color=col if lv != 'L0' else C['DARK'], align='c')
    tb(s, x + 0.18, 4.32, w - 0.36, 0.7, [mean], size=13.5, align='c')
    box(s, x + 0.15, 5.03, w - 0.3, 0.62, fill='FFFFFF', radius=0.06, paras=[dict(t=c_, after=0) for c_ in crit], size=12.5, anchor='m', align='c', margin=0.06)
    x += w + 0.18
take(s, 0.5, 5.98, 9.0, 0.52, '기준 0.1은 측정 불확도(1–3%)보다 충분히 큰 값으로 골랐다 (제안)', kind='i', size=13.5)
notes(s, '독립성을 말로만 하지 않기 위해 응답 행렬 J로 정의했다. 조작은 총 흡수 전력과 중앙 전력 몫 x, 출력은 ln n̄와 ln R이다. 로그를 쓰면 J의 원소가 상대 변화의 비가 되어 압력과 전력이 달라도 같은 기준으로 비교할 수 있다.\n'
         '독립성은 세 수준으로 나눴다. L0은 두 열이 거의 평행해서 어떤 조합으로도 한쪽만 움직일 수 없는 상태, L1은 섞이지만 역행렬로 보상하면 한쪽을 유지할 수 있는 상태, L2는 한 조작이 다른 출력을 거의 건드리지 않는 상태다.\n'
         '과제는 최소 L1, 가능하면 L2를 요구한다고 해석했다. L2 기준 0.1과 목표 R 0.8–1.2, n̄ ±5%는 제안값이며, 측정 불확도(약 1–3%)보다 충분히 커야 의미가 있다는 점을 근거로 들었다.')

# =================================================================== 5 chain
s = new('chain', '1. 문제 정의 · 검토 사항 2 (상호 영향의 원인)', '한 영역의 조작은 다섯 단계 어디서든 샌다', 'Ⅰ')
stages = [('① 회로', '코일 전류, 정합', ['C1 공통 전원', 'C2 상호 인덕턴스', 'C3 플라즈마가 공통 2차측'], 'n'),
          ('② 장', '유도 전기장, 표피층', ['C4 두 코일 장의 중첩', 'C5 창을 통한 축전 결합'], 'n'),
          ('③ 전자 가열', '에너지 완화 길이 λ_{ε}', ['C6 비국소 가열: 다른 영역에서 이온화'], 'a'),
          ('④ 입자 수송', '양극성 확산, 퍼짐 길이 ℓ', ['C7 영역 간 확산'], 'a'),
          ('⑤ 벽 손실', 'h-factor, 영역 밀도', ['측벽 손실이 가장자리에만 더해짐'], 'g')]
w, gap = 1.56, 0.3
for i, (nm, sub, leaks, k) in enumerate(stages):
    x = 0.5 + i * (w + gap)
    col = {'n': C['NAVY'], 'a': C['AMBER'], 'g': C['GRAY']}[k]
    box(s, x, 1.45, w, 1.25, fill='FFFFFF', line=col, lw=2, radius=0.08,
        paras=[dict(t=nm, bold=True, size=15, color=col if k != 'g' else C['DARK'], align='c', after=4),
               dict(t=sub, size=12.5, align='c')], anchor='m', margin=0.06)
    if i < 4:
        seg(s, x + w + 0.03, 2.075, x + w + gap - 0.03, 2.075, color=C['NAVY'], w=2, head=True)
    tb(s, x + 0.02, 2.85, w - 0.02, 1.5, [dict(t=l, size=13, after=5) for l in leaks], size=13, color=C['TEXT'],
       bullet=True, bullet_color=col)
groups = [(0, 1, 'n', 'C1–C5: 구동부 설계로 줄인다', '전원 구성, 위상, 코일 배치 → 4. 구동 구조 (§triangle§–§arch§쪽)'),
          (2, 3, 'a', 'C6·C7: 압력과 간격 L이 정한다', '어떤 구동을 골라도 남는다 → 3. 압력 범위 (§scales§–§predict§쪽)'),
          (4, 4, 'g', '손실 비대칭', '총 전력으로 보상 → §procedure§쪽')]
for a, b, k, head, body in groups:
    x0 = 0.5 + a * (w + gap); x1 = 0.5 + b * (w + gap) + w
    panel(s, x0, 4.4, x1 - x0, 1.1, head, [body], kind=k, size=12.5, head_size=13.5)
take(s, 0.5, 5.7, 9.0, 0.62, '구동 방식은 C1–C5를 얼마나 줄이는가로, 운전 압력은 C6·C7의 크기로 고른다', kind='i', size=14)
foot(s, 'C8 비선형·이력(E–H 전이 등)은 전 단계에 걸친다. C1–C8은 팀 저장소 배경 이론 문서의 번호. 교재 2.3.4절(식 2.52–2.57), 1.10절, 2.4절', y=6.45)
notes(s, '검토 사항 2(상호 영향의 원인)에 대한 답의 뼈대다. 코일 전류에서 영역 밀도까지 다섯 단계를 거치고, 단계마다 한 영역의 조작이 다른 영역으로 새는 경로가 있다.\n'
         '파란 테두리(회로·장)는 구동부 설계로 줄일 수 있는 결합이고, 주황 테두리(가열·확산)는 압력과 창–웨이퍼 간격으로 정해지는 결합이다. 회색(벽 손실)은 가장자리에만 측벽 손실이 더해지는 비대칭이다.\n'
         '이 구분이 발표의 순서를 정한다. 주황(C6·C7)은 3장에서 운전 압력 범위로, 파랑(C1–C5)은 4장에서 구동 방식 선택으로, 회색은 5장의 조정 절차에서 총 전력 보상으로 다룬다.\n'
         '수동 공진 구조에서는 플라즈마 부하가 바뀌면 공진점이 움직여 전류 분배가 바뀌는데, 이것이 C1·C3의 대표 예다.')

# =================================================================== 6 literature map
s = new('litmap', '2. 기존 연구 · 검토 사항 1 (수단과 영향 영역)', '기존 연구는 균일도만 맞췄다: 밀도비 설정은 빈 곳', 'Ⅱ')
rows = [['후보', '수단 [근거]', '주로 바꾸는 곳', '알려진 한계'],
        ['', '이중 코일 + 단일 전원 [P1][P2]', '각 코일 아래', '두 코일 전류 조정이 독립적이지 않다 (P1 원문)'],
        ['A', 'LC 공진 코일 [KC20][J1]', '공진 코일 쪽', '공진점이 부하에 따라 이동, 공진 근처 급경사'],
        ['B', '독립 전원 + 위상 고정 [P3]', '코일 아래와 사이', '상호 인덕턴스로 전원 간 간섭, 위상별 효과 미공개'],
        ['', '이중 주파수·이종 소스 [J2][C3]', '각 소스 아래', '장 간섭은 없지만 전원 2대·필터 필요'],
        ['', '페라이트 [교재 식 2.62][C3]', '페라이트 주변', '13.56 MHz에서 손실·발열, 점화 어려움'],
        ['C', '정자기장 [P4][C5][C6]', '반경 방향 수송', '이온 선속·에너지 분포도 함께 바뀜']]
fills = {(2, 0): C['NAVY_L'], (3, 0): C['NAVY_L'], (6, 0): C['NAVY_L']}
table(s, 0.5, 1.42, [0.6, 2.75, 1.6, 4.05], rows, size=12.5, row_h=0.47, col_align=['c', 'l', 'l', 'l'],
      fills=fills, colors={(2, 0): C['NAVY'], (3, 0): C['NAVY'], (6, 0): C['NAVY']}, bold_cells={(2, 0), (3, 0), (6, 0)})
panel(s, 0.5, 5.0, 4.4, 1.0, '공통점', ['대부분 코일 전류비와 위상을 조작하고, 목표는 균일도 최적화다'], kind='g', size=13)
panel(s, 5.1, 5.0, 4.4, 1.0, '빈 곳', ['밀도비를 임의 값으로 설정하고 독립성을 정량화한 연구는 찾지 못했다'], kind='a', size=13)
foot(s, '후보 열: 뒤에서 비교하는 A 수동 공진, B 독립 전원, C 자기장 보조. [P] 특허·[KC20] 학술지는 본문 확인, [J][C]는 초록만 확인 → 사례 소개로만', y=6.12, h=0.45)
notes(s, '검토 사항 1(어떤 수단을 조합하고, 각 수단이 주로 어디에 영향을 주는가)의 근거 자료다. 산업에서 쓰는 방식은 대부분 코일 전류비와 위상을 조작한다.\n'
         '전원 하나와 수동 소자를 쓰는 방식(P1, P2, KC20)은 싸고 단순하지만 회로 결합이 본질적으로 남는다. Lam의 P1 특허 원문도 두 코일 전류 조정이 독립적이지 않다고 적고 있다. 전원 둘에 위상을 고정하는 방식(P3)은 자유도가 많지만, 어느 위상에서 중앙과 가장자리가 어떻게 바뀌는지는 특허에 없다. 자기장은 가열 위치가 아니라 수송을 바꾸는 성격이 다른 손잡이다.\n'
         '왼쪽 후보 열의 A, B, C는 4장에서 비교하는 세 후보와 같은 것이다.\n'
         '기존 연구의 목표는 거의 모두 균일도다. 이 과제는 밀도비를 원하는 값으로 맞추고 독립성을 보여야 하므로, 독립성 지표와 평균 밀도 유지 조건은 우리가 정의해야 했다.\n'
         '확인 수준: 특허와 KC20·Park 2017은 본문을 읽었고, J1·J2와 GEC 학회 자료는 초록만 확인했다. 초록 자료는 주장의 근거로 쓰지 않는다.')

# =================================================================== 7 KC20
s = new('kc20', '2. 기존 연구 · Kim & Chung, Phys. Plasmas 27, 063511 (2020)', 'KC20: 고압에서는 공진 코일이 분포를 뒤집는다', 'Ⅱ')
cx_, cy_, cw_, ch_ = 0.5, 1.35, 5.3, 3.5
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
xa = px0 + pw * (2.5 / 4) + 0.21
seg(s, xa, 2.02, xa, py0 + ph * (3.5 - 0.62) / 3.5, color=C['ORANGE_D'], w=2.25, head=True)
tb(s, xa - 1.85, 1.84, 1.8, 0.28, ['공진 → 분포 반전'], size=12, bold=True, color=C['ORANGE_D'], align='r')
tb(s, 0.62, 4.85, 5.1, 0.28, ['옅은 보라 띠: 이 과제의 목표 R 0.8–1.2'], size=11.5, color=C['MUTED'])
panel(s, 6.0, 1.42, 3.5, 3.7, '실험 구성', [
    dict(t='챔버 r 19 cm, 높이 10 cm', bullet=True),
    dict(t='급전 코일 r 9.5 cm + 수동 공진 코일 r 17.5 cm (가변 C, 공진 139 pF)', bullet=True),
    dict(t='λ_{ε}: 1 mTorr 119 cm, 50 mTorr 2.3 cm (계산)', bullet=True)], kind='g', size=13.5, after=8)
cards = [('저압 (1 mTorr)', 'λ_{ε}가 챔버보다 길다 → 가열 위치를 옮겨도 R이 조금만 변한다', 'g'),
         ('고압 (50 mTorr)', '공진만으로 R < 1 → “A는 R = 1에 못 닿는다”던 초기 판단을 철회', 'g'),
         ('남은 빈 곳', '두 끝 상태만 있다. 중간값을 연속으로, 밀도와 무관하게 맞출 수 있는지는 미확인', 'a')]
x = 0.5
for head, body, k in cards:
    panel(s, x, 5.25, 2.9, 1.3, head, [body], kind=k, size=12.5, head_size=13)
    x += 3.05
foot(s, 'R: 탐침 반경 분포를 경계 13.5 cm로 면적 평균 (팀 디지타이즈, Fig. 3, 8). 웨이퍼 FHP 지도로도 공진 때 R ≈ 0.4 (150 W), 0.7 (50 W) (Fig. 4, 9)', y=6.6)
notes(s, '제공받은 첫 번째 논문이다. 안쪽 코일은 전원으로 급전하고, 바깥 코일은 전원 없이 가변 커패시터로 닫아 공진시키는 구조다. 공진에 가까워지면 바깥 코일 전류가 커지고, 같은 전력에서 급전 전류가 줄어 중앙 가열도 줄어든다.\n'
         '핵심 결과는 압력에 따라 반응이 완전히 다르다는 것이다. 1 mTorr에서는 λε가 119 cm로 챔버보다 길어, 가열 위치를 바꿔도 R이 1.81에서 1.22로 조금만 변한다. 50 mTorr에서는 λε가 2.3 cm로 짧아 공진 코일 아래에서 국소적으로 이온화가 일어나고, 밀도 봉우리가 반지름 15 cm 쪽으로 옮겨 가 R이 0.39까지 내려간다. 웨이퍼 FHP 지도에서도 같은 경향이 보인다.\n'
         '배운 것 세 가지. 첫째, 분포를 움직일 수 있는지는 구동 방식보다 압력(λε)이 먼저 정한다. 둘째, 수동 공진도 고압에서는 R < 1을 만들 수 있다. 우리 초기 모델은 이것을 재현하지 못했고, 그래서 “수동 공진은 R = 1에 못 닿는다”던 초기 판단을 고쳤다. 셋째, 논문은 비공진과 공진 두 끝 상태만 보여 준다. 중간값을 연속으로, 밀도가 바뀌어도 흔들리지 않게 맞출 수 있는지는 답하지 않는다. 이것이 우리 과제가 채워야 할 부분이다.')

# =================================================================== 8 Park 2017
s = new('park', '2. 기존 연구 · Park et al., Phys. Plasmas 24, 123506 (2017)', 'Park 2017: H 모드에서는 h-factor 이론이 맞는다', 'Ⅱ')
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
tb(s, 7.25, 2.645, 1.5, 0.26, ['전력 ↑'], size=11, color=C['MUTED'], anchor='m')
tb(s, 0.5, 4.0, 9.0, 0.3, ['우리 설계에 가져온 것'], size=13.5, bold=True, color=C['INDIGO'])
cards = [('모델', 'H 모드에서는 영역마다 h-factor로 벽 손실을 쓰는 2-영역 모델이 정당화된다'),
         ('운전', '점화 후 H 모드를 확인하고 나서 바깥 루프를 닫는다'),
         ('측정', '같은 부유 고조파 탐침을 웨이퍼 배열로 써서 밀도비를 잰다')]
x = 0.5
for head, body in cards:
    panel(s, x, 4.38, 2.9, 1.45, head, [body], kind='i', size=13.5, head_size=14)
    x += 3.05
foot(s, '같은 논문의 λ_{ε} 39 / 12 / 4.7 / 2.4 cm (3 / 10 / 25 / 50 mTorr)는 계산값 → λ_{ε} 식의 독립 검증으로 쓰지 않는다. 3, 10 mTorr의 절대값 차이는 탐침 위치 탓', y=6.05, h=0.45)
notes(s, '제공받은 두 번째 논문이다. ICP에서 전력을 올려 E 모드에서 H 모드로 넘어갈 때 가장자리/중앙 밀도비가 어떻게 바뀌는지를 부유 고조파 탐침으로 재고, h-factor 이론과 비교했다.\n'
         '결론은 모드에 따라 갈린다. H 모드에서는 고압(25–100 mTorr)까지 포함해 이론 h-factor 비가 측정과 맞는다. E 모드에서는 분포가 축전 결합을 따라가서 이론이 크게 어긋난다. 저압 3, 10 mTorr에서 보이는 절대값 차이는 탐침 위치 때문이라고 설명한다.\n'
         '우리 설계에 가져온 것은 세 가지다. H 모드라면 영역마다 h-factor로 벽 손실을 쓰는 2-영역 모델이 정당화된다. 운전에서는 점화 후 H 모드를 확인한 다음에야 바깥 루프를 닫는다. 측정에서는 같은 부유 고조파 탐침을 웨이퍼 배열로 써서 밀도비를 잰다.\n'
         '주의: 이 논문의 압력별 λε 값은 계산값이라, 우리 λε 식과 맞는다는 것을 독립 검증이라고 말하지 않는다.')

# =================================================================== 9 questions
s = new('questions', '2. 기존 연구 · 정리', '기존 연구가 남긴 질문 세 가지', 'Ⅱ')
qs = [('Q1', '어느 압력에서 가능한가', 'KC20: 같은 구조가 1 mTorr와 50 mTorr에서 전혀 다르게 반응 (결합 C6·C7)', '3. 압력 범위 (§scales§–§predict§쪽)', 'λ_{ε}와 코일 간격으로 경계를 정한다'),
      ('Q2', '어떤 구동이 R만 움직이나', 'P1 “독립적이지 않다”, KC20 공진점 이동, P3 위상 효과 미공개 (결합 C1–C5)', '4. 구동 구조 (§triangle§–§arch§쪽)', '회로 누설로 후보를 비교하고 위상을 정한다'),
      ('Q3', '어떻게 맞추고 확인하나', 'KC20은 두 끝 상태뿐, 기존 연구는 균일도만 측정', '5. 조정과 측정 (§control§–§measure§쪽)', '연속 조정 절차와 측정 판정 기준을 만든다')]
y = 1.45
for tag, q, ev, sec, how in qs:
    h = 1.42
    circle(s, 0.98, y + h / 2, 0.92, fill=QCOL[tag], paras=[tag], size=18, color='FFFFFF')
    tb(s, 1.65, y + 0.1, 4.1, 0.45, [q], size=17, bold=True, color=C['INDIGO'])
    tb(s, 1.65, y + 0.58, 4.1, 0.8, ['근거: ' + ev], size=13, color=C['DARK'])
    seg(s, 5.85, y + h / 2, 6.3, y + h / 2, color=C['INDIGO'], w=2.5, head=True)
    box(s, 6.4, y + 0.1, 3.1, h - 0.2, fill=QLIGHT[tag], radius=0.08,
        paras=[dict(t=R(sec), bold=True, size=13.5, color=C['INDIGO'], after=4), dict(t=how, size=13)],
        margin=0.14, anchor='m')
    y += h + 0.14
take(s, 0.5, 6.05, 9.0, 0.45, '이어서 6. 검증과 한계(§verify§–§decisions§쪽)에서 가설과 판정 기준을 정리한다. 판정 기준 J는 §criteria§쪽', kind='g', size=12.5, lead=None)
notes(s, '기존 연구 분석을 세 질문으로 정리한다. 이것이 나머지 발표의 순서다.\n'
         '첫째, 같은 장치라도 압력에 따라 반응이 전혀 다르므로 “어느 압력에서 독립 제어가 가능한가”를 먼저 정해야 한다. 3장에서 λε와 코일 간격으로 경계를 정한다.\n'
         '둘째, 어떤 구동이 R만 움직이는가. 특허 P1은 두 코일 전류가 독립적이지 않다고만 적고, KC20의 공진점은 부하에 따라 움직이며, P3은 위상 효과를 공개하지 않았다. 4장에서 회로 누설로 후보를 비교한다.\n'
         '셋째, KC20은 비공진과 공진 두 상태만 보여 주고 기존 연구는 균일도만 쟀으므로, 원하는 밀도비로 연속 조정하는 절차와 그것을 확인하는 측정 기준을 5장에서 만든다.')

# =================================================================== 10 scales
s = new('scales', '3. 압력 범위 · Q1 어느 압력에서 가능한가', '분배가 R을 움직이는 힘은 λ_{ε}가 정한다', 'Ⅲ')
cd = XyChartData()
s1 = cd.add_series('g_R')
for k in range(2, 61):
    p_ = k / 2
    s1.add_data_point(p_, 1 - math.exp(-7.5 * p_ / 119))
s2 = cd.add_series('표시점')
pts = [1, 5, 10, 20, 30]
for p_ in pts:
    s2.add_data_point(p_, 1 - math.exp(-7.5 * p_ / 119))
s3 = cd.add_series('p*')
s3.add_data_point(15.87, 0.0); s3.add_data_point(15.87, 1 - math.exp(-1))
gf = s.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_SMOOTH_NO_MARKERS, I(0.5), I(1.38), I(5.2), I(3.95), cd)
gf.name = 'g_R 압력 그래프'
ch = gf.chart; style_chart(ch, size=12); ch.has_legend = False
ser = ch.plots[0].series
ser[0].format.line.color.rgb = rgb(C['INDIGO']); ser[0].format.line.width = Pt(2.75); ser[0].smooth = True
sr = ser[1]; sr.smooth = False; sr.format.line.fill.background()
sr.marker.style = XL_MARKER_STYLE.CIRCLE; sr.marker.size = 9
sr.marker.format.fill.solid(); sr.marker.format.fill.fore_color.rgb = rgb(C['INDIGO'])
sr.marker.format.line.color.rgb = rgb('FFFFFF')
sr = ser[2]; sr.smooth = False
sr.format.line.color.rgb = rgb(C['AMBER']); sr.format.line.width = Pt(1.75); sr.format.line.dash_style = MSO_LINE.DASH
sr.marker.style = XL_MARKER_STYLE.NONE
label_point(sr.points[1], 'p* ≈ 16 mTorr (λ_{ε} = Δ)', XL_LABEL_POSITION.LEFT, size=12, color=C['AMBER'], bold=True)
style_axis(ch.category_axis, 0, 30, 5, '0', grid=False, size=12)
style_axis(ch.value_axis, 0, 1.0, 0.2, '0.0', grid=True, size=12)
axis_title(ch.category_axis, '압력 p (mTorr)', size=12); axis_title(ch.value_axis, 'g_{R}', size=12)
eq(s, 'eq_lambda', 5.95, 1.42, pt=17)
eq(s, 'eq_gR', 5.95, 2.2, pt=17)
tb(s, 5.95, 2.75, 3.55, 1.0, ['g_{R}: 분배를 바꿨을 때 R이 움직이는 힘 (완전 국소 가열 = 1)',
                              'Δ = 7.5 cm: 두 코일 간격 (§geometry§쪽)'], size=12.5, space_after=4)
table(s, 5.95, 3.75, [1.05, 0.5, 0.5, 0.5, 0.5, 0.5], [
    ['p (mTorr)', '1', '5', '10', '20', '30'],
    ['λ_{ε} (cm)', '119', '24', '12', '6.0', '4.0'],
    ['g_{R}', '0.06', '0.27', '0.47', '0.72', '0.85']], size=12, row_h=0.34, col_align=['l', 'c', 'c', 'c', 'c', 'c'],
    bold_cells={(2, j) for j in range(6)}, colors={(2, j): C['INDIGO'] for j in range(6)})
tb(s, 5.95, 4.88, 3.55, 0.5, ['g_{R} = 0.5인 압력 ≈ 11 mTorr. §predict§쪽 모델 계산에서는 15 mTorr가 경계'], size=12, color=C['DARK'])
take(s, 0.5, 5.5, 9.0, 0.72, '1 mTorr에서는 g_{R} = 0.06: 어떤 구동을 써도 분포가 거의 안 움직인다. 운전 범위는 구동 방식보다 압력이 먼저 정한다', kind='a', size=13.5)
foot(s, 'λ_{ε} 기준값: KC20 Fig. 5 (1 mTorr에서 119 cm). 한 영역 전력 중 다른 영역에서 쓰이는 몫 w = e^{−Δ/λε}는 가정 → 가설 H1로 검증 (계산)', y=6.32)
notes(s, 'λε는 전자가 에너지를 잃기 전에 움직이는 거리다. 1/p로 줄어들기 때문에 저압에서는 한 코일 아래에서 가열된 전자가 다른 영역에서 이온화를 일으킨다.\n'
         '한 영역에 넣은 전력 중 다른 영역에서 쓰이는 몫을 w = e^(−Δ/λε)로 두면, 분배를 바꿨을 때 R이 움직이는 힘은 g_R = 1 − w다. w의 형태는 가정이고, 가설 H1이 곧 이 가정의 검증이다.\n'
         '그래프에서 1 mTorr의 g_R은 0.06이라 분배를 바꿔도 R이 거의 안 변한다. 이것은 구동 방식과 무관한 물리적 한계다. λε가 코일 간격 7.5 cm와 같아지는 압력이 약 16 mTorr이고, g_R = 0.5인 압력은 약 11 mTorr다. KC20이 1 mTorr와 50 mTorr에서 전혀 다르게 반응한 이유가 이 곡선이다.\n'
         '주의: Park 2017의 압력별 λε(3, 10, 25, 50 mTorr에서 39, 12, 4.7, 2.4 cm)가 1/p와 맞는 것은 같은 계산식에서 나온 값이기 때문이라, 독립적인 실험 검증으로 말하지 않는다.')

# =================================================================== 11 geometry
s = new('geometry', '3. 압력 범위 · 형상 (질문 1-5, 2-3)', '형상: 코일 간격 7.5 cm, 창–웨이퍼 간격 10 cm', 'Ⅲ')
ax_x, k = 5.15, 0.165  # axis x, inch per cm
wy = 2.0  # window bottom
L_in = 10 * k
wf_y = wy + L_in
box(s, ax_x - 12 * k, wy, 24 * k, L_in, fill=C['BLUE_L'], radius=None, name='중앙 영역')
box(s, ax_x - 20 * k, wy, 8 * k, L_in, fill=C['ORANGE_L'], radius=None, name='가장자리 영역 왼쪽')
box(s, ax_x + 12 * k, wy, 8 * k, L_in, fill=C['ORANGE_L'], radius=None, name='가장자리 영역 오른쪽')
box(s, ax_x - 20 * k - 0.06, wy - 0.12, 40 * k + 0.12, 0.12, fill='C7D3E6', line='9AA3B5', lw=0.75, radius=None, name='유전체 창')
box(s, ax_x - 20 * k - 0.06, wy - 0.12, 0.06, L_in + 0.2, fill=C['NAVY'], radius=None, name='측벽 왼쪽')
box(s, ax_x + 20 * k, wy - 0.12, 0.06, L_in + 0.2, fill=C['NAVY'], radius=None, name='측벽 오른쪽')
box(s, ax_x - 15 * k, wf_y, 30 * k, 0.07, fill='5F6779', radius=None, name='웨이퍼')
box(s, ax_x - 20 * k - 0.06, wf_y + 0.08, 40 * k + 0.12, 0.06, fill=C['NAVY'], radius=None, name='바닥')
for sx in (-1, 1):
    seg(s, ax_x + sx * 12 * k, wy, ax_x + sx * 12 * k, wf_y, color=C['MUTED'], w=1, dash=True)
    for r_ in (7.6, 8.4):
        circle(s, ax_x + sx * r_ * k, wy - 0.24, 0.15, fill=C['BLUE'])
    circle(s, ax_x + sx * 15.5 * k, wy - 0.24, 0.15, fill=C['ORANGE'])
seg(s, ax_x, wy - 0.4, ax_x, wf_y + 0.2, color=C['MUTED'], w=1, dash=True)
tb(s, ax_x - 0.8, wf_y + 0.18, 1.6, 0.28, ['축 (E_{θ} = 0)'], size=12, color=C['DARK'], align='c')
# 코일 라벨: 왼쪽 코일 바로 위
tb(s, ax_x - 8 * k - 0.95, wy - 0.68, 1.9, 0.28, ['[[b:안쪽 코일]] r ≈ 8 cm, 2턴'], size=12, align='c')
tb(s, 0.3, wy - 0.74, 1.38, 0.75, ['[[o:바깥 코일]]', 'r ≈ 15.5 cm', '1–2턴'], size=12, space_after=0, align='r')
seg(s, 1.72, wy - 0.24, ax_x - 15.5 * k - 0.1, wy - 0.24, color=C['ORANGE'], w=1)
# Δ dimension (right side, above coils)
yd = wy - 0.55
seg(s, ax_x + 8 * k, yd, ax_x + 15.5 * k, yd, color=C['TEXT'], w=1.25, head=True, tail=True)
tb(s, ax_x + 8 * k - 0.2, yd - 0.31, 7.5 * k + 0.4, 0.28, ['Δ = 7.5 cm'], size=13, bold=True, color=C['INDIGO'], align='c')
xl = ax_x + 18.6 * k
seg(s, xl, wy + 0.02, xl, wf_y - 0.02, color=C['TEXT'], w=1.25, head=True, tail=True)
tb(s, xl - 1.25, wy + 1.0, 1.18, 0.28, ['L = 10 cm'], size=12.5, bold=True, color=C['TEXT'], align='r')
tb(s, ax_x - 12 * k + 0.06, wy + 0.06, 1.3, 0.28, ['경계 12 cm'], size=12, color=C['DARK'])
tb(s, ax_x - 1.75, wy + 0.62, 1.6, 0.3, ['중앙 영역'], size=13, bold=True, color=C['BLUE'], align='r')
tb(s, ax_x + 12.5 * k, wy + 0.5, 0.95, 0.3, ['가장자리'], size=13, bold=True, color=C['ORANGE_D'])
tb(s, ax_x - 1.8, wf_y + 0.42, 3.6, 0.28, ['웨이퍼 300 mm · 측벽 r = 20 cm'], size=12, color=C['DARK'], align='c')
rows = [['항목', '값', '이유'],
        ['창–웨이퍼 간격 L', '10 cm', '확산 누설 e^{−πΔ/L} ≈ 0.10 (퍼짐 길이 ℓ = L/π ≈ 3.2 cm)'],
        ['안쪽 코일', 'r ≈ 8 cm, 2턴', '축 위 E_{θ} = 0 → 축에 붙이면 가열이 약해 도넛 가열'],
        ['바깥 코일', 'r ≈ 15.5 cm, 1–2턴', '웨이퍼 끝 위, 측벽과 4.5 cm (KC20은 1.5 cm)'],
        ['경계 / 챔버 반지름', '12 cm / 20 cm', '두 코일의 중간 / 에지 링·배기 간극 5 cm']]
table(s, 0.5, 4.42, [1.85, 1.75, 5.4], rows, size=12.5, row_h=0.39, first_col_bold=True)
foot(s, '턴은 자기 영역의 좁은 띠에 모은다. 턴 수 N: 같은 전력의 전류 ∝ 1/N, 코일 전압 ∝ N. 대칭 급전은 설계 요구 조건 (2D 축대칭 가정의 전제)', y=6.42, h=0.45)
notes(s, '형상은 하나의 길이, 코일 간격 Δ = 7.5 cm로 설명한다. Δ는 확산 퍼짐 길이 ℓ = L/π ≈ 3.2 cm의 약 2.4배라 이온화가 국소적이면 확산만으로는 크게 섞이지 않고, λε가 Δ와 같아지는 압력(약 16 mTorr)이 분포 제어가 본격적으로 되는 압력의 1차 추정이 된다.\n'
         'Δ를 더 키우면 p*는 내려가지만, 안쪽 코일을 축에 붙이면 축 위에서 유도 전기장이 0이라 가열이 약해지고 바깥 코일은 측벽에 막힌다. 반지름 20 cm 챔버에서는 7.5 cm가 실질적인 최대다.\n'
         '창–웨이퍼 간격 L은 확산 누설을 정한다. 축 방향 기본 모드가 cos(πz/L)이면 고리 모양 소스가 반경 방향으로 L/π만큼 퍼지고, 다른 영역으로 새는 몫은 e^(−πΔ/L)이다. L = 10 cm에서 약 0.10으로 L2 기준의 경계다. L을 줄이면 분리는 좋아지지만 영역 안 균일도와 창–웨이퍼 축전 결합이 나빠진다.\n'
         '바깥 코일은 KC20처럼 측벽에서 1.5 cm만 떨어지면 가열된 전자가 이온화 전에 벽으로 빠지므로 4.5 cm를 띄웠다. 턴 수는 N을 늘리면 효율이 오르지만 코일 전압이 N에 비례해 커져 축전 결합이 늘어난다. 안쪽 2턴, 바깥 1–2턴에서 시작하고 V1에서 다중 턴 회로 계산으로 다시 정한다.')

# =================================================================== 12 model
s = new('model', '3. 압력 범위 · 분석 도구: §predict§–§phase_cmp§쪽 수치의 근거 (질문 1-1 – 1-4)', '2-영역 0D + 회로로 좁히고 2D로 확인한다', 'Ⅲ')
rows = [['모델', 'R 계산', '담는 결합 경로', '역할'],
        ['단일 영역 0D [LL95]', '불가', '없음 (h-factor가 압력·치수로만)', 'n̄ 크기의 기준선'],
        ['[[n:2-영역 0D + 회로 (선택)]]', '영역 평균', 'C2 상호 인덕턴스, C3 공통 2차측, C6 비국소 가열(λ_{ε}), C7 확산', '압력별 제어 폭, J, 조작 순서'],
        ['축대칭 2D 유체 + 전자기', 'n(r, z)', '대부분 (비국소 가열은 모델에 따라)', '0D 검증, 측정 위치 R 환산']]
table(s, 0.5, 1.42, [2.4, 1.0, 3.2, 2.4], rows, size=12.5, row_h=0.5, fills={(2, j): C['NAVY_L'] for j in range(4)},
      row_heights=[0.4, 0.5, 0.75, 0.55])
panel(s, 0.5, 3.85, 4.4, 1.5, '맞은 것 (KC20 데이터)', [
    dict(t='보정 파라미터 하나로 비공진 급전 전류가 보정 밖 3점에서 ±9% 안', bullet=True),
    dict(t='압력이 높을수록 R 제어 폭이 커지는 경향', bullet=True)], kind='n', size=13.5, after=5)
panel(s, 5.1, 3.85, 4.4, 1.5, '못 맞춘 것', [
    dict(t='절대 밀도 1.4–18배, 공진 급전 전류 +74–85%', bullet=True),
    dict(t='50 mTorr 공진의 R: 측정 2.54 → 0.39, 모델 5.72 → 5.17', bullet=True)], kind='a', size=13.5, after=5)
take(s, 0.5, 5.5, 9.0, 0.62, '판정은 절대값이 아니라 비(R, g_{R}, 누설)로 한다. R 범위의 절대값은 V1·V2에서 다시 확인', kind='i', size=13.5)
foot(s, 'V1 = 회로 모델 확장(다음 2주), V2 = 축대칭 2D 계산 (§decisions§쪽). 영역 분할 조건: 영역마다 안테나 하나, 벽 손실·확산을 따로, 에너지 수송은 λ_{ε}로. 회로 결합: Dodd–Deeds (1968)', y=6.25, h=0.5)
notes(s, '단일 영역 0D는 h-factor가 압력과 치수로만 정해져 어느 코일에 전력을 넣어도 같은 R이 나온다. 그래서 R을 계산할 수 있는 가장 단순한 모델인 2-영역 0D에 코일 회로를 붙였다. 2D 유체 모델은 맥스웰·국소장 근사를 쓰면 저압의 비국소 가열을 잘못 그리고 동작점당 비용이 커서, 0D로 범위를 좁힌 뒤 2D로 확인하는 순서를 택했다.\n'
         '모델의 한계를 숨기지 않는다. KC20 데이터로 비공진 급전 전류는 ±9% 안으로 맞았지만, 공진 상태의 급전 전류는 74–85% 높게, 절대 밀도는 1.4–18배 높게 나온다. 특히 50 mTorr 공진 조건에서 측정된 R의 변화(2.54에서 0.39로, 가장자리가 더 높아짐)를 모델은 5.72에서 5.17로밖에 그리지 못했다. “압력이 높을수록 제어 폭이 커진다”는 경향만 맞고 크기는 맞지 않는다.\n'
         '또 λε 브리지가 모델 안에 들어 있으므로, 앞의 g_R 식과 모델이 비슷한 값을 내는 것은 독립적인 검증이 아니다. 그래서 다음 쪽의 R 범위 예측은 경향과 비로만 읽는다.')

# =================================================================== 13 predict
s = new('predict', '3. 압력 범위 · Q1의 답', '예측: 20 mTorr 이상은 여유, 15 mTorr는 경계', 'Ⅲ')
data = [(5, 1.07, 1.97, 1.10, 1.11), (10, 0.88, 2.81, 0.92, 0.94), (15, 0.73, 3.68, 0.78, 0.81),
        (20, 0.62, 4.52, 0.68, 0.72), (30, 0.49, 5.97, 0.55, 0.60)]
VMIN, VMAX = 0.4, 1.6
cx_, cy_, cw_, ch_ = 0.5, 1.5, 5.4, 4.75
lay = (0.13, 0.05, 0.84, 0.80)
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
for i in range(5):
    xc = px0 + pw * (i + 0.5) / 5
    tb(s, xc - 0.3, py0 - 0.3, 0.6, 0.28, ['↑'], size=13, bold=True, color=C['NAVY'], align='c')
lx = 6.1
items = [(C['NAVY'], '코일 선택도 한계 안에서 낼 수 있는 R (↑ 위로 계속)'),
         ('C3D0EA', '중앙 몫을 2%까지 줄여야 닿는 부분'),
         (C['TARGET'], '목표 R 0.8–1.2')]
for i, (col, txt) in enumerate(items):
    yy = 1.5 + i * 0.45
    box(s, lx, yy + 0.05, 0.28, 0.28, fill=col, radius=0.03)
    tb(s, lx + 0.38, yy, 3.0, 0.42, [txt], size=12.5, anchor='m')
tb(s, lx, 2.9, 3.4, 0.3, ['막대 아래 숫자 = 낼 수 있는 R의 하한'], size=12, color=C['DARK'])
rows = [['압력', '판정'],
        ['5, 10 mTorr', '0.8에 못 닿음'],
        ['15 mTorr', '[[a:경계]]'],
        ['20, 30 mTorr', '[[n:여유]]']]
table(s, lx, 3.3, [1.6, 1.8], rows, size=13, row_h=0.38, col_align=['l', 'c'])
tb(s, lx, 4.95, 3.4, 1.15, ['같은 전력 밀도의 R ≈ 1.36–1.47 → 운전은 늘 가장자리에 전력을 더 준다',
                            'R 1.2 → 0.8에서 총 전력을 고정하면 n̄ −4%'], size=12.5, bullet=True, space_after=5)
foot(s, '2-영역 0D, 설계 형상, 흡수 전력 300 W, 영역 전력 직접 지정 = 어떤 구동이든 분배를 마음대로 정할 때의 범위 (계산). 같은 모델이 KC20 공진의 R 변화를 과소평가 → 절대 범위는 V1·V2에서 재확인', y=6.32, h=0.5)
notes(s, 'Q1에 대한 답이다. 이 그래프는 영역 전력을 직접 지정한 계산이라, 어떤 구동 방식이든 분배를 마음대로 정할 수 있을 때 압력별로 낼 수 있는 R의 범위다.\n'
         '옅은 막대는 중앙 전력 몫을 2%까지 줄였을 때 닿는 부분인데, 실제 코일은 바깥 코일만 켜도 흡수 전력의 5–7%가 중앙에 떨어진다(코일 선택도). 이것을 넣은 하한이 진한 막대의 아래 끝이고, 숫자로 적었다.\n'
         '그러면 R = 0.8은 15 mTorr에서 겨우 닿고(하한 0.78–0.81), 20 mTorr부터 여유가 생긴다. 10 mTorr는 약 0.9–1.2, 5 mTorr는 1.1 위만 가능하다. λε = Δ가 되는 p* ≈ 16 mTorr 추정과 같은 그림이다.\n'
         '두 영역에 같은 전력 밀도를 주면 R ≈ 1.4다. 목표 띠가 이보다 아래에 있으므로 운전은 항상 가장자리에 전력을 더 주는 쪽에서 이뤄진다.\n'
         '한계를 같이 말한다. 같은 0D 모델이 KC20의 50 mTorr 공진 측정에서 R 변화 폭을 크게 과소평가했다(측정 2.54 → 0.39, 모델 5.17). 고압에서는 실제 범위가 더 넓을 수 있지만, 절대값은 V1·V2에서 다시 확인해야 한다. 그래서 운전 압력 20–30 mTorr(15 mTorr는 경계)를 1차 목표로 제안하고 팀 합의 사항으로 남긴다.')

# =================================================================== 14 triangle
s = new('triangle', '4. 구동 구조 · Q2 어떤 구동이 R만 움직이나 · 제출물 ②', '플라즈마만 보면 J는 삼각형이다', 'Ⅳ')
tb(s, 0.5, 1.4, 4.2, 0.3, ['설계 형상, 20 mTorr, 영역 전력 직접 지정 (계산)'], size=12, color=C['MUTED'])
mx, my, cs = 1.75, 2.15, 1.2
tb(s, mx, my - 0.42, cs, 0.35, ['Δln P_{tot}'], size=13, bold=True, align='c', color=C['NAVY'])
tb(s, mx + cs + 0.1, my - 0.42, cs, 0.35, ['Δx (중앙 몫)'], size=13, bold=True, align='c', color=C['NAVY'])
tb(s, 0.5, my + 0.4, 1.15, 0.4, ['Δln n̄'], size=13, bold=True, align='r', color=C['NAVY'])
tb(s, 0.5, my + cs + 0.1 + 0.4, 1.15, 0.4, ['Δln R'], size=13, bold=True, align='r', color=C['NAVY'])
cells = [(0, 0, '1.00', C['NAVY_L'], None, C['TEXT']), (0, 1, '0.25', C['AMBER_L'], None, C['AMBER']),
         (1, 0, '0', 'FFFFFF', C['AMBER'], C['AMBER']), (1, 1, '2.44', C['NAVY'], None, 'FFFFFF')]
for i, j, v, f, ln, tc in cells:
    box(s, mx + j * (cs + 0.1), my + i * (cs + 0.1), cs, cs, fill=f, line=ln, lw=2.25, dash=bool(ln), radius=0.08,
        paras=[v], size=26, bold=True, color=tc, align='c', anchor='m')
tb(s, 0.5, 4.75, 4.3, 0.95, ['[[a:J_{21} = 0]]: 총 전력은 n̄만 움직인다',
                            '[[a:J_{12}/J_{22} ≈ 0.10]]: L2 기준(≤ 0.1, §criteria§쪽)의 경계 → 총 전력으로 보상'], size=13, space_after=6)
eq(s, 'eq_bal1', 4.95, 1.42, pt=16)
eq(s, 'eq_bal2', 4.95, 2.1, pt=16)
tb(s, 4.95, 2.85, 4.55, 2.5, [
    dict(t='교재 식 2.70: T_{e}는 기체 밀도와 크기로 정해지고 전력과 무관 → 분배를 고정하면 총 전력은 R을 바꾸지 않는다', bullet=True),
    dict(t='가장자리엔 측벽 손실이 더해져 같은 전력 밀도에서 R = 1.36–1.47 → R = 1에는 중앙 몫 0.11–0.22', bullet=True)],
   size=13, space_after=8)
take(s, 0.5, 5.75, 9.0, 0.58, '이 모델에서 누설은 회로·장 단계(①②)에서만 온다 → 구동 방식은 회로 누설이 작은 것을 고른다', kind='i', size=13.5)
foot(s, '주의: J_{21} = 0은 “T_{e}가 전력과 무관”이라는 H 모드 가정의 귀결 (KC20 비공진 R도 50 → 150 W에서 3.33 → 2.54) → H4로 확인. 교재 식 2.69–2.73, 10–30 mTorr에서 J_{12}/J_{22} ≈ 0.10, 5 mTorr 0.14', y=6.38, h=0.48)
notes(s, '영역마다 입자 균형과 전력 균형을 쓰면 영역 밀도는 그 영역의 흡수 전력에 비례한다. 교재 식 2.70에 따르면 T_e는 n_g와 유효 길이로 정해지고 전력과 무관하므로, 분배를 고정한 채 총 전력을 바꾸면 R은 변하지 않는다. 그래서 J₂₁ = 0이 나온다. 계산 결과라기보다 가정의 귀결이다.\n'
         '교재도 2.4.2절 끝에서 실제로는 T_e가 밀도·압력·면적 대 부피 비의 함수라고 적고 있고, KC20의 50 mTorr 비공진 R도 50 W에서 150 W로 갈 때 3.33에서 2.54로 변했다(E–H 전이가 섞였을 가능성). 실제 측정에서 확인하는 것이 가설 H4다.\n'
         '두 번째 메시지는 손실 비대칭이다. 가장자리 영역에는 측벽 손실이 더해지므로 같은 전력 밀도를 주면 중앙이 높다. 그래서 R = 1을 만들려면 가장자리에 전력을 더 줘야 하고, 이때 n̄도 조금 움직인다(J₁₂/J₂₂ ≈ 0.10, 즉 분배 열은 L1/L2 경계). 이것은 조정 절차에서 총 전력으로 보상한다.\n'
         '결론: 플라즈마 단계만 보면 거의 L2이므로, 남는 누설은 회로·장 단계에서 온다. 다음 쪽의 후보 비교는 이 회로 누설을 기준으로 한다. 이 슬라이드가 제출물 ②(조작 변수와 밀도 응답의 관계)의 핵심이다.')

# =================================================================== 15 candidates
s = new('candidates', '4. 구동 구조 · 검토 사항 1, 질문 2-4', '후보를 가르는 것은 범위가 아니라 독립성이다', 'Ⅳ')
hdr = ['기준', dict(paras=[dict(t='A 수동 공진', bold=True, size=13.5, color='FFFFFF', align='c', after=0), dict(t='전원 1 + 가변 C', size=12, color='FFFFFF', align='c')]),
       dict(paras=[dict(t='B 독립 전원 2대 ✓ 선택', bold=True, size=13.5, color='FFFFFF', align='c', after=0), dict(t='위상 고정', size=12, color='FFFFFF', align='c')]),
       dict(paras=[dict(t='C 자기장 보조', bold=True, size=13.5, color='FFFFFF', align='c', after=0), dict(t='B에 추가', size=12, color='FFFFFF', align='c')])]
rows = [hdr,
        ['R 범위', '50 mTorr에서 0.39까지 (KC20 측정), 연속 조정 미확인', '20–30 mTorr에서 0.8–1.2 (모델), 15는 경계', '저압까지 넓힘 (추정)'],
        ['[[n:분배의 밀도 의존]]', '공진점이 부하 따라 이동, 공진 근처 급경사 → [[a:L1]]', '0°에서 ≤ 0.10 (계산) → [[n:L2 기준선]]', 'B와 같음'],
        ['n̄ 유지 보상', 'P와 C를 동시에 (예: ΔC +14.8 pF, ΔP +3.5%)', '총 전력만 (예: Δln P +2.1%)', 'B + 벽 손실(h_{R}) 변화 보정'],
        ['부작용·비용', '공진 코일 고전압 (5 A에 약 350 V)', '전원·정합기 2벌, 정합기 상호 영향', '파동·ECR, 웨이퍼 자기장, 전자석']]
fills = {(i, 2): C['NAVY_L'] for i in range(1, 5)}
fills.update({(0, 2): C['INDIGO']})
table(s, 0.5, 1.42, [1.55, 2.5, 2.55, 2.4], rows, size=12.5, row_h=0.62, first_col_bold=True, fills=fills,
      row_heights=[0.62, 0.8, 0.72, 0.72, 0.72])
box(s, 0.5, 5.2, 9.0, 1.1, fill=C['INDIGO_L'], radius=0.08, paras=[
    dict(t='A는 범위로 기각되지 않는다 (KC20). 손잡이 C 하나가 n̄와 R을 함께 움직이고 밀도에 민감해 L1에 머문다', size=13.5, after=5),
    dict(t='→ 선택: B. A는 전원이 1대뿐일 때, C는 15 mTorr 아래에서 운전해야 할 때', size=14, bold=True, color=C['INDIGO'])],
    margin=0.15, anchor='m')
foot(s, 'A의 수치(ΔC, ΔP, 코일 전압)는 앞선 0D 모델 계산. 모델은 공진 상태를 재현하지 못하므로 경향으로만 읽는다', y=6.4)
notes(s, '검토 사항 1과 질문 2-4에 대한 비교다. 처음 문서에서는 “수동 공진은 가장자리 전력이 모자라 R = 1에 못 닿는다”는 모델 계산을 A의 기각 이유로 들었다. 그런데 KC20 자체가 50 mTorr에서 공진만으로 R을 0.39까지 내렸으므로, 그 이유는 철회한다. 우리 0D 모델이 공진 상태를 재현하지 못한 것이다.\n'
         'A를 기준으로 삼지 않는 진짜 이유는 독립성이다. A의 손잡이는 커패시터 하나와 전원 전력이다. 공진점은 플라즈마 부하에 따라 움직이고 공진 근처에서 기울기가 가파르므로, 밀도가 바뀌면 분배가 같이 바뀐다. 그래서 n̄를 유지하며 R만 바꾸려면 P와 C를 동시에 정밀하게 움직여야 한다.\n'
         'B는 분배를 공진점이 아니라 두 전원의 설정값으로 정하므로, 위상 0°에서 분배의 밀도 의존이 0.10 이하로 작다(분배 열은 손실 비대칭 때문에 L2 경계).\n'
         'A는 버리지 않는다. 전원을 1대만 쓸 수 있으면 L1을 감수하고 A로 간다. C(약한 축 자기장)는 15 mTorr 아래에서 운전해야 할 때만 B에 더한다(백업 B2).')

# =================================================================== 16 phase why
s = new('phase_why', '4. 구동 구조 · 위상 (질문 2-2, 2-5)', '위상은 연속 손잡이가 아니다 → 0°나 180°에 고정', 'Ⅳ')
eq(s, 'eq_phase', 0.55, 1.45, pt=17)
tb(s, 5.15, 1.4, 4.35, 0.62, ['같은 주파수의 두 전원은 상호 인덕턴스로 서로 전력을 밀어 넣는다. 크기는 sin φ에 비례'], size=13, anchor='m')
cx_, cy_, cw_, ch_ = 0.5, 2.15, 5.6, 3.6
lay = (0.15, 0.05, 0.81, 0.74)
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
label_point(sr[1].points[0], '0° 동상', XL_LABEL_POSITION.RIGHT, size=12, color=C['NAVY'], bold=True)
label_point(sr[1].points[1], '180° 역상', XL_LABEL_POSITION.RIGHT, size=12, color=C['AMBER'], bold=True)
style_axis(ch.category_axis, 0, 360, 90, '0', grid=False, size=12)
style_axis(ch.value_axis, -1, 1, 0.5, '0.0', grid=True, size=12)
ch.value_axis.crosses = XL_AXIS_CROSSES.MINIMUM
axis_title(ch.category_axis, '위상차 φ (°)', size=12); axis_title(ch.value_axis, '교환 전력 (90°의 값 = 1)', size=12)
plot_layout(ch, *lay)
tb(s, 0.6, 5.75, 5.5, 0.3, ['띠: 교환 전력 ≤ 흡수의 10%인 위상 (보수적 값)'], size=11.5, color=C['MUTED'])
stats = [('0.2–0.7배', 'φ = 90°의 교환 전력 ÷ 흡수 전력 → 연속 손잡이로 쓰기엔 크다', C['INDIGO']),
         ('±19–38°', '0°의 위상 허용 오차', C['NAVY']),
         ('±4–12°', '180°의 위상 허용 오차 (전류가 커서 좁다)', C['AMBER'])]
y = 2.2
for big, small, col in stats:
    box(s, 6.3, y, 3.2, 1.12, fill=C['PANEL'], radius=0.08, paras=[
        dict(t=big, size=26, bold=True, color=col, after=2), dict(t=small, size=12.5)], margin=0.14, anchor='m')
    y += 1.2
take(s, 0.5, 6.0, 9.0, 0.42, '둘 중 무엇을 기준으로 할지는 다음 쪽에서 고른다', kind='i', size=13)
foot(s, 'ωM_{12} = 7.8 Ω, 플라즈마 상호 리액턴스 X′_{12} ≈ −4 ~ −6 Ω. 설계 형상, 단일 턴, 균일 반공간 (Dodd–Deeds), 밀도 고정 3×10^{10}–10^{11} cm^{−3} (계산)', y=6.5, h=0.3)
notes(s, '같은 주파수의 두 전원을 쓰면 상호 인덕턴스를 통해 한 전원이 다른 전원으로 전력을 밀어 넣는다. 그 크기는 sin φ에 비례하므로 0°와 180°에서 사라진다.\n'
         '플라즈마가 상호 리액턴스를 일부 상쇄해서(X′₁₂ ≈ −4 ~ −6 Ω, ωM₁₂ = 7.8 Ω) 90°에서도 흡수 전력의 0.2–0.7배지만, 위상을 연속 손잡이로 쓰기에는 크다. 그래서 위상은 0°나 180° 근처에 고정한다.\n'
         '교환 전력을 흡수 전력의 10% 안으로 묶으려면 0°에서는 ±19–38°, 180°에서는 ±4–12°의 위상 여유가 있다. 180°는 같은 전력에 코일 전류가 훨씬 커서 여유가 좁다. 그래서 공통 발진기로 위상을 묶고 코일 전류 위상을 직접 잰다.')

# =================================================================== 17 phase compare
s = new('phase_cmp', '4. 구동 구조 · 위상 비교 (중앙 전력 몫 0.20, 300 W, 계산)', '0°는 독립성, 180°는 이득이 낫다 → 기준 0°', 'Ⅳ')
B0 = '[[n:0°]]'; B1 = '[[d:180°]]'
rows = [['항목', 'φ = 0° (동상)', 'φ = 180° (역상)', '유리'],
        ['[[i:분배의 밀도 의존]] ∂ln(P_{c}/P_{e})/∂ln n', '−0.10 ~ −0.01', '+0.41 ~ +0.73', B0],
        ['위상 허용 오차 (교환 ≤ 10%)', '±19–38°', '±4–12°', B0],
        ['필요한 코일 전류 I_{1} / I_{2}', '3.4 / 6.6–7.3 A', '8–12 / 8–10 A', B0],
        ['효율 η (교재 식 2.57)', '0.95–0.96', '0.85–0.91', B0],
        ['분배 이득 ∂ln(P_{c}/P_{e})/∂ln k', '−0.8 ~ −1.0', '−2.9 ~ −4.0', B1],
        ['경계 ±3 cm 띠에 흡수되는 몫', '0.34–0.35', '0.20–0.22', B1],
        ['안쪽 정합 리액턴스 변화 (X′_{12} 포함)', '+13–24%', '−7–10%', B1]]
fills = {(1, j): C['INDIGO_L'] for j in range(4)}
table(s, 0.5, 1.42, [4.0, 1.9, 1.9, 1.2], rows, size=13, row_h=0.44, col_align=['l', 'c', 'c', 'c'], fills=fills)
box(s, 0.5, 5.12, 9.0, 1.15, fill=C['INDIGO_L'], radius=0.08, paras=[
    dict(t='[[i:기준 0°]]  밀도가 바뀌어도 분배가 그대로다(독립성). 전류·효율·위상 여유도 낫다', size=13.5, after=5),
    dict(t='180°의 큰 분배 이득은 전류비 오차도 같이 키운다 → H6에서 같은 기준으로 비교 (팀 원안 180° → 0° 변경은 합의 사항)', size=12.5)],
    margin=0.15, anchor='m')
foot(s, 'k = I_{2}/I_{1} (두 코일 전류비). 설계 형상, 단일 턴, 균일 반공간 (Dodd–Deeds), 밀도 고정 3×10^{10}–10^{11} cm^{−3}, 10–20 mTorr, 두 코일 저항 0.23 Ω 가정. V1에서 다중 턴으로 다시 계산', y=6.36, h=0.45)
notes(s, '둘 중 무엇을 기준으로 할지는 계산 비교다. 이 과제의 핵심 기준은 독립성이므로 첫 줄, 분배의 밀도 의존을 가장 무겁게 본다. 0°에서는 밀도가 바뀌어도 분배가 거의 그대로(−0.10 ~ −0.01)이고, 180°에서는 0.4–0.7이나 움직인다.\n'
         '0°는 같은 300 W에 필요한 코일 전류가 훨씬 작아(I₁ 3.4 A, I₂ 6.6–7.3 A) 코일 전압·구리 손실이 작고, 효율과 위상 여유도 낫다.\n'
         '180°는 코일 사이에서 장이 상쇄되어 경계 띠 흡수가 0.34에서 0.21로 줄고, 전류비에 대한 분배 이득이 3–4배 크며, 안쪽 정합이 덜 흔들린다(−7–10% vs +13–24%, 플라즈마 상호 리액턴스 포함. 코일 항만 보면 −20–25% vs +47–51%). 다만 분배 이득이 크다는 것은 범위가 넓다는 뜻이 아니라 같은 전류비 오차가 더 큰 분배 오차가 된다는 뜻이기도 하다.\n'
         '그래서 0°를 기준으로 제안하고, 180°는 가설 H6에서 같은 기준으로 비교한다. 팀 원안이 180°였으므로 기준을 0°로 바꾸는 것은 팀 합의 사항이다. 한계: 단일 턴, 균일 반공간, 밀도 고정 계산이라 V1에서 다중 턴·자기일관 밀도로 다시 계산한다.')

# =================================================================== 18 architecture
s = new('arch', '4. 구동 구조 · 제출물 ① 영역별 소스·구동부 구성도', '선택: 독립 전원 2대, 공통 발진기로 위상 0°', 'Ⅳ')
def blk(x, y, w, h, text, fill, line, tc=C['TEXT'], size=13, bold=False):
    return box(s, x, y, w, h, fill=fill, line=line, lw=1.75, radius=0.08, paras=text, size=size, color=tc,
               bold=bold, align='c', anchor='m', margin=0.05)
y1, y2, bh = 1.55, 4.15, 0.68
blk(0.5, 2.6, 1.35, 1.0, [dict(t='공통 발진기', bold=True, color='FFFFFF', size=13, align='c', after=0), dict(t='13.56 MHz', size=12, color='FFFFFF', align='c')], C['NAVY'], None)
blk(2.25, y1, 1.35, bh, ['[[n:RF 전원 1]]'], 'FFFFFF', C['NAVY'])
blk(3.9, y1, 1.15, bh, ['정합기 1'], 'FFFFFF', C['GRAY'])
blk(5.35, y1, 1.7, bh, [dict(t='안쪽 코일', bold=True, color=C['BLUE'], align='c', after=0), dict(t='r 8 cm', size=12, align='c')], C['BLUE_L'], C['BLUE'])
blk(2.25, y2, 1.35, bh, ['[[n:RF 전원 2]]'], 'FFFFFF', C['NAVY'])
blk(3.9, y2, 1.15, bh, ['정합기 2'], 'FFFFFF', C['GRAY'])
blk(5.35, y2, 1.7, bh, [dict(t='바깥 코일', bold=True, color=C['ORANGE_D'], align='c', after=0), dict(t='r 15.5 cm', size=12, align='c')], C['ORANGE_L'], C['ORANGE'])
box(s, 7.45, y1, 2.05, y2 + bh - y1, fill='FFFFFF', line=C['NAVY'], lw=2, radius=0.1,
    paras=[dict(t='챔버 + 플라즈마', bold=True, size=13.5, color=C['NAVY'], align='c', after=2), dict(t='R 20 cm, L 10 cm', size=12, align='c')],
    anchor='m', margin=0.08)
blk(7.6, y2 + bh - 0.62, 1.75, 0.5, ['웨이퍼 FHP 배열'], C['PANEL'], C['GRAY'], size=12)
path(s, [(1.85, 2.85), (2.05, 2.85), (2.05, y1 + bh / 2), (2.23, y1 + bh / 2)], color=C['NAVY'], w=1.75)
path(s, [(1.85, 3.35), (2.05, 3.35), (2.05, y2 + bh / 2), (2.23, y2 + bh / 2)], color=C['NAVY'], w=1.75)
for yy in (y1 + bh / 2, y2 + bh / 2):
    seg(s, 3.6, yy, 3.88, yy, color=C['NAVY'], w=1.75, head=True)
    seg(s, 5.05, yy, 5.33, yy, color=C['NAVY'], w=1.75, head=True)
    seg(s, 7.05, yy, 7.43, yy, color=C['NAVY'], w=1.75, head=True)
# inner loop (gray)
box(s, 2.25, 2.55, 3.0, 1.1, fill=C['PANEL'], line=C['MUTED'], lw=1.5, dash=True, radius=0.1,
    paras=[dict(t='안쪽 루프 (≤ ms)', bold=True, size=13, color=C['DARK'], align='c', after=2),
           dict(t='코일 전류의 크기·위상을 직접 재서 맞춘다', size=12, align='c')], anchor='m', margin=0.08)
seg(s, 2.75, 2.55, 2.75, y1 + bh + 0.02, color=C['MUTED'], w=1.75, dash=True, head=True)
seg(s, 2.75, 3.65, 2.75, y2 - 0.02, color=C['MUTED'], w=1.75, dash=True, head=True)
path(s, [(6.2, y1 + bh), (6.2, 2.85), (5.27, 2.85)], color=C['MUTED'], w=1.75, dash=True)
path(s, [(6.2, y2), (6.2, 3.35), (5.27, 3.35)], color=C['MUTED'], w=1.75, dash=True)
tb(s, 6.3, 2.9, 1.1, 0.5, ['전류·위상', '센서'], size=12, color=C['DARK'], space_after=0)
# outer loop (indigo)
box(s, 2.25, 5.3, 5.0, 0.85, fill=C['INDIGO_L'], line=C['INDIGO'], lw=1.5, dash=True, radius=0.1,
    paras=[dict(t='바깥 루프 (≈ 1 s): FHP → n̄, R_{Γ} → J^{−1} 피드포워드 + 적분', bold=True, size=12.5, color=C['INDIGO'], align='c', after=0),
           dict(t='두 코일 전류의 설정값(총량, 비 k)을 안쪽 루프에 준다', size=12, align='c')], anchor='m', margin=0.06)
path(s, [(8.475, y2 + bh + 0.02), (8.475, 5.72), (7.27, 5.72)], color=C['INDIGO'], w=1.75, dash=True)
seg(s, 3.75, 5.3, 3.75, 3.67, color=C['INDIGO'], w=1.75, dash=True, head=True)
tb(s, 3.82, 3.75, 1.0, 0.28, ['설정값'], size=11.5, bold=True, color=C['INDIGO'])
foot(s, 'R_{Γ}: FHP가 재는 이온 선속비 (≈ R). 선택이 바뀌는 조건: 전원 1대뿐 → 수동 공진(L1 감수) · 15 mTorr 아래 운전 → 자기장 보조 · 경계 분리가 우선이고 위상 유지가 되면 → 180°', y=6.27, h=0.5)
notes(s, '제출물 ① 영역별 소스·구동부 구성도다. 같은 주파수의 RF 전원 두 대가 각자 정합기를 거쳐 안쪽·바깥 코일을 구동하고, 공통 발진기가 두 전원의 위상을 0°로 묶는다. 파란 점선이 안쪽 루프로, 코일 전류의 크기와 위상을 직접 재서 맞춘다. 주황 점선이 바깥 루프로, 웨이퍼 FHP 배열로 n̄와 R_Γ를 재고 J⁻¹ 피드포워드와 적분 동작으로 두 코일 전류의 설정값을 정한다.\n'
         '이 구조를 고른 이유는 세 가지다. 첫째, 분배를 공진점이 아니라 설정값으로 직접 지정하므로 플라즈마 부하가 바뀌어도 분배가 덜 흔들린다(0°에서 분배의 밀도 의존 0.10 이하). 둘째, 플라즈마만 보면 J가 삼각형이라 두 단일 루프로 나뉜다. 셋째, 기존 회로 모델에 전원 하나를 더하면 바로 계산할 수 있어 검증 경로가 짧다.\n'
         '대가는 전원·정합기 두 벌, 공통 발진기, 전류·위상 센서, 그리고 상호 인덕턴스로 두 정합기가 서로 영향을 주는 문제(백업 B4)다. 질문 2-1(전원 수와 배치), 2-2(코일 2개면 충분한가)도 여기서 답한다. 독립으로 다룰 수 있는 영역 수는 반경 폭 약 11 cm를 max(λε, ℓ)로 나눈 값 정도라 20 mTorr에서 약 2개이고, 출력이 중앙·가장자리 둘인 이 과제에는 코일 2개가 최소이자 충분하다.')

# =================================================================== 19 control
s = new('control', '5. 조정과 측정 · Q3 어떻게 맞추고 확인하나 (질문 2-5, 4-2)', '플라즈마가 가장 빠르다 → 세 겹 루프로 나눈다', 'Ⅴ')
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
for e, lab in [(-8, '10 ns'), (-6, '1 μs'), (-4, '100 μs'), (-2, '10 ms'), (0, '1 s'), (2, '100 s'), (4, '3 시간')]:
    x = xt(10 ** e)
    tb(s, x - 0.45, y0 + 7 * rh + 0.18, 0.9, 0.26, [lab], size=11.5, color=C['MUTED'], align='c')
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
    tb(s, xe + 0.08, yy, 1.3, rh, [val], size=12, color=col, anchor='m')
# gap annotation
ya = y0 + 3 * rh + 0.04
seg(s, xt(2e-4), ya, xt(0.1), ya, color=C['AMBER'], w=1.75, head=True, tail=True)
tb(s, xt(0.1) + 0.06, ya - 0.14, 2.3, 0.28, ['약 3자릿수 차이'], size=12, bold=True, color=C['AMBER'], anchor='m')
loops = [('안쪽 (≤ ms)', '코일 전류의 크기·위상', '전력 대신 전류 기준: VI 프로브 전력은 위상 0.1° 오차에 17% (식 5.33)'),
         ('가운데 (0.1–1 s)', '자동 정합', '정합 위치를 전류비 k의 함수로 미리 옮기는 피드포워드'),
         ('바깥 (≈ 1 s 측정)', 'FHP로 n̄, R_{Γ}', 'J^{−1} 피드포워드 + 적분. 교차 주파수 ≤ 0.2 rad/s (0.03 Hz), 설정 ≈ 20 s')]
x = 0.5
for head, what, body in loops:
    box(s, x, 4.35, 2.9, 1.5, fill='FFFFFF', line=C['NAVY'], lw=1.25, radius=0.08, paras=[
        dict(t=head, bold=True, size=13.5, color=C['NAVY'], after=1), dict(t=what, bold=True, size=12.5, after=3),
        dict(t=body, size=12, color=C['TEXT'])], margin=0.12)
    x += 3.05
take(s, 0.5, 5.95, 9.0, 0.5, '세 루프는 시간으로 갈라진다. 바깥 루프의 두 채널(n̄, R)은 J_{21} ≈ 0이라 서로 독립 (RGA λ_{11} ≈ 1)', kind='i', size=13)
foot(s, 'RGA: 상대 이득 배열 (Bristol 1966), 1에 가까우면 단일 루프로 나눠도 된다. 시간 상수: 교재 식 1.88, 2.72 (계산), 교재 5장 (FHP)', y=6.5, h=0.3)
notes(s, '플라즈마 밀도 응답은 0.1–0.2 ms 수준이고 센서와 정합기는 0.1–1 s다. 센서·정합기와는 세 자릿수, 코일 전류 루프와는 한 자릿수 정도 차이가 나므로 제어 설계에서는 플라즈마를 정적 이득 J로 다뤄도 되고, 정상 상태 0D 모델이 제어 설계에 충분하다.\n'
         '루프는 바깥으로 갈수록 5–10배씩 느리게 잡아 서로 쫓지 않게 한다. 안쪽 루프를 전력이 아니라 코일 전류로 잡는 이유: ICP 안테나는 리액턴스가 커서 tan φ_Z ≈ 100이고, VI 프로브 전력은 위상 0.1° 오차에 17%가 틀린다.\n'
         '바깥 루프 대역폭은 측정 지연이 정한다. 적분기와 지연만 있는 루프에서 위상 여유 60°를 지키려면 ω_c ≤ π/(6 T_d)이고, T_d = 1–2 s면 0.26–0.52 rad/s다. 정합기보다 5배 이상 느리게 두면 0.2 rad/s(약 0.03 Hz)가 상한이고 설정 시간은 약 20 s다. 레시피 단계가 수십 초 이상이면 충분하다. 단계 변경 자체는 피드포워드가 즉시 처리한다.\n'
         '2×2 루프를 두 단일 루프로 나눠도 되는지는 RGA로 본다. 독립 전원 0°는 J₂₁ ≈ 0이라 λ₁₁ ≈ 1이다. 안테나 수가 위상 여유를 정하는 것은 아니고, 3개 이상이면 J의 조건수가 나빠져 오히려 이득을 낮춰야 한다(질문 4-2).')

# =================================================================== 20 procedure
s = new('procedure', '5. 조정과 측정 · 제출물 ③ 목표 밀도비 조정 절차, 검토 사항 3', '조정 절차: 분배로 R, 총 전력으로 n̄', 'Ⅴ')
steps = [('점화', '안쪽 코일로 점화 → H 모드 확인 → 바깥 전원·위상 고정'),
         ('동작점', '압력별 J 표에서 J_{11}, J_{12}, J_{22} 읽기'),
         ('피드포워드', 'Δx와 Δln P를 동시에 설정'),
         ('전류 루프·정합', '전류·위상 맞춤, 정합기는 k별 위치표'),
         ('바깥 루프', 'FHP로 a_{0}(전체)·a_{1}(분포) → 남은 오차 적분'),
         ('판정', '|Δln R_{Γ}| ≤ 0.02, n̄ ±5% → 완료')]
y = 1.42
for i, (head, body) in enumerate(steps):
    circle(s, 0.75, y + 0.36, 0.46, fill=C['NAVY'], paras=[str(i + 1)], size=15, color='FFFFFF')
    tb(s, 1.15, y + 0.03, 4.4, 0.78, [dict(t=head, bold=True, size=14, color=C['NAVY'], after=1), dict(t=body, size=13)], line=1.0)
    if i < 5:
        seg(s, 0.75, y + 0.61, 0.75, y + 0.83, color='9AA3B5', w=1.25)
    y += 0.84
box(s, 5.75, 1.42, 3.75, 4.95, fill=C['PANEL'], radius=0.1)
tb(s, 5.95, 1.55, 3.4, 0.6, [dict(t='계산 예 (20 mTorr)', bold=True, size=14, color=C['NAVY'], after=2),
                             dict(t='R을 ln 기준 0.2 (약 18%) 낮추고 n̄는 유지', size=13)])
eq(s, 'eq_step1', 5.95, 2.3, pt=16)
eq(s, 'eq_step2', 5.95, 2.98, pt=16)
tb(s, 5.95, 3.68, 3.4, 0.3, ['J_{11} = 1, J_{12} = 0.25, J_{22} = 2.44'], size=12.5, color=C['DARK'])
box(s, 5.95, 4.08, 3.35, 0.62, fill='FFFFFF', radius=0.06, paras=[dict(t='Δx = −0.082', size=20, bold=True, color=C['NAVY'], align='c')], anchor='m')
box(s, 5.95, 4.8, 3.35, 0.62, fill='FFFFFF', radius=0.06, paras=[dict(t='Δln P = +2.1%', size=20, bold=True, color=C['NAVY'], align='c')], anchor='m')
tb(s, 5.95, 5.52, 3.4, 0.75, ['보상하지 않으면 n̄ −2.1%', '(수동 공진이면 ΔC +14.8 pF와 ΔP +3.5%를 함께)'], size=12, color=C['TEXT'], space_after=2)
foot(s, 'x = 중앙 전력 몫, P = 총 흡수 전력. 분배가 한계(중앙 몫 약 0.07 / 0.93)에 닿으면 압력을 올리거나 자기장 보조. 실제 운전은 두 조작을 J^{−1}로 동시에 낸다', y=6.45, h=0.42)
notes(s, '검토 사항 3(한 영역을 유지하며 다른 영역을 바꾸는 조작 순서와 보상)에 대한 답이자 제출물 ③이다. 플라즈마만 보면 J가 삼각형이므로 순서가 자연스럽게 정해진다. 분배로 R을 맞추고, 그때 생기는 n̄ 변화(J₁₂ 몫)를 총 전력으로 되돌린다. 실제 운전에서는 두 조작을 J⁻¹로 동시에 내보내고, 순서 규칙은 피드포워드가 틀렸을 때의 수동 조정 절차로 쓴다.\n'
         '숫자 예: 20 mTorr에서 R을 ln 기준 0.2(약 18%) 낮추려면 중앙 몫을 0.082 줄이고 총 전력을 2.1% 올린다. 보상하지 않으면 n̄가 2.1% 내려간다. 같은 변경을 수동 공진 구조로 하면 ΔC = +14.8 pF와 ΔP = +3.5%를 함께 움직여야 했다(앞선 모델).\n'
         '절차의 실패 조건도 정해 두었다. 분배가 코일 선택도의 한계(중앙 몫 약 0.07 또는 0.93)에 닿으면 그 압력에서는 목표에 닿지 못하는 것이므로 압력을 올리거나 자기장 보조를 검토한다. 판정 기준은 FHP가 직접 재는 R_Γ로 |Δln R_Γ| ≤ 0.02다.')

# =================================================================== 21 measure
s = new('measure', '5. 조정과 측정 · 제출물 ④ 측정 계획, 검토 사항 4 (질문 1-6)', '웨이퍼 FHP 배열이 약 1초마다 n̄와 R_{Γ}를 준다', 'Ⅴ')
wcx, wcy, wd = 2.0, 2.95, 2.9
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
    yy = 4.55 + i * 0.27
    circle(s, 0.72, yy + 0.13, 0.13, fill=col)
    tb(s, 0.88, yy, 2.8, 0.27, [txt], size=12)
rows = [['진단', '재는 것', '역할'],
        ['[[n:FHP 배열]] (식 5.23–5.25)', '점별 이온 선속, T_{e}', '바깥 루프 주 센서'],
        ['랭뮤어 탐침 (5.1절)', 'EEPF → 국소/비국소', 'λ_{ε} 가설 검증'],
        ['컷오프 탐침 (식 5.34)', '전자 밀도 절대값', 'n̄ 절대값 교정'],
        ['B-dot (식 5.35, 5.36)', 'RF 자기장 → 표피 깊이', '회로·장 모델 검증'],
        ['코일 전류·위상 센서', '전류 크기와 위상', '안쪽 루프']]
table(s, 3.75, 1.42, [2.05, 1.95, 1.75], rows, size=12, row_h=0.5, fills={(1, j): C['NAVY_L'] for j in range(3)})
box(s, 0.5, 5.45, 9.0, 0.95, fill=C['PANEL'], radius=0.08)
eq(s, 'eq_split', 0.62, 5.52, pt=15)
tb(s, 0.65, 5.98, 3.9, 0.35, ['ψ = +½ (중앙), −½ (가장자리)'], size=11.5, color=C['MUTED'])
tb(s, 4.55, 5.5, 4.85, 0.85, [
    dict(t='[[n:a_{0}]] 전체 변화, [[n:a_{1}]] 분포 변화. a_{1}이 2% 안이면 전체 변화만', after=3),
    dict(t='점별 잡음 2%(가정) → ln R_{Γ} 불확도 ≈ 1.1%, R로 환산하면 ≈ 3.7%')], size=12, anchor='m')
foot(s, 'FHP는 밀도가 아니라 이온 선속을 잰다: R_{Γ} = R·√(T_{e,c}/T_{e,e}) → 제어 출력은 R_{Γ}, R은 환산 보고 (팀 합의 제안). 교재 5장', y=6.45)
notes(s, '측정은 세 가지에 답해야 한다. 바깥 루프 주기 안에 n̄와 R을 잴 수 있는가, 전체 변화와 분포 변화를 구분할 수 있는가, 모델의 중간 단계를 확인할 수 있는가. 하나로는 안 되므로 역할을 나눴다.\n'
         '랭뮤어 탐침만으로 충분한가(질문 1-6)에 대한 답은 “아니다”다. EEPF를 줄 수 있는 유일한 수단이라 λε 가설 검증에는 꼭 필요하지만, 한 점씩 이동하며 재고 RF 보상과 면적 조건(교재 식 5.1, 교재 예로 접지면의 약 4만분의 1 이하, Ar이면 약 2.7만분의 1)이 까다로워 제어용 센서로는 맞지 않는다.\n'
         'FHP가 재는 것은 밀도가 아니라 이온 선속이다. 선속비 R_Γ = R·√(T_e,c/T_e,e)이므로 R로 바꾸려면 T_e 비가 필요하고, T_e 상대 오차 5%(가정)면 R의 불확도는 약 3.7%로 커진다. 그래서 제어 출력을 R_Γ로 두고 R은 환산해 보고하자는 것이 팀 합의 제안이다.\n'
         '전체/분포 변화 구분은 점별 로그 변화를 a₀ + a₁ψ + ε로 최소제곱 분해한다. a₁이 불확도의 2배(약 2%) 안이면 전체 변화만 있었다고 본다. 75 mm의 잔차 ε가 크면 코일 2개로 고칠 수 없는 모양 변화다.')

# =================================================================== 22 verify
s = new('verify', '6. 검증과 한계 · 주장마다 예측값과 판정 기준', '가설 7개: 5개는 다음 2주(V1)에 판정한다', 'Ⅵ')
rows = [['가설', '예측 (수식)', '판정 기준', '단계'],
        ['**H1** 압력이 높을수록 분배가 R을 움직이는 힘이 크다', 'g_{R} = 0.5인 압력 ≈ 11 mTorr', '반값 압력 5.5–22 mTorr', 'V1'],
        ['**H2** L이 작을수록 확산 누설이 작다', 'e^{−πΔ/L} = 0.02–0.14', '2D 누설이 식의 0.5–2배', 'V2'],
        ['**H3** 저압 동반 변화는 비국소 가열·회로 결합 탓', '전류 고정 시 남는 결합 ≈ 1 − g_{R}', '식과 ±30% 안', 'V1'],
        ['**H4** (총 전류, 분배) 좌표에서 J가 삼각형', 'J_{21} = 0 (식 2.70), 회로 포함 0°에서 ≤ 0.09', 'J_{21}/J_{11} ≤ 0.1 (L2)', 'V1'],
        ['**H5** 약한 축 자기장이 저압 독립성을 높인다', '5 mTorr, 약 2.7 G에서 λ_{ε⊥} = Δ', '5 mTorr에서 g_{R} ≥ 0.5', 'V2'],
        ['**H6** 0°가 더 독립적, 180°는 이득이 크다', '위상 비교표 (§phase_cmp§쪽)', '180° 채택: 이득 ×2 이상, 누설 ≤ 0.2', 'V1'],
        ['**H7** 20–30 mTorr에서 R 0.8–1.2, n̄ ±5%', 'R 범위 예측 (§predict§쪽)', '|Δln R_{Γ}| ≤ 0.02, n̄ ±5%', 'V1']]
rows = [[R(c) for c in r] for r in rows]
table(s, 0.5, 1.42, [3.45, 2.65, 2.2, 0.7], rows, size=12.5, row_h=0.56, col_align=['l', 'l', 'l', 'c'],
      row_heights=[0.4] + [0.58] * 7, bold_cells={(i, 3) for i in range(1, 8)}, colors={(i, 3): C['NAVY'] for i in range(1, 8)})
take(s, 0.5, 6.0, 9.0, 0.5, 'V1 = 회로 모델 확장(다음 2주), V2 = 축대칭 2D 계산. 판정은 절대 밀도가 아니라 비(R, g_{R}, 누설)로', kind='i', size=13)
notes(s, '오늘 말한 주장을 모두 “수식 → 예측값 → 판정 기준”으로 바꿔 두었다. 그래야 다음 단계에서 맞고 틀림을 가릴 수 있다. 판정 범위(예측의 0.5–2배, ±30%)는 0D 근사의 정확도를 고려해 정한 제안값이다.\n'
         '가장 중요한 것은 H1이다. λε 브리지 w = e^(−Δ/λε)는 가정이고, 운전 압력 범위와 목표 도달 압력이 모두 이 가정에 걸려 있다. H4는 J₂₁ = 0이라는 모델 가정을 측정으로 확인하는 것이고, H6은 위상 기준(0° vs 180°)을 확정하는 판정이다. H7이 과제 목표 자체의 판정이다.\n'
         '단계 열의 V1은 회로 모델 확장, V2는 축대칭 2D 계산이다. 다음 쪽에서 이 판정을 흔들 수 있는 가정들을 정리한다.')

# =================================================================== 23 risks
s = new('risks', '6. 검증과 한계', '결정을 바꿀 수 있는 가정은 네 가지다', 'Ⅵ')
risks = [('λ_{ε} 브리지 w = e^{−Δ/λε}', '운전 압력 범위와 p*', 'H1, 위치별 EEPF (랭뮤어)'),
         ('0D 모델이 고압 공진을 재현하지 못함', 'R 범위의 절대값', 'V1·V2에서 재계산'),
         ('단일 턴·균일 반공간·밀도 고정 계산', '0°/180° 비교 수치 (sin φ 결론은 유지)', 'V1 다중 턴·자기일관 밀도'),
         ('장비: 전원 2대, 공통 발진기, FHP', '구조 자체 (없으면 수동 공진으로 후퇴)', '즉시 확인')]
pos = [(0.5, 1.42), (5.1, 1.42), (0.5, 3.72), (5.1, 3.72)]
for i, ((a, d, chk), (x, y)) in enumerate(zip(risks, pos)):
    box(s, x, y, 4.4, 2.15, fill=C['PANEL'], radius=0.1)
    circle(s, x + 0.38, y + 0.4, 0.46, fill=C['INDIGO'], paras=[str(i + 1)], size=15, color='FFFFFF')
    tb(s, x + 0.75, y + 0.17, 3.5, 0.55, [a], size=14, bold=True, color=C['INDIGO'], anchor='m')
    tb(s, x + 0.2, y + 0.85, 4.0, 0.65, ['[[m:걸린 결정]] ' + d], size=13.5)
    box(s, x + 0.2, y + 1.55, 4.0, 0.42, fill='FFFFFF', radius=0.06, paras=['[[n:확인]] ' + chk], size=13, anchor='m', margin=0.1)
take(s, 0.5, 6.0, 9.0, 0.5, '나머지 가정(맥스웰 EEPF, 코일 저항, 확산 원거리 근사)은 수치를 옮기지만 방향은 바꾸지 않는다', kind='g', size=12.5, lead=None)
notes(s, '우리가 모르는 것을 정리한다. 결정을 뒤집을 수 있는 것은 네 가지다.\n'
         '첫째, λε 브리지는 가정이라 운전 압력 범위가 여기에 걸려 있다. 위치별 EEPF를 랭뮤어 탐침으로 재서 H1과 함께 확인한다.\n'
         '둘째, 0D 모델은 KC20의 고압 공진 측정을 재현하지 못했으므로 R 범위의 절대값은 아직 확정이 아니다.\n'
         '셋째, 위상 비교는 단일 턴·균일 반공간·밀도 고정 계산이라 V1에서 다시 해야 한다. 다만 교환 전력이 sin φ에 비례한다는 결론은 유지된다.\n'
         '넷째, 장비가 없으면 구조 자체를 수동 공진으로 바꿔야 하므로 가장 먼저 확인한다.')

# =================================================================== 24 decisions
s = new('decisions', '6. 검증과 한계 · 팀 합의', '결정 요청 5건과 다음 2주 계획', 'Ⅵ')
rows = [['항목', '제안', '근거'],
        ['위상 기준', '[[n:0°]] (원안 180°는 H6에서 비교)', '§phase_cmp§쪽'],
        ['운전 압력', '[[n:20–30 mTorr]] 1차 (15는 경계), 그 아래는 자기장 보조 검토', '§predict§쪽'],
        ['목표 수치', 'R 0.8–1.2, n̄ ±5%', '§task§쪽'],
        ['제어 출력', 'FHP가 재는 R_{Γ}, R은 환산 보고', '§measure§쪽'],
        ['2D 도구', 'COMSOL 가용 여부 확인 뒤 결정', '§model§쪽']]
rows = [[R(c) for c in r] for r in rows]
table(s, 0.5, 1.42, [1.7, 6.2, 1.1], rows, size=13, row_h=0.47, first_col_bold=True, col_align=['l', 'l', 'c'])
tb(s, 0.5, 4.45, 9.0, 0.3, ['검증 단계'], size=13, bold=True, color=C['INDIGO'])
phases = [('V0 이번 발표', '식과 단발 계산', C['GRAY_L'], C['TEXT']),
          ('V1 다음 2주', '회로에 전원 2·위상·다중 턴 → 압력·위상별 J 표, H1·H3·H4·H6·H7', C['NAVY'], 'FFFFFF'),
          ('V2 2D 계산', '축대칭 확산·장, 측정 위치 환산 → H2, H5', C['NAVY_L'], C['TEXT']),
          ('V3 측정', '장비가 있으면 실제 J로 최종 판정', C['NAVY_L'], C['TEXT'])]
x = 0.5
ws = [1.55, 3.05, 2.3, 2.0]
for (head, body, f, tc), w in zip(phases, ws):
    shp = box(s, x, 4.82, w + 0.15, 1.45, fill=f, shape=MSO_SHAPE.CHEVRON if x > 0.5 else MSO_SHAPE.PENTAGON, radius=None,
              adj=[0.14], paras=[dict(t=head, bold=True, size=13, color=tc, after=3), dict(t=body, size=12, color=tc)],
              margin=0.08, anchor='m')
    shp.text_frame.margin_left = I(0.3 if x > 0.5 else 0.12); shp.text_frame.margin_right = I(0.22)
    x += w + 0.03
foot(s, '먼저 확인할 장비: 전원 2대, 공통 발진기, FHP 배열, 정합기 응답 시간', y=6.42)
notes(s, '팀이 정할 것 중 가장 큰 것은 위상 기준을 원안 180°에서 0°로 바꾸는 것과, 운전 압력을 20–30 mTorr(15 mTorr는 경계)로 좁히는 것이다.\n'
         '제어 출력을 R_Γ로 두는 이유는 FHP가 직접 재는 양이라 불확도가 약 1%로 작기 때문이다(R로 환산하면 T_e 오차 때문에 약 3.7%). 2D 도구는 COMSOL을 쓸 수 있는지 확인한 뒤 정한다.\n'
         '검증은 네 단계다. V0가 오늘 발표한 식과 단발 계산이고, 다음 2주의 일은 V1이다. 회로 모델을 전원 2개·위상·다중 턴으로 확장해 압력·위상별 J 표를 만들고 H1, H3, H4, H6, H7을 판정한다. V2는 축대칭 2D 확산·장 계산으로 확산 누설과 측정 위치 환산을, V3는 장비가 있으면 실제 J를 잰다.')

# =================================================================== 25 conclusion
s = new('conclusion', '결론', '정리: 세 질문에 대한 답', '결론')
ans = [('Q1', '어느 압력에서', '**20–30 mTorr** (15는 경계). λ_{ε}가 코일 간격 7.5 cm보다 짧을 때 분배가 R을 움직인다'),
       ('Q2', '어떤 구동으로', '**독립 전원 2대 + 위상 0°.** 분배를 설정값으로 정해 밀도 의존 ≤ 0.10'),
       ('Q3', '어떻게 맞추고 확인', '**분배로 R, 총 전력으로 n̄.** FHP 배열의 a_{0}·a_{1}로 전체와 분포를 가른다')]
y = 1.42
for tag, q, a in ans:
    box(s, 0.5, y, 9.0, 0.82, fill=C['PANEL'], radius=0.08)
    chip(s, 0.5, y, 0.75, 0.82, tag, QCOL[tag], size=15, radius=0.08)
    tb(s, 1.4, y, 2.0, 0.82, [q], size=14, bold=True, color=C['DARK'], anchor='m')
    tb(s, 3.4, y, 6.0, 0.82, [a], size=14, anchor='m', color=C['TEXT'])
    y += 0.92
tb(s, 0.5, 4.25, 9.0, 0.3, ['제출물'], size=13, bold=True, color=C['INDIGO'])
dl_ = [('①', '소스·구동부 구성도', '§arch§쪽'), ('②', '조작 변수 → 밀도 응답', '§triangle§쪽'),
       ('③', '목표 밀도비 조정 절차', '§procedure§쪽'), ('④', '측정 계획', '§measure§쪽')]
x = 0.5
for n_, t_, p_ in dl_:
    box(s, x, 4.6, 2.15, 0.85, fill='FFFFFF', line=C['INDIGO'], lw=1.25, radius=0.08,
        paras=[dict(t=f'{n_} {t_}', bold=True, size=12.5, color=C['INDIGO'], after=1, align='c'), dict(t=R(p_) + ' · 초안', size=11, color=C['MUTED'], align='c')],
        anchor='m', margin=0.06)
    x += 2.283
take(s, 0.5, 5.62, 9.0, 0.82, '다음 2주 (V1): 회로 모델에 전원 2개·위상·다중 턴을 넣어 압력·위상별 J 표를 만들고 H1·H3·H4·H6·H7을 판정한다. 그 전에 장비부터 확인한다', kind='b', size=13.5)
notes(s, '정리한다. 어느 압력에서 가능한가에는 20–30 mTorr, 15 mTorr는 경계라고 답했다. λε가 코일 간격보다 짧아야 분배가 R을 움직이기 때문이다.\n'
         '어떤 구동으로 하는가에는 독립 전원 두 대와 위상 0° 고정이라고 답했다. 분배를 공진점이 아니라 설정값으로 정해 밀도가 바뀌어도 분배가 거의 그대로다.\n'
         '어떻게 맞추고 확인하는가에는 분배로 R, 총 전력으로 n̄를 맞추고, 웨이퍼 FHP 배열로 전체 변화와 분포 변화를 가른다고 답했다.\n'
         '네 제출물은 모두 초안이 있고, V1 결과로 갱신한다. 다음 2주는 회로 모델 확장과 장비 확인이다. 질문 받겠다.')

# =================================================================== 26 refs
s = new('refs', '참고문헌', '근거 자료와 확인 수준', '참고')
left = [dict(t='교재·학술지 (본문 확인)', bold=True, color=C['INDIGO'], size=12.5, after=3),
        '[교재] 「플라즈마 전자공학」 4판, 1.10절, 2.3.4·2.4절, 5장',
        '[KC20] J.-H. Kim, C.-W. Chung, Phys. Plasmas 27, 063511 (2020)',
        '[P17] I.-S. Park et al., Phys. Plasmas 24, 123506 (2017)',
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
tb(s, 0.5, 1.42, 4.4, 4.9, left, size=12, space_after=5)
tb(s, 5.1, 1.42, 4.4, 4.9, right, size=12, space_after=5)
take(s, 0.5, 6.0, 9.0, 0.5, '수치 표시: (문헌) 출처 값 · (계산) 모델·스크립트 값 · (추정) 차수 어림 · (가정) 근거 없이 둔 값', kind='g', size=12, lead=None)
notes(s, '참고문헌은 확인 수준에 따라 나눴다. 주장의 근거는 본문을 확인한 교재·학술지·특허로만 대고, 초록만 확인한 자료는 선행 사례 소개에만 쓴다.')

# =================================================================== backup divider
s = new('bk_div', '백업', '백업 슬라이드', '백업')
items = [('B1', '반응 테이블', '질문 1-7', 'bk_reactions'), ('B2', '자기장·페라이트 보조', '질문 3-1, 3-2', 'bk_field'),
         ('B3', '과도 상황', '질문 4-3', 'bk_transient'), ('B4', '정합기 상호작용', '독립 전원의 대가', 'bk_matching'),
         ('B5', '질문 대응표', '질문 번호 → 쪽', 'bk_qmap')]
y = 1.5
for code, t_, q_, k_ in items:
    box(s, 1.5, y, 7.0, 0.78, fill=C['PANEL'], radius=0.08)
    chip(s, 1.5, y, 0.9, 0.78, code, C['GRAY'], size=15, radius=0.08)
    tb(s, 2.6, y, 3.8, 0.78, [t_], size=15, bold=True, color=C['TEXT'], anchor='m')
    tb(s, 6.2, y, 2.15, 0.78, [f'{q_} · {NUM[k_]}쪽'], size=12, color=C['MUTED'], anchor='m', align='r')
    y += 0.92
notes(s, '질의응답용 백업 슬라이드다. 질문 번호로 해당 쪽을 찾으려면 B5 대응표를 연다.')

# =================================================================== B1 reactions
s = new('bk_reactions', '백업 B1 · 반응 테이블 (질문 1-7)', '1차 모델은 Ar 반응 다섯 개로 충분하다', '백업')
rows = [['반응', '문턱 (eV)', '모델에서의 역할'],
        ['R1 이온화 e + Ar → Ar^{+} + 2e', '15.76', '입자 균형 → T_{e} (교재 식 2.69, 2.70)'],
        ['R2 여기(합산) e + Ar → Ar* + e', '12.14', '충돌 에너지 손실 ε_{c} (식 2.63)'],
        ['R3 탄성 e + Ar → e + Ar', '–', 'ε_{c}의 탄성 항, ν_{m} (표피 깊이, 자화 조건)'],
        ['R4 이온-중성 (전하 교환 포함)', '–', 'h-factor (식 2.71), 양극성 확산 (식 1.68)'],
        ['W1 벽 재결합', '–', '입자·에너지 손실 (식 2.66, 2.69)']]
table(s, 0.5, 1.42, [3.6, 1.0, 4.4], rows, size=11.5, row_h=0.4, col_align=['l', 'c', 'l'])
tb(s, 0.5, 3.92, 9.0, 0.55, ['속도 계수: 맥스웰 분포의 L&L 표 3.3 식. T_{e} = 2.5 eV에서 K_{iz} ≈ 3.8×10^{−17}, K_{ex} ≈ 2.0×10^{−16}, K_{el} ≈ 9.8×10^{−14} m^{3}/s, ε_{c} ≈ 81 V, ε_{T} ≈ 99 V (계산)'],
   size=11.5, color=C['TEXT'])
rows = [['확장 후보', '왜 중요한가', '넣는 기준'],
        ['준안정 Ar^{m}, 단계 이온화', '밀도가 전력에 비선형 → J_{21} ≠ 0', '단계 이온화 비중 > 10%'],
        ['기체 가열·중성 고갈', 'n_{g} 감소 → λ_{ε} 증가 → g_{R} 감소', '고전력 기체 온도 추정 뒤'],
        ['공정 기체 (Cl_{2}, CF_{4}, O_{2})', '음이온이 T_{e}를 전력 의존으로 (교재 2.4.2절)', '과제를 공정 기체로 넓힐 때']]
table(s, 0.5, 4.55, [2.7, 3.6, 2.7], rows, size=11.5, row_h=0.4, header_fill=C['GRAY'])
foot(s, '맥스웰 가정 점검: 비국소 영역(약 10 mTorr 아래)은 랭뮤어 EEPF를 적분한 속도 계수와 비교', y=6.32)
notes(s, '5–30 mTorr Ar에서 T_e와 에너지 손실을 정하는 것은 R1–R3이고 이온 수송을 정하는 것은 R4다. 이 범위에서는 교재 식 2.70대로 T_e가 전력과 무관해 J₂₁ = 0이 성립한다. 확장 후보는 모두 이 결론을 깨는 방향으로 작용하므로, 넣을지를 판정 기준과 함께 정해 두었다. ε_T = ε_c + 2T_e + 5.2T_e ≈ 99 V는 교재 그림 2.43의 값(T_e = 2 V에서 약 90 V)과 같은 크기다.')

# =================================================================== B2 field / ferrite
s = new('bk_field', '백업 B2 · 보조 수단 (질문 3-1, 3-2)', '자기장 보조는 저압 전용 손잡이다', '백업')
panel(s, 0.5, 1.42, 4.4, 4.0, '약한 축 방향 정자기장', [
    dict(t='λ_{ε⊥} = Δ가 되는 자기장: 1 / 5 / 10 mTorr에서 2.9 / 2.7 / 2.2 G (추정)', bullet=True),
    dict(t='ECR 4.84 G 아래지만 ω_{ce}/ω ≈ 0.46–0.59 → 그 전에 파동 전파가 바뀐다', bullet=True),
    dict(t='h_{R}이 줄어 R 기준값이 바뀐다', bullet=True),
    dict(t='웨이퍼 위 자기장은 대전 손상 위험', bullet=True)], kind='n', size=14, after=9)
panel(s, 5.1, 1.42, 4.4, 2.7, '페라이트', [
    dict(t='교재 식 2.62: E ∝ ωμI → 같은 E를 1/μ의 전류로. 교재 예(400 kHz)에서 전류 약 1/60, 효율 약 99%, 점화가 어렵다 (문헌)', after=6),
    dict(t='13.56 MHz에서는 손실이 커질 것 (추정) → 코일 뒤 요크로 M_{12}와 장 중첩을 줄이는 보조로만')], kind='g', size=13)
panel(s, 5.1, 4.27, 4.4, 1.15, '보조 루프 구성', [
    '자석 전류는 압력별 고정값, 분배가 한계에 가까울 때만 천천히 옮긴다'], kind='g', size=13)
foot(s, 'D_{⊥} = D / [1 + (ω_{ce}/ν_{m})^{2}] (L&L 5장), λ_{ε⊥} ≈ λ_{ε} / √(1 + (ω_{ce}/ν_{m})^{2})로 가정. T_{e} ≈ 2.5 eV, ν_{m} = n_{g}K_{el}. 선행 사례: 축 방향 수 G 자기장으로 분포가 뒤집힘 (GEC 2025 초록, 2D 유체 계산)', y=5.6, h=0.6)
notes(s, '자기장은 가열 위치가 아니라 수송을 바꾸는 손잡이라, 저압에서 g_R을 키워 독립 전원의 분배 조작이 다시 효과를 갖게 하는 것이 상승 효과다. 대가는 자화 수송을 다루는 2D 모델과 자기장 측정이 추가된다는 것이다. 운전 압력을 15 mTorr 아래로 내려야 할 때만 더한다.')

# =================================================================== B3 transients
s = new('bk_transient', '백업 B3 · 과도 상황 (질문 4-3)', '과도는 점화, 레시피 변경, 위상 드리프트에서', '백업')
rows = [['상황', '무엇이 바뀌나', '대응'],
        ['점화와 E→H 전이', 'E 모드에선 분포가 축전 결합을 따르고 전이 때 h_{R} 급변, 이력 (교재 그림 2.44)', '안쪽 코일로 점화, H 모드 확인 뒤 바깥 전원, 그 뒤 바깥 루프'],
        ['레시피 변경', '압력·기체가 바뀌면 λ_{ε}, h, T_{e}가 바뀌어 J 자체가 바뀐다 (g_{R} 0.27 → 0.85)', '압력별 J 표로 이득 스케줄링, 압력 안정 뒤 루프 재개'],
        ['한쪽 전원 변경', 'M_{12}로 다른 쪽 정합이 틀어져 반사 전력이 잠시 는다', '전류 루프가 먼저 잡고 정합기는 위치표로'],
        ['위상 드리프트', '정합 상태에 따라 코일 전류 위상이 움직여 교환 전력이 생긴다', '코일 전류 위상을 직접 재서 보정 (0°에서 약 ±20° 안)'],
        ['분배를 극단으로', '약한 쪽 영역의 가열이 축전 결합 쪽으로 기울 수 있다', '분배 하한을 실험으로 정함 (추정)'],
        ['느린 드리프트', '창 가열, 벽 증착으로 h와 코일 저항이 변한다', '바깥 루프의 적분 동작']]
table(s, 0.5, 1.42, [1.7, 4.0, 3.3], rows, size=11.5, row_h=0.6, first_col_bold=True, row_heights=[0.38] + [0.66] * 6)
foot(s, 'H 모드 유지에는 최소 코일 전류가 있다 (교재 2.4.1절). 레시피 단계가 수 초 이하이거나 펄스 운전이면 피드포워드 표의 정확도가 성능을 정한다', y=6.32, h=0.45)
notes(s, '레시피 단계가 수십 초 이상이면 느린 바깥 루프로 손해가 없다. 단계가 수 초 이하이거나 펄스 운전이면 바깥 루프는 따라가지 못하고, 피드포워드 표의 정확도가 성능을 정한다.')

# =================================================================== B4 matching
s = new('bk_matching', '백업 B4 · 정합기 상호작용', '바깥 전류를 바꾸면 안쪽 정합이 가장 많이 움직인다', '백업')
tb(s, 0.5, 1.42, 9.0, 0.6, ['전원 1이 보는 임피던스 = 자기 임피던스 + (jωM_{12} + ΔZ_{12})·I_{2}/I_{1}', dict(t='단일 턴, 네 동작점 범위, 플라즈마 상호 리액턴스 X′_{12} 포함 (계산)', size=11.5, color=C['MUTED'])], size=13)
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
foot(s, 'L_{1} ≈ 379 nH, L_{2} ≈ 863 nH, M_{12} ≈ 91 nH (결합 계수 0.16, ωM_{12} ≈ 7.8 Ω), 단일 턴 코일 (계산). 전원 사양: 반사 전력 내성, 외부 기준 클록 입력', y=6.1, h=0.45)
notes(s, '독립 전원 구조의 대가 중 하나다. 분배를 바꾸면 상대 코일의 전류가 상호 인덕턴스를 통해 입력 임피던스를 바꾼다. 0°에서 R ≈ 1을 만드는 k ≈ 2 동작점에서는 안쪽 코일 리액턴스가 13–24% 늘어난다(플라즈마 상호 리액턴스 포함, 코일 항만 보면 약 절반). 그래서 바깥 전류를 바꿀 때 안쪽 정합이 가장 많이 움직인다. 반대 방향은 작다.\n'
         '대책 세 가지는 V1에서 효과를 계산한 뒤 고른다. 전원은 상대 전원이 밀어 넣는 교환 전력을 과도 상태에서 견뎌야 하므로 반사 전력 내성과 외부 기준 클록 입력이 사양에 들어간다.')

# =================================================================== B5 question map
s = new('bk_qmap', '백업 B5 · 질문 대응표', '질문·검토 사항·제출물이 답해지는 곳', '백업')
q = [['팀 질문', '쪽'],
     ['1-1 – 1-4 챔버 모델 (2D, 0D, 영역 분할)', '§model§'],
     ['1-5 안테나 수·배치, 챔버 크기', '§geometry§'],
     ['1-6 밀도 측정', '§measure§'],
     ['1-7 반응 테이블', 'B1'],
     ['2-1 단일 vs 다중 코일, 전원 수', '§candidates§, §arch§'],
     ['2-2 코일 2개의 이점, 180° 위상', '§phase_why§, §phase_cmp§'],
     ['2-3 턴 수와 간격', '§geometry§'],
     ['2-4 독립 전원 vs 가변 C, 보조 수단', '§candidates§, B2'],
     ['2-5 세부 구조, 위상 여유', '§phase_why§, §control§'],
     ['3-1 – 3-3 보조 루프, 최종 구조', '§arch§, B2'],
     ['4-1 / 4-2 / 4-3 상황, 과도', '§task§ / §control§ / B3']]
t = [['과제 항목', '쪽'],
     ['검토 1 수단 조합과 영향 영역', '§litmap§, §chain§, §candidates§'],
     ['검토 2 상호 영향의 원인', '§chain§, §scales§, §triangle§'],
     ['검토 3 조작 순서와 보상', '§procedure§'],
     ['검토 4 비율 확인, 전체/분포 구분', '§measure§'],
     ['제출물 ① 소스·구동부 구성도', '§arch§'],
     ['제출물 ② 조작 변수 → 밀도 응답', '§triangle§, §procedure§'],
     ['제출물 ③ 목표 비율 조정 절차', '§procedure§'],
     ['제출물 ④ 측정 계획', '§measure§'],
     ['공통: 가정·대안·부작용·검증', '§candidates§, §verify§, §risks§']]
q = [[R(c) for c in r] for r in q]; t = [[R(c) for c in r] for r in t]
table(s, 0.5, 1.42, [3.25, 1.2], q, size=11, row_h=0.4, col_align=['l', 'c'])
table(s, 5.0, 1.42, [3.2, 1.3], t, size=11, row_h=0.4, col_align=['l', 'c'])
foot(s, '팀 질문 번호는 「프로젝트에 대한 생각」, 과제 항목은 IC-PBL 주제안 3번', y=6.4)
notes(s, '질의응답 때 질문 번호로 바로 해당 슬라이드를 찾아갈 수 있게 만든 표다.')

# =================================================================== finish
assert [k for k in ORDER] == list(built.keys()), (list(built.keys()))
cp = prs.core_properties
cp.title = '중앙·가장자리 밀도비의 독립 제어 — 1차 발표'
cp.author = '주제 3 팀'; cp.last_modified_by = '주제 3 팀'; cp.subject = '플라즈마 전자공학 IC-PBL 주제 3'
cp.keywords = ''; cp.comments = ''; cp.category = ''
cp.revision = 1
import datetime
cp.created = datetime.datetime(2026, 11, 5, 12, 0, 0); cp.modified = datetime.datetime(2026, 11, 5, 12, 0, 0)
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
