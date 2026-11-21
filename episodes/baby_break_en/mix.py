"""Soundtrack: English narration + the ORIGINAL sound effects, SRT, final mux.

The source has no music bed: just narration and a few effects (rattle shakes, pops, heartbeats,
a happy squeal). The effects are lifted from the source's music+effects stem (Demucs htdemucs_ft
two-stem separation of the source audio, stored in assets/audio/baby_break/sfx_stem.wav), gated to the
effect events only (so no trace of the Turkish voice remains) and placed at the retimed positions.
No new effects, no whooshes.

usage:
  python -m episodes.baby_break_en.mix audio   # build/baby_break_en/mix.wav + output SRT
  python -m episodes.baby_break_en.mix final   # mux -> output/
"""
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

from cinecode import tts
from episodes.baby_break_en import render

ROOT = render.ROOT
BUILD = render.BUILD
OUT = os.path.join(ROOT, "output")
NAME = "Just_Needy_Baby_Turns_Head_Away_EN"
SR = 48000
STEM = os.path.join(ROOT, "assets", "audio", "baby_break", "sfx_stem.wav")
# effect events in the source (original seconds), found by gating the stem at -46 dBFS
EVENTS = [(0.00, 0.40), (2.90, 3.10), (8.05, 9.60), (14.30, 14.85), (23.25, 23.50), (24.45, 24.70),
          (25.35, 25.60), (33.20, 33.50), (33.70, 34.00), (34.20, 34.55), (34.95, 35.30), (36.00, 36.25),
          (38.00, 38.50), (38.90, 39.35), (40.45, 40.70), (42.15, 42.55), (44.25, 45.53)]
VOICE_GAIN_DB = 0.0


def _resample(x, sr_in, sr_out):
    from scipy.signal import resample_poly
    from math import gcd
    g = gcd(sr_in, sr_out)
    return resample_poly(x, sr_out // g, sr_in // g, axis=0).astype(np.float32)


def deess(x, sr, f0=5000.0, over_pct=97, ratio=3.0):
    """Gentle split-band de-esser: only the band above f0 is turned down, and only where it exceeds the
    voice's own 97th-percentile sibilant level (tames a few hot 's' sounds without dulling the voice)."""
    from scipy.signal import butter, sosfiltfilt
    sos = butter(4, f0, "hp", fs=sr, output="sos")
    hi = sosfiltfilt(sos, x)
    lo = x - hi
    n = int(0.008 * sr)
    env = np.sqrt(np.convolve(hi ** 2, np.ones(n) / n, mode="same") + 1e-12)
    db = 20 * np.log10(env)
    thr = np.percentile(db[db > db.max() - 50], over_pct)
    red = np.where(db > thr, (db - thr) * (1 - 1 / ratio), 0.0)
    m = int(0.012 * sr)  # smooth the gain so it never pumps
    red = np.convolve(red, np.hanning(m) / np.hanning(m).sum(), mode="same")
    return (lo + hi * 10 ** (-red / 20)).astype(np.float32)


def _rms_active(x):
    n = len(x) // 1024 * 1024
    fr = x[:n].reshape(-1, 1024)
    r = np.sqrt((fr ** 2).mean(1) + 1e-12)
    act = r > np.percentile(r, 90) * 0.1
    return np.sqrt((r[act] ** 2).mean())


def audio():
    tm = render.timing()
    dur = tm["duration"]
    n = int(round(dur * SR))
    voice = deess(tts.read_wav(os.path.join(BUILD, "voice.wav")), tts.SR)
    voice = _resample(voice, tts.SR, SR)[:n]
    mixbuf = np.zeros((n, 2), np.float32)
    mixbuf[:len(voice)] += voice[:, None] * 10 ** (VOICE_GAIN_DB / 20)
    # effects at the same level relative to the narration as in the source
    stem, sr = sf.read(STEM, dtype="float32")
    stem = _resample(stem, sr, SR)
    vref, vsr = sf.read(os.path.join(ROOT, "assets", "audio", "baby_break", "source_voice_level.wav"), dtype="float32") \
        if os.path.exists(os.path.join(ROOT, "assets", "audio", "baby_break", "source_voice_level.wav")) else (None, None)
    g = 1.0
    if vref is not None:
        g = _rms_active(voice) / _rms_active(vref if vref.ndim == 1 else vref.mean(1))
    fade = int(0.03 * SR)
    for a, b in EVENTS:
        s0, s1 = int(a * SR), min(len(stem), int(b * SR))
        seg = stem[s0:s1].copy()
        if len(seg) < 2 * fade:
            continue
        ramp = np.linspace(0, 1, fade, dtype=np.float32)[:, None]
        seg[:fade] *= ramp
        seg[-fade:] *= ramp[::-1]
        at = int(render.unwarp(a) * SR)
        e = min(n, at + len(seg))
        mixbuf[at:e] += seg[:e - at] * g
    tmp = os.path.join(BUILD, "mix_raw.wav")
    sf.write(tmp, mixbuf, SR, subtype="FLOAT")
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                    f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true,afade=t=out:st={dur - 0.3:.3f}:d=0.3", "-ar", str(SR), out], check=True)
    print(out, f"{dur:.2f}s, sfx gain {20 * np.log10(g):+.1f} dB")
    srt()


def _ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def cues(maxlen=42):
    """Subtitle cues: caption chunks joined up to `maxlen` chars, always breaking after sentence punctuation."""
    out, cur = [], None
    for t0, t1, words, _ in render.captions().chunks:
        txt = " ".join(w for w, _, _ in words)
        if cur and len(cur[2]) + 1 + len(txt) <= maxlen and not cur[2].rstrip('"').endswith((".", "?", "!")):
            cur[1], cur[2] = t1, cur[2] + " " + txt
        else:
            if cur:
                out.append(cur)
            cur = [t0, t1, txt]
    out.append(cur)
    return out


def srt():
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, NAME + ".en.srt")
    with open(p, "w") as f:
        for i, (a, b, txt) in enumerate(cues(), 1):
            f.write(f"{i}\n{_ts(a)} --> {_ts(b)}\n{txt}\n\n")
    print(p)


def final():
    v = os.path.join(BUILD, "video_silent.mp4")
    a = os.path.join(BUILD, "mix.wav")
    out = os.path.join(OUT, NAME + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-shortest", "-movflags", "+faststart", out],
                   check=True)
    print(out)


if __name__ == "__main__":
    {"audio": audio, "final": final, "srt": srt}[sys.argv[1]]()
