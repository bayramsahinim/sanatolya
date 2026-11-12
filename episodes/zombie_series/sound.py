"""Series sound identity for Just Needy — Zombie Apocalypse (procedural, 48 kHz, reproducible).

Everything here is synthesised with numpy/scipy so every episode sounds the same:
SFX (rooster, groans, creaks, power failure, faucet ...), two music beds ("dread",
"confident") and three ambience beds ("farm", "house", "house_dark").
"""
import functools
import math

import numpy as np
from scipy import signal

from cinecode import audio as A
from cinecode.audio import SR, add, bp, exp_env, fade, hp, lp, noise, norm, t_arr


# ------------------------------------------------------------------ helpers
def reverb(x, t60=1.2, wet=0.3, seed=0, pre=0.012, tone=5000):
    """Cheap convolution reverb (decaying filtered noise IR)."""
    n = int(t60 * SR)
    r = np.random.default_rng(seed)
    ir = r.standard_normal(n) * np.exp(-6.9 * np.arange(n) / n)
    ir = lp(ir, tone)
    ir[: int(pre * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum()) + 1e-9
    y = signal.fftconvolve(x, ir)[: len(x) + n]
    out = np.zeros(len(x) + n)
    out[: len(x)] += x * (1 - wet)
    out[: len(y)] += y * wet * 1.4
    return out


def formants(src, fs_bw, gains=None):
    out = np.zeros_like(src)
    gains = gains or [1.0] * len(fs_bw)
    for (f, bw), g in zip(fs_bw, gains):
        out += bp(src, max(30, f - bw / 2), min(SR / 2 - 200, f + bw / 2), 2) * g
    return out


def glottal(f0, jitter=0.0, seed=0):
    """Band-limited-ish sawtooth following the f0 contour array (Hz)."""
    r = np.random.default_rng(seed)
    if jitter:
        j = lp(r.standard_normal(len(f0)), 30) * jitter * 40
        f0 = f0 * (1 + j)
    ph = np.cumsum(f0) / SR
    saw = 2 * (ph % 1) - 1
    return lp(saw, 7000)


def contour(points, d):
    """points = [(t, value), ...] -> per-sample linear contour of duration d."""
    t = t_arr(d)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return np.interp(t, xs, ys)


# ------------------------------------------------------------------ voices / animals
def _voice_sfx(name):
    """A cached voice-actor SFX take (assets/audio/sfx_voice, generated once with Gemini TTS) at 48 kHz."""
    import os
    from cinecode import tts
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    x = tts.read_wav(os.path.join(root, "assets", "audio", "sfx_voice", name + ".wav")).astype(np.float64)
    x = A.resample(x, tts.SR, SR)
    nz = np.abs(x) > 0.02 * np.abs(x).max()
    i0, i1 = np.argmax(nz), len(x) - np.argmax(nz[::-1])
    return x[max(0, i0 - 200): i1 + 2400]


def _pitch(x, semis):
    import os
    import subprocess
    import tempfile
    import soundfile as sf
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "a.wav"), os.path.join(d, "b.wav")
        sf.write(a, x, SR)
        subprocess.run(["rubberband", "-q", "-p", str(semis), a, b], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        y, _ = sf.read(b)
    return y


def sfx_rooster(big=True):
    """The farm rooster: a cartoon-performed, ridiculously loud 'COCK-A-DOODLE-DOO', pushed up in
    pitch, saturated like a bird's rasp, with a slapback echo off the barn."""
    x = _pitch(_voice_sfx("rooster_tts_a"), 3.0)
    x = np.tanh(hp(x, 300) * 4.0) * 0.7 + bp(x, 1500, 5000) * 0.6
    echo = np.zeros(len(x) + int(0.24 * SR))
    add(echo, x, 0)
    add(echo, lp(x, 2500) * 0.28, 0.24)
    out = reverb(echo, 1.8, 0.2, seed=3)
    return norm(out, 0.95 if big else 0.55)


def sfx_groan(seed=0, d=1.8, pitch=95):
    r = np.random.default_rng(seed)
    tt = t_arr(d)
    f = pitch * (1 + 0.15 * np.sin(2 * np.pi * (0.4 + r.random() * 0.4) * tt + r.random() * 6)) \
        * np.linspace(1.05, 0.85, len(tt))
    g = glottal(f, jitter=0.06, seed=seed + 10)
    v = formants(g, [(620, 220), (1150, 300), (2500, 500)], [1.0, 0.55, 0.2])
    v += lp(noise(d, seed + 20), 1800) * 0.25                 # breath / rasp
    am = 0.7 + 0.3 * lp(r.standard_normal(len(tt)), 6) * 4
    env = np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 0.7
    return norm(v * np.clip(am, 0.2, 1.3) * env, 0.8)


def sfx_groan_far(seed=0):
    x = sfx_groan(seed, 2.0, 88 + seed * 7)
    return norm(reverb(lp(x, 1600), 2.2, 0.45, seed=seed), 0.5)


def sfx_scream_far(seed=1):
    d = 1.4
    tt = t_arr(d)
    f = contour([(0, 520), (0.15, 760), (0.9, 720), (d, 480)], d) * (1 + 0.025 * np.sin(2 * np.pi * 6.5 * tt))
    g = glottal(f, jitter=0.03, seed=seed)
    v = formants(g, [(950, 300), (1500, 400), (2800, 700)], [1, 0.6, 0.3])
    env = np.minimum(1, tt / 0.05) * np.minimum(1, (d - tt) / 0.35)
    x = lp(v * env, 2600)
    return norm(reverb(x, 2.4, 0.55, seed=seed + 4), 0.55)


def sfx_crow_caw(seed=2):
    out = np.zeros(int(1.1 * SR))
    for k in range(2):
        du = 0.22
        tt = t_arr(du)
        f = np.linspace(560, 480, len(tt))
        v = formants(glottal(f, 0.08, seed + k) * (1 + 0.6 * np.sin(2 * np.pi * 45 * tt)),
                     [(1300, 600), (2400, 800)])
        add(out, v * np.sin(np.pi * tt / du) ** 0.5, k * 0.34)
    return norm(reverb(lp(out, 3000), 2.0, 0.5, seed=seed), 0.4)


# ------------------------------------------------------------------ house / mechanics
def _stick_slip(d, rate_pts, res, seed=0, jitter=0.18):
    """Wood creak: irregular stick-slip impulses at a varying rate, ringing a dense, inharmonic bank of
    wooden modes (a few strong `res` modes plus random ones, so it never sounds vocal)."""
    r = np.random.default_rng(seed)
    rate = contour(rate_pts, d) * (1 + jitter * lp(r.standard_normal(int(d * SR)), 25) * 8)
    ph = np.cumsum(np.maximum(rate, 5)) / SR
    imp = (np.diff(np.floor(ph), prepend=0) > 0).astype(float)
    imp *= 0.3 + 0.7 * r.random(len(imp)) ** 2
    modes = list(res) + [(f, 6 + r.random() * 10, 0.3 + r.random() * 0.3)
                         for f in np.exp(r.uniform(np.log(450), np.log(6500), 14))]
    y = np.zeros_like(imp)
    for f, q, g in modes:
        b, a = signal.iirpeak(f, q, fs=SR)
        y += signal.lfilter(b, a, imp) * g
    return y


def sfx_floor_creak(seed=0, d=0.9):
    """Floorboard 'crrrk': slow irregular stick-slip clicks (50-140 Hz) ringing bright wooden modes."""
    tt = t_arr(d)
    y = _stick_slip(d, [(0, 50), (d * 0.45, 140), (d, 70)],
                    [(1150, 9, 1), (2300, 11, 0.6)], seed, jitter=0.3)
    y *= np.minimum(1, tt / 0.04) * np.minimum(1, (d - tt) / 0.2)
    return norm(reverb(hp(y, 600), 0.7, 0.2, seed=seed), 0.8)


def sfx_door_creak(d=2.6, seed=5):
    """Old hinge: gritty stick-slip that speeds up and slows down (60-260 Hz), bright metal/wood modes."""
    tt = t_arr(d)
    y = _stick_slip(d, [(0, 60), (d * 0.3, 180), (d * 0.55, 260), (d * 0.8, 150), (d, 70)],
                    [(1700, 10, 1), (2900, 12, 0.7), (4300, 14, 0.4)], seed, jitter=0.35)
    y *= np.minimum(1, tt / 0.2) * np.minimum(1, (d - tt) / 0.5)
    return norm(reverb(hp(y, 700), 1.0, 0.25, seed=seed), 0.7)


def sfx_step_wood(seed=0):
    d = 0.32
    tt = t_arr(d)
    x = lp(noise(d, 120 + seed), 420) * np.exp(-tt * 28)
    x += np.sin(2 * np.pi * 75 * tt) * np.exp(-tt * 22) * 0.9
    x += _stick_slip(d, [(0, 60), (d, 140)], [(900, 5, 1), (1800, 7, 0.5)], seed)[: len(tt)] * 0.18 * np.exp(-tt * 6)
    return norm(reverb(x, 0.8, 0.3, seed=seed + 2), 0.7)


def sfx_lock():
    """Deadbolt turning + latch."""
    out = np.zeros(int(0.5 * SR))
    for st, f, a in [(0.0, 3200, 0.5), (0.06, 2500, 0.4), (0.16, 1800, 1.0)]:
        d = 0.12
        tt = t_arr(d)
        c = hp(noise(d, int(f)), 1500) * np.exp(-tt * 90)
        c += sum(np.sin(2 * np.pi * ff * tt) * np.exp(-tt * 45) for ff in (f, f * 1.47)) * 0.3
        add(out, c * a, st)
    add(out, A.sfx_thud(140, 0.15) * 0.4, 0.16)
    return norm(out, 0.8)


def sfx_chain():
    out = np.zeros(int(0.6 * SR))
    r = np.random.default_rng(7)
    for k in range(9):
        d = 0.05
        tt = t_arr(d)
        f = 3500 + r.random() * 2500
        add(out, np.sin(2 * np.pi * f * tt) * np.exp(-tt * 80) * (0.5 + r.random() * 0.5), 0.02 + k * 0.05)
    add(out, sfx_lock()[: int(0.3 * SR)] * 0.6, 0.42)
    return norm(out, 0.6)


def sfx_curtain():
    w = A.sfx_whoosh(0.45, 600, 3000) * 0.7
    out = np.zeros(int(0.6 * SR))
    add(out, w, 0)
    r = np.random.default_rng(3)
    for k in range(6):
        d = 0.06
        tt = t_arr(d)
        add(out, np.sin(2 * np.pi * (2600 + r.random() * 600) * tt) * np.exp(-tt * 70) * 0.35, 0.03 + k * 0.05)
    return norm(out, 0.7)


def sfx_power_down():
    """Fridge/house hum + bulb dying: relay clunk, hum spinning down, tiny filament tink."""
    d = 1.8
    tt = t_arr(d)
    k = np.clip(1 - tt / 1.1, 0, 1) ** 1.6
    f = 60 * (0.35 + 0.65 * k)
    ph = np.cumsum(f) / SR
    hum = sum(a * np.sin(2 * np.pi * m * ph) for m, a in [(1, 1), (2, 0.6), (3, 0.35), (5, 0.15)])
    hum *= k ** 0.6
    x = hum * 0.5
    clunk = A.sfx_thud(90, 0.35)
    add(x, clunk * 0.7, 0.0)
    add(x, A.sfx_click() * 0.8, 0.0)
    tink = np.sin(2 * np.pi * 4200 * t_arr(0.2)) * np.exp(-t_arr(0.2) * 30) * 0.25
    add(x, tink, 0.05)
    return norm(x, 0.85)


def sfx_hum_loop(d=4.0):
    tt = t_arr(d)
    hum = sum(a * np.sin(2 * np.pi * 60 * m * tt) for m, a in [(1, 1), (2, 0.5), (3, 0.25)])
    return hum * 0.12


def sfx_faucet():
    """Handle squeak + click, a pipe gurgle, one sad drip."""
    out = np.zeros(int(1.6 * SR))
    d = 0.22
    tt = t_arr(d)
    sq = np.sin(2 * np.pi * np.cumsum(np.linspace(1500, 2100, len(tt))) / SR) * np.sin(np.pi * tt / d)
    sq *= 1 + 0.5 * np.sin(2 * np.pi * 90 * tt)
    add(out, sq * 0.35, 0.0)
    add(out, A.sfx_click() * 0.7, 0.22)
    add(out, A.sfx_click() * 0.5, 0.42)
    g = lp(noise(0.5, 77), 500) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 9 * t_arr(0.5)))) * np.exp(-t_arr(0.5) * 5)
    add(out, g * 0.6, 0.45)
    add(out, A.sfx_drip() * 0.9, 1.15)
    return norm(out, 0.75)


