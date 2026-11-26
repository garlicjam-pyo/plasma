import sys, time, json
import numpy as np, soundfile as sf, sherpa_onnx
wav, out, tmax = sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv)>3 else 1e9
m='models/sherpa-onnx-whisper-turbo/'
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=m+'turbo-encoder.int8.onnx', decoder=m+'turbo-decoder.int8.onnx',
    tokens=m+'turbo-tokens.txt', language='ko', task='transcribe', num_threads=2, tail_paddings=-1)
x,sr=sf.read(wav,dtype='float32'); x=x[:int(tmax*sr)]
cfg=sherpa_onnx.VadModelConfig(); cfg.silero_vad.model='silero_vad.onnx'; cfg.silero_vad.min_silence_duration=0.35
cfg.silero_vad.min_speech_duration=0.25; cfg.silero_vad.max_speech_duration=20; cfg.sample_rate=sr
vad=sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=900)
segs=[]; ws=cfg.silero_vad.window_size; i=0
while i < len(x):
    vad.accept_waveform(x[i:i+ws]); i+=ws
    while not vad.empty():
        s=vad.front; segs.append((s.start/sr, np.array(s.samples))); vad.pop()
vad.flush()
while not vad.empty():
    s=vad.front; segs.append((s.start/sr, np.array(s.samples))); vad.pop()
speech=[(st, st+len(smp)/sr) for st,smp in segs]
open(out.replace('.json','_vad.json'),'w').write(json.dumps(speech))
groups=[]
for a,b in speech:
    if groups and b-groups[-1][0] <= 25 and a-groups[-1][1] < 1.5: groups[-1][1]=b
    else: groups.append([a,b])
res=[]; t0=time.time()
for a,b in groups:
    smp=x[int(max(0,a-0.1)*sr):int((b+0.1)*sr)]
    s=rec.create_stream(); s.set_option('max_tokens_per_second','25'); s.accept_waveform(sr, smp); rec.decode_stream(s)
    r={'start':round(a,2),'end':round(b,2),'text':s.result.text.strip()}
    res.append(r); print(f"[{r['start']:7.2f}-{r['end']:7.2f}] {r['text']}", flush=True)
json.dump(res, open(out,'w'), ensure_ascii=False, indent=0)
print('segments',len(res),'asr time',round(time.time()-t0,1), file=sys.stderr)
