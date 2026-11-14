"""Assemble THE BUTTON (English): timeline, narration, score, SFX, captions, final render.

usage: python -m episodes.the_button_en.build plan|audio|video|all
Source paths come from env: BUTTON_SRC (original mp4), BUTTON_CLEAN (caption-free mp4), BUTTON_WORK (temp dir).
"""
import json
import os
import re
import subprocess
import sys

import cv2
import librosa
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

from cinecode import align as A
from cinecode import audio as AU
from episodes.the_button_en.make_voice import OUT as TTS_DIR
from episodes.the_button_en.script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("BUTTON_SRC", "")
CLEAN = os.environ.get("BUTTON_CLEAN", "")
WORK = os.environ.get("BUTTON_WORK", "/tmp/button_work")
OUTDIR = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_THE_BUTTON_ENGLISH"

FPS = 30
SRC_DUR = 4176 / FPS            # 139.2 s of picture
SR = 48000
TEMPO = 1.05                    # gentle tightening of the English read (medium-fast, still natural)
GAP_MIN = 0.16                  # minimum silence between two English lines
TAIL_MIN = 0.12                 # room after a line before the next shot's line starts
W, H = 1080, 1920

FONT = os.path.join(ROOT, "assets", "fonts", "Montserrat-ExtraBold.ttf")
CAP_SIZE = 84                   # px at 1080x1920
CAP_STROKE = 9                  # thick clean black outline
CAP_Y = 1580                    # caption centre line: bottom-centre, below the action, above platform UI
CAP_MAXW = 900

# Sound events in SOURCE time (seconds), checked against the source frames.
SFX_EVENTS = [
    (19.95, "thud_soft"),      # package at the door
    (30.2, "clock"),           # 8 p.m. clock shot (ticks)
    (35.2, "key"),             # key placed on the table
    (50.3, "tear"),            # card torn up
    (56.3, "dial"),            # Norma calls Steward
    (63.3, "thud_soft"),       # package appears again
    (88.7, "click"),           # button pressed
    (94.0, "bin"),             # box thrown in the trash
    (95.8, "ring"),            # hospital call
    (99.9, "train"),           # train arrives
    (113.8, "break"),          # box broken open
    (118.3, "ring"),           # phone rings again
]


# ---------------------------------------------------------------------------
# timeline
# ---------------------------------------------------------------------------
def tr_segments():
    return json.load(open(os.path.join(HERE, "tr_segments.json")))


def line_audio(k):
    """English line k at 48 kHz after the tempo adjustment (cached)."""
    os.makedirs(os.path.join(WORK, "lines48"), exist_ok=True)
    p = os.path.join(WORK, "lines48", f"{k:02d}.wav")
    if not os.path.exists(p):
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", os.path.join(TTS_DIR, "lines", f"{k:02d}.wav"),
                        "-af", f"atempo={TEMPO},aresample={SR}", "-ac", "1", p], check=True)
    a, _ = sf.read(p, dtype="float32")
    return a


def motion_profile():
    """Per-frame motion of the source picture (caption band excluded), used to pick hold frames."""
    p = os.path.join(WORK, "motion.npy")
    if os.path.exists(p):
        return np.load(p)
    cap = cv2.VideoCapture(SRC)
    prev, out = None, []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(f, (90, 160)), cv2.COLOR_BGR2GRAY).astype(np.float32)
        g[20:37] = 0                      # caption band
        out.append(0.0 if prev is None else float(np.abs(g - prev).mean()))
        prev = g
    m = np.array(out)
    np.save(p, m)
    return m


