"""Narration: a few long takes from ONE TTS model (consistent voice), split into lines.

usage: python -m episodes.numbers_above.make_voice          # synthesize missing takes
       python -m episodes.numbers_above.make_voice split    # split takes into per-line wavs
"""
import json
import os
import sys
import time

import numpy as np

from cinecode import tts
from cinecode.align import HOP, find_pauses, syllables, trim
from .script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "assets", "audio", "tts_numbers")
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
MODEL = "gemini-3.8-flash-lite-tts"
VOICE = CFG["voice"]

NOTES = ("Narrator of a reflective, emotional short animated film. Voice: young adult American male, "
         "calm, clear and natural, warm and quietly curious, like telling a friend something strange and "
         "meaningful that happened to them. Medium pace, unhurried but never slow or sleepy. Gentle natural "
         "pauses at ellipses. Not dark, not depressing, not dramatic, not a trailer voice, no whispering, no "
         "fake emotion. Read quoted dialogue lightly and naturally, in the same voice.\n"
         "Each paragraph is one line. Leave a clear pause of about one and a half seconds between paragraphs.\n"
         "Speak only the transcript below, nothing else.")

CHUNKS = [(0, 10), (10, 17), (17, 24), (24, 34), (34, 42)]


def take_text(i):
    a, b = CHUNKS[i]
    return "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(s for _, s, _ in LINES[a:b])


def take_path(i):
    return os.path.join(CACHE, f"take_{i}_{tts.text_hash(take_text(i), VOICE, MODEL)}.wav")


def line_path(lid):
    return os.path.join(CACHE, "lines", f"{lid}.wav")


def synth_all():
    for i in range(len(CHUNKS)):
        p = take_path(i)
        if os.path.exists(p):
            continue
        a = tts.synth(take_text(i), p, MODEL, voice=VOICE, retries=4)
        print(f"take {i}: {len(a) / tts.SR:.1f}s", flush=True)
        time.sleep(8)


# Usable region of each take (seconds), found by transcribing the takes: the lite TTS model
# sometimes speaks the director notes (take 0), repeats a block (take 2) or adds a preamble (take 3).
REGIONS = {0: (43.4, None), 1: (None, None), 2: (None, 34.9), 3: (8.7, None), 4: (None, None)}


def _snap(pauses, t, before=True):
    """Return the edge of the pause nearest to t (pause end for a start, pause start for an end)."""
    best = min(pauses, key=lambda p: abs((p[1] if before else p[0]) - t))
    return best[1] if before else best[0]


def split():
    os.makedirs(os.path.join(CACHE, "lines"), exist_ok=True)
    report = {}
    for i, (a, b) in enumerate(CHUNKS):
        audio = tts.read_wav(take_path(i))
        lines = LINES[a:b]
        pauses, db, thr = find_pauses(audio, min_len=0.22)
        voiced = np.where(db >= thr)[0]
        t0, t1 = voiced[0] * HOP / tts.SR, (voiced[-1] + 1) * HOP / tts.SR
        r0, r1 = REGIONS[i]
        if r0 is not None:
            t0 = _snap(pauses, r0, before=True)
        if r1 is not None:
            t1 = _snap(pauses, r1, before=False)
        inner = [p for p in pauses if p[0] > t0 + 0.2 and p[1] < t1 - 0.2]
        exp = np.array([syllables(s) for _, s, _ in lines], float)
        _dp(inner, t0, t1, exp, len(lines))
        starts = [t0] + [p[1] for p in _chosen]
        ends = [p[0] for p in _chosen] + [t1]
        for (lid, s, _), st, en in zip(lines, starts, ends):
            clip = _cap_pauses(trim(audio, st, en, pre=0.04, post=0.14))
            tts.write_wav(line_path(lid), clip)
            report[lid] = round(len(clip) / tts.SR, 2)
            print(lid, f"{st:6.2f}-{en:6.2f}", f"{len(clip) / tts.SR:5.2f}s", f"rate={syllables(s) / (en - st):.2f}", s[:50], flush=True)
    json.dump(report, open(os.path.join(CACHE, "lines", "durations.json"), "w"), indent=1)
    print("total speech", round(sum(report.values()), 1))


def _cap_pauses(clip, cap=0.55):
    """Shorten internal silences longer than `cap` seconds (keeps dramatic pauses, drops dead air)."""
    pauses, _, _ = find_pauses(clip, min_len=cap)
    out, last = [], 0
    for s, e in pauses:
        if s < 0.1 or e > len(clip) / tts.SR - 0.1:
            continue
        cut0 = int((s + cap / 2) * tts.SR)
        cut1 = int((e - cap / 2) * tts.SR)
        out.append(clip[last:cut0])
        last = cut1
    out.append(clip[last:])
    return np.concatenate(out)


_chosen = []
best_pause_end = []


def _dp(inner, t0, t1, exp, n):
    """Pick n-1 pauses (in order) so piece durations are proportional to expected syllables."""
    global _chosen, best_pause_end
    m = len(inner)
    total = t1 - t0
    rate = exp.sum() / total
    import functools

    @functools.lru_cache(None)
    def f(j, k, prev_end_idx):
        # j: line index whose start is at pause prev_end_idx (-1 = t0); k: next candidate pause
        start = t0 if prev_end_idx < 0 else inner[prev_end_idx][1]
        if j == n - 1:
            d = t1 - start
            return _cost(d, exp[j], rate), ()
        best = (1e9, ())
        for q in range(k, m - (n - 2 - j)):
            d = inner[q][0] - start
            if d <= 0.3:
                continue
            plen = inner[q][1] - inner[q][0]
            c = _cost(d, exp[j], rate) - 2.5 * min(plen, 1.6)
            rest, path = f(j + 1, q + 1, q)
            if c + rest < best[0]:
                best = (c + rest, (q,) + path)
        return best

    _, path = f(0, 0, -1)
    _chosen = [inner[q] for q in path]
    best_pause_end = [p[1] for p in _chosen]
    return [p[0] for p in _chosen]


def _cost(d, syl, rate):
    r = (syl / d) / rate
    return 4.0 * (np.log(r)) ** 2


if __name__ == "__main__":
    if sys.argv[1:] == ["split"]:
        split()
    else:
        synth_all()
