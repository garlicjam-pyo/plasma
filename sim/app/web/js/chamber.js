// 챔버 단면 그림: 선택한 양의 (r, z) 지도 위에 코일, 유전체 창, 웨이퍼, 평가 영역을 겹쳐 그린다.
import { COLORS, colormap, fmt, prepare, scale, ticks } from "./draw.js";

// 표시할 수 있는 양: 이름, 단위, 값에 곱할 배수, 전체 영역(창·코일 포함)에 값이 있는지
export const MAPS = {
  ne: { label: "전자 밀도", unit: "10¹⁶ m⁻³", factor: 1e-16, full: false },
  p_abs: { label: "흡수 전력 밀도", unit: "kW/m³", factor: 1e-3, full: false },
  E_abs: { label: "유도 전기장 세기", unit: "V/m", factor: 1, full: true },
  Te: { label: "전자온도", unit: "V", factor: 1, full: false },
};

// 2D 배열(행: z, 열: r)을 작은 그림으로 만든다. 화면에 늘려 그리면 부드럽게 보간된다.
function rasterize(data, lo, hi, cmap) {
  const rows = data.length, cols = data[0].length;
  const off = document.createElement("canvas");
  off.width = cols; off.height = rows;
  const octx = off.getContext("2d");
  const img = octx.createImageData(cols, rows);
  for (let j = 0; j < rows; j++) {
    const src = data[rows - 1 - j];                 // 그림은 위에서 아래로, z 는 아래에서 위로
    for (let i = 0; i < cols; i++) {
      const [r, g, b] = cmap((src[i] - lo) / (hi - lo || 1));
      const p = 4 * (j * cols + i);
      img.data[p] = r; img.data[p + 1] = g; img.data[p + 2] = b; img.data[p + 3] = 255;
    }
  }
  octx.putImageData(img, 0, 0);
  return off;
}

export function drawChamber(canvas, result, geom, which) {
  const { ctx, width, height } = prepare(canvas);
  const spec = MAPS[which];
  const box = { left: 40, right: width - 74, top: 26, bottom: height - 40 };
  const sx = scale(0, geom.R, box.left, box.right);
  const sz = scale(0, geom.z_top, box.bottom, box.top);
  const text = "#c9ccdf";

  // --- 바탕: 플라즈마 위쪽(창·코일 공간)은 어둡게, 유전체 창은 띠로
  ctx.fillStyle = "#1c1f38";
  ctx.fillRect(box.left, box.top, box.right - box.left, box.bottom - box.top);

  // --- 선택한 양의 지도
  const data = result.maps[which];
  const zTop = spec.full ? geom.z_top : geom.L;
  let lo = Infinity, hi = -Infinity;
  for (const row of data) for (const v of row) { if (v < lo) lo = v; if (v > hi) hi = v; }
  if (which !== "Te") lo = 0;                        // 온도만 변화 폭을 키워 보여 준다
  const cmap = colormap(which);
  ctx.imageSmoothingEnabled = true;
  ctx.drawImage(rasterize(data, lo, hi, cmap), box.left, sz(zTop), box.right - box.left, sz(0) - sz(zTop));

  // --- 유전체 창
  ctx.fillStyle = spec.full ? "rgba(255,255,255,0.10)" : "rgba(214,226,240,0.22)";
  ctx.fillRect(box.left, sz(geom.L + geom.window), box.right - box.left, sz(geom.L) - sz(geom.L + geom.window));
  ctx.fillStyle = text; ctx.textAlign = "left"; ctx.textBaseline = "middle";
  ctx.fillText("유전체 창", box.left + 8, sz(geom.L + geom.window / 2));

  // --- 코일: 전류가 클수록 원을 크게
  const maxI = Math.max(result.heating.I_in, result.heating.I_out, 1e-6);
  const coil = (radii, current, color, name) => {
    const rad = 4 + 5 * Math.sqrt(current / maxI);
    for (const r of radii) {
      ctx.beginPath(); ctx.arc(sx(r), sz(geom.z_coil), rad, 0, 2 * Math.PI);
      ctx.fillStyle = color; ctx.fill(); ctx.strokeStyle = "#fff"; ctx.lineWidth = 1.2; ctx.stroke();
    }
    const mid = radii.reduce((a, b) => a + b, 0) / radii.length;
    ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "bottom";
    ctx.fillText(`${name} ${fmt(current, 3)} A`, sx(mid), sz(geom.z_coil) - 12);
  };
  coil(geom.r_in, result.heating.I_in, COLORS.coilIn, "안쪽 코일");
  coil(geom.r_out, result.heating.I_out, COLORS.coilOut, "바깥쪽 코일");

  // --- 관측 높이와 평가 영역 (중앙: 파랑, 가장자리: 주황)
  ctx.setLineDash([5, 4]); ctx.strokeStyle = "rgba(255,255,255,0.85)"; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(sx(0), sz(geom.z_w)); ctx.lineTo(sx(geom.R_w), sz(geom.z_w)); ctx.stroke();
  ctx.setLineDash([]);
  const zone = (r0, r1, color, name) => {
    ctx.fillStyle = color; ctx.fillRect(sx(r0), box.bottom + 3, sx(r1) - sx(r0), 6);
    ctx.fillStyle = text; ctx.textAlign = "center"; ctx.textBaseline = "top";
    ctx.fillText(name, (sx(r0) + sx(r1)) / 2, box.bottom + 22);
  };
  zone(0, geom.r_c, COLORS.coilIn, "중앙");
  zone(geom.r_1, geom.r_2, COLORS.coilOut, "가장자리");

  // --- 축 눈금
  ctx.fillStyle = text; ctx.strokeStyle = "rgba(255,255,255,0.35)"; ctx.lineWidth = 1;
  ctx.textAlign = "center"; ctx.textBaseline = "top";
  for (const r of ticks(0, geom.R, 6)) {
    ctx.beginPath(); ctx.moveTo(sx(r), box.bottom); ctx.lineTo(sx(r), box.bottom + 3); ctx.stroke();
    if (r !== 0 && Math.abs(r - (geom.r_1 + geom.r_2) / 2) > 2) ctx.fillText(String(r), sx(r), box.bottom + 10);
  }
  ctx.textAlign = "right"; ctx.fillText("r [cm]", box.right, box.bottom + 24);
  ctx.textAlign = "right"; ctx.textBaseline = "middle";
  for (const z of ticks(0, geom.z_top, 5)) ctx.fillText(String(z), box.left - 6, sz(z));
  ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.fillText("z [cm]", 4, 6);

  // --- 색 눈금
  const bar = { x: box.right + 16, w: 12 };
  for (let y = box.top; y < box.bottom; y++) {
    const [r, g, b] = cmap(1 - (y - box.top) / (box.bottom - box.top));
    ctx.fillStyle = `rgb(${r},${g},${b})`; ctx.fillRect(bar.x, y, bar.w, 1.5);
  }
  ctx.fillStyle = text; ctx.textAlign = "left"; ctx.textBaseline = "middle";
  ctx.fillText(fmt(hi * spec.factor, 3), bar.x + bar.w + 5, box.top + 4);
  ctx.fillText(fmt(lo * spec.factor, 3), bar.x + bar.w + 5, box.bottom - 4);
  ctx.textBaseline = "top"; ctx.textAlign = "right";
  ctx.fillText(`${spec.label} [${spec.unit}]`, width - 6, 6);
}
