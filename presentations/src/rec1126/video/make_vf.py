"""map3.json → ffmpeg filter_complex 스크립트(vf3.txt). 영상 시간 사상은 오디오와 같은 지도를 쓴다."""
import json
M=json.load(open('map3.json')); C=M['cut']
expr="+".join(f"{o/(b-a):.6f}*clip(T-{a:.4f},0,{b-a:.4f})" for a,b,o in M['vsegs'] if b-a>1e-6)
open('vf3.txt','w').write(f"[0:v]select='not(between(t,{C[0]},{C[1]}))',setpts='({expr})/TB',fps=30,"
                          f"tpad=stop_mode=clone:stop_duration={M['hold']}[v]")
