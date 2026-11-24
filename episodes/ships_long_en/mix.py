"""Sound for the long-form Ships documentary: narration + a cinematic score per section + word-pinned SFX -> -14 LUFS, SRT, mux.

The score is composed here from cinecode.audio instruments (pads, brass, bass, plucks, frame drums): calmer and more
cinematic than the Shorts' comic beds, one mood per section, crossfaded at the section gaps.
usage (repo root): python3 -m episodes.ships_long_en.mix audio   # yumurta/stories/ships-long-en/audio/mix.wav + SRT
                   python3 -m episodes.ships_long_en.mix final   # concat the rendered parts, mux -> output/
"""
import json
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

from cinecode import audio as AU
from cinecode.audio import SR, add, bp, lp, noise, norm, t_arr

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ST = os.path.join(ROOT, "yumurta", "stories", "ships-long-en")
OUT_DIR = os.path.join(ROOT, "output")
NAME = "ShipsOverHill_Documentary_EN"
WORDS = json.load(open(os.path.join(ST, "voice", "words.json")))["words"]
SECS = json.load(open(os.path.join(ST, "voice", "sections.json")))
SEC = {}
for x in WORDS: SEC.setdefault(x["sec"], []).append(x)
ws = lambda s, i: SEC[s][min(i, len(SEC[s]) - 1)]["start"]
DUR = np.ceil((WORDS[-1]["end"] + 1.6) * 30) / 30


# ------------------------------------------------------------------ the score
# moods: (root midi, scale, chord degrees, bpm, layers)
PHRYG = [0, 1, 4, 5, 7, 8, 10]          # the "Ottoman" colour (phrygian dominant)
MINOR = [0, 2, 3, 5, 7, 8, 10]
MAJOR = [0, 2, 4, 5, 7, 9, 11]
MOODS = {
    "mystery":  (45, MINOR, [0, 5, 2, 6], 70, {"pad": .9, "pulse": .35, "glock": .25}),
    "majesty":  (48, MAJOR, [0, 4, 5, 3], 76, {"pad": .9, "brass": .45, "glock": .35, "bass": .5}),
    "march":    (43, PHRYG, [0, 0, 1, 0], 96, {"pad": .6, "drum": .7, "brass": .5, "bass": .6, "pluck": .35}),
    "tension":  (45, MINOR, [0, 1, 5, 4], 88, {"pad": .7, "drum": .55, "bass": .6, "pulse": .4}),
    "build":    (47, MINOR, [0, 5, 3, 6], 100, {"pad": .7, "pluck": .55, "bass": .55, "drum": .35}),
    "drive":    (45, PHRYG, [0, 1, 0, 6], 112, {"pad": .7, "drum": .85, "brass": .55, "bass": .7, "pluck": .4}),
    "elegy":    (43, MINOR, [0, 5, 3, 4], 64, {"pad": 1.0, "brass": .4, "bass": .45}),
    "dawn":     (48, MAJOR, [0, 5, 3, 4], 70, {"pad": 1.0, "glock": .4, "bass": .4, "brass": .3}),
}


def chord(root, scale, deg):
    s = scale + [x + 12 for x in scale]
    return [root + s[deg], root + s[deg + 2], root + s[deg + 4]]


def bed(mood, dur, seed=1):
    root, scale, prog, bpm, L = MOODS[mood]
    beat = 60 / bpm; bar = beat * 4; n = int(dur * SR) + SR
    out = np.zeros(n); rng = np.random.default_rng(seed)
    nb = int(dur / bar) + 2
    for b in range(nb):
        t0 = b * bar; deg = prog[b % len(prog)]; ch = chord(root, scale, deg)
        if "pad" in L:
            for m in ch + [ch[0] + 12]: add(out, AU.pad(m, bar * 1.15, .25) * L["pad"] * .22, t0)
        if "bass" in L:
            add(out, AU.bass(ch[0] - 12, bar * .95) * L["bass"] * .5, t0)
        if "brass" in L and b % 2 == 0:
            add(out, AU.brass(ch[0] + 12, bar * 1.8, .7) * L["brass"] * .28, t0)
        if "pluck" in L:
            pat = [0, 2, 1, 2, 0, 2, 1, 2]
            for k in range(8): add(out, AU.pluck(ch[pat[k] % 3] + 12, beat * .6, .5, seed=b * 8 + k) * L["pluck"] * .3, t0 + k * beat / 2)
        if "drum" in L:
            for k in range(4):
                add(out, AU.frame_drum(True) * L["drum"] * (.55 if k == 0 else .35), t0 + k * beat)
                if bpm > 95: add(out, AU.frame_drum(False) * L["drum"] * .18, t0 + k * beat + beat / 2)
        if "pulse" in L:
            for k in range(2): add(out, AU.frame_drum(True) * L["pulse"] * .35, t0 + k * beat * 2)
        if "glock" in L and b % 2 == 1:
            for k, m in enumerate([ch[2] + 12, ch[1] + 12, ch[0] + 24]): add(out, AU.glock(m, 1.2) * L["glock"] * .2, t0 + k * beat)
    return out[: int(dur * SR)]


