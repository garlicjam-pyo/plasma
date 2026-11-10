"""README 지시에 따라 슬라이드 3–8을 다시 만든다 (기존 양식 요소를 그대로 재사용)."""
import os
import re
import shutil
from xml.sax.saxutils import escape
from PIL import Image

U = "un"                      # 풀어 둔 pptx
EQ = "eq"                     # 새 식 PNG
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

# ===================== 3. 문제 정의와 제어 목표 (slide4.xml) =====================
s = Slide()
s.frame("문제 정의와 제어 목표", "설계 과제  ·  중앙·가장자리 밀도비의 독립 조절",
        "목표는 평균 밀도 n̄_{w}를 유지하면서 밀도비 ρ를 바꾸는 것이다.",
        "[정의] 축대칭 면적 요소 dA = 2πr dr에 따른 면적 가중 평균. 경계 r_{c}, r_{1}, r_{2}, R_{w}(≥ r_{2})와 관측 높이 z_{w}는 설계 단계에서 정한다. 부록 A3.")
s.box("과제 문단", L, 1335000, W, 1150000, [
    para("**문제 정의**  하나의 챔버에서 중앙부와 가장자리의 플라즈마 밀도를 독립적으로 조절할 수 있는 소스를 설계한다. "
         "두 영역의 밀도를 함께 높이거나 낮추는 데 그치지 않고, 밀도비를 원하는 값으로 조정할 수 있는 구조와 구동 방식을 제안한다.", 1350, aft=700),
    para("**제어 목표**  중앙부와 가장자리의 밀도비 ρ = n_{c}/n_{edge}를 전체 밀도 수준과 따로 조정한다.", 1350)])
# 반단면 개략도 (기존 슬라이드 4의 도형을 아래로 옮기고 기호 표기를 더함)
dy = 2950000 - 1943100
s.box("개략도 제목", 548640, 2600000, 3840480, 230000, [para("반단면 개략도: 축 r = 0에서 측벽까지", 1200, SUB, True)])
s.shape("rect", "석영 창", 548640, 2139696 + dy, 3840480, 365760, fill="D6E2F0")
s.shape("rect", "플라즈마", 548640, 2482596 + dy, 3840480, 1097280, fill="F7F9FC")
s.shape("rect", "웨이퍼", 548640, 3557016 + dy, 2743200, 45720, fill="5F6779")
s.line("측벽", 4389120, 2505456 + dy, 0, 1097280, INK)
s.line("바닥", 548640, 3602736 + dy, 3840480, 0, INK)
s.line("축", 548640, 1901952 + dy, 0, 1700784, "8C93A3")
for k, xx in enumerate([1028700, 1577340, 2125980, 2674620, 3223260, 3771900]):
    s.shape("ellipse", f"코일 {k + 1}", xx, 1943100 + dy, 137160, 137160, fill=BLUE if k < 3 else ORANGE)
s.shape("rect", "중앙 영역", 548640, 3342132 + dy, 914400, 64008, fill=BLUE)
s.shape("rect", "가장자리 영역", 2743200, 3342132 + dy, 457200, 64008, fill=ORANGE)
s.box("n_c 표기", 566928, 3099816 + dy, 914400, 274320, [para("n_{c}", 1250, BLUE, True)])
s.box("n_edge 표기", 2697480, 3099816 + dy, 914400, 274320, [para("n_{edge}", 1250, ORANGE_T, True)])
s.box("관측면 표기", 3291840, 3300000 + dy, 1050000, 230000, [para("z = z_{w}", 1200, SUB)])
for lab, xx in [("0", 548640), ("r_{c}", 1463040), ("r_{1}", 2743200), ("r_{2}", 3200400)]:
    s.box(f"반경 {lab}", xx - 228600, 3640000 + dy, 457200, 230000, [para(lab, 1200, SUB, algn="ctr")])
s.box("코일 범례", 548640, 4900000, 3840480, 420000,
      [para("[[3366CC|●]] 안쪽 코일   [[D9622B|●]] 바깥쪽 코일", 1200, SUB, aft=100),
       para("n(r, z_{w}): 관측 높이 z_{w}에서의 전자 밀도", 1200, SUB, aft=0)])
