"""v3 지도: 쉼은 '조용한 가운데 부분'만 늘린다(소리·영상 같은 지점). 말 구간은 ×SPEECH_F."""
import json, sys, numpy as np, soundfile as sf
sp=json.load(open('full_vad.json')); best=np.load('best.npy')
x,sr=sf.read('audio48.wav',dtype='float32'); xm=x.mean(1)
CUT=(419.9,506.0); T=855.9; HOLD=2.0; TARGET=1080.0
SPEECH_F=float(sys.argv[1]) if len(sys.argv)>1 else 1.15
SHORT=0.5; SHORT_F=1.3; CAP=6.0; TRANS_MIN=3.0; QDB=-50.0; MARG=0.03; W=0.10
changes=[t for t in range(1,len(best)) if best[t]!=best[t-1]]
def keep(a,b):
    if b<=CUT[0] or a>=CUT[1]: return [(a,b)]
    out=[]
    if a<CUT[0]: out.append((a,CUT[0]))
    if b>CUT[1]: out.append((CUT[1],b))
    return out
speech=[]
for a,b in sp: speech+=keep(a,b)
raw=[]; t=0.0
for a,b in speech:
    if a>t:
        for u,v in keep(t,a):
            if v-u>1e-6: raw.append([u,v,'gap'])
    raw.append([a,b,'speech']); t=b
if t<T: raw.append([t,T,'gap'])
def core(a,b):
    """가장 긴 조용한 구간 (10 ms RMS < QDB), 양끝 MARG 여유."""
    h=int(0.01*sr); i0,i1=int(a*sr),int(b*sr); n=(i1-i0)//h
    if n<3: return None
    r=20*np.log10(np.sqrt((xm[i0:i0+n*h].reshape(n,h)**2).mean(1))+1e-9)
    q=r<QDB; bestrun=(0,0); s=None
    for i,v in enumerate(list(q)+[False]):
        if v and s is None: s=i
        if not v and s is not None:
            if i-s>bestrun[1]-bestrun[0]: bestrun=(s,i)
            s=None
    ca=a+bestrun[0]*0.01+MARG; cb=a+bestrun[1]*0.01-MARG
    return (ca,cb) if cb-ca>=0.06 else None
def is_trans(a,b): return any(a-1.0<=c<=b+1.0 for c in changes)
def gout(a,b,g):
    d=b-a
    if is_trans(a,b): return min(max(d*g, TRANS_MIN), max(d,CAP))
    if d<SHORT: return d*SHORT_F
    return min(d*g, max(d,CAP))
def total(g): return sum((b-a)*SPEECH_F if k=='speech' else gout(a,b,g) for a,b,k in raw)
lo,hi=1.0,8.0
for _ in range(60):
    g=(lo+hi)/2
    if total(g)<TARGET-HOLD: lo=g
    else: hi=g
g=(lo+hi)/2
vsegs=[]; aplan=[]; nocore=0
for a,b,k in raw:
    if k=='speech':
        o=(b-a)*SPEECH_F; vsegs.append([a,b,o]); aplan.append(['speech',a,b,o]); continue
    o=gout(a,b,g); add=o-(b-a); c=core(a,b)
    if c is None: c=(a,b); nocore+=1
    ca,cb=c; m=(ca+cb)/2; w=min(W,(cb-ca)/2)
    if m-w>a: vsegs.append([a,m-w,m-w-a])
    vsegs.append([m-w,m+w,2*w+add])
    if b>m+w: vsegs.append([m+w,b,b-m-w])
    aplan.append(['gap',a,b,o,m])
json.dump({'vsegs':vsegs,'aplan':aplan,'g':g,'speech_f':SPEECH_F,'cut':CUT,'hold':HOLD},open('map3.json','w'))
print(f"speech x{SPEECH_F}  g={g:.2f}  total={sum(v[2] for v in vsegs)+HOLD:.2f}s  gaps={sum(1 for p in aplan if p[0]=='gap')}  no-quiet-core gaps={nocore}")
