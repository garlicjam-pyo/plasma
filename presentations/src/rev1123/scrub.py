"""공개 저장소용: 표지의 학번·이름 줄을 지운다. 사용: python scrub.py <입력.pptx> <출력.pptx>"""
import re
import sys
from pptx import Presentation

src, out = sys.argv[1:3]
prs = Presentation(src)
removed = 0
for sh in prs.slides[0].shapes:
    if not sh.has_text_frame:
        continue
    for p in list(sh.text_frame.paragraphs):
        if re.search(r"\d{10}", p.text):
            p._p.getparent().remove(p._p)
            removed += 1
prs.core_properties.author = "주제 3 팀"
prs.core_properties.last_modified_by = "주제 3 팀"
prs.save(out)
print("removed", removed)
