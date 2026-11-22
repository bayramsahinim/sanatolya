"""Music sections + SFX (from shot cues) + voice -> loudness-normalised mix, SRT, final mux.

usage: python -m episodes.troy_en.mix audio     # build/troy_en/mix.wav + output SRT
       python -m episodes.troy_en.mix final     # mux with build/troy_en/video_silent.mp4 -> output/
"""
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

from cinecode import audio as A
from cinecode import tts
from cinecode.audio import SR, add, bp, env_adsr, exp_env, hp, lp, noise, norm, sweep, t_arr
from episodes.troy_en.render import CUES
from episodes.troy_en.shots import DUR, SHOTS, WS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "troy_en")
OUT_DIR = os.path.join(ROOT, "output")
NAME = "Just_Needy_The_Trojan_Horse_EN"


# ------------------------------------------------------------------ extra procedural sfx
def _hollow():
    """Big hollow wooden DONG: resonant low modes + knock."""
    d = 1.6
    t = t_arr(d)
    x = np.zeros_like(t)
    for f, a, tau in ((92, 1.0, 0.55), (147, 0.6, 0.4), (231, 0.35, 0.25), (365, 0.2, 0.15)):
        x += a * np.sin(2 * np.pi * f * t) * np.exp(-t / tau)
    knock = lp(noise(0.05, 3), 900) * exp_env(int(0.05 * SR), 0.015) * 1.5
    x[:len(knock)] += knock
    return norm(x, 0.9)


def _noise_env(d, lo, hi, a, r, seed):
    x = bp(noise(d, seed), lo, hi)
    return x * env_adsr(len(x), a, 0.05, 0.8, r)


def _gull():
    out = np.zeros(int(1.2 * SR))
    for k, t0 in enumerate((0.0, 0.35, 0.6)):
        s = sweep(2200, 1400, 0.22, "sine") * env_adsr(int(0.22 * SR), 0.01, 0.05, 0.7, 0.08) * 0.25
        add(out, s, t0)
    return out


def _waves(d=3.0):
    x = lp(noise(d, 21), 700)
    t = t_arr(d)
    return norm(x * (0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * t) ** 2), 0.5)


def _wind(d=3.0):
    t = t_arr(d)
    return norm(bp(noise(d, 22), 200, 900) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * t)), 0.4)


def _skid():
    d = 0.5
    x = bp(noise(d, 23), 1500, 5000) * exp_env(int(d * SR), 0.18)
    return norm(x, 0.6)


def _thunk():
    out = np.zeros(int(0.6 * SR))
    add(out, A.get_sfx("thud"), 0)
    add(out, A.get_sfx("click") * 0.6, 0)
    return norm(out, 0.9)


def _hiss():
    d = 1.2
    return norm(hp(noise(d, 24), 3500) * env_adsr(int(d * SR), 0.15, 0.1, 0.7, 0.4), 0.45)


def _rubble():
    out = np.zeros(int(2.0 * SR))
    add(out, A.get_sfx("crash_wood") * 0.6, 0)
    add(out, lp(noise(1.6, 25), 400) * exp_env(int(1.6 * SR), 0.5) * 1.2, 0)
    rng = np.random.default_rng(5)
    for k in range(14):
        add(out, A.get_sfx("thud") * rng.uniform(0.2, 0.5), rng.uniform(0.05, 1.3))
    return norm(out, 0.95)


def _scream():
    d = 0.9
    t = t_arr(d)
    f = 900 + 250 * np.sin(2 * np.pi * 7 * t) + 300 * t
    ph = np.cumsum(f) / SR
    x = (2 * (ph % 1) - 1)
    x = bp(x, 700, 3000) * env_adsr(len(t), 0.03, 0.1, 0.8, 0.25)
    return norm(x, 0.4)


def _sob():
    out = np.zeros(int(2.0 * SR))
    for k in range(5):
        d = 0.22
        t = t_arr(d)
        f = 420 - 120 * t / d
        x = bp(2 * ((np.cumsum(f) / SR) % 1) - 1, 400, 2200) * env_adsr(len(t), 0.02, 0.05, 0.7, 0.08)
        add(out, x * 0.35, k * 0.34)
    return out


