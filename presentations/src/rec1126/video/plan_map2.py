import json, sys, numpy as np
sp=json.load(open('full_vad.json')); best=np.load('best.npy')
CUT=(419.9,506.0); T=855.9; HOLD=2.0; TARGET=1080.0
SPEECH_F=float(sys.argv[1]); SHORT=0.5; SHORT_F=1.3; CAP=6.0; TRANS_MIN=3.0
changes=[t for t in range(1,len(best)) if best[t]!=best[t-1]]
def keep(a,b):
    if b<=CUT[0] or a>=CUT[1]: return [(a,b)]
    out=[]
    if a<CUT[0]: out.append((a,CUT[0]))
    if b>CUT[1]: out.append((CUT[1],b))
    return out
speech=[]
for a,b in sp: speech+=keep(a,b)
segs=[]; t=0.0
for a,b in speech:
    if a>t:
        for x,y in keep(t,a):
            if y-x>1e-6: segs.append([x,y,'gap'])
    segs.append([a,b,'speech']); t=b
if t<T: segs.append([t,T,'gap'])
def is_trans(a,b): return any(a-1.0<=c<=b+1.0 for c in changes)
def gout(a,b,g):
    d=b-a
    if is_trans(a,b): return min(max(d*g, TRANS_MIN), max(d,CAP))
    if d<SHORT: return d*SHORT_F
    return min(d*g, max(d,CAP))
def total(g): return sum((b-a)*SPEECH_F if k=='speech' else gout(a,b,g) for a,b,k in segs)
lo,hi=1.0,8.0
for _ in range(60):
    g=(lo+hi)/2
    if total(g)<TARGET-HOLD: lo=g
    else: hi=g
g=(lo+hi)/2
for s in segs: s.append((s[1]-s[0])*SPEECH_F if s[2]=='speech' else gout(s[0],s[1],g))
json.dump({'segs':segs,'g':g,'speech_f':SPEECH_F,'cut':CUT,'hold':HOLD},open('map.json','w'))
gs=[s for s in segs if s[2]=='gap']
sh=[(s[1]-s[0],s[3]) for s in gs if s[1]-s[0]<SHORT and not is_trans(s[0],s[1])]
lg=[(s[1]-s[0],s[3]) for s in gs if s[1]-s[0]>=SHORT and not is_trans(s[0],s[1])]
tr=[(s[1]-s[0],s[3]) for s in gs if is_trans(s[0],s[1])]
med=lambda L,i: round(float(np.median([x[i] for x in L])),2)
print(f"speech x{SPEECH_F} ({1/SPEECH_F:.2f}배속)  g={g:.2f}  total={sum(s[3] for s in segs)+HOLD:.1f}")
print(f" short gaps n={len(sh)} med {med(sh,0)}->{med(sh,1)} | sentence gaps n={len(lg)} med {med(lg,0)}->{med(lg,1)} max {max(x[1] for x in lg):.1f} | transitions n={len(tr)} med {med(tr,0)}->{med(tr,1)}")
