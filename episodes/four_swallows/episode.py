"""Just Needy — "Can You Swallow Four Times?" : animation, audio mix, SRT and final export.

usage:
  python -m episodes.four_swallows.episode stills        # QA stills -> build/four_swallows/stills
  python -m episodes.four_swallows.episode audio         # mix + SRT
  python -m episodes.four_swallows.episode video         # full render + mux -> output/
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cairo
import numpy as np

from cinecode import audio as A
from cinecode import captions as C
from cinecode.core import back_out, clamp, ease_io, ease_out, prog, smooth
from episodes.four_swallows import art
from episodes.four_swallows.script import LINES
from episodes.four_swallows.timing import beats, caption_groups, clips, timeline

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "four_swallows")
OUT = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_FOUR_SWALLOWS_ENGLISH"
FPS = 30
W, H = art.W, art.H
CAP_Y = 1500
CAP_SIZE = 88

B = beats()
END = B["end"]
GROUPS = caption_groups()
WORDS = B["words"]


def win(t, a, b):
    return smooth(prog(t, a, b))


def bump(t, a, d):
    """0 -> 1 -> 0 over [a, a+d]."""
    x = prog(t, a, a + d)
    return math.sin(math.pi * x) if 0 < x < 1 else 0.0


def swallow_curve(x):
    """Larynx lift for one dry swallow (x = 0..1 over ~0.75 s)."""
    return smooth(prog(x, 0.0, 0.38)) * (1 - smooth(prog(x, 0.55, 1.0)))


# ------------------------------------------------------------------ state
T_LENS = B["to_lens"]
T_FRONT = B["to_front"]
T_RESET = T_FRONT + 0.12


def circle_states(t):
    st = [dict() for _ in range(4)]
    four = WORDS["hook"][3][0]                         # "four" in the hook
    for i in range(4):
        st[i]["pulse"] = bump(t, four + i * 0.09, 0.38)
    for k in range(1, 5):
        s = st[k - 1]
        s["active"] = win(t, B[f"n{k}"] - 0.06, B[f"n{k}"] + 0.12)
        if k < 4:
            s["done"] = clamp(prog(t, B[f"ok{k}"] - 0.22, B[f"ok{k}"] + 0.30))
        else:
            s["warn"] = clamp(prog(t, B["stall"], B["stall"] + 0.40))
            hard = win(t, B["hard_swallow"], B["hard_swallow"] + 0.3) * (1 - win(t, T_FRONT - 0.2, T_FRONT))
            s["wobble"] = 1.0 + 1.6 * hard
    # reset for "try it again": everything returns to the opening state
    for i in range(4):
        r = win(t, T_RESET + i * 0.08, T_RESET + i * 0.08 + 0.28)
        if r > 0:
            s = st[i]
            for key in ("active", "done", "warn"):
                s[key] = s.get(key, 0) * (1 - r)
            s["pulse"] = s.get("pulse", 0) + bump(t, T_RESET + i * 0.08 + 0.14, 0.32)
    return st


def front_state(t):
    st = {"brows": "neutral", "mouth": "smile", "look": (0, 0), "eyes": "open"}
    st["dy"] = 3.0 * math.sin(t * 2 * math.pi / 3.4)               # breathing
    start = timeline()[0]
    # "Sounds easy, right?" - confident little brow raise
    if start["easy"] <= t < start["try"]:
        st["brows"], st["mouth"] = "up", "smirk"
    # "Let's try it" - small ready nod
    st["head_dy"] = 10 * bump(t, start["try"] + 0.1, 0.45)
    sw = 0.0
    strain = 0.0
    for k in (1, 2, 3):
        x = prog(t, B[f"sw{k}"], B[f"sw{k}"] + 0.78)
        if 0 < x < 1:
            sw = max(sw, swallow_curve(x))
            st["mouth"] = "flat"
            st["brows"] = "flat" if x < 0.8 else "neutral"
    # the fourth attempt: starts, stalls part-way, gives up
    t4 = B["sw4"]
    if t >= t4 - 0.05:
        x = t - t4
        rise = 0.5 * smooth(prog(x, 0.0, 0.42))
        fall = smooth(prog(x, 1.25, 1.75))
        sw = max(sw, rise * (1 - fall))
        strain = smooth(prog(x, 0.35, 0.6)) * (1 - smooth(prog(x, 1.2, 1.6)))
        if x < 1.5:
            st["mouth"] = "flat"
            st["brows"] = "flat" if x < 0.5 else "worried"
        else:
            st["mouth"], st["brows"] = "frown", "worried"
            st["look"] = (-0.35, 0.15) if t >= B["stuck"] + 0.3 else (0, 0)
    st["sw"] = sw
    st["strain"] = strain
    st["head_dy"] += 7 * sw
    # back on the front shot for "Go on, try it again"
    if t >= T_FRONT:
        st.update(brows="neutral", mouth="smile", look=(0, 0), strain=0.0, sw=0.0)
        tr = WORDS["again"][2][0]
        if B["again"] <= t < tr + 0.6:
            st["brows"] = "up"
        st["head_dy"] = st.get("head_dy", 0) * 0 + 8 * bump(t, B["again"] + 0.05, 0.45)
    # keep the very first and last frames free of blinks (clean loop)
    st["blink"] = 0.3 < t < END - 0.4
    return st


def lens_state(t):
    st = {"bolus": 1.0, "bolus_pos": 0.0, "wet": 1.0, "sw": 0.0, "signal": 0.0, "empty": 0.0, "strain": 0.0}
    # reflex: a signal pulse on the word "reflex"
    rw = B["reflex_word"]
    sig1 = prog(t, rw - 0.1, rw + 0.8)
    # the swallow on "...something in your throat to swallow"
    ks = B["kick_swallow"]
    x = prog(t, ks, ks + 1.35)
    st["sw"] = x if 0 < x < 1 else 0.0
    st["bolus_pos"] = smooth(prog(t, ks + 0.08, ks + 1.35))
    sig2 = prog(t, ks + 0.25, ks + 1.0)
    if 0 < sig1 < 1:
        st["signal"], st["signal_pos"] = math.sin(math.pi * sig1), ease_io(sig1)
    elif 0 < sig2 < 1:
        st["signal"], st["signal_pos"] = math.sin(math.pi * sig2), ease_io(sig2)
    # a smaller drop builds up again, then runs low
    if t > ks + 1.35:
        st["bolus_pos"] = 0.0
        st["bolus"] = 0.45 * win(t, ks + 1.4, ks + 1.9) * (1 - win(t, B["saliva_low"], B["saliva_low"] + 0.9))
    st["wet"] = 1 - 0.85 * win(t, B["saliva_low"], B["saliva_low"] + 1.3)
    st["empty"] = win(t, B["saliva_low"] + 0.6, B["saliva_low"] + 1.0)
    # "...so that next swallow gets a lot harder": the throat tries with nothing to move
    hs = B["hard_swallow"]
    y = prog(t, hs, hs + 1.5)
    if 0 < y < 1:
        st["sw"] = 0.5 * swallow_curve(y) / 0.5 * 0.42 if False else 0.42 * math.sin(math.pi * y)
        st["strain"] = math.sin(math.pi * y)
    return st


def profile_head_state(t):
    st = {"brows": "neutral", "mouth": "smile", "look": (0.3, 0)}
    if t >= B["saliva_low"]:
        st["mouth"] = "flat"
    if t >= B["bubble"] - 0.1:
        st["brows"], st["look"] = "up", (0.5, -0.5)
    if t >= B["hard_swallow"]:
        st.update(brows="worried", mouth="flat", look=(0.3, 0.2))
        st["head_dy"] = 4 * math.sin(t * 38) * bump(t, B["hard_swallow"], 1.5)
    return st


# ------------------------------------------------------------------ captions
def draw_captions(cx, t):
    for t0, t1, txt in GROUPS:
        if t0 <= t < t1:
            surf, w, h, pad = C.render_text(txt, CAP_SIZE)
            k = ease_out(prog(t, t0, t0 + 0.10))
            sc = 0.94 + 0.06 * k
            a = k if t - t0 < 0.10 else 1.0
            # a short fade only where a line ends (no next group right after)
            nxt = [g for g in GROUPS if abs(g[0] - t1) < 0.02]
            if not nxt:
                a *= 1 - prog(t, t1 - 0.12, t1)
            cx.save()
            cx.translate(W / 2, CAP_Y)
            cx.scale(sc, sc)
            cx.set_source_surface(surf, -w / 2, -h / 2)
            cx.paint_with_alpha(a)
            cx.restore()
            break


# ------------------------------------------------------------------ frame
def draw_front_scene(cx, t, zoom=1.0, focus=(540, 1080)):
    cx.save()
    if zoom != 1.0:
        cx.translate(focus[0], focus[1])
        cx.scale(zoom, zoom)
        cx.translate(-focus[0], -focus[1])
    art.background(cx)
    art.draw_front(cx, front_state(t), t)
    cx.restore()


def draw_lens_scene(cx, t, appear, zoom=1.0):
    cx.save()
    if zoom != 1.0:
        cx.translate(540, 1000)
        cx.scale(zoom, zoom)
        cx.translate(-540, -1000)
    art.background(cx)
    hs = profile_head_state(t)
    art.draw_profile_body(cx, t, 2.5 * math.sin(t * 2 * math.pi / 3.4))
    art.draw_profile_head(cx, t, hs)
    art.draw_lens(cx, lens_state(t), t, appear)
    lx, ly, _ = art.LENS
    sal_a = win(t, B["something"], B["something"] + 0.3) * (1 - win(t, B["saliva_low"] + 0.9, B["saliva_low"] + 1.2))
    th_a = win(t, WORDS["kicks"][6][0], WORDS["kicks"][6][0] + 0.3) * (1 - win(t, B["saliva_low"], B["saliva_low"] + 0.3))
    art.draw_label(cx, "throat", 150, 940, lx - 125 * art.LENS[2] / 292, ly - 40 * art.LENS[2] / 292, th_a * appear)
    art.draw_label(cx, "saliva", 880, 820, lx - 11 * art.LENS[2] / 292, ly - 176 * art.LENS[2] / 292, sal_a * appear)
    ba = win(t, B["bubble"], B["bubble"] + 0.35) * (1 - win(t, B["hard_swallow"] - 0.2, B["hard_swallow"] + 0.1))
    art.draw_thought(cx, 820, 560, ba, t, (575, 585))
    cx.restore()


def frame(t):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(surf)
    in_lens = T_LENS <= t < T_FRONT + 0.5
    if not in_lens:
        draw_front_scene(cx, t)
    else:
        # front -> cutaway: push toward the throat, then an iris opens from the throat (no ghosting);
        # cutaway -> front: the iris closes back onto the throat.
        lx, ly, _ = art.LENS
        if t < T_FRONT:
            k = ease_io(prog(t, T_LENS + 0.22, T_LENS + 0.62))
            rad, ctr = 1500 * k, (540, 1080)
            under_z = 1 + 0.30 * ease_io(prog(t, T_LENS, T_LENS + 0.55))
        else:
            k = ease_io(prog(t, T_FRONT, T_FRONT + 0.36))
            rad, ctr = 1500 * (1 - k), (lx, ly)
            under_z = 1 + 0.10 * (1 - ease_out(prog(t, T_FRONT + 0.1, T_FRONT + 0.5)))
        if rad < 1500:
            draw_front_scene(cx, t, under_z)
        if rad > 0:
            cx.save()
            cx.arc(ctr[0], ctr[1], rad, 0, 2 * math.pi)
            cx.clip()
            appear = prog(t, T_LENS + 0.35, T_LENS + 0.85)
            z = 1.0 + 0.08 * (1 - ease_out(prog(t, T_LENS + 0.2, T_LENS + 0.8)))
            draw_lens_scene(cx, t, appear, z)
            cx.restore()
            if rad < 1500:
                cx.arc(ctr[0], ctr[1], rad, 0, 2 * math.pi)
                cx.set_source_rgba(1, 1, 1, 0.9)
                cx.set_line_width(14)
                cx.stroke_preserve()
                cx.set_source_rgba(0.11, 0.11, 0.14, 1)
                cx.set_line_width(5)
                cx.stroke()
    art.draw_circles(cx, circle_states(t), t)
    draw_captions(cx, t)
    return surf


def _render_frame(i):
    s = frame(i / FPS)
    s.flush()
    return bytes(s.get_data())


# ------------------------------------------------------------------ audio
def glock_soft(m, d=0.7):
    return A.glock(m, d)


def mix_audio():
    n = int(END * A.SR) + A.SR
    voice = np.zeros(n)
    fx = np.zeros(n)
    start, dur, _ = timeline()
    for lid, *_ in LINES:
        x = clips()[lid].astype(np.float64)
        x = A.resample(x, 24000, A.SR)
        v = x[np.abs(x) > 0.02]
        x = x * (0.16 / (np.sqrt((v ** 2).mean()) + 1e-9))
        if lid.startswith("c"):
            x *= 0.95
        A.add(voice, x, start[lid])
    # --- subtle feedback sounds (never on top of a word)
    four = WORDS["hook"][3][0]
    for i in range(4):
        A.add(fx, A.woodblock(True) * 0.10, four + i * 0.09 + 0.05)
    for k in (1, 2, 3):
        A.add(fx, glock_soft(79 + [0, 4, 7][k - 1], 0.6) * 0.45, B[f"ok{k}"] - 0.05)
    A.add(fx, glock_soft(76, 0.5) * 0.30, B["stall"])
    A.add(fx, glock_soft(72, 0.8) * 0.30, B["stall"] + 0.16)
    A.add(fx, A.sfx_whoosh(0.5, 400, 1800) * 0.16, T_LENS + 0.05)
    A.add(fx, A.sfx_sparkle() * 0.10, B["reflex_word"] - 0.05)
    A.add(fx, A.sfx_pop() * 0.16, B["bubble"])
    A.add(fx, A.sfx_whoosh(0.45, 1800, 400) * 0.14, T_FRONT - 0.05)
    for i in range(4):
        A.add(fx, A.woodblock(False) * 0.08, T_RESET + i * 0.08 + 0.14)
    # --- light music bed, ducked under the narrator
    music = A.track("room", END + 1)[: n] if len(A.track("room", END + 1)) >= n else np.pad(A.track("room", END + 1), (0, n))[:n]
    k = int(0.25 * A.SR)
    music[:k] *= np.linspace(0.3, 1, k)
    env = A.envelope_follow(voice, 0.03, 0.45)
    duck = 1.0 - 0.55 * np.clip(env / 0.08, 0, 1)
    music_gain = 10 ** (-11 / 20)
    fx_gain = 10 ** (-8 / 20)
    total = voice + music * music_gain * duck + fx * fx_gain
    total = np.tanh(total * 0.95) / 0.95
    total = total[: int(END * A.SR)]
    tail = int(0.3 * A.SR)
    total[-tail:] *= np.linspace(1, 0.15, tail)       # soft tail; loop restarts on the hook
    os.makedirs(BUILD, exist_ok=True)
    import soundfile as sf
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, total.astype(np.float32), A.SR, subtype="FLOAT")
    # stems for QA (voice vs. bed level)
    sf.write(os.path.join(BUILD, "stem_voice.wav"), voice[: len(total)].astype(np.float32), A.SR, subtype="FLOAT")
    sf.write(os.path.join(BUILD, "stem_bed.wav"), (total - voice[: len(total)]).astype(np.float32), A.SR,
             subtype="FLOAT")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    return out


# ------------------------------------------------------------------ SRT
def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt_cues():
    cues = []
    for lid, text, *_ in LINES:
        w = WORDS[lid]
        if lid.startswith("c"):
            text = text.rstrip(".") + "…"
        cues.append([w[0][0] - 0.05, w[-1][1] + (1.0 if lid.startswith("c") else 0.35), text])
    for a, b in zip(cues, cues[1:]):
        a[1] = min(a[1], b[0] - 0.04)
    return cues


def write_srt(path):
    with open(path, "w") as f:
        for i, (a, b, txt) in enumerate(srt_cues(), 1):
            if len(txt) > 42:              # two balanced lines for long cues
                words = txt.split()
                best = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
                txt = " ".join(words[:best]) + "\n" + " ".join(words[best:])
            f.write(f"{i}\n{fmt(max(0, a))} --> {fmt(b)}\n{txt}\n\n")


# ------------------------------------------------------------------ render
def render_video():
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    mix = mix_audio()
    write_srt(os.path.join(OUT, NAME + ".srt"))
    nfr = int(round(END * FPS))
    silent = os.path.join(BUILD, "video_silent.mp4")
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-movflags", "+faststart", silent]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, data in enumerate(pool.imap(_render_frame, range(nfr), chunksize=4)):
            p.stdin.write(data)
            if i % 60 == 0:
                print(f"frame {i}/{nfr}", flush=True)
    p.stdin.close()
    p.wait()
    final = os.path.join(OUT, NAME + ".mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", mix, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-shortest", "-movflags", "+faststart", final],
                   check=True)
    print("wrote", final)


def stills(times):
    d = os.path.join(BUILD, "stills")
    os.makedirs(d, exist_ok=True)
    for t in times:
        frame(t).write_to_png(os.path.join(d, f"t{t:05.2f}.png"))
    return d


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "video"
    if cmd == "stills":
        ts = [float(x) for x in sys.argv[2:]] or [0.0, 3.2, 6.9, 7.6, 11.8, 13.2, 15.5, 17.0, 19.0, 20.4, 22.6,
                                                  23.8, 25.9, 27.0, 28.0, END - 1 / FPS]
        print(stills(ts))
    elif cmd == "audio":
        print(mix_audio())
        write_srt(os.path.join(OUT, NAME + ".srt"))
    else:
        render_video()
