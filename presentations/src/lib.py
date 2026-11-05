"""python-pptx helpers for decks built on the course template (4:3, Hanyang PEL)."""
import re, json, copy, uuid
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.dml import MSO_LINE
from pptx.oxml.ns import qn
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml import parse_xml

EA_FONT = '맑은 고딕'
LATIN = 'Arial'

C = dict(
    INDIGO='333399', NAVY='004483', BLUE='3366CC', ORANGE='D9622B', ORANGE_D='B24A16',
    TEXT='222222', MUTED='5F6779', LINE='C9CED8', PANEL='F2F4F8', BLUE_L='E8EEF9',
    ORANGE_L='FBEDE4', NAVY_L='E3ECF4', WHITE='FFFFFF', GRAY='8C93A3', GRAY_L='ECEEF2',
    INDIGO_L='ECECF7', GREEN='2E7D4F', EQ='1F2340', AMBER='8A5A00', AMBER_L='FFF3D6', TARGET='E6E2F4',
    DARK='3B4658',
)

def I(v):
    return Emu(int(round(v * 914400)))

def rgb(h):
    return RGBColor.from_string(h)

# ---------------------------------------------------------------- text
TOKEN = re.compile(r'\*\*(.+?)\*\*|\[\[(\w):(.+?)\]\]|_\{(.+?)\}|\^\{(.+?)\}')
CMAP = {'o': 'ORANGE_D', 'b': 'BLUE', 'n': 'NAVY', 'i': 'INDIGO', 'm': 'MUTED', 'g': 'GREEN', 'w': 'WHITE', 'a': 'AMBER', 'd': 'DARK'}

def parse(text, style=None):
    style = dict(style or {})
    out, pos = [], 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], style))
        if m.group(1) is not None:
            out += parse(m.group(1), {**style, 'bold': True})
        elif m.group(2) is not None:
            out += parse(m.group(3), {**style, 'bold': True, 'color': C[CMAP[m.group(2)]]})
        elif m.group(4) is not None:
            out += parse(m.group(4), {**style, 'baseline': '-25000'})
        else:
            out += parse(m.group(5), {**style, 'baseline': '30000'})
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], style))
    return out

def style_run(r, size=None, bold=None, color=None, baseline=None, italic=None, font=LATIN):
    f = r.font
    if size: f.size = Pt(size)
    if bold is not None: f.bold = bold
    if italic: f.italic = True
    if color: f.color.rgb = rgb(color)
    f.name = font
    rPr = r._r.get_or_add_rPr()
    rPr.set('lang', 'ko-KR'); rPr.set('altLang', 'en-US')
    if baseline: rPr.set('baseline', baseline)
    latin = rPr.find(qn('a:latin'))
    for old in rPr.findall(qn('a:ea')):
        rPr.remove(old)
    ea = OxmlElement('a:ea'); ea.set('typeface', EA_FONT)
    latin.addnext(ea)

def set_bullet(p, char='•', indent=0.17, color=None):
    pPr = p._p.get_or_add_pPr()
    pPr.set('marL', str(I(indent))); pPr.set('indent', str(-I(indent)))
    for tag in ('a:buNone', 'a:buChar', 'a:buFont', 'a:buClr', 'a:buAutoNum'):
        for e in pPr.findall(qn(tag)):
            pPr.remove(e)
    if color:
        buClr = OxmlElement('a:buClr'); s = OxmlElement('a:srgbClr'); s.set('val', color); buClr.append(s)
        pPr.append(buClr)
    buFont = OxmlElement('a:buFont'); buFont.set('typeface', 'Arial'); pPr.append(buFont)
    bu = OxmlElement('a:buChar'); bu.set('char', char); pPr.append(bu)

def no_bullet(p):
    pPr = p._p.get_or_add_pPr()
    if pPr.find(qn('a:buNone')) is None:
        pPr.append(OxmlElement('a:buNone'))

