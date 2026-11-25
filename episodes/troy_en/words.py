import sys,json
from faster_whisper import WhisperModel
m=WhisperModel(sys.argv[2] if len(sys.argv)>2 else "small.en",device="cpu",compute_type="int8")
import librosa
aud,_=librosa.load(sys.argv[1],sr=16000)
segs,_=m.transcribe(aud,word_timestamps=True,beam_size=5,initial_prompt="Laocoön, Sinon, Athena, Cassandra, Helen, Odysseus, Troy, Trojans.")
W=[]
for s in segs:
    for w in s.words: W.append((round(w.start,3),round(w.end,3),w.word.strip()))
json.dump(W,open(sys.argv[1]+'.words.json','w'))
print(" ".join(w for *_,w in W)); print(len(W),"words, last end",W[-1][1])
