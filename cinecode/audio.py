"""Procedural sound design + music + mixing (numpy, 48 kHz)."""
import functools
import zlib
import math

import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(12345)


def t_arr(d):
    return np.arange(int(d * SR)) / SR


def env_adsr(n, a=0.005, d=0.05, s=0.6, r=0.1):
    e = np.ones(n) * s
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na = min(na, n)
    e[:na] = np.linspace(0, 1, na, endpoint=False)
    if na + nd < n:
        e[na:na + nd] = np.linspace(1, s, nd, endpoint=False)
    if nr > 0 and nr < n:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def exp_env(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def noise(d, seed=None):
    r = np.random.default_rng(seed) if seed is not None else RNG
    return r.standard_normal(int(d * SR))


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    sos = signal.butter(order, f, btype="low", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def hp(x, f, order=2):
    sos = signal.butter(order, f, btype="high", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def norm(x, peak=0.9):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def sweep(f0, f1, d, kind="sine", curve="exp"):
    t = t_arr(d)
    if curve == "exp":
        f = f0 * (f1 / f0) ** (t / d)
    else:
        f = f0 + (f1 - f0) * t / d
    ph = 2 * np.pi * np.cumsum(f) / SR
    if kind == "sine":
        return np.sin(ph)
    if kind == "square":
        return np.sign(np.sin(ph))
    if kind == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    return np.sin(ph)


def fade(x, fi=0.005, fo=0.02):
    x = x.copy()
    a, b = int(fi * SR), int(fo * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


# ============================================================ SFX library
def sfx_whoosh(d=0.45, f0=300, f1=2500):
    n = noise(d, 1)
    t = t_arr(d)
    e = np.sin(np.pi * t / d) ** 2
    out = np.zeros_like(n)
    # moving band
    steps = 24
    seg = len(n) // steps
    for k in range(steps):
        fc = f0 * (f1 / f0) ** (k / steps)
        part = bp(n, fc * 0.7, min(fc * 1.4, SR / 2 - 100))
        out[k * seg:(k + 1) * seg] = part[k * seg:(k + 1) * seg]
    return norm(out * e, 0.8)


def sfx_swish():
    return sfx_whoosh(0.22, 800, 4000) * 0.7


def sfx_pop():
    d = 0.09
    x = sweep(900, 300, d) * exp_env(int(d * SR), 0.02)
    return norm(x, 0.8)


def sfx_boing():
    d = 0.6
    t = t_arr(d)
    f = 180 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4) + 60 * t
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * exp_env(len(t), 0.25)
    return norm(x, 0.8)


def sfx_thud(f=70, d=0.35):
    t = t_arr(d)
    x = np.sin(2 * np.pi * (f * t + 30 * (1 - np.exp(-t * 30)) / 30)) * exp_env(len(t), 0.08)
    x += lp(noise(d, 2), 400) * exp_env(len(t), 0.03) * 0.6
    return norm(x, 0.9)


def sfx_bonk():
    """metal bucket on a head."""
    d = 0.9
    t = t_arr(d)
    x = np.zeros_like(t)
    for f, a, tau in [(523, 1.0, 0.25), (1312, 0.6, 0.15), (2210, 0.35, 0.1), (3170, 0.25, 0.07), (740, 0.5, 0.3)]:
        x += a * np.sin(2 * np.pi * f * t + RNG.random()) * np.exp(-t / tau)
    x += hp(noise(d, 3), 2000) * exp_env(len(t), 0.01) * 0.8
    x += sfx_thud(90, d)[:len(t)] * 0.6
    return norm(x, 0.9)


def sfx_splash(d=1.1):
    t = t_arr(d)
    n = noise(d, 4)
    x = bp(n, 300, 6000) * (np.exp(-t * 5) * (1 - np.exp(-t * 80)))
    # droplets
    for k in range(40):
        st = int((0.05 + RNG.random() * (d - 0.2)) * SR)
        f = 900 + RNG.random() * 2200
        dd = int(0.05 * SR)
        tt = np.arange(dd) / SR
        drop = np.sin(2 * np.pi * (f + 3000 * tt) * tt) * np.exp(-tt * 70) * 0.25 * np.exp(-st / SR * 2)
        x[st:st + dd] += drop[:len(x[st:st + dd])]
    return norm(x, 0.9)


def sfx_drip():
    d = 0.15
    tt = t_arr(d)
    x = np.sin(2 * np.pi * (1200 + 5000 * tt) * tt) * np.exp(-tt * 40)
    return norm(x, 0.6)


def sfx_coo():
    """pigeon: 'coo-rr-oo'."""
    d = 0.9
    t = t_arr(d)
    f = 340 + 60 * np.sin(np.pi * t / d) + 12 * np.sin(2 * np.pi * 28 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    x += 0.3 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR)
    am = (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t)) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.6
    x *= am
    x = lp(x, 1400)
    return norm(fade(x, 0.03, 0.08), 0.6)


def sfx_flap():
    d = 0.5
    x = np.zeros(int(d * SR))
    for k in range(6):
        st = int(k * 0.07 * SR)
        b = bp(noise(0.06, 10 + k), 300, 2500) * exp_env(int(0.06 * SR), 0.015)
        x[st:st + len(b)] += b
    return norm(x, 0.6)


def sfx_growl():
    d = 1.4
    t = t_arr(d)
    n = lp(noise(d, 5), 220)
    am = 0.5 + 0.5 * np.sin(2 * np.pi * (3 + 4 * t) * t)
    x = n * am * np.sin(np.pi * t / d)
    x += 0.3 * np.sin(2 * np.pi * (70 + 20 * np.sin(2 * np.pi * 2 * t)) * t) * np.sin(np.pi * t / d)
    return norm(x, 0.8)


def sfx_beep(f=2400, d=0.08):
    t = t_arr(d)
    x = np.sign(np.sin(2 * np.pi * f * t)) * 0.4 + np.sin(2 * np.pi * f * t) * 0.6
    return norm(fade(lp(x, 6000), 0.003, 0.01), 0.45)


def sfx_beep2():
    a = sfx_beep(2400, 0.07)
    gap = np.zeros(int(0.06 * SR))
    return np.concatenate([a, gap, a])


def sfx_click():
    d = 0.03
    x = hp(noise(d, 6), 2000) * exp_env(int(d * SR), 0.004)
    return norm(x, 0.6)


def sfx_zap(d=0.9):
    """teleport flash."""
    x = sweep(200, 3500, d * 0.7, "saw")
    x = np.concatenate([x, sweep(3500, 3000, d * 0.3, "sine")])
    t = t_arr(len(x) / SR)
    x = lp(x, 7000) * 0.5 + hp(noise(len(x) / SR, 7), 3000) * 0.3 * np.sin(np.pi * t / t[-1])
    shimmer = sum(np.sin(2 * np.pi * f * t) for f in (1760, 2217, 2637, 3520)) * 0.15 * np.exp(-t * 2)
    return norm(fade(x + shimmer, 0.01, 0.15), 0.8)


def sfx_poof():
    d = 0.5
    t = t_arr(d)
    x = lp(noise(d, 8), 1500) * np.exp(-t * 8) * (1 - np.exp(-t * 200))
    return norm(x, 0.8)


def sfx_rewind(d=1.6):
    t = t_arr(d)
    f = 600 + 1800 * (t / d) + 400 * np.sin(2 * np.pi * 14 * t)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.3
    x = bp(x, 400, 5000)
    chirp = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 22 * t))
    x = x * (0.5 + 0.5 * chirp) + hp(noise(d, 9), 3000) * 0.15
    return norm(fade(x, 0.02, 0.1), 0.6)


