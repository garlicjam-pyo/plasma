"""README 지시에 따라 표지와 슬라이드 3–10을 다시 만든다 (기존 양식 유지, 0D 부분은 교재 식으로, 임피던스는 2D로 넘김)."""
import os
import re
import shutil
from xml.sax.saxutils import escape
from PIL import Image

U = "un"                      # 풀어 둔 pptx
EQ = "eq2"                    # 새 식 PNG
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
            f'<p:pic><p:nvPicPr><p:cNvPr id="{i}" name="수식 {media[:-4]}" descr="{media}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
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



# 새 식 PNG를 media로 복사
for f in os.listdir(EQ):
    if f.startswith("n_") and f.endswith(".png"):
        shutil.copy(f"{EQ}/{f}", f"{U}/ppt/media/eq_{f[2:]}")

L, R, W = 457200, 8686800, 8229600   # 좌우 여백, 본문 폭
TOP, BOT = 1335000, 5310000          # 본문 위·아래 끝
CW = 4023360                         # 2단 카드 폭
X2 = L + CW + 182880                 # 오른쪽 카드 x


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
    s.box("창 표기", x0, c0 + 196596, cwid, 365760, [para("유전체 창", 1200, SUB, algn="ctr", aft=0)], anchor="ctr")
    s.box("플라즈마 표기", x0, c0 + 640000, cwid, 230000, [para("플라즈마", 1200, SUB, algn="ctr", aft=0)])
    s.box("웨이퍼 표기", 1560000, c0 + 1613916 - 235000, 1100000, 230000, [para("웨이퍼", 1200, SUB, algn="ctr", aft=0)])
    if regions:
        s.shape("rect", "중앙 영역", x0, c0 + 1399032, 914400, 64008, fill=BLUE)
        s.shape("rect", "가장자리 영역", 2743200, c0 + 1399032, 457200, 64008, fill=ORANGE)
        s.box("n_c 표기", 566928, c0 + 1156716, 914400, 274320, [para("n_{c}", 1250, BLUE, True)])
        s.box("n_edge 표기", 2697480, c0 + 1156716, 914400, 274320, [para("n_{edge}", 1250, ORANGE_T, True)])
        s.box("관측면 표기", 3291840, c0 + 1356900, 1050000, 230000, [para("z = z_{w}", 1200, SUB)])
        for lab, xx in [("0", x0), ("r_{c}", 1463040), ("r_{1}", 2743200), ("r_{2}", 3200400)]:
            s.box(f"반경 {lab}", xx - 228600, c0 + 1696900, 457200, 230000, [para(lab, 1200, SUB, algn="ctr")])
    if currents:
        s.box("안쪽 전류", 1028700 - 300000, c0 - 300000, 1371600 + 600000, 250000,
              [para("I_{in} = I_{0}", 1300, BLUE, True, algn="ctr", aft=0)])
        s.box("바깥쪽 전류", 2674620 - 300000, c0 - 300000, 1371600 + 600000, 250000,
              [para("I_{out} = k e^{jφ} I_{0}", 1300, ORANGE_T, True, algn="ctr", aft=0)])


