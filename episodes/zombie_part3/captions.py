"""Burned-in word-group captions for Part 3, styled after the "How Mine Salting Worked" reference.

Word timing is measured from the actual narration audio (aeneas-style forced alignment): each line is
re-spoken with espeak-ng, both signals are turned into MFCC sequences, DTW maps the synthetic word
boundaries (known exactly) onto the real take, and each onset is snapped to the nearest energy dip.

usage: python -m episodes.zombie_part3.captions            -> build/p3/captions.ass + output/*_CAPTIONED.srt
       python -m episodes.zombie_part3.captions burn       -> output/JUST_NEEDY_ZOMBIE_PART_3_CAPTIONED.mp4
"""
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

import librosa
import numpy as np

from cinecode import align, tts
from episodes.zombie_part3.script import NARRATION, RADIO

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TL = json.load(open(os.path.join(HERE, "timeline.json")))
TTS_DIR = os.path.join(ROOT, "assets", "audio", "tts", "zombie_p3")
BUILD = os.path.join(ROOT, "build", "p3")
OUT = os.path.join(ROOT, "output")
SRC_MP4 = os.path.join(OUT, "JUST_NEEDY_ZOMBIE_PART_3_FINAL.mp4")
CAP_MP4 = os.path.join(OUT, "JUST_NEEDY_ZOMBIE_PART_3_CAPTIONED.mp4")
CAP_SRT = os.path.join(OUT, "JUST_NEEDY_ZOMBIE_PART_3_CAPTIONED.srt")
SR = tts.SR
HOP = 160  # 6.7 ms at 24 kHz


def espeak(text, speed):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        p = f.name
    subprocess.run(["espeak-ng", "-v", "en-us", "-s", str(int(speed)), "-w", p, text], check=True)
    y, sr = librosa.load(p, sr=SR)
    os.remove(p)
    return y


def trim_sil(y, db=35):
    yt, idx = librosa.effects.trim(y, top_db=db)
    return y[idx[0]:idx[1]]


def feats(y):
    m = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=13, hop_length=HOP, n_fft=512)
    m = m[1:]  # drop energy term
    return (m - m.mean(axis=1, keepdims=True)) / (m.std(axis=1, keepdims=True) + 1e-6)


def word_times(y0, text):
    """Return [(word, start, end)] in seconds relative to y0."""
    # crop to the voiced span (the line-level segments carry a little breath/room noise at the head)
    r0 = librosa.feature.rms(y=y0, frame_length=480, hop_length=HOP)[0]
    db0 = 20 * np.log10(r0 / r0.max() + 1e-9)
    vo = np.where(db0 > -28)[0]
    on, off = vo[0] * HOP / SR, min(len(y0) / SR, (vo[-1] + 2) * HOP / SR)
    y = y0[int(on * SR):int(off * SR)]
    res = _word_times(y, text)
    return [(w, a + on, b + on) for w, a, b in res]


def _word_times(y, text):
    words = text.split()
    real_len = len(y) / SR
    # match the synthetic speaking rate to the real line
    speed = 175
    for _ in range(2):
        full = trim_sil(espeak(text, speed))
        speed = np.clip(speed * (len(full) / SR) / max(real_len, 0.3), 80, 450)
    full = trim_sil(espeak(text, speed))
    # synthetic word boundaries from cumulative prefixes
    bounds = [0.0]
    for k in range(1, len(words)):
        pre = trim_sil(espeak(" ".join(words[:k]), speed))
        bounds.append(len(pre) / SR)
    bounds.append(len(full) / SR)
    A, B = feats(full), feats(y)
    D, wp = librosa.sequence.dtw(X=A, Y=B, metric="cosine")
    wp = wp[::-1]
    def map_t(ts):
        f = int(round(ts * SR / HOP))
        js = wp[wp[:, 0] == min(f, A.shape[1] - 1), 1]
        return (js.min() if len(js) else wp[-1, 1]) * HOP / SR
    rt = [map_t(b) for b in bounds[:-1]] + [real_len]
    # snap interior boundaries to the quietest point within +-50 ms
    rms = librosa.feature.rms(y=y, frame_length=480, hop_length=HOP)[0]
    for i in range(1, len(rt) - 1):
        c = int(rt[i] * SR / HOP)
        lo, hi = max(0, c - 8), min(len(rms) - 1, c + 8)
        rt[i] = (lo + int(np.argmin(rms[lo:hi + 1]))) * HOP / SR
    rt[0] = 0.0
    # at punctuation the narrator pauses: put the boundary at the real silence nearest the DTW estimate
    db = 20 * np.log10(rms / rms.max() + 1e-9)
    sil = db < -30
    runs, i = [], 0
    while i < len(sil):
        if sil[i]:
            j = i
            while j < len(sil) and sil[j]:
                j += 1
            if (j - i) * HOP / SR >= 0.07:
                runs.append((i * HOP / SR, j * HOP / SR))
            i = j
        else:
            i += 1
    ends = {}
    for k in range(1, len(words)):
        if re.search(r"[.,:;!?]$", words[k - 1]):
            near = [r for r in runs if abs((r[0] + r[1]) / 2 - rt[k]) < 0.45]
            if near:
                r = max(near, key=lambda r: r[1] - r[0])
                rt[k] = r[1]
                ends[k - 1] = r[0]
    for i in range(1, len(rt)):
        rt[i] = max(rt[i], rt[i - 1] + 0.04)
    for i in range(1, len(rt)):
        rt[i] = max(rt[i], rt[i - 1] + 0.04)
    return [(w, rt[i], rt[i + 1]) for i, w in enumerate(words)]