def sfx_scratch():
    d = 0.35
    t = t_arr(d)
    f = 400 + 1600 * np.abs(np.sin(2 * np.pi * 3 * t))
    x = bp(noise(d, 11), 300, 3000) * 0.6 + 0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR)
    return norm(fade(x * np.exp(-t * 3), 0.005, 0.05), 0.7)


def sfx_freeze():
    """freeze-frame hit: whoosh into thump."""
    w = sfx_whoosh(0.25, 2000, 600) * 0.6
    th = sfx_thud(60, 0.5)
    out = np.zeros(int(0.75 * SR))
    out[:len(w)] += w
    out[int(0.2 * SR):int(0.2 * SR) + len(th)] += th
    return norm(out, 0.9)


def sfx_step(seed=0, heavy=False):
    d = 0.12
    x = lp(noise(d, 20 + seed), 900 if heavy else 1600) * exp_env(int(d * SR), 0.02)
    x += sfx_thud(90 if heavy else 140, d)[:len(x)] * (0.7 if heavy else 0.3)
    return norm(x, 0.7 if heavy else 0.45)


def sfx_clank():
    d = 0.4
    t = t_arr(d)
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, k in [(1900, 18), (2870, 22), (4100, 30)])
    x += hp(noise(d, 21), 3000) * np.exp(-t * 40)
    return norm(x, 0.5)


