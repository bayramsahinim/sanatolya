"""Sound design + score + mix for 'He Survived 60 Hours Underwater' (48 kHz, numpy).

Everything is synthesised procedurally and placed on the same marks the picture uses
(shot cuts + aligned narration words), so SFX land on the visible actions.
Mix: narration is the reference level; score is side-chain ducked under the voice;
loudness normalised to ~-14 LUFS-ish (RMS based) with a peak ceiling of -1 dBFS.
"""
import math

import numpy as np
import soundfile as sf
from scipy import signal

from cinecode.audio import SR, bp, exp_env, hp, lp, noise, t_arr
from .episode import BUILD, Episode
from . import shots_a as A
from . import shots_b as B

RNG = np.random.default_rng(2013)


def place(buf, x, t, g=1.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    if i < 0:
        x = x[-i:]
        i = 0
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n] * g


def fadeio(x, a=0.01, b=0.05):
    na, nb = int(a * SR), int(b * SR)
    x = x.copy()
    if na:
        x[:na] *= np.linspace(0, 1, na)
    if nb:
        x[-nb:] *= np.linspace(1, 0, nb)
    return x


def db(v):
    return 10 ** (v / 20)


# ------------------------------------------------------------------ sources
def rumble(d, seed=0, f=180):
    return lp(noise(d, seed), f, 4) * 3.0


def underwater_bed(d, seed=1):
    """deep muffled pressure + slow swells + faint distant groans."""
    n = rumble(d, seed, 140)
    t = t_arr(d)
    sw = 0.65 + 0.35 * np.sin(2 * np.pi * 0.07 * t + seed)
    hiss = bp(noise(d, seed + 5), 300, 900) * 0.12 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * t))
    return (n * sw + hiss)


