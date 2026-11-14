"""Assemble "Why You Stay Awake" (Just Needy English adaptation), 1080x1920 @30fps.

usage:
  python -m episodes.why_you_stay_awake.film stills t1 t2 ...   # PNG previews
  python -m episodes.why_you_stay_awake.film audio              # voice + music + sfx mix, SRT
  python -m episodes.why_you_stay_awake.film video              # final mp4 (needs audio)
"""
import math
import multiprocessing as mp
import os
import subprocess
import sys

import cairo
import numpy as np

from cinecode import audio as A
from cinecode import tts
from cinecode.captions import render_text
from cinecode.core import back_out, clamp, ease_in, ease_io, ease_out, kf, noise1, prog, smooth
from . import graphics as G
from . import timing as TM

W, H, FPS = 1080, 1920, 30
ROOT = TM.ROOT
BUILD = TM.BUILD
OUT = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_WHY_YOU_STAY_AWAKE_ENGLISH"
TL = TM.build()
L = {l["key"]: l for l in TL["lines"]}
END = TL["end"]
CAP_Y = 330
CAP_SIZE = 80
LEAD = 0.05          # visual events lead the spoken word by a frame or two


def g(key, i):
    return L[key]["words"][i][1] - LEAD


def ge(key, i):
    return L[key]["words"][i][2]


def t0(key):
    return L[key]["t0"] - LEAD


CUT = 0.04
SCENES = [
    ("eye1", 0.0, t0("eaten") - CUT),
    ("clockA", t0("eaten") - CUT, t0("battery") - CUT),
    ("batA", t0("battery") - CUT, t0("steal") - CUT),
    ("night", t0("steal") - CUT, t0("loop") - CUT),
    ("batB", t0("loop") - CUT, t0("ending") - CUT),
    ("clockB", t0("ending") - CUT, t0("share") - CUT),
    ("eye2", t0("share") - CUT, t0("follow") - CUT),
    ("card", t0("follow") - CUT, END - TM.LOOP_TAIL),
    ("eyeloop", END - TM.LOOP_TAIL, END + 1),
]


def scene_at(t):
    for name, a, b in SCENES:
        if a <= t < b:
            return name, a
    return SCENES[-1][0], SCENES[-1][1]


def entry_zoom(t, a, amt=0.035, d=0.45):
    """Small settle-in on every cut (keeps the original's hard-cut rhythm, smoother)."""
    return 1 + amt * (1 - ease_out(prog(t, a, a + d)))


# ------------------------------------------------------------------ EYE
def eye_state1(t):
    o = kf(t, [
        (0.0, 0.80), (0.75, 0.80), (1.15, 0.30), (1.32, 0.26), (1.42, 0.92), (1.65, 0.82),
        (2.25, 0.82), (2.55, 0.55), (2.68, 0.85),
        (g("revenge", 1) + 0.05, 0.78), (g("revenge", 2) - 0.05, 0.08),
        (g("revenge", 2) + 0.06, 1.0)], ease_io)
    o += 0.015 * noise1(t * 3, 4)
    zoom = 1 + 0.42 * ease_io(prog(t, g("revenge", 2), g("revenge", 2) + 0.55))
    phase = 0 if t < 1.4 else 1 if t < 2.65 else 2 if t < g("revenge", 2) else 3
    return o, zoom, phase


def eye_state2(t):
    a = SCENES[6][1]
    snap = g("share", 3)
    o = kf(t, [(a, 0.85), (g("share", 1), 0.80), (ge("share", 2) - 0.02, 0.04), (snap, 0.04), (snap + 0.10, 1.0),
               (snap + 0.6, 0.86)], ease_io)
    o += 0.015 * noise1(t * 3, 9)
    ca = ease_out(prog(t, snap, snap + 0.18))
    cs = 0.85 + 0.15 * back_out(prog(t, snap, snap + 0.3))
    phase = 4 if t < snap else 0
    return o, phase, ("3:00 AM", ca, cs)


# ------------------------------------------------------------------ CLOCK
def pop(t, at, d=0.32):
    return back_out(prog(t, at, at + d)) if t >= at else 0.0


