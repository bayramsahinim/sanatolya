"""Sound for the Ships Over the Hill short: voice + music sections + word-pinned SFX -> -14 LUFS mix, SRT, final mux.

usage (repo root): python3 -m episodes.ships_en.mix audio   # yumurta/stories/arrows-en/audio/mix.wav + SRT
                   python3 -m episodes.ships_en.mix final   # mux with the rendered video -> output/
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
ST = os.path.join(ROOT, "yumurta", "stories", "ships-en")
OUT_DIR = os.path.join(ROOT, "output")
NAME = "ShipsOverHill_EN_yumurta"
WORDS = json.load(open(os.path.join(ST, "voice", "words.json")))["words"]
w = lambda i: WORDS[i]["start"]
A = lambda i: WORDS[i]["start"] - 2 / 30          # two frames before word i (where the acting lands)
DUR = np.ceil((WORDS[-1]["end"] + 2.2) * 30) / 30


# ------------------------------------------------------------------ procedural effects
def waves(d, seed=1):
    """harbour water: slow swells of filtered noise"""
    t = t_arr(d); x = lp(noise(d, seed), 500) * (.6 + .4 * np.sin(2 * np.pi * .23 * t) * np.sin(2 * np.pi * .11 * t + 1))
    return norm(x * np.minimum(1, t / .5) * np.minimum(1, (d - t) / .5), .4)


def haul(d, seed=2):
    """a ship dragged on rollers: low rumble with wooden knocks"""
    t = t_arr(d); x = lp(noise(d, seed), 180) * 1.2
    knocks = (np.sin(2 * np.pi * 3.1 * t) > .85) * 1.0
    x += bp(noise(d, seed + 1), 300, 1200) * lp(knocks, 60) * 1.4
    return norm(x * np.minimum(1, t / .4) * np.minimum(1, (d - t) / .6), .6)


def drum(seed=0):
    t = t_arr(.5); f = 70 * np.exp(-t * 6) + 45
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) + .3 * lp(noise(.5, seed), 900) * np.exp(-t * 30)
    return norm(x, .9)


# ------------------------------------------------------------------ the cue list (time, sound, gain)
def cues():
    C = []
    W = lambda i, d=0: w(i) + d
    rng = np.random.default_rng(5)
    cr = lambda a, b, g=.3: [(a + k * 2.4, AU.get_sfx("crickets")[: int(2.5 * SR)], g) for k in range(int(max(0, b - a) / 2.4) + 1)]
    # ambience: night crickets, the harbour water, the haul
    C += cr(0, w(14) - .2, .28) + cr(W(99), W(163) - .2, .26)
    C += [(W(14), waves(w(66) - w(14), 1), .35), (W(163), waves(DUR - w(163), 3), .35), (0, haul(w(14), 4), .3), (W(102), haul(w(139) - w(102), 5), .5)]
    # whips
    for i in [6, 9, 10, 14, 20, 26, 34, 40, 44, 49, 55, 66, 72, 77, 85, 90, 99, 102, 116, 120, 131, 135, 139, 146, 150, 163, 175, 182]:
        C.append((W(i) - .4, AU.get_sfx("whoosh"), .5))
    # the hook
    C += [(.05, AU.get_sfx("swish"), .35), (W(0) + .2, AU.get_sfx("creak"), .35), (W(7), AU.get_sfx("creak"), .4), (W(9), AU.music_sting("dun"), .45), (W(10), AU.get_sfx("splash"), .5)]
    # the chain
    C += [(W(18), AU.get_sfx("ding"), .3), (W(23), AU.get_sfx("clank"), .45), (W(24), AU.get_sfx("clank"), .3)]
    for k in range(6): C.append((W(27) + k * .32, AU.get_sfx("splash")[: int(.4 * SR)], .15))
    C += [(W(31) - .05, AU.get_sfx("bonk"), .7), (W(31), AU.get_sfx("boing"), .5), (W(31) + .05, AU.get_sfx("clank"), .5)]
    C += [(W(35), AU.get_sfx("laugh"), .45), (W(36) + .3, AU.get_sfx("laugh"), .3), (W(43) + .3, AU.get_sfx("laugh"), .35)]
    # the stakes
    for k in range(15): C.append((W(44) + k * (w(48) - w(44)) / 15, AU.get_sfx("pop"), .2))
    for k in range(4): C.append((W(44) + k * .95, AU.get_sfx("thud"), .4))
    C += [(W(47), AU.get_sfx("ding"), .3), (W(50), AU.get_sfx("cheer"), .35), (W(58), AU.get_sfx("murmur")[: int(2.0 * SR)], .25), (W(63), AU.music_sting("dun"), .35)]
    # the road
    C += [(W(68), AU.get_sfx("ding"), .3)]
    for k in range(5): C.append((W(72) + k * .4, AU.get_sfx("thud"), .3))
    C += [(W(76) - .02, AU.get_sfx("poof"), .5), (W(76), AU.get_sfx("crash_wood"), .4)]
    for k in range(10): C.append((W(77) + .2 + k * .55, AU.get_sfx("crash_wood"), .12))
    C += [(W(86), AU.get_sfx("slide_down"), .3), (W(88), AU.get_sfx("sparkle"), .25), (W(96), AU.get_sfx("gasp"), .3)]
    # the night
    C += [(W(99), AU.music_sting("dun"), .4)]
    for k in range(20): C.append((W(102) + k * .45 + rng.uniform(0, .1), AU.get_sfx("step_heavy"), .25))
    C += [(W(105), AU.get_sfx("creak"), .45), (W(112), AU.get_sfx("creak"), .4), (W(116), AU.get_sfx("creak"), .35)]
    C += [(W(127), AU.get_sfx("slide_up"), .35), (W(128) + .2, AU.get_sfx("flap"), .4), (W(132), AU.get_sfx("swish"), .3), (W(133), AU.get_sfx("swish"), .3)]
    for k in range(12): C.append((W(135) + k * .4, drum(k), .55 if k < 6 else .3))
    # why
    C += [(W(142), AU.get_sfx("ding"), .35), (W(147), AU.music_sting("wah")[: int(1.0 * SR)], .3), (W(156), AU.get_sfx("slide_down"), .4), (W(161) + .2, AU.get_sfx("splash"), .5)]
    # dawn and the payoff
    C += [(W(163), AU.get_sfx("sparkle"), .3), (W(165), AU.get_sfx("coo"), .3), (W(170), AU.get_sfx("ooh")[: int(1.0 * SR)], .15)]
    C += [(W(174) - .05, AU.get_sfx("freeze"), .5), (W(174), AU.music_sting("dun"), .45), (W(176), AU.get_sfx("gasp"), .35), (W(176) + .2, AU.get_sfx("murmur")[: int(1.6 * SR)], .3)]
    C += [(W(184) + .1, AU.get_sfx("click"), .35), (W(185) + .08, AU.get_sfx("clank"), .7), (W(185) + .2, AU.music_sting("wah")[: int(1.4 * SR)], .4)]
    return C


def sfx_track(n):
    buf = np.zeros(n)
    for t, x, g in cues():
        add(buf, np.asarray(x, dtype=np.float64) * g * .5, max(0.0, t))
    return buf


def music_track(n):
    secs = [(0.0, w(14), "chase", .5), (w(14), w(66), "suspense", .5), (w(66), w(99), "quirky", .5),
            (w(99), w(139), "chase", .55), (w(139), w(163), "suspense", .45), (w(163), w(182), "suspense", .45), (w(182), DUR, "market", .45)]
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