def sfx_bite():
    d = 0.18
    x = hp(noise(d, 22), 1500) * exp_env(int(d * SR), 0.03)
    x += bp(noise(d, 23), 200, 900) * exp_env(int(d * SR), 0.05)
    return norm(x, 0.7)


def sfx_chew():
    out = np.zeros(int(0.9 * SR))
    for k in range(4):
        b = sfx_bite() * 0.5
        st = int(k * 0.22 * SR)
        out[st:st + len(b)] += b[: len(out) - st]
    return out


def sfx_dishes():
    d = 0.9
    t = t_arr(d)
    x = np.zeros_like(t)
    for k in range(7):
        st = int(RNG.random() * 0.7 * SR)
        f = 1800 + RNG.random() * 2500
        dd = int(0.2 * SR)
        tt = np.arange(dd) / SR
        clink = (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 2.7 * tt)) * np.exp(-tt * 30)
        x[st:st + dd] += clink[: len(x) - st] * (0.4 + 0.6 * RNG.random())
    return norm(x, 0.6)


def sfx_crash_wood():
    d = 1.2
    t = t_arr(d)
    x = lp(noise(d, 24), 2500) * np.exp(-t * 4) * (1 - np.exp(-t * 300))
    for k in range(8):
        th = sfx_thud(60 + RNG.random() * 120, 0.3) * 0.6
        st = int(RNG.random() * 0.6 * SR)
        x[st:st + len(th)] += th[: len(x) - st]
    crack = hp(noise(0.08, 25), 1500) * exp_env(int(0.08 * SR), 0.01)
    x[: len(crack)] += crack * 1.2
    return norm(x, 0.9)


def sfx_creak():
    d = 0.8
    t = t_arr(d)
    f = 140 + 60 * np.sin(2 * np.pi * 1.2 * t)
    pulses = (np.sin(2 * np.pi * np.cumsum(f) / SR) > 0.95).astype(float)
    x = bp(pulses, 300, 2500) * np.sin(np.pi * t / d)
    return norm(x, 0.6)


def sfx_rope_tug():
    return norm(sfx_creak()[: int(0.4 * SR)] * 0.6 + sfx_swish()[: int(0.4 * SR)] * 0.0 if False else
                sfx_creak()[: int(0.45 * SR)], 0.6)


def sfx_ding():
    d = 1.2
    t = t_arr(d)
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * k) for f, a, k in
            [(1568, 1, 3), (3136, 0.4, 5), (4704, 0.2, 7), (2093, 0.3, 4)])
    return norm(x, 0.5)


def sfx_sparkle():
    d = 1.0
    t = t_arr(d)
    x = np.zeros_like(t)
    notes = [2093, 2637, 3136, 4186, 3520]
    for k, f in enumerate(notes):
        st = int(k * 0.08 * SR)
        tt = t[: len(t) - st]
        x[st:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt * 6) * 0.5
    return norm(x, 0.45)


def sfx_thunder(d=3.0):
    t = t_arr(d)
    x = lp(noise(d, 26), 180, 4) * (np.exp(-t * 1.2) * (1 - np.exp(-t * 6)))
    x += lp(noise(d, 27), 600) * np.exp(-t * 6) * 0.5
    return norm(x, 0.9)


def sfx_slide_down():
    d = 0.7
    x = sweep(1400, 300, d) * np.sin(np.pi * t_arr(d) / d) ** 0.4
    return norm(x, 0.5)


def sfx_slide_up():
    d = 0.5
    return norm(sweep(300, 1500, d) * np.sin(np.pi * t_arr(d) / d) ** 0.4, 0.5)


def sfx_gulp():
    d = 0.25
    t = t_arr(d)
    x = np.sin(2 * np.pi * np.cumsum(260 - 400 * t) / SR) * np.sin(np.pi * t / d)
    return norm(x, 0.6)


def sfx_cart():
    d = 1.6
    t = t_arr(d)
    x = lp(noise(d, 28), 500) * 0.5
    clacks = np.zeros_like(t)
    for k in range(int(d * 9)):
        st = int(k / 9 * SR)
        cl = sfx_thud(180, 0.06) * 0.4
        clacks[st:st + len(cl)] += cl[: len(t) - st]
    return norm((x + clacks) * np.sin(np.pi * t / d) ** 0.3, 0.6)