def sfx_click_click():
    out = np.zeros(int(0.5 * SR))
    for k in range(3):
        add(out, sfx_lock()[: int(0.08 * SR)] * 0.6, k * 0.14)
    return out


def sfx_pump_stop():
    d = 1.6
    tt = t_arr(d)
    k = np.clip(1 - tt / 1.2, 0, 1) ** 1.3
    f = 120 * (0.15 + 0.85 * k)
    ph = np.cumsum(f) / SR
    m = (2 * (ph % 1) - 1) * 0.5 + np.sin(2 * np.pi * 2 * ph) * 0.4
    x = lp(m, 1500) * k
    add(x, A.sfx_thud(70, 0.4) * 0.8, 1.15)
    add(x, A.sfx_click() * 0.6, 0.0)
    return norm(x, 0.8)


def sfx_window_slam():
    out = np.zeros(int(1.0 * SR))
    add(out, A.sfx_thud(110, 0.4), 0)
    r = np.random.default_rng(11)
    tt = t_arr(0.6)
    rattle = sum(np.sin(2 * np.pi * (2800 + r.random() * 2500) * tt + r.random()) for _ in range(5))
    rattle *= np.exp(-tt * 9) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 28 * tt)))
    add(out, rattle * 0.12, 0.01)
    add(out, sfx_lock()[: int(0.2 * SR)] * 0.5, 0.35)
    return norm(out, 0.9)


