"""Sound for the Pompeii short: voice + music sections + word-pinned SFX -> -14 LUFS mix, SRT, final mux.

usage (repo root): python3 -m episodes.pompeii_en.mix audio   # yumurta/stories/pompeii-en/audio/mix.wav + SRT
                   python3 -m episodes.pompeii_en.mix final   # mux with the rendered video -> output/
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
ST = os.path.join(ROOT, "yumurta", "stories", "pompeii-en")
OUT_DIR = os.path.join(ROOT, "output")
NAME = "Pompeii_EN_yumurta"
WORDS = json.load(open(os.path.join(ST, "voice", "words.json")))["words"]
w = lambda i: WORDS[i]["start"]
A = lambda i: WORDS[i]["start"] - 2 / 30          # two frames before word i (where the acting lands)
DUR = np.ceil((WORDS[-1]["end"] + 2.2) * 30) / 30
BOOM = w(210) + .55
ERUPT = w(67) + .05


# ------------------------------------------------------------------ procedural effects
def boom(d=2.6, seed=3, low=180):
    n = int(SR * d); t = np.arange(n) / SR; rng = np.random.default_rng(seed); x = rng.standard_normal(n)
    b, a = butter(2, low / (SR / 2)); rum = lfilter(b, a, x); rum /= np.abs(rum).max()
    b2, a2 = butter(2, [300 / (SR / 2), 3000 / (SR / 2)], "band"); crack = lfilter(b2, a2, x); crack /= np.abs(crack).max()
    thump = np.sin(2 * np.pi * np.cumsum(np.linspace(70, 28, n)) / SR)
    y = .9 * rum * np.exp(-t * 1.4) * (1 - np.exp(-t * 80)) + .6 * thump * np.exp(-t * 3) + .35 * crack * np.exp(-t * 7) * (1 - np.exp(-t * 200))
    return norm(y, .9)


def rumble(d=1.4, seed=5):
    t = t_arr(d); x = lp(noise(d, seed), 120) * (np.sin(2 * np.pi * 9 * t) * .3 + .7)
    env = np.minimum(1, t / .08) * np.exp(-t * 1.8)
    return norm(x * env, .8)


def patter(d=4.0, seed=7, rate=40):
    """pumice on roofs and stones: many small dry clicks"""
    out = np.zeros(int(d * SR)); rng = np.random.default_rng(seed)
    click = bp(noise(.03, seed), 1500, 5000) * np.exp(-t_arr(.03) * 160)
    for _ in range(int(d * rate)):
        add(out, click * rng.uniform(.2, 1), rng.uniform(0, d - .05))
    return norm(out, .6)


def fizz(d=1.6, seed=9):
    t = t_arr(d); x = bp(noise(d, seed), 3000, 9000) * np.exp(-t * 1.5) * np.minimum(1, t / .02)
    return norm(x, .6)


def shake_rattle(d=.6, seed=11):
    """a bottle being shaken: fast swishes"""
    t = t_arr(d); x = bp(noise(d, seed), 800, 4000) * (np.abs(np.sin(2 * np.pi * 7 * t)) ** 2)
    return norm(x, .5)


def surge(d=4.5, seed=13):
    t = t_arr(d); x = lp(noise(d, seed), 400) * .8 + bp(noise(d, seed + 1), 600, 2500) * .25
    env = np.minimum(1, t / 1.2) * np.minimum(1, (d - t) / .6)
    return norm(x * env, .8)


def hammer():
    return norm(AU.get_sfx("clank")[: int(.18 * SR)] * .6 + AU.get_sfx("thud")[: int(.18 * SR)] * .6, .7)


# ------------------------------------------------------------------ the cue list (time, sound, gain)
def cues():
    C = []
    W = lambda i, d=0: w(i) + d
    for k in np.arange(.05, w(12) - .2, 1 / 3.2): C.append((k + .3, hammer(), .35))              # the hook's hammering
    C += [(.25, rumble(1.0), .9), (W(2) + .25, rumble(.9, 6), .7)]
    # whip pans (whoosh at the start of each whip)
    for t0 in [W(2) - .4, W(6) - .26, W(11) - .36, W(12) - .2, W(24) - .22, W(29) - .2, W(46) - .2, W(57) - .36, W(63) - .2,
               W(68) - .22, W(88) - .2, W(107) - .22, W(113) - .36, W(117) - .2, W(128) - .2, W(131) - .22, W(141) - .22,
               W(155) - .36, W(160) - .2, W(183) - .22, W(188) - .38, W(201) - .38]:
        C.append((t0, AU.get_sfx("whoosh"), .55))
    C += [(W(11) + .1, AU.music_sting("dun"), .55)]
    # 62: the quake, the column, the rebuild
    C += [(W(20) - .1, rumble(1.6, 8), 1.0), (W(21) - .05, AU.get_sfx("crash_wood"), .7), (W(21) + .25, boom(1.2, 4, 120), .5)]
    C += [(W(26) + .1, AU.get_sfx("creak"), .5), (W(27), AU.get_sfx("ding"), .45)]
    C += [(W(36), AU.get_sfx("sparkle"), .3)]
    # 79: tremors, rattling jars, the shrug
    for k in [50, 51, 53, 61]: C.append((W(k) - .08, rumble(.9, k), .75)); C.append((W(k), AU.get_sfx("clank"), .25))
    C += [(W(62) + .15, AU.get_sfx("laugh")[: int(1.2 * SR)], .25)]
    # midday: the eruption
    C += [(ERUPT - .05, boom(3.2, 21), 1.0), (ERUPT + .4, AU.get_sfx("gasp"), .4)]
    C += [(W(82), AU.get_sfx("sparkle"), .2), (W(92), AU.music_sting("tada")[: int(.8 * SR)], .25), (W(94), AU.get_sfx("splash"), .3)]
    C += [(W(103) - .1, rumble(2.4, 30), .4)]
    # pumice
    C += [(W(107), patter(9.6, 31), .55), (A(114) + .15, AU.get_sfx("bonk"), .8), (W(121) + .1, AU.get_sfx("creak"), .55)]
    C += [(W(123) - .12, AU.get_sfx("crash_wood"), 1.0), (W(123) - .05, boom(1.0, 33, 140), .55), (W(128), AU.get_sfx("murmur")[: int(2.6 * SR)], .35)]
    C += [(W(131), patter(3.8, 35, 18), .3), (W(139) - .1, rumble(1.0, 36), .45)]
    # the surge
    C += [(W(141) + .1, surge(4.6), .9), (W(155) - .1, AU.get_sfx("whoosh"), .4)]
    for k in range(6): C.append((W(155) + k * .2, AU.get_sfx("step"), .3))
    # the soda
    for k in range(5): C.append((W(165) + k * .55, shake_rattle(), .4))
    C += [(A(175), AU.get_sfx("pop"), 1.0), (A(175) + .02, fizz(), .7), (A(175) + .05, boom(1.6, 41), .55)]
    # buried / 1599
    C += [(W(184), surge(2.6, 50), .45), (W(189), AU.get_sfx("ding"), .3)]
    for k in np.arange(W(188), W(201), .62): C.append((k, AU.get_sfx("clank"), .2))
    C += [(W(199) + .1, AU.get_sfx("wah")[: int(.5 * SR)], .2)]
    # finale
    for k in np.arange(W(201), BOOM - .2, 1 / 3.2): C.append((k + .1, hammer(), .3))
    C += [(BOOM - .02, boom(2.8, 3), 1.15), (BOOM + 1.0, AU.get_sfx("gulp"), .5)]
    return C




def sfx_track(n):
    buf = np.zeros(n)
    for t, x, g in cues():
        add(buf, np.asarray(x, dtype=np.float64) * g * .5, max(0.0, t))
    return buf


def music_track(n):
    secs = [(0.0, w(63), "market", .5), (w(63), w(160), "suspense", .6), (w(160), w(183), "quirky", .5),
            (w(183), w(201), "suspense", .45), (w(201), DUR, "quirky", .5)]
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