def sfx_crickets(d=2.5):
    t = t_arr(d)
    x = np.zeros_like(t)
    for burst in np.arange(0.1, d - 0.3, 0.55):
        for k in range(3):
            st = int((burst + k * 0.045) * SR)
            dd = int(0.03 * SR)
            tt = np.arange(dd) / SR
            x[st:st + dd] += np.sin(2 * np.pi * 4300 * tt) * np.sin(np.pi * tt / tt[-1])
    return norm(x, 0.35)


def sfx_heartbeat():
    out = np.zeros(int(0.9 * SR))
    for st in (0.0, 0.22):
        th = sfx_thud(55, 0.25)
        s = int(st * SR)
        out[s:s + len(th)] += th * (1 if st == 0 else 0.7)
    return norm(out, 0.8)


def sfx_flashlight():
    a = sfx_click()
    hum = np.sin(2 * np.pi * 1200 * t_arr(0.4)) * np.exp(-t_arr(0.4) * 12) * 0.2
    out = np.zeros(int(0.45 * SR))
    out[: len(a)] += a
    out[: len(hum)] += hum
    return out


def sfx_portal(d=2.2):
    t = t_arr(d)
    base = sum(np.sin(2 * np.pi * f * t * (1 + 0.002 * np.sin(2 * np.pi * 3 * t))) for f in (110, 165, 220))
    swirl = bp(noise(d, 29), 400, 3000) * (0.5 + 0.5 * np.sin(2 * np.pi * 6 * t))
    rise = sweep(200, 1200, d) * 0.3
    x = (base * 0.3 + swirl * 0.4 + rise) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.5
    return norm(x, 0.8)


def sfx_suck():
    d = 0.6
    x = sfx_whoosh(d, 3000, 200)
    return norm(x * np.linspace(0.3, 1, len(x)), 0.8)


def sfx_ta_da():
    return music_sting("tada")


def sfx_wah():
    return music_sting("wah")


def sfx_dun():
    return music_sting("dun")


def sfx_stomach():
    return sfx_growl()


# crowd -----------------------------------------------------------------
def _babble(d, seed, voices=10, lo=250, hi=2500):
    t = t_arr(d)
    out = np.zeros_like(t)
    r = np.random.default_rng(seed)
    n = noise(d, seed)
    for v in range(voices):
        f1 = 400 + r.random() * 500
        rate = 3 + r.random() * 3
        am = np.clip(np.sin(2 * np.pi * rate * t + r.random() * 6) + 0.2 * r.standard_normal(1), 0, 1)
        voice = bp(np.roll(n, r.integers(0, len(n))), f1 * 0.8, f1 * 2.2)
        out += voice * am
    return hp(lp(out, hi), lo)


def sfx_crowd_murmur(d=4.0):
    return norm(_babble(d, 30), 0.5)


def sfx_cheer(d=3.0):
    t = t_arr(d)
    x = _babble(d, 31, voices=24, lo=400, hi=4500) * 1.4
    x += bp(noise(d, 32), 1500, 6000) * 0.5  # claps-ish hiss
    # claps
    r = np.random.default_rng(33)
    for k in range(int(d * 30)):
        st = int(r.random() * (d - 0.05) * SR)
        cl = hp(noise(0.02, 40 + k), 1200) * exp_env(int(0.02 * SR), 0.004) * 0.6
        x[st:st + len(cl)] += cl
    e = (1 - np.exp(-t * 6)) * np.exp(-np.maximum(0, t - d * 0.6) * 2.5)
    return norm(x * e, 0.85)


def sfx_gasp(d=1.0):
    t = t_arr(d)
    x = bp(noise(d, 34), 600, 4000) * (np.exp(-t * 6) * (1 - np.exp(-t * 40)))
    return norm(x, 0.7)


def sfx_laugh(d=2.5):
    t = t_arr(d)
    x = _babble(d, 35, voices=16, lo=300, hi=3500)
    ha = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 5 * t))
    e = (1 - np.exp(-t * 8)) * np.exp(-np.maximum(0, t - d * 0.5) * 2)
    return norm(x * (0.4 + 0.6 * ha) * e, 0.8)


def sfx_ooh(d=1.4):
    t = t_arr(d)
    f = 220 + 80 * t / d
    x = np.zeros_like(t)
    for k in range(12):
        ff = f * (1 + 0.6 * np.random.default_rng(k).random())
        x += np.sin(2 * np.pi * np.cumsum(ff) / SR + k)
    x = lp(x, 900) * np.sin(np.pi * t / d)
    return norm(x, 0.5)