def sfx_bed_jolt():
    out = np.zeros(int(0.8 * SR))
    add(out, A.sfx_boing() * 0.25, 0.0)
    add(out, sfx_floor_creak(3, 0.4) * 0.5, 0.02)
    add(out, A.sfx_whoosh(0.25, 900, 3000) * 0.4, 0.0)
    return norm(out, 0.7)


def sfx_sting_low():
    """Low hit + dissonant tail (for cuts to danger)."""
    d = 3.0
    tt = t_arr(d)
    hit = A.sfx_thud(42, 1.2) * 1.0
    clus = sum(np.sin(2 * np.pi * f * tt) for f in (220, 233.1, 311.1)) * np.exp(-tt * 1.4) * 0.12
    clus *= np.minimum(1, tt / 0.05)
    out = np.zeros(len(tt))
    add(out, hit, 0)
    out += clus
    return norm(reverb(out, 2.5, 0.35, seed=9), 0.85)


def sfx_end_tone():
    """Black-screen tail: sub drone, a high thin whine, wind, and somewhere a latch clicks."""
    d = 3.2
    tt = t_arr(d)
    sub = np.sin(2 * np.pi * 41 * tt) * 0.6 + np.sin(2 * np.pi * 61.5 * tt) * 0.2
    whine = np.sin(2 * np.pi * 1870 * tt * (1 + 0.002 * np.sin(2 * np.pi * 0.7 * tt))) * 0.05
    wind = bp(noise(d, 140), 200, 900) * 0.18
    env = np.minimum(1, tt / 0.15) * np.minimum(1, (d - tt) / 1.4)
    out = (sub + whine + wind) * env
    add(out, reverb(sfx_lock(), 1.4, 0.45)[: int(1.2 * SR)] * 0.35, 1.45)
    return norm(out, 0.7)