def all_words():
    take = glob.glob(os.path.join(TTS_DIR, "narration_*.wav"))[0]
    a = tts.read_wav(take)
    segs = align.align(a, [t for _, t in NARRATION])
    out = []
    for (lid, text), (s, e) in zip(NARRATION, segs):
        pad = min(0.05, s)
        y = a[int((s - pad) * SR):int((e + 0.1) * SR)].astype(np.float32)
        place = TL["lines"][lid] - pad  # video time of y[0] (soundtrack places speech onset s at the line start)
        for w, ws, we in word_times(y, text):
            out.append((w, place + ws, place + we, lid))
    # radio whisper (same trim rule as soundtrack.radio_voice)
    p = glob.glob(os.path.join(TTS_DIR, "radio_*.wav"))[0]
    r = tts.read_wav(p)
    pz, db, thr = align.find_pauses(r, 0.05)
    v = np.where(db >= thr)[0]
    s, e = v[0] * align.HOP / SR, (v[-1] + 1) * align.HOP / SR
    pad = min(0.04, s)
    y = r[int((s - pad) * SR):int((e + 0.1) * SR)].astype(np.float32)
    place = TL["lines"]["r01"] - pad
    for w, ws, we in word_times(y, RADIO[1]):
        out.append((w, place + ws, place + we, "r01"))
    return out


def text_w(t):
    """Rendered width (px) of a caption at FONT_SIZE (libass size ~= 0.63 x PIL point size for Montserrat)."""
    from PIL import ImageFont
    f = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", "Montserrat-ExtraBold.ttf"), int(FONT_SIZE * 0.63))
    b = f.getbbox(t)
    return b[2] - b[0] + 2 * OUTLINE


def group(words):
    """1-3 word groups: split each line at punctuation into phrases, then cut every phrase into balanced
    chunks of at most 3 words (4 -> 2+2, 5 -> 3+2) and at most ~16 characters."""
    import math
    groups = []
    lines = []
    for w in words:
        if not lines or lines[-1][-1][3] != w[3]:
            lines.append([])
        lines[-1].append(w)
    for ln in lines:
        phrases, cur = [], []
        for w in ln:
            cur.append(w)
            if re.search(r"[.,:;!?]$", w[0]):
                phrases.append(cur)
                cur = []
        if cur:
            phrases.append(cur)
        for ph in phrases:
            n = len(ph)
            k = math.ceil(n / 3) if len(" ".join(x[0] for x in ph)) <= 9 else math.ceil(n / 2)
            while True:
                sizes = [n // k + (1 if i < n % k else 0) for i in range(k)]
                chunks, i = [], 0
                for sz in sizes:
                    chunks.append(ph[i:i + sz])
                    i += sz
                if all(len(c) == 1 or (text_w(" ".join(x[0] for x in c)) <= 880 and (len(c) <= 2 or len(" ".join(x[0] for x in c)) <= 9)) for c in chunks):
                    break
                k += 1
            groups.extend(chunks)
    caps = []
    for gi, g in enumerate(groups):
        start = g[0][1]
        end = g[-1][2] + 0.12
        if gi + 1 < len(groups):
            ns = groups[gi + 1][0][1]
            # hold until the next group if the gap is short; never overlap
            end = ns if ns - g[-1][2] < 0.6 else min(end + 0.2, ns)
        caps.append([start, end, " ".join(x[0] for x in g)])
    return caps


def ts_ass(x):
    cs = int(round(x * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def ts_srt(x):
    ms = int(round(x * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# Style measured from the reference (480x854 -> scaled to 1080x1920): text block centred at ~70.5% height,
# "magnifying" ~41% of frame width, white bold sans with ~2px (ref) / 5px (1080p) black outline, no box.
FONT_SIZE = 106
OUTLINE = 7
CAP_Y = 1355  # 70.6 % of 1920


def write(caps):
    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat ExtraBold,{FONT_SIZE},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,{OUTLINE},0,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for s, e, t in caps:
        ass += f"Dialogue: 0,{ts_ass(s)},{ts_ass(e)},Cap,,0,0,0,,{{\\pos(540,{CAP_Y})}}{t}\n"
    open(os.path.join(BUILD, "captions.ass"), "w").write(ass)
    with open(CAP_SRT, "w") as f:
        for i, (s, e, t) in enumerate(caps, 1):
            f.write(f"{i}\n{ts_srt(s)} --> {ts_srt(e)}\n{t}\n\n")


def burn():
    fonts = os.path.join(ROOT, "assets", "fonts")
    ass = os.path.join(BUILD, "captions.ass")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning", "-i", SRC_MP4,
                    "-vf", f"subtitles={ass}:fontsdir={fonts}", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "copy", "-movflags", "+faststart", CAP_MP4], check=True)


if __name__ == "__main__":
    if sys.argv[1:] == ["burn"]:
        burn()
    else:
        words = all_words()
        json.dump(words, open(os.path.join(BUILD, "words.json"), "w"), indent=0)
        caps = group(words)
        write(caps)
        # refresh the sentence-level SRT of the uncaptioned master with the measured word times
        from episodes.zombie_part3.script import NARRATION as NAR
        texts = dict(NAR); texts["r01"] = "(radio, whispering) " + RADIO[1]
        order = [l for l, _ in NAR] + ["r01"]
        with open(os.path.join(OUT, "JUST_NEEDY_ZOMBIE_PART_3_FINAL.srt"), "w") as f:
            for i, lid in enumerate(order, 1):
                ws = [w for w in words if w[3] == lid]
                nxt = [w for w in words if w[3] == order[i]][0][1] - 0.02 if i < len(order) else 1e9
                f.write(f"{i}\n{ts_srt(ws[0][1])} --> {ts_srt(min(ws[-1][2] + 0.25, nxt))}\n{texts[lid]}\n\n")
        for c in caps:
            print(f"{c[0]:6.2f} {c[1]:6.2f}  {c[2]}")
