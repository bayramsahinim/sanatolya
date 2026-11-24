"""Give each word of script.txt a time from the Whisper words (faster-whisper output of episodes/troy_en/words.py).
Whisper spells numbers and names its own way ("50", "Alan", "Thirty -six"); the script's spelling is kept and the times
are carried over by a sequence alignment. Unmatched script words get times interpolated from their neighbours.
usage (repo root): python3 yumurta/stories/alcatraz-en/align.py
"""
import difflib, json, os, re, subprocess, sys

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voice')
wav = os.path.join(D, 'voice.wav')
if not os.path.exists(wav + '.words.json') or os.path.getmtime(wav + '.words.json') < os.path.getmtime(wav):
    subprocess.run([sys.executable, 'episodes/troy_en/words.py', wav], check=True, capture_output=True)
ww = json.load(open(wav + '.words.json'))
script = open(os.path.join(D, 'script.txt')).read().split()
norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
a, b = [norm(x) for x in script], [norm(x[2]) for x in ww]
out = [None] * len(script)
for tag, i0, i1, j0, j1 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
    if tag == 'equal':
        for k in range(i1 - i0): out[i0 + k] = ww[j0 + k][:2]
    elif j1 > j0:                                  # replaced span: spread the whisper span over the script words
        s, e = ww[j0][0], ww[j1 - 1][1]
        n = i1 - i0
        for k in range(n): out[i0 + k] = [s + (e - s) * k / n, s + (e - s) * (k + 1) / n]
for i in range(len(out)):                          # deleted (no whisper words): squeeze in after the previous word
    if out[i] is None:
        p = out[i - 1][1] if i else 0
        nx = next((o[0] for o in out[i + 1:] if o), p + .2)
        out[i] = [p, min(nx, p + .15)]
words = [{'word': w, 'start': round(s, 3), 'end': round(e, 3)} for w, (s, e) in zip(script, out)]
json.dump({'words': words}, open(os.path.join(D, 'words.json'), 'w'))
print(len(words), 'words, last ends', words[-1]['end'])
