"""Subtle cinematic score, voice/music mix, English SRT, final mux.

usage: python -m episodes.ancestry_en.mix audio      # build/ancestry_en/mix.wav + output SRT
       python -m episodes.ancestry_en.mix final      # mux with build/ancestry_en/video_silent.mp4
"""
import os
import subprocess
import sys

import numpy as np
from scipy import signal

from cinecode import tts
from episodes.ancestry_en.render import CAPS, DUR, BUILD, ROOT, S, E

SR = 48000
OUT_DIR = os.path.join(ROOT, "output")
NAME = "Just_Needy_What_If_Every_Human_Is_Related_EN"


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def adsr(n, a, r):
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na) ** 1.5
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e


def pad_note(m, d, bright=1800):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = midi(m)
    x = np.zeros(n)
    for det, ph in ((-0.07, 0.1), (0.0, 0.7), (0.06, 1.9)):
        ff = f * 2 ** (det / 12)
        # band-limited saw approximation (first harmonics)
        for k in range(1, 9):
            x += np.sin(2 * np.pi * ff * k * t + ph * k) / k * (0.85 ** k)
    b, a = signal.butter(2, min(bright, SR / 2 - 100) / (SR / 2))
    x = signal.lfilter(b, a, x)
    return x * adsr(n, d * 0.35, d * 0.4) * 0.05


def pluck(m, d=1.6):
    n = int(d * SR)
    t = np.arange(n) / SR
    f = midi(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6) + 0.12 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 9)
    return x * np.exp(-t * 2.6) * adsr(n, 0.004, 0.2) * 0.11


def sub(m, d):
    n = int(d * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * midi(m) * t) * adsr(n, 0.08, 0.5) * 0.12


def soft_kick():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 52 + 60 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 0.22


def reverb(x, secs=2.6, mix=0.32):
    n = int(secs * SR)
    rng = np.random.default_rng(1)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / SR * 3.0 / secs * 2.2)
    b, a = signal.butter(1, 5000 / (SR / 2))
    ir = signal.lfilter(b, a, ir)
    ir /= np.sqrt((ir ** 2).sum())
    wet = signal.fftconvolve(x, ir)[: len(x)]
    return x * (1 - mix) + wet * mix * 1.4


def add(buf, x, t):
    i = int(t * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i]


# chord = (bass root, [pad notes])
D = (38, [62, 66, 69, 73])     # Dmaj7
Bm = (35, [59, 62, 66, 69])    # Bm7
G = (31, [59, 62, 67, 71])     # Gmaj7
A = (33, [61, 64, 69, 71])     # Asus-ish
Em = (40, [59, 64, 67, 71])    # Em7
F_ = (42, [61, 64, 66, 69])    # F#m7


def score(total):
    buf = np.zeros(int((total + 4) * SR))
    bpm = 84
    beat = 60 / bpm
    bar = 4 * beat
    sections = [
        (0.0, S("rewind") - 0.2, [D, Bm, G, A], 1.0),
        (S("rewind") - 0.2, S("out") - 0.2, [Bm, G, Em, F_], 0.9),
        (S("out") - 0.2, S("think") - 0.1, [G, A, Bm, A], 1.05),
        (S("think") - 0.1, total + 2, [G, A, D, D], 1.0),
    ]
    kicks = [(S("g30"), E("mix")), (S("out"), E("route"))]
    arp_pat = [0, 2, 1, 3, 2, 1, 3, 2]
    for s0, s1, chords, vol in sections:
        t, ci = s0, 0
        while t < s1:
            root, notes = chords[ci % len(chords)]
            d = min(bar * 2, s1 - t) if s1 - t > bar else bar * 2
            for m in notes:
                add(buf, pad_note(m, d + 1.2) * vol, t)
            add(buf, sub(root + 12, d) * vol, t)
            for k in range(int(d / (beat / 2))):
                tt = t + k * beat / 2
                if tt >= s1:
                    break
                if s0 == sections[1][0] and k % 2:
                    continue  # sparser, more mysterious in the deep-time section
                m = notes[arp_pat[k % 8]] + (12 if k % 4 == 3 else 0)
                v = 0.6 if tt < S("par") else 1.0
                add(buf, pluck(m) * v * vol, tt)
            for k in range(int(d / beat)):
                tt = t + k * beat
                if any(a_ <= tt <= b_ for a_, b_ in kicks) and tt < s1:
                    add(buf, soft_kick(), tt)
            t += d
            ci += 1
    buf = reverb(buf)
    # gentle fade in / out
    n = len(buf)
    fi = int(1.0 * SR)
    buf[:fi] *= np.linspace(0, 1, fi)
    end = int(total * SR)
    buf[end - int(1.6 * SR):end] *= np.linspace(1, 0, int(1.6 * SR))
    buf[end:] = 0
    return buf[: end]