# 평가 지표 상자
bx, bw = 4572000, 4114800
s.box("평가 지표 상자", bx, 2600000, bw, 2700000, None, fill="EEF3FB")
s.box("평가 지표 제목", bx + 137160, 2660000, bw - 274320, 260000, [para("평가 지표 (면적 가중 평균)", 1400, HEAD, True)])
y = 2950000
for m, lab in [("eq_nc.png", "중앙 영역"), ("eq_nedge.png", "가장자리 고리"), ("eq_nw.png", "관측면 전체")]:
    w, h = s.eq(m, bx + 137160, y, emu_per_px=1150)
    s.box("기호 " + m, bx + 137160 + 2400000, y + h // 2 - 150000, bw - 137160 - 2400000 - 60000, 300000,
          [para(lab, 1200, SUB)], anchor="ctr")
    y += h + 30000
s.eq("eq_rhotgt.png", bx + 137160, y + 50000, emu_per_px=1150)
s.pagenum()
s.write(4)
notes(4, "[대본 · 0:20–1:20 / 60초]",
      "저희 과제는 하나의 챔버에서 중앙부와 가장자리의 플라즈마 밀도를 독립적으로 조절할 수 있는 소스를 설계하는 것입니다. "
      "두 영역을 함께 올리거나 내리는 것이 아니라, 밀도비를 원하는 값으로 맞추는 것이 목표입니다. "
      "이를 식으로 쓰기 위해 웨이퍼 위 관측 높이에서 중앙 영역과 가장자리 고리의 면적 평균 밀도를 n_c, n_edge로 두고, 그 비를 ρ라고 하겠습니다. "
      "전체 수준은 관측면 전체의 평균 n̄_w로 봅니다. 그러면 목표는 n̄_w는 유지하고 ρ만 바꾸는 것입니다.",
      "과제 정의: IC-PBL 주제 3. 면적 가중 평균은 축대칭 면적 요소 dA = 2πr dr에서 나온다. "
      "평가 영역 경계 r_c, r_1, r_2, R_w와 관측 높이 z_w는 설계 단계에서 정한다. 목표는 한 영역을 고정하고 다른 영역만 바꾸는 것과 다르다. 상세 정의: 부록 A3.")

# ===================== 4. 단일 코일 (slide5.xml) =====================
s = Slide()
s.frame("단일 코일 ICP: 입력은 전력 하나", "변압기 모델과 0D 전력 균형  ·  교재 §2.3.4, §2.4",
        "단일 코일로는 평균 밀도를 유지한 채 밀도비를 바꿀 수 없다.",
        "정진욱 (2026) §2.3.4 pp.123–125 식 (2.54)–(2.57), §2.4 pp.133–138 식 (2.66)–(2.68). 유도: 부록 A10, A14.")
cw = 4023360
s.card("변압기 모델 카드", L, 1335000, cw, 2380000, [para("변압기 모델: 코일에서 본 플라즈마", 1400, HEAD, True)])
w, h = s.eq("image72.png", L + 109728, 1680000, emu_per_px=1550, max_w=cw - 219456)
w2, h2 = s.eq("eq_pabs1.png", L + 109728, 1680000 + h + 30000, emu_per_px=1550, max_w=cw - 219456)
s.box("변압기 기호", L + 109728, 1680000 + h + h2 + 70000, cw - 219456, 1335000 + 2380000 - (1680000 + h + h2 + 70000) - 40000, [
    para("M: 코일–플라즈마 상호 인덕턴스", 1200, SUB, bullet=True, aft=200),
    para("Z_{p} = R_{p} + jω(L_{g} + L_{p}): 플라즈마 고리의 임피던스", 1200, SUB, bullet=True, aft=200),
    para("Re(ω^{2}M^{2}/Z_{p}) > 0: 저항성 부하로 보인다", 1200, SUB, bullet=True, aft=0)])
