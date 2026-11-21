"""Narration: one continuous directed Gemini take -> per-line clips -> voice track timed to the original.

Each English line starts where its Turkish line started in the original (picture is retimed only where
the English line runs longer than the Turkish one; see timeline.py).

usage:
  python -m episodes.baby_break_en.voice take     # record the take (cached in assets/audio/tts_baby)
  python -m episodes.baby_break_en.voice build    # split + place -> build/baby_break_en/voice.wav + timing.json
"""
import json
import os
import sys
import time

import numpy as np

from cinecode import align, tts
from episodes.baby_break_en.script import LINES, TEXT

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets", "audio", "tts_baby")
BUILD = os.path.join(ROOT, "build", "baby_break_en")
DIRECTION = open(os.path.join(HERE, "direction.txt")).read().strip()
MODEL = os.environ.get("VO_MODEL", "gemini-3.1-flash-tts-preview")
VOICE = os.environ.get("VO_VOICE", "Fenrir")  # closest to the reference narration (blind comparison vs Puck, Charon)
TAKE = int(os.environ.get("VO_TAKE", "0"))
REL_DB = 30
IDS = [l[0] for l in LINES]


def take_text():
    return DIRECTION + "\n\n#### TRANSCRIPT\n" + "\n".join(TEXT[l] for l in IDS)


def take_path(model=MODEL, voice=VOICE, n=TAKE):
    return os.path.join(OUT, f"take_{voice}_{n}_{tts.text_hash(take_text(), voice, model)}.wav")


def record(model=MODEL, voice=VOICE, n=TAKE):
    p = take_path(model, voice, n)
    exp = sum(align.syllables(TEXT[l]) * 0.19 + 0.35 for l in IDS)
    for attempt in range(3):
        a = tts.synth(take_text(), p, model, voice=voice, retries=3)
        d = len(a) / tts.SR
        print(f"{os.path.basename(p)}: {d:.1f}s (expected ~{exp:.0f}s)")
        if d < exp * 1.5:
            return p
        os.remove(p)  # looped transcript
        time.sleep(20)
    raise RuntimeError("take keeps running long")


def cap_pauses(c, cap=0.36):
    pauses, _, _ = align.find_pauses(c, min_len=cap + 0.05, rel_db=REL_DB)
    out, last = [], 0
    for a, b in pauses:
        if a < 0.1 or b > len(c) / tts.SR - 0.1:
            continue
        h = int(cap / 2 * tts.SR)
        out.append(c[last:int(a * tts.SR) + h])
        last = int(b * tts.SR) - h
    out.append(c[last:])
    return np.concatenate(out)


def clips_from_take(p):
    audio = tts.read_wav(p)
    segs = align.align(audio, [TEXT[l] for l in IDS], rel_db=REL_DB)
    clips = {}
    for l, (s, e) in zip(IDS, segs):
        clips[l] = cap_pauses(align.trim(audio, s, e, pre=0.05, post=0.14))
    for l, c in clips.items():  # short fades: no clicks or abrupt cuts at line edges
        n_in, n_out = int(0.012 * tts.SR), int(0.04 * tts.SR)
        c = c.copy()
        c[:n_in] *= np.linspace(0, 1, n_in)
        c[-n_out:] *= np.linspace(1, 0, n_out)
        clips[l] = c
    for l, c in clips.items():  # level-match on active speech
        db = align.envelope_db(c)
        act = db > np.percentile(db, 95) - 20
        fr = c[: len(db) * align.HOP].reshape(len(db), align.HOP)[act]
        clips[l] = c * (10 ** (-21 / 20) / np.sqrt((fr ** 2).mean() + 1e-12))
    return clips


MIN_GAP = 0.22  # shortest breath between lines
MAX_EXTRA_GAP = 0.10  # a pause may exceed the original pause by at most this


def build(p=None):
    clips = clips_from_take(p or take_path())
    t = 0.0
    timing, parts = {}, []
    for k, (l, o0, o1, _, _) in enumerate(LINES):
        c = clips[l]
        d = len(c) / tts.SR
        # keep the original start when possible (never earlier than the previous line + a breath), but never
        # leave a pause much longer than the original's pause between these two lines
        if k:
            orig_gap = o0 - LINES[k - 1][2]
            start = min(max(o0, t + MIN_GAP), t + max(MIN_GAP, orig_gap + MAX_EXTRA_GAP))
        else:
            start = o0 + 0.05
        pauses, _, _ = align.find_pauses(c, min_len=0.12, rel_db=REL_DB)
        timing[l] = {"start": round(start, 3), "end": round(start + d, 3), "orig": [o0, o1],
                     "pauses": [(round(a, 3), round(b, 3)) for a, b in pauses if 0.1 < a and b < d - 0.1]}
        parts.append((start, c))
        t = start + d
    from episodes.baby_break_en.script import ORIG_DURATION
    total = max(t + (ORIG_DURATION - LINES[-1][2]), ORIG_DURATION)
    buf = np.zeros(int(total * tts.SR) + 1, np.float32)
    for st, c in parts:
        a = int(st * tts.SR)
        buf[a:a + len(c)] += c
    os.makedirs(BUILD, exist_ok=True)
    tts.write_wav(os.path.join(BUILD, "voice.wav"), buf)
    json.dump({"duration": round(total, 3), "take": os.path.basename(p or take_path()), "lines": timing},
              open(os.path.join(BUILD, "timing.json"), "w"), indent=1)
    print(f"voice track {total:.2f}s (original {ORIG_DURATION}s)")
    for l, v in timing.items():
        o0, o1 = v["orig"]
        print(f"  {l:4s} EN {v['start']:6.2f}-{v['end']:6.2f} ({v['end'] - v['start']:4.2f}s)   TR {o0:6.2f}-{o1:6.2f} ({o1 - o0:4.2f}s)")
    return total


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "take":
        record()
    elif cmd == "audition":  # VO_VOICE=... VO_MODEL=... python -m ... audition
        record()
        build()
    elif cmd == "build":
        build(sys.argv[2] if len(sys.argv) > 2 else None)
