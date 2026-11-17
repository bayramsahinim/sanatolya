"""Place each English narration line on the beat of its Turkish counterpart.

The narration is one continuous Gemini TTS take; Whisper word timestamps
(assets/audio/tts_cola/words.json) split it into lines. Each line is placed at
max(turkish_start, previous_end + gap) so the English voice follows the original
video's rhythm without ever overlapping itself. Lines that run together in the take
(no breath between them) stay glued so the delivery remains natural.
"""
import json
import os
import re

from episodes.glass_bottle_cola.script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TTS_DIR = os.path.join(ROOT, "assets", "audio", "tts_cola")
TAKE = os.path.join(TTS_DIR, "take_9cb6312f89.wav")
WORDS = os.path.join(TTS_DIR, "words.json")

GAP_SENTENCE = 0.30
GAP_COMMA = 0.14
GLUE = 0.15          # take gap below which two lines are kept contiguous
PRE, POST = 0.06, 0.16


def _norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def build():
    words = json.load(open(WORDS))
    out = []
    k = 0
    prev = None
    for lid, tr0, text, chunks in LINES:
        n = len(text.split())
        ws = words[k:k + n]
        k += n
        s, e = ws[0][0], ws[-1][1]
        if prev is None:
            start = tr0
        else:
            take_gap = s - prev["take_e"]
            if take_gap < GLUE:
                start = prev["start"] + (s - prev["take_s"])
            else:
                gap = GAP_COMMA if prev["text"].rstrip().endswith(",") else GAP_SENTENCE
                start = max(tr0, prev["end"] + gap)
        off = start - s
        line = {"id": lid, "text": text, "tr0": tr0, "take_s": s, "take_e": e,
                "start": start, "end": e + off, "off": off,
                "words": [(a + off, b + off, w) for a, b, w in ws]}
        # caption chunks -> word ranges
        cw, j = [], 0
        for c in chunks:
            m = len(c.split())
            cw.append((c, line["words"][j][0], line["words"][j + m - 1][1]))
            j += m
        assert j == n, lid
        line["chunks"] = cw
        out.append(line)
        prev = line
    assert k == len(words), (k, len(words))
    return out


TL = build()
L = {l["id"]: l for l in TL}


def ws(lid, i):
    """start time of word i (0-based, negative ok) of a line."""
    return L[lid]["words"][i][0]


def we(lid, i):
    return L[lid]["words"][i][1]


def word(lid, token, nth=0):
    """start time of the nth word in a line matching token."""
    hits = [w for w in L[lid]["words"] if _norm(w[2]) == _norm(token)]
    return hits[nth][0]


def S(lid):
    return L[lid]["start"]


def E(lid):
    return L[lid]["end"]


if __name__ == "__main__":
    for l in TL:
        print(f"{l['id']}  tr {l['tr0']:5.2f}  en {l['start']:5.2f}-{l['end']:5.2f}  drift {l['start'] - l['tr0']:+.2f}  {l['text']}")