def write(tf, paras, size=14, color=None, bold=False, align='l', space_after=4,
          line=1.0, bullet=False, bullet_color=None):
    """paras: list of str or dict(t=, size=, color=, bold=, bullet=, align=, after=, before=)."""
    color = color or C['TEXT']
    if isinstance(paras, str):
        paras = [paras]
    first = True
    for item in paras:
        d = item if isinstance(item, dict) else {'t': item}
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        al = d.get('align', align)
        p.alignment = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT}[al]
        p.space_after = Pt(d.get('after', space_after))
        if d.get('before'):
            p.space_before = Pt(d['before'])
        p.line_spacing = d.get('line', line)
        if d.get('bullet', bullet):
            set_bullet(p, d.get('char', '•'), d.get('indent', 0.17), d.get('bullet_color', bullet_color))
        else:
            no_bullet(p)
        sz = d.get('size', size)
        for txt, st in parse(d['t']):
            r = p.add_run(); r.text = txt
            style_run(r, size=sz, bold=st.get('bold', d.get('bold', bold)),
                      color=st.get('color', d.get('color', color)), baseline=st.get('baseline'),
                      italic=d.get('italic'))
    return tf

def _strip_style(shape):
    st = shape._element.find(qn('p:style'))
    if st is not None:
        shape._element.remove(st)

def tb(slide, x, y, w, h, paras, size=14, color=None, bold=False, align='l', anchor='t',
       margin=0.0, space_after=4, line=1.0, bullet=False, name=None, wrap=True, bullet_color=None):
    s = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = s.text_frame
    tf.word_wrap = wrap
    tf.auto_size = MSO_AUTO_SIZE.NONE
    for side in ('left', 'right', 'top', 'bottom'):
        setattr(tf, f'margin_{side}', I(margin))
    tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}[anchor]
    write(tf, paras, size=size, color=color, bold=bold, align=align, space_after=space_after,
          line=line, bullet=bullet, bullet_color=bullet_color)
    if name: s.name = name
    return s

def _alpha(fill_elm, alpha):
    clr = fill_elm.find(qn('a:srgbClr'))
    a = OxmlElement('a:alpha'); a.set('val', str(int(alpha * 1000)))
    clr.append(a)

def box(slide, x, y, w, h, fill=None, line=None, lw=1.0, radius=0.08, shape=None, dash=False,
        paras=None, size=13, color=None, bold=False, align='l', anchor='t', margin=0.1,
        space_after=3, line_sp=1.0, name=None, alpha=None, adj=None, bullet=False):
    if shape is None:
        shape = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    s = slide.shapes.add_shape(shape, I(x), I(y), I(w), I(h))
    _strip_style(s)
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE and radius:
        s.adjustments[0] = min(0.5, radius / min(w, h))
    if adj is not None:
        for i, v in enumerate(adj):
            s.adjustments[i] = v
    if fill:
        s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
        if alpha is not None:
            _alpha(s.fill._xPr.find(qn('a:solidFill')), alpha)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line); s.line.width = Pt(lw)
        if dash: s.line.dash_style = MSO_LINE.DASH
    else:
        s.line.fill.background()
    tf = s.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    for side in ('left', 'right', 'top', 'bottom'):
        setattr(tf, f'margin_{side}', I(margin))
    tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}[anchor]
    if paras:
        write(tf, paras, size=size, color=color, bold=bold, align=align, space_after=space_after,
              line=line_sp, bullet=bullet)
    if name: s.name = name
    return s

def circle(slide, cx, cy, d, fill=None, line=None, lw=1.0, paras=None, size=13, color=None,
           bold=True, name=None):
    return box(slide, cx - d / 2, cy - d / 2, d, d, fill=fill, line=line, lw=lw,
               shape=MSO_SHAPE.OVAL, radius=None, paras=paras, size=size, color=color,
               bold=bold, align='c', anchor='m', margin=0, name=name)

def seg(slide, x1, y1, x2, y2, color=None, w=1.5, dash=False, head=False, tail=False, name=None):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, I(x1), I(y1), I(x2), I(y2))
    _strip_style(c)
    c.line.color.rgb = rgb(color or C['NAVY'])
    c.line.width = Pt(w)
    if dash:
        c.line.dash_style = MSO_LINE.DASH
    ln = c.line._get_or_add_ln()
    if tail:
        e = OxmlElement('a:headEnd'); e.set('type', 'triangle'); e.set('w', 'med'); e.set('len', 'med'); ln.append(e)
    if head:
        e = OxmlElement('a:tailEnd'); e.set('type', 'triangle'); e.set('w', 'med'); e.set('len', 'med'); ln.append(e)
    if name: c.name = name
    return c

