// 선 그래프 두 개(밀도 분포, 온도·가열)와 목표 선택 판.
import { COLORS, fmt, prepare, scale, ticks } from "./draw.js";

// 그래프 틀: 바탕 눈금과 축 이름을 그리고 변환 함수를 돌려준다.
function frame(ctx, width, height, { xRange, yRange, xLabel, yLabel, right = 16 }) {
  const box = { left: 46, right: width - right, top: 14, bottom: height - 36 };
  const sx = scale(xRange[0], xRange[1], box.left, box.right);
  const sy = scale(yRange[0], yRange[1], box.bottom, box.top);
  ctx.strokeStyle = COLORS.grid; ctx.fillStyle = COLORS.muted; ctx.lineWidth = 1;
  ctx.textAlign = "right"; ctx.textBaseline = "middle";
  for (const v of ticks(yRange[0], yRange[1], 5)) {
    ctx.beginPath(); ctx.moveTo(box.left, sy(v)); ctx.lineTo(box.right, sy(v)); ctx.stroke();
    ctx.fillText(String(v), box.left - 6, sy(v));
  }
  ctx.textAlign = "center"; ctx.textBaseline = "top";
  for (const v of ticks(xRange[0], xRange[1], 6)) ctx.fillText(String(v), sx(v), box.bottom + 6);
  ctx.fillText(xLabel, (box.left + box.right) / 2, box.bottom + 20);
  ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.fillText(yLabel, 4, 0);
  ctx.strokeStyle = COLORS.muted;
  ctx.beginPath(); ctx.moveTo(box.left, box.bottom); ctx.lineTo(box.right, box.bottom); ctx.stroke();
  return { box, sx, sy };
}

function path(ctx, xs, ys, sx, sy) {
  ctx.beginPath();
  xs.forEach((x, i) => (i ? ctx.lineTo(sx(x), sy(ys[i])) : ctx.moveTo(sx(x), sy(ys[i]))));
}

// 웨이퍼 높이의 밀도 분포. 중앙·가장자리 영역을 칠하고 영역 평균을 굵은 선으로 표시한다.
export function drawProfile(canvas, result, previous, geom) {
  const { ctx, width, height } = prepare(canvas);
  const n = result.n_wafer.map((v) => v * 1e-16);
  const before = previous ? previous.n_wafer.map((v) => v * 1e-16) : null;
  const top = Math.max(...n, ...(before || [0])) * 1.15;
  const { box, sx, sy } = frame(ctx, width, height, { xRange: [0, geom.R], yRange: [0, top], xLabel: "r [cm]", yLabel: "10¹⁶ m⁻³" });
  const band = (r0, r1, color) => { ctx.fillStyle = color; ctx.fillRect(sx(r0), box.top, sx(r1) - sx(r0), box.bottom - box.top); };
  band(0, geom.r_c, "rgba(42,120,214,0.10)");
  band(geom.r_1, geom.r_2, "rgba(232,99,43,0.13)");
  if (before) { path(ctx, previous.r_cm, before, sx, sy); ctx.strokeStyle = "#b9bfd0"; ctx.lineWidth = 1.5; ctx.stroke(); }
  path(ctx, result.r_cm, n, sx, sy); ctx.strokeStyle = COLORS.ink; ctx.lineWidth = 2.4; ctx.stroke();
  const m = result.metrics;
  const mark = (r0, r1, value, color, label, align) => {
    ctx.strokeStyle = color; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(sx(r0), sy(value)); ctx.lineTo(sx(r1), sy(value)); ctx.stroke();
    ctx.fillStyle = color; ctx.textAlign = "left"; ctx.textBaseline = "bottom";   // 가장자리 이름은 띠 오른쪽에 둔다
    ctx.fillText(`${label} ${fmt(value, 3)}`, align === "left" ? sx(r0) + 2 : sx(r1) + 6, sy(value) - 5);
  };
  mark(0, geom.r_c, m.n_c * 1e-16, COLORS.coilIn, "중앙", "left");
  mark(geom.r_1, geom.r_2, m.n_edge * 1e-16, COLORS.coilOut, "가장자리", "after");
  ctx.setLineDash([4, 4]); ctx.strokeStyle = COLORS.muted; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(sx(0), sy(m.n_bar * 1e-16)); ctx.lineTo(sx(geom.R_w), sy(m.n_bar * 1e-16)); ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = COLORS.muted; ctx.textAlign = "right"; ctx.textBaseline = "top";
  ctx.fillText("점선: 평균", box.right, box.top);
}

