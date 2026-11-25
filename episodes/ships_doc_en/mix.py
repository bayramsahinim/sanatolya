"""Sound for the tight Ships documentary (ships-doc-en): narration + a cinematic score per section + word-pinned SFX -> -14 LUFS, SRT, mux.

The score is composed here from cinecode.audio instruments (pads, brass, bass, plucks, frame drums): calmer and more
cinematic than the Shorts' comic beds, one mood per section, crossfaded at the section gaps.
usage (repo root): python3 -m episodes.ships_doc_en.mix audio   # yumurta/stories/ships-doc-en/audio/mix.wav + SRT
                   python3 -m episodes.ships_doc_en.mix final   # concat the rendered parts, mux -> output/
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
ST = os.path.join(ROOT, "yumurta", "stories", "ships-doc-en")
OUT_DIR = os.path.join(ROOT, "output")
NAME = "ShipsOverHill_Doc_EN"
WORDS = json.load(open(os.path.join(ST, "voice", "words.json")))["words"]
SECS = json.load(open(os.path.join(ST, "voice", "sections.json")))
SEC = {}
for x in WORDS: SEC.setdefault(x["sec"], []).append(x)
ws = lambda s, i: SEC[s][min(i, len(SEC[s]) - 1)]["start"]
DUR = np.ceil((WORDS[-1]["end"] + 4.5) * 30) / 30


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
    plan = {"setup": "march", "chain": "mystery", "defeat": "tension", "plan": "build", "night": "drive"}
    we = lambda s_, i: SEC[s_][min(i, len(SEC[s_]) - 1)]["end"]
    buf = np.zeros(n); xf = 1.0
    bounds = [(s_["id"], s_["start"]) for s_ in SECS] + [("_end", DUR)]
    for i, (sid, a) in enumerate(bounds[:-1]):
        b = bounds[i + 1][1]
        if sid == "hook":
            parts = [(0, we("hook", 72) + .25, "mystery"), (we("hook", 72) + .25, b, "majesty")]
        elif sid == "end":
            parts = [(a, ws("end", 55), "tension"), (ws("end", 55), ws("end", 80), "drive"), (ws("end", 80), ws("end", 104), "elegy"), (ws("end", 104), b, "dawn")]
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
    S = lambda s_, i, d=0: ws(s_, i) + d
    we = lambda s_, i: SEC[s_][min(i, len(SEC[s_]) - 1)]["end"]
    cr = lambda a, b, g=.25: [(a + k * 2.4, AU.get_sfx("crickets")[: int(2.5 * SR)], g) for k in range(int(max(0, b - a) / 2.4) + 1)]
    # ambience
    C += [(0, waves(S("setup", 0), 1), .35), (0, wind(S("setup", 0), 2), .22)]
    C += [(S("chain", 11), waves(S("defeat", 74) - S("chain", 11), 5), .28)]
    C += [(S("night", 0), haul(S("night", 86) - S("night", 0), 7), .4)] + cr(S("night", 0), S("night", 86), .22) + cr(S("end", 32), S("end", 45), .2)
    C += [(S("end", 104), waves(DUR - S("end", 104), 9), .3)]
    # hook
    C += [(S("hook", 24), AU.music_sting("dun"), .4), (S("hook", 24), AU.get_sfx("gasp"), .3), (S("hook", 40), AU.get_sfx("clank"), .4), (we("hook", 72) + .25, boom(1, .6), .45)]
    # setup
    C += [(S("setup", 54), AU.get_sfx("splash")[: int(.5 * SR)], .2)]
    for k in range(10): C.append((S("setup", 75) + k * .5, AU.get_sfx("step_heavy"), .2))
    for k in range(8): C.append((S("setup", 81) + k * .6, AU.get_sfx("step_heavy"), .22))
    C += [(S("setup", 94), boom(94, 1.0), .7), (S("setup", 94) + .7, AU.get_sfx("thud"), .45)]
    # chain
    C += [(S("chain", 11), AU.get_sfx("cheer")[: int(2.5 * SR)], .18), (S("chain", 36), AU.get_sfx("clank"), .4), (S("chain", 49), AU.get_sfx("clank"), .3)]
    # defeat
    C += [(S("defeat", 5) - .05, AU.get_sfx("clank"), .55), (S("defeat", 8), AU.music_sting("dun"), .3)]
    C += [(S("defeat", 26), AU.get_sfx("cheer"), .35), (S("defeat", 40), AU.get_sfx("splash"), .5), (S("defeat", 46), AU.get_sfx("growl")[: int(1.0 * SR)], .2)]
    C += [(S("defeat", 52), AU.get_sfx("clank"), .4), (S("defeat", 57), AU.get_sfx("cheer"), .3), (S("defeat", 63), AU.get_sfx("clank"), .35)]
    # plan
    C += [(S("plan", 8), AU.get_sfx("clank"), .25), (S("plan", 21), AU.get_sfx("ding"), .3)]
    C += [(S("plan", 48), AU.get_sfx("poof"), .35)]
    for k in range(6): C.append((S("plan", 45) + k * .45, AU.get_sfx("crash_wood"), .14))
    for k in range(8): C.append((S("plan", 50) + k * .6, AU.get_sfx("thud"), .2))
    # night
    C += [(S("night", 12), AU.get_sfx("creak"), .45), (S("night", 35), AU.get_sfx("creak"), .45), (S("night", 60), AU.get_sfx("flap"), .4)]
    for k in range(14): C.append((S("night", 56) + k * .4, AU.get_sfx("thud"), .25 if k < 7 else .15))
    for k in range(4): C.append((S("night", 81) + k * 1.2, AU.get_sfx("splash"), .3))
    C += [(S("night", 89), AU.music_sting("dun"), .3)]
    # end
    C += [(S("end", 3), AU.get_sfx("clank"), .35), (S("end", 32), fire_crackle(6.0, 3), .35), (S("end", 42), boom(42, .8), .6), (S("end", 43), AU.get_sfx("splash"), .6)]
    for k in range(10): C.append((S("end", 46) + k * .45, AU.get_sfx("thud"), .15))
    C += [(S("end", 60), AU.get_sfx("cheer"), .35), (S("end", 60) + 2.5, AU.get_sfx("cheer"), .3)]
    for k in range(5): C.append((S("end", 61) + k * 1.3, boom(100 + k, .7), .32))
    C += [(S("end", 76), AU.get_sfx("thud"), .25), (S("end", 82), AU.music_sting("dun"), .3)]
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
    mixw = voice * 1.0 + music * .24 + sfx * .5
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