def path(slide, pts, color=None, w=1.5, dash=False, head=True, tail=False):
    for i in range(len(pts) - 1):
        seg(slide, *pts[i], *pts[i + 1], color=color, w=w, dash=dash,
            head=head and i == len(pts) - 2, tail=tail and i == 0)

def pic(slide, path_, x, y, w=None, h=None, name=None):
    s = slide.shapes.add_picture(path_, I(x), I(y), I(w) if w else None, I(h) if h else None)
    if name: s.name = name
    return s

# ---------------------------------------------------------------- equations
EQ_DIR = None
EQ_SIZES = {}

def eq(slide, name, x, y, pt=18, align='l', box_w=None):
    """Place equation image so that 40px KaTeX text renders at about `pt` points."""
    s = EQ_SIZES[name]
    scale = pt / 30.0  # 40 px CSS = 30 pt
    w = s['w'] / 96 * scale
    h = s['h'] / 96 * scale
    if box_w is not None and align == 'c':
        x = x + (box_w - w) / 2
    shp = pic(slide, f'{EQ_DIR}/{name}.png', x, y, w=w, h=h, name=f'수식 {name}')
    return shp, w, h

# ---------------------------------------------------------------- tables
NO_STYLE = '{2D5ABB26-0587-4C30-8999-92F81FD0307C}'

def _border(tcPr, side, color, w):
    tag = {'L': 'a:lnL', 'R': 'a:lnR', 'T': 'a:lnT', 'B': 'a:lnB'}[side]
    ln = OxmlElement(tag)
    if color:
        ln.set('w', str(int(w * 12700))); ln.set('cap', 'flat'); ln.set('cmpd', 'sng')
        sf = OxmlElement('a:solidFill'); c = OxmlElement('a:srgbClr'); c.set('val', color); sf.append(c); ln.append(sf)
        d = OxmlElement('a:prstDash'); d.set('val', 'solid'); ln.append(d)
    else:
        ln.set('w', '0'); ln.append(OxmlElement('a:noFill'))
    return ln

def cell_borders(cell, L=None, R=None, T=None, B=None):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ('a:lnL', 'a:lnR', 'a:lnT', 'a:lnB'):
        for e in tcPr.findall(qn(tag)):
            tcPr.remove(e)
    items = [_border(tcPr, s, *(v if v else (None, 0))) for s, v in (('L', L), ('R', R), ('T', T), ('B', B))]
    for i, e in enumerate(items):
        tcPr.insert(i, e)

