// 캔버스 그리기의 공통 도구: 고해상도 준비, 눈금 계산, 색 지도.

export const COLORS = {
  ink: "#1b1f2e", muted: "#5f6880", grid: "#e4e7ee", argon: "#6a4bd6",
  coilIn: "#2a78d6", coilOut: "#e8632b",
};

// 캔버스를 화면 배율에 맞춰 준비하고 (그리기 맥락, 너비, 높이)를 돌려준다.
// HTML 의 width/height 속성은 가로세로 비율로만 쓴다.
export function prepare(canvas) {
  if (!canvas.dataset.aspect) canvas.dataset.aspect = canvas.height / canvas.width;
  const width = Math.max(200, canvas.clientWidth);
  const height = Math.round(width * Number(canvas.dataset.aspect));
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, width, height);
  ctx.font = "12px Pretendard, 'Noto Sans KR', 'Malgun Gothic', sans-serif";
  return { ctx, width, height };
}

// [min, max] 구간을 보기 좋은 간격(1, 2, 5 × 10ⁿ)의 눈금으로 나눈다.
export function ticks(min, max, count = 5) {
  const raw = (max - min) / count;
  const power = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * power).find((s) => s >= raw);
  const out = [];
  for (let v = Math.ceil(min / step) * step; v <= max + step * 1e-9; v += step) out.push(Number(v.toPrecision(12)));
  return out;
}

// 값 구간과 화면 구간을 잇는 1차 변환.
export function scale(domainMin, domainMax, pixelMin, pixelMax) {
  const fn = (v) => pixelMin + ((v - domainMin) / (domainMax - domainMin)) * (pixelMax - pixelMin);
  fn.invert = (p) => domainMin + ((p - pixelMin) / (pixelMax - pixelMin)) * (domainMax - domainMin);
  return fn;
}

// 색 지도: 낮은 값 → 높은 값. 밀도는 플라즈마 빛깔, 전력은 불꽃, 전기장은 청록, 온도는 자홍 계열.
const STOPS = {
  ne: ["#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636", "#f0f921"],
  p_abs: ["#000004", "#420a68", "#932667", "#dd513a", "#fca50a", "#fcffa4"],
  E_abs: ["#440154", "#414487", "#2a788e", "#22a884", "#7ad151", "#fde725"],
  Te: ["#000004", "#3b0f70", "#8c2981", "#de4968", "#fe9f6d", "#fcfdbf"],
};

function hexToRgb(hex) {
  return [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
}

// 0–1 사이 값 t 를 [r, g, b] 로 바꾸는 함수를 돌려준다.
export function colormap(name) {
  const stops = STOPS[name].map(hexToRgb);
  return (t) => {
    const x = Math.min(1, Math.max(0, t)) * (stops.length - 1);
    const i = Math.min(stops.length - 2, Math.floor(x));
    const f = x - i;
    return stops[i].map((c, j) => Math.round(c + (stops[i + 1][j] - c) * f));
  };
}

// 숫자를 유효숫자 기준으로 짧게 적는다.
export function fmt(value, digits = 3) {
  if (!Number.isFinite(value)) return "–";
  return Number(value.toPrecision(digits)).toString();
}
