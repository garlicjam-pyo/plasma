"""백엔드의 계산 창구. 화면(프론트엔드)의 요청을 모델 호출로 바꾸고, 결과를 JSON 으로 보낼 수 있는 dict 로 만든다.

server.py 는 HTTP 만 다루고, 계산과 직렬화는 모두 여기서 한다.
요청 하나를 처리하는 동안에는 잠금을 걸어 계산이 한 번에 하나씩만 돌게 한다.
가까운 운전점의 해를 기억해 두었다가 다음 계산의 출발점으로 써서 응답을 빠르게 한다.
"""
from __future__ import annotations

import threading

import numpy as np

from hybrid import inverse
from hybrid.config import Config
from hybrid.control import control_jacobian
from hybrid.coupled import Solution, solve_point

# 화면의 조절 범위 (프론트엔드가 /api/meta 로 받아 간다)
LIMITS = dict(P_tot=[30, 1000], k=[0, 5], phi_deg=[-180, 180], p_mtorr=[3, 50],
              n_target_1e16=[1, 15], rho_target=[0.4, 3.2])
COIL_MODES = {"dual": "이중 코일 (안쪽·바깥쪽 따로 구동)", "single_series": "단일 코일 (모든 턴 직렬)",
              "single_inner": "단일 코일 (안쪽만)"}


def _round(a, digits: int = 4):
    """배열을 유효숫자 몇 자리로 줄여 목록으로 바꾼다 (전송량을 줄이기 위함)."""
    a = np.asarray(a, dtype=float)
    scale = np.where(a == 0, 1.0, 10.0 ** (digits - 1 - np.floor(np.log10(np.abs(np.where(a == 0, 1.0, a))))))
    return (np.round(a * scale) / scale).tolist()


