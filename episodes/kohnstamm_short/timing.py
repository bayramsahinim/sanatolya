"""Narration schedule, word timings, caption groups and SRT for the Kohnstamm short."""
import json
import os
import re

import numpy as np

from cinecode import align, tts
from .script import DISPLAY, LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "assets", "audio", "tts", "kohnstamm")
GAP = 0.12


def clip(i):
    return tts.read_wav(os.path.join(CACHE, f"line_{i:02d}.wav"))


def _syl(w):
    w = re.sub(r"[^a-z0-9']", "", w.lower())
    if w.isdigit():
        return 4 if len(w) == 4 else 2 * len(w)   # "nineteen fifteen"
    v = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and v > 1 and not w.endswith("le"):
        v -= 1
    return max(1, v)


def _word_times(audio, text):
    """Spread words over the voiced frames of a clip (pauses are skipped, so
    punctuation pauses land between the right words)."""
    db = align.envelope_db(audio)
    thr = np.percentile(db, 95) - 30
    voiced = db >= thr
    hop = align.HOP / align.SR
    idx = np.nonzero(voiced)[0]
    cum = np.cumsum(voiced) * hop                       # voiced seconds up to frame
    total = cum[-1]
    words = text.split()
    wts = np.array([_syl(w) + 0.35 for w in words], float)
    edges = np.concatenate([[0], np.cumsum(wts)]) / wts.sum() * total

    def at(v, first):
        k = int(np.searchsorted(cum, v + (1e-6 if first else -1e-6), side="left"))
        k = min(max(k, idx[0]), idx[-1])
        return k * hop

    out = []
    for i, w in enumerate(words):
        s = at(edges[i], True)
        e = at(edges[i + 1], False) + hop
        out.append((w, s, max(e, s + 0.08)))
    return out


def schedule():
    """[(line_index, start, end, text, words[(w, s, e)])] in video time."""
    out = []
    prev = 0.0
    for i, (plan, text) in enumerate(LINES):
        a = clip(i)
        st = max(plan, prev + GAP)
        dur = len(a) / tts.SR
        words = [(w, st + s, st + e) for w, s, e in _word_times(a, text)]
        out.append((i, st, st + dur, text, words))
        prev = st + dur
    return out


def _disp(w):
    core = re.sub(r"[^A-Za-z0-9']", "", w).lower()
    if core in DISPLAY:
        w = re.sub(r"[A-Za-z]+", DISPLAY[core], w, count=1)
    return w


def caption_groups(sched):
    """1-3 word caption groups: (text, start, end)."""
    groups = []
    for _, st, en, text, words in sched:
        cur = []
        for k, (w, s, e) in enumerate(words):
            cur.append((w, s, e))
            chars = sum(len(x[0]) + 1 for x in cur)
            nxt = words[k + 1][0] if k + 1 < len(words) else None
            brk = (len(cur) == 3 or re.search(r"[,.?!]$", w) or nxt is None or chars + len(nxt or "") > 15
                   or (len(cur) == 2 and len(nxt or "") > 8))
            if brk:
                txt = " ".join(_disp(x[0]) for x in cur).rstrip(",")
                groups.append([txt, cur[0][1], cur[-1][2]])
                cur = []
    # each group stays until the next one starts (if close), else a short tail
    for a, b in zip(groups, groups[1:]):
        a[2] = b[1] if b[1] - a[2] < 0.45 else a[2] + 0.2
    groups[-1][2] += 0.25
    return [tuple(g) for g in groups]


def word_time(sched, line, word):
    for i, _, _, _, words in sched:
        if i == line:
            for w, s, e in words:
                if word.lower() in w.lower():
                    return s
    raise KeyError(word)


def _fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _wrap(s, n=42):
    if len(s) <= n:
        return s
    words = s.split()
    best = None
    for k in range(1, len(words)):
        a, b = " ".join(words[:k]), " ".join(words[k:])
        sc = max(len(a), len(b))
        if best is None or sc < best[0]:
            best = (sc, a + "\n" + b)
    return best[1]


def srt(sched, path):
    """One cue per sentence, timed to the spoken words."""
    cues = []
    for _, _, _, text, words in sched:
        cur = []
        for w, s, e in words:
            cur.append((w, s, e))
            if re.search(r"[.?!]$", w) and not w.endswith("..."):
                cues.append(cur)
                cur = []
        if cur:
            cues.append(cur)
    with open(path, "w", encoding="utf-8") as f:
        for n, c in enumerate(cues, 1):
            s = c[0][1] - 0.05
            e = c[-1][2] + 0.25
            if n < len(cues):
                e = min(e, cues[n][0][1] - 0.05 - 0.02)
            txt = " ".join(_disp(w) for w, _, _ in c)
            f.write(f"{n}\n{_fmt(s)} --> {_fmt(e)}\n{_wrap(txt)}\n\n")
    return len(cues)


if __name__ == "__main__":
    sc = schedule()
    for i, st, en, text, words in sc:
        print(f"{i:02d} {st:6.2f}-{en:6.2f}  {text}")
    for g in caption_groups(sc):
        print(f"   {g[1]:6.2f}-{g[2]:6.2f}  {g[0]}")