def score(n):
    plan = {"hook": "mystery", "city": "majesty", "sultan": "march", "chain": "mystery", "defeat": "tension",
            "plan": "build", "night": "drive", "change": "tension", "end": "elegy"}
    buf = np.zeros(n); xf = 1.2
    bounds = [(s["id"], s["start"]) for s in SECS] + [("_end", DUR)]
    for i, (sid, a) in enumerate(bounds[:-1]):
        b = bounds[i + 1][1]
        if sid == "end":   # the elegy turns into a sunrise at "Istanbul"
            parts = [(a, ws("end", 67), "elegy"), (ws("end", 67), b, "dawn")]
        elif sid == "hook":
            parts = [(0, a + 30.6, "mystery"), (a + 30.6, b, "majesty")]
        else:
            parts = [(a, b, plan[sid])]
        for k, (p0, p1, mood) in enumerate(parts):
            p0x = max(0.0, p0 - xf); seg = bed(mood, p1 - p0x + xf, seed=i * 7 + k); m = len(seg); env = np.ones(m); q = int(xf * SR)
            env[:q] = np.linspace(0, 1, q); env[-q:] = np.linspace(1, 0, q)
            add(buf, seg * env, p0x)
    return buf


# ------------------------------------------------------------------ procedural ambience and effects
def waves(d, seed=1):
    t = t_arr(d); x = lp(noise(d, seed), 500) * (.6 + .4 * np.sin(2 * np.pi * .23 * t) * np.sin(2 * np.pi * .11 * t + 1))
    return norm(x * np.minimum(1, t / .8) * np.minimum(1, (d - t) / .8), .4)


def haul(d, seed=2):
    t = t_arr(d); x = lp(noise(d, seed), 180) * 1.2
    knocks = (np.sin(2 * np.pi * 3.1 * t) > .85) * 1.0
    x += bp(noise(d, seed + 1), 300, 1200) * lp(knocks, 60) * 1.4
    return norm(x * np.minimum(1, t / .4) * np.minimum(1, (d - t) / .6), .6)


def boom(seed=0, big=1.0):
    t = t_arr(2.2); f = 55 * np.exp(-t * 3) + 32
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4) * 1.2 + lp(noise(2.2, seed), 700) * np.exp(-t * 3.5) * big
    return norm(x, .95)


def wind(d, seed=3):
    t = t_arr(d); x = bp(noise(d, seed), 200, 900) * (.5 + .5 * np.sin(2 * np.pi * .07 * t) ** 2)
    return norm(x * np.minimum(1, t / 1.5) * np.minimum(1, (d - t) / 1.5), .35)


def fire_crackle(d, seed=4):
    t = t_arr(d); rng = np.random.default_rng(seed); x = lp(noise(d, seed), 1200) * .3
    for k in range(int(d * 14)): add(x, AU.get_sfx("click") * rng.uniform(.2, .6), rng.uniform(0, d))
    return norm(x, .5)


