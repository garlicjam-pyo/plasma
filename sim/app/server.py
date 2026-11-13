"""독립 제어 GUI 의 백엔드 서버. 파이썬 표준 라이브러리만 쓴다(추가 설치 없음).

    python sim/app/server.py            # http://127.0.0.1:8765 에서 실행하고 브라우저를 연다
    python sim/app/server.py --port 9000 --no-browser

역할 분담
  server.py   : HTTP 요청을 받아 정적 파일(web/)을 주거나 /api/* 를 service 로 넘긴다
  service.py  : 모델을 불러 계산하고 결과를 JSON 용 dict 로 만든다
  web/        : 프론트엔드 (index.html, style.css, js/)

API (모두 JSON)
  GET  /api/meta        조절 범위, 기본값, 챔버 형상
  POST /api/simulate    {P_tot, k, phi_deg, p_mtorr, coil_mode, transport} → 계산 결과
  POST /api/control     위 항목 + {n_target, rho_target} → 찾은 입력, 걸음별 궤적, 계산 결과
  POST /api/reachable   {phi_deg, p_mtorr, transport} → (n̄_w, ρ) 평면의 도달 가능 영역
  POST /api/jacobian    운전점 → 제어 민감도 행렬 J_ctrl
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # sim/ 을 경로에 넣어 hybrid 패키지를 찾는다

from app.service import ModelService  # noqa: E402

WEB_ROOT = (Path(__file__).resolve().parent / "web").resolve()
SERVICE = ModelService()
POST_ROUTES = {"/api/simulate": SERVICE.simulate, "/api/control": SERVICE.control,
               "/api/reachable": SERVICE.reachable, "/api/jacobian": SERVICE.jacobian}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802 (표준 라이브러리가 정한 이름)
        path = self.path.split("?")[0]
        if path == "/api/meta":
            return self._json(200, SERVICE.meta())
        # 정적 파일: web/ 폴더 밖으로 나가는 경로는 막는다
        target = (WEB_ROOT / ("index.html" if path == "/" else path.lstrip("/"))).resolve()
        if WEB_ROOT not in target.parents and target != WEB_ROOT or not target.is_file():
            return self._json(404, {"error": "파일을 찾을 수 없습니다."})
        ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype.endswith("javascript"):
            ctype += "; charset=utf-8"
        self._send(200, target.read_bytes(), ctype)

    def do_POST(self) -> None:  # noqa: N802
        route = POST_ROUTES.get(self.path.split("?")[0])
        if route is None:
            return self._json(404, {"error": "알 수 없는 요청입니다."})
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length) or b"{}")
            self._json(200, route(req))
        except (KeyError, ValueError, TypeError) as exc:           # 입력값 문제
            self._json(400, {"error": f"입력값을 확인하세요: {exc}"})
        except Exception as exc:  # noqa: BLE001  계산 중 오류는 화면에 알리고 서버는 계속 돈다
            traceback.print_exc()
            self._json(500, {"error": f"계산 중 오류가 났습니다: {exc}"})

    def log_message(self, fmt: str, *args) -> None:
        if "/api/" in (args[0] if args else ""):                    # 계산 요청만 터미널에 남긴다
            super().log_message(fmt, *args)


def main() -> None:
    ap = argparse.ArgumentParser(description="독립 제어 GUI 서버")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true", help="브라우저를 자동으로 열지 않는다")
    a = ap.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)     # 이 컴퓨터에서만 접속 가능
    url = f"http://127.0.0.1:{a.port}"
    print(f"독립 제어 GUI: {url}  (끝내려면 Ctrl+C)")
    if not a.no_browser:
        threading.Timer(0.6, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 끝냅니다.")


if __name__ == "__main__":
    main()