def table(slide, x, y, col_w, rows, size=12, header=True, row_h=0.3, header_fill=None,
          header_color='FFFFFF', header_size=None, fills=None, col_align=None, valign='m',
          first_col_bold=False, line_color=None, margin=0.06, name=None, row_heights=None,
          col_fills=None, colors=None, bold_cells=None):
    nr, nc = len(rows), len(col_w)
    gf = slide.shapes.add_table(nr, nc, I(x), I(y), I(sum(col_w)), I(row_h * nr))
    tbl = gf.table
    tblPr = tbl._tbl.tblPr
    sid = tblPr.find(qn('a:tableStyleId'))
    if sid is None:
        sid = OxmlElement('a:tableStyleId'); tblPr.append(sid)
    sid.text = NO_STYLE
    tblPr.set('firstRow', '1' if header else '0'); tblPr.set('bandRow', '0')
    for j, w in enumerate(col_w):
        tbl.columns[j].width = I(w)
    for i in range(nr):
        tbl.rows[i].height = I(row_heights[i] if row_heights else row_h)
    header_fill = header_fill or C['NAVY']
    line_color = line_color or C['LINE']
    fills = fills or {}
    for i, row in enumerate(rows):
        for j in range(nc):
            val = row[j] if j < len(row) else ''
            cell = tbl.cell(i, j)
            cell.margin_left = I(margin); cell.margin_right = I(margin)
            cell.margin_top = I(0.04); cell.margin_bottom = I(0.04)
            cell.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE}[valign]
            is_h = header and i == 0
            if is_h:
                f = fills.get((i, j), header_fill)
            else:
                f = fills.get((i, j)) or (col_fills or {}).get(j)
            if f:
                cell.fill.solid(); cell.fill.fore_color.rgb = rgb(f)
            else:
                cell.fill.background()
            al = (col_align[j] if col_align else 'l')
            d = val if isinstance(val, dict) else {'t': str(val)}
            tf = cell.text_frame
            tf.word_wrap = True
            col = header_color if is_h else (colors or {}).get((i, j), C['TEXT'])
            bold = is_h or (first_col_bold and j == 0) or ((i, j) in (bold_cells or ()))
            paras = d.get('paras') or [d]
            write(tf, paras,
                  size=d.get('size', (header_size or size) if is_h else size), color=d.get('color', col),
                  bold=d.get('bold', bold), align=d.get('align', al), space_after=d.get('after', 0), line=1.0)
            bottom = (C['NAVY'], 1.25) if is_h else (line_color, 0.75)
            cell_borders(cell, L=None, R=None, T=None, B=bottom)
    if name: gf.name = name
    return gf

# ---------------------------------------------------------------- charts
def chart_no_fill(chart):
    cs = chart._chartSpace
    for old in cs.findall(qn('c:spPr')):
        cs.remove(old)
    spPr = parse_xml('<c:spPr xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart" '
                     'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                     '<a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>')
    txPr = cs.find(qn('c:txPr'))
    if txPr is not None:
        txPr.addprevious(spPr)
    else:
        cs.find(qn('c:chart')).addnext(spPr)
    pa = cs.find(qn('c:chart')).find(qn('c:plotArea'))
    for old in pa.findall(qn('c:spPr')):
        pa.remove(old)
    spPr2 = copy.deepcopy(spPr)
    ext = pa.find(qn('c:extLst'))
    if ext is not None:
        ext.addprevious(spPr2)
    else:
        pa.append(spPr2)

def plot_layout(chart, x, y, w, h):
    pa = chart._chartSpace.find(qn('c:chart')).find(qn('c:plotArea'))
    for old in pa.findall(qn('c:layout')):
        pa.remove(old)
    lay = parse_xml('<c:layout xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart">'
                    '<c:manualLayout><c:layoutTarget val="inner"/><c:xMode val="edge"/><c:yMode val="edge"/>'
                    f'<c:x val="{x}"/><c:y val="{y}"/><c:w val="{w}"/><c:h val="{h}"/></c:manualLayout></c:layout>')
    pa.insert(0, lay)

def axis_title(axis, text, size=11, color=None):
    axis.has_title = True
    tf = axis.axis_title.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    for txt, st in parse(text):
        r = p.add_run(); r.text = txt
        style_run(r, size=size, bold=False, color=color or C['MUTED'], baseline=st.get('baseline'))

def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text

def slide_number(slide, num, x=8.9, y=7.06, w=0.55, h=0.26, size=10):
    s = slide.shapes.add_textbox(I(x), I(y), I(w), I(h))
    tf = s.text_frame
    for side in ('left', 'right', 'top', 'bottom'):
        setattr(tf, f'margin_{side}', 0)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT
    fld = OxmlElement('a:fld'); fld.set('id', '{' + str(uuid.uuid4()).upper() + '}'); fld.set('type', 'slidenum')
    rPr = OxmlElement('a:rPr'); rPr.set('lang', 'en-US'); rPr.set('sz', str(size * 100))
    sf = OxmlElement('a:solidFill'); c = OxmlElement('a:srgbClr'); c.set('val', C['MUTED']); sf.append(c); rPr.append(sf)
    la = OxmlElement('a:latin'); la.set('typeface', LATIN); rPr.append(la)
    fld.append(rPr)
    t = OxmlElement('a:t'); t.text = str(num); fld.append(t)
    p._p.append(fld)
    s.name = '쪽 번호'
    return s
