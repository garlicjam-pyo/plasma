"""변압기 모델 등가회로 그림 (단일 코일, 이중 코일). 기호만 그림에 넣고 한글 설명은 슬라이드 글상자로 둔다."""
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["mathtext.fontset"] = "cm"
import schemdraw
import schemdraw.elements as elm

schemdraw.use("matplotlib")
INK, BLUE, ORANGE, NAVY = "#1F2340", "#3366CC", "#D9622B", "#303399"
FS = 18


def coil_loop(d, x, ytop, ybot, xl, col, R, L, V, lab_dx=-0.55):
    """1차 회로: 오른쪽 변에 권선(볼록면이 오른쪽), 위 변에 저항, 왼쪽 변에 전원."""
    d.add(elm.Inductor(loops=4).at((x, ytop)).down().toy(ybot).flip().color(col))
    d.add(elm.Label().at((x + lab_dx, (ytop + ybot) / 2)).label(L).color(col))
    d.add(elm.Line().at((x, ytop)).left().length(0.35).color(col))
    d.add(elm.Resistor().left().tox(xl + 0.35).label(R).color(col))
    d.add(elm.Line().left().tox(xl).color(col))
    d.add(elm.SourceSin().down().toy(ybot).label(V, loc="bot", ofst=0.2).color(col))
    d.add(elm.Line().right().tox(x).color(col))


def plasma_loop(d, x, ytop, ybot, loops):
    """2차 회로(플라즈마 고리): 왼쪽 변에 권선 L_g(볼록면이 왼쪽), 위 변에 L_p, 오른쪽 변에 R_p."""
    d.add(elm.Inductor(loops=loops).at((x, ytop)).down().toy(ybot).color(NAVY))
    d.add(elm.Label().at((x + 0.5, (ytop + ybot) / 2)).label("$L_g$").color(NAVY))
    d.add(elm.Line().at((x, ytop)).right().length(0.35).color(NAVY))
    d.add(elm.Inductor(loops=3).right().length(1.7).label("$L_p$").color(NAVY))
    d.add(elm.Line().right().length(0.35).color(NAVY))
    d.add(elm.Resistor().down().toy(ybot).label("$R_p$", loc="bot").color(NAVY))
    d.add(elm.Line().left().tox(x).color(NAVY))


def mutual(d, p0, p1, lab, lab_at):
    d.add(elm.Arrow(double=True, headwidth=0.16, headlength=0.2).at(p0).to(p1).color(INK).linewidth(1.1))
    d.add(elm.Label().at(lab_at).label(lab).color(INK))


def single():
    d = schemdraw.Drawing(show=False)
    d.config(unit=2.0, fontsize=FS, color=INK, lw=1.5)
    coil_loop(d, 3.2, 3.0, 0.0, 0.0, INK, "$R_a$", "$L_a$", "$V_\\mathrm{RF}$")
    plasma_loop(d, 4.6, 3.0, 0.0, 4)
    mutual(d, (3.5, 1.5), (4.3, 1.5), "$M$", (3.9, 1.85))
    return d


def dual(with_mio):
    d = schemdraw.Drawing(show=False)
    d.config(unit=2.0, fontsize=FS, color=INK, lw=1.5)
    coil_loop(d, 3.2, 5.4, 3.2, 0.0, BLUE, "$R_i$", "$L_i$", "$V_\\mathrm{in}$")
    coil_loop(d, 3.2, 2.2, 0.0, 0.0, ORANGE, "$R_o$", "$L_o$", "$V_\\mathrm{out}$")
    plasma_loop(d, 5.0, 5.4, 0.0, 4)
    mutual(d, (3.5, 4.2), (4.7, 3.1), "$M_{ip}$", (4.35, 4.15))
    mutual(d, (3.5, 1.2), (4.7, 2.3), "$M_{op}$", (4.35, 1.25))
    if with_mio:
        mutual(d, (3.2, 3.1), (3.2, 2.3), "$M_{io}$", (2.65, 2.7))
    return d


single().save("fig_single.png", dpi=400, transparent=True)
dual(False).save("fig_dual.png", dpi=400, transparent=True)
dual(True).save("fig_dual_mio.png", dpi=400, transparent=True)
from PIL import Image
for f in ("fig_single.png", "fig_dual.png", "fig_dual_mio.png"):
    print(f, Image.open(f).size)
