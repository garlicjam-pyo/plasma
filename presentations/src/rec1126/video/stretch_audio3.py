"""v3 오디오: 말 구간은 Rubber Band ×F, 쉼은 원음 그대로 두고 map3의 m(조용한 가운데)에 무음 삽입.
영상도 같은 m 주변의 조용한 구간만 늘리므로, 들리는 소리는 항상 영상과 같은 속도로 재생된다."""
import json, time, numpy as np, soundfile as sf
from pylibrb import RubberBandStretcher, Option
M=json.load(open('map3.json')); F=M['speech_f']
x,sr=sf.read('audio48.wav',dtype='float32')
opts=Option.PROCESS_OFFLINE | Option.ENGINE_FINER | Option.FORMANT_PRESERVED | Option.CHANNELS_TOGETHER
CTX=0.10; FADE=int(0.003*sr)
def rb(sig, ratio):
    st=RubberBandStretcher(sample_rate=sr, channels=2, options=opts, initial_time_ratio=ratio)
    a=np.ascontiguousarray(sig.T); st.set_expected_input_duration(a.shape[1])
    st.study(a, final=True); st.process(a, final=True)
    out=[]
    while st.available()>0: out.append(st.retrieve_available())
    return np.concatenate(out,axis=1).T
def fit(y,n):
    y=y[:n]
    return np.pad(y,((0,n-len(y)),(0,0))) if len(y)<n else y
win=(0.5-0.5*np.cos(np.linspace(0,np.pi,FADE)))[:,None].astype(np.float32)
pieces=[]; cum=0.0; t0=time.time()
for p in M['aplan']:
    k,a,b,o=p[:4]
    n_out=int(round((cum+o)*sr))-int(round(cum*sr)); cum+=o
    ia,ib=int(round(a*sr)),int(round(b*sr))
    if k=='speech':
        ca,cb=max(0,ia-int(CTX*sr)), min(len(x), ib+int(CTX*sr))
        y=rb(x[ca:cb],F); lead=int(round((ia-ca)*F)); y=fit(y[lead:],n_out)
    else:
        g=x[ia:ib].copy(); add=n_out-len(g); im=int(round(p[4]*sr))-ia
        im=min(max(im,0),len(g))
        L,R=g[:im].copy(),g[im:].copy()
        f=min(240,len(L),len(R))
        if f>0:
            L[-f:]*=np.linspace(1,0,f)[:,None]; R[:f]*=np.linspace(0,1,f)[:,None]
        y=fit(np.concatenate([L,np.zeros((max(add,0),2),np.float32),R]),n_out)
    y=y.astype(np.float32).copy()
    if len(y)>2*FADE: y[:FADE]*=win; y[-FADE:]*=win[::-1]
    pieces.append(y)
z=np.concatenate(pieces+[np.zeros((int(M['hold']*sr),2),np.float32)])
sf.write('stretched3.wav',z,sr,subtype='FLOAT')
print('out',round(len(z)/sr,3),'s  expected',round(cum+M['hold'],3),' rb',round(time.time()-t0,1),'s')
