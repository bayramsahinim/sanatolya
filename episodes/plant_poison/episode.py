"""Assemble the English adaptation.

    python -m episodes.plant_poison.episode CLEAN_VIDEO OUT_DIR

CLEAN_VIDEO is the Turkish source with its captions removed (tools: episodes/plant_poison/
decaption.py). Each English line is placed at the start of the scene/caption block it
replaces; if an English line needs more room than the Turkish one had, that stretch of the
video is slowed slightly so picture and narration stay in sync.
"""
import json
import os
import re
import subprocess
import sys

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import resample_poly

from episodes.plant_poison import music
from episodes.plant_poison.script import CAPS, LINES
from episodes.plant_poison.voice import SR as VSR, clips, words_timing

W, H, FPS = 1080, 1920, 24
SR = 48000
LEAD = 0.10        # speech starts this long after its scene block begins
TAIL = 0.22        # minimum breathing room after a line
FONT = "assets/fonts/Montserrat-ExtraBold.ttf"
CAP_SIZE = 76
CAP_STROKE = 8
CAP_Y = int(H * 0.70)
NAME = "JUST_NEEDY_PLANT_POISON_ENGLISH"


# ------------------------------------------------------------------ timing plan
def plan():
    """Map each English line onto its source scene block. A block whose line would need the
    video slowed by >12% is merged with the next block so the slowdown is spread thinner."""
    xs = clips()
    durs = [len(x) / VSR for x in xs]
    units, i = [], 0
    while i < len(LINES):
        lead = 0.15 if i == 0 else LEAD
        need = lead + durs[i] + TAIL
        a, b = LINES[i][2], LINES[i][3]
        if need / (b - a) > 1.12 and i + 1 < len(LINES):
            units.append([i, i + 1]); i += 2
        else:
            units.append([i]); i += 1
    segs, t = [], 0.0
    for u in units:
        a, b = LINES[u[0]][2], LINES[u[-1]][3]
        lead = 0.15 if u[0] == 0 else LEAD
        need = lead + sum(durs[k] for k in u) + 0.30 * (len(u) - 1) + TAIL
        d = max(b - a, need)
        rate = (b - a) / d
        cur = t + lead
        for k in u:
            nat = t + (LINES[k][2] - a) / rate + lead
            st = max(cur, nat) if k != u[0] else t + lead
            en = st + durs[k]
            words = [(w, st + w0, st + w1) for w, w0, w1 in words_timing(xs[k], LINES[k][0])]
            segs.append(dict(i=k, text=LINES[k][0], src=(a, b), out=(t, t + d), speech=(st, en),
                             clip=xs[k], words=words, rate=rate))
            cur = en + 0.30
        t += d
    return segs


def src_time(segs, T):
    for s in segs:
        o0, o1 = s["out"]
        if T < o1 or s is segs[-1]:  # (merged lines share one mapping)
            a, b = s["src"]
            return min(b, a + (T - o0) * s["rate"])


# ------------------------------------------------------------------ captions
def groups(seg):
    """Caption groups for one line, from the hand-authored CAPS breaks."""
    sizes = [len(g.split()) for g in CAPS[seg["i"]].split(" | ")]
    out, k = [], 0
    for n in sizes:
        out.append(seg["words"][k:k + n])
        k += n
    return out


def clean_word(w):
    w = w.replace("…", "...")
    w = re.sub(r"^\.\.\.", "", w)
    return w


def cues(segs):
    cs = []
    for k, s in enumerate(segs):
        gs = groups(s)
        nxt_line = segs[k + 1]["speech"][0] if k + 1 < len(segs) else s["out"][1] + 1
        for j, g in enumerate(gs):
            t0 = g[0][1] - 0.04
            if j + 1 < len(gs):
                t1 = gs[j + 1][0][1] - 0.04
            else:
                t1 = min(g[-1][2] + 0.30, nxt_line - 0.08)
            cs.append(dict(text=" ".join(clean_word(w) for w, _, _ in g), t0=t0, t1=t1))
    return cs


_font = None


def cap_img(text):
    global _font
    if _font is None:
        _font = ImageFont.truetype(FONT, CAP_SIZE)
    pad = CAP_STROKE + 6
    box = _font.getbbox(text, stroke_width=CAP_STROKE)
    w, h = box[2] - box[0] + 2 * pad, box[3] - box[1] + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad - box[0], pad - box[1]), text, font=_font, fill=(255, 255, 255, 255),
           stroke_width=CAP_STROKE, stroke_fill=(0, 0, 0, 255))
    a = np.asarray(im).astype(np.float32) / 255.0
    # vertical anchor: centre on the x-height band so groups with/without descenders don't jump
    asc = _font.getbbox("x")[1]
    return a, w, h, pad - box[1] + (asc + _font.getbbox("x")[3]) / 2


