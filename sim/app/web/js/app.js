// 화면 동작 전체: 상태를 한곳(state)에 두고, 조작 → 백엔드 요청 → 다시 그리기 순서로 움직인다.
import { api } from "./api.js";
import { drawChamber } from "./chamber.js";
import { drawHeating, drawPad, drawProfile } from "./charts.js";
import { fmt } from "./draw.js";

const $ = (id) => document.getElementById(id);

const state = {
  meta: null,                     // 조절 범위, 기본값, 챔버 형상
  mode: "control",                // "control"(목표로 맞추기) | "manual"(직접 조정)
  inputs: {},                     // 현재 입력: P_tot, k, phi_deg, p_mtorr, coil_mode, transport
  target: { n: 5, rho: 1 },       // 목표: 평균 밀도 [10¹⁶ m⁻³], 밀도비
  result: null, previous: null,   // 가장 최근 결과와 그 직전 결과
  map: "ne",                      // 챔버 단면에 표시할 양
  band: null, trajectory: null,   // 도달 가능 영역, 목표로 맞춰 간 걸음
  pad: null, request: 0,          // 목표 판의 좌표 변환, 요청 번호(늦게 온 응답을 버리는 데 사용)
};

// ------------------------------------------------------------------ 상태 표시
function setStatus(text, kind = "") {
  $("status").textContent = text;
  $("status").className = `status ${kind}`;
}

// ------------------------------------------------------------------ 그리기
function render() {
  const { result, meta } = state;
  if (!result) return;
  const g = meta.geom, m = result.metrics;
  drawChamber($("chamber"), result, g, state.map);
  drawProfile($("profile"), result, state.previous, g);
  drawHeating($("heat"), result, g);
  state.pad = drawPad($("pad"), { limits: meta.limits, target: state.target, current: m, band: state.band, trajectory: state.trajectory });
  $("r-n").textContent = (m.n_bar * 1e-16).toFixed(2);
  $("r-rho").textContent = m.rho.toFixed(3);
  $("r-nc").textContent = `${(m.n_c * 1e-16).toFixed(2)} ×10¹⁶`;
  $("r-ne").textContent = `${(m.n_edge * 1e-16).toFixed(2)} ×10¹⁶`;
  $("r-pabs").textContent = `${result.heating.P_abs.toFixed(0)} W (${(100 * result.heating.efficiency).toFixed(0)} %)`;
  $("r-I").textContent = `${fmt(result.heating.I_in, 3)} / ${fmt(result.heating.I_out, 3)} A`;
  $("r-te").textContent = `${result.Te_range[0].toFixed(2)} – ${result.Te_range[1].toFixed(2)} V`;
  const showTarget = state.mode === "control";
  const diff = (now, goal) => `목표 ${goal} (차 ${(100 * (now / goal - 1)).toFixed(1)} %)`;
  $("r-n-target").textContent = showTarget ? diff(m.n_bar * 1e-16, state.target.n.toFixed(2)) : "";
  $("r-rho-target").textContent = showTarget ? diff(m.rho, state.target.rho.toFixed(3)) : "";
}

// 입력 상태를 조작 요소에 반영한다 (목표로 맞춘 뒤 슬라이더가 따라 움직이게).
function syncControls() {
  const i = state.inputs;
  $("m-P").value = i.P_tot; $("m-P-out").textContent = `${Math.round(i.P_tot)} W`;
  $("m-k").value = i.k; $("m-k-out").textContent = Number(i.k).toFixed(2);
  $("m-phi").value = i.phi_deg; $("m-phi-out").textContent = `${Math.round(i.phi_deg)}°`;
  $("c-p").value = i.p_mtorr; $("c-p-out").textContent = `${i.p_mtorr} mTorr`;
  $("c-mode").value = i.coil_mode; $("c-transport").value = i.transport;
  $("t-n").value = state.target.n.toFixed(2); $("t-rho").value = state.target.rho.toFixed(3);
  for (const chip of document.querySelectorAll('input[name="c-phi"]')) chip.checked = Number(chip.value) === Math.round(i.phi_deg);
  $("c-phi-now").textContent = `지금 ${Math.round(i.phi_deg)}°`;
  const single = i.coil_mode !== "dual";              // 단일 코일에서는 k, φ 가 고정이라 조절할 수 없다
  $("m-k").disabled = single; $("m-phi").disabled = single;
}

