"""Sound for the Straw Boats short: voice + music sections + word-pinned SFX -> -14 LUFS mix, SRT, final mux.

usage (repo root): python3 -m episodes.arrows_en.mix audio   # yumurta/stories/arrows-en/audio/mix.wav + SRT
                   python3 -m episodes.arrows_en.mix final   # mux with the rendered video -> output/
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
ST = os.path.join(ROOT, "yumurta", "stories", "arrows-en")
OUT_DIR = os.path.join(ROOT, "output")
NAME = "StrawBoats_EN_yumurta"
WORDS = json.load(open(os.path.join(ST, "voice", "words.json")))["words"]
w = lambda i: WORDS[i]["start"]
A = lambda i: WORDS[i]["start"] - 2 / 30          # two frames before word i (where the acting lands)
DUR = np.ceil((WORDS[-1]["end"] + 2.2) * 30) / 30
BOOM = w(209) + .3
HIT = BOOM + .12


# ------------------------------------------------------------------ procedural effects
def lapping(d, seed=1):
    t = t_arr(d); x = lp(noise(d, seed), 500) * (.6 + .4 * np.sin(2 * np.pi * .35 * t) ** 2)
    return norm(x, .5)


def wind(d, seed=2):
    t = t_arr(d); x = bp(noise(d, seed), 150, 900) * (.7 + .3 * np.sin(2 * np.pi * .13 * t))
    return norm(x, .5)


def drum(seed=0, big=1.0):
    d = .7; t = t_arr(d); f = np.linspace(95, 55, len(t)) * big ** -.2
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 6)
    skin = bp(noise(d, seed), 120, 900) * np.exp(-t * 18)
    return norm(body + .5 * skin, .9)


def thwack(seed=0):
    """an arrow hitting straw: a dry crunch and a soft thump"""
    d = .22; t = t_arr(d)
    x = bp(noise(d, seed), 900, 5000) * np.exp(-t * 45) + .7 * np.sin(2 * np.pi * 110 * t) * np.exp(-t * 30)
    return norm(x, .8)


def zip_(seed=0):
    """an arrow passing: a short falling whistle"""
    d = .35; t = t_arr(d); f = np.linspace(2600, 1500, len(t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2 * .3 + bp(noise(d, seed), 2000, 6000) * np.sin(np.pi * t / d) * .4
    return norm(x, .5)


def quiver(d=.6):
    t = t_arr(d); return norm(np.sin(2 * np.pi * 180 * t + 3 * np.sin(2 * np.pi * 28 * t)) * np.exp(-t * 6), .6)


def honk():
    d = .45; t = t_arr(d); f = 330 + 40 * np.sin(2 * np.pi * 5 * t)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * .5 + np.sin(2 * np.pi * np.cumsum(f * 2) / SR) * .3
    return norm(lp(x, 2200) * np.minimum(1, t / .02) * np.exp(-t * 2.5), .6)


def caw():
    out = np.zeros(int(.9 * SR))
    for k in range(2):
        d = .28; t = t_arr(d); f = 900 - 300 * t / d
        x = bp(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) + .6 * noise(d, k), 500, 3000) * np.sin(np.pi * t / d)
        add(out, x, k * .36)
    return norm(out, .6)


def snore(d=2.4):
    t = t_arr(d); x = lp(noise(d, 4), 260) * np.maximum(0, np.sin(2 * np.pi * .8 * t)) ** 2
    return norm(x, .5)


def rustle(d=1.0, seed=6):
    t = t_arr(d); x = bp(noise(d, seed), 1500, 7000) * (np.abs(np.sin(2 * np.pi * 3 * t)) * .7 + .3)
    return norm(x * np.sin(np.pi * t / d), .5)


def hiss(d=2.0):
    t = t_arr(d); return norm(bp(noise(d, 8), 3000, 9000) * np.minimum(1, t / .05) * np.minimum(1, (d - t) / .4), .4)


# ------------------------------------------------------------------ the cue list (time, sound, gain)
def cues():
    C = []
    W = lambda i, d=0: w(i) + d
    rng = np.random.default_rng(5)
    # ambience: water and fog on the river, birds by day, crickets at night
    C += [(0, lapping(w(15) + .2, 1), .35), (0, wind(w(15), 2), .25)]
    C += [(W(61), AU.get_sfx("crickets")[: int(2.5 * SR)], .35), (W(61) + 2.4, AU.get_sfx("crickets")[: int(2.5 * SR)], .35), (W(61) + 4.8, AU.get_sfx("crickets")[: int(2.5 * SR)], .3)]
    C += [(W(88), wind(w(107) - w(88), 3), .4), (W(88), lapping(w(107) - w(88), 4), .35)]
    C += [(W(139), lapping(w(182) - w(139), 5), .3), (W(182), lapping(DUR - w(182) - .3, 6), .3)]
    # whips
    for i in [3, 9, 13, 15, 25, 33, 39, 45, 53, 61, 72, 77, 88, 97, 104, 107, 116, 125, 136, 139, 143, 149, 155, 160, 170, 182, 187, 192, 197, 206]:
        C.append((W(i) - .4, AU.get_sfx("whoosh"), .5))
    C += [(.05, AU.get_sfx("swish"), .35), (W(9), AU.music_sting("dun"), .5), (W(13) + .1, AU.get_sfx("boing"), .3)]
    # the order
    C += [(W(29), AU.get_sfx("ding"), .3), (W(31), AU.get_sfx("ding"), .3), (W(38), AU.get_sfx("sparkle"), .35)]
    C += [(W(42), AU.get_sfx("slide_down"), .35), (W(44), AU.music_sting("dun"), .5)]
    # two days of nothing
    C += [(W(47), AU.get_sfx("pop"), .35), (W(49), AU.get_sfx("pop"), .35), (W(53) - .1, snore(), .45), (W(56) - .05, honk(), .6), (W(60), AU.music_sting("wah")[: int(.9 * SR)], .35)]
    # the third night
    C += [(W(63), AU.get_sfx("pop"), .3), (W(66), rustle(2.2, 6), .5), (W(69), rustle(1.6, 7), .4)]
    for k in range(6): C.append((W(72) + k * .66, AU.get_sfx("pop"), .35))
    C += [(W(86) - .05, AU.get_sfx("flap"), .4), (W(86), caw(), .55)]
    # the voyage and the drums
    C += [(W(93), AU.get_sfx("sparkle"), .15)]
    for i in [104, 105, 106]: C.append((W(i) - .03, drum(i, 1.2), 1.0))
    for k in np.arange(W(106) + .45, W(182) - .3, .62): C.append((k, drum(int(k * 10), 1.0), .28))
    # the enemy shore
    C += [(W(110), AU.get_sfx("ooh")[: int(1.0 * SR)], .25), (W(118), AU.music_sting("dun"), .3), (W(131) - .05, AU.get_sfx("thud"), .3)]
    C += [(W(132) + .2, AU.get_sfx("creak"), .5)]
    for k in range(40): C.append((W(136) - .06 + rng.uniform(0, 1.3), AU.get_sfx("swish"), .18))
    # the barrage: zips and thwacks on side A, the tip, the turn, side B
    for k in range(90):
        t0 = rng.uniform(W(139) - .3, W(149) + .1); C.append((t0, thwack(k), rng.uniform(.25, .6)));
        if k % 3 == 0: C.append((t0 - .3, zip_(k), .25))
    C += [(W(146) - .1, AU.get_sfx("creak"), .6), (W(150), AU.get_sfx("creak"), .5), (W(151), AU.get_sfx("splash"), .4)]
    for k in range(80):
        u = rng.uniform(0, 1); t0 = W(159) + .1 + (W(182) - .4 - W(159) - .1) * u * u
        C.append((t0, thwack(k + 100), rng.uniform(.2, .5)))
        if k % 3 == 0: C.append((t0 - .3, zip_(k + 100), .2))
    C += [(W(163) - .02, thwack(7), .9), (W(163), quiver(), .5)]
    # sunrise, home, the shout
    C += [(W(182), AU.get_sfx("sparkle"), .35), (W(193), AU.get_sfx("ding"), .4), (W(197), AU.get_sfx("cheer")[: int(3.0 * SR)], .5), (W(206), AU.get_sfx("laugh")[: int(1.5 * SR)], .3)]
    # the payoff: one arrow back into his crown
    C += [(HIT - .35, zip_(3), .7), (HIT, thwack(3), 1.2), (HIT + .02, quiver(.8), .7), (HIT + .4, hiss(1.6), .45), (HIT + .3, AU.music_sting("dun"), .5)]
    return C


def sfx_track(n):
    buf = np.zeros(n)
    for t, x, g in cues():
        add(buf, np.asarray(x, dtype=np.float64) * g * .5, max(0.0, t))
    return buf


def music_track(n):
    secs = [(0.0, w(45), "market", .5), (w(45), w(88), "quirky", .5), (w(88), w(160), "suspense", .6),
            (w(160), w(182), "quirky", .45), (w(182), DUR, "festival", .5)]
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
    parts = [os.path.join(ST, "out", p + ".mp4") for p in ("part1", "part2")]
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
