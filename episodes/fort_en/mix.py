"""Sound for the Empty Fort short: voice + music sections + word-pinned SFX -> -14 LUFS mix, SRT, final mux.

usage (repo root): python3 -m episodes.fort_en.mix audio   # yumurta/stories/fort-en/audio/mix.wav + SRT
                   python3 -m episodes.fort_en.mix final   # mux with the rendered video -> output/
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import butter, lfilter

from cinecode import audio as AU
from cinecode.audio import SR, add, bp, lp, noise, norm, t_arr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ST = os.path.join(ROOT, "yumurta", "stories", "fort-en")
OUT_DIR = os.path.join(ROOT, "output")
NAME = "EmptyFort_EN_yumurta"
WORDS = json.load(open(os.path.join(ST, "voice", "words.json")))["words"]
w = lambda i: WORDS[i]["start"]
A = lambda i: WORDS[i]["start"] - 2 / 30          # two frames before word i (where the acting lands)
DUR = np.ceil((WORDS[-1]["end"] + 2.2) * 30) / 30


# ------------------------------------------------------------------ procedural effects
PENTA = [62, 64, 67, 69, 71, 74, 76, 79, 81]          # D major pentatonic: the zither's tune


def zither(d, seed=1, density=3.2):
    """a calm guqin-like line: plucked pentatonic notes, an occasional slide, room tail"""
    rng = np.random.default_rng(seed); out = np.zeros(int(d * SR) + SR); t = 0.0; i = 4
    while t < d:
        i = int(np.clip(i + rng.choice([-2, -1, -1, 1, 1, 2]), 0, len(PENTA) - 1))
        add(out, AU.pluck(PENTA[i], 1.4, .45, int(rng.integers(0, 5))) * .7, t)
        if rng.random() < .3: add(out, AU.pluck(PENTA[i] - 12, 1.8, .3, 1) * .5, t)
        t += rng.choice([1, 1, 2, .5]) / density
    out = out[: int(d * SR)]
    k = int(.3 * SR); out[-k:] *= np.linspace(1, 0, k)
    return norm(out, .7)


def twang():
    """a string snapping"""
    t = t_arr(.9); f = 330 * np.exp(-t * 3) + 90
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    p = np.zeros_like(x); q = AU.pluck(50, .8, .9, 2)[: len(t)]; p[: len(q)] = q
    return norm(x + .3 * p, .9)


def march(d, seed=2):
    """an army on the march: low rumble with a steady tramp"""
    t = t_arr(d); x = lp(noise(d, seed), 160) * 1.3
    tramp = (np.sin(2 * np.pi * 2.0 * t) > .6) * 1.0
    x += bp(noise(d, seed + 1), 200, 800) * lp(tramp, 40) * 1.6
    return norm(x * np.minimum(1, t / .5) * np.minimum(1, (d - t) / .6), .6)


def gong():
    t = t_arr(2.5); x = np.zeros_like(t)
    for f, a in [(110, 1), (167, .6), (231, .45), (297, .3), (412, .2)]: x += a * np.sin(2 * np.pi * f * t * (1 + .002 * np.sin(5 * t)))
    return norm(x * np.exp(-t * 1.2) * np.minimum(1, t / .01), .9)


# ------------------------------------------------------------------ the cue list (time, sound, gain)
def cues():
    C = []
    W = lambda i, d=0: w(i) + d
    rng = np.random.default_rng(5)
    # whips (one per camera whip)
    for i in [11, 15, 19, 26, 36, 39, 41, 46, 52, 56, 59, 61, 66, 75, 79, 82, 86, 94, 99, 102, 107, 112, 117, 119, 121, 123, 127, 131, 136, 143, 148, 152, 159, 165, 172, 174]:
        C.append((W(i) - .38, AU.get_sfx("whoosh"), .45))
    # hook: the army, the gate, the song
    C += [(0, march(w(11), 3), .5), (W(6), AU.music_sting("dun"), .45), (W(6), gong(), .35)]
    C += [(W(12), AU.get_sfx("creak"), .55), (W(13) + .2, AU.get_sfx("creak"), .35), (W(14) + .3, AU.get_sfx("thud"), .4)]
    C += [(W(15) - .1, zither(w(19) - w(15) + .2, 1), .55)]
    # the problem
    C += [(W(24), AU.get_sfx("wah")[: int(1.0 * SR)], .25), (W(33), AU.get_sfx("ding"), .3), (W(36), AU.get_sfx("dishes"), .35), (W(37), AU.get_sfx("chew")[: int(.6 * SR)], .25)]
    for k in range(3): C.append((W(39) + .2 + k * .55, AU.get_sfx("growl")[: int(.4 * SR)], .12))
    for k in range(9): C.append((W(41) + k * .22, AU.get_sfx("step"), .35))
    C += [(W(41) + .1, AU.get_sfx("creak"), .3), (W(46), AU.get_sfx("gasp"), .35), (W(48), march(w(56) - w(48), 6), .35), (W(53), AU.music_sting("dun"), .45)]
    # run? fight? panic
    C += [(W(56), AU.get_sfx("pop"), .35), (W(58), AU.get_sfx("bonk"), .35), (W(59), AU.get_sfx("clank"), .4), (W(60), AU.music_sting("wah")[: int(1.0 * SR)], .35)]
    C += [(W(61) + .2, AU.get_sfx("murmur")[: int(2.0 * SR)], .35), (W(63), AU.get_sfx("gasp"), .3)]
    for k in range(10): C.append((W(61) + k * .2 + rng.uniform(0, .05), AU.get_sfx("step"), .25))
    # the orders: a tick per item
    C += [(W(70), AU.get_sfx("sparkle"), .3)]
    C += [(W(76) + k * .35, AU.get_sfx("swish"), .3) for k in range(6)] + [(W(78), AU.get_sfx("ding"), .3)]
    C += [(W(80) + k * .12, AU.get_sfx("slide_down")[: int(.4 * SR)], .2) for k in range(5)] + [(W(81), AU.get_sfx("ding"), .3), (W(81) + .2, AU.get_sfx("pop"), .3)]
    C += [(W(82) + .1, AU.get_sfx("creak"), .6), (W(84), AU.get_sfx("creak"), .4), (W(85), AU.get_sfx("thud"), .45), (W(85) + .05, AU.get_sfx("ding"), .3)]
    C += [(W(86) + k * .45, AU.get_sfx("swish"), .3) for k in range(7)] + [(W(89), AU.get_sfx("ding"), .3), (W(90), AU.get_sfx("slide_up"), .35), (W(92), AU.get_sfx("tada"), .3)]
    # the wall
    C += [(W(94) + k * .3, AU.get_sfx("step"), .3) for k in range(14)]
    C += [(W(99) + .2, AU.get_sfx("zap")[: int(.3 * SR)], .15), (W(100), AU.get_sfx("sparkle"), .25), (W(102) + .2, AU.get_sfx("thud"), .25)]
    C += [(W(107) - .1, zither(w(152) - w(107) + 6, 7), .55)]
    # the enemy
    C += [(W(112), march(w(118) - w(112) + .4, 8), .55), (W(118), AU.get_sfx("freeze"), .5), (W(118), AU.music_sting("dun"), .4)]
    C += [(W(121) + .4, AU.get_sfx("coo"), .3), (W(123) + .2, AU.get_sfx("ooh")[: int(.9 * SR)], .15), (W(128), AU.get_sfx("heartbeat"), .35)]
    C += [(W(135), AU.get_sfx("thud"), .4)] + [(W(137) + k * .2, AU.get_sfx("pop"), .3) for k in range(8)] + [(W(142), AU.music_sting("dun"), .5), (W(142), gong(), .4)]
    C += [(W(144), AU.get_sfx("gasp"), .4), (RUN0(), march(DUR - RUN0() - 6, 9), .6), (RUN0() + .3, AU.get_sfx("murmur")[: int(2.5 * SR)], .45)]
    C += [(RUN0() + k * .16, AU.get_sfx("step_heavy"), .25) for k in range(20)]
    # why it works; the end
    C += [(W(157), AU.get_sfx("ding"), .3), (W(164), AU.get_sfx("thud"), .55), (W(164) + .02, AU.get_sfx("clank"), .35)]
    C += [(W(170), AU.get_sfx("wah")[: int(1.0 * SR)], .3), (W(172) + .2, AU.get_sfx("laugh"), .3), (W(176), AU.get_sfx("sparkle"), .25)]
    C += [(BOOM(), twang(), .7), (BOOM() + .05, AU.get_sfx("gulp"), .45), (BOOM() + .3, AU.get_sfx("boing"), .3)]
    return C


RUN0 = lambda: w(145) - .1
BOOM = lambda: w(178) + .05


def sfx_track(n):
    buf = np.zeros(n)
    for t, x, g in cues():
        add(buf, np.asarray(x, dtype=np.float64) * g * .5, max(0.0, t))
    return buf


def music_track(n):
    secs = [(0.0, w(15), "chase", .5), (w(19), w(41), "quirky", .5), (w(41), w(66), "chase", .5), (w(66), w(94), "quirky", .5),
            (w(112), w(143), "suspense", .45), (w(143), w(152), "chase", .55), (w(165), DUR, "market", .4)]
    buf = np.zeros(n); xf = .25
    for a, b, name, g in secs:
        a0 = max(0.0, a - xf); seg = AU.track(name, b - a0 + xf); m = len(seg); env = np.ones(m); k = int(xf * SR)
        env[:k] = np.linspace(0, 1, k); env[-k:] = np.linspace(1, 0, k)
        add(buf, seg * env * g, a0)
    return buf


def duck(music, voice, depth_db=9.0):
    env = AU.envelope_follow(voice, .03, .4); env = env / (env.max() + 1e-9)
    return music * 10 ** (-depth_db * np.clip(env * 3, 0, 1) / 20)


def build_audio():
    v, vsr = sf.read(os.path.join(ST, "voice", "voice.wav"))
    v = AU.resample(v.astype(np.float64), vsr, SR) if vsr != SR else v
    n = int(DUR * SR) + 1
    voice = np.zeros(n); voice[: min(n, len(v))] = v[:n]
    music = duck(music_track(n), voice)
    sfx = sfx_track(n)
    mixw = voice * 1.0 + music * .2 + sfx * .55
    k = int(.5 * SR); mixw[-k:] *= np.linspace(1, 0, k)
    raw = os.path.join(ST, "audio", "mix_raw.wav")
    sf.write(raw, np.stack([mixw, mixw], 1).astype(np.float32), SR)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", os.path.join(ST, "audio", "mix.wav")], check=True)
    os.remove(raw)
    print("mix", os.path.join(ST, "audio", "mix.wav"), f"{DUR:.2f}s")
    write_srt()


def _ts(t):
    h, rem = divmod(t, 3600); m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"


def write_srt():
    cues_, cur = [], []
    for x in WORDS:
        cur.append(x)
        if x["word"][-1] in ".?!\"" or len(cur) >= 7 or (x["word"][-1] in ",:" and len(cur) >= 4):
            cues_.append(cur); cur = []
    if cur: cues_.append(cur)
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, NAME + ".en.srt")
    with open(p, "w") as f:
        for i, c in enumerate(cues_, 1):
            f.write(f"{i}\n{_ts(c[0]['start'])} --> {_ts(c[-1]['end'])}\n{' '.join(x['word'] for x in c)}\n\n")
    print("srt", p)


def final():
    parts = [os.path.join(ST, "out", p + ".mp4") for p in ("p1", "p2", "p3")]
    lst = os.path.join(ST, "out", "parts.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    silent = os.path.join(ST, "out", "video_silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    out = os.path.join(OUT_DIR, NAME + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", os.path.join(ST, "audio", "mix.wav"), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("final", out)


if __name__ == "__main__":
    {"audio": build_audio, "final": final}[sys.argv[1]]()