def _horn():
    out = np.zeros(int(2.0 * SR))
    add(out, A.brass(43, 1.6, 0.8) + A.brass(55, 1.6, 0.6) * 0.5, 0)
    return norm(out, 0.7)


def _choir():
    out = np.zeros(int(2.4 * SR))
    for m in (60, 64, 67, 72, 76):
        add(out, A.pad(m, 2.2, 0.5), 0)
    return norm(out, 0.5)


def _slap():
    x = hp(noise(0.08, 26), 1200) * exp_env(int(0.08 * SR), 0.015)
    out = np.zeros(int(0.5 * SR))
    add(out, x * 1.0, 0)
    add(out, A.get_sfx("thud") * 0.5, 0)
    return norm(out, 0.9)


def _mmmf():
    d = 0.7
    t = t_arr(d)
    f = 160 + 30 * np.sin(2 * np.pi * 5 * t)
    x = lp(2 * ((np.cumsum(f) / SR) % 1) - 1, 500) * env_adsr(len(t), 0.02, 0.1, 0.8, 0.2)
    return norm(x, 0.45)


def _inhale():
    d = 0.6
    return norm(bp(noise(d, 27), 800, 4000) * np.linspace(0, 1, int(d * SR)) ** 2, 0.35)


def _oars():
    out = np.zeros(int(2.5 * SR))
    for k in range(4):
        add(out, A.get_sfx("splash")[: int(0.5 * SR)] * 0.4, k * 0.6)
    return out


def _ram():
    out = np.zeros(int(0.8 * SR))
    add(out, A.get_sfx("thud") * 1.0, 0)
    add(out, A.get_sfx("bonk") * 0.5, 0)
    return norm(out, 0.9)


def _measure():
    out = np.zeros(int(0.6 * SR))
    add(out, A.get_sfx("slide_up") * 0.6, 0)
    add(out, A.get_sfx("click") * 0.6, 0.35)
    return out


def _sail():
    return A.get_sfx("flap")


MAP = {
    "wind": _wind, "creak": lambda: A.get_sfx("creak"), "gull": _gull, "pop": lambda: A.get_sfx("pop"),
    "sparkle": lambda: A.get_sfx("sparkle"), "waves": _waves, "sail": _sail,
    "gate": lambda: A.get_sfx("creak"), "crowd_run": lambda: A.get_sfx("cheer"), "skid": _skid,
    "step": lambda: A.get_sfx("step_heavy"), "whoosh": lambda: A.get_sfx("whoosh"), "thunk": _thunk,
    "boing_wood": lambda: A.get_sfx("boing"), "dong": _hollow, "gulp": lambda: A.get_sfx("gulp"),
    "sting": lambda: A.music_sting("dun"), "rustle": lambda: _noise_env(1.2, 2000, 7000, 0.05, 0.4, 28),
    "drag": lambda: _noise_env(1.6, 150, 900, 0.1, 0.4, 29), "sob": _sob, "violin": _choir,
    "measure": _measure, "ding": lambda: A.get_sfx("ding"), "sting_low": lambda: A.music_sting("dun"),
    "splash": lambda: A.get_sfx("splash"), "hiss": _hiss, "squeeze": lambda: A.get_sfx("slide_down"),
    "yank": lambda: A.get_sfx("slide_up"), "crickets": lambda: A.get_sfx("crickets"), "choir": _choir,
    "rope_pull": lambda: A.get_sfx("creak"), "wood_roll": lambda: A.get_sfx("cart"),
    "bonk_big": lambda: A.get_sfx("bonk"), "pick": lambda: A.get_sfx("clank"), "rubble": _rubble,
    "festival": lambda: A.get_sfx("murmur"), "scream": _scream, "crowd_cheer": lambda: A.get_sfx("cheer"),
    "thunder_small": lambda: A.get_sfx("thunder")[: int(1.2 * SR)], "night_amb": lambda: A.get_sfx("crickets"),
    "voice_honey": lambda: A.get_sfx("sparkle"), "voice_honey_far": lambda: A.get_sfx("ooh")[: int(1.0 * SR)],
    "inhale": _inhale, "slap": _slap, "mmmf": _mmmf, "rope_drop": lambda: A.get_sfx("thud"),
    "gate_heavy": lambda: A.get_sfx("creak"), "horn": _horn, "oars": _oars, "ram": _ram,
}
GAIN = {"crowd_run": 0.35, "festival": 0.35, "crowd_cheer": 0.4, "violin": 0.35, "choir": 0.45, "wind": 0.6,
        "waves": 0.7, "crickets": 0.6, "night_amb": 0.5, "sting": 0.55, "sting_low": 0.6, "rubble": 0.8,
        "dong": 0.95, "horn": 0.55}