def cues():
    C = []
    S = lambda s, i, d=0: ws(s, i) + d
    cr = lambda a, b, g=.25: [(a + k * 2.4, AU.get_sfx("crickets")[: int(2.5 * SR)], g) for k in range(int(max(0, b - a) / 2.4) + 1)]
    # ambience under whole stretches
    C += [(0, waves(34.0, 1), .35), (0, wind(34.0, 2), .25)]
    C += [(S("chain", 26), waves(S("chain", 89) - S("chain", 26), 5), .3), (S("defeat", 17), waves(S("defeat", 80) - S("defeat", 17), 6), .3)]
    C += [(S("night", 0), haul(S("night", 60) - S("night", 0), 7), .4)] + cr(S("night", 0), S("night", 60), .22)
    C += cr(S("defeat", 9), S("defeat", 17), .22) + cr(S("change", 37), S("change", 67), .2)
    C += [(S("end", 67), waves(DUR - S("end", 67), 9), .3)]
    # the hook
    C += [(S("hook", 14), AU.get_sfx("creak"), .2), (S("hook", 26), AU.music_sting("dun"), .4), (S("hook", 26), AU.get_sfx("gasp"), .3)]
    C += [(S("hook", 40), AU.get_sfx("clank"), .4), (S("hook", 62) + .4, boom(1, .6), .45)]
    # the city
    C += [(S("city", 64), AU.get_sfx("splash")[: int(.5 * SR)], .25), (S("city", 85), AU.get_sfx("splash"), .55), (S("city", 85) + .1, AU.get_sfx("boing"), .3)]
    C += [(S("city", 115), AU.get_sfx("murmur")[: int(3.0 * SR)], .2)]
    # the sultan
    C += [(S("sultan", 26), AU.get_sfx("ding"), .25), (S("sultan", 70), AU.get_sfx("wah")[: int(1.0 * SR)], .25), (S("sultan", 76), AU.get_sfx("sparkle"), .3)]
    for k in range(10): C.append((S("sultan", 81) + k * .6, AU.get_sfx("step_heavy"), .25))
    C += [(S("sultan", 92) + .3, AU.get_sfx("gulp")[: int(.6 * SR)], .25), (S("sultan", 99), AU.get_sfx("thud"), .4)]
    for k in range(16): C.append((S("sultan", 106) + k * .5, AU.get_sfx("step_heavy"), .2))
    # the chain
    C += [(S("chain", 8), AU.get_sfx("cheer")[: int(2.5 * SR)], .2), (S("chain", 44), AU.get_sfx("clank"), .4), (S("chain", 56), AU.get_sfx("clank"), .3)]
    # the defeat: three cannon shots, the rams, the supply ships, the furious ride, the chain lowered
    for ft in [S("defeat", 2), S("defeat", 6) + .2, S("defeat", 8) + .2]: C += [(ft, boom(int(ft), 1.0), .7), (ft + .7, AU.get_sfx("thud"), .45)]
    for k in range(8): C.append((S("defeat", 11) + k * .5, AU.get_sfx("thud"), .15))
    C += [(S("defeat", 21) - .05, AU.get_sfx("clank"), .55), (S("defeat", 21), AU.get_sfx("bonk"), .35), (S("defeat", 23), AU.music_sting("dun"), .3)]
    C += [(S("defeat", 39), AU.get_sfx("cheer"), .35), (S("defeat", 52), AU.get_sfx("splash"), .5), (S("defeat", 58), AU.get_sfx("growl")[: int(1.0 * SR)], .2)]
    C += [(S("defeat", 71), AU.get_sfx("clank"), .4), (S("defeat", 76), AU.get_sfx("cheer"), .3)]
    # the plan
    C += [(S("plan", 15), AU.get_sfx("ding"), .3), (S("plan", 32), AU.get_sfx("thud"), .25)]
    for k in range(6): C.append((S("plan", 58) + k * .45, AU.get_sfx("crash_wood"), .14))
    C += [(S("plan", 62), AU.get_sfx("poof"), .35)]
    for k in range(8): C.append((S("plan", 65) + k * .6, AU.get_sfx("thud"), .2))
    C += [(S("plan", 75), AU.get_sfx("slide_down"), .35), (S("plan", 76), AU.get_sfx("thud"), .3)]
    # the night
    C += [(S("night", 11), AU.get_sfx("creak"), .45), (S("night", 23), AU.get_sfx("creak"), .4), (S("night", 44), AU.get_sfx("flap"), .4), (S("night", 52), AU.get_sfx("swish"), .3)]
    for k in range(14): C.append((S("night", 56) + k * .4, AU.get_sfx("thud"), .3 if k < 7 else .18))
    for k in range(5): C.append((S("night", 62) + k * 1.3, AU.get_sfx("splash"), .3))
    C += [(S("night", 90), AU.music_sting("dun"), .3)]
    # the change
    C += [(S("change", 3), AU.get_sfx("clank"), .35), (S("change", 44), fire_crackle(8.0, 3), .35), (S("change", 58), boom(58, .8), .6), (S("change", 59), AU.get_sfx("splash"), .6)]
    for k in range(10): C.append((S("change", 73) + k * .5, AU.get_sfx("thud"), .15))
    for k in range(12): C.append((S("change", 78) + k * .45, AU.get_sfx("step"), .2))
    # the end
    C += [(S("end", 13), AU.get_sfx("cheer"), .35), (S("end", 13) + 2.5, AU.get_sfx("cheer"), .3)]
    for k in range(6): C.append((S("end", 14) + k * 1.4, boom(100 + k, .7), .35))
    C += [(S("end", 47), AU.get_sfx("creak"), .45), (S("end", 56), AU.music_sting("dun"), .3), (S("end", 68), AU.get_sfx("thud"), .2)]
    return C


def sfx_track(n):
    buf = np.zeros(n)
    for t, x, g in cues():
        add(buf, np.asarray(x, dtype=np.float64) * g * .5, max(0.0, t))
    return buf


def duck(music, voice, depth_db=8.0):
    env = AU.envelope_follow(voice, .05, .6); env = env / (env.max() + 1e-9)
    return music * 10 ** (-depth_db * np.clip(env * 3, 0, 1) / 20)


def build_audio():
    v, vsr = sf.read(os.path.join(ST, "voice", "voice.wav"))
    if v.ndim > 1: v = v.mean(1)
    v = AU.resample(v.astype(np.float64), vsr, SR) if vsr != SR else v
    n = int(DUR * SR) + 1
    voice = np.zeros(n); voice[: min(n, len(v))] = v[:n]
    music = duck(norm(score(n), .9), voice)
    sfx = sfx_track(n)
    mixw = voice * 1.0 + music * .2 + sfx * .5
    k = int(1.2 * SR); mixw[-k:] *= np.linspace(1, 0, k)
    os.makedirs(os.path.join(ST, "audio"), exist_ok=True)
    raw = os.path.join(ST, "audio", "mix_raw.wav")
    sf.write(raw, np.stack([mixw, mixw], 1).astype(np.float32), SR)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=9:print_format=json", "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=9:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=192000,alimiter=limit=0.75:level=false,aresample=48000")
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
        if x["word"][-1] in ".?!\"…" or len(cur) >= 9 or (x["word"][-1] in ",:" and len(cur) >= 5):
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