def creak(d=1.4, f0=220, f1=160, seed=0):
    """metal groan: resonant, slightly stuttering band-passed sawtooth."""
    t = t_arr(d)
    f = f0 * (f1 / f0) ** (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = signal.sawtooth(ph) * (0.6 + 0.4 * (np.sin(2 * np.pi * 13 * t + seed) > -0.2))
    x = bp(saw, f0 * 0.8, f0 * 4) + 0.3 * bp(noise(d, seed), 200, 1200)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
    return lp(x * env, 1500) * 0.6


def boom(d=2.0, f=48, seed=0):
    t = t_arr(d)
    sub = np.sin(2 * np.pi * (f * (1 + 0.6 * np.exp(-t * 6))) * t) * np.exp(-t * 2.2)
    body = lp(noise(d, seed), 400, 2) * np.exp(-t * 5) * 0.8
    return (sub + body)


def hit(d=1.6, seed=3):
    """cinematic impact for the hand grab: transient + boom + metallic ring."""
    t = t_arr(d)
    trans = hp(noise(d, seed), 1500) * np.exp(-t * 60) * 0.7
    ring = sum(np.sin(2 * np.pi * fr * t + k) for k, fr in enumerate((311, 467, 733))) * np.exp(-t * 3.5) * 0.12
    return lp(trans, 6000) + boom(d, 42, seed) * 1.1 + ring


def whoosh(d=0.6, up=True, seed=0):
    t = t_arr(d)
    x = noise(d, seed)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    lo, hi = (300, 2400) if up else (2400, 300)
    out = np.zeros_like(x)
    seg = 8
    L = len(x) // seg
    for k in range(seg):
        fc = lo * (hi / lo) ** (k / (seg - 1))
        sl = slice(k * L, (k + 1) * L if k < seg - 1 else len(x))
        out[sl] = bp(x, fc * 0.6, fc * 1.6)[sl]
    return out * env * 1.2


def bubbles(d=1.0, rate=14, seed=0, lo=500, hi=1600):
    rng = np.random.default_rng(seed)
    out = np.zeros(int(d * SR))
    for _ in range(int(d * rate)):
        st = rng.uniform(0, d - 0.06)
        bd = rng.uniform(0.02, 0.06)
        tt = t_arr(bd)
        f0 = rng.uniform(lo, hi)
        b = np.sin(2 * np.pi * f0 * (1 + tt * 18) * tt) * np.exp(-tt * 70) * rng.uniform(0.3, 1)
        place(out, b, st)
    return lp(out, 2500) * 0.5


def regulator(d, seed=0, period=3.2):
    """diver helmet breathing: hissy inhale + bubbly exhale."""
    out = np.zeros(int(d * SR))
    t = 0.0
    k = 0
    while t < d:
        inh = bp(noise(0.9, seed + k), 900, 4000) * np.sin(np.pi * np.clip(t_arr(0.9) / 0.9, 0, 1)) ** 2 * 0.25
        place(out, inh, t)
        place(out, bubbles(1.0, 24, seed + k, 300, 900) * 0.8, t + 1.2)
        t += period
        k += 1
    return out


def human_breath(d=0.8, seed=0, gasp=False, inhale=True):
    t = t_arr(d)
    x = bp(noise(d, seed), 500 if gasp else 350, 3500 if gasp else 2200)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** (0.6 if gasp else 1.5)
    if gasp:
        env *= 1 + 1.5 * np.exp(-t * 10)
    return x * env * (0.5 if gasp else 0.25)


def water_rush(d=2.0, seed=0):
    t = t_arr(d)
    x = lp(noise(d, seed), 1800, 2) + 0.4 * bp(noise(d, seed + 1), 2000, 6000)
    return x * np.clip(t / 0.15, 0, 1) * 0.6


def splash_s(d=1.0, seed=0):
    t = t_arr(d)
    return (bp(noise(d, seed), 400, 5000) * np.exp(-t * 6) * 0.8 + bubbles(d, 30, seed) * 0.8)


def rain(d, seed=0):
    return (bp(noise(d, seed), 2000, 9000) * 0.18 + lp(noise(d, seed + 1), 300) * 0.5)


def waves(d, seed=0):
    t = t_arr(d)
    sw = 0.5 + 0.5 * np.sin(2 * np.pi * 0.35 * t) ** 2
    return lp(noise(d, seed), 700, 2) * sw * 1.2


def thunder(d=3.0, seed=0):
    t = t_arr(d)
    x = lp(noise(d, seed), 300, 2) * (np.exp(-t * 1.2) + 0.4 * np.exp(-((t - 0.4) / 0.2) ** 2))
    return x * 2.0


def tick(f=2200, d=0.05):
    t = t_arr(d)
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 90) * 0.5


def heartbeat(d=0.9):
    t = t_arr(d)
    b1 = np.sin(2 * np.pi * 52 * t) * np.exp(-t * 18)
    t2 = np.clip(t - 0.22, 0, None)
    b2 = np.sin(2 * np.pi * 46 * t2) * np.exp(-t2 * 16) * (t > 0.22) * 0.75
    return (b1 + b2) * 1.2


def clank(d=2.2, seed=0):
    """distant metallic knock heard through the hull."""
    t = t_arr(d)
    tone = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * (2 + k)) for k, f in enumerate((180, 262, 397, 590)))
    return lp(tone * 0.3 + noise(d, seed) * np.exp(-t * 40) * 0.5, 1200)