def plan():
    """Map every source segment (one per Turkish sentence) to output time, inserting holds where the
    English line needs more room. Returns dict with segments and line placements."""
    tr = tr_segments()
    n = len(LINES)
    bounds = [0.0] + [tr[i]["start"] - 0.05 for i in range(1, n)] + [SRC_DUR]
    motion = motion_profile()
    segs, lines = [], []
    out_t = 0.0
    prev_end = -1.0
    for i in range(n):
        b0, b1 = bounds[i], bounds[i + 1]
        L = b1 - b0
        d = len(line_audio(i)) / SR
        onset = tr[i]["start"] - b0                      # where the Turkish line starts within its shot
        start = max(out_t + onset, prev_end + GAP_MIN)
        tail = TAIL_MIN if i < n - 1 else (SRC_DUR - tr[-1]["end"])   # keep the original closing hold
        need = (start - out_t) + d + tail
        ext = max(0.0, need - L)
        ext = round(ext * FPS) / FPS
        # hold on the stillest frame of the shot (never inside a transition)
        f0, f1 = int(b0 * FPS) + 4, int(b1 * FPS) - 4
        hold_f = f0 + int(np.argmin(motion[f0:f1])) if f1 > f0 else int(b0 * FPS)
        segs.append({"i": i, "src0": b0, "src1": b1, "out0": out_t, "ext": ext, "hold_frame": hold_f})
        lines.append({"i": i, "start": start, "end": start + d, "text": LINES[i][1]})
        prev_end = start + d
        out_t += L + ext
    return {"segments": segs, "lines": lines, "duration": out_t}


def src2out(P, t):
    for s in P["segments"]:
        if s["src0"] <= t < s["src1"] or s is P["segments"][-1]:
            local = t - s["src0"]
            hold_t = s["hold_frame"] / FPS - s["src0"]
            return s["out0"] + local + (s["ext"] if local > hold_t else 0.0)


def frame_map(P):
    """Output frame -> source frame index."""
    idx = []
    for s in P["segments"]:
        f0, f1 = int(round(s["src0"] * FPS)), int(round(s["src1"] * FPS))
        for f in range(f0, f1):
            idx.append(f)
            if f == s["hold_frame"]:
                idx += [f] * int(round(s["ext"] * FPS))
    return idx


# ---------------------------------------------------------------------------
# captions
# ---------------------------------------------------------------------------
DISPLAY = [  # spoken words -> how they read on screen (one caption unit)
    (["fifty", "thousand", "dollars."], "$50,000."),
    (["fifty", "thousand", "dollars"], "$50,000"),
    (["twenty-five-thousand-dollar"], "$25,000"),
    (["eight", "p.m."], "8 p.m."),
    (['"Button,', 'Button,"'], '"Button, Button,"'),
]


def syl(w):
    w = re.sub(r"[^a-z']", "", w.lower().replace("-", " "))
    if not w:
        return 1
    v = len(re.findall(r"[aeiouy]+", w))
    if w.endswith("e") and v > 1 and not w.endswith("le"):
        v -= 1
    return max(1, v)


def word_times(k, a):
    """Estimate per-word (start, end) inside the line clip: syllable weights spread over voiced time,
    with sentence/comma breaks snapped to the real pauses in the take."""
    words = LINES[k][1].split()
    y = librosa.resample(a, orig_sr=SR, target_sr=24000)
    pauses, db, thr = A.find_pauses(y, min_len=0.07)
    vo = np.where(db >= thr)[0]
    t0, t1 = vo[0] * A.HOP / 24000, (vo[-1] + 1) * A.HOP / 24000
    pauses = [(p0, p1) for p0, p1 in pauses if p0 > t0 + 0.05 and p1 < t1 - 0.05]
    voiced = []
    s = t0
    for p0, p1 in pauses:
        voiced.append((s, p0))
        s = p1
    voiced.append((s, t1))
    V = sum(b - a_ for a_, b in voiced)
    wts = np.array([syl(w) + 0.35 for w in words], float)
    cum = np.concatenate([[0], np.cumsum(wts)]) / wts.sum() * V

    def at(v):
        for a_, b in voiced:
            if v <= b - a_ + 1e-9:
                return a_ + v
            v -= b - a_
        return t1

    st = [at(c) for c in cum[:-1]]
    en = [at(c) for c in cum[1:]]
    # snap: a word after punctuation starts at the end of the nearest pause
    for j in range(1, len(words)):
        if re.search(r"[,.:;?!\"]$", words[j - 1]):
            best = min(pauses, key=lambda p: abs(p[1] - st[j]), default=None)
            if best and abs(best[1] - st[j]) < 0.45:
                st[j] = best[1]
                en[j - 1] = best[0]
    for j in range(1, len(words)):
        st[j] = max(st[j], st[j - 1] + 0.05)
    return list(zip(words, st, en))


