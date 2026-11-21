"""Voiceover replacement on a LOCKED picture.

The visuals (and the captions burned into them) were rendered from timing_locked.json. This module
records new narration as continuous, directed Gemini takes (one per story section, so intonation flows
across sentences), splits them into lines, and places every line at its locked start time. Nothing about
the picture changes; the final mux copies the existing video stream bit for bit.

usage:
  python -m episodes.ancestry_en.voice_replace audition VOICE [MODEL]   # short test take
  python -m episodes.ancestry_en.voice_replace takes                     # record missing section takes
  python -m episodes.ancestry_en.voice_replace build                     # split + fit -> build/ancestry_en/voice.wav
"""
import json
import os
import subprocess
import sys
import tempfile
import time

import numpy as np

from cinecode import align, tts
from episodes.ancestry_en.script import LINES, TEXT

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets", "audio", "tts_ancestry")
BUILD = os.path.join(ROOT, "build", "ancestry_en")
LOCKED = json.load(open(os.path.join(HERE, "timing_locked.json")))
DIRECTION = open(os.path.join(HERE, "direction.txt")).read().strip()

MODEL = os.environ.get("VO_MODEL", "gemini-3.1-flash-tts-preview")
VOICE = os.environ.get("VO_VOICE", "Puck")
MAX_FIT = 0.06  # never time-adjust a line by more than this; report instead

SECTIONS = [
    ["hook1", "hook2", "intro", "par", "gp", "ggp", "dbl"],
    ["g30", "pop", "same", "mix", "mrca"],
    ["rewind", "gen", "mt", "eve"],
    ["adam", "couple", "trace", "unbroken"],
    ["out", "route", "think", "rel", "end"],
]
# how each section should feel (added to the director's notes for that take)
SECTION_NOTE = {
    0: "This take is the opening and the family-tree start: genuine curiosity, then interested and a bit amused by the numbers.",
    1: "This take is the big-numbers part: amused by how fast it grows, then the 'aha' that trees overlap; the last line is a calm, intriguing fact.",
    2: "This take goes deep into the past: clear and confident, matter-of-fact, still talking to a friend.",
    3: "This take explains genetic lineages: clear and grounded; the 'not a couple' line has a light, knowing touch.",
    4: "This take is the journey out of Africa and the ending. Keep it moving through the places, then for the last line slow down slightly and let it land, quietly meaningful.",
}
REL_DB = 30


def take_text(i, lines=None):
    lines = lines or SECTIONS[i]
    note = SECTION_NOTE.get(i, "")
    body = DIRECTION.replace("Speak only the transcript, nothing else.", note + "\nSpeak only the transcript, nothing else.")
    return body + "\n\n#### TRANSCRIPT\n" + "\n".join(TEXT[l] for l in lines)


def take_path(i):
    return os.path.join(OUT, f"vo3_{i:02d}_{tts.text_hash(take_text(i), VOICE, MODEL)}.wav")


def expected(lines):
    return sum(align.syllables(TEXT[l]) * 0.19 + 0.35 for l in lines)


def record_takes():
    for i in range(len(SECTIONS)):
        p = take_path(i)
        if os.path.exists(p):
            print("cached", os.path.basename(p))
            continue
        exp = expected(SECTIONS[i])
        for attempt in range(2):
            a = tts.synth(take_text(i), p, MODEL, voice=VOICE, retries=2)
            d = len(a) / tts.SR
            print(f"take {i}: {d:.1f}s (expected ~{exp:.0f}s)")
            if d < exp * 1.6:
                break
            os.remove(p)  # looped transcript
            time.sleep(30)
        time.sleep(25)


def _stretch(c, ratio):
    """ratio > 1 shortens. Only used for |ratio-1| <= MAX_FIT."""
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        tts.write_wav(a, c)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af",
                        f"rubberband=tempo={ratio:.4f}:pitchq=quality:formant=preserved", b], check=True)
        return tts.read_wav(b)


