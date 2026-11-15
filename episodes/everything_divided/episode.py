"""Assemble "What If We Divided Everything on Earth?" (English, 9:16, 30 fps).

usage:
  python -m episodes.everything_divided.voice           # align + tighten the narration (timing.json)
  python -m episodes.everything_divided.episode audio   # sound design + mix + SRT
  python -m episodes.everything_divided.episode video   # render frames + mux final MP4
"""
import json
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np

from cinecode import audio as A
from episodes.everything_divided import common as C

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "everything")
OUT = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_EVERYTHING_DIVIDED_ENGLISH"
SR = A.SR


# ------------------------------------------------------------------ custom sound effects
def _t(d):
    return np.arange(int(d * SR)) / SR


def sfx_cake_slice(seed=0):
    """Knife through soft sponge: short airy swish into a soft muffled 'thk'."""
    d = 0.32
    t = _t(d)
    sw = A.bp(A.noise(d, 300 + seed), 1500, 7000) * np.exp(-((t - 0.06) / 0.04) ** 2) * 0.5
    squish = A.lp(A.noise(d, 400 + seed), 900) * np.exp(-np.maximum(0, t - 0.08) * 28) * (t > 0.07) * 1.4
    thk = np.sin(2 * np.pi * 110 * t) * np.exp(-np.maximum(0, t - 0.09) * 40) * (t > 0.09) * 0.5
    return A.norm(A.fade(sw + squish + thk, 0.002, 0.03), 0.7)


def sfx_shing():
    d = 0.7
    t = _t(d)
    x = A.hp(A.noise(d, 9), 5000) * np.exp(-t * 9) * 0.3
    x += sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) * a for f, a, k in [(3520, .4, 6), (5274, .25, 8), (7040, .1, 10)])
    return A.norm(A.fade(x, 0.01, 0.05), 0.5)


def sfx_slide():
    d = 0.55
    t = _t(d)
    x = A.bp(A.noise(d, 21), 200, 1400) * np.sin(np.pi * t / d) ** 2
    return A.norm(A.fade(x, 0.01, 0.05), 0.5)


def sfx_rustle(d=3.2):
    t = _t(d)
    x = A.bp(A.noise(d, 31), 1800, 7000) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 3.1 * t) * np.sin(2 * np.pi * 1.3 * t)))
    for k in range(40):  # little 'leaf pops' as trees appear
        st = np.random.default_rng(k).random() * (d - 0.1)
        add_into(x, A.bp(A.noise(0.04, 500 + k), 2000, 6000) * np.exp(-_t(0.04) * 90) * 0.8, st)
    env = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.6)
    return A.norm(x * env, 0.5)


def sfx_chirp(seed=0):
    rng = np.random.default_rng(seed)
    d = 0.35
    out = np.zeros(int(d * SR))
    for k in range(rng.integers(2, 4)):
        dd = 0.07
        tt = _t(dd)
        f0 = rng.uniform(2800, 4200)
        f = f0 * (1 + 0.35 * np.sin(np.pi * tt / dd))
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / dd) ** 2
        add_into(out, x * 0.6, k * 0.095)
    return A.norm(out, 0.4)


def sfx_cluck(seed=0):
    d = 0.45
    out = np.zeros(int(d * SR))
    rng = np.random.default_rng(seed + 50)
    for k in range(3):
        dd = 0.07 if k < 2 else 0.16
        tt = _t(dd)
        f = rng.uniform(420, 520) * (1 + (0.5 if k == 2 else 0.2) * (1 - tt / dd))
        x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.4 + np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * 0.3
        x = A.bp(x, 350, 2500) * np.sin(np.pi * tt / dd) ** 1.5
        add_into(out, x, [0, 0.1, 0.22][k])
    return A.norm(out, 0.45)


def sfx_ting():
    d = 1.6
    t = _t(d)
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, a, k in
            [(2637, 1, 2.2), (5274, 0.35, 4), (3951, 0.3, 3), (7902, 0.12, 6)])
    return A.norm(A.fade(x, 0.002, 0.2), 0.55)


