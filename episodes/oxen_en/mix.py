"""Sound for the Fire Oxen short: voice + music sections + word-pinned SFX -> -14 LUFS mix, SRT, final mux.

usage (repo root): python3 -m episodes.oxen_en.mix audio   # yumurta/stories/arrows-en/audio/mix.wav + SRT
                   python3 -m episodes.oxen_en.mix final   # mux with the rendered video -> output/
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
ST = os.path.join(ROOT, "yumurta", "stories", "oxen-en")
OUT_DIR = os.path.join(ROOT, "output")
NAME = "FireOxen_EN_yumurta"
WORDS = json.load(open(os.path.join(ST, "voice", "words.json")))["words"]
w = lambda i: WORDS[i]["start"]
A = lambda i: WORDS[i]["start"] - 2 / 30          # two frames before word i (where the acting lands)
DUR = np.ceil((WORDS[-1]["end"] + 2.2) * 30) / 30


# ------------------------------------------------------------------ procedural effects
def crackle(d, seed=1, dens=40):
    """a fire: soft roar plus random pops"""
    rng = np.random.default_rng(seed); n = int(d * SR); x = lp(noise(d, seed), 700) * .35
    for _ in range(int(d * dens)):
        k = int(rng.integers(0, max(1, n - 800))); m = int(rng.integers(60, 400)); burst = bp(noise(m / SR + .01, k % 997), 1500, 6000)[:m]; m = len(burst); x[k:k + m] += burst * np.exp(-np.arange(m) / (m / 4)) * rng.uniform(.4, 1.2)
    return norm(x, .5)


def rumble(d, seed=2):
    """a herd on the run: low rumble with hoof beats"""
    t = t_arr(d); x = lp(noise(d, seed), 160) * 1.2
    beats = (np.sin(2 * np.pi * 7.3 * t) > .6) * 1.0 + (np.sin(2 * np.pi * 9.1 * t + 1) > .7) * .8
    x += lp(noise(d, seed + 1), 400) * lp(beats, 40) * 1.5
    return norm(x * np.minimum(1, t / .4) * np.minimum(1, (d - t) / .6), .6)


def moo(d=1.1, f0=150, seed=0):
    t = t_arr(d); f = f0 * (1 + .12 * np.sin(np.pi * t / d)) * (1 + .015 * np.sin(2 * np.pi * 5.5 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR; x = sum(np.sin(k * ph) / k for k in range(1, 12))
    env = np.minimum(1, t / .12) * np.minimum(1, (d - t) / .25)
    x = bp(x, 180, 1400) + .4 * lp(x, 400)
    return norm(x * env, .7)


def hiss(d=1.0):
    t = t_arr(d); return norm(bp(noise(d, 8), 3000, 9000) * np.minimum(1, t / .05) * np.minimum(1, (d - t) / .3), .4)


# ------------------------------------------------------------------ the cue list (time, sound, gain)
def cues():
    C = []
    W = lambda i, d=0: w(i) + d
    rng = np.random.default_rng(5)
    cr = lambda a, b, g=.3: [(a + k * 2.4, AU.get_sfx("crickets")[: int(2.5 * SR)], g) for k in range(int(max(0, b - a) / 2.4) + 1)]
    # night ambience, fire, the herd
    C += cr(0, w(14) - .2, .3) + [(0, crackle(w(14), 1), .35), (.2, rumble(w(14) - .3, 2), .45)]
    C += cr(W(58), W(70) - .2, .3)
    C += cr(W(106), W(195) - .2, .28)
    C += [(W(118) + .2, crackle(w(128) - w(118), 3, 60), .55), (W(122), rumble(w(128) - w(122) + .3, 4), .7)]
    C += [(W(128), rumble(w(152) - w(128), 5) * .5, .35), (W(152), crackle(w(179) - w(152), 6, 25), .3)]
    # whips
    for i in [3, 6, 11, 14, 23, 29, 36, 41, 52, 58, 70, 79, 85, 88, 94, 106, 107, 122, 128, 140, 147, 152, 160, 164, 179, 186, 195, 207]:
        C.append((W(i) - .4, AU.get_sfx("whoosh"), .5))
    C += [(.05, AU.get_sfx("swish"), .35), (W(3) + .1, AU.music_sting("dun"), .45), (W(6) + .2, moo(1.0, 140, 1), .45), (W(11), AU.get_sfx("chew"), .5), (W(12), crackle(.8, 9, 90), .5)]
    # the trap
    C += [(W(19), AU.music_sting("dun"), .45), (W(29), AU.get_sfx("ding"), .35), (W(38), AU.get_sfx("clank"), .35), (W(38) + .15, AU.get_sfx("murmur")[: int(1.5 * SR)], .3)]
    C += [(W(42), AU.get_sfx("slide_down"), .3), (W(46), AU.get_sfx("sparkle"), .2)]
    # the stakes: sacks vanish, eyes in the dark, a man picked off, the bottleneck
    for k in range(11): C.append((W(53) + k * (w(57) - w(53)) / 11, AU.get_sfx("pop"), .25))
    C += [(W(60), AU.get_sfx("growl"), .4), (W(65) - .02, AU.get_sfx("suck"), .5), (W(65) + .1, AU.get_sfx("poof"), .4), (W(66), AU.get_sfx("gasp"), .3)]
    C += [(W(70) + .1, AU.get_sfx("clank"), .4), (W(75), AU.get_sfx("thud"), .5), (W(75) + .05, AU.music_sting("dun"), .4)]
    # the order: branches, cattle, the question
    C += [(W(81), AU.get_sfx("ding"), .3)]
    for k in range(5): C.append((W(85) + .3 + k * .45, AU.get_sfx("crash_wood"), .12))
    for k in range(12): C.append((W(89) + k * .32, AU.get_sfx("step"), .25))
    C += [(W(90), moo(1.0, 150, 2), .45), (W(92), moo(.8, 125, 3), .35)]
    C += [(W(104) + .15, AU.get_sfx("gulp"), .55), (W(104) + .25, AU.get_sfx("scratch"), .25)]
    # midnight: tie, light, run
    C += [(W(106), AU.music_sting("dun"), .4), (W(110), AU.get_sfx("rope") if "rope" in AU.SFX else AU.get_sfx("creak"), .3)]
    C += [(W(118) + .2, AU.get_sfx("whoosh"), .6), (W(118) + .25, crackle(1.0, 11, 120), .7), (W(119), moo(.9, 175, 4), .5)]
    for k in range(4): C.append((W(122) + .3 + k * .7, moo(.7 + .2 * (k % 2), 150 + 20 * k, 5 + k), .3))
    # the guards
    C += [(W(134), AU.get_sfx("ooh")[: int(1.2 * SR)], .3), (W(140) - .05, AU.get_sfx("gasp"), .35), (W(145), AU.get_sfx("clank"), .45)]
    for k in range(18): C.append((W(147) + k * .14 + rng.uniform(0, .08), AU.get_sfx("step_heavy"), .3))
    C += [(W(149), AU.get_sfx("ding"), .35)]
    # why
    C += [(W(162), AU.get_sfx("sparkle"), .25), (W(170) - .05, AU.get_sfx("click"), .3), (W(171), AU.get_sfx("pop"), .35), (W(176), AU.get_sfx("pop"), .35)]
    # the walk out
    for k in range(10): C.append((W(186) + k * .3, AU.get_sfx("step"), .15))
    C += [(W(189), hiss(.7), .35)]
    # dawn and the payoff
    C += [(W(195), AU.get_sfx("sparkle"), .3), (W(197), AU.get_sfx("murmur")[: int(2.0 * SR)], .3), (W(207), AU.music_sting("dun"), .35)]
    C += [(W(211) + .3, moo(1.4, 120, 9), 1.0), (W(211) + 1.8, AU.music_sting("wah")[: int(1.2 * SR)], .35)]
    return C


def sfx_track(n):
    buf = np.zeros(n)
    for t, x, g in cues():
        add(buf, np.asarray(x, dtype=np.float64) * g * .5, max(0.0, t))
    return buf


def music_track(n):
    secs = [(0.0, w(14), "chase", .5), (w(14), w(79), "suspense", .5), (w(79), w(106), "quirky", .5),
            (w(106), w(152), "chase", .55), (w(152), w(179), "suspense", .45), (w(179), w(195), "quirky", .45), (w(195), DUR, "market", .45)]
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
