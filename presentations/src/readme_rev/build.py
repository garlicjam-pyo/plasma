"""README 지시에 따라 표지와 슬라이드 3–10을 다시 만든다 (기존 양식 유지, 0D 부분은 교재 식으로, 임피던스는 2D로 넘김)."""
import os
import re
import shutil
from xml.sax.saxutils import escape
from PIL import Image

U = "un"                      # 풀어 둔 pptx
EQ = "eq3"                    # 새 식·도식 PNG
NAVY, SUB, INK, HEAD, LINE = "303399", "4C5B72", "17263C", "004680", "D8E1EB"
BLUE, ORANGE, ORANGE_T = "3366CC", "D9622B", "B24A16"
FONT = '<a:latin typeface="Arial"/><a:ea typeface="맑은 고딕"/>'


# ---------- 텍스트 ----------
def runs(markup, sz, color=INK, bold=False):
    """간단한 표기: **굵게**, _{아래첨자}, ^{위첨자}, [[HEX|글자]] 색 지정."""
    out = []
    pat = re.compile(r"\*\*(.+?)\*\*|_\{(.+?)\}|\^\{(.+?)\}|\[\[([0-9A-F]{6})\|(.+?)\]\]")
    pos = 0

    def r(t, b=bold, base=None, col=color):
        if not t:
            return
        bl = f' baseline="{base}"' if base else ""
        out.append(f'<a:r><a:rPr lang="ko-KR" altLang="en-US" sz="{sz}" b="{1 if b else 0}"{bl} dirty="0">'
                   f'<a:solidFill><a:srgbClr val="{col}"/></a:solidFill>{FONT}</a:rPr><a:t>{escape(t)}</a:t></a:r>')
    for m in pat.finditer(markup):
        r(markup[pos:m.start()])
        if m.group(1) is not None:
            r(m.group(1), b=True)
        elif m.group(2) is not None:
            r(m.group(2), base="-25000")
        elif m.group(3) is not None:
            r(m.group(3), base="30000")
        else:
            r(m.group(5), col=m.group(4))
        pos = m.end()
    r(markup[pos:])
    return "".join(out)


def para(markup, sz=1350, color=INK, bold=False, bullet=False, algn="l", aft=400):
    if bullet:
        ppr = (f'<a:pPr marL="155448" indent="-155448" algn="{algn}"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc>'
               f'<a:spcAft><a:spcPts val="{aft}"/></a:spcAft><a:buFont typeface="Arial"/><a:buChar char="•"/></a:pPr>')
    else:
        ppr = (f'<a:pPr algn="{algn}"><a:lnSpc><a:spcPct val="100000"/></a:lnSpc>'
               f'<a:spcAft><a:spcPts val="{aft}"/></a:spcAft><a:buNone/></a:pPr>')
    return f"<a:p>{ppr}{runs(markup, sz, color, bold)}</a:p>"