def sfx_cube_land():
    d = 0.9
    t = _t(d)
    x = np.sin(2 * np.pi * 70 * t) * np.exp(-t * 9) * 0.8
    x += sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 5) * 0.15 for f in (523, 787, 1180))
    x += A.lp(A.noise(d, 41), 400) * np.exp(-t * 20) * 0.5
    return A.norm(A.fade(x, 0.002, 0.1), 0.6)


def sfx_glass():
    """Magnifying glass swoop: soft air + glassy shimmer."""
    d = 0.9
    t = _t(d)
    x = A.bp(A.noise(d, 51), 600, 3000) * np.sin(np.pi * np.minimum(1, t / 0.6)) ** 2 * 0.6
    x += sum(np.sin(2 * np.pi * f * t) * np.exp(-np.maximum(0, t - 0.35) * 5) * (t > 0.35) * 0.12
             for f in (2093, 2794, 3520))
    return A.norm(A.fade(x, 0.01, 0.1), 0.5)


def sfx_scuttle(d=4.5):
    """Very soft ant patter texture."""
    x = np.zeros(int(d * SR))
    rng = np.random.default_rng(61)
    for k in range(int(d * 260)):
        st = rng.random() * (d - 0.01)
        add_into(x, A.hp(A.noise(0.004, 600 + (k % 50)), 3500) * rng.uniform(0.2, 1.0), st)
    t = _t(d)
    env = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.8)
    return A.norm(x * env, 0.35)


def sfx_swell(d=3.0):
    t = _t(d)
    x = np.zeros_like(t)
    for m in (55, 62, 67, 71, 74):
        f = A.midi_f(m)
        x += np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.3 * t)) * (0.6 if m < 70 else 0.3)
    x += A.bp(A.noise(d, 71), 3000, 9000) * 0.08
    env = np.minimum(1, t / 1.2) ** 2 * np.minimum(1, (d - t) / 1.2)
    return A.norm(x * env, 0.45)


def sfx_twinkle(k):
    d = 0.9
    t = _t(d)
    f = A.midi_f([84, 86, 88, 91, 93, 96][k % 6])
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 5) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 8)
    return A.norm(A.fade(x, 0.002, 0.1), 0.35)


def sfx_tick():
    d = 0.05
    t = _t(d)
    x = np.sin(2 * np.pi * 1900 * t) * np.exp(-t * 120)
    return A.norm(x, 0.35)


def add_into(buf, x, t):
    s = int(t * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s]


# ------------------------------------------------------------------ cue sheet
def cues():
    from episodes.everything_divided import render as R
    from episodes.everything_divided import scene_cake as SC
    from episodes.everything_divided import scene_island as SI
    from episodes.everything_divided import scene_space as SS
    c = []
    add = lambda t, x, v: c.append((t, x, v))
    # cake
    add(0.05, sfx_shing(), 0.30)
    for i, ct in enumerate(SC.CHOPS):
        add(ct - 0.06, sfx_cake_slice(i), 0.85)
    tt, k = SC.CHOPS[-1] + 0.3, 0
    while tt < SC.T_PEOPLE_END - 0.05:
        add(tt, sfx_cake_slice(10 + k), 0.32 + 0.1 * (k % 2))
        tt += 0.135
        k += 1
    for i in range(10):    # soft counter ticks while the slice count rolls up
        add(SC.CHOPS[-1] + 0.35 + i * (SC.T_PEOPLE_END - SC.CHOPS[-1] - 0.4) / 10, sfx_tick(), 0.25)
    add(SC.T_PEOPLE_END - 0.05, A.get_sfx("sparkle"), 0.28)
    add(SC.T_Q + 0.02, sfx_slide(), 0.5)
    add(SC.T_Q + 0.48, A.get_sfx("pop"), 0.4)
    add(SC.T_SPLIT + 0.45, A.get_sfx("whoosh"), 0.3)
    # land
    add(SI.T_IN, sfx_slide(), 0.35)
    for tf in (SI.T_F1, SI.T_F2, SI.T_F3):
        add(tf + 0.05, A.get_sfx("pop"), 0.38)
    # trees
    add(SI.T_TREE_3T, A.get_sfx("sparkle"), 0.12)
    add(SI.T_TREE_GROW0, sfx_rustle(SI.T_TREE_GROW1 - SI.T_TREE_GROW0 + 0.6), 0.42)
    # birds & chickens
    for k in range(6):
        add(SI.T_BIRDS + k * 0.12 + 0.1, A.get_sfx("flap"), 0.22)
    for k, tc in enumerate([0.4, 1.3, 2.2, 3.4, 4.6, 6.0, 8.5, 11.0, 14.5]):
        add(SI.T_BIRDS + tc, sfx_chirp(k), 0.16)
    for k in range(3):
        add(SI.T_CHICK + 0.15 * k + 0.25, sfx_cluck(k), 0.3)
    # gold
    add(SI.T_CUBE + 0.35, sfx_cube_land(), 0.45)
    add(SI.T_27, A.get_sfx("whoosh"), 0.18)
    add(SI.T_27 + 0.62, sfx_ting(), 0.5)
    add(SI.T_27 + 0.85, A.get_sfx("sparkle"), 0.2)
    # ants
    add(SI.T_ANTS - 0.4, sfx_glass(), 0.4)
    add(SI.T_ANT2 + 0.05, A.get_sfx("whoosh"), 0.16)
    add(SI.T_ANT2 + 0.6, sfx_scuttle(SI.T_MILLION - SI.T_ANT2 + 0.3), 0.16)
    # galaxy
    add(SS.T_STAR - 0.25, sfx_swell(3.4), 0.42)
    for i in range(12):
        add(SS.T_TWELVE - 0.35 + i * 0.07, sfx_twinkle(i), 0.13)
    # recap
    for k in range(7):
        add(SS.T_END1 + 0.5 + k * 0.17, A.get_sfx("pop"), 0.18)
    add(R.T_RW0, A.sfx_rewind(R.T_RW1 - R.T_RW0 + 0.1), 0.32)
    return c