def clock_A(t):
    a = SCENES[1][1]
    st = {}
    work, school, traffic, home = (g("list", i) for i in range(4))
    yrs = g("yours", 3)
    because = g("brain", 4)
    tomorrow = g("brain", 6)
    hand = kf(t, [(a, 7.4), (work, 11.5), (school, 15.5), (traffic, 17.2), (home, 19.8), (g("yours", 0), 21.6),
                  (yrs, 22.8), (g("brain", 1), 23.5), (because, 23.85)], ease_io)
    if g("brain", 1) <= t < tomorrow:
        hand = min(hand, 23.85) + 0.05 * math.sin(t * 38) * clamp((t - g("brain", 1)) / 0.4)
    if t >= tomorrow:
        hand = 23.85 + (8.5 + 24 - 23.85) * ease_io(prog(t, tomorrow, ge("brain", 9)))
    st["hand"] = hand
    sp = lambda at, d=0.42: ease_out(prog(t, at, at + d))
    st["sectors"] = {"trafficAM": sp(work), "work": sp(work), "school": sp(school), "traffic": sp(traffic),
                     "home": sp(home), "yours": sp(g("yours", 1), 0.6)}
    fade_out = 1 - smooth(prog(t, g("yours", 0), g("yours", 0) + 0.35))
    back = smooth(prog(t, because + 0.3, because + 0.6))
    lab = lambda at: clamp(pop(t, at) * 1.0) * max(fade_out, back) if t >= at else 0.0
    st["labels"] = {"work": lab(work), "school": lab(school), "traffic": lab(traffic), "home": lab(home)}
    st["label_scale"] = {k: 0.6 + 0.4 * pop(t, at) for k, at in
                         (("work", work), ("school", school), ("traffic", traffic), ("home", home))}
    st["label_scale"] = {k: (v if t < because else 1.0) for k, v in st["label_scale"].items()}
    zin = ease_io(prog(t, g("yours", 1), yrs + 0.1))
    zout = ease_io(prog(t, because, because + 0.6))
    z = zin * (1 - zout)
    st["zoom"] = (1 + 0.85 * z) * entry_zoom(t, a)
    st["focus"] = (540 + (455 - 540) * z, 1110 + (835 - 1110) * z)
    glow = smooth(prog(t, yrs, yrs + 0.3)) * (1 - smooth(prog(t, because, because + 0.5)))
    st["yours_glow"] = glow * (0.75 + 0.25 * math.sin(t * 6))
    st["grey"] = smooth(prog(t, because, because + 0.6))
    st["night_dim"] = 0.0
    ba = min(pop(t, yrs), 1 - smooth(prog(t, because, because + 0.3)))
    st["badge"] = (clamp(ba), 0.7 + 0.3 * pop(t, yrs), (540, 1270), 96)
    return st


def clock_B(t):
    a = SCENES[5][1]
    st = {"sectors": {k: 1.0 for k in G.SECTORS}, "labels": {}}
    only = g("ending", 6)
    yrs = g("ending", 8)
    st["hand"] = kf(t, [(a, 23.1), (g("ending", 3), 23.6), (only, 23.82)], ease_io)
    if t > only:
        st["hand"] = 23.82 + 0.04 * math.sin(t * 40)
    st["sleep_label"] = clamp(pop(t, a + 0.15))
    st["sleep_scale"] = 0.6 + 0.4 * pop(t, a + 0.15)
    gl = smooth(prog(t, g("ending", 4), g("ending", 4) + 0.4))
    st["yours_glow"] = gl * (0.8 + 0.2 * math.sin(t * 6))
    st["night_dim"] = 0.85 * gl
    st["others_dim"] = 0.0
    st["grey"] = 0.0
    st["zoom"] = (1 + 0.07 * ease_io(prog(t, g("ending", 3), ge("ending", 8)))) * entry_zoom(t, a)
    st["focus"] = (540, 1080)
    st["badge"] = (clamp(pop(t, only)), 0.6 + 0.4 * pop(t, only), (540, 1395), 88)
    return st


