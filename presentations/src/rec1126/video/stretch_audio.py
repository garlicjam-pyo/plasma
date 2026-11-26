import json, time, numpy as np, soundfile as sf
from pylibrb import RubberBandStretcher, Option
M=json.load(open('map.json')); segs=M['segs']; F=M['speech_f']
x,sr=sf.read('audio48.wav',dtype='float32')     # (n,2), original timeline
opts=Option.PROCESS_OFFLINE | Option.ENGINE_FINER | Option.FORMANT_PRESERVED | Option.CHANNELS_TOGETHER
CTX=0.10
def rb(sig, ratio):
    st=RubberBandStretcher(sample_rate=sr, channels=2, options=opts, initial_time_ratio=ratio)
    a=np.ascontiguousarray(sig.T); st.set_expected_input_duration(a.shape[1])
    st.study(a, final=True); st.process(a, final=True)
    out=[]
    while st.available()>0: out.append(st.retrieve_available())
    return np.concatenate(out,axis=1).T
pieces=[]; t0=time.time(); drift=[]
for a,b,k,o in segs:
    ia,ib=int(round(a*sr)),int(round(b*sr)); n_out=int(round(o*sr))
    if k=='speech':
        ca,cb=max(0,ia-int(CTX*sr)), min(len(x), ib+int(CTX*sr))
        y=rb(x[ca:cb], F)
        lead=int(round((ia-ca)*F)); y=y[lead:lead+n_out]
        if len(y)<n_out: y=np.pad(y,((0,n_out-len(y)),(0,0)))
        drift.append(abs(len(y)-n_out))
    else:
        g=x[ia:ib]; add=n_out-len(g)
        if add<=0: y=g[:n_out]
        else:
            e=np.convolve((g**2).mean(1), np.ones(480)/480, 'same') if len(g)>960 else np.ones(len(g))
            m=int(np.argmin(e)) if len(g)>960 else len(g)//2
            f=min(240, m, len(g)-m)
            left=g[:m].copy(); right=g[m:].copy()
            if f>0:
                left[-f:]*=np.linspace(1,0,f)[:,None]; right[:f]*=np.linspace(0,1,f)[:,None]
            y=np.concatenate([left,np.zeros((add,2),np.float32),right])
    pieces.append(y.astype(np.float32))
z=np.concatenate(pieces)
# 이음매마다 3 ms 페이드 (딸깍 소리 방지)
n=int(0.003*sr); fo=0.5*(1+np.cos(np.linspace(0,np.pi,n)))[:,None]; fi=fo[::-1]; t=0
for a_,b_,k_,o_ in segs:
    i=int(round(t*sr))
    if n<i<len(z)-n: z[i-n:i]*=fo; z[i:i+n]*=fi
    t+=o_
# 10 ms crossfade-free joins are in silence; add END hold
hold=np.zeros((int(M['hold']*sr),2),np.float32); z=np.concatenate([z,hold])
sf.write('stretched.wav', z, sr, subtype='FLOAT')
print('out',round(len(z)/sr,2),'s  expected',round(sum(s[3] for s in segs)+M['hold'],2),' rb time',round(time.time()-t0,1))