SFX = {
    "whoosh": sfx_whoosh, "swish": sfx_swish, "pop": sfx_pop, "boing": sfx_boing, "thud": sfx_thud,
    "bonk": sfx_bonk, "splash": sfx_splash, "drip": sfx_drip, "coo": sfx_coo, "flap": sfx_flap,
    "growl": sfx_growl, "beep": sfx_beep, "beep2": sfx_beep2, "click": sfx_click, "zap": sfx_zap,
    "poof": sfx_poof, "rewind": sfx_rewind, "scratch": sfx_scratch, "freeze": sfx_freeze,
    "clank": sfx_clank, "bite": sfx_bite, "chew": sfx_chew, "dishes": sfx_dishes,
    "crash_wood": sfx_crash_wood, "creak": sfx_creak, "ding": sfx_ding, "sparkle": sfx_sparkle,
    "thunder": sfx_thunder, "slide_down": sfx_slide_down, "slide_up": sfx_slide_up, "gulp": sfx_gulp,
    "cart": sfx_cart, "crickets": sfx_crickets, "heartbeat": sfx_heartbeat, "flashlight": sfx_flashlight,
    "portal": sfx_portal, "suck": sfx_suck, "tada": sfx_ta_da, "wah": sfx_wah, "dun": sfx_dun,
    "murmur": sfx_crowd_murmur, "cheer": sfx_cheer, "gasp": sfx_gasp, "laugh": sfx_laugh, "ooh": sfx_ooh,
    "step": lambda: sfx_step(0), "step_heavy": lambda: sfx_step(1, True),
}


@functools.lru_cache(maxsize=None)
def get_sfx(name):
    return np.asarray(SFX[name](), dtype=np.float32)


# ============================================================ instruments
def midi_f(m):
    return 440.0 * 2 ** ((m - 69) / 12)


@functools.lru_cache(maxsize=4096)
def _pluck_cached(m, d, bright, seed):
    f = midi_f(m)
    n = int(d * SR)
    N = max(2, int(SR / f))
    r = np.random.default_rng(seed)
    buf = r.uniform(-1, 1, N)
    buf = lp(buf, min(SR / 2 - 100, 1500 + 6000 * bright), 1)
    out = np.zeros(n)
    # vectorised-ish Karplus-Strong in blocks of N
    decay = 0.996 if f < 300 else 0.993
    y = buf.copy()
    pos = 0
    while pos < n:
        k = min(N, n - pos)
        out[pos:pos + k] = y[:k]
        y = decay * 0.5 * (y + np.roll(y, -1))
        pos += N
    out *= exp_env(n, d * 0.35 + 0.08)
    return fade(out, 0.001, 0.02)


def pluck(m, d=0.6, bright=0.5, seed=0):
    return _pluck_cached(int(m), round(d, 3), round(bright, 2), seed % 5)


def pad(m, d, bright=0.3):
    t = t_arr(d)
    f = midi_f(m)
    x = np.zeros_like(t)
    for det in (-0.08, 0.0, 0.07):
        ff = f * 2 ** (det / 12)
        x += 2 * ((ff * t) % 1) - 1
    x = lp(x, 400 + 1800 * bright)
    return fade(x * env_adsr(len(t), 0.25, 0.3, 0.8, 0.4) * 0.25, 0.01, 0.1)


def brass(m, d, vel=1.0):
    t = t_arr(d)
    f = midi_f(m)
    x = 2 * ((f * t) % 1) - 1
    e = env_adsr(len(t), 0.04, 0.1, 0.75, 0.12)
    cutoff = 600 + 3000 * e * vel
    # time-varying filter approximation: blend two filters
    a = lp(x, 900)
    b = lp(x, 3500)
    y = a + (b - a) * e
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t * 3, 0, 1)
    return y * e * 0.4 * vel


def bass(m, d):
    t = t_arr(d)
    f = midi_f(m)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    return fade(x * exp_env(len(t), 0.35) * 0.55, 0.003, 0.03)


def kick():
    return sfx_thud(58, 0.3) * 0.8


def frame_drum(low=True):
    d = 0.25
    t = t_arr(d)
    x = np.sin(2 * np.pi * (110 if low else 220) * t) * np.exp(-t * 18)
    x += bp(noise(d, 50 if low else 51), 200, 2500) * np.exp(-t * (30 if low else 45)) * 0.6
    return x * 0.6


def shaker():
    d = 0.08
    return hp(noise(d, 52), 4000) * exp_env(int(d * SR), 0.02) * 0.25


def woodblock(hi=True):
    d = 0.12
    t = t_arr(d)
    f = 1100 if hi else 800
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 45) * 0.35


