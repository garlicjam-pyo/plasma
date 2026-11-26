import json, numpy as np
sp=json.load(open('full_vad.json'))
CUT=(419.9,506.0); T=855.9; SPEECH_F=1.25; CAP=5.0; HOLD=2.0; TARGET=1080.0
def keep(a,b):
    if b<=CUT[0] or a>=CUT[1]: return [(a,b)]
    out=[]
    if a<CUT[0]: out.append((a,CUT[0]))
    if b>CUT[1]: out.append((CUT[1],b))
    return out
speech=[]
for a,b in sp: speech+=keep(a,b)
# build alternating segments over [0,T] minus CUT
segs=[]; t=0.0
for a,b in speech:
    if a>t:
        # gap [t,a] may straddle the cut
        for x,y in keep(t,a):
            if y-x>1e-6: segs.append([x,y,'gap'])
    segs.append([a,b,'speech']); t=b
if t<T: segs.append([t,T,'gap'])
# merge adjacent gaps (around cut) into one logical gap for capping
def total(g):
    tot=0
    for a,b,k in segs:
        d=b-a
        tot+= d*SPEECH_F if k=='speech' else min(d*g, max(d,CAP))
    return tot
lo,hi=1.0,6.0
for _ in range(60):
    g=(lo+hi)/2
    if total(g)<TARGET-HOLD: lo=g
    else: hi=g
g=(lo+hi)/2
for s in segs:
    d=s[1]-s[0]; s.append(d*SPEECH_F if s[2]=='speech' else min(d*g, max(d,CAP)))
json.dump({'segs':segs,'g':g,'speech_f':SPEECH_F,'cut':CUT,'hold':HOLD},open('map.json','w'))
gaps=[s for s in segs if s[2]=='gap']
gin=np.array([s[1]-s[0] for s in gaps]); gout=np.array([s[3] for s in gaps])
print('segments',len(segs),'gap factor',round(g,3),'content out',round(sum(s[3] for s in segs),1),'+hold',HOLD)
print('gaps in: median %.2f max %.2f | out: median %.2f max %.2f'%(np.median(gin),gin.max(),np.median(gout),gout.max()))
print('speech in %.1f -> out %.1f'%(sum(s[1]-s[0] for s in segs if s[2]=='speech'), sum(s[3] for s in segs if s[2]=='speech')))
