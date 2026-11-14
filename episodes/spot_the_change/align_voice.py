"""Cut each block take into sentence clips and estimate word timings inside each sentence.

Sentences: cinecode.align.align (pause DP).  Words: syllable-proportional positions snapped to
the nearest local energy minimum (±140 ms), monotonic.  Caption groups take the onset of their
first word and the end of their last word.

usage: python -m episodes.spot_the_change.align_voice   -> assets/audio/tts/spot_the_change/lines.json
"""
import json
import os
import re

import numpy as np

from cinecode import tts
from cinecode.align import HOP, SR, align, envelope_db
from episodes.spot_the_change.script import BLOCKS, groups, plain

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "assets", "audio", "tts", "spot_the_change")


def syl(w):
    w = w.lower().strip(".,?!'")
    if re.fullmatch(r"\d+", w):
        return 2
    v = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and v > 1 and not w.endswith("le"):
        v -= 1
    return max(1, v)


def speech_bounds(db, s, e, thr):
    a, b = int(s * SR / HOP), int(e * SR / HOP)
    seg = db[a:b]
    on = np.where(seg >= thr)[0]
    if len(on) == 0:
        return s, e
    return (a + on[0]) * HOP / SR, (a + on[-1] + 1) * HOP / SR


def word_times(db, s, e, words):
    """Return [(w, t0, t1)] spanning [s, e]."""
    w8 = np.array([syl(w) + (0.6 if re.search(r"[,.?!]$", w) else 0) for w in words], float)
    cum = np.concatenate([[0], np.cumsum(w8)]) / w8.sum()
    bounds = [s]
    for k in range(1, len(words)):
        tx = s + cum[k] * (e - s)
        lo = max(bounds[-1] + 0.08, tx - 0.14)
        hi = min(e - 0.08 * (len(words) - k), tx + 0.14)
        if hi <= lo:
            bounds.append(max(lo, min(tx, hi)))
            continue
        i0, i1 = int(lo * SR / HOP), int(hi * SR / HOP) + 1
        win = db[i0:i1]
        # prefer the minimum, lightly biased toward the proportional estimate
        bias = np.abs(np.arange(i0, i1) * HOP / SR - tx) * 25
        j = int(np.argmin(win + bias))
        bounds.append((i0 + j) * HOP / SR)
    bounds.append(e)
    return [(w, bounds[i], bounds[i + 1]) for i, w in enumerate(words)]


def main():
    takes = json.load(open(os.path.join(D, "takes.json")))
    out = {}
    for name, lines in BLOCKS:
        audio = tts.read_wav(os.path.join(ROOT, takes[name]))
        texts = [plain(l) for _, l in lines]
        db = envelope_db(audio)
        thr = np.percentile(db, 95) - 38
        v = np.where(db >= thr)[0]
        whole = (v[0] * HOP / SR, (v[-1] + 1) * HOP / SR)
        try:
            segs = align(audio, texts) if len(texts) > 1 else [whole]
        except RuntimeError:
            # no clean pause (e.g. a breath bridges the sentences): time the block word by word
            allw = " ".join(texts).split()
            wt = word_times(db, whole[0], whole[1], allw)
            segs, k = [], 0
            for t in texts:
                n = len(t.split())
                segs.append((wt[k][1], wt[k + n - 1][2]))
                k += n
        for (lid, line), (s, e) in zip(lines, segs):
            s, e = speech_bounds(db, s, e, thr)
            words = plain(line).split()
            wt = word_times(db, s, e, words)
            gs, k = [], 0
            for g in groups(line):
                n = len(g.split())
                gs.append({"text": g, "t0": round(wt[k][1] - s, 3), "t1": round(wt[k + n - 1][2] - s, 3)})
                k += n
            out[lid] = {"block": name, "take": takes[name], "start": round(s, 3), "end": round(e, 3),
                        "text": plain(line), "groups": gs,
                        "words": [(w, round(a - s, 3), round(b - s, 3)) for w, a, b in wt]}
            print(f"{lid:3s} {s:6.2f}-{e:6.2f} ({e - s:4.2f}s) {plain(line)}")
    json.dump(out, open(os.path.join(D, "lines.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