# ------------------------------------------------------------------ BATTERY
def clock_str(mins):
    mins = int(round(mins)) % (24 * 60)
    h, m = divmod(mins, 60)
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {ap}"


def bat_A(t):
    plus = g("battery", 0)
    red = g("battery", 4)
    because = g("battery", 7)
    endd = ge("battery", 10)
    if t < because:
        x = ease_in(prog(t, plus + 0.15, red + 0.25)) ** 0.9
        pct = 100 - 97 * x
        mins = 8 * 60 + (23 * 60 - 8 * 60) * x
        show_time = t >= g("battery", 1)
    else:
        x = prog(t, because + 0.12, endd - 0.05)
        x = smooth(x)
        pct = 100 - 97 * x
        mins = 8 * 60 + (23 * 60 - 8 * 60) * x
        show_time = True
    tag = ease_out(prog(t, g("battery", 2), g("battery", 2) + 0.25))
    low = clamp((25 - pct) / 20)
    blink = 1.0
    if pct < 5 and t < because:
        blink = 0.65 + 0.35 * math.cos(t * 9)
    return dict(pct=pct, tag=tag, time=clock_str(mins) if show_time else None, bolt=0, yesterday=0,
                low=low * blink, warm=0.0)


def bat_B(t):
    a = SCENES[4][1]
    k1 = g("loop", 2)          # "next day" -> 60 %, 7:00 AM
    k2 = g("loop", 4)          # "drops"
    k3 = ge("loop", 5)         # "even lower." -> 29 %, 12:30 PM
    k4 = g("loop", 6)          # "And you do"
    k5 = g("loop", 7)          # -> 3 %, 5:15 PM
    k6 = g("loop", 8)          # "thing again." -> charging again at 3:00 AM
    keys_p = [(a, 3), (a + 0.25, 3), (k1 + 0.25, 60), (k2, 60), (k3, 29), (k4, 29), (k5 + 0.1, 3), (k6, 3)]
    keys_m = [(a, 180), (a + 0.25, 180), (k1 + 0.25, 420), (k2, 420), (k3, 750), (k4, 750), (k5 + 0.1, 1035),
              (k6, 1035), (k6 + 0.01, 180)]
    pct = kf(t, keys_p, ease_io)
    mins = kf(t, keys_m, smooth)
    charging = t < k1 + 0.3 or t >= k6
    bolt = 1.0 if charging else 0.0
    tag = 0.0 if charging else ease_out(prog(t, k1 + 0.3, k1 + 0.5))
    yest = ease_out(prog(t, g("loop", 1), g("loop", 1) + 0.25)) * (1 - smooth(prog(t, k4, k4 + 0.3)))
    low = clamp((25 - pct) / 20)
    warm = clamp((pct - 20) / 30) * 0.9
    return dict(pct=pct, tag=tag, time=clock_str(mins), bolt=bolt, yesterday=yest, low=low, warm=warm)


# ------------------------------------------------------------------ NIGHT
def night_state(t):
    hours = g("steal", 1)
    knowing = g("steal", 3)
    pay = g("steal", 5)
    if t < hours:
        s, ap = "11:00", "PM"
    elif t < knowing:
        s, ap = " 2:00", "AM"
    else:
        s, ap = " 4:47", "AM"
    fl = 1.0
    for at in (hours, knowing):
        if at <= t < at + 0.08:
            fl = 0.15
    red = smooth(prog(t, pay - 0.1, pay + 0.5)) * (0.85 + 0.15 * math.sin(t * 7))
    return s, ap, red, fl


# ------------------------------------------------------------------ CAPTIONS
CAPS = TL["caps"]


def draw_caption(cx, t):
    for c in CAPS:
        if c["t0"] - LEAD <= t < c["t1"]:
            txt = c["text"]
            size = CAP_SIZE
            surf, w, h, pad = render_text(txt, size)
            while w - 2 * pad > 940 and size > 50:
                size -= 4
                surf, w, h, pad = render_text(txt, size)
            a = clamp((t - (c["t0"] - LEAD)) / 0.06)
            cx.set_source_surface(surf, W / 2 - w / 2, CAP_Y - h / 2)
            cx.paint_with_alpha(a)
            return