def sfx_riser(d=1.6):
    tt = t_arr(d)
    x = hp(noise(d, 150), 600) * (tt / d) ** 2.2
    x += np.sin(2 * np.pi * np.cumsum(np.linspace(90, 260, len(tt))) / SR) * (tt / d) ** 2 * 0.4
    return norm(x, 0.6)


def sfx_fridge_hum_stop():
    return sfx_power_down()


def sfx_bite_toast():
    return A.sfx_bite()


def sfx_paper():
    return A.sfx_flap()


def sfx_whoosh_soft():
    return A.sfx_whoosh(0.35, 400, 1800) * 0.6


def sfx_tiptoe(seed=0):
    d = 0.08
    tt = t_arr(d)
    x = bp(noise(d, 160 + seed), 600, 2500) * np.exp(-tt * 60)
    return norm(x, 0.35)


def sfx_gulp_dry():
    return A.sfx_gulp()


def sfx_pop_in():
    return A.sfx_pop() * 0.7


SFX = {
    "rooster": sfx_rooster,
    "rooster_small": lambda: sfx_rooster(False),
    "groan_va": lambda: norm(lp(_voice_sfx("groan_tts_a"), 3500), 0.8),
    "groan_vb": lambda: norm(lp(_voice_sfx("groan_tts_b"), 3500), 0.8),
    "groan_va_far": lambda: norm(reverb(lp(_voice_sfx("groan_tts_a"), 1400), 2.2, 0.45, seed=1), 0.5),
    "groan_vb_far": lambda: norm(reverb(lp(_voice_sfx("groan_tts_b"), 1400), 2.2, 0.45, seed=2), 0.5),
    "groan0": lambda: sfx_groan(0), "groan1": lambda: sfx_groan(1, 1.6, 110), "groan2": lambda: sfx_groan(2, 2.2, 84),
    "groan_far0": lambda: sfx_groan_far(0), "groan_far1": lambda: sfx_groan_far(1), "groan_far2": lambda: sfx_groan_far(2),
    "scream_far": sfx_scream_far, "scream_far2": lambda: sfx_scream_far(4),
    "caw": sfx_crow_caw,
    "creak": sfx_floor_creak, "creak2": lambda: sfx_floor_creak(4, 1.2), "door_creak": sfx_door_creak,
    "step_wood": sfx_step_wood, "step_wood2": lambda: sfx_step_wood(1),
    "lock": sfx_lock, "chain": sfx_chain, "curtain": sfx_curtain,
    "power_down": sfx_power_down, "faucet": sfx_faucet, "pump_stop": sfx_pump_stop,
    "window_slam": sfx_window_slam, "bed_jolt": sfx_bed_jolt,
    "sting": sfx_sting_low, "end_tone": sfx_end_tone, "riser": sfx_riser,
    "tiptoe": sfx_tiptoe, "tiptoe2": lambda: sfx_tiptoe(1), "whoosh_soft": sfx_whoosh_soft, "paper": sfx_paper,
    "pop_in": sfx_pop_in,
}