def composite(frame, cap):
    a, w, h, cy = cap
    x0 = (W - w) // 2
    y0 = int(CAP_Y - cy)
    roi = frame[y0:y0 + h, x0:x0 + w].astype(np.float32)
    al = a[..., 3:4]
    rgb = a[..., [2, 1, 0]] * 255  # PIL RGBA -> BGR
    frame[y0:y0 + h, x0:x0 + w] = (rgb * al + roi * (1 - al)).astype(np.uint8)


# ------------------------------------------------------------------ audio
def narration_track(segs, dur):
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    for s in segs:
        x = resample_poly(s["clip"], SR, VSR).astype(np.float32)
        i0 = int(s["speech"][0] * SR)
        e = min(n, i0 + len(x))
        out[i0:e] += x[: e - i0]
    return out


def mix(segs, dur):
    vo = narration_track(segs, dur)
    vo = vo / (np.max(np.abs(vo)) + 1e-9) * 0.89
    bed = music.render(dur)
    # duck the bed under speech (smooth sidechain envelope)
    n = len(vo)
    act = np.zeros(n, np.float32)
    for s in segs:
        a, b = s["speech"]
        act[int(a * SR): int(b * SR)] = 1
    k = int(0.35 * SR)
    act = np.convolve(act, np.ones(k) / k, mode="same")
    gain = 0.20 - 0.09 * np.clip(act, 0, 1)  # ~-14 dB under voice, ~-20 dB in speech
    m = vo + bed[:n] * gain
    return m, vo, bed[:n] * gain


# ------------------------------------------------------------------ main
def main(clean_video, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs("build", exist_ok=True)
    segs = plan()
    dur = segs[-1]["out"][1] + 0.4
    for s in segs:
        print(f"{s['out'][0]:6.2f}-{s['out'][1]:6.2f} src {s['src'][0]:5.2f}-{s['src'][1]:5.2f} "
              f"slow x{1 / s['rate']:.2f}  {s['text']}")
    print("duration", round(dur, 2))

    # audio
    m, vo, bed = mix(segs, dur)
    sf.write("build/plant_poison_mix_raw.wav", m, SR, subtype="FLOAT")
    sf.write("build/plant_poison_vo.wav", vo, SR)

    # captions + SRT
    cs = cues(segs)
    json.dump(dict(cues=cs, lines=[dict(text=s["text"], speech=s["speech"], out=s["out"], src=s["src"])
                                   for s in segs]), open("build/plant_poison_timing.json", "w"), indent=1)
    write_srt(segs, os.path.join(out_dir, NAME + ".srt"))

    # video
    cap = cv2.VideoCapture(clean_video)
    src = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        src.append(f)
    sfps = 24.0
    tmp = "build/plant_poison_video.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                          "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    cache = {}
    nfr = int(round(dur * FPS))
    for k in range(nfr):
        T = k / FPS
        st = src_time(segs, T)
        idx = min(len(src) - 1, int(st * sfps + 1e-6))
        if idx not in cache:
            cache.clear()
            cache[idx] = cv2.resize(src[idx], (W, H), interpolation=cv2.INTER_LANCZOS4)
        fr = cache[idx].copy()
        for c in cs:
            if c["t0"] <= T < c["t1"]:
                composite(fr, cap_cached(c["text"]))
                break
        p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()

    # loudness-normalise and mux
    final = os.path.join(out_dir, NAME + ".mp4")
    # gentle bus compression + peak limiting so the -14 LUFS target isn't peak-bound
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "build/plant_poison_mix_raw.wav", "-af",
                    "acompressor=threshold=-20dB:ratio=3:attack=4:release=120:makeup=4dB,"
                    "alimiter=limit=0.6:attack=2:release=40:level=false",
                    "-c:a", "pcm_f32le", "build/plant_poison_mix_comp.wav"], check=True)
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", "build/plant_poison_mix_comp.wav", "-af",
                           "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    j = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    gain = -13.1 - float(j["input_i"])  # limiter shaves ~1 dB -> lands near -14 LUFS
    ln = f"volume={gain:.2f}dB,alimiter=limit={10 ** (-2.6 / 20):.4f}:attack=1:release=50:level=false"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-i", "build/plant_poison_mix_comp.wav",
                    "-filter_complex", f"[1:a]{ln},aresample=48000[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", final], check=True)
    print("wrote", final)


_caps = {}


def cap_cached(t):
    if t not in _caps:
        _caps[t] = cap_img(t)
    return _caps[t]


def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(segs, path):
    out = []
    for k, s in enumerate(segs):
        a, b = s["speech"]
        nxt = segs[k + 1]["speech"][0] if k + 1 < len(segs) else b + 1
        t1 = min(b + 0.35, nxt - 0.05)
        text = s["text"].replace("…", "...")
        if len(text) > 42:  # two balanced lines
            words = text.split()
            best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
            text = " ".join(words[:best]) + "\n" + " ".join(words[best:])
        out.append(f"{k + 1}\n{fmt(a)} --> {fmt(t1)}\n{text}\n")
    open(path, "w", encoding="utf-8").write("\n".join(out))


if __name__ == "__main__":
    main(*sys.argv[1:3])