class Slide:
    def __init__(self):
        self.items, self.nid, self.pics = [], 2, []

    def id(self):
        self.nid += 1
        return self.nid

    def title(self, text):
        self.items.append('<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title 1"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
                          '<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>'
                          f'<a:p><a:r><a:rPr lang="ko-KR" altLang="en-US" sz="2400" dirty="0"/><a:t>{escape(text)}</a:t></a:r></a:p>'
                          '</p:txBody></p:sp>')

    def box(self, name, x, y, w, h, paras, fill=None, line=None, inset=0, anchor="t", wrap="square"):
        i = self.id()
        f = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
        ln = (f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>' if line
              else ("<a:ln><a:noFill/></a:ln>" if fill else ""))
        tx = ' txBox="1"' if not (fill or line) else ""
        body = "".join(paras) if paras else '<a:p><a:pPr algn="ctr"/><a:endParaRPr/></a:p>'
        self.items.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="{escape(name)}"/><p:cNvSpPr{tx}/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{f}{ln}</p:spPr>'
            f'<p:txBody><a:bodyPr wrap="{wrap}" lIns="{inset}" tIns="{inset}" rIns="{inset}" bIns="{inset}" rtlCol="0" anchor="{anchor}"><a:noAutofit/></a:bodyPr>'
            f'<a:lstStyle/>{body}</p:txBody></p:sp>')

    def card(self, name, x, y, w, h, paras, accent=HEAD):
        self.box(name, x, y, w, h, paras, line=LINE, inset=109728)
        self.box(name + " 강조선", x, y, w, 36576, None, fill=accent)

    def shape(self, prst, name, x, y, w, h, fill=None, line=None):
        i = self.id()
        f = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
        ln = f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>' if line else "<a:ln><a:noFill/></a:ln>"
        self.items.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="{escape(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="{prst}"><a:avLst/></a:prstGeom>{f}{ln}</p:spPr>'
            '<p:txBody><a:bodyPr rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p><a:pPr algn="ctr"/><a:endParaRPr/></a:p></p:txBody></p:sp>')

    def line(self, name, x, y, w, h, color, width=12700):
        i = self.id()
        self.items.append(
            f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{i}" name="{escape(name)}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
            f'<a:ln w="{width}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:ln></p:spPr></p:cxnSp>')

    def arrow(self, name, x, y, w, color=SUB, width=15875):
        """수평 화살표 (오른쪽 끝에 삼각형)."""
        i = self.id()
        self.items.append(
            f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{i}" name="{escape(name)}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="0"/></a:xfrm><a:prstGeom prst="straightConnector1"><a:avLst/></a:prstGeom>'
            f'<a:ln w="{width}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:tailEnd type="triangle" w="med" len="med"/></a:ln></p:spPr></p:cxnSp>')

    def eq(self, media, x, y, emu_per_px=1900, max_w=None, max_h=None, center_w=None):
        """media: ppt/media 안의 파일 이름. 크기는 픽셀×비율, 넘치면 줄인다."""
        pw, ph = Image.open(f"{U}/ppt/media/{media}").size
        s = emu_per_px
        if max_w and pw * s > max_w:
            s = max_w / pw
        if max_h and ph * s > max_h:
            s = max_h / ph
        w, h = int(pw * s), int(ph * s)
        if center_w:
            x = x + (center_w - w) // 2
        i = self.id()
        self.pics.append(media)
        rid = f"rIdP{len(self.pics)}"
        self.items.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{i}" name="{"그림" if media.startswith("fig_") else "수식"} {media[:-4]}" descr="{media}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')
        return w, h

    # 슬라이드 공통 틀 (기존 슬라이드 5와 같은 위치·서식)
    def frame(self, title, subtitle, message, footnote=None):
        self.title(title)
        self.box("소제목", 457200, 960120, 8193024, 283464, [para(subtitle, 1200, SUB, True)])
        self.box("구분선", 457200, 5413248, 8229600, 11430, None, fill=NAVY)
        self.box("핵심 메시지", 457200, 5495544, 8238744, 457200, [para(message, 1600, NAVY, True)], anchor="ctr")
        if footnote:
            self.box("각주", 457200, 5998464, 7726680, 256032, [para(footnote, 1050, SUB)])

    def pagenum(self):
        i = self.id()
        self.items.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="쪽 번호"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr><a:xfrm><a:off x="8266176" y="6044184"/>'
            '<a:ext cx="411480" cy="210312"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody>'
            '<a:bodyPr wrap="none" lIns="0" tIns="0" rIns="0" bIns="0"><a:spAutoFit/></a:bodyPr><a:lstStyle/><a:p><a:pPr algn="r"/>'
            '<a:fld id="{1A97B99E-87CE-4EB6-9491-B00F01881557}" type="slidenum"><a:rPr lang="en-US" sz="1050"><a:solidFill><a:srgbClr val="4C5B72"/>'
            '</a:solidFill><a:latin typeface="Arial"/></a:rPr><a:t>‹#›</a:t></a:fld><a:endParaRPr lang="en-US" sz="1050"><a:solidFill>'
            '<a:srgbClr val="4C5B72"/></a:solidFill><a:latin typeface="Arial"/></a:endParaRPr></a:p></p:txBody></p:sp>')

    def write(self, n):
        path = f"{U}/ppt/slides/slide{n}.xml"
        x = open(path, encoding="utf-8").read()
        head = re.search(r"^.*?<p:spTree>.*?</p:grpSpPr>", x, re.S).group(0)
        tail = x[x.index("</p:spTree>"):]
        open(path, "w", encoding="utf-8").write(head + "".join(self.items) + tail)
        rp = f"{U}/ppt/slides/_rels/slide{n}.xml.rels"
        rels = open(rp, encoding="utf-8").read()
        keep = [m for m in re.findall(r"<Relationship [^>]*/>", rels) if "/image" not in m]
        for k, media in enumerate(self.pics, 1):
            keep.append(f'<Relationship Id="rIdP{k}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{media}"/>')
        open(rp, "w", encoding="utf-8").write(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + "".join(keep) + "</Relationships>")


