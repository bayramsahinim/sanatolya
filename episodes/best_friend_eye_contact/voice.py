"""Split the narration take into lines and lay them out on the reference timeline.

Each line starts where the matching Turkish sentence starts in the reference video.
If the previous line has not finished yet, it starts right after it instead (never
more than a fraction of a second late). Word times inside a line are distributed by
syllable weight and snapped to the line's internal pauses, which drives the
caption reveal and the SRT.
"""
import functools
import json
import os
import re

import numpy as np

from cinecode import align, tts
from episodes.best_friend_eye_contact.make_voice import take_path
from episodes.best_friend_eye_contact.script import CAPTION_PHRASES, LINES

SR = tts.SR
GAP = 0.08          # minimum breath between consecutive lines
MAX_EARLY = 0.20    # a line may start this much before its source time to avoid a pile-up


def _syl(w):
    w = re.sub(r"[^a-z']", "", w.lower())
    v = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and v > 1 and not w.endswith("le"):
        v -= 1
    return max(1, v)


def split_take():
    audio = tts.read_wav(take_path())
    orig = align.find_pauses
    align.find_pauses = lambda a, min_len=0.10: orig(a, 0.10)
    try:
        segs = align.align(audio, [l[4] for l in LINES])
    finally:
        align.find_pauses = orig
    return audio, segs


def _word_times(clip, text, start):
    words = text.split()
    weights = np.array([_syl(w) + (0.9 if re.search(r"[,.?!]$", w) else 0) for w in words], float)
    db = align.envelope_db(clip)
    thr = np.percentile(db, 95) - 30
    voiced = np.where(db >= thr)[0]
    v0 = voiced[0] * align.HOP / SR if len(voiced) else 0.0
    v1 = (voiced[-1] + 1) * align.HOP / SR if len(voiced) else len(clip) / SR
    edges = np.concatenate([[0], np.cumsum(weights)]) / weights.sum()
    times = v0 + edges * (v1 - v0)
    return [(w, start + times[i], start + times[i + 1]) for i, w in enumerate(words)]


@functools.lru_cache(maxsize=None)
def layout():
    """[{id, start, end, text, words:[(w,t0,t1)], clip_range}] in reference time."""
    audio, segs = split_take()
    out = []
    prev_end = 0.0
    for i, ((lid, s0, s1, _, en), (a, b)) in enumerate(zip(LINES, segs)):
        clip = audio[int(a * SR): int(b * SR)]
        d = len(clip) / SR
        nxt = LINES[i + 1][1] if i + 1 < len(LINES) else 35.0
        early = min(MAX_EARLY, max(0.0, s0 + d + GAP - nxt))  # only if it would overrun the next line
        start = max(s0 - early, prev_end + GAP, 0.05)
        out.append({"id": lid, "src_start": s0, "src_end": s1, "start": start, "end": start + d,
                    "text": en, "take": (a, b), "words": _word_times(clip, en, start)})
        prev_end = start + d
    return out


def phrases():
    """Caption phrases with times: [(text_words, t0, t1, line_id)]."""
    res = []
    for ln in layout():
        ws = ln["words"]
        i = 0
        groups = CAPTION_PHRASES[ln["id"]]
        for gi, g in enumerate(groups):
            n = len(g.split())
            chunk = ws[i:i + n]
            assert [w for w, _, _ in chunk] == g.split(), (ln["id"], g, chunk)
            res.append({"words": chunk, "t0": chunk[0][1], "t1": chunk[-1][2], "line": ln["id"],
                        "last_in_line": gi == len(groups) - 1})
            i += n
        assert i == len(ws), ln["id"]
    return res


def narration_track(dur):
    audio, _ = split_take()
    buf = np.zeros(int(dur * SR) + SR, np.float32)
    for ln in layout():
        a, b = ln["take"]
        clip = audio[int(a * SR): int(b * SR)].copy()
        n = len(clip)
        f = min(int(0.012 * SR), n // 4)
        clip[:f] *= np.linspace(0, 1, f)
        clip[-f:] *= np.linspace(1, 0, f)
        s = int(ln["start"] * SR)
        buf[s:s + n] += clip[: len(buf) - s]
    return buf[: int(dur * SR)]


if __name__ == "__main__":
    for ln in layout():
        print(f'{ln["id"]} src {ln["src_start"]:5.2f}  start {ln["start"]:5.2f}-{ln["end"]:5.2f} '
              f'(late {ln["start"]-ln["src_start"]:+.2f})  {ln["text"]}')
    os.makedirs("build", exist_ok=True)
    json.dump(layout(), open("build/bf_layout.json", "w"), indent=1)