def glock(m, d=0.8):
    t = t_arr(d)
    f = midi_f(m)
    return (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t * 4) * 0.25


# ============================================================ composition
SCALES = {
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "phrygdom": [0, 1, 4, 5, 7, 8, 10],
    "mixo": [0, 2, 4, 5, 7, 9, 10],
}


def add(buf, x, t):
    s = int(t * SR)
    if s >= len(buf) or s + len(x) <= 0:
        return
    if s < 0:
        x = x[-s:]
        s = 0
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s]


def track(name, dur):
    """Render a music bed of `dur` seconds (looped composition)."""
    loop = _loop(name)
    n = int(dur * SR)
    reps = n // len(loop) + 1
    out = np.tile(loop, reps)[:n]
    return out


@functools.lru_cache(maxsize=None)
def _loop(name):
    rng = np.random.default_rng(zlib.crc32(name.encode()))
    if name == "quirky":
        return _quirky(rng, root=50, bpm=104, scale="dorian", bars=8)
    if name == "market":
        return _quirky(rng, root=50, bpm=100, scale="phrygdom", bars=8, drum=True)
    if name == "room":
        return _quirky(rng, root=55, bpm=96, scale="major", bars=8, soft=True)
    if name == "chase":
        return _chase(rng, root=50, bpm=150, bars=8)
    if name == "suspense":
        return _suspense(rng, root=45, bpm=80, bars=4)
    if name == "festival":
        return _festival(rng, root=53, bpm=112, bars=8)
    if name == "warm":
        return _warm(rng, root=55, bpm=84, bars=8)
    if name == "egypt":
        return _quirky(rng, root=50, bpm=112, scale="phrygdom", bars=8, drum=True, bright=0.9)
    if name == "rain":
        return _warm(rng, root=50, bpm=72, bars=8, minor=True)
    raise KeyError(name)