@functools.lru_cache(maxsize=None)
def get_sfx(name):
    if name in SFX:
        return np.asarray(SFX[name](), dtype=np.float32)
    return A.get_sfx(name)


# ------------------------------------------------------------------ music
def _string(m, d, vib=0.004, bright=0.25):
    tt = t_arr(d)
    f = A.midi_f(m) * (1 + vib * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt * 2, 0, 1))
    ph = np.cumsum(f) / SR
    x = sum((2 * ((ph * k * 1.0) % 1) - 1) / k for k in (1,))
    x = lp(x, 500 + 2500 * bright)
    return fade(x * A.env_adsr(len(tt), 0.6, 0.4, 0.85, 0.9) * 0.25, 0.01, 0.2)


def _piano(m, d=2.5):
    tt = t_arr(d)
    f = A.midi_f(m)
    x = sum(a * np.sin(2 * np.pi * f * k * tt) * np.exp(-tt * (1.2 + k * 0.9)) for k, a in
            [(1, 1.0), (2, 0.45), (3, 0.2), (4, 0.1)])
    return fade(x * np.minimum(1, tt / 0.004) * 0.35, 0.001, 0.2)


@functools.lru_cache(maxsize=None)
def _loop(name):
    rng = np.random.default_rng(len(name) * 31 + 7)
    if name == "dread":
        bpm, bars = 70, 8
        beat = 60 / bpm
        L = bars * 4 * beat
        buf = np.zeros(int(L * SR) + 3 * SR)
        root = 33  # A1
        add(buf, A.pad(root + 12, L + 1, 0.12) * 0.9, 0)
        add(buf, A.pad(root + 19, L + 1, 0.08) * 0.45, 0)
        notes = [57, 60, 59, 57, 64, 63, 60, 59]   # A minor with a nagging flat-5 colour
        for b in range(bars):
            t0 = b * 4 * beat
            add(buf, A.bass(root, beat * 1.5) * 0.7, t0)
            add(buf, A.bass(root, beat * 1.2) * 0.45, t0 + 0.42 * beat)
            if b % 2 == 0:
                add(buf, _piano(notes[b], 3.0) * 0.5, t0 + 2 * beat)
            else:
                add(buf, _piano(notes[b], 3.0) * 0.35, t0 + 1.5 * beat)
            if b in (3, 7):
                add(buf, _string(root + 36 + 3, 4 * beat, bright=0.15) * 0.25, t0)
        buf = reverb(buf, 2.4, 0.3, seed=21)[: int(L * SR)]
        return A._xfade_loop(buf)
    if name == "confident":
        bpm, bars = 112, 8
        beat = 60 / bpm
        L = bars * 4 * beat
        buf = np.zeros(int(L * SR) + SR)
        root = 55  # G
        chords = A._chords("major", [0, 3, 4, 0, 0, 3, 4, 0])
        mel = [7, 9, 11, 9, 7, 4, 2, 4, 7, 9, 11, 14, 11, 9, 7, 7]
        for b in range(bars):
            t0 = b * 4 * beat
            ch = chords[b]
            add(buf, A.bass(root - 24 + ch[0], beat * 0.5), t0)
            add(buf, A.bass(root - 24 + ch[2], beat * 0.5), t0 + 2 * beat)
            for k in range(8):                       # banjo-ish roll
                n = ch[[0, 1, 2, 1][k % 4]] + (12 if k % 4 == 2 else 0)
                add(buf, A.pluck(root + n, beat * 0.6, 0.85, seed=k) * 0.12, t0 + k * beat / 2)
            for k in range(2):                       # whistled tune
                m = root + 12 + mel[(b * 2 + k) % len(mel)]
                tt = t_arr(beat * 1.7)
                f = A.midi_f(m) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * tt) * np.clip(tt * 3, 0, 1))
                w = np.sin(2 * np.pi * np.cumsum(f) / SR) * A.env_adsr(len(tt), 0.05, 0.1, 0.7, 0.2)
                w += hp(noise(beat * 1.7, b * 2 + k), 3000) * 0.03
                add(buf, w * 0.09, t0 + k * 2 * beat)
            for k in range(4):
                add(buf, A.woodblock(k % 2 == 0) * 0.4, t0 + k * beat + beat / 2)
        return A._xfade_loop(buf[: int(L * SR)])
    raise KeyError(name)


