"""Narration: Gemini TTS takes (cached) -> per-line clips -> timed voice track.

usage: python -m episodes.ancestry_en.voice          # synthesize missing takes + build timing
"""
import json
import os

import numpy as np

from cinecode import align, tts
from episodes.ancestry_en.script import (DEFAULT_GAP, GAP_AFTER, LEAD_IN, LINES, TAIL, TAKES, TEXT)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts_ancestry")
# 2.5-flash TTS: same Puck voice; the 3.x models looped the transcript for these takes
MODEL = "gemini-2.5-flash-preview-tts"
REL_DB = 28  # these takes have a ~-55 dB noise floor
BUILD = os.path.join(ROOT, "build", "ancestry_en")

NOTES = ("Narrator of a science explainer for a YouTube animation channel. Voice: young adult American male, "
         "clear and natural, curious and engaging, slightly playful but respectful of the scientific topic. "
         "Brisk YouTube Shorts pace (about three words per second) with natural emphasis on the numbers. Not deep, not booming, not a movie-trailer voice, "
         "never shouting, no fake excitement.\n"
         "Leave a short pause of about half a second between paragraphs.\n"
         "Speak only the transcript below, nothing else.")


def take_text(i):
    return "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(TEXT[l] for l in TAKES[i])


def take_path(i):
    return os.path.join(OUT, f"take_{i:02d}_{tts.text_hash(take_text(i), CFG['voice'], MODEL)}.wav")


def make_takes():
    for i in range(len(TAKES)):
        p = take_path(i)
        if os.path.exists(p):
            continue
        expect = sum(align.syllables(TEXT[l]) * 0.2 + 1.0 for l in TAKES[i])
        for attempt in range(3):
            a = tts.synth(take_text(i), p, MODEL, voice=CFG["voice"])
            d = len(a) / tts.SR
            print(f"take {i}: {d:.1f}s (expected ~{expect:.0f}s)")
            if d < expect * 1.6:
                break
            os.remove(p)  # model looped the transcript; ask again
        else:
            raise RuntimeError(f"take {i} keeps running long")


TEMPO = 1.16  # brings the read to the 80-85 s target without cutting any of the explanation


def squeeze_pauses(c, keep=0.24):
    """Shorten long internal pauses (commas) to `keep` seconds."""
    pauses, _, _ = align.find_pauses(c, min_len=keep + 0.06, rel_db=REL_DB)
    out, last = [], 0
    for a, b in pauses:
        if a < 0.1 or b > len(c) / tts.SR - 0.1:
            continue
        mid = int((a + b) / 2 * tts.SR)
        h = int(keep / 2 * tts.SR)
        out.append(c[last:int(a * tts.SR) + h])
        last = int(b * tts.SR) - h
    out.append(c[last:])
    return np.concatenate(out)


def speed_up(c):
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        tts.write_wav(a, c)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af",
                        f"rubberband=tempo={TEMPO}:pitchq=quality:formant=preserved:transients=smooth", b], check=True)
        return tts.read_wav(b)


def build():
    """Split takes into lines, lay them out on the timeline. Writes voice.wav + timing.json."""
    clips = {}
    for i, ids in enumerate(TAKES):
        audio = tts.read_wav(take_path(i))
        segs = align.align(audio, [TEXT[l] for l in ids], rel_db=REL_DB)
        for l, (s, e) in zip(ids, segs):
            clips[l] = speed_up(squeeze_pauses(align.trim(audio, s, e, pre=0.04, post=0.10)))
    t = LEAD_IN
    timing = {}
    parts = []
    for l, _, _ in LINES:
        c = clips[l]
        d = len(c) / tts.SR
        # internal pauses (for caption word timing)
        pauses, _, _ = align.find_pauses(c, min_len=0.12, rel_db=REL_DB)
        timing[l] = {"start": round(t, 3), "end": round(t + d, 3),
                     "pauses": [(round(a, 3), round(b, 3)) for a, b in pauses if 0.1 < a and b < d - 0.1]}
        parts.append((t, c))
        t += d + DEFAULT_GAP + GAP_AFTER.get(l, 0.0)
    total = t + TAIL
    buf = np.zeros(int(total * tts.SR) + 1, np.float32)
    for st, c in parts:
        a = int(st * tts.SR)
        buf[a:a + len(c)] += c
    os.makedirs(BUILD, exist_ok=True)
    tts.write_wav(os.path.join(BUILD, "voice.wav"), buf)
    json.dump({"duration": round(total, 3), "lines": timing}, open(os.path.join(BUILD, "timing.json"), "w"), indent=1)
    print(f"voice track {total:.2f}s")
    for l, v in timing.items():
        print(f"  {l:9s} {v['start']:6.2f}-{v['end']:6.2f}")
    return total


if __name__ == "__main__":
    make_takes()
    build()
