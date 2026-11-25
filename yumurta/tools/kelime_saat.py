# kelime_saat.py — word timings for a voice file, aligned back onto the exact script words.
#   python kelime_saat.py <voice.wav> <script.txt> <out.json> [language=turkish]
# Whisper hears the words (and may misspell them); we keep the SCRIPT's spelling and take only the times.
import sys, json, re, difflib
import torch, librosa
from transformers import pipeline

wav, script, out = sys.argv[1], sys.argv[2], sys.argv[3]
lang = sys.argv[4] if len(sys.argv) > 4 else 'turkish'
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
p = pipeline('automatic-speech-recognition', model='openai/whisper-large-v3-turbo', device=dev,
             torch_dtype=torch.float16 if dev == 'cuda' else torch.float32)
y, _ = librosa.load(wav, sr=16000)
r = p({'raw': y, 'sampling_rate': 16000}, return_timestamps='word', chunk_length_s=30,
      generate_kwargs={'language': lang})
heard = [{'w': c['text'].strip(), 's': c['timestamp'][0], 'e': c['timestamp'][1]} for c in r['chunks'] if c['text'].strip()]

def norm(w): return re.sub(r"[^\wçğıöşüâîû]", '', w.lower().replace('İ', 'i').replace('I', 'ı'))
words = open(script, encoding='utf-8').read().split()
A, B = [norm(w) for w in words], [norm(h['w']) for h in heard]
sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
times = [None] * len(words)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal':
        for k in range(i2 - i1): times[i1 + k] = (heard[j1 + k]['s'], heard[j1 + k]['e'])
    elif j2 > j1:   # replaced span: spread the heard span over the script words
        s, e = heard[j1]['s'], heard[j2 - 1]['e'] or heard[j2 - 1]['s']
        n = i2 - i1
        for k in range(n): times[i1 + k] = (s + (e - s) * k / n, s + (e - s) * (k + 1) / n)
# fill gaps (words whisper skipped) by interpolation
for i, t in enumerate(times):
    if t is None:
        prev = next((times[j][1] for j in range(i - 1, -1, -1) if times[j]), 0.0)
        nxt = next((times[j][0] for j in range(i + 1, len(times)) if times[j]), prev + .3)
        times[i] = (prev, nxt)
res = [{'word': w, 'start': round(float(s), 3), 'end': round(float(e if e is not None else s + .25), 3)}
       for w, (s, e) in zip(words, times)]
json.dump({'words': res, 'duration': round(len(y) / 16000, 3)}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
gaps = [(res[i]['word'], round(res[i + 1]['start'] - res[i]['end'], 2)) for i in range(len(res) - 1) if res[i + 1]['start'] - res[i]['end'] > .35]
same = sum(i2 - i1 for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag == 'equal')
print('heard exactly:', same, '/', len(words), [(' '.join(A[i1:i2]), ' '.join(B[j1:j2])) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != 'equal'])
print('OK', len(res), 'words', res[-1]['end'], 's | gaps>0.35:', gaps)