// ------------------------------------------------------------------ 계산 요청
function accept(result, adoptInputs = false) {
  state.previous = state.result;
  state.result = result;
  // 목표로 맞춘 경우에만 찾은 입력을 받아들인다. 직접 조정 중에는 슬라이더 값이 기준이다.
  if (adoptInputs) Object.assign(state.inputs, result.inputs);
}

async function simulate() {
  const id = ++state.request;
  setStatus("계산하는 중…", "busy");
  try {
    const result = await api.simulate(state.inputs);
    if (id !== state.request) return;                  // 그사이 새 요청이 나갔으면 이 응답은 버린다
    accept(result);
    setStatus(`계산 완료: ${(result.seconds * 1000).toFixed(0)} ms, 반복 ${result.outer_iters}회${result.converged ? "" : " (수렴하지 못함)"}`,
      result.converged ? "" : "error");
    render();
  } catch (err) { setStatus(err.message, "error"); }
}

let timer = null;
function simulateSoon() {                              // 슬라이더를 끄는 동안 요청이 몰리지 않게 조금 모았다가 보낸다
  clearTimeout(timer);
  timer = setTimeout(simulate, 90);
}

async function solveTargets() {
  const id = ++state.request;
  $("btn-solve").disabled = true;
  setStatus("목표를 만드는 입력을 찾는 중…", "busy");
  try {
    const out = await api.control({ ...state.inputs, n_target: state.target.n * 1e16, rho_target: state.target.rho });
    if (id !== state.request) return;
    accept(out.result, true);
    state.trajectory = out.trajectory;
    const card = $("solve-result");
    card.hidden = false; card.classList.toggle("failed", !out.success);
    $("solve-message").textContent = out.message;
    $("f-P").textContent = `${out.result.inputs.P_tot.toFixed(1)} W`;
    $("f-k").textContent = out.result.inputs.k.toFixed(3);
    $("f-Iin").textContent = `${fmt(out.result.heating.I_in, 3)} A`;
    $("f-Iout").textContent = `${fmt(out.result.heating.I_out, 3)} A`;
    $("solve-meta").textContent = `위상차 ${Math.round(out.result.inputs.phi_deg)}° 고정, 걸음 ${out.trajectory.length - 1}번, ${out.seconds.toFixed(2)} s`;
    setStatus(out.success ? `목표 도달: ${out.seconds.toFixed(2)} s` : "목표에 도달하지 못함", out.success ? "" : "error");
    syncControls(); render();
  } catch (err) { setStatus(err.message, "error"); } finally { $("btn-solve").disabled = false; }
}

async function loadBand() {                            // 도달 가능 영역은 몇 초 걸리므로 따로 불러 와 나중에 덧그린다
  state.band = null;
  if (state.inputs.coil_mode !== "dual") { render(); return; }
  const key = `${state.inputs.p_mtorr}|${state.inputs.phi_deg}|${state.inputs.transport}`;
  state.bandKey = key;
  try {
    const band = await api.reachable(state.inputs);
    if (state.bandKey === key) { state.band = band; render(); }
  } catch (err) { /* 영역 표시는 보조 정보라 실패해도 조용히 넘어간다 */ }
}

async function showJacobian() {
  $("btn-jac").disabled = true;
  setStatus("제어 민감도를 계산하는 중…", "busy");
  try {
    const jac = await api.jacobian(state.inputs);
    $("jac-result").hidden = false;
    for (let r = 0; r < 2; r++) for (let c = 0; c < 3; c++) {
      const v = jac.J_norm[r][c];
      $(`j${r}${c}`).textContent = v === undefined ? "–" : `${v >= 0 ? "+" : ""}${(c < 2 ? v : v * 100).toFixed(2)} %`;
    }
    const gain = jac.shape_gain.k;
    $("jac-meta").textContent = jac.rank === 2
      ? `두 출력을 따로 움직일 수 있습니다 (계수 2, 조건수 ${jac.condition.toFixed(1)}). 평균을 유지할 때 전류비 1 % 변화가 밀도비를 ${gain.toFixed(2)} % 바꿉니다.`
      : "입력이 전력 하나라 평균 밀도와 밀도비가 함께 움직입니다 (계수 1).";
    setStatus(`제어 민감도 계산 완료: ${jac.seconds.toFixed(2)} s`);
  } catch (err) { setStatus(err.message, "error"); } finally { $("btn-jac").disabled = false; }
}

// ------------------------------------------------------------------ 조작 연결
function setMode(mode) {
  state.mode = mode;
  for (const name of ["control", "manual"]) {
    $(`tab-${name}`).setAttribute("aria-selected", String(name === mode));
    $(`panel-${name}`).hidden = name !== mode;
  }
  render();
}