def cap_pauses(c, cap=0.42):
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


def split_lines():
    clips = {}
    for i, ids in enumerate(SECTIONS):
        audio = tts.read_wav(take_path(i))
        segs = align.align(audio, [TEXT[l] for l in ids], rel_db=REL_DB)
        for l, (s, e) in zip(ids, segs):
            clips[l] = cap_pauses(align.trim(audio, s, e, pre=0.05, post=0.14))
    # level-match (active speech RMS)
    for l, c in clips.items():
        db = align.envelope_db(c)
        act = db > np.percentile(db, 95) - 20
        fr = c[: len(db) * align.HOP].reshape(len(db), align.HOP)[act]
        clips[l] = c * (10 ** (-22 / 20) / np.sqrt((fr ** 2).mean() + 1e-12))
    return clips


def build():
    clips = split_lines()
    L = LOCKED["lines"]
    ids = [l for l, _, _ in LINES]
    total = LOCKED["duration"]
    buf = np.zeros(int(total * tts.SR) + tts.SR, np.float32)
    report = []
    prev_end = 0.0
    for k, l in enumerate(ids):
        c = clips[l]
        s_lock, e_lock = L[l]["start"], L[l]["end"]
        nxt = L[ids[k + 1]]["start"] if k + 1 < len(ids) else total - 1.2
        d_new = len(c) / tts.SR
        d_old = e_lock - s_lock
        # room: may start up to 0.12 s early (if the previous line is done) and run into the gap before the next line
        start = s_lock
        room = nxt - 0.06 - start
        ratio = 1.0
        drift = d_new / d_old
        if d_new > room:
            early = min(0.12, max(0.0, s_lock - prev_end - 0.05))
            start -= early
            room += early
        need = max(d_new / room if d_new > room else 1.0, drift if drift > 1 + MAX_FIT else 1.0,
                   drift if drift < 1 - MAX_FIT else 1.0)
        if need != 1.0:
            ratio = float(np.clip(need, 1 - MAX_FIT, 1 + MAX_FIT))
            c = _stretch(c, ratio)
        a = int(start * tts.SR)
        buf[a:a + len(c)] += c[: len(buf) - a]
        end = start + len(c) / tts.SR
        prev_end = end
        report.append((l, d_old, d_new, ratio, start - s_lock, end - nxt))
    tts.write_wav(os.path.join(BUILD, "voice.wav"), buf[: int(total * tts.SR)])
    print(f"{'line':9s} {'old':>5s} {'new':>5s} {'adj':>6s} {'shift':>6s} {'over':>6s}")
    for l, do, dn, r, sh, ov in report:
        flag = "" if (r == 1.0 and ov <= 0) else "  <-" if ov > 0 else "  (fit)"
        print(f"{l:9s} {do:5.2f} {dn:5.2f} {('%+.1f%%' % ((1 / r - 1) * 100)) if r != 1 else '   -':>6s} {sh:6.2f} {ov:6.2f}{flag}")
    n_adj = sum(1 for r in report if r[3] != 1.0)
    print(f"lines time-adjusted: {n_adj}/{len(report)}; max adjustment "
          f"{max(abs(1 / r[3] - 1) for r in report) * 100:.1f}%")
    json.dump([dict(zip(("line", "old", "new", "ratio", "shift", "overrun"), r)) for r in report],
              open(os.path.join(BUILD, "vo_fit.json"), "w"), indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "audition":
        v = sys.argv[2]
        m = sys.argv[3] if len(sys.argv) > 3 else MODEL
        txt = take_text(0, ["hook1", "hook2", "intro", "par", "gp", "ggp", "dbl"])
        p = os.path.join(BUILD, "audition", f"{m}_{v}.wav")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        a = tts.synth(txt, p, m, voice=v, retries=1)
        print(p, round(len(a) / tts.SR, 2))
    elif cmd == "takes":
        record_takes()
    elif cmd == "build":
        build()
