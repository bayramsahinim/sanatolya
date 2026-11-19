"""Split the narration take into lines and time every word -> assets/audio/tts/dry_peas/lines.json

Lines: pause-based dynamic-programming alignment (cinecode.align.align) - the take has a clear
paragraph pause between every line. Words: inside each line, words are laid along the *voiced*
time (pauses excluded), weighted by length, with punctuation pauses snapped to real silences.

usage: python -m episodes.dry_peas_escape.align_voice
"""
import json
import os
import re

import numpy as np

from cinecode import align, tts
from episodes.dry_peas_escape.make_voice import OUT, ROOT, take_path
from episodes.dry_peas_escape.script import LINES

LINES_JSON = os.path.join(OUT, "lines.json")


def _spread(words, vt, s, hop, i0, i1):
    """lay words along voiced time between frame i0 and i1 (proportional to length)."""
    w = np.array([len(re.sub(r"[^A-Za-z0-9']", "", x)) + 1.6 for x in words], float)
    v0, v1 = (vt[i0 - 1] if i0 > 0 else 0.0), vt[min(i1, len(vt)) - 1]
    cum = v0 + np.concatenate([[0], np.cumsum(w)]) / w.sum() * (v1 - v0)
    seg = vt[i0:i1]

    def at(v, right):
        i = i0 + int(np.searchsorted(seg, v, side="right" if right else "left"))
        return s + min(i, len(vt) - 1) * hop

    out = []
    for k, x in enumerate(words):
        t0 = at(cum[k] + 1e-4, False)
        t1 = at(cum[k + 1] - 1e-4, False)
        out.append([x, t0, max(t1, t0 + 0.08)])
    return out


def word_times(audio, s, e, text):
    """Words laid along voiced time; silences inside the line are snapped to punctuation."""
    words = text.split()
    seg = audio[int(s * align.SR):int(e * align.SR)]
    db = align.envelope_db(seg)
    voiced = db >= (np.percentile(db, 95) - 34)
    hop = align.HOP / align.SR
    vt = np.cumsum(voiced) * hop
    # internal pauses (frame index ranges)
    pauses, i = [], 0
    while i < len(voiced):
        if not voiced[i]:
            j = i
            while j < len(voiced) and not voiced[j]:
                j += 1
            if i > 5 and j < len(voiced) - 5 and (j - i) * hop >= 0.10:
                pauses.append((i, j))
            i = j
        else:
            i += 1
    first = _spread(words, vt, s, hop, 0, len(vt))
    cands = [k for k, x in enumerate(words[:-1]) if x[-1] in ",.?!:\""]
    anchors = []  # (word index k ends at pause start, frames)
    for (a, b) in pauses:
        mid = s + (a + b) / 2 * hop
        best = min(cands, key=lambda k: abs(first[k][2] - mid), default=None)
        if best is not None and abs(first[best][2] - mid) < 0.9 and best not in [x[0] for x in anchors]:
            anchors.append((best, a, b))
    anchors.sort()
    out, k0, f0 = [], 0, 0
    for k, a, b in anchors:
        out += _spread(words[k0:k + 1], vt, s, hop, f0, a)
        k0, f0 = k + 1, b
    out += _spread(words[k0:], vt, s, hop, f0, len(vt))
    return [[x, round(t0, 3), round(t1, 3)] for x, t0, t1 in out]


def main():
    p = take_path()
    audio = tts.read_wav(p)
    texts = [en for _, _, en, _ in LINES]
    segs = [list(s) for s in align.align(audio, texts)]
    # lines the narrator reads as one breath ("...?" a guard asks, waving ...): re-split the pair at
    # the quietest point near the syllable-proportional boundary
    ids = [l[0] for l in LINES]
    for a, b in [("L04", "L05")]:
        i, j = ids.index(a), ids.index(b)
        s, e = segs[i][0], segs[j][1]
        frac = align.syllables(texts[i]) / (align.syllables(texts[i]) + align.syllables(texts[j]))
        cut = align.split_point(audio, s, e, frac, window=0.35)
        segs[i][1], segs[j][0] = cut, cut + 0.01
    res = {}
    for (lid, _, en, _), (s, e) in zip(LINES, segs):
        res[lid] = {"file": os.path.relpath(p, ROOT), "start": round(s, 3), "end": round(e, 3),
                    "words": word_times(audio, s, e, en)}
        print(f"{lid} {s:6.2f}-{e:6.2f} ({e - s:4.2f}s)  {en}")
    json.dump(res, open(LINES_JSON, "w"), indent=1)
    return res


if __name__ == "__main__":
    main()