x2 = L + cw + 182880
s.card("0D 전력 균형 카드", x2, 1335000, cw, 2380000, [para("0D 전력 균형: 밀도 수준", 1400, HEAD, True)])
w, h = s.eq("image23.png", x2 + 109728, 1680000, emu_per_px=1550, max_w=cw - 219456)
s.box("전력 균형 기호", x2 + 109728, 1690000 + h + 80000, cw - 219456, 1335000 + 2380000 - (1690000 + h + 80000) - 60000, [
    para("ε_{T}: 이온–전자 쌍 하나를 잃을 때의 총 에너지 비용", 1200, SUB, bullet=True, aft=200),
    para("u_{B}: 봄 속도,  A_{eff}: 유효 손실 면적", 1200, SUB, bullet=True, aft=200),
    para("T_{e}, ε_{T}, u_{B}, A_{eff}가 크게 변하지 않으면 n_{*}는 P_{abs}에 비례한다", 1200, SUB, bullet=True, aft=0)])
s.box("단일 입력 상자", L, 3810000, W, 1500000, None, fill="F4F6FA")
s.box("단일 입력 제목", L + 109728, 3870000, W - 219456, 280000, [para("입력이 하나면 출력 두 개를 따로 정할 수 없다", 1400, HEAD, True)])
w, h = s.eq("eq_single.png", L, 4170000, emu_per_px=1550, max_w=W - 400000, center_w=W)
s.box("단일 입력 설명", L + 109728, 4170000 + h + 50000, W - 219456, 5310000 - (4170000 + h + 50000) - 30000, [
    para("압력·주파수·코일 형상을 고정하면 운전 상태는 공급 전력 P 하나로 정해진다.", 1300, aft=150),
    para("0D에서 n_{*} ∝ P_{abs}이므로 평균 밀도는 P에 따라 단조 증가한다. n̄_{w}를 유지하면 P가 고정되고 ρ도 바뀌지 않는다.", 1300, aft=0)])
s.pagenum()
s.write(5)
notes(5, "[대본 · 1:20–2:20 / 60초]",
      "코일이 하나일 때를 교재의 변압기 모델로 보겠습니다. 코일을 1차 회로, 플라즈마의 방위각 방향 전류를 2차 회로로 보면, 코일 쪽에서 플라즈마는 ω²M²/Z_p라는 임피던스로 보이고, "
      "그 실수부가 양수라서 플라즈마로 전력이 전달됩니다. 흡수 전력은 코일 전류의 제곱에 비례합니다. 그리고 0D 전력 균형에서 밀도 수준은 흡수 전력에 비례합니다. "
      "그런데 압력과 코일 형상을 고정하면 단일 코일에서 바꿀 수 있는 것은 전력 하나뿐입니다. 평균 밀도를 유지하려면 전력을 바꿀 수 없고, 그러면 밀도비도 그대로입니다. "
      "그래서 단일 코일로는 목표를 이룰 수 없습니다.",
      "정진욱 (2026) §2.3.4 pp.123–125 식 (2.54)–(2.57): 변압기 모델, Re(ω²M²/Z_p) = ω²M²R_p/[R_p² + ω²(L_g + L_p)²] > 0. "
      "§2.4 pp.133–138 식 (2.66)–(2.68): 전력 균형 n_* = P_abs/(eε_T u_B A_eff). 단일 전류의 위상은 시간 원점의 선택이므로 시간 평균 전력에 영향이 없다. "
      "실제 장치에서는 전력이 밀도와 표피 효과를 바꿔 형상도 변하지만, 그 변화도 P 하나의 함수이므로 n̄_w와 따로 정할 수 없다. 유도: 부록 A10, A14.")

# ===================== 5. 이중 코일 0D (slide6.xml) =====================
s = Slide()
s.frame("이중 코일 ICP의 0D 기술", "두 1차 코일과 하나의 플라즈마 고리  ·  변압기 모델의 확장",
        "0D에서 k와 φ는 흡수 전력의 크기로만 나타나고, 밀도비 ρ는 정의되지 않는다.",
        "정진욱 (2026) §2.3.4 식 (2.54)–(2.57)의 두 1차 코일 확장 [유도]. 플라즈마를 하나의 2차 고리로 본 등가회로, M은 실수.")