def mix():
    import soundfile as sf
    dur = C.DURATION
    n = int(dur * SR) + SR
    voice = np.zeros(n)
    v, sr = sf.read(os.path.join(BUILD, "voice.wav"))
    voice[: len(v)] = v[: n]
    # gentle voice levelling + compression
    vv = voice[np.abs(voice) > 0.02]
    voice *= 0.16 / (np.sqrt((vv ** 2).mean()) + 1e-9)
    env = A.envelope_follow(voice, 0.005, 0.12)
    gain = np.ones_like(env)
    over = env > 0.3
    gain[over] = (0.3 + (env[over] - 0.3) / 2.5) / env[over]
    voice *= gain
    fx = np.zeros(n)
    for t, x, vol in cues():
        add_into(fx, np.asarray(x, dtype=np.float64) * vol, max(0, t))
    # music beds: curious light bed for Earth, warmer bed for the sky + ending
    t_sky = C.L0("star1") - 0.3
    m1 = A.track("room", t_sky + 1.5)
    m2 = A.track("warm", dur - t_sky + 1.0)
    music = np.zeros(n)
    k = int(1.5 * SR)
    m1[-k:] *= np.linspace(1, 0, k)
    m2[:k] *= np.linspace(0, 1, k)
    add_into(music, m1, 0)
    add_into(music, m2, t_sky - 0.5)
    music[: int(0.4 * SR)] *= np.linspace(0, 1, int(0.4 * SR))
    tail = int(0.5 * SR)
    end = int(dur * SR)
    music[end - tail:end] *= np.linspace(1, 0.3, tail)
    # wind/air ambience on the island (very low)
    amb = np.zeros(n)
    a0, a1 = C.L0("land1") - 0.3, C.L0("star1") + 0.6
    w = np.tile(A.amb_loop("desert"), 8)[: int((a1 - a0) * SR)].astype(np.float64)
    kk = int(0.8 * SR)
    w[:kk] *= np.linspace(0, 1, kk)
    w[-kk:] *= np.linspace(1, 0, kk)
    add_into(amb, w, a0)
    venv = A.envelope_follow(voice, 0.03, 0.45)
    duck = 1.0 - 0.6 * np.clip(venv / 0.08, 0, 1)
    fx_duck = 1.0 - 0.35 * np.clip(venv / 0.08, 0, 1)
    total = (voice + music * 10 ** (-19 / 20) * duck + amb * 10 ** (-30 / 20) * duck
             + fx * 10 ** (-8 / 20) * fx_duck)
    total = np.tanh(total * 0.95) / 0.95
    total = total[: int(dur * SR)]
    os.makedirs(BUILD, exist_ok=True)
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, total.astype(np.float32), SR, subtype="FLOAT")
    # stems for QA (voice vs. everything else)
    sf.write(os.path.join(BUILD, "stem_voice.wav"), voice[: len(total)].astype(np.float32), SR, subtype="FLOAT")
    sf.write(os.path.join(BUILD, "stem_bed.wav"), (total - voice[: len(total)]).astype(np.float32), SR,
             subtype="FLOAT")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    print("mix ->", out)
    return out