def notes(slide_n, script_head, script, basis):
    rp = f"{U}/ppt/slides/_rels/slide{slide_n}.xml.rels"
    nf = re.search(r'Target="\.\./notesSlides/([^"]+)"', open(rp, encoding="utf-8").read()).group(1)
    path = f"{U}/ppt/notesSlides/{nf}"
    x = open(path, encoding="utf-8").read()
    body = "".join(f"<a:p><a:r><a:t>{escape(t)}</a:t></a:r></a:p>" if t else "<a:p><a:endParaRPr/></a:p>"
                   for t in [script_head, script, "", "[근거(읽지 않음)]", basis])
    x = re.sub(r'(<p:ph type="body"[^>]*/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>).*?(</p:txBody>)',
               lambda m: m.group(1) + body + m.group(2), x, count=1, flags=re.S)
    open(path, "w", encoding="utf-8").write(x)



import json

# 새 식·도식 PNG를 media로 복사
for f in os.listdir(EQ):
    if f.endswith(".png") and (f.startswith("n_") or f.startswith("fig_")):
        shutil.copy(f"{EQ}/{f}", f"{U}/ppt/media/{'eq_' + f[2:] if f.startswith('n_') else f}")
SPANS = json.load(open(f"{EQ}/pe3_spans.json"))

L, R, W = 457200, 8686800, 8229600   # 좌우 여백, 본문 폭
TOP, BOT = 1335000, 5310000          # 본문 위·아래 끝
CW = 4023360                         # 2단 카드 폭
X2 = L + CW + 182880                 # 오른쪽 카드 x
T1, B1, S1 = 1600, 1400, 1250        # 패널 제목, 본문, 표기 글자 크기


# ---------- 공통 도식 ----------
def chamber(s, c0, regions=False, currents=False):
    """반단면 개략도. c0 = 코일 윗변 y. 축 r = 0(왼쪽)에서 측벽(오른쪽)까지."""
    x0, cwid = 548640, 3840480
    s.shape("rect", "유전체 창", x0, c0 + 196596, cwid, 365760, fill="D6E2F0")
    s.shape("rect", "플라즈마", x0, c0 + 539496, cwid, 1097280, fill="F7F9FC")
    s.shape("rect", "웨이퍼", x0, c0 + 1613916, 2743200, 45720, fill="5F6779")
    s.line("측벽", x0 + cwid, c0 + 562356, 0, 1097280, INK)
    s.line("바닥", x0, c0 + 1659636, cwid, 0, INK)
    s.line("축", x0, c0 - 41148, 0, 1700784, "8C93A3")
    for k, xx in enumerate([1028700, 1577340, 2125980, 2674620, 3223260, 3771900]):
        s.shape("ellipse", f"코일 {k + 1}", xx, c0, 137160, 137160, fill=BLUE if k < 3 else ORANGE)
    s.box("창 표기", x0, c0 + 196596, cwid, 365760, [para("유전체 창", S1, SUB, algn="ctr", aft=0)], anchor="ctr")
    s.box("플라즈마 표기", x0, c0 + 640000, cwid, 230000, [para("플라즈마", S1, SUB, algn="ctr", aft=0)])
    s.box("웨이퍼 표기", 1560000, c0 + 1613916 - 245000, 1100000, 230000, [para("웨이퍼", S1, SUB, algn="ctr", aft=0)])
    if regions:
        s.shape("rect", "중앙 영역", x0, c0 + 1399032, 914400, 73152, fill=BLUE)
        s.shape("rect", "가장자리 영역", 2743200, c0 + 1399032, 457200, 73152, fill=ORANGE)
        s.box("n_c 표기", 566928, c0 + 1120000, 914400, 290000, [para("n_{c}", 1500, BLUE, True)])
        s.box("n_edge 표기", 2697480, c0 + 1120000, 1000000, 290000, [para("n_{edge}", 1500, ORANGE_T, True)])
        s.box("관측면 표기", 3291840, c0 + 1356900, 1050000, 230000, [para("z = z_{w}", S1, SUB)])
        for lab, xx in [("0", x0), ("r_{c}", 1463040), ("r_{1}", 2743200), ("r_{2}", 3200400)]:
            s.box(f"반경 {lab}", xx - 228600, c0 + 1696900, 457200, 230000, [para(lab, S1, SUB, algn="ctr")])
    if currents:
        s.box("안쪽 전류", 1028700 - 300000, c0 - 330000, 1371600 + 600000, 280000,
              [para("I_{in}", 1600, BLUE, True, algn="ctr", aft=0)])
        s.box("바깥쪽 전류", 2674620 - 300000, c0 - 330000, 1371600 + 600000, 280000,
              [para("I_{out}", 1600, ORANGE_T, True, algn="ctr", aft=0)])