def track(name, dur):
    loop = _loop(name)
    n = int(dur * SR)
    return np.tile(loop, n // len(loop) + 1)[:n]


# ------------------------------------------------------------------ ambience
@functools.lru_cache(maxsize=None)
def amb_loop(name):
    d = 16.0
    tt = t_arr(d)
    if name == "farm":
        gust = 0.55 + 0.45 * np.sin(2 * np.pi * 0.09 * tt) * np.sin(2 * np.pi * 0.023 * tt + 1)
        x = bp(noise(d, 200), 180, 1400) * gust * 0.9
        x += hp(noise(d, 201), 2500) * 0.05 * gust
        add(x, sfx_crow_caw(5) * 0.35, 5.5)
        add(x, sfx_crow_caw(6) * 0.25, 12.2)
    elif name == "house":
        x = lp(noise(d, 210), 180) * 0.25
        x += lp(bp(noise(d, 211), 150, 700), 700) * 0.12 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt))
        for k in range(int(d)):          # wall clock
            add(x, A.woodblock(k % 2 == 0)[: int(0.05 * SR)] * 0.08, k + 0.2)
        x += sfx_hum_loop(d) * 0.6
    elif name == "house_dark":
        x = lp(noise(d, 212), 160) * 0.22
        x += lp(bp(noise(d, 213), 150, 700), 700) * 0.14 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * tt))
        for k in range(int(d)):
            add(x, A.woodblock(k % 2 == 0)[: int(0.05 * SR)] * 0.07, k + 0.2)
    else:
        raise KeyError(name)
    return A._xfade_loop(x.astype(np.float64))