# ------------------------------------------------------------------ FRAME
def render_frame(t, surf=None):
    surf = surf or cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(surf)
    name, a = scene_at(t)
    if name in ("eye1", "eyeloop"):
        if name == "eye1":
            o, zoom, phase = eye_state1(t)
        else:
            o, zoom, phase = 0.80 + 0.015 * noise1(t * 3, 4), 1.0, 0
        G.draw_eye(cx, t, o, zoom * entry_zoom(t, a, 0.0), phase)
        G.watermark(cx)
    elif name == "eye2":
        o, phase, chip = eye_state2(t)
        G.draw_eye(cx, t, o, entry_zoom(t, a), phase, chip=chip)
        G.watermark(cx)
    elif name in ("clockA", "clockB"):
        st = clock_A(t) if name == "clockA" else clock_B(t)
        G.draw_clock_bg(cx, st.get("grey", 0.0), t)
        G.draw_clock(cx, st, t)
        G.watermark(cx)
    elif name in ("batA", "batB"):
        st = bat_A(t) if name == "batA" else bat_B(t)
        G.draw_battery_bg(cx, st["low"], st["warm"])
        z = entry_zoom(t, a)
        cx.save()
        cx.translate(540, 1060)
        cx.scale(z, z)
        cx.translate(-540, -1060)
        G.draw_battery(cx, t, st["pct"], st["tag"], st["time"], st["bolt"], st["yesterday"],
                       render_text=render_text)
        cx.restore()
        G.watermark(cx)
    elif name == "night":
        s, ap, red, fl = night_state(t)
        z = entry_zoom(t, a)
        cx.save()
        cx.translate(540, 960)
        cx.scale(z, z)
        cx.translate(-540, -960)
        G.draw_night(cx, t, s, ap, red, fl, phone_phase=1)
        cx.restore()
        G.watermark(cx)
    elif name == "card":
        tap = g("follow", 3)
        fp = prog(t, tap, tap + 0.45) if t >= tap else 0.0
        G.draw_card(cx, t, t - a, fp, render_text)
    draw_caption(cx, t)
    return surf


# ------------------------------------------------------------------ OUTPUT
def stills(times, prefix="still"):
    os.makedirs(os.path.join(BUILD, "stills"), exist_ok=True)
    for tt in times:
        s = render_frame(float(tt))
        p = os.path.join(BUILD, "stills", f"{prefix}_{float(tt):06.2f}.png")
        s.write_to_png(p)
        print(p)


def _worker(args):
    i0, i1, path = args
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
           "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for i in range(i0, i1):
        cx = cairo.Context(surf)
        cx.set_source_rgb(0, 0, 0)
        cx.paint()
        render_frame(i / FPS, surf)
        surf.flush()
        p.stdin.write(bytes(surf.get_data()))
    p.stdin.close()
    p.wait()
    return path