s.box("고리 전류 제목", L, 1335000, W, 280000, [para("플라즈마 고리 전류", 1400, HEAD, True)])
w, h = s.eq("eq_sec.png", L + 45720, 1650000, emu_per_px=1800)
s.eq("eq_cur.png", L + 45720 + w + 450000, 1650000 + 10000, emu_per_px=1800)
yy = 1650000 + h + 120000
s.box("흡수 전력 제목", L, yy, W, 280000, [para("흡수 전력", 1400, HEAD, True)])
w, h = s.eq("eq_pabs2.png", L, yy + 320000, emu_per_px=1800, max_w=W - 200000, center_w=W)
yy = yy + 320000 + h + 60000
s.box("세 항 설명", L, yy, W, 520000, [
    para("괄호 안의 세 항은 안쪽 코일 항, 바깥쪽 코일 항, **간섭항**이다. 간섭항은 두 코일이 유도한 플라즈마 전류가 보강하거나 상쇄하는 효과다(M_{ip}M_{op} > 0이면 φ = 0에서 보강, φ = π에서 상쇄).", 1300, aft=0)])
yy += 560000
s.box("기호 설명", L, yy, W, 300000, [
    para("M_{ip}, M_{op}: 안쪽·바깥쪽 코일과 플라즈마 고리 사이의 상호 인덕턴스   I_{p}: 플라즈마 고리(방위각 방향 유도 전류)의 등가 전류", 1200, SUB, aft=0)])
s.box("0D 해석 상자", L, 4200000, W, 1110000, [
    para("0D에서 k와 φ가 보이는 방식", 1400, HEAD, True, aft=300),
    para("k와 φ는 P_{abs}라는 값 하나로만 들어가 밀도 수준 n_{*} ∝ P_{abs}를 바꾼다. 어느 위치를 데우는지는 이 모델에 없으므로, 같은 P_{abs}를 주는 (k, φ) 조합은 0D에서 서로 구별되지 않는다.", 1300, aft=0)],
      fill="F4F6FA", inset=109728)
s.pagenum()
s.write(6)
notes(6, "[대본 · 2:20–3:15 / 55초]",
      "코일이 둘이면 같은 변압기 모델에서 1차 코일이 두 개가 됩니다. 플라즈마 고리 전류는 두 코일이 각각 유도한 몫의 합이고, 흡수 전력을 계산하면 괄호 안에 세 항이 나옵니다. "
      "안쪽 코일 항, 바깥쪽 코일 항, 그리고 cos φ가 붙은 간섭항입니다. 간섭항은 두 코일이 만든 플라즈마 전류가 서로 보강하거나 상쇄하는 효과입니다. "
      "그런데 0D에서는 k와 φ가 결국 흡수 전력이라는 값 하나로만 들어가고, 밀도 수준만 바꿉니다. 어느 위치를 데우는지는 이 모델에 없습니다.",
      "정진욱 (2026) §2.3.4 식 (2.54)–(2.57)을 두 1차 코일로 확장. 2차 회로식에서 I_p = jω(M_ip I_in + M_op I_out)/Z_p, P_abs = ½R_p|I_p|². "
      "M은 실수로 두며 부호는 권선 방향에 따른다. 플라즈마를 하나의 2차 고리로 보는 근사이므로, 두 코일이 서로 다른 반경의 플라즈마 전류와 결합하는 효과는 나타나지 않는다. "
      "공간 분포에서의 간섭(위치마다 다른 위상)은 2D 장 해석에서 다룬다.")

# ===================== 6. 세 독립 변수 (slide7.xml) =====================
s = Slide()
s.frame("두 코일 전류의 독립 변수는 세 개다", "제어 입력  ·  상대 진폭 k, 상대 위상 φ, 총 공급 전력 P_{tot}",
        "제어 입력은 (k, φ, P_{tot}) 세 개이고, 맞춰야 할 출력은 (n̄_{w}, ρ) 두 개다.",
        "[유도] 2포트 페이저 전력. 전력 균형: 정진욱 (2026) §2.4 식 (2.66)–(2.68). 상세: 부록 A4–A5.")
