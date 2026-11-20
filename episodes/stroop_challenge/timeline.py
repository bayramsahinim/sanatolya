"""Timing: narration placement, word timings, card schedule, scene ranges.

Everything is derived from the real voice takes so picture and sound stay locked.
"""
import functools
import re

import numpy as np

from cinecode import tts
from episodes.stroop_challenge import make_voice as mv
from episodes.stroop_challenge.script import LEVELS, LINES

TEMPO = 1.10        # light speed-up of the narration (pitch preserved, ffmpeg atempo)
GAP = 0.12          # default breath between lines
GO_TO_CARD = 0.45   # "Go!" end -> first card
END_PAD = 2.5       # hold after the last line
SR = tts.SR


@functools.lru_cache(maxsize=None)
def take(lid):
    """Narration take for line `lid` at TEMPO (cached on disk in build/)."""
    import os
    import subprocess
    import tempfile
    if lid == "go3":
        g = mv.load("go1")
        segs = [x for x in _segments(g, min_gap=0.12) if x[1] - x[0] > 0.05]
        s0 = [x for x in segs if x[0] > segs[0][1]][0][0]   # first phrase after "Level one."
        a = g[max(0, int((s0 - 0.04) * SR)):]
    else:
        a = mv.load(lid)
    if TEMPO == 1.0:
        return a
    os.makedirs("build/tempo", exist_ok=True)
    out = f"build/tempo/{lid}_{TEMPO:.3f}_{len(a)}.wav"
    if not os.path.exists(out):
        with tempfile.NamedTemporaryFile(suffix=".wav") as f:
            tts.write_wav(f.name, a)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f.name, "-filter:a", f"atempo={TEMPO}",
                            "-ar", str(SR), "-ac", "1", out], check=True)
    return tts.read_wav(out)


def _segments(a, thr=0.012, min_gap=0.14, min_len=0.0):
    fr = int(0.01 * SR)
    e = np.array([np.sqrt((a[i:i + fr] ** 2).mean()) for i in range(0, max(1, len(a) - fr), fr)])
    on = e > thr
    segs, s = [], None
    for i, v in enumerate(on):
        if v and s is None:
            s = i
        if not v and s is not None:
            segs.append([s, i])
            s = None
    if s is not None:
        segs.append([s, len(on)])
    merged = []
    for sg in segs:
        if merged and (sg[0] - merged[-1][1]) * 0.01 < min_gap:
            merged[-1][1] = sg[1]
        else:
            merged.append(sg)
    return [(x * 0.01, y * 0.01) for x, y in merged if (y - x) * 0.01 >= min_len]


def word_times(text, a):
    """Approximate start time of every word in a take.

    Phrases (split on punctuation) are matched to the take's voiced segments when the
    counts agree; inside a phrase words are spread by character count."""
    words = text.split()
    dur = len(a) / SR
    # phrase boundaries
    phrases, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if re.search(r"[.,?!:;]$|\.\.\.$", w):
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    segs = _segments(a, min_gap=0.12)
    if len(segs) != len(phrases):
        segs = None
    out = [0.0] * len(words)
    for pi, ph in enumerate(phrases):
        if segs:
            s0, s1 = segs[pi]
        else:
            tot = sum(len(w) + 2 for w in words)
            before = sum(len(words[i]) + 2 for p in phrases[:pi] for i in p)
            mine = sum(len(words[i]) + 2 for i in ph)
            s0, s1 = dur * before / tot, dur * (before + mine) / tot
        tot = sum(len(words[i]) + 1 for i in ph)
        acc = 0
        for i in ph:
            out[i] = s0 + (s1 - s0) * acc / tot
            acc += len(words[i]) + 1
    return out


@functools.lru_cache(maxsize=None)
def build():
    """Return the full timing plan."""
    T = {"lines": {}, "levels": [], "l3words": []}
    cur = 0.0
    level_end = {}
    order = [l[0] for l in LINES]
    for lid, at, text in LINES:
        a = take(lid)
        if isinstance(at, str):          # starts after a level's cards
            start = level_end[at] + 0.35
        elif at is not None:
            start = max(at, cur)
        else:
            start = cur + GAP
        if lid == "go1":
            start = cur + 0.55           # let the GREEN example land
        d = len(a) / SR
        T["lines"][lid] = dict(start=start, end=start + d, text=text,
                               words=[start + w for w in word_times(text, a)])
        cur = start + d
        # cards follow the "Go!" lines
        go_lines = {"go1": 0, "go2": 1, "go3": 2}
        if lid in go_lines:
            li = go_lines[lid]
            L = LEVELS[li]
            c0 = cur + GO_TO_CARD
            cards = [(c0 + k * L["per_card"], c0 + (k + 1) * L["per_card"]) for k in range(len(L["cards"]))]
            T["levels"].append(dict(start=c0, end=cards[-1][1], cards=cards))
            level_end[f"L{li + 1}_END"] = cards[-1][1]
            cur = cards[-1][1]
    # level-3 distractor words: one per card, just after the card lands
    w = take("l3read")
    segs = [s for s in _segments(w, min_gap=0.15) if s[1] - s[0] >= 0.2]
    assert len(segs) == 8, f"level-3 read-out split into {len(segs)} words, expected 8"
    for k, (s0, s1) in enumerate(segs):
        c0 = T["levels"][2]["cards"][k][0]
        T["l3words"].append(dict(at=c0 + 0.10, src=(max(0, s0 - 0.03), min(len(w) / SR, s1 + 0.22)),
                                 word=LEVELS[2]["cards"][k][0]))
    T["end"] = cur + END_PAD
    T["order"] = order
    return T


def line(lid):
    return build()["lines"][lid]


def scenes():
    """(name, t0, t1) ranges covering the whole video."""
    T = build()
    L = T["lines"]
    lv = T["levels"]
    marks = [
        ("hook", 0.0),
        ("rule", L["rule"]["start"] - 0.15),
        ("intro1", L["go1"]["start"] - 0.1),
        ("play1", lv[0]["start"]),
        ("matched", lv[0]["end"]),
        ("intro2", L["lvl2"]["start"] - 0.1),
        ("play2", lv[1]["start"]),
        ("pause", lv[1]["end"]),
        ("race", L["interfere"]["start"] - 0.1),
        ("intro3", L["final3"]["start"] - 0.1),
        ("play3", lv[2]["start"]),
        ("end", lv[2]["end"]),
    ]
    out = []
    for i, (n, t0) in enumerate(marks):
        t1 = marks[i + 1][1] if i + 1 < len(marks) else T["end"]
        out.append((n, t0, t1))
    return out


if __name__ == "__main__":
    T = build()
    for lid in T["order"]:
        l = T["lines"][lid]
        print(f"{l['start']:6.2f}-{l['end']:6.2f}  {lid:8} {l['text']}")
    for i, lv in enumerate(T["levels"]):
        print(f"LEVEL {i+1}: {lv['start']:.2f}-{lv['end']:.2f} ({len(lv['cards'])} cards)")
    for n, a, b in scenes():
        print(f"  scene {n:8} {a:6.2f}-{b:6.2f}")
    print("END", round(T["end"], 2))
