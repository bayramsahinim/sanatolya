"""Timeline for the short: where every narration clip sits, word timings inside each clip,
caption groups, and the countdown beats the animation is keyed to."""
import functools
import json
import os
import re
import subprocess
import tempfile

import numpy as np

from cinecode import align, tts
from episodes.four_swallows.script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TTS_DIR = os.path.join(ROOT, "assets", "audio", "tts", "four_swallows")
SR = tts.SR

# Explanation lines get a barely audible 4% tempo lift so the short lands at ~28.5 s
# without cutting a single word or any of the countdown pauses.
TEMPO = {"reflex": 1.04, "kicks": 1.04, "saliva": 1.04, "nothing": 1.04, "harder": 1.04}
COUNT_SPACING = 1.60      # seconds between numbers: time to actually swallow
FOURTH_HOLD = 1.60        # silence after "Four" while the attempt stalls


def atempo(x, tempo):
    if abs(tempo - 1) < 1e-3:
        return x
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        tts.write_wav(a, x)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a, "-af", f"atempo={tempo}", b], check=True)
        return tts.read_wav(b)


@functools.lru_cache(maxsize=None)
def clips():
    meta = json.load(open(os.path.join(TTS_DIR, "lines.json")))
    out = {}
    for lid, *_ in LINES:
        x = tts.read_wav(os.path.join(ROOT, meta[lid]["file"]))
        out[lid] = atempo(x, TEMPO.get(lid, 1.0)).astype(np.float32)
    return out


def _voiced(x):
    db = align.envelope_db(x)
    thr = db.max() - 34
    v = np.where(db > thr)[0]
    return v[0] * align.HOP / SR, (v[-1] + 1) * align.HOP / SR, db, thr


def word_times(lid, text, t0):
    """Absolute (start, end, word) for each word: syllable-weighted over the voiced time of the clip,
    with internal pauses skipped (so pauses fall between words, where they really are)."""
    x = clips()[lid]
    on, off, db, thr = _voiced(x)
    frames = np.arange(len(db)) * align.HOP / SR
    voiced = (db > thr - 6) & (frames >= on) & (frames <= off)
    # close tiny gaps (< 60 ms) so stops inside words don't count as pauses
    v = voiced.copy()
    i = 0
    while i < len(v):
        if not v[i] and on < frames[i] < off:
            j = i
            while j < len(v) and not v[j]:
                j += 1
            if (j - i) * align.HOP / SR < 0.06:
                v[i:j] = True
            i = j
        else:
            i += 1
    vt = np.cumsum(v) * align.HOP / SR           # voiced-time clock
    total = vt[-1]
    words = text.replace('"', "").split()
    syl = np.array([max(1.0, align.syllables(w) - 1.5) for w in words])
    cum = np.concatenate([[0], np.cumsum(syl)]) / syl.sum() * total

    def at(vtime):
        k = int(np.searchsorted(vt, vtime))
        return frames[min(k, len(frames) - 1)]

    res = []
    for k, w in enumerate(words):
        res.append((t0 + at(cum[k] + 1e-4), t0 + at(cum[k + 1]), w))
    return res


@functools.lru_cache(maxsize=None)
def timeline():
    c = clips()
    dur = {k: len(v) / SR for k, v in c.items()}
    start = {}
    start["hook"] = 0.02
    start["easy"] = start["hook"] + dur["hook"] + 0.06
    start["try"] = start["easy"] + dur["easy"] + 0.10
    start["c1"] = start["try"] + dur["try"] + 0.30
    for k in (2, 3, 4):
        start[f"c{k}"] = start[f"c{k-1}"] + COUNT_SPACING
    start["stuck"] = start["c4"] + dur["c4"] + FOURTH_HOLD - 0.55
    seq = ["stuck", "reflex", "kicks", "saliva", "nothing", "harder"]
    gaps = {"reflex": 0.20, "kicks": 0.10, "saliva": 0.14, "nothing": 0.10, "harder": 0.12}
    for a, b in zip(seq, seq[1:]):
        start[b] = start[a] + dur[a] + gaps[b]
    start["again"] = start["harder"] + dur["harder"] + 0.30
    end = start["again"] + dur["again"] + 0.38
    return start, dur, end


def beats():
    """Key animation times (absolute seconds)."""
    start, dur, end = timeline()
    b = {"end": end}
    for k in range(1, 5):
        on = start[f"c{k}"] + _voiced(clips()[f"c{k}"])[0]
        b[f"n{k}"] = on                        # number heard
        b[f"sw{k}"] = on + 0.42                # swallow begins
        b[f"ok{k}"] = on + 1.18                # checkmark (1-3)
    b["stall"] = b["n4"] + 1.25                # 4th turns amber
    b["stuck"] = start["stuck"]
    b["to_lens"] = start["reflex"] - 0.30      # front -> cutaway transition start
    words = {lid: word_times(lid, text, start[lid]) for lid, text, *_ in LINES}
    b["words"] = words
    w = words
    b["reflex_word"] = w["reflex"][-1][0]
    b["something"] = w["kicks"][4][0]
    b["kick_swallow"] = w["kicks"][-1][0] - 0.05
    b["saliva_low"] = w["saliva"][3][0]       # "runs"
    b["brain"] = w["saliva"][6][0]
    b["bubble"] = w["saliva"][-1][0]
    b["nothing"] = start["nothing"]
    b["hard_swallow"] = w["harder"][2][0]     # "next"
    b["to_front"] = start["harder"] + dur["harder"] - 0.05
    b["again"] = start["again"]
    return b


def caption_groups():
    """[(t0, t1, text)] burned-in caption groups (1-3 words), locked to the words."""
    start, dur, end = timeline()
    b = beats()
    out = []
    for lid, text, _, groups in LINES:
        if not groups:                       # countdown numbers: one caption each
            groups = [text.rstrip(".") + "…"]
        wt = b["words"][lid]
        k = 0
        line_groups = []
        for g in groups:
            n = len(g.replace('"', "").replace("…", "").split())
            ws = wt[k:k + n]
            k += n
            line_groups.append([ws[0][0] - 0.04, ws[-1][1], g])
        assert k == len(wt), (lid, k, len(wt))
        for i, g in enumerate(line_groups):
            if i + 1 < len(line_groups):
                g[1] = line_groups[i + 1][0]
            else:
                g[1] = g[1] + (0.85 if lid.startswith("c") else 0.18)
        out.extend(tuple(g) for g in line_groups)
    # never overlap the next line's first group
    for i in range(len(out) - 1):
        if out[i][1] > out[i + 1][0]:
            out[i] = (out[i][0], out[i + 1][0], out[i][2])
    return out


if __name__ == "__main__":
    start, dur, end = timeline()
    for lid, text, *_ in LINES:
        print(f"{lid:8s} {start[lid]:6.2f} - {start[lid]+dur[lid]:6.2f}  {text}")
    print("end", round(end, 2))
    b = beats()
    print({k: round(v, 2) for k, v in b.items() if k != "words"})
    for g in caption_groups():
        print(f"  {g[0]:6.2f} {g[1]:6.2f}  {g[2]}")
