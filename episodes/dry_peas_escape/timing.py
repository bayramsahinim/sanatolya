"""Global timing: every narration line starts where its Turkish counterpart starts in the
reference video (or straight after the previous line when the English runs longer).

SCHED[lid] = (t0, t1) global seconds of the (tempo-adjusted) clip.
WORDS[lid] = [(word, t0, t1), ...] global seconds, for captions and lip-sync.
"""
import json
import os

from episodes.dry_peas_escape.script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINES_JSON = os.path.join(ROOT, "assets", "audio", "tts", "dry_peas", "lines.json")

TEMPO = 1.08            # medium-fast delivery; also brings the cut to the source's ~68 s
CLIP_PRE, CLIP_POST = 0.05, 0.10
GAP_MIN = 0.16          # shortest breath between two lines
JOINED = {"L05"}        # read as the continuation of the previous line
TAIL = 1.0              # final hold after the last word

_meta = json.load(open(LINES_JSON))


def _build():
    sched, words = {}, {}
    t = 0.0
    for lid, src_t, _, _ in LINES:
        m = _meta[lid]
        dur = (m["end"] - m["start"] + CLIP_PRE + CLIP_POST) / TEMPO
        st = t if lid in JOINED else max(src_t, t + GAP_MIN)
        if lid == "L01":
            st = 0.25
        sched[lid] = (st, st + dur)
        clip0 = m["start"] - CLIP_PRE
        words[lid] = [(w, st + (a - clip0) / TEMPO, st + (b - clip0) / TEMPO) for w, a, b in m["words"]]
        t = st + dur
    return sched, words, t + TAIL


SCHED, WORDS, TOTAL = _build()


def word_t(lid, k, end=False):
    """global time of the k-th word of a line (negative k from the end)."""
    w = WORDS[lid][k]
    return w[2] if end else w[1]


def find_word(lid, text, end=False, nth=0):
    hits = [w for w in WORDS[lid] if w[0].strip('",.?!:').lower() == text.lower()]
    w = hits[nth]
    return w[2] if end else w[1]


if __name__ == "__main__":
    for lid, src_t, en, _ in LINES:
        a, b = SCHED[lid]
        print(f"{lid}  src {src_t:5.1f}  ->  {a:6.2f}-{b:6.2f}  (+{a - src_t:4.2f})  {en}")
    print("TOTAL", round(TOTAL, 2))