def chain(s, y, h, items, name, gap_min=240000):
    """가로 사슬: 상자 n개 + 사이 화살표. items = [(윗줄, 아랫줄), ...]"""
    n = len(items)
    bw = (W - (n - 1) * gap_min) // n
    gap = (W - n * bw) // (n - 1)
    for k, (top, bot) in enumerate(items):
        x = L + k * (bw + gap)
        s.box(f"{name} {k + 1}", x, y, bw, h,
              [para(top, 1200, SUB, algn="ctr", aft=0), para(bot, 1250, INK, True, algn="ctr", aft=0)],
              line="8C93A3", anchor="ctr")
        if k < n - 1:
            s.arrow(f"{name} 화살표 {k + 1}", x + bw + 30000, y + h // 2, gap - 60000)


def io_strip(s, y, inputs, system, caption):
    """입력 → 장치 → 출력 도식과 그 아래 한 줄 결론."""
    bh, wi, ws = 520000, 2103120, 2743200
    g = (W - 2 * wi - ws) // 2
    xs = [L, L + wi + g, L + wi + g + ws + g]
    s.box("입력", xs[0], y, wi, bh, [para("입력", 1200, SUB, algn="ctr", aft=0), para(inputs, 1300, INK, True, algn="ctr", aft=0)],
          line="8C93A3", anchor="ctr")
    s.box("장치", xs[1], y, ws, bh, [para(system, 1300, HEAD, True, algn="ctr", aft=0),
                                     para("압력·주파수·코일 형상 고정", 1200, SUB, algn="ctr", aft=0)], fill="EEF3FB", anchor="ctr")
    s.box("출력", xs[2], y, wi, bh, [para("출력", 1200, SUB, algn="ctr", aft=0), para("n̄_{w},  ρ", 1300, INK, True, algn="ctr", aft=0)],
          line="8C93A3", anchor="ctr")
    s.arrow("입력 화살표", xs[0] + wi + 40000, y + bh // 2, g - 80000)
    s.arrow("출력 화살표", xs[1] + ws + 40000, y + bh // 2, g - 80000)
    s.box("입출력 결론", L, y + bh + 70000, W, BOT - (y + bh + 70000), [para(caption, 1300, INK, algn="ctr", aft=0)])


# ===================== 1. 표지 (slide1.xml): 부제만 흐름에 맞춤 =====================
p1 = f"{U}/ppt/slides/slide1.xml"
x = open(p1, encoding="utf-8").read()
x = x.replace("<a:t>이론적 배경과 상세 수식 유도 · 핵심 수식판</a:t>",
              "<a:t>문제 정의 · 단일·이중 코일의 0D 기술 · 2D 모델의 필요성</a:t>")
open(p1, "w", encoding="utf-8").write(x)
notes(1, "[대본 · 0:00–0:20 / 20초]",
      "안녕하세요, 6조입니다. 저희 주제는 이중 코일 유도 결합 플라즈마에서 중앙과 가장자리의 전자 밀도를 따로 조절하는 것입니다. "
      "오늘은 문제를 정의하고, 단일 코일과 이중 코일을 0D 모델로 살펴본 뒤, 0D의 한계와 2D 모델이 필요한 이유까지 말씀드리겠습니다.",
      "IC-PBL 주제 3. 흐름(팀 README): 문제 정의 → 단일 코일로는 불가 → 이중 코일(0D) → 0D의 한계와 2D 모델의 필요성. "
      "이론식은 정진욱 (2026) 『플라즈마 전자공학』 4판을 우선 인용한다.")

# ===================== 3. 문제 정의와 제어 목표 (slide4.xml) =====================
s = Slide()
s.frame("문제 정의와 제어 목표", "설계 과제  ·  중앙·가장자리 밀도비의 독립 조절",
        "목표는 평균 밀도 n̄_{w}를 유지하면서 밀도비 ρ를 바꾸는 것이다.",
        "[정의] 축대칭이므로 dA = 2πr dr. 경계 r_{c}, r_{1}, r_{2}, R_{w}(≥ r_{2})와 관측 높이 z_{w}는 설계 단계에서 정한다. 부록 A3.")
s.box("과제 문단", L, TOP, W, 1150000, [
    para("**문제 정의**  하나의 챔버에서 중앙부와 가장자리의 플라즈마 밀도를 독립적으로 조절할 수 있는 소스를 설계한다. "
         "두 영역의 밀도를 함께 높이거나 낮추는 데 그치지 않고, 밀도비를 원하는 값으로 조정할 수 있는 구조와 구동 방식을 제안한다.", 1350, aft=700),
    para("**제어 목표**  중앙부와 가장자리의 밀도비 ρ = n_{c}/n_{edge}를 전체 밀도 수준과 따로 조정한다.", 1350)])
s.box("개략도 제목", 548640, 2600000, 3840480, 230000, [para("반단면 개략도: 축 r = 0에서 측벽까지", 1200, SUB, True)])
chamber(s, 2950000, regions=True)
s.box("코일 범례", 548640, 4900000, 3840480, 420000,
      [para("[[3366CC|●]] 안쪽 코일   [[D9622B|●]] 바깥쪽 코일", 1200, SUB, aft=100),
       para("n(r, z_{w}): 관측 높이 z_{w}에서의 전자 밀도", 1200, SUB, aft=0)])
bx, bw = 4572000, 4114800
s.box("평가 지표 상자", bx, 2600000, bw, 2700000, None, fill="EEF3FB")
s.box("평가 지표 제목", bx + 137160, 2670000, bw - 274320, 260000, [para("평가 지표: 영역 S의 면적 평균", 1400, HEAD, True)])
w, h = s.eq("eq_avg.png", bx + 137160, 3000000, emu_per_px=1150)
s.box("A_S 설명", bx + 137160 + w + 120000, 3000000, bw - w - 400000, h,
      [para("A_{S}: 영역 S의 넓이", 1200, SUB)], anchor="ctr")
s.box("세 영역", bx + 137160, 3000000 + h + 80000, bw - 274320, 800000, [
    para("n_{c}:  S = 중앙 영역, 0 ≤ r ≤ r_{c}", 1250, bullet=True, aft=200),
    para("n_{edge}:  S = 가장자리 고리, r_{1} ≤ r ≤ r_{2}", 1250, bullet=True, aft=200),
    para("n̄_{w}:  S = 관측면 전체, 0 ≤ r ≤ R_{w}", 1250, bullet=True, aft=0)])
s.box("제어 목표 제목", bx + 137160, 4420000, bw - 274320, 260000, [para("제어 목표", 1400, HEAD, True)])
s.eq("eq_rhotgt.png", bx + 137160, 4760000, emu_per_px=1150)
s.pagenum()
s.write(4)
notes(4, "[대본 · 0:20–1:20 / 60초]",
      "저희 과제는 하나의 챔버에서 중앙부와 가장자리의 플라즈마 밀도를 독립적으로 조절할 수 있는 소스를 설계하는 것입니다. "
      "두 영역을 함께 올리거나 내리는 것이 아니라, 밀도비를 원하는 값으로 맞추는 것이 목표입니다. "
      "이를 식으로 쓰기 위해 웨이퍼 위 관측 높이에서 영역 S의 면적 평균을 정의하고, 영역만 바꿔 중앙 n_c, 가장자리 n_edge, 관측면 전체 n̄_w를 정합니다. "
      "중앙과 가장자리의 비를 ρ라고 하면, 목표는 n̄_w는 유지하고 ρ만 바꾸는 것입니다. 먼저 코일이 하나일 때 이것이 가능한지 보겠습니다.",
      "과제 정의: IC-PBL 주제 3. 면적 평균은 축대칭 면적 요소 dA = 2πr dr로 계산한다(예: n_c = (2/r_c²)∫₀^(r_c) n r dr). "
      "평가 영역 경계 r_c, r_1, r_2, R_w와 관측 높이 z_w는 설계 단계에서 정한다. 목표는 한 영역을 고정하고 다른 영역만 바꾸는 것과 다르다. 상세 정의: 부록 A3.")

# ===================== 4. 단일 코일 (slide5.xml) =====================
s = Slide()
s.frame("단일 코일 ICP: 입력은 전력 하나", "단일 코일  ·  유도 가열과 0D 균형 (교재 §2.3, §2.4)",
        "단일 코일로는 평균 밀도를 유지한 채 밀도비를 바꿀 수 없다.",
        "정진욱 (2026) §2.3.1 pp.103–105 식 (2.26), (2.31)–(2.32), §2.3.4 p.122 식 (2.52), §2.4 pp.136–138 식 (2.70), (2.73).")
chain(s, TOP, 500000, [("안테나 전류", "I(t)"), ("시변 자속", "dΦ/dt"), ("원주 유도 전기장", "E_{θ}"),
                       ("흡수 옴전력", "p_{e}"), ("충돌 이온화", "K_{iz}(T_{e})")], "가열 사슬")
cy4, ch4 = TOP + 640000, 2040000
s.card("공간 카드", L, cy4, CW, ch4, [para("공간 분포: 전류는 크기만 바꾼다", 1400, HEAD, True)])
w, h = s.eq("eq_pe.png", L + 109728, cy4 + 370000, emu_per_px=1350, center_w=CW - 219456)
s.box("식 번호 2.31", L + CW - 800000, cy4 + 370000, 700000, h, [para("(2.31)", 1200, SUB, algn="r", aft=0)], anchor="ctr")
yy = cy4 + 370000 + h + 100000
s.box("공간 설명", L + 109728, yy, CW - 219456, cy4 + ch4 - yy - 40000, [
    para("σ_{p} = n_{e}e^{2}/[m(ν + jω)]: 플라즈마 전도도 (2.26)", 1200, SUB, bullet=True, aft=150),
    para("E_{θ}는 안테나 전류에 비례하고, 공간 분포는 코일 구조가 정한다 (2.52).", 1200, SUB, bullet=True, aft=150),
    para("전도도가 같으면 전류는 p_{e}(r, z)의 크기만 바꾼다.", 1250, INK, True, aft=0)])
s.card("0D 카드", X2, cy4, CW, ch4, [para("0D 균형: 전력이 밀도 수준을 정한다", 1400, HEAD, True)])
tw, th = 1077 * 1250, 385 * 1250
nw_, nh_ = 1047 * 1250, 349 * 1250
x0 = X2 + 109728 + (CW - 219456 - (tw + 300000 + nw_)) // 2
s.eq("eq_te.png", x0, cy4 + 340000, emu_per_px=1250)
s.eq("eq_n0.png", x0 + tw + 300000, cy4 + 340000 + (th - nh_) // 2, emu_per_px=1250)
yy = cy4 + 340000 + th + 80000
s.box("0D 설명", X2 + 109728, yy, CW - 219456, cy4 + ch4 - yy - 40000, [
    para("입자 균형 (2.70): T_{e}는 압력(n_{g})과 용기 크기(d_{eff})가 정한다. 전력과 무관하다.", 1200, SUB, bullet=True, aft=150),
    para("전력 균형 (2.73): P_{abs} = ∫p_{e} dV,  ε_{T}는 전자–이온 한 쌍의 총 손실 에너지", 1200, SUB, bullet=True, aft=150),
    para("n_{0}는 P_{abs}에 비례한다.", 1250, INK, True, aft=0)])
io_strip(s, cy4 + ch4 + 140000, "P", "단일 코일 ICP",
         "n̄_{w}를 정하면 P가 정해지고, 그 P에서 ρ도 정해진다.")
s.pagenum()
s.write(5)
notes(5, "[대본 · 1:20–2:20 / 60초]",
      "코일이 하나일 때를 보겠습니다. 안테나에 흐르는 교류 전류가 시변 자속을 만들고, 패러데이 법칙에 따라 원주 방향의 유도 전기장이 생깁니다. "
      "이 전기장은 플라즈마 전도도를 통해 전자에 옴전력을 줍니다. 전도도가 같다면 전기장은 전류에 비례하고 공간 분포는 코일 구조가 정하므로, 전류는 가열 분포의 크기만 바꿉니다. "
      "0D 모델에서는 입자 균형이 압력과 용기 크기로 전자온도를 정하고, 전력 균형에서 밀도 n_0는 흡수 전력에 비례합니다. "
      "결국 압력과 코일 형상을 고정한 단일 코일에서 바꿀 수 있는 입력은 전력 하나입니다. 평균 밀도를 정하면 전력이 정해지고, 그 전력에서 밀도비도 정해집니다. "
      "출력 둘을 따로 정하려면 입력이 더 필요합니다. 그래서 코일을 둘로 나눕니다.",
      "정진욱 (2026) §2.3.1 p.103 식 (2.25) J = σ_pE, 식 (2.26) σ_p = n_e e²/[m(ν + jω)]. p.105 식 (2.31) p_e = ⟨J·E⟩ = ½Re(J·E*) [W/m³], "
      "식 (2.32) p_e = ½E²σ_dc ν²/(ω² + ν²), σ_dc = ne²/(mν). 따라서 p_e = ½Re(σ_p)|E|²(E는 피크 진폭). "
      "§2.3.4 p.122 식 (2.52): 원통형 ICP에서 V = 2πrE_θ = −dΦ/dt로부터 E_θ(r, t) = −(μ_0r/2)ωnI_0cos ωt(n은 단위 길이당 감은 수). 평면 코일도 E_θ는 전류에 비례하고 축 위에서 0이다. "
      "§2.4 p.136 식 (2.69)–(2.70): K_iz n_g n_0 V = h n_0 u_B A, K_iz(T_e)/u_B(T_e) = 1/(n_g d_eff), d_eff = V/(hA). "
      "p.138 식 (2.73): n_0 = P_abs/(e u_B ε_T A_eff), A_eff = 2πR²h_L + 2πRLh_R. p.134: ε_T = ε_c + ε_e + ε_i (식 2.65). "
      "p.137: 이 단순 모델에서는 T_e가 밀도와 무관하지만, 실제로는 두 식이 결합되어 T_e가 밀도·압력·면적 대 부피비의 함수가 된다. "
      "실제 장치에서는 전력에 따라 밀도와 표피 깊이가 바뀌어 ρ도 변할 수 있지만(예: E–H 전이, Park 2017), 그 변화도 P 하나의 함수이므로 n̄_w와 따로 정할 수 없다. 부록 A2, A8–A10.")

# ===================== 5. 이중 코일의 제어 입력 (slide6.xml) =====================
s = Slide()
s.frame("이중 코일 ICP: 제어 입력은 셋", "이중 코일  ·  제어 입력과 출력",
        "이중 코일의 제어 입력은 (k, φ, P_{tot}) 셋, 맞출 출력은 (n̄_{w}, ρ) 둘이다.",
        "P_{abs}의 정의: 정진욱 (2026) §2.4 p.135. 전류 표기와 공통 위상 제거: 부록 A4.")
c5 = TOP + 330000
chamber(s, c5, currents=True)
rx, rw = 4572000, 4114800
hs = [600000, 600000, 850000]
yk = TOP
for k, (hd, body, col) in enumerate([
        ("상대 진폭  k = |I_{out}| / |I_{in}|", "두 코일 전류 크기의 비", BLUE),
        ("상대 위상  φ = arg I_{out} − arg I_{in}", "두 코일 전류의 위상차", ORANGE_T),
        ("총 공급 전력  P_{tot}", "전류 크기 I_{0} 대신 지정한다. 매처와 안테나의 손실을 뺀 나머지가 P_{abs}다.", HEAD)]):
    s.card(f"입력 카드 {k + 1}", rx, yk, rw, hs[k], [para(hd, 1300, col, True, aft=150), para(body, 1200, aft=0)], accent=col)
    yk += hs[k] + 70000
ty = max(yk, c5 + 1659636) + 130000
s.box("자유도 세기", L, ty, W, 300000, [
    para("두 전류는 복소수 두 개(크기 둘, 위상 둘)이고, 공통 위상은 시간 평균 전력에 영향이 없다. 독립 변수는 셋이다.", 1300, algn="ctr", aft=0)])
io_strip(s, ty + 450000, "k,  φ,  P_{tot}", "이중 코일 ICP",
         "입력 수 ≥ 출력 수는 독립 조절의 필요조건이다. 충분한지는 각 입력이 n̄_{w}와 ρ를 어떻게 바꾸는지에 달려 있다.")
s.pagenum()
s.write(6)
notes(6, "[대본 · 2:20–3:05 / 45초]",
      "코일을 안쪽과 바깥쪽으로 나누고 각각 전류를 흘립니다. 두 전류는 복소수 두 개이므로 크기 둘, 위상 둘인데, "
      "공통 위상은 시간 원점을 어디에 두느냐의 문제라 시간 평균 전력에 영향이 없습니다. 그래서 독립 변수는 상대 진폭 k, 상대 위상 φ, 그리고 전체 크기 세 개입니다. "
      "전체 크기는 전류 대신 RF 전원의 총 전력으로 지정하고, 여기서 매처와 안테나의 손실을 뺀 나머지가 플라즈마에 흡수됩니다. "
      "이제 입력은 셋, 맞출 출력은 평균 밀도와 밀도비 둘입니다. 다만 입력이 더 많다는 것은 필요조건일 뿐입니다. "
      "그러면 k와 φ가 플라즈마에서 실제로 무엇을 바꾸는지 보겠습니다.",
      "I = I_0[1, ke^(jφ)]ᵀ, k = |I_out|/|I_in|, φ = arg I_out − arg I_in (부록 A4). "
      "교재 p.135: P_abs는 RF 전력이 아닌 순수 플라즈마에 공급되는 전력이고, RF 전력에서 매처와 안테나(또는 전극)의 손실을 뺀 값이다. "
      "P_tot에서 I_0를 정하는 관계(코일 단자 임피던스, 매처·안테나 손실)는 0D가 아니라 2D 장 해석과 함께 다룬다(부록 A5). "
      "교재 p.123의 k는 변압기 모델의 결합 계수(M = k√(L_gL_a))로, 여기의 전류비 k와 다른 기호다.")

# ===================== 6. 이중 코일의 가열과 0D (slide7.xml) =====================
s = Slide()
s.frame("이중 코일의 가열: 0D에는 흡수 전력만 남는다", "이중 코일  ·  두 코일 장의 중첩과 부피 적분",
        "0D에서 k와 φ는 흡수 전력의 크기로만 나타나고, 밀도비 ρ는 정의되지 않는다.",
        "정진욱 (2026) 식 (2.31)–(2.32), (2.73)을 두 코일로 확장 [유도]. 장의 중첩은 전도도를 고정한 선형 장 문제에서 성립한다. 부록 A13.")
s.box("중첩 제목", L, TOP, W, 280000, [para("두 코일의 유도 전기장은 겹친다", 1400, HEAD, True)])
w, h = s.eq("eq_esup.png", L, TOP + 380000, emu_per_px=1400, center_w=W)
y6 = TOP + 380000 + h + 50000
s.box("단위 전류 장", L, y6, W, 250000, [
    para("Ẽ_{in}, Ẽ_{out}: 각 코일에 단위 전류를 흘렸을 때의 E_{θ} (복소수)", 1200, SUB, algn="ctr", aft=0)])
y6 += 430000
s.box("간섭 제목", L, y6, W, 280000, [para("흡수 옴전력에는 간섭항이 생긴다", 1400, HEAD, True)])
w, h = s.eq("eq_pe2.png", L, y6 + 380000, emu_per_px=1700, max_w=W - 150000, center_w=W)
y6 += 380000 + h + 50000
s.box("세 항", L, y6, W, 250000, [
    para("괄호 안: 안쪽 코일 항, 바깥쪽 코일 항, **간섭항**.   ψ(r, z) = arg Ẽ_{out} − arg Ẽ_{in}: 위치마다 다른 상대 위상", 1200, SUB, algn="ctr", aft=0)])
cy6 = y6 + 430000
ch6 = BOT - cy6
cw6 = 3657600
s.card("공간 분포 카드", L, cy6, cw6, ch6, [
    para("2D 분포 p_{e}(r, z)", 1400, HEAD, True, aft=250),
    para("간섭항의 크기와 부호가 위치마다 다르다.", 1250, bullet=True, aft=150),
    para("k와 φ가 가열 분포의 모양을 바꾼다.", 1250, bullet=True, aft=0)])
s.card("0D 카드", R - cw6, cy6, cw6, ch6, [
    para("0D 값 P_{abs}", 1400, HEAD, True, aft=250),
    para("k와 φ는 n_{0} ∝ P_{abs}만 바꾼다.", 1250, bullet=True, aft=150),
    para("P_{abs}를 코일별로 나눌 수 없다. k는 흡수 전력의 비가 아니다.", 1250, bullet=True, aft=0)])
gx, gw = L + cw6 + 60000, W - 2 * cw6 - 120000
s.arrow("적분 화살표", gx, cy6 + ch6 // 2, gw, color=NAVY, width=19050)
s.box("적분 표기", gx - 40000, cy6 + ch6 // 2 - 300000, gw + 80000, 250000, [para("∫ dV", 1300, NAVY, True, algn="ctr", aft=0)])
s.pagenum()
s.write(7)
notes(7, "[대본 · 3:05–4:05 / 60초]",
      "두 코일이 만든 유도 전기장은 겹칩니다. 전도도가 같다고 두면 전체 전기장은 안쪽 코일의 단위 전류 장에 바깥쪽 코일의 단위 전류 장을 k e^{jφ}배 해서 더한 것입니다. "
      "이것을 앞의 옴전력 식에 넣으면 괄호 안에 세 항이 나옵니다. 안쪽 코일 항, 바깥쪽 코일 항, 그리고 cos(φ + ψ)가 붙은 간섭항입니다. "
      "ψ는 위치마다 다르므로 간섭항은 어떤 곳에서는 보강, 어떤 곳에서는 상쇄가 되고, 그래서 k와 φ가 가열 분포의 모양을 바꿉니다. "
      "그런데 0D에서는 이 분포를 부피 적분한 P_abs 하나만 남습니다. k와 φ는 밀도 수준만 바꾸고, 밀도비는 정의되지 않습니다. "
      "또 간섭항 때문에 흡수 전력을 코일별로 나눌 수 없으므로, k는 흡수 전력의 비가 아닙니다. 그러면 0D 모델로는 어디까지 말할 수 있을까요.",
      "교재 식 (2.25) J = σ_pE, (2.31) p_e = ½Re(J·E*), Re σ_p = σ_dc ν²/(ω² + ν²) (식 2.26, 2.32). "
      "σ_p를 고정하면 장 방정식이 전류에 선형이므로 E_θ = I_0[Ẽ_in + ke^(jφ)Ẽ_out]. |E_θ|² = I_0²[|Ẽ_in|² + k²|Ẽ_out|² + 2k Re(Ẽ_in* Ẽ_out e^(jφ))], "
      "Re(Ẽ_in* Ẽ_out e^(jφ)) = |Ẽ_in||Ẽ_out|cos(φ + ψ). 교재에는 두 코일 중첩식이 없다(팀 유도, 부록 A4·A13). "
      "φ = π라도 ψ가 위치마다 달라 모든 위치에서 상쇄되지는 않는다. 0D에서는 P_abs = ∫p_e dV만 식 (2.73)에 들어가므로 같은 P_abs를 주는 (k, φ)는 구별되지 않는다. "
      "단위 전류 장은 플라즈마 전도도에 따라 바뀌므로, ψ와 Ẽ의 실제 분포는 2D 장 해석으로 구한다.")

# ===================== 7. 0D의 한계와 2D 모델의 필요성 (slide10.xml) =====================
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

s = Slide()
s.frame("0D의 한계와 2D 모델의 필요성", "0D에서 2D로  ·  0D 모델의 적용 범위 (교재 §2.4, §1.10)",
        "ρ는 n(r, z)에서만 정해지므로, 코일 전류에서 n(r, z)까지를 2D로 풀어야 한다.",
        "정진욱 (2026) §2.4 p.137, §1.10 pp.62–64 식 (1.76), (1.79), (1.83). χ_{01}: J_{0}의 첫 영점. T_{e}(r, z)는 팀 2D 모델에서 구한다.")
ch7 = 1980000
s.card("0D 카드", L, TOP, CW, ch7, [
    para("0D가 주는 것과 주지 않는 것", 1400, HEAD, True, aft=300),
    para("입자 균형과 전력 균형이 주는 T_{e}, n_{0}는 공간 평균된 값이다 (교재 p.137).", 1250, bullet=True, aft=200),
    para("r, z가 없으므로 n_{c}, n_{edge}, ρ를 정의할 수 없다.", 1250, bullet=True, aft=200),
    para("코일은 P_{abs} 하나로만 들어간다.", 1250, bullet=True, aft=0)])
s.card("확산 카드", X2, TOP, CW, ch7, [para("T_{e}가 균일하면 형상은 고정된다", 1400, HEAD, True)])
w, h = s.eq("eq_diff.png", X2 + 109728, TOP + 380000, emu_per_px=1350, center_w=CW - 219456)
s.box("식 번호 1.76", X2 + CW - 800000, TOP + 380000, 700000, h, [para("(1.76)", 1200, SUB, algn="r", aft=0)], anchor="ctr")
my = TOP + 380000 + h + 110000
w, h = s.eq("eq_mode.png", X2 + 109728, my, emu_per_px=1300, center_w=CW - 219456)
s.box("모드 설명", X2 + 109728, my + h + 80000, CW - 219456, TOP + ch7 - (my + h + 80000) - 40000, [
    para("이온화 주파수 ν_{iz}가 어디서나 같으면 해는 용기 크기 R, L만으로 정해지는 기본 모드다. 이때 ρ는 k, φ와 무관하다.", 1250, aft=0)])
fy7 = TOP + ch7 + 200000
s.box("사슬 제목", L, fy7, W, 280000, [para("2D (r, z) 모델이 이어야 할 사슬", 1400, HEAD, True)])
chain(s, fy7 + 340000, 600000, [("코일 전류", "I_{0}, k, φ"), ("유도 전기장", "E_{θ}(r, z)"), ("흡수 옴전력", "p_{e}(r, z)"),
                                 ("전자온도", "T_{e}(r, z)"), ("이온화", "G(r, z)"), ("밀도", "n(r, z) → ρ")], "2D 사슬", gap_min=200000)
ny = fy7 + 340000 + 600000 + 80000
s.box("사슬 설명", L, ny, W, BOT - ny, [
    para("n과 T_{e}가 바뀌면 σ_{p}와 E_{θ}도 바뀌므로 사슬을 반복해 맞춘다. 코일 단자 임피던스와 I_{0}도 이 장 해석에서 정한다.", 1200, SUB, algn="ctr", aft=0)])
s.pagenum()
s.write(10)
notes(10, "[대본 · 4:05–5:05 / 60초]",
      "0D 모델이 무엇을 주고 무엇을 주지 못하는지 정리하겠습니다. 입자 균형은 전자온도를, 전력 균형은 밀도를 주는데, 교재도 밝히듯 이것은 공간 평균된 값입니다. "
      "r과 z가 없으니 중앙과 가장자리, 그리고 밀도비를 정의할 수 없고, 코일은 흡수 전력 하나로만 들어옵니다. "
      "그렇다면 0D의 가정을 그대로 공간으로 넓히면 어떨까요. 교재의 확산 방정식에서 이온화 주파수가 어디서나 같다고 두면, 해는 용기 크기만으로 정해지는 기본 모드 하나뿐입니다. "
      "이때는 코일을 어떻게 구동해도 밀도비가 바뀌지 않습니다. 밀도비를 바꾸려면 전자온도와 이온화가 흡수 위치를 따라 공간적으로 달라져야 하고, "
      "이것을 보려면 코일 전류에서 유도 전기장, 흡수 전력, 전자온도, 이온화, 밀도까지를 2D로 이어서 풀어야 합니다. 이 2D 모델의 구성을 이어서 말씀드리겠습니다.",
      "교재 §2.4 p.137: 전력 균형 방정식과 입자 균형 방정식으로 공간 평균된 플라즈마 밀도와 전자온도를 구한다. 단순 모델에서는 T_e가 밀도와 무관하지만, 실제로는 두 식이 결합되어 T_e가 밀도·압력·면적 대 부피비의 함수다. "
      "0D의 쓰임: 2D 계산의 초기값(T_e, n_0)과 부피 수지 점검. "
      "§1.10 p.62 식 (1.75) ∂n/∂t + ∇·Γ = G − L, Γ = −D_a∇n, G = nν_iz, 내부 L = 0 → 식 (1.76). p.63: ν_iz = n_g⟨σ_iz v⟩가 위치에 따라 변하지 않는 것은 전자온도가 공간에서 일정한 경우에 해당. "
      "정상 상태 −D_a∇²n = ν_iz n(생성 = 확산 손실), 벽 n = 0에서 평판 해 n_0cos(πx/l) (1.79), 원통 반경 해 n_0J_0(χ_01 r/R) (1.83), χ_01 ≈ 2.41. "
      "유한 원통은 두 해의 곱이고 고유값 조건 ν_iz/D_a = (χ_01/R)² + (π/L)²가 T_e를 정한다(0D 입자 균형과 같은 역할). 봄 경계를 써도 형상은 용기 크기가 정하고 코일과 무관하다. "
      "사슬의 국소 이온화 G = n n_g K_iz(T_e)는 식 (2.69)의 좌변을 위치별로 쓴 것. T_e(r, z)를 구하는 전자 에너지 식과 장 방정식은 교재 범위 밖이며 팀 2D 모델(이론 정리 4–5장)에서 다룬다. "
      "코일 단자 임피던스(2포트)는 2D 장 해석에서 얻는다(이론 정리 5.4절, 부록 A14–A15).")
print("built")