w, h = s.eq("image44.png", L, 1335000, emu_per_px=1330, center_w=W)
s.box("공통 위상", L, 1335000 + h + 40000, W, 280000, [
    para("공통 위상은 시간 평균 전력에 영향을 주지 않으므로, 독립 변수는 I_{0}, k, φ 세 개다.", 1300, aft=0)])
cy, ch, cw3 = 2620000, 960000, 2651760
for k, (head, body, col) in enumerate([
        ("상대 진폭 k = |I_{out}|/|I_{in}|", "두 코일 전류 크기의 비. 흡수 전력의 비가 아니다.", BLUE),
        ("상대 위상 φ", "두 코일 전류의 위상차. 0D에서는 간섭항 cos φ로 들어간다.", ORANGE_T),
        ("총 공급 전력 P_{tot}", "I_{0} 대신 지정한다. 아래 식으로 I_{0}가 정해진다.", HEAD)]):
    x = L + k * (cw3 + 137160)
    s.card(f"입력 카드 {k + 1}", x, cy, cw3, ch, [para(head, 1350, col, True, aft=300), para(body, 1250, aft=0)], accent=col)
s.box("전력 제목", L, 3690000, W, 280000, [para("전력이 전류 크기를 정한다", 1400, HEAD, True)])
w, h = s.eq("image13.png", L, 4010000, emu_per_px=1500, max_w=4900000)
w2, h2 = s.eq("image47.png", L, 4010000 + h + 60000, emu_per_px=1500, max_w=4900000)
s.box("전력 설명", L + 5050000, 4010000, W - 5050000, 1300000, [
    para("Z는 플라즈마 상태(밀도, 전자온도)에 의존하므로, 같은 P_{tot}에서도 I_{0}는 k, φ와 플라즈마 상태에 따라 달라진다.", 1200, bullet=True, aft=300),
    para("정합기·코일 손실 때문에 P_{tot}, P_{port}, P_{abs}는 서로 다르다.", 1200, bullet=True, aft=300),
    para("a = [1, ke^{jφ}]^{T}, a^{H}: a의 켤레 전치", 1200, SUB, bullet=True, aft=0)])
s.pagenum()
s.write(7)
notes(7, "[대본 · 3:15–4:05 / 50초]",
      "두 코일 전류는 복소수 두 개, 즉 크기 둘과 위상 둘입니다. 공통 위상은 시간 원점을 어디에 두느냐의 문제라 시간 평균 전력에 영향을 주지 않으므로, "
      "독립 변수는 안쪽 전류 크기 I_0, 상대 진폭 k, 상대 위상 φ 세 개입니다. 실제로는 I_0 대신 총 공급 전력을 지정하고, 포트 전력 식에서 I_0가 정해집니다. "
      "이때 임피던스가 플라즈마 상태에 의존하므로 같은 전력에서도 전류는 k, φ와 플라즈마 상태에 따라 달라집니다. "
      "정리하면 입력은 k, φ, P_tot 세 개, 맞춰야 할 출력은 평균 밀도와 밀도비 두 개입니다.",
      "식 (1.9) I = I₀[1, ke^(jφ)]ᵀ, k = |I_out|/|I_in|, φ = arg I_out − arg I_in. 식 (1.13) P_port = (I₀²/2)Re[aᴴZa], I₀ = √(2P_port/Re(aᴴZa)): "
      "분모가 양수이고 k, φ를 구동기에서 실현할 수 있을 때. P_tot = P_match,loss + P_port, P_port = P_coil,loss + P_abs. 정진욱 (2026) §2.4 식 (2.66)–(2.68). 상세: 부록 A4–A5.")

