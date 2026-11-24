"""Word times for a voice take, aligned back onto the script's own spelling (faster-whisper on CPU).
usage: python3 -m episodes.ships_en.words <voice.wav> <script.txt> <out.json>
"""
import difflib
import json
import re
import sys

import librosa
from faster_whisper import WhisperModel

wav, script, out = sys.argv[1:4]
m = WhisperModel("small.en", device="cpu", compute_type="int8")
aud, _ = librosa.load(wav, sr=16000)
segs, _ = m.transcribe(aud, word_timestamps=True, beam_size=5,
                       initial_prompt="Golden Horn, chain, warships, greased logs.")
heard = [(w.start, w.end, w.word.strip()) for s in segs for w in s.words]
NUM = {"62": "sixtytwo", "79": "seventynine", "1599": "fifteenninetynine"}
norm = lambda w: NUM.get(re.sub(r"[^\w]", "", w.lower()), re.sub(r"[^\w]", "", w.lower()))
words = open(script).read().split()
A, B = [norm(w) for w in words], [norm(h[2]) for h in heard]
sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
T = [None] * len(words)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        for k in range(i2 - i1): T[i1 + k] = heard[j1 + k][:2]
    elif j2 > j1:
        s, e, n = heard[j1][0], heard[j2 - 1][1], i2 - i1
        for k in range(n): T[i1 + k] = (s + (e - s) * k / n, s + (e - s) * (k + 1) / n)
for i in range(len(T)):                                   # words whisper skipped: squeeze between neighbours
    if T[i] is None:
        a = T[i - 1][1] if i and T[i - 1] else 0
        j = i
        while j < len(T) and T[j] is None: j += 1
        b = T[j][0] if j < len(T) else a + .3 * (j - i)
        for k in range(i, j): T[k] = (a + (b - a) * (k - i) / (j - i), a + (b - a) * (k - i + 1) / (j - i))
json.dump({"words": [{"word": w, "start": round(s, 3), "end": round(e, 3)} for w, (s, e) in zip(words, T)]}, open(out, "w"), indent=0)
print(" ".join(h[2] for h in heard)); print(len(words), "script words,", len(heard), "heard, last end", T[-1][1])
miss = [(o, A[i1:i2], B[j1:j2]) for o, i1, i2, j1, j2 in sm.get_opcodes() if o != "equal"]
print("mismatches:", miss)