def _chords(scale, prog_degrees):
    sc = SCALES[scale]
    out = []
    for d in prog_degrees:
        out.append([sc[(d + k) % 7] + 12 * ((d + k) // 7) for k in (0, 2, 4)])
    return out


def _quirky(rng, root, bpm, scale, bars, drum=False, soft=False, bright=0.6):
    beat = 60 / bpm
    L = bars * 4 * beat
    buf = np.zeros(int(L * SR) + SR)
    sc = SCALES[scale]
    prog_deg = [0, 3, 4, 0, 5, 3, 4, 4] if scale != "phrygdom" else [0, 1, 0, 6, 0, 1, 5, 0]
    chords = _chords(scale, prog_deg)
    for b in range(bars):
        ch = chords[b % len(chords)]
        t0 = b * 4 * beat
        # bass on 1 and 3 (staccato)
        add(buf, bass(root - 12 + ch[0], beat * 0.6), t0)
        add(buf, bass(root - 12 + ch[0] + (7 if b % 2 else 0), beat * 0.5), t0 + 2 * beat)
        # pizzicato offbeat chords
        for k in (1, 3):
            for j, n in enumerate(ch):
                add(buf, pluck(root + n, beat * 0.5, 0.4, seed=j) * 0.18, t0 + k * beat + j * 0.008)
        # melody: playful steps, rests
        pos = 0.0
        last = 7
        while pos < 4:
            dur = rng.choice([0.5, 0.5, 0.25, 1.0, 0.75])
            if rng.random() < 0.28:
                pos += dur
                continue
            step = rng.choice([-2, -1, 1, 1, 2, -3, 3])
            last = int(np.clip(last + step, 2, 12))
            deg = last
            m = root + 12 + sc[deg % 7] + 12 * (deg // 7)
            v = (0.22 if not soft else 0.14)
            add(buf, pluck(m, max(0.25, dur * beat * 1.5), bright, seed=int(m)) * v, t0 + pos * beat)
            pos += dur
        if drum:
            for k in range(4):
                add(buf, frame_drum(True) * 0.5, t0 + k * beat)
                if rng.random() < 0.6:
                    add(buf, frame_drum(False) * 0.35, t0 + (k + 0.5) * beat)
        for k in range(8):
            add(buf, shaker() * (0.6 if k % 2 else 0.3), t0 + k * beat / 2)
        if not soft and b % 2 == 1:
            add(buf, woodblock(True), t0 + 3.5 * beat)
    buf = buf[: int(L * SR)]
    return _xfade_loop(buf)


def _chase(rng, root, bpm, bars):
    beat = 60 / bpm
    L = bars * 4 * beat
    buf = np.zeros(int(L * SR) + SR)
    sc = SCALES["minor"]
    pat = [0, 0, 3, 0, 5, 0, 3, 7]
    roots = [0, 0, -2, -4, 0, 0, -2, -5]
    for b in range(bars):
        t0 = b * 4 * beat
        r = roots[b % len(roots)]
        for k in range(8):
            m = root + r + pat[k]
            add(buf, pluck(m, beat * 0.4, 0.7, seed=k) * 0.2, t0 + k * beat / 2)
            add(buf, pluck(m + 12, beat * 0.3, 0.8, seed=k + 1) * 0.08, t0 + k * beat / 2)
        add(buf, kick() * 0.5, t0)
        add(buf, kick() * 0.4, t0 + 1.5 * beat)
        add(buf, kick() * 0.5, t0 + 2 * beat)
        for k in range(4):
            add(buf, frame_drum(False) * 0.3, t0 + k * beat + beat / 2)
        add(buf, bass(root - 12 + r, beat * 1.8), t0)
        add(buf, bass(root - 12 + r, beat * 1.8), t0 + 2 * beat)
        if b % 2 == 1:
            add(buf, brass(root + 12 + r + 7, beat * 1.5, 0.6) * 0.5, t0 + 2 * beat)
    return _xfade_loop(buf[: int(L * SR)])


def _suspense(rng, root, bpm, bars):
    beat = 60 / bpm
    L = bars * 4 * beat
    buf = np.zeros(int(L * SR) + SR)
    add(buf, pad(root, L + 0.5, 0.15) * 0.8, 0)
    add(buf, pad(root + 7, L + 0.5, 0.1) * 0.4, 0)
    for b in range(bars * 2):
        add(buf, pluck(root - 12, beat * 1.5, 0.3, seed=b) * 0.3, b * 2 * beat)
        add(buf, pluck(root - 11 if b % 4 == 3 else root - 12, beat, 0.3, seed=b + 1) * 0.2, b * 2 * beat + beat)
    return _xfade_loop(buf[: int(L * SR)])


def _festival(rng, root, bpm, bars):
    beat = 60 / bpm
    L = bars * 4 * beat
    buf = np.zeros(int(L * SR) + SR)
    chords = _chords("major", [0, 3, 4, 0, 0, 3, 4, 4])
    mel = [7, 9, 11, 12, 11, 9, 7, 4, 5, 7, 9, 7, 5, 4, 2, 0]
    for b in range(bars):
        t0 = b * 4 * beat
        ch = chords[b]
        for k in range(4):
            add(buf, frame_drum(k % 2 == 0) * 0.5, t0 + k * beat)
        add(buf, kick() * 0.4, t0)
        add(buf, bass(root - 12 + ch[0], beat * 0.9), t0)
        add(buf, bass(root - 12 + ch[2], beat * 0.9), t0 + 2 * beat)
        for j, n in enumerate(ch):
            add(buf, brass(root + n, beat * 0.45, 0.6) * 0.18, t0 + beat)
            add(buf, brass(root + n, beat * 0.45, 0.6) * 0.18, t0 + 3 * beat)
        for k in range(2):
            m = mel[(b * 2 + k) % len(mel)]
            add(buf, brass(root + 12 + m, beat * 1.8, 0.8) * 0.22, t0 + k * 2 * beat)
    return _xfade_loop(buf[: int(L * SR)])


def _warm(rng, root, bpm, bars, minor=False):
    beat = 60 / bpm
    L = bars * 4 * beat
    buf = np.zeros(int(L * SR) + SR)
    scale = "minor" if minor else "major"
    chords = _chords(scale, [0, 5, 3, 4, 0, 5, 3, 4] if not minor else [0, 5, 2, 6, 0, 3, 4, 0])
    sc = SCALES[scale]
    for b in range(bars):
        t0 = b * 4 * beat
        ch = chords[b]
        for n in ch:
            add(buf, pad(root + n, 4 * beat + 0.4, 0.25) * 0.5, t0)
        add(buf, bass(root - 12 + ch[0], beat * 3), t0)
        for k in range(8):
            n = ch[k % 3] + (12 if k >= 4 else 0)
            add(buf, pluck(root + n, beat * 1.2, 0.35, seed=k) * 0.1, t0 + k * beat / 2)
    return _xfade_loop(buf[: int(L * SR)])


def _xfade_loop(buf):
    n = int(0.05 * SR)
    buf = buf.copy()
    buf[:n] *= np.linspace(0, 1, n)
    buf[-n:] *= np.linspace(1, 0, n)
    return norm(buf, 0.5).astype(np.float32)


def music_sting(kind):
    if kind == "tada":
        out = np.zeros(int(1.6 * SR))
        for i, (m, t, d) in enumerate([(67, 0.0, 0.12), (72, 0.14, 0.9)]):
            for k in (0, 4, 7):
                add(out, brass(m + k, d, 1.0) * 0.4, t)
        return norm(out, 0.7)
    if kind == "wah":
        out = np.zeros(int(2.6 * SR))
        for i, (m, d) in enumerate([(63, 0.45), (62, 0.45), (61, 0.45), (60, 1.1)]):
            x = brass(m, d, 0.7)
            if i == 3:
                tt = t_arr(d)
                f = midi_f(60) * (1 + 0.012 * np.sin(2 * np.pi * 6 * tt))
                x = lp(2 * ((np.cumsum(f) / SR) % 1) - 1, 1200) * env_adsr(len(tt), 0.04, 0.1, 0.8, 0.3) * 0.4
            add(out, x, i * 0.5)
        return norm(out, 0.6)
    if kind == "dun":
        out = np.zeros(int(2.4 * SR))
        for i, m in enumerate([45, 46, 41]):
            d = 0.35 if i < 2 else 1.4
            x = brass(m, d, 1.0) + brass(m + 12, d, 0.8) * 0.5
            add(out, x, [0, 0.4, 0.8][i])
        add(out, kick(), 0.8)
        return norm(out, 0.8)
    raise KeyError(kind)


# ============================================================ ambience
@functools.lru_cache(maxsize=None)
def amb_loop(name):
    d = 12.0
    t = t_arr(d)
    if name == "market":
        x = _babble(d, 60, voices=14, lo=300, hi=2600) * 0.6
        x += lp(noise(d, 61), 300) * 0.1
        for k in range(10):
            st = RNG.random() * (d - 1)
            add(x, sfx_step(k) * 0.15, st)
    elif name == "crowd":
        x = _babble(d, 62, voices=24, lo=300, hi=3000)
    elif name == "street":
        x = lp(noise(d, 63), 500) * 0.25 + _babble(d, 64, voices=4) * 0.2
    elif name == "rain":
        x = bp(noise(d, 65), 400, 8000) * 0.6 + lp(noise(d, 66), 250) * 0.3
        for k in range(300):
            add(x, sfx_drip() * 0.06, RNG.random() * (d - 0.2))
    elif name == "room":
        x = lp(noise(d, 67), 200) * 0.08
    elif name == "bakery":
        x = lp(noise(d, 68), 700) * 0.15
        # fire crackle
        for k in range(120):
            cr = hp(noise(0.01, 70 + k), 2000) * 0.15
            add(x, cr, RNG.random() * (d - 0.02))
        x += _babble(d, 69, voices=4) * 0.15
    elif name == "desert":
        x = bp(noise(d, 71), 150, 1200) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.15 * t))
    else:
        raise KeyError(name)
    return _xfade_loop(x.astype(np.float64))


# ============================================================ mix
def stretch(x, sr_in, tempo, tmpdir):
    """Slow speech with rubberband (formant-preserving)."""
    import os
    import subprocess
    import uuid

    import soundfile as sf
    a = os.path.join(tmpdir, f"rb_{uuid.uuid4().hex}.wav")
    b = a.replace(".wav", "_o.wav")
    sf.write(a, x, sr_in)
    subprocess.run(["rubberband", "-q", "-T", str(tempo), "--formant", "-3", a, b], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    y, sr = sf.read(b)
    os.remove(a)
    os.remove(b)
    return y, sr


def resample(x, sr_in, sr_out=SR):
    if sr_in == sr_out:
        return x
    g = math.gcd(sr_in, sr_out)
    return signal.resample_poly(x, sr_out // g, sr_in // g)


def envelope_follow(x, att=0.02, rel=0.35):
    """Smoothed amplitude envelope (for ducking)."""
    a = np.abs(x)
    # block max then smooth
    hop = 480
    n = len(a) // hop + 1
    pad = np.zeros(n * hop)
    pad[: len(a)] = a
    blocks = pad.reshape(n, hop).max(axis=1)
    out = np.zeros(n)
    ka = math.exp(-hop / (att * SR))
    kr = math.exp(-hop / (rel * SR))
    v = 0.0
    for i, b in enumerate(blocks):
        k = ka if b > v else kr
        v = k * v + (1 - k) * b
        out[i] = v
    return np.repeat(out, hop)[: len(x)]
