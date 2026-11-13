"""감쇠 Newton 풀이 (1D·2D 수송 모델 공용).

미지수 벡터는 x = [ln(n/n_ref) (앞 절반), T_e (뒤 절반)] 로 약속한다.
야코비안은 촘촘한 배열(1D)이나 희소 행렬(2D) 어느 쪽이든 받는다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve


@dataclass
class NewtonResult:
    x: np.ndarray
    iterations: int
    residual_history: list = field(default_factory=list)   # 반복별 max|F|
    converged: bool = False


def damped_newton(residual: Callable, jacobian: Callable, x0: np.ndarray, tol: float, max_iter: int) -> NewtonResult:
    """F(x) = 0 을 푼다.

    - 한 번에 너무 멀리 가지 않게 보폭을 제한한다: ln n 은 1, T_e 는 30 %.
    - 잔차가 줄지 않으면 보폭을 반씩 줄인다(최대 10번).
    """
    x = x0.copy()
    half = x.size // 2
    F = residual(x)
    hist = [float(np.max(np.abs(F)))]
    for it in range(1, max_iter + 1):
        if hist[-1] < tol:
            return NewtonResult(x, it - 1, hist, True)
        J = jacobian(x, F)
        dx = spsolve(J.tocsc(), -F) if sp.issparse(J) else np.linalg.solve(J, -F)
        limit = np.concatenate([np.full(half, 1.0), 0.3 * x[half:]])
        dx *= min(1.0, 1.0 / np.max(np.abs(dx) / limit))
        lam = 1.0
        for _ in range(10):
            x_new = x + lam * dx
            F_new = residual(x_new)
            if np.all(np.isfinite(F_new)) and np.max(np.abs(F_new)) < hist[-1]:
                break
            lam *= 0.5
        x, F = x_new, F_new
        hist.append(float(np.max(np.abs(F))))
    return NewtonResult(x, max_iter, hist, hist[-1] < tol)
