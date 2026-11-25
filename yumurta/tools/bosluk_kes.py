# bosluk_kes.py — shorten the pauses in a voice take, then (optionally) speed it up.
#   python bosluk_kes.py <in.wav> <words.json> <out.wav> [tempo=1.0]
# words.json = kelime_saat.py output for <in.wav>; it tells which pause follows a sentence end, a comma or nothing.
# Pause targets (before tempo): sentence end .22 s, comma .14 s, inside a phrase .09 s. Lead-in .03 s.
import sys, json, subprocess
import numpy as np

src, wj, dst = sys.argv[1], sys.argv[2], sys.argv[3]
tempo = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
SR = 24000
y = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                                 capture_output=True, check=True).stdout, np.float32).copy()
words = json.load(open(wj, encoding='utf-8'))['words']

# 10 ms frames, silence = 40 dB under the loud speech level
hop = SR // 100
fr = np.sqrt(np.mean(y[:len(y) // hop * hop].reshape(-1, hop) ** 2, 1) + 1e-12)
db = 20 * np.log10(fr)
quiet = db < np.percentile(db, 95) - 40
runs, i = [], 0
while i < len(quiet):
    if quiet[i]:
        j = i
        while j < len(quiet) and quiet[j]: j += 1
        runs.append((i * hop, j * hop)); i = j
    else: i += 1

def kind(t):          # punctuation of the last word that started before this pause
    w = [x for x in words if x['start'] < t]
    if not w: return 'lead'
    p = w[-1]['word'].rstrip('"\'')
    return 'end' if p[-1:] in '.:?!' else 'comma' if p[-1:] in ',;' else 'mid'

TARGET = {'lead': .03, 'end': .22, 'comma': .14, 'mid': .09}
keep, cur, log = [], 0, []
for a, b in runs:
    dur = (b - a) / SR
    k = 'lead' if a == 0 else 'tail' if b >= len(y) - hop else kind((a + b) / 2 / SR)
    tgt = .30 if k == 'tail' else TARGET[k]
    if dur <= tgt + .02: continue
    h = int(tgt * SR / 2)
    cut_a, cut_b = (a, b - int(tgt * SR)) if k == 'lead' else (a + h, b - h) if k != 'tail' else (a + int(tgt * SR), b)
    keep.append((cur, cut_a)); cur = cut_b
    log.append((round(a / SR, 2), round(dur, 2), k, round(tgt, 2)))
keep.append((cur, len(y)))

# join with 8 ms crossfades (all joins sit inside silence, so this only guards against clicks)
xf = int(.008 * SR); out = y[keep[0][0]:keep[0][1]].copy()
for a, b in keep[1:]:
    seg = y[a:b].copy()
    if len(out) > xf and len(seg) > xf:
        r = np.linspace(0, 1, xf, dtype=np.float32)
        out[-xf:] = out[-xf:] * (1 - r) + seg[:xf] * r; seg = seg[xf:]
    out = np.concatenate([out, seg])

for l in log: print('pause at %6.2fs  %.2fs (%s) -> %.2fs' % l)
print('length %.2fs -> %.2fs' % (len(y) / SR, len(out) / SR))
af = ['-af', f'atempo={tempo}'] if tempo != 1.0 else []
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', *af,
                '-c:a', 'pcm_s16le', dst], input=out.astype(np.float32).tobytes(), check=True)
print('tempo x%.2f -> %.2fs' % (tempo, len(out) / SR / tempo))