def _absolute(P):
    """Caption groups of 1-3 words in absolute output time, line by line."""
    out = []
    for ln in P["lines"]:
        k = ln["i"]
        wt = word_times(k, line_audio(k))
        units, j = [], 0
        while j < len(wt):
            for spoken, shown in DISPLAY:
                if [w for w, _, _ in wt[j:j + len(spoken)]] == spoken:
                    units.append((shown, wt[j][1], wt[j + len(spoken) - 1][2]))
                    j += len(spoken)
                    break
            else:
                units.append(wt[j])
                j += 1
        gs = group_units(units)
        for gi, g in enumerate(gs):
            s = ln["start"] + g[0][1] - 0.04
            e = ln["start"] + (gs[gi + 1][0][1] - 0.04 if gi + 1 < len(gs) else g[-1][2] + 0.22)
            out.append({"line": k, "start": round(s, 3), "end": round(e, 3),
                        "text": " ".join(x[0] for x in g)})
    # never overlap
    for a_, b in zip(out, out[1:]):
        a_["end"] = min(a_["end"], b["start"])
    return out


FUNC = set("a an the of in on at to for by with and or but if who that this its it's their her his "
           "is are was will won't you you'll they they'll she he there's what not".split())
ABBR = {"Mr.", "p.m.", "8 p.m."}


def _ends_clause(w):
    return w not in ABBR and re.search(r"[,.:;?!]\"?$", w) is not None


def group_units(units):
    """Split a line into 1-3 word caption groups (<= 15 chars) along natural phrase breaks (DP)."""
    words = [u[0] for u in units]
    n = len(words)
    best = [0.0] + [1e9] * n
    back = [0] * (n + 1)
    for j in range(1, n + 1):
        for size in (1, 2, 3):
            i = j - size
            if i < 0:
                continue
            g = words[i:j]
            text = " ".join(g)
            if len(text) > 15 and size > 1:
                continue
            if any(_ends_clause(w) for w in g[:-1]):
                continue                                  # never run across punctuation
            c = 1.0 + 0.35 * abs(size - 2)
            last = re.sub(r"[^\w']", "", g[-1]).lower()
            if j < n and last in FUNC and not _ends_clause(g[-1]):
                c += 1.6                                  # don't end a caption on "the", "will", ...
            if size == 1 and last in FUNC:
                c += 1.0
            if j < n and _ends_clause(g[-1]):
                c -= 0.3
            if best[i] + c < best[j]:
                best[j], back[j] = best[i] + c, i
    out, j = [], n
    while j > 0:
        out.append(units[back[j]:j])
        j = back[j]
    return out[::-1]


_font = None


def render_caption(text):
    global _font
    if _font is None:
        _font = ImageFont.truetype(FONT, CAP_SIZE)
    size = CAP_SIZE
    font = _font
    while font.getlength(text) > CAP_MAXW:
        size -= 4
        font = ImageFont.truetype(FONT, size)
    pad = CAP_STROKE + 12
    w = int(font.getlength(text)) + 2 * pad
    asc, desc = font.getmetrics()
    h = asc + desc + 2 * pad
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((pad, pad), text, font=font, fill=(255, 255, 255, 255), stroke_width=CAP_STROKE,
           stroke_fill=(0, 0, 0, 255))
    arr = np.array(im).astype(np.float32) / 255.0
    return arr, asc


# ---------------------------------------------------------------------------
# audio: narration, score, sfx
# ---------------------------------------------------------------------------
def tone(f, d, partials=((1, 1.0),), decay=1.5):
    t = np.arange(int(d * SR)) / SR
    x = sum(a * np.sin(2 * np.pi * f * m * t) * np.exp(-t * decay * (1 + 0.6 * m)) for m, a in partials)
    att = min(len(x), int(0.006 * SR))
    x[:att] *= np.linspace(0, 1, att)
    return x