class ModelService:
    def __init__(self):
        self._lock = threading.Lock()
        self._warm: dict = {}          # (압력, 코일 구성, 수송 모델) → 마지막 해
        self._bands: dict = {}         # (압력, 위상, 수송 모델) → 도달 가능 영역

    # ------------------------------------------------------------------ 요청 → 설정
    def _config(self, req: dict) -> Config:
        d = Config().op
        cfg = Config().with_op(
            P_tot=float(req.get("P_tot", d.P_tot)), k=float(req.get("k", d.k)),
            phi=float(np.radians(req.get("phi_deg", 0.0))), p_mtorr=float(req.get("p_mtorr", d.p_mtorr)),
            coil_mode=req.get("coil_mode", "dual") if req.get("coil_mode") in COIL_MODES else "dual")
        return cfg.with_num(transport="full_2d" if req.get("transport") == "2d" else "radial_1d")

    def _key(self, cfg: Config) -> tuple:
        return (cfg.op.p_mtorr, cfg.op.coil_mode, cfg.num.transport)

    def _solve(self, cfg: Config) -> Solution:
        """기억해 둔 해에서 출발해 풀고, 수렴에 실패하면 0D 초기값에서 다시 푼다."""
        warm = self._warm.get(self._key(cfg))
        sol = solve_point(cfg, guess=warm.state if warm else None)
        if not sol.converged and warm is not None:
            sol = solve_point(cfg)
        if sol.converged:
            self._warm[self._key(cfg)] = sol
        return sol

    # ------------------------------------------------------------------ 결과 → dict
    def _pack(self, sol: Solution) -> dict:
        cfg, g, st, heat, m = sol.cfg, sol.grid, sol.state, sol.heating, sol.metrics
        k, phi = cfg.op.effective_k_phi()
        zp = g.z[: g.Nzp]
        Te_map = st.Te_rz(zp)
        return dict(
            inputs=dict(P_tot=cfg.op.P_tot, k=k, phi_deg=float(np.degrees(phi)), p_mtorr=cfg.op.p_mtorr,
                        coil_mode=cfg.op.coil_mode, transport="2d" if cfg.num.transport == "full_2d" else "1d"),
            metrics=dict(n_bar=m.n_bar, rho=m.rho, n_c=m.n_c, n_edge=m.n_edge),
            heating=dict(I_in=heat.I0, I_out=heat.I0 * k, P_abs=heat.P_abs, P_coil=heat.P_coil,
                         efficiency=heat.P_abs / cfg.op.P_tot),
            Te_range=[float(Te_map.min()), float(Te_map.max())],
            converged=bool(sol.converged), seconds=sol.timing["total"], outer_iters=sol.timing["outer_iters"],
            balance=dict(particle=float(abs(sol.balance["particle_error"])), energy=float(abs(sol.balance["energy_error"]))),
            r_cm=_round(g.r * 100), n_wafer=_round(st.wafer_profile(cfg)), n_mid=_round(st.midplane(cfg)),
            Te_r=_round(st.Te_radial()), S=_round(heat.S),
            maps=dict(z_cm=_round(g.z * 100), z_plasma_cm=_round(zp * 100), E_abs=_round(np.abs(heat.E)),
                      p_abs=_round(heat.p_abs), ne=_round(st.ne_rz(zp, cfg)), Te=_round(Te_map)),
            history=[dict(iter=h["iter"], residual=h["coupled_residual"]) for h in sol.history])

    # ------------------------------------------------------------------ API
    def meta(self) -> dict:
        cfg = Config()
        g, op = cfg.geom, cfg.op
        return dict(limits=LIMITS, coil_modes=COIL_MODES,
                    defaults=dict(P_tot=op.P_tot, k=op.k, phi_deg=0.0, p_mtorr=op.p_mtorr, coil_mode="dual", transport="1d"),
                    geom=dict(R=g.R * 100, L=g.L * 100, window=g.window * 100, z_coil=g.z_coil * 100, z_top=g.z_top * 100,
                              r_in=[r * 100 for r in g.r_in], r_out=[r * 100 for r in g.r_out],
                              r_c=g.r_c * 100, r_1=g.r_1 * 100, r_2=g.r_2 * 100, R_w=g.R_w * 100, z_w=g.z_w * 100))

    def simulate(self, req: dict) -> dict:
        """직접 조정: 입력 (P_tot, k, φ) 그대로 한 번 계산한다."""
        with self._lock:
            return self._pack(self._solve(self._config(req)))

    def control(self, req: dict) -> dict:
        """목표로 맞추기: 목표 (n̄_w, ρ) 를 만드는 (P_tot, k) 를 찾는다. 출발점은 요청에 담긴 현재 입력."""
        with self._lock:
            cfg = self._config(req)
            res = inverse.solve_targets(cfg, float(req["n_target"]), float(req["rho_target"]),
                                        start=self._warm.get(self._key(cfg)))
            if res.solution.converged:
                self._warm[self._key(cfg)] = res.solution
            return dict(success=res.success, message=res.message, trajectory=res.trajectory,
                        n_solves=res.n_solves, seconds=res.seconds, result=self._pack(res.solution))

    def reachable(self, req: dict) -> dict:
        """(n̄_w, ρ) 평면의 도달 가능 영역. 압력·위상·수송 모델이 같으면 저장해 둔 것을 돌려준다."""
        with self._lock:
            cfg = self._config(req).with_op(coil_mode="dual")
            key = (cfg.op.p_mtorr, round(float(req.get("phi_deg", 0.0)), 3), cfg.num.transport)
            if key not in self._bands:
                self._bands[key] = inverse.reachable_band(cfg)
            return self._bands[key]

    def jacobian(self, req: dict) -> dict:
        """현재 운전점의 제어 민감도 행렬 J_ctrl."""
        with self._lock:
            jc = control_jacobian(self._config(req))
            return dict(inputs=list(jc.inputs), J_norm=jc.J_norm.tolist(), rank=jc.rank,
                        condition=jc.condition if np.isfinite(jc.condition) else None,
                        shape_gain=jc.shape_gain, seconds=jc.seconds)
