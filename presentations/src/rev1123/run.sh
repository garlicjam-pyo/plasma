#!/usr/bin/env bash
# 1차 발표 피드백 반영판 (2026-11-23) 재생성.
# 사용: bash presentations/src/rev1123/run.sh <팀 1차 발표 원본.pptx>
#   원본은 표지(학번·이름) 때문에 저장소에 넣지 않는다. 표지 양식과 마스터만 쓰고 나머지 쪽은 새로 만든다.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
SRC="$1"
OUT="${2:-$ROOT/presentations/1차발표_피드백반영판.pptx}"
TMP="$(mktemp -d)"
# 1) 근거 그림 (모델 계산, 약 5초)
python3 "$HERE/calc/figs.py" "$HERE/fig" > /dev/null
# 2) 수식 이미지 (KaTeX + Playwright; NODE_PATH에 katex, playwright 필요). 이미 있으면 생략 가능
if [ "${RENDER_EQ:-0}" = "1" ]; then (cd "$HERE/eq" && python3 mk.py && node render.js); fi
# 3) 슬라이드 (이름이 있는 판) → 4) 공개용 표지 정리
python3 "$HERE/build.py" "$SRC" "$TMP/full.pptx" "$HERE/eq" "$HERE/fig" "$ROOT/presentations/src"
python3 "$HERE/scrub.py" "$TMP/full.pptx" "$OUT"
echo "saved $OUT (이름이 있는 판: $TMP/full.pptx)"