def render_video(workers=4):
    n = int(round(END * FPS))
    chunk = math.ceil(n / (workers * 3))
    jobs = [(i, min(n, i + chunk), os.path.join(BUILD, f"part_{k:03d}.mp4"))
            for k, i in enumerate(range(0, n, chunk))]
    with mp.Pool(workers) as pool:
        parts = pool.map(_worker, jobs)
    lst = os.path.join(BUILD, "parts.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    silent = os.path.join(BUILD, "silent.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    silent], check=True)
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, NAME + ".mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", os.path.join(BUILD, "mix.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    print(out)


# ------------------------------------------------------------------ AUDIO
def music_bed(dur):
    """Soft late-night bed: warm pads + sparse plucks, A minor, 84 bpm."""
    SR = A.SR
    n = int(dur * SR)
    buf = np.zeros(n + SR * 4)
    beat = 60 / 84
    chords = [(57, 60, 64), (53, 57, 60), (48, 55, 60), (55, 59, 62)]   # Am F C G
    bar = beat * 4
    t = 0.0
    k = 0
    while t < dur:
        ch = chords[k % 4]
        for m in ch:
            A.add(buf, A.pad(m - 12, bar + 0.6, 0.22) * 0.35, t)
        A.add(buf, A.bass(ch[0] - 24, bar * 0.9) * 0.35, t)
        arp = [ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[1], ch[0] + 12, ch[2]]
        for j, m in enumerate(arp):
            A.add(buf, A.pluck(m, 0.7, 0.35, seed=j) * 0.16, t + j * beat / 2)
        t += bar
        k += 1
    x = buf[:n]
    return x / (np.abs(x).max() + 1e-9)


def sfx_events():
    ev = []
    for name, a, b in SCENES[1:8]:
        ev.append(("whoosh", a - 0.08, 0.10))
    ev += [("pop", g("list", i), 0.22) for i in range(4)]
    ev += [("sparkle", g("yours", 3), 0.16), ("sparkle", g("ending", 6), 0.14)]
    ev += [("beep", g("steal", 1), 0.10), ("beep", g("steal", 3), 0.10)]
    ev += [("beep2", g("battery", 4), 0.12), ("beep2", ge("battery", 10) - 0.1, 0.10)]
    ev += [("zap", SCENES[4][1] + 0.05, 0.05), ("zap", g("loop", 8), 0.05)]
    ev += [("click", g("follow", 3) + 0.02, 0.35), ("pop", g("share", 3), 0.22), ("ding", g("follow", 0), 0.12)]
    # clock ticks while the hand sweeps
    for tt in np.arange(SCENES[1][1] + 0.1, g("list", 3) + 0.4, 0.5):
        ev.append(("tick", tt, 0.06))
    return ev


def _tick():
    d = 0.05
    tt = A.t_arr(d)
    return (np.sin(2 * np.pi * 2600 * tt) * np.exp(-tt * 160)) * 0.6


def mix_audio():
    SR = A.SR
    n = int((END + 0.2) * SR)
    voice = np.zeros(n)
    for l in TL["lines"]:
        clip = tts.read_wav(l["clip"]).astype(np.float64)
        clip = A.resample(clip, tts.SR, SR)
        A.add(voice, clip, l["t0"])
    voice /= (np.abs(voice).max() + 1e-9)
    voice *= 0.9
    music = music_bed(END + 0.2)[:n]
    env = A.envelope_follow(voice, 0.03, 0.45)
    duck = 1 - 0.55 * np.clip(env / 0.25, 0, 1)
    music = music * 0.13 * duck
    # fade music in/out
    fi = int(0.4 * SR)
    music[:fi] *= np.linspace(0, 1, fi)
    fo = int(0.5 * SR)
    music[-fo:] *= np.linspace(1, 0, fo)
    sfx = np.zeros(n)
    for name, tt, gain in sfx_events():
        if name == "tick":
            x = _tick()
        else:
            x = A.get_sfx(name)
        A.add(sfx, x * gain, tt)
    mixd = voice + music + sfx
    raw = os.path.join(BUILD, "mix_raw.wav")
    import soundfile as sf
    sf.write(raw, mixd.astype(np.float32), SR)
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af",
                    "loudnorm=I=-14:TP=-1.0:LRA=9", "-ar", "48000", out], check=True)
    print(out)


def fmt(t):
    t = max(0, t)
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, NAME + ".srt")
    with open(path, "w", encoding="utf-8") as f:
        for i, c in enumerate(CAPS, 1):
            end = c["t1"]
            if i < len(CAPS):
                end = min(end, CAPS[i]["t0"] - LEAD - 0.001)
            f.write(f"{i}\n{fmt(c['t0'] - LEAD)} --> {fmt(end)}\n{c['text']}\n\n")
    print(path)


def main():
    cmd = sys.argv[1]
    if cmd == "stills":
        stills(sys.argv[2:])
    elif cmd == "audio":
        mix_audio()
        write_srt()
    elif cmd == "video":
        render_video()
    elif cmd == "scenes":
        for nm, a, b in SCENES:
            print(f"{nm:8s} {a:6.2f} {b:6.2f}")


if __name__ == "__main__":
    main()