// 전자온도(왼쪽 축, 검정 선)와 z 로 적분한 가열(오른쪽 축, 주황 면).
export function drawHeating(canvas, result, geom) {
  const { ctx, width, height } = prepare(canvas);
  const Te = result.Te_r, S = result.S.map((v) => v * 1e-3);
  const pad = (Math.max(...Te) - Math.min(...Te)) * 0.15 + 0.01;
  const yRange = [Math.min(...Te) - pad, Math.max(...Te) + pad];
  const { box, sx, sy } = frame(ctx, width, height, { xRange: [0, geom.R], yRange, xLabel: "r [cm]", yLabel: "전자온도 [V]", right: 50 });
  const s2 = scale(0, Math.max(...S) * 1.15, box.bottom, box.top);
  path(ctx, result.r_cm, S, sx, s2);
  ctx.lineTo(sx(result.r_cm.at(-1)), box.bottom); ctx.lineTo(sx(result.r_cm[0]), box.bottom); ctx.closePath();
  ctx.fillStyle = "rgba(232,99,43,0.22)"; ctx.fill();
  path(ctx, result.r_cm, S, sx, s2); ctx.strokeStyle = COLORS.coilOut; ctx.lineWidth = 1.5; ctx.stroke();
  path(ctx, result.r_cm, Te, sx, sy); ctx.strokeStyle = COLORS.ink; ctx.lineWidth = 2.4; ctx.stroke();
  ctx.fillStyle = COLORS.coilOut; ctx.textAlign = "left"; ctx.textBaseline = "middle";
  for (const v of ticks(0, Math.max(...S) * 1.15, 4)) ctx.fillText(String(v), box.right + 6, s2(v));
  ctx.textAlign = "right"; ctx.textBaseline = "top"; ctx.fillText("가열 [kW/m²]", width - 2, 0);
}

// 목표 선택 판: 가로 평균 밀도, 세로 밀도비. 도달 가능 영역, 현재 상태, 목표, 맞춰 간 궤적을 그린다.
// 반환값의 toValue 로 화면 좌표를 (평균 밀도, 밀도비)로 바꾼다.
export function drawPad(canvas, { limits, target, current, band, trajectory }) {
  const { ctx, width, height } = prepare(canvas);
  const [n0, n1] = limits.n_target_1e16, [r0, r1] = limits.rho_target;
  const { box, sx, sy } = frame(ctx, width, height, { xRange: [n0, n1], yRange: [r0, r1], xLabel: "평균 밀도 [10¹⁶ m⁻³]", yLabel: "밀도비 ρ", right: 12 });
  ctx.save(); ctx.beginPath(); ctx.rect(box.left, box.top, box.right - box.left, box.bottom - box.top); ctx.clip();
  if (band) {                                        // 도달 가능 영역 (위 경계는 왼→오, 아래 경계는 오→왼)
    ctx.beginPath();
    band.upper.forEach(([n, rho], i) => (i ? ctx.lineTo(sx(n * 1e-16), sy(rho)) : ctx.moveTo(sx(n * 1e-16), sy(rho))));
    [...band.lower].reverse().forEach(([n, rho]) => ctx.lineTo(sx(n * 1e-16), sy(rho)));
    ctx.closePath(); ctx.fillStyle = "rgba(106,75,214,0.13)"; ctx.fill();
  }
  ctx.setLineDash([4, 4]); ctx.strokeStyle = COLORS.muted; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(box.left, sy(1)); ctx.lineTo(box.right, sy(1)); ctx.stroke(); ctx.setLineDash([]);
  if (trajectory && trajectory.length > 1) {         // 맞춰 간 걸음
    ctx.beginPath();
    trajectory.forEach((p, i) => (i ? ctx.lineTo(sx(p.n_bar * 1e-16), sy(p.rho)) : ctx.moveTo(sx(p.n_bar * 1e-16), sy(p.rho))));
    ctx.strokeStyle = COLORS.ink; ctx.lineWidth = 1.3; ctx.stroke();
    for (const p of trajectory) { ctx.beginPath(); ctx.arc(sx(p.n_bar * 1e-16), sy(p.rho), 2.3, 0, 7); ctx.fillStyle = COLORS.ink; ctx.fill(); }
  }
  if (current) {                                     // 현재 상태
    ctx.beginPath(); ctx.arc(sx(current.n_bar * 1e-16), sy(current.rho), 6, 0, 7);
    ctx.fillStyle = COLORS.ink; ctx.fill(); ctx.strokeStyle = "#fff"; ctx.lineWidth = 2; ctx.stroke();
  }
  const tx = sx(target.n), ty = sy(target.rho);     // 목표 표적
  ctx.strokeStyle = COLORS.argon; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(box.left, ty); ctx.lineTo(box.right, ty); ctx.moveTo(tx, box.top); ctx.lineTo(tx, box.bottom); ctx.stroke();
  ctx.beginPath(); ctx.arc(tx, ty, 9, 0, 7); ctx.lineWidth = 2.5; ctx.stroke();
  ctx.beginPath(); ctx.arc(tx, ty, 2.5, 0, 7); ctx.fillStyle = COLORS.argon; ctx.fill();
  ctx.restore();
  ctx.fillStyle = COLORS.muted; ctx.textAlign = "right"; ctx.textBaseline = "bottom";
  ctx.fillText("ρ = 1", box.right - 2, sy(1) - 2);
  if (band) { ctx.fillStyle = COLORS.argon; ctx.textAlign = "right"; ctx.textBaseline = "top"; ctx.fillText("옅은 보라: 도달 가능", box.right - 2, box.top + 2); }
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  return { toValue: (px, py) => ({ n: clamp(sx.invert(px), n0, n1), rho: clamp(sy.invert(py), r0, r1) }) };
}