def chain(s, y, h, items, name, gap_min=240000, sz=(S1, B1)):
    """가로 사슬: 상자 n개 + 사이 화살표. items = [(윗줄, 아랫줄), ...]"""
    n = len(items)
    bw = (W - (n - 1) * gap_min) // n
    gap = (W - n * bw) // (n - 1)
    for k, (top, bot) in enumerate(items):
        x = L + k * (bw + gap)
        s.box(f"{name} {k + 1}", x, y, bw, h,
              [para(top, sz[0], SUB, algn="ctr", aft=0), para(bot, sz[1], INK, True, algn="ctr", aft=0)],
              line="8C93A3", anchor="ctr")
        if k < n - 1:
            s.arrow(f"{name} 화살표 {k + 1}", x + bw + 30000, y + h // 2, gap - 60000, width=19050)


def io_strip(s, y, inputs, system, caption):
    """입력 → 장치 → 출력 도식과 그 아래 한 줄 결론."""
    bh, wi, ws = 640000, 2194560, 2560320
    g = (W - 2 * wi - ws) // 2
    xs = [L, L + wi + g, L + wi + g + ws + g]
    s.box("입력", xs[0], y, wi, bh, [para("입력", S1, SUB, algn="ctr", aft=0), para(inputs, 1800, INK, True, algn="ctr", aft=0)],
          line="8C93A3", anchor="ctr")
    s.box("장치", xs[1], y, ws, bh, [para(system, T1, "FFFFFF", True, algn="ctr", aft=0)], fill=HEAD, anchor="ctr")
    s.box("출력", xs[2], y, wi, bh, [para("출력", S1, SUB, algn="ctr", aft=0), para("n̄_{w},  ρ", 1800, INK, True, algn="ctr", aft=0)],
          line="8C93A3", anchor="ctr")
    s.arrow("입력 화살표", xs[0] + wi + 50000, y + bh // 2, g - 100000, color=INK, width=25400)
    s.arrow("출력 화살표", xs[1] + ws + 50000, y + bh // 2, g - 100000, color=INK, width=25400)
    s.box("입출력 결론", L, y + bh + 90000, W, BOT - (y + bh + 90000), [para(caption, 1500, INK, algn="ctr", aft=0)])


# slide10에는 노트가 없으므로 기존 노트 하나를 복사해 연결한다
nn = "notesSlide50.xml"
shutil.copy(f"{U}/ppt/notesSlides/notesSlide6.xml", f"{U}/ppt/notesSlides/{nn}")
open(f"{U}/ppt/notesSlides/_rels/{nn}.rels", "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../slides/slide10.xml"/>'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster" Target="../notesMasters/notesMaster1.xml"/>'
    '</Relationships>')
ctp = f"{U}/[Content_Types].xml"
ct = open(ctp, encoding="utf-8").read()
if nn not in ct:
    ct = ct.replace("</Types>", f'<Override PartName="/ppt/notesSlides/{nn}" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/></Types>')
    open(ctp, "w", encoding="utf-8").write(ct)
rp10 = f"{U}/ppt/slides/_rels/slide10.xml.rels"
r10 = open(rp10, encoding="utf-8").read()
if nn not in r10:
    r10 = r10.replace("</Relationships>", f'<Relationship Id="rIdN1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/{nn}"/></Relationships>')
    open(rp10, "w", encoding="utf-8").write(r10)

# ===================== 1. 표지 (slide1.xml): 부제만 흐름에 맞춤 =====================
p1 = f"{U}/ppt/slides/slide1.xml"
x = open(p1, encoding="utf-8").read()
x = x.replace("<a:t>이론적 배경과 상세 수식 유도 · 핵심 수식판</a:t>",
              "<a:t>문제 정의 · 단일·이중 코일의 0D 기술 · 2D 모델의 필요성</a:t>")
open(p1, "w", encoding="utf-8").write(x)

# ===================== 3. 문제 정의와 제어 목표 (slide4.xml) =====================
s = Slide()
s.frame("문제 정의와 제어 목표", "설계 과제  ·  중앙·가장자리 밀도비의 독립 조절",
        "목표는 평균 밀도 n̄_{w}를 유지하면서 밀도비 ρ를 바꾸는 것이다.",
        "[정의] 면적 평균 ⟨n⟩_{S} = (1/A_{S})∫_{S} n(r, z_{w}) dA, dA = 2πr dr. 경계 r_{c}, r_{1}, r_{2}, R_{w}와 관측 높이 z_{w}는 설계 단계에서 정한다. 부록 A3.")
s.box("과제 문단", L, TOP, W, 950000, [
    para("**문제 정의**  하나의 챔버에서 중앙부와 가장자리의 플라즈마 밀도를 독립적으로 조절하는 소스를 설계한다.", T1, aft=500),
    para("**제어 목표**  밀도비 ρ를 전체 밀도 수준과 따로 조정한다.", T1, aft=0)])
c3 = 2760000
chamber(s, c3, regions=True)
s.box("코일 범례", 548640, c3 + 1960000, 3840480, 260000,
      [para("[[3366CC|●]] 안쪽 코일   [[D9622B|●]] 바깥쪽 코일", S1, SUB, aft=0)])
rx, rw = 4663440, 4023360
# 밀도비 정의
s.box("밀도비 상자", rx, 2560000, rw, 960000, None, fill="EEF3FB")
w, h = s.eq("eq_rho.png", rx + 230000, 2560000 + (960000 - 333 * 1500) // 2, emu_per_px=1500)
s.box("밀도비 설명", rx + 230000 + w + 250000, 2560000, rw - w - 600000, 960000, [
    para("밀도비", T1, HEAD, True, aft=100),
    para("중앙 평균 밀도 ÷ 가장자리 평균 밀도", S1, SUB, aft=0)], anchor="ctr")
# 목표 두 가지
gw = (rw - 137160) // 2
for k, (nm, verb, cond, col) in enumerate([("평균 밀도  n̄_{w}", "유지", "Δn̄_{w} = 0", NAVY),
                                            ("밀도비  ρ", "조절", "Δρ ≠ 0", ORANGE_T)]):
    gx = rx + k * (gw + 137160)
    s.box(f"목표 {k + 1}", gx, 3660000, gw, 1120000, [
        para(nm, B1, SUB, algn="ctr", aft=50),
        para(verb, 2400, col, True, algn="ctr", aft=50),
        para(cond, B1, INK, algn="ctr", aft=0)], line=LINE, anchor="ctr")
    s.box(f"목표 {k + 1} 강조선", gx, 3660000, gw, 45720, None, fill=col)
s.box("평균 설명", rx, 4880000, rw, 420000, [
    para("n_{c}, n_{edge}, n̄_{w}: 각 영역의 면적 평균 밀도", S1, SUB, algn="ctr", aft=0)])
s.pagenum()
s.write(4)

# ===================== 4. 단일 코일 (slide5.xml) =====================
s = Slide()
s.frame("단일 코일 ICP: 입력은 전력 하나", "단일 코일  ·  유도 가열과 0D 균형 (교재 §2.3, §2.4)",
        "단일 코일로는 평균 밀도를 유지한 채 밀도비를 바꿀 수 없다.",
        "정진욱 (2026) 식 (2.31)–(2.32), (2.52), (2.70), (2.73). f(r, z) = ½Re(σ_{p})|Ẽ|², Ẽ: 단위 전류당 E_{θ} (전도도 고정).")
chain(s, TOP, 560000, [("안테나 전류", "I(t)"), ("시변 자속", "dΦ/dt"), ("유도 전기장", "E_{θ}"),
                       ("흡수 옴전력", "p_{e}"), ("이온화", "K_{iz}(T_{e})")], "가열 사슬")
cy4, ch4 = TOP + 690000, 1760000
s.card("가열 카드", L, cy4, CW, ch4, [para("가열 분포: 전류는 크기만 바꾼다", T1, HEAD, True)])
ty4, th4 = cy4 + 520000, 1060000
w, h = s.eq("eq_pelhs.png", L + 130000, ty4 + 150000, emu_per_px=1500)
xa = L + 130000 + w + 90000
wa, wb = 1000000, 1330000
for nm, x, wt, img, hd, body, col in [("크기", xa, wa, "eq_i2.png", "크기", "전류가 정한다", BLUE),
                                      ("모양", xa + wa + 300000, wb, "eq_f.png", "모양", "코일 구조가 정한다", HEAD)]:
    s.box(f"{nm} 타일", x, ty4, wt, th4, None, fill="EEF3FB")
    s.eq(img, x, ty4 + 120000, emu_per_px=1500, center_w=wt)
    s.box(f"{nm} 설명", x, ty4 + 500000, wt, th4 - 520000, [
        para(hd, B1, col, True, algn="ctr", aft=0), para(body, S1, INK, algn="ctr", aft=0)])
s.box("곱하기", xa + wa, ty4, 300000, 550000, [para("×", 2000, INK, algn="ctr", aft=0)], anchor="ctr")
s.card("0D 카드", X2, cy4, CW, ch4, [para("0D 균형: 밀도는 전력에 비례한다", T1, HEAD, True)])
w, h = s.eq("eq_n0.png", X2 + 109728, cy4 + 500000, emu_per_px=1600, center_w=CW - 219456)
s.box("0D 설명", X2 + 109728, cy4 + 500000 + h + 110000, CW - 219456, 520000, [
    para("T_{e}는 압력과 용기 크기가 정한다.", B1, INK, algn="ctr", aft=50),
    para("전력을 바꿔도 달라지지 않는다 (2.70).", S1, SUB, algn="ctr", aft=0)])
io_strip(s, cy4 + ch4 + 150000, "P", "단일 코일 ICP",
         "n̄_{w}를 정하면 P가 정해지고, 그 P에서 ρ도 정해진다.")
s.pagenum()
s.write(5)

# ===================== 5. 이중 코일의 제어 입력 (slide6.xml) =====================
s = Slide()
s.frame("이중 코일 ICP: 제어 입력은 셋", "이중 코일  ·  제어 입력과 출력",
        "이중 코일의 제어 입력은 (k, φ, P_{tot}) 셋, 맞출 출력은 (n̄_{w}, ρ) 둘이다.",
        "P_{tot}에서 매처와 안테나의 손실을 뺀 나머지가 P_{abs}다: 정진욱 (2026) §2.4 p.135. 전류 표기와 공통 위상: 부록 A4.")
c5 = TOP + 330000
chamber(s, c5, currents=True)
px = 4663440
pw, ph = s.eq("fig_phasor.png", px, TOP + 20000, emu_per_px=2650)
s.box("페이저 설명", px, TOP + 20000 + ph + 10000, pw, 280000, [para("I_{out} = k e^{jφ} I_{in}", B1, INK, True, algn="ctr", aft=0)])
kx = px + pw + 150000
kw = R - kx
kh = 500000
for k, (sym, nm) in enumerate([("k", "전류 크기비"), ("φ", "전류 위상차"), ("P_{tot}", "총 공급 전력")]):
    ky = TOP + 60000 + k * (kh + 90000)
    s.box(f"입력 {k + 1} 기호", kx, ky, 560000, kh, [para(sym, 1500, "FFFFFF", True, algn="ctr", aft=0)], fill=NAVY, anchor="ctr")
    s.box(f"입력 {k + 1}", kx + 560000, ky, kw - 560000, kh, [para(nm, B1, INK, True, aft=0)], line=LINE, inset=91440, anchor="ctr")
ty = c5 + 1659636 + 130000
s.box("자유도 세기", L, ty, W, 300000, [
    para("전류 2개 = 크기 2 + 위상 2.  공통 위상은 시간 평균 전력과 무관하므로 독립 변수는 3개다.", B1, algn="ctr", aft=0)])
io_strip(s, ty + 400000, "k,  φ,  P_{tot}", "이중 코일 ICP",
         "입력이 출력보다 많은 것은 필요조건이다. 각 입력이 n̄_{w}와 ρ를 어떻게 바꾸는지 봐야 한다.")
s.pagenum()
s.write(6)

# ===================== 6. 이중 코일의 가열과 0D (slide7.xml) =====================
s = Slide()
s.frame("이중 코일의 가열: 0D에는 흡수 전력만 남는다", "이중 코일  ·  두 코일 장의 중첩과 부피 적분",
        "0D에서 k와 φ는 흡수 전력의 크기로만 나타나고, 밀도비 ρ는 정의되지 않는다.",
        "정진욱 (2026) 식 (2.31)–(2.32), (2.73)을 두 코일로 확장 [유도]. Ẽ: 단위 전류당 E_{θ} (전도도 고정). 부록 A13.")
ew, eh = s.eq("eq_pe3.png", L, TOP + 40000, emu_per_px=1900, max_w=W - 60000, center_w=W)
ex = L + (W - ew) // 2
ly = TOP + 40000 + eh + 40000
for key, lab, col in [("in", "안쪽 코일", BLUE), ("out", "바깥쪽 코일", ORANGE), ("x", "간섭: 위치마다 다르다", NAVY)]:
    a, b = SPANS[key]
    s.box(f"밑줄 {key}", ex + int(a * ew), ly, int((b - a) * ew), 27432, None, fill=col)
    mid = ex + int((a + b) / 2 * ew)
    s.box(f"항 {key}", mid - 1300000, ly + 50000, 2600000, 280000,
          [para(lab, B1, ORANGE_T if col == ORANGE else col, True, algn="ctr", aft=0)])
ry = ly + 480000
# 왼쪽: 한 위치에서 두 장의 합
s.box("합 제목", L, ry, 3300000, 280000, [para("한 위치에서 두 코일 장의 합", B1, HEAD, True, aft=0)])
fw, fh = s.eq("fig_sum.png", L, ry + 330000, emu_per_px=3050)
s.box("합 설명", L, ry + 330000 + fh + 60000, 3300000, 520000, [
    para("ψ(r, z): 두 장의 상대 위상", S1, SUB, aft=40),
    para("사이 각 φ + ψ가 보강·상쇄를 정한다.", S1, INK, aft=0)])
# 오른쪽: 2D 분포 → 부피 적분 → 0D 값
tx1, tw6 = 3930000, 2011680
tx2 = R - tw6
th6 = 1850000
for nm, x, hd, sym, l1, l2, col in [
        ("2D", tx1, "2D 분포", "p_{e}(r, z)", "간섭이 위치마다 다르다.", "k와 φ가 가열 분포의 모양을 바꾼다.", HEAD),
        ("0D", tx2, "0D 값", "P_{abs}", "숫자 하나만 남는다.", "k와 φ는 n_{0}만 바꾼다. ρ는 없다.", ORANGE_T)]:
    s.box(f"{nm} 타일", x, ry, tw6, th6, [
        para(hd, T1, col, True, algn="ctr", aft=50),
        para(sym, 1800, INK, True, algn="ctr", aft=250),
        para(l1, S1, SUB, algn="ctr", aft=100),
        para(l2, B1, INK, algn="ctr", aft=0)], line=LINE, inset=91440, anchor="ctr")
    s.box(f"{nm} 강조선", x, ry, tw6, 45720, None, fill=col)
gx, gw = tx1 + tw6 + 60000, tx2 - tx1 - tw6 - 120000
s.arrow("적분 화살표", gx, ry + th6 // 2, gw, color=INK, width=25400)
s.box("적분 표기", gx - 60000, ry + th6 // 2 - 330000, gw + 120000, 280000, [para("∫ dV", 1500, INK, True, algn="ctr", aft=0)])
s.box("전력비 설명", tx1, ry + th6 + 90000, R - tx1, 520000, [
    para("P_{abs}는 코일별로 나눌 수 없다. k는 흡수 전력의 비가 아니다.", S1, INK, algn="ctr", aft=0)])
s.pagenum()
s.write(7)

# ===================== 7. 0D의 한계와 2D 모델의 필요성 (slide10.xml) =====================
s = Slide()
s.frame("0D의 한계와 2D 모델의 필요성", "0D에서 2D로  ·  0D 모델의 적용 범위 (교재 §2.4, §1.10)",
        "ρ는 n(r, z)에서만 정해지므로, 코일 전류에서 n(r, z)까지를 2D로 풀어야 한다.",
        "정진욱 (2026) §2.4 p.137, §1.10 pp.62–64 식 (1.76), (1.79), (1.83). χ_{01}: J_{0}의 첫 영점. T_{e}(r, z)는 팀 2D 모델에서 구한다.")
pw7, ph7 = 3566160, 1480000
xr7 = R - pw7
for nm, x, hd, col in [("0D", L, "0D 모델", ORANGE_T), ("2D", xr7, "2D 모델 (r, z)", HEAD)]:
    s.box(f"{nm} 패널", x, TOP, pw7, ph7, None, line=LINE)
    s.box(f"{nm} 강조선", x, TOP, pw7, 45720, None, fill=col)
    s.box(f"{nm} 제목", x + 109728, TOP + 90000, pw7 - 219456, 300000, [para(hd, T1, col, True, aft=0)])
mx, my, mw, mh = 150000, 480000, 1500000, 820000
# 0D: 값 하나로 채운 상자
s.shape("rect", "0D 챔버", L + mx, TOP + my, mw, mh, fill="DCE6F5", line="5F6779")
s.box("0D 값", L + mx, TOP + my, mw, mh, [para("T_{e},  n_{0}", 1600, INK, True, algn="ctr", aft=0)], anchor="ctr")
s.box("0D 설명", L + mx + mw + 130000, TOP + my, pw7 - mx - mw - 230000, mh, [
    para("공간 평균 값 하나씩", S1, SUB, aft=120),
    para("ρ를 정의할 수 없다", B1, INK, True, aft=0)], anchor="ctr")
# 2D: 중앙·가장자리 영역이 있는 상자
s.shape("rect", "2D 챔버", xr7 + mx, TOP + my, mw, mh, fill="F7F9FC", line="5F6779")
s.box("2D 값", xr7 + mx, TOP + my + 60000, mw, 300000, [para("n(r, z)", 1500, INK, True, algn="ctr", aft=0)])
s.shape("rect", "2D 중앙", xr7 + mx, TOP + my + mh - 190000, 430000, 64008, fill=BLUE)
s.shape("rect", "2D 가장자리", xr7 + mx + 920000, TOP + my + mh - 190000, 300000, 64008, fill=ORANGE)
s.box("2D n_c", xr7 + mx + 20000, TOP + my + mh - 440000, 500000, 240000, [para("n_{c}", S1, BLUE, True, aft=0)])
s.box("2D n_edge", xr7 + mx + 880000, TOP + my + mh - 440000, 620000, 240000, [para("n_{edge}", S1, ORANGE_T, True, aft=0)])
s.box("2D 설명", xr7 + mx + mw + 130000, TOP + my, pw7 - mx - mw - 230000, mh, [
    para("위치마다 다른 밀도", S1, SUB, aft=120),
    para("ρ = n_{c} / n_{edge}", B1, INK, True, aft=0)], anchor="ctr")
s.arrow("모델 화살표", L + pw7 + 90000, TOP + ph7 // 2, xr7 - L - pw7 - 180000, color=INK, width=25400)
# 전자온도 균일이면 형상 고정
iy, ih = TOP + ph7 + 130000, 1000000
s.box("형상 상자", L, iy, W, ih, None, fill="F4F6FA")
w, h = s.eq("eq_diffmode.png", L + 150000, iy + (ih - 293 * 1480) // 2, emu_per_px=1480)
s.box("형상 설명", L + 150000 + w + 200000, iy, W - w - 450000, ih, [
    para("T_{e}가 균일하면 분포의 모양은 용기 크기가 정한다.", S1, INK, aft=100),
    para("ρ는 k, φ로 바뀌지 않는다.", B1, ORANGE_T, True, aft=0)], anchor="ctr")
# 2D 사슬
fy7 = iy + ih + 110000
s.box("사슬 제목", L, fy7, W, 280000, [para("2D 모델이 이어야 할 사슬", B1, HEAD, True, aft=0)])
chain(s, fy7 + 320000, 560000, [("코일 전류", "I_{0}, k, φ"), ("유도 전기장", "E_{θ}(r, z)"), ("흡수 옴전력", "p_{e}(r, z)"),
                                 ("전자온도", "T_{e}(r, z)"), ("이온화", "G(r, z)"), ("밀도", "n(r, z) → ρ")], "2D 사슬",
      gap_min=200000, sz=(1200, 1300))
s.pagenum()
s.write(10)

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes_text.py"), encoding="utf-8").read())
print("built")