def envelope(x, att=0.03, rel=0.4):
    a = np.exp(-1 / (att * SR))
    r = np.exp(-1 / (rel * SR))
    y = np.abs(x)
    # block-wise approximate follower for speed
    hop = 240
    m = y[: len(y) // hop * hop].reshape(-1, hop).max(axis=1)
    out = np.zeros_like(m)
    v = 0.0
    ah, rh = a ** hop, r ** hop
    for i, s in enumerate(m):
        v = ah * v + (1 - ah) * s if s > v else rh * v + (1 - rh) * s
        out[i] = v
    return np.repeat(out, hop)[: len(x)] if len(out) else np.zeros(len(x))


def polish_voice(x):
    """High-pass, a touch of presence/air, gentle compression and a peak limiter (ffmpeg)."""
    import soundfile as sf
    a = os.path.join(BUILD, "voice_raw48.wav")
    b = os.path.join(BUILD, "voice_polished.wav")
    sf.write(a, x.astype(np.float32), SR)
    chain = ("highpass=f=75,equalizer=f=250:t=q:w=1.0:g=-1.5,equalizer=f=3200:t=q:w=1.2:g=2.5,"
             "highshelf=f=7500:g=2,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=140:makeup=2,"
             "alimiter=limit=0.89:attack=3:release=60:level=disabled")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", chain, "-ar", str(SR), b], check=True)
    y, _ = sf.read(b)
    return y


def build_audio():
    voice24 = tts.read_wav(os.path.join(BUILD, "voice.wav"))
    voice = signal.resample_poly(voice24, 2, 1)
    total = DUR
    n = int(total * SR)
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    voice = polish_voice(voice)
    music = score(total)
    music = np.pad(music, (0, max(0, n - len(music))))[:n]
    music = music / (np.abs(music).max() + 1e-9) * 0.5
    env = envelope(voice)
    env = np.pad(env, (0, n - len(env)))
    duck = 1 - 0.5 * np.clip(env / 0.25, 0, 1)
    mixd = voice + music * 0.30 * duck
    path = os.path.join(BUILD, "mix_raw.wav")
    import soundfile as sf
    sf.write(path, mixd.astype(np.float32), SR)
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000", out], check=True)
    print(out)


def voice_remap():
    """If the narration was replaced on a locked picture, map locked times to where each line is now spoken."""
    import json
    fit = os.path.join(BUILD, "vo_fit.json")
    if not os.path.exists(fit):
        return None
    from episodes.ancestry_en.render import TL
    rows = json.load(open(fit))
    spans = []
    for r in rows:
        s0, e0 = TL[r["line"]]["start"], TL[r["line"]]["end"]
        ns = s0 + r["shift"]
        spans.append((s0, e0, ns, ns + r["new"] / r["ratio"]))

    def f(t, end=False):
        for i, (s0, e0, ns, ne) in enumerate(spans):
            nxt = spans[i + 1][0] if i + 1 < len(spans) else 1e9
            if s0 - 0.3 <= t < nxt - 0.05 or (end and s0 <= t <= nxt):
                if t <= e0:
                    return ns + (t - s0) * (ne - ns) / max(0.01, e0 - s0)
                return ne + (t - e0)
        return t
    return f


def srt():
    def ts(x):
        x = max(0, x)
        h, r = divmod(x, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}".replace(",1000", ",999")
    os.makedirs(OUT_DIR, exist_ok=True)
    cues = CAPS.srt_cues()
    remap = voice_remap()
    if remap:
        cues = [(remap(a), remap(b, end=True), txt) for a, b, txt in cues]
    p = os.path.join(OUT_DIR, NAME + ".en.srt")
    with open(p, "w") as f:
        for i, (a, b, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n\n")
    print(p, len(cues), "cues")


def final():
    v = os.path.join(BUILD, "video_silent.mp4")
    a = os.path.join(BUILD, "mix.wav")
    out = os.path.join(OUT_DIR, NAME + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "libx264",
                    "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    print(out)


def final_locked(picture):
    """Swap the soundtrack only: the video stream of `picture` is copied untouched (no re-encode)."""
    a = os.path.join(BUILD, "mix.wav")
    out = os.path.join(OUT_DIR, NAME + ".mp4")
    tmp = out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", picture, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", tmp], check=True)
    os.replace(tmp, out)
    print(out)


if __name__ == "__main__":
    if sys.argv[1] == "audio":
        build_audio()
        srt()
    elif sys.argv[1] == "final":
        final()
    elif sys.argv[1] == "relock":
        final_locked(sys.argv[2])
