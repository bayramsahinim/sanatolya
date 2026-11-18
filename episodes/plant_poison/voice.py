"""Split the narration take into per-line clips and estimate word timings.

Line boundaries: approximate times from a Gemini listen-through (BOUNDS, seconds into the take),
each snapped to the quietest stretch within +-0.6 s. Word timings: phrases (split at
punctuation) are matched to voiced chunks, words spread by syllable weight inside each chunk.
"""
import re

import numpy as np

from cinecode import align, tts
from episodes.plant_poison.script import LINES

# Revision 2 narration: take "c" (crisper, more forward, medium-fast; chosen over "a"/"b" by a
# blind listening comparison against the delivery reference). Boundaries were read off the
# take's pause map (line content x expected duration); each is snapped to the quietest
# 0.12 s inside its +-window.
TAKE = "assets/audio/tts/plant_poison_c_b8625b7d3f.wav"
BOUNDS = [(2.40, 0.3), (4.80, 0.4), (7.90, 0.2), (12.40, 0.4), (14.30, 0.3), (18.80, 0.7),
          (21.50, 0.2), (25.30, 0.25), (28.20, 0.5), (30.60, 0.06), (33.50, 0.4), (35.30, 0.15),
          (37.20, 0.6), (40.25, 0.2), (42.90, 0.3), (45.00, 0.5), (47.80, 0.3)]
# Revision 1 (take "a"): Gemini-estimated boundaries, +-0.6 s snap
# TAKE = "assets/audio/tts/plant_poison_a_3910928469.wav"
SR = tts.SR
HOP = 240


def env(a):
    n = len(a) // HOP
    r = np.sqrt((a[: n * HOP].reshape(n, HOP) ** 2).mean(1) + 1e-12)
    return np.convolve(20 * np.log10(r), np.ones(3) / 3, mode="same")


def snap(db, t, win=0.6, width=0.12):
    w = int(width * 100)
    i0, i1 = int((t - win) * 100), max(int((t + win) * 100), int((t - win) * 100) + 1)
    k = np.convolve(db, np.ones(w) / w, mode="same")
    j = i0 + int(np.argmin(k[i0:i1]))
    return j / 100


def clips():
    a = tts.read_wav(TAKE)
    db = env(a)
    thr = np.percentile(db, 95) - 35
    cuts = [0.0] + [snap(db, b, w) for b, w in BOUNDS] + [len(a) / SR]
    out = []
    for i in range(len(LINES)):
        s, e = cuts[i], cuts[i + 1]
        seg = db[int(s * 100): int(e * 100)]
        v = np.where(seg > thr)[0]
        on = s + v[0] / 100 - 0.03
        off = s + (v[-1] + 1) / 100 + 0.06
        on, off = max(on, s), min(off, e)
        x = a[int(on * SR): int(off * SR)].copy()
        x = tighten(x, keep=0.5 if i == len(LINES) - 1 else 0.28)
        n = int(0.008 * SR)
        x[:n] *= np.linspace(0, 1, n)
        x[-n:] *= np.linspace(1, 0, n)
        out.append(x)
    return out


def tighten(x, keep=0.28, longer=0.32):
    """Shorten internal silences longer than `longer` s to `keep` s (crossfaded), so the read
    keeps a medium-fast pace without touching the words themselves."""
    db = env(x)
    thr = np.percentile(db, 95) - 32
    quiet = db < thr
    runs, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if i > 0 and j < len(quiet) and (j - i) / 100 > longer:
                runs.append((i, j))
            i = j
        else:
            i += 1
    out, pos = [], 0
    fade = int(0.01 * SR)
    for i, j in runs:
        mid = (i + j) / 2 / 100
        cut0, cut1 = int((mid - keep / 2) * SR), int((mid + keep / 2) * SR)
        drop0, drop1 = int(i / 100 * SR) + int(keep / 2 * SR), int(j / 100 * SR) - int(keep / 2 * SR)
        seg = x[pos:drop0].copy()
        if out:
            seg[:fade] *= np.linspace(0, 1, fade)
        seg[-fade:] *= np.linspace(1, 0, fade)
        out.append(seg)
        pos = drop1
    tail = x[pos:].copy()
    if out:
        tail[:fade] *= np.linspace(0, 1, fade)
    out.append(tail)
    return np.concatenate(out)


def syl(w):
    w = re.sub(r"[^a-z']", "", w.lower())
    v = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and v > 1 and not w.endswith("le"):
        v -= 1
    return max(1, v)


def words_timing(x, text):
    """Return [(word, t0, t1)] relative to clip start."""
    words = text.split()
    # phrases: break after , . : ; ? ! or ellipsis
    phrases, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[,.:;?!”]$", w) and not w.startswith("..."):
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    db = env(x)
    thr = np.percentile(db, 95) - 30
    voiced = db > thr
    # voiced chunks separated by pauses >= 0.11 s
    chunks, i, n = [], 0, len(voiced)
    while i < n:
        if voiced[i]:
            j = i
            while j < n and (voiced[j] or (j + 11 < n and voiced[j:j + 11].any())):
                j += 1
            chunks.append((i / 100, j / 100))
            i = j
        else:
            i += 1
    if not chunks:
        chunks = [(0, len(x) / SR)]
    t0, t1 = chunks[0][0], chunks[-1][1]
    tot = sum(sum(syl(w) for w in p) for p in phrases)
    gaps = [(chunks[k][1], chunks[k + 1][0]) for k in range(len(chunks) - 1)]
    bounds, acc, last = [], 0, t0
    for p in phrases[:-1]:
        acc += sum(syl(w) for w in p)
        exp_t = t0 + (t1 - t0) * acc / tot
        cand = [g for g in gaps if g[0] > last + 0.15]
        if cand:
            g = min(cand, key=lambda g: abs((g[0] + g[1]) / 2 - exp_t) - 1.5 * (g[1] - g[0]))
            if abs((g[0] + g[1]) / 2 - exp_t) < 0.8:
                bounds.append(g)
                last = g[1]
                continue
        bounds.append((exp_t, exp_t))
        last = exp_t
    edges = [t0] + [x for g in bounds for x in g] + [t1]
    spans = [(edges[2 * k], edges[2 * k + 1]) for k in range(len(phrases))]
    out = []
    for p, (s, e) in zip(phrases, spans):
        ws = [syl(w) + 0.3 for w in p]
        tot = sum(ws)
        acc = s
        for w, k in zip(p, ws):
            d = (e - s) * k / tot
            out.append((w, acc, acc + d))
            acc += d
    return out


if __name__ == "__main__":
    for x, l in zip(clips(), LINES):
        print(f"{len(x)/SR:5.2f} slot {l[3]-l[2]:5.2f}  {l[0]}")
        print("     ", " ".join(f"{w}@{a:.2f}" for w, a, b in words_timing(x, l[0])))