def piano(f, d=3.5):
    return tone(f, d, ((1, 1.0), (2, 0.45), (3, 0.18), (4, 0.08)), decay=0.9)


def score(P, dur):
    """Restrained suspense underscore: low drone + sparse minor piano + pulse that tightens near the end."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(7)
    # drone: D minor root + fifth, slowly breathing, lowpassed
    drone = np.zeros(n)
    for f, a in ((36.71, 0.5), (73.42, 0.35), (110.0, 0.18), (146.83, 0.08)):
        ph = rng.random() * 6.28
        drone += a * np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.07 * t + ph))
        drone += a * 0.6 * np.sin(2 * np.pi * f * 1.004 * t + ph)
    pad_noise = AU.lp(rng.standard_normal(n), 400) * 0.05
    drone = AU.lp(drone + pad_noise, 600)
    drone *= 0.75 + 0.25 * np.sin(2 * np.pi * t / 11.0)
    out = drone * 0.22

    # piano motif (D minor: D F A, with a cold Bb/C# colour), sparse
    beats = {
        "intro": (0.0, src2out(P, 10.3), [293.66, 349.23, 440.0, 277.18], 2.6),
        "story": (src2out(P, 10.3), src2out(P, 87.0), [293.66, 349.23, 440.0, 466.16, 349.23, 293.66], 3.2),
        "tension": (src2out(P, 87.0), src2out(P, 103.2), [293.66, 277.18, 233.08], 2.4),
        "aftermath": (src2out(P, 103.2), src2out(P, 118.0), [220.0, 233.08, 293.66], 3.0),
        "reveal": (src2out(P, 118.0), dur - 2.0, [293.66, 277.18, 220.0, 207.65], 2.8),
    }
    for _, (a_, b, notes, step) in beats.items():
        k = 0
        tt = a_ + 0.4
        while tt < b - 1.0:
            note = piano(notes[k % len(notes)] / 2, 4.0) * (0.11 if k % 4 else 0.14)
            s = int(tt * SR)
            out[s:s + len(note)] += note[: max(0, n - s)]
            k += 1
            tt += step
    # silence the piano for "Nothing happens." -> only the drone (the beat lands on the empty room)
    # heartbeat pulse from the hospital call to the end, getting slightly louder
    hb = AU.sfx_heartbeat() if hasattr(AU, "sfx_heartbeat") else None
    if hb is not None:
        hb = librosa.resample(hb.astype(np.float32), orig_sr=AU.SR, target_sr=SR) if AU.SR != SR else hb
        tt = src2out(P, 95.0)
        endt = dur - 3.0
        while tt < endt:
            prog = (tt - src2out(P, 95.0)) / max(1, endt - src2out(P, 95.0))
            s = int(tt * SR)
            out[s:s + len(hb)] += hb[: max(0, n - s)] * (0.10 + 0.08 * prog)
            tt += 1.25 - 0.25 * prog
    # low swell under the final line, then a cold sustained low D to the end
    fin0 = src2out(P, 128.5)
    s = int(fin0 * SR)
    swell = np.zeros(n - s)
    ts = np.arange(len(swell)) / SR
    swell += (np.sin(2 * np.pi * 73.42 * ts) + 0.5 * np.sin(2 * np.pi * 146.83 * ts)
              + 0.25 * np.sin(2 * np.pi * 174.61 * ts))
    swell *= np.clip(ts / 4.0, 0, 1) * 0.08
    out[s:] += AU.lp(swell, 800)
    # fades
    fi, fo = int(1.2 * SR), int(2.5 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    out[-fo:] *= np.linspace(1, 0, fo)
    return out


def sfx(name):
    rs = (lambda x: librosa.resample(np.asarray(x, np.float32), orig_sr=AU.SR, target_sr=SR)) \
        if AU.SR != SR else (lambda x: np.asarray(x, np.float32))
    rng = np.random.default_rng(abs(hash(name)) % 1000)
    if name == "thud_soft":
        return rs(AU.sfx_thud(80, 0.4)) * 0.35
    if name == "key":
        x = sum(tone(f, 0.35, ((1, 1),), decay=9) for f in (2100, 3170, 4320)) * 0.12
        return x
    if name == "tear":
        d = 0.55
        tt = np.arange(int(d * SR)) / SR
        x = AU.bp(rng.standard_normal(len(tt)), 1200, 6000) * (rng.random(len(tt)) > 0.6)
        return x * np.sin(np.pi * tt / d) * 0.25
    if name == "dial":
        x = np.zeros(int(1.6 * SR))
        for k in range(6):
            c = rs(AU.sfx_click()) * 0.25
            s = int((0.1 + k * 0.24) * SR)
            x[s:s + len(c)] += c[: len(x) - s]
        return x
    if name == "click":
        a, b = rs(AU.sfx_click()) * 0.55, rs(AU.sfx_thud(110, 0.15)) * 0.25
        x = np.zeros(max(len(a), len(b)))
        x[:len(a)] += a
        x[:len(b)] += b
        return x
    if name == "bin":
        return rs(AU.sfx_clank()) * 0.22
    if name == "ring":
        d = 1.6
        tt = np.arange(int(d * SR)) / SR
        bell = (np.sin(2 * np.pi * 980 * tt) + 0.6 * np.sin(2 * np.pi * 1310 * tt)) \
            * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * tt)))
        env = np.ones_like(tt)
        env[int(0.05 * SR):] *= 1
        env *= np.minimum(1, tt / 0.01) * np.minimum(1, (d - tt) / 0.08)
        one = AU.lp(bell * env, 4000) * 0.07
        return np.concatenate([one, np.zeros(int(0.5 * SR)), one])
    if name == "train":
        d = 2.6
        tt = np.arange(int(d * SR)) / SR
        x = AU.lp(rng.standard_normal(len(tt)), 900) * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 2
        return x * 0.35
    if name == "break":
        return rs(AU.sfx_crash_wood()) * 0.4
    if name == "clock":
        x = np.zeros(int(3.0 * SR))
        for k in range(3):
            c = tone(3200, 0.05, ((1, 1),), decay=60) * 0.08 + tone(1600, 0.05, ((1, 1),), decay=60) * 0.05
            s = int(k * 1.0 * SR)
            x[s:s + len(c)] += c
        return x
    raise KeyError(name)


def mix(P):
    dur = P["duration"]
    n = int(dur * SR) + SR
    voice = np.zeros(n)
    for ln in P["lines"]:
        a = line_audio(ln["i"])
        s = int(ln["start"] * SR)
        voice[s:s + len(a)] += a
    # loudness-match the voice: peak normalise then gentle compression via soft clip
    voice = voice / (np.percentile(np.abs(voice[voice != 0]), 99.9) + 1e-9) * 0.82
    mus = score(P, n / SR)
    # duck the music under narration (smooth envelope)
    env = np.abs(voice)
    k = int(0.25 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    duck = 1.0 - 0.45 * np.clip(env / 0.05, 0, 1)
    fx = np.zeros(n)
    for t, name in SFX_EVENTS:
        x = sfx(name)
        s = int(src2out(P, t) * SR)
        fx[s:s + len(x)] += x[: max(0, n - s)]
    master = voice + mus * duck * 0.2 + fx * 0.45
    master = np.tanh(master * 1.05) / np.tanh(1.05)
    master = master[: int(dur * SR)]
    os.makedirs(WORK, exist_ok=True)
    sf.write(os.path.join(WORK, "mix.wav"), master.astype(np.float32), SR)
    sf.write(os.path.join(WORK, "voice.wav"), voice[: int(dur * SR)].astype(np.float32), SR)
    # loudness normalise to -14 LUFS for platforms
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", os.path.join(WORK, "mix.wav"), "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", str(SR), os.path.join(WORK, "mix_norm.wav")], check=True)


# ---------------------------------------------------------------------------
# subtitles (.srt): phrase-level cues timed to the voice
# ---------------------------------------------------------------------------
def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(P, caps):
    """Phrase-level cues: one clause per cue (split at punctuation), long clauses split near the middle."""
    cues = []
    for ln in P["lines"]:
        gs = [c for c in caps if c["line"] == ln["i"]]
        clauses, cur = [], []
        for c in gs:
            cur.append(c)
            if _ends_clause(c["text"].split()[-1]):
                clauses.append(cur)
                cur = []
        if cur:
            clauses.append(cur)
        merged = []
        for cl in clauses:          # glue very short clauses to the previous one
            if merged and len(" ".join(x["text"] for x in merged[-1] + cl)) <= 42 and \
                    len(" ".join(x["text"] for x in cl)) < 16:
                merged[-1] = merged[-1] + cl
            else:
                merged.append(cl)
        for cl in merged:
            parts = [cl]
            if len(" ".join(x["text"] for x in cl)) > 42 and len(cl) > 1:
                tot = len(" ".join(x["text"] for x in cl))
                acc, cut = 0, 1
                for j, x in enumerate(cl[:-1]):
                    acc += len(x["text"]) + 1
                    if acc >= tot / 2:
                        cut = j + 1
                        break
                parts = [cl[:cut], cl[cut:]]
            for p_ in parts:
                cues.append((p_[0]["start"], p_[-1]["end"], " ".join(x["text"] for x in p_)))
    with open(os.path.join(OUTDIR, NAME + ".srt"), "w") as f:
        for k, (s_, e, t) in enumerate(cues, 1):
            f.write(f"{k}\n{srt_time(s_)} --> {srt_time(e)}\n{t}\n\n")


# ---------------------------------------------------------------------------
# video
# ---------------------------------------------------------------------------
def render(P, caps, out_path):
    fmap = frame_map(P)
    nout = len(fmap)
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", CLEAN, "-vf",
                            f"scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", os.path.join(WORK, "mix_norm.wav"),
                            "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                            "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k",
                            "-movflags", "+faststart", "-shortest", out_path], stdin=subprocess.PIPE)
    sz = W * H * 3
    cur_src, frame = -1, None
    cache = {}
    ci = 0
    for of in range(nout):
        want = fmap[of]
        while cur_src < want:
            buf = dec.stdout.read(sz)
            if len(buf) < sz:
                break
            frame = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
            cur_src += 1
        img = frame.astype(np.float32)
        t = of / FPS
        while ci < len(caps) and caps[ci]["end"] <= t:
            ci += 1
        if ci < len(caps) and caps[ci]["start"] <= t < caps[ci]["end"]:
            c = caps[ci]
            if c["text"] not in cache:
                cache[c["text"]] = render_caption(c["text"])
            arr, asc = cache[c["text"]]
            age = t - c["start"]
            alpha_mul = min(1.0, age / 0.05 + 0.35)          # 2-frame soft pop-in, no bounce
            h_, w_ = arr.shape[:2]
            x0 = (W - w_) // 2
            y0 = CAP_Y - h_ // 2
            a_ = arr[..., 3:4] * alpha_mul
            reg = img[y0:y0 + h_, x0:x0 + w_]
            img[y0:y0 + h_, x0:x0 + w_] = reg * (1 - a_) + arr[..., :3] * 255 * a_
        enc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    dec.stdout.close()
    dec.wait()


def main(what):
    os.makedirs(WORK, exist_ok=True)
    P = plan()
    caps = _absolute(P)
    json.dump({"plan": P, "captions": caps}, open(os.path.join(HERE, "timeline.json"), "w"), indent=1)
    print(f"duration {P['duration']:.2f}s, holds {sum(s['ext'] for s in P['segments']):.2f}s, "
          f"{len(caps)} caption groups")
    if what in ("audio", "all"):
        mix(P)
        os.makedirs(OUTDIR, exist_ok=True)
        write_srt(P, caps)
    if what in ("video", "all"):
        render(P, caps, os.path.join(OUTDIR, NAME + ".mp4"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "plan")