# ===================== 7. 두 코일의 결합 (slide8.xml) =====================
s = Slide()
s.frame("두 코일은 플라즈마를 통해 결합한다", "코일 포트  ·  2포트 임피던스와 상호 결합",
        "두 코일은 직접 결합과 플라즈마를 통한 결합으로 묶여 있어, k는 흡수 전력의 비율이 아니다.",
        "정진욱 (2026) §2.3.4 식 (2.54)–(2.57)의 두 코일 확장 [유도]. 등가회로이므로 공간 분포는 나타내지 않는다. 상세: 부록 A14–A15.")
s.box("단자 제목", L, 1335000, W, 280000, [para("코일 포트의 단자 관계", 1400, HEAD, True)])
w, h = s.eq("eq_port.png", L, 1650000, emu_per_px=1800, center_w=W)
yy = 1650000 + h + 120000
s.box("성분 제목", L, yy, W, 280000, [para("0D 변압기 모델에서 얻은 성분", 1400, HEAD, True)])
w, h = s.eq("eq_zmat.png", L, yy + 320000, emu_per_px=1800, max_w=W - 200000, center_w=W)
yy = yy + 320000 + h + 60000
s.box("성분 기호", L, yy, W, 520000, [
    para("M_{io}: 두 코일 사이의 직접 상호 인덕턴스   ω^{2}M_{ip}M_{op}/Z_{p}: 같은 플라즈마 고리를 매개로 한 결합   Z_{oo}도 Z_{ii}와 같은 꼴이다", 1200, SUB, aft=0)])
cy = 3600000
ch = 5310000 - cy
s.card("비대각 카드", L, cy, cw, ch, [
    para("비대각 성분이 뜻하는 것", 1400, HEAD, True, aft=400),
    para("전류 구동: 한쪽 코일의 전류를 바꾸면 다른 쪽 코일에 필요한 단자 전압이 바뀐다.", 1250, bullet=True, aft=300),
    para("전압 구동: 한쪽 코일의 전압을 바꾸면 다른 쪽 코일의 전류가 바뀐다.", 1250, bullet=True, aft=0)])
s.card("k 해석 카드", L + cw + 182880, cy, cw, ch, [
    para("k는 흡수 전력의 비가 아니다", 1400, HEAD, True, aft=400),
    para("흡수 전력에는 간섭항이 있어 안쪽·바깥쪽 코일의 몫으로 나눌 수 없다.", 1250, bullet=True, aft=300),
    para("Z_{p}가 플라즈마 밀도와 충돌 주파수에 따라 바뀌므로, 같은 k, φ라도 포트 조건이 달라진다.", 1250, bullet=True, aft=0)])
s.pagenum()
s.write(8)
notes(8, "[대본 · 4:05–4:55 / 50초]",
      "두 코일의 단자 관계는 2×2 임피던스로 씁니다. 변압기 모델을 두 코일로 확장하면 대각 성분에는 각 코일의 반사 임피던스가, "
      "비대각 성분에는 두 코일 사이의 직접 상호 인덕턴스와 같은 플라즈마 고리를 매개로 한 결합이 들어갑니다. 그래서 한쪽 코일의 전류를 바꾸면 다른 쪽 코일에 필요한 전압이 바뀝니다. "
      "또 흡수 전력에 간섭항이 있어 안쪽과 바깥쪽 코일의 몫으로 나눌 수 없고, 플라즈마 임피던스는 상태에 따라 바뀝니다. 따라서 k는 흡수 전력의 비율이 아닙니다.",
      "V_in = (R_i + jωL_i)I_in + jωM_io I_out − jωM_ip I_p에 I_p = jω(M_ip I_in + M_op I_out)/Z_p를 대입하면 Z_ii, Z_io를 얻는다. Z_io = Z_oi(상호성). "
      "jωM_io 항의 부호는 권선 방향과 상호 인덕턴스 정의에 따른다. 정진욱 (2026) §2.3.4 식 (2.54)–(2.57)의 두 코일 확장. "
      "2D 모델에서는 같은 단자 관계를 장 해(코일 전류가 만드는 E_θ와 플라즈마 전류)로부터 계산해 이 식과 연결한다. 상세: 부록 A14–A15.")
print("built")