def sfx_track(n):
    buf = np.zeros(n)
    for sh in SHOTS:
        for t, name, g in sh.sfx:
            x = np.asarray(MAP[name](), dtype=np.float64)
            T = sh.t0 + t
            if T >= sh.t1 + 0.6:
                continue
            add(buf, x * g * GAIN.get(name, 1.0) * 0.5, max(0.0, T))
    return buf


# ------------------------------------------------------------------ music
def music_track(n):
    sections = [  # (start, end, loop, gain)
        (0.0, WS("snakes", 0), "market", 0.55),
        (WS("snakes", 0), WS("walls", 0), "suspense", 0.6),
        (WS("walls", 0), WS("helen", 0), "festival", 0.5),
        (WS("helen", 0), WS("end", 0), "suspense", 0.45),
        (WS("end", 0), DUR, "quirky", 0.6),
    ]
    buf = np.zeros(n)
    xf = 0.25
    for a, b, name, g in sections:
        a0 = max(0.0, a - xf)
        seg = A.track(name, b - a0 + xf)
        m = len(seg)
        env = np.ones(m)
        k = int(xf * SR)
        env[:k] = np.linspace(0, 1, k)
        env[-k:] = np.linspace(1, 0, k)
        add(buf, seg * env * g, a0)
    # final button: tada on the last word end
    add(buf, A.music_sting("tada") * 0.55, WS("end", 15) + 0.55)
    return buf


def duck(music, voice, depth_db=9.0):
    env = A.envelope_follow(voice, 0.03, 0.4)
    env = env / (env.max() + 1e-9)
    g = 10 ** (-depth_db * np.clip(env * 3, 0, 1) / 20)
    return music * g


def build_audio():
    v = tts.read_wav(os.path.join(BUILD, "voice.wav")).astype(np.float64)
    v = A.resample(v, tts.SR, SR)
    n = int(DUR * SR) + 1
    voice = np.zeros(n)
    voice[:min(n, len(v))] = v[:n]
    music = music_track(n)
    sfx = sfx_track(n)
    music = duck(music, voice)
    mixw = voice * 1.0 + music * 0.22 + sfx * 0.55
    # gentle fade out
    k = int(0.6 * SR)
    mixw[-k:] *= np.linspace(1, 0, k)
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, np.stack([mixw, mixw], 1).astype(np.float32), SR)
    out = os.path.join(BUILD, "mix.wav")
    # two-pass loudness normalisation to -14 LUFS, -1 dBTP
    import json
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af",
                        "loudnorm=I=-14:TP=-1.2:LRA=7:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    m = json.loads(js)
    af = (f"loudnorm=I=-14:TP=-1.2:LRA=7:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    print("mix", out)
    write_srt()


def _ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s - int(s)) * 1000):03d}"


def write_srt():
    cues, cur = [], []
    for s, e, w in CUES:
        cur.append((s, e, w))
        if w[-1] in ".?!" or len(cur) >= 7 or (w[-1] in ",:" and len(cur) >= 4):
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    os.makedirs(OUT_DIR, exist_ok=True)
    p = os.path.join(OUT_DIR, NAME + ".en.srt")
    with open(p, "w") as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{_ts(c[0][0])} --> {_ts(c[-1][1])}\n{' '.join(w for _, _, w in c)}\n\n")
    print("srt", p)


def final():
    out = os.path.join(OUT_DIR, NAME + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(BUILD, "video_silent.mp4"), "-i",
                    os.path.join(BUILD, "mix.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("final", out)


if __name__ == "__main__":
    {"audio": build_audio, "final": final}[sys.argv[1]]()
