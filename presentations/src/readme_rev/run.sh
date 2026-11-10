#!/usr/bin/env bash
# 팀 수정본(README 슬라이드와 쪽별 메모가 달린 판)에서 표지 부제와 슬라이드 3–8을 다시 만든다.
# 사용: bash run.sh <팀 수정본.pptx> <출력.pptx> <pptx 스킬의 scripts 폴더>
#   필요: matplotlib, Pillow, schemdraw (등가회로 그림)
#   - 옛 슬라이드 3(sldId 325)은 목록에서 빼고, 옛 4에 합친다. 9쪽 이후는 그대로 둔다.
#   - clean.py가 목록에서 빠진 슬라이드·노트·미디어를 정리한다.
set -e
SRC=$(realpath "$1"); OUT=$(realpath -m "$2"); S=$(realpath "$3")
D=$(cd "$(dirname "$0")" && pwd)
W=$(mktemp -d); cd "$W"
python3 -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall('un')" "$SRC"
mkdir eq2 fig && (cd eq2 && python3 "$D/render_eqs.py" >/dev/null) && (cd fig && python3 "$D/circuits.py" >/dev/null)
python3 "$D/build.py"
python3 - <<'PY'
p = 'un/ppt/presentation.xml'
s = open(p, encoding='utf-8').read()
s = s.replace('<p:sldId id="325" r:id="rId4"/>', '')
open(p, 'w', encoding='utf-8').write(s)
PY
sed -i 's#<cp:lastModifiedBy>[^<]*</cp:lastModifiedBy>#<cp:lastModifiedBy>주제 3 팀</cp:lastModifiedBy>#' un/docProps/core.xml
python3 "$S/clean.py" un >/dev/null
rm -f "$OUT"; (cd un && zip -q -XrD "$OUT" .)
python3 "$S/office/validate.py" "$OUT" --original "$SRC" | tail -1