# ------------------------------------------------------------------ SRT
def fmt(t):
    ms = int(round(max(0, t) * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(path):
    """Phrase-level cues (<= ~7 words, <= 2 lines of 42 chars) cut at caption-group boundaries."""
    from episodes.everything_divided.script import LINES
    cues_ = []
    for lid, _, _ in LINES:
        groups = [g for g in C.CAPS if g["line"] == lid]
        cur = []
        for g in groups:
            words = sum(len(x["text"].split()) for x in cur)
            if cur and words + len(g["text"].split()) > 7:
                cues_.append(cur)
                cur = []
            cur.append(g)
        if cur:
            cues_.append(cur)
    rows = []
    for i, cu in enumerate(cues_):
        t0 = cu[0]["t0"]
        t1 = cu[-1]["t1"] + 0.25
        if i + 1 < len(cues_):
            t1 = min(t1, cues_[i + 1][0]["t0"] - 0.02)
        txt = " ".join(g["text"] for g in cu)
        if len(txt) > 42:
            ws = txt.split()
            best = min(range(1, len(ws)), key=lambda k: abs(len(" ".join(ws[:k])) - len(" ".join(ws[k:]))))
            txt = " ".join(ws[:best]) + "\n" + " ".join(ws[best:])
        rows.append(f"{i + 1}\n{fmt(t0)} --> {fmt(t1)}\n{txt}\n")
    with open(path, "w") as f:
        f.write("\n".join(rows))
    print("srt ->", path, f"({len(rows)} cues)")
    return path


# ------------------------------------------------------------------ video
def _render_range(args):
    i0, i1, path = args
    from episodes.everything_divided import render as R
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                          "-s", f"{C.W}x{C.H}", "-r", str(C.FPS), "-i", "-", "-c:v", "libx264",
                          "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        s = R.frame(i / C.FPS)
        s.flush()
        p.stdin.write(bytes(s.get_data()))
    p.stdin.close()
    p.wait()
    return path


def render_video(workers=4, t0=0.0, t1=None, draft=False):
    nfr = int(round(C.DURATION * C.FPS))
    a, b = int(t0 * C.FPS), nfr if t1 is None else int(t1 * C.FPS)
    os.makedirs(os.path.join(BUILD, "parts"), exist_ok=True)
    nparts = workers * 3
    edges = [a + (b - a) * k // nparts for k in range(nparts + 1)]
    jobs = [(edges[k], edges[k + 1], os.path.join(BUILD, "parts", f"p{k:02d}.mp4")) for k in range(nparts)]
    st = time.time()
    with Pool(workers) as pool:
        parts = pool.map(_render_range, jobs, chunksize=1)
    print(f"rendered {b - a} frames in {time.time() - st:.0f}s")
    lst = os.path.join(BUILD, "parts", "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    os.makedirs(OUT, exist_ok=True)
    final = os.path.join(OUT, f"{NAME}{'_draft' if draft else ''}.mp4")
    mixp = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-ss", f"{t0}", "-i", mixp, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-profile:v", "high", "-r", str(C.FPS), "-movflags", "+faststart",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", final], check=True)
    print("video ->", final)
    return final


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("audio", "all"):
        mix()
        write_srt(os.path.join(OUT, f"{NAME}.srt"))
    if cmd in ("video", "all"):
        render_video()
    if cmd == "draft":
        t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
        t1 = float(sys.argv[3]) if len(sys.argv) > 3 else None
        render_video(t0=t0, t1=t1, draft=True)


if __name__ == "__main__":
    main()