function setTarget(n, rho) {
  const lim = state.meta.limits;
  const clamp = (v, [a, b]) => Math.min(b, Math.max(a, v));
  state.target = { n: clamp(n, lim.n_target_1e16), rho: clamp(rho, lim.rho_target) };
  $("t-n").value = state.target.n.toFixed(2); $("t-rho").value = state.target.rho.toFixed(3);
  render();
}

function bind() {
  $("tab-control").addEventListener("click", () => setMode("control"));
  $("tab-manual").addEventListener("click", () => setMode("manual"));
  // 직접 조정 슬라이더: 움직이는 즉시 값 표시를 바꾸고 곧 계산한다
  for (const [id, key] of [["m-P", "P_tot"], ["m-k", "k"], ["m-phi", "phi_deg"]]) {
    $(id).addEventListener("input", (e) => {
      state.inputs[key] = Number(e.target.value);
      state.trajectory = null;
      syncControls(); simulateSoon();
      if (key === "phi_deg") loadBandSoon();
    });
  }
  // 공통 조건: 바뀌면 다시 계산하고 도달 가능 영역도 새로 받는다
  $("c-p").addEventListener("input", (e) => { state.inputs.p_mtorr = Number(e.target.value); state.trajectory = null; syncControls(); simulateSoon(); loadBandSoon(); });
  for (const [id, key] of [["c-mode", "coil_mode"], ["c-transport", "transport"]]) {
    $(id).addEventListener("change", (e) => { state.inputs[key] = e.target.value; state.trajectory = null; syncControls(); simulate(); loadBand(); });
  }
  for (const chip of document.querySelectorAll('input[name="c-phi"]')) {
    chip.addEventListener("change", (e) => { state.inputs.phi_deg = Number(e.target.value); state.trajectory = null; syncControls(); simulate(); loadBand(); });
  }
  // 목표 입력 칸과 버튼
  $("t-n").addEventListener("change", (e) => setTarget(Number(e.target.value), state.target.rho));
  $("t-rho").addEventListener("change", (e) => setTarget(state.target.n, Number(e.target.value)));
  $("btn-solve").addEventListener("click", solveTargets);
  $("btn-jac").addEventListener("click", showJacobian);
  // 목표 판: 누르고 끄는 동안 표적이 따라오고, 손을 떼면 바로 맞춘다
  const pad = $("pad");
  const move = (e) => {
    const rect = pad.getBoundingClientRect();
    const v = state.pad.toValue(e.clientX - rect.left, e.clientY - rect.top);
    setTarget(v.n, v.rho);
  };
  pad.addEventListener("pointerdown", (e) => { pad.setPointerCapture(e.pointerId); pad.dataset.drag = "1"; move(e); });
  pad.addEventListener("pointermove", (e) => { if (pad.dataset.drag) move(e); });
  pad.addEventListener("pointerup", () => { if (pad.dataset.drag) { delete pad.dataset.drag; solveTargets(); } });
  // 챔버 단면에 표시할 양
  for (const button of document.querySelectorAll(".seg button")) {
    button.addEventListener("click", () => {
      state.map = button.dataset.map;
      for (const other of document.querySelectorAll(".seg button")) other.setAttribute("aria-pressed", String(other === button));
      render();
    });
  }
  window.addEventListener("resize", render);
}

let bandTimer = null;
function loadBandSoon() { clearTimeout(bandTimer); bandTimer = setTimeout(loadBand, 600); }

// ------------------------------------------------------------------ 시작
async function start() {
  try {
    state.meta = await api.meta();
  } catch (err) { setStatus(err.message, "error"); return; }
  const lim = state.meta.limits;
  for (const [id, key] of [["m-P", "P_tot"], ["m-k", "k"], ["m-phi", "phi_deg"], ["c-p", "p_mtorr"]]) {
    $(id).min = lim[key][0]; $(id).max = lim[key][1];
  }
  $("c-mode").innerHTML = Object.entries(state.meta.coil_modes).map(([v, t]) => `<option value="${v}">${t}</option>`).join("");
  state.inputs = { ...state.meta.defaults };
  bind();
  syncControls();
  await simulate();
  if (state.result) setTarget(Math.round(state.result.metrics.n_bar * 1e-15) / 10, 1.0);   // 처음 목표: 지금 평균 밀도에서 ρ = 1
  loadBand();
}

start();