def riser(d=1.2, seed=0):
    t = t_arr(d)
    f = 200 * (8 ** (t / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15
    return (tone + whoosh(d, True, seed) * 0.6) * (t / d) ** 2


# ------------------------------------------------------------------ score
def note(m):
    return 440 * 2 ** ((m - 69) / 12)


def pad_tone(m, d, bright=0.25, seed=0):
    t = t_arr(d)
    f = note(m)
    x = np.zeros_like(t)
    for k, det in enumerate((-0.12, 0.0, 0.11)):
        ph = 2 * np.pi * f * (1 + det / 100) * t
        x += signal.sawtooth(ph + k) * 0.33
    x = lp(x, 300 + 1800 * bright)
    env = np.clip(t / 0.8, 0, 1) * np.clip((d - t) / 0.8, 0, 1)
    return x * env


def score(dur, marks):
    """Dark ticking pulse + drones through the story, swelling to a warm resolve at the rescue."""
    out = np.zeros(int(dur * SR) + SR)
    # drone bed in D minor
    drone = pad_tone(38, dur, 0.15) * 0.5 + pad_tone(45, dur, 0.1) * 0.25
    t = t_arr(dur)
    drone *= 0.6 + 0.4 * np.clip(t / 3, 0, 1)
    place(out, drone, 0)
    # pulse: low tom-ish thump on every beat, 96 bpm, from hook end to the rescue
    beat = 60 / 96
    tb = marks["pulse_on"]
    while tb < marks["rescue"] - 0.2:
        x = boom(0.5, 60, int(tb * 10)) * 0.35
        place(out, x, tb)
        place(out, tick(1800, 0.04) * 0.25, tb + beat / 2)
        tb += beat
    # tension chord swells for the science/wait section
    for (a, b, chord) in ((marks["science"], marks["wait"], (50, 53, 57)), (marks["wait"], marks["rescue"], (49, 52, 56))):
        for m in chord:
            place(out, pad_tone(m, b - a + 0.8, 0.3) * 0.18, a)
    # warm resolve: D major lift from "they found a survivor" to the end
    r = marks["rescue"]
    for m in (50, 54, 57, 62, 66):
        place(out, pad_tone(m, dur - r + 0.5, 0.45) * 0.17, r)
    place(out, boom(2.5, 40, 9) * 0.5, r)
    return out


def limit(x, ceil, look=0.005, rel=0.08):
    """look-ahead peak limiter: gain = min(1, ceil/peak) over a sliding window, smooth release."""
    from scipy.ndimage import maximum_filter1d
    w = int(look * SR) * 2 + 1
    pk = maximum_filter1d(np.abs(x), w)
    g = np.minimum(1.0, ceil / (pk + 1e-9))
    a = math.exp(-1 / (rel * SR))
    # release smoothing (attack is instant thanks to the look-ahead window)
    g = signal.lfilter([1 - a], [1, -a], g - 1) + 1
    g = np.minimum(g, ceil / (pk + 1e-9))
    return x * g


# ------------------------------------------------------------------ build
def build():
    ep = Episode()
    V = ep.V
    dur = ep.duration
    N = int(dur * SR) + SR
    sfx = np.zeros(N)
    amb = np.zeros(N)
    S = {type(s).__name__: s for s in ep.shots}

    def span(name):
        s = S[name]
        return s.t0, s.t1

    # --- beds per scene (underwater vs storm vs pocket)
    under = [("S1a", "S3b"), ("S7a", "S7a"), ("S14b", "S16"), ("S18b", "S18b")]
    order = [type(s).__name__ for s in ep.shots]

    def rng_(a, b):
        return S[a].t0, S[b].t1

    for a, b in under:
        t0, t1 = rng_(a, b)
        x = fadeio(underwater_bed(t1 - t0 + 0.3, seed=int(t0)), 0.05, 0.3)
        place(amb, x, t0, 0.55)
        place(amb, fadeio(regulator(t1 - t0, seed=int(t0)), 0.05, 0.2), t0, 0.5)
    # air pocket room tone: close, damp, lapping water
    for a, b in (("S2", "S2"), ("S7b", "S7b"), ("S9a", "S14a"), ("S17", "S18a")):
        t0, t1 = rng_(a, b)
        d = t1 - t0 + 0.2
        lap = lp(noise(d, int(t0) + 3), 600, 2) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.6 * t_arr(d)) ** 4)
        place(amb, fadeio(rumble(d, int(t0), 120) * 0.5 + lap * 0.6, 0.03, 0.2), t0, 0.5)
    # the cutaway shot: soft deep bed
    t0, t1 = span("S8")
    place(amb, fadeio(underwater_bed(t1 - t0, 9), 0.05, 0.2), t0, 0.35)
    # storm
    t0, t1 = rng_("S4", "S5")
    d = t1 - t0
    place(amb, fadeio(rain(d, 4) + waves(d, 5), 0.02, 0.3), t0, 0.32)
    place(sfx, thunder(3.0, 7), t0 + 0.4, 0.28)
    # flooding corridor
    t0, t1 = span("S6")
    place(amb, fadeio(water_rush(t1 - t0 + 0.2, 6), 0.02, 0.15), t0, 0.7)

    # --- hook
    place(sfx, creak(1.6, 240, 150, 1), 0.2, 0.3)
    place(sfx, whoosh(0.5, True, 2), S["S1b"].t0 - 0.25, 0.35)
    grab = V.w("grabbed")
    place(sfx, hit(2.2, 3) * np.exp(-t_arr(2.2) * 1.2), grab - 0.01, 0.75)
    place(sfx, bubbles(1.4, 60, 4, 300, 1200) * 1.5, grab, 0.45)
    place(sfx, human_breath(0.5, 1, gasp=True), S["S1d"].t0 + 0.05, 0.5)  # diver's startled gasp in helmet
    place(sfx, bubbles(1.0, 50, 5) * 1.3, S["S1d"].t0, 0.35)
    # reveal
    place(sfx, whoosh(0.4, False, 6), S["S2"].t0 - 0.15, 0.3)
    place(sfx, splash_s(0.8, 7), S["S2"].t0 + 0.05, 0.35)
    place(sfx, human_breath(0.7, 8, gasp=True), S["S2"].t0 + 0.6, 0.35)
    # exterior wreck
    place(sfx, creak(2.4, 120, 90, 10), S["S3a"].t0 + 0.2, 0.6)
    place(sfx, bubbles(2.0, 10, 11, 400, 900), S["S3b"].t0, 0.7)
    # flashback whoosh + flash
    place(sfx, riser(0.9, 12), S["S4"].t0 - 0.85, 0.45)
    place(sfx, whoosh(0.6, False, 13), S["S4"].t0 - 0.1, 0.5)
    # capsize: crash of the swell, hull groan, roll
    roll = S["S5"].t0 + S["S5"].roll
    place(sfx, boom(2.6, 38, 14) * 1.2, roll + 0.35, 0.5)
    place(sfx, splash_s(1.6, 15) * 1.4, roll + 0.45, 0.45)
    place(sfx, creak(1.8, 160, 70, 16), roll - 0.3, 0.45)
    # interior flooding
    place(sfx, creak(1.2, 300, 200, 17), S["S6"].t0, 0.5)
    place(sfx, whoosh(0.5, True, 18), S["S7a"].t0 - 0.2, 0.3)
    place(sfx, bubbles(1.3, 25, 19), S["S7a"].t0, 0.8)
    br = S["S7b"].t0 + S["S7b"].breach
    place(sfx, splash_s(1.0, 20), br, 0.6)
    place(sfx, human_breath(0.9, 21, gasp=True), br + 0.1, 0.65)
    place(sfx, human_breath(0.8, 22, gasp=True), br + 1.0, 0.4)
    # science
    place(sfx, whoosh(0.5, True, 23), S["S8"].t0 - 0.2, 0.3)
    place(sfx, water_rush(1.2, 24) * fadeio(np.ones(int(1.2 * SR)), 0.02, 0.6), S["S8"].t0, 0.25)
    lab = S["S8"].t0 + S["S8"].label_t
    place(sfx, tick(1400, 0.08), lab, 0.4)
    for k in range(3):   # calm breathing in the pocket
        place(sfx, human_breath(1.0, 30 + k), S["S9a"].t0 + k * 1.15, 0.45)
    place(sfx, boom(2.0, 36, 31) * 0.6, S["S9c"].t0, 0.5)     # "but only temporarily" - ominous low hit
    # O2: soft blips as molecules disappear
    s10 = S["S10"]
    for i in range(14):
        place(sfx, tick(1200 + 40 * i, 0.06), s10.t0 + 0.15 + i * 0.075, 0.18)
    place(sfx, human_breath(0.9, 32), s10.t0 + 0.1, 0.45)
    # CO2: exhale + thickening low swell
    s11 = S["S11"]
    place(sfx, human_breath(1.1, 33, inhale=False), s11.t0, 0.5)
    place(sfx, pad_tone(41, s11.dur + 0.3, 0.2) * np.linspace(0, 1, int((s11.dur + 0.3) * SR)) * 0.25, s11.t0)
    # water rising: lapping + creak
    place(sfx, creak(2.2, 200, 140, 34), S["S12"].t0 + 0.2, 0.4)
    # time passing: heartbeat in the dark
    t = S["S13a"].t0
    while t < S["S14a"].t1 - 0.4:
        place(sfx, heartbeat(), t, 0.55)
        t += 1.05
    place(sfx, human_breath(1.2, 35), S["S13b"].t0 + 0.2, 0.35)
    clank_t = S["S14a"].t0 + S["S14a"].clank
    place(sfx, clank(2.2, 36), clank_t, 0.7)
    # divers enter
    place(sfx, whoosh(0.5, True, 37), S["S14b"].t0 - 0.2, 0.3)
    place(sfx, creak(1.5, 260, 180, 38), S["S15"].t0 + 0.3, 0.4)
    place(sfx, riser(1.0, 39), S["S16"].t0, 0.4)
    # discovery
    r = S["S17"].t0
    place(sfx, splash_s(1.0, 40), r, 0.7)
    place(sfx, hit(1.8, 41) * 0.7, S["S17"].t0 + S["S17"].grab, 0.6)
    place(sfx, human_breath(0.8, 42, gasp=True), r + 0.2, 0.4)
    place(sfx, bubbles(3.0, 14, 43), S["S18b"].t0, 0.6)

    marks = {"pulse_on": S["S2"].t0, "science": S["S8"].t0, "wait": S["S13a"].t0, "rescue": S["S17"].t0}
    mus = score(dur, marks)

    # --- narration + ducking
    nar, sr = sf.read(f"{BUILD}/narration.wav")
    assert sr == SR
    voice = np.zeros(N)
    voice[:len(nar)] = nar
    env = np.abs(voice)
    env = lp(env, 6, 1)
    env = env / (env.max() + 1e-9)
    gate = np.clip(env * 6, 0, 1)
    # smooth attack/release
    k = int(0.25 * SR)
    gate = np.convolve(gate, np.ones(k) / k, mode="same")
    duck = 1 - 0.6 * np.clip(gate, 0, 1)          # ~ -8 dB under speech
    duck_amb = 1 - 0.6 * np.clip(gate, 0, 1)      # ~ -8 dB under speech

    vr = np.sqrt(np.mean(nar[np.abs(nar) > 0.02] ** 2))
    voice_n = voice / vr * db(-18)
    mix = (voice_n
           + sfx / (np.sqrt(np.mean(sfx ** 2)) + 1e-9) * db(-27) * duck_amb
           + amb / (np.sqrt(np.mean(amb ** 2)) + 1e-9) * db(-31) * duck_amb
           + mus / (np.sqrt(np.mean(mus ** 2)) + 1e-9) * db(-29) * duck)
    mix = mix[:int(dur * SR)]
    # gentle fade-out on the final frames
    fo = int(0.6 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)
    # loudness: +2.2 dB (measured -16.2 LUFS -> ~-14 LUFS for Shorts), then a look-ahead peak limiter
    mix = limit(mix * db(2.2), db(-2.0))
    sf.write(f"{BUILD}/mix.wav", np.stack([mix, mix], 1).astype(np.float32), SR, subtype="PCM_24")
    # stems for QA
    sf.write(f"{BUILD}/stem_voice.wav", voice_n[:len(mix)].astype(np.float32), SR)
    print("mix", f"{BUILD}/mix.wav", round(len(mix) / SR, 2), "s  peak", round(float(np.max(np.abs(mix))), 3))


if __name__ == "__main__":
    build()
