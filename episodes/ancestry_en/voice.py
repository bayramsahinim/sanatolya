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

NOTES = ("You are a smart, entertaining American YouTube creator explaining something fascinating to a friend. "
         "Voice: young adult American male, natural General American accent, clear, bright and articulate. "
         "Energetic but controlled, conversational and engaging, slightly curious and playful, with natural "
         "emotional variation: a little wonder on the big numbers, a knowing smile on the twists. "
         "Medium-fast pace, like a well-edited YouTube Short: keep it moving, no dramatic pauses, no drawn-out words. "
         "Keep the same voice, energy and microphone distance from start to finish. "
         "Not a documentary voice, not deep or booming, not a radio announcer, never shouting, no fake excitement.\n"
         "Pause briefly (about a third of a second) between paragraphs.\n"
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


TEMPO = 1.0  # no time-stretching: it made the previous read sound synthetic


def squeeze_pauses(c, keep=0.32):
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


# ---------------------------------------------------------------- Kokoro (local neural TTS)
ENGINE = "kokoro"          # "kokoro" (local, per line) or "gemini" (takes, needs daily quota)
KOKORO_VOICE = "am_fenrir"  # picked in a blind comparison against the reference narration
KOKORO_SPEED = 1.13
KOKORO_DIR = os.path.join(ROOT, "build", "kokoro")
KOKORO_URL = "https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main"
# per-line delivery: slight pace changes give natural variation (lists quicker, reveals steadier)
LINE_SPEED = {"hook1": 0.97, "hook2": 0.95, "par": 1.04, "gp": 1.04, "ggp": 1.03, "g30": 1.03, "mrca": 1.03,
              "trace": 1.03, "think": 0.93, "end": 0.95, "eve": 0.97, "couple": 1.02}
# spoken forms that the phonemizer reads more naturally
SAY = {"Y-chromosomal": "Y chromosomal"}


def _kokoro():
    import subprocess
    os.makedirs(os.path.join(KOKORO_DIR, "voices"), exist_ok=True)
    model = os.path.join(KOKORO_DIR, "model.onnx")
    if not os.path.exists(model):
        subprocess.run(["curl", "-sL", "-o", model, KOKORO_URL + "/onnx/model.onnx"], check=True)
    vb = os.path.join(KOKORO_DIR, "voices", KOKORO_VOICE + ".bin")
    if not os.path.exists(vb):
        subprocess.run(["curl", "-sL", "-o", vb, f"{KOKORO_URL}/voices/{KOKORO_VOICE}.bin"], check=True)
    npz = os.path.join(KOKORO_DIR, KOKORO_VOICE + ".npz")
    if not os.path.exists(npz):
        np.savez(npz, **{KOKORO_VOICE: np.fromfile(vb, dtype=np.float32).reshape(510, 1, 256)})
    from kokoro_onnx import Kokoro
    return Kokoro(model, npz)


def kokoro_line(l, k=None):
    txt = TEXT[l]
    for a, b in SAY.items():
        txt = txt.replace(a, b)
    sp = round(KOKORO_SPEED * LINE_SPEED.get(l, 1.0), 3)
    p = os.path.join(OUT, f"kokoro_{l}_{tts.text_hash(txt, KOKORO_VOICE, str(sp))}.wav")
    if not os.path.exists(p):
        k = k or _kokoro()
        a, sr = k.create(txt, voice=KOKORO_VOICE, speed=sp, lang="en-us")
        assert sr == tts.SR
        tts.write_wav(p, a.astype(np.float32))
    return tts.read_wav(p)


def build():
    """Split takes into lines, lay them out on the timeline. Writes voice.wav + timing.json."""
    clips = {}
    if ENGINE == "kokoro":
        k = _kokoro()
        for l, _, _ in LINES:
            c = kokoro_line(l, k)
            db = align.envelope_db(c)
            v = np.where(db > np.percentile(db, 95) - 35)[0]
            c = c[max(0, v[0] * align.HOP - 1200): min(len(c), (v[-1] + 1) * align.HOP + 2400)]
            clips[l] = squeeze_pauses(c)
    for i, ids in enumerate(TAKES if ENGINE == "gemini" else []):
        audio = tts.read_wav(take_path(i))
        segs = align.align(audio, [TEXT[l] for l in ids], rel_db=REL_DB)
        for l, (s, e) in zip(ids, segs):
            c = squeeze_pauses(align.trim(audio, s, e, pre=0.05, post=0.12))
            clips[l] = speed_up(c) if TEMPO != 1.0 else c
    # level-match lines (active-speech RMS) so no line jumps out
    for l, c in clips.items():
        db = align.envelope_db(c)
        act = db > np.percentile(db, 95) - 20
        frames = c[: len(db) * align.HOP].reshape(len(db), align.HOP)[act]
        rms = np.sqrt((frames ** 2).mean() + 1e-12)
        clips[l] = c * (10 ** (-22 / 20) / rms)
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
    if ENGINE == "gemini":
        make_takes()
    build()
