"""Procedural ambient bed for the plant-poison short (replaces the original's music/rain
atmosphere, which cannot be separated from the Turkish voice): warm minor-key pads, sparse
soft piano, low sub, and a faint rain texture. Reflective, slightly ominous, gentle swell
near the end and a soft resolve."""
import numpy as np

from cinecode import audio as A

SR = A.SR
BPM = 72
BAR = 4 * 60 / BPM
# A minor: Am F C G | Am F Dm E | Am F C G | Dm F E Am(hold)
PROG = [(57, "m"), (53, "M"), (48, "M"), (55, "M"),
        (57, "m"), (53, "M"), (50, "m"), (52, "M"),
        (57, "m"), (53, "M"), (48, "M"), (55, "M"),
        (50, "m"), (53, "M"), (52, "M"), (57, "m")]


def chord(root, q):
    third = 3 if q == "m" else 4
    return [root, root + third, root + 7]


def piano(m, d=2.2, vel=0.5):
    t = A.t_arr(d)
    f = A.midi_f(m)
    x = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (2.2 + 1.6 * k))
            for k, a in [(1, 1.0), (2, 0.35), (3, 0.12), (4, 0.05)])
    att = np.clip(t / 0.006, 0, 1)
    return A.lp(x * att, 2500) * vel * 0.32


def rain(dur, seed=7):
    n = int(dur * SR)
    r = np.random.default_rng(seed)
    hiss = A.bp(r.standard_normal(n), 1800, 7000) * 0.05
    hiss = A.lp(hiss, 6000)
    drops = np.zeros(n)
    for t in r.uniform(0, dur, int(dur * 22)):
        dd = A.bp(r.standard_normal(int(0.02 * SR)), 2500, 9000) * np.exp(-np.arange(int(0.02 * SR)) / (0.003 * SR))
        A.add(drops, dd * r.uniform(0.02, 0.07), t)
    slow = 0.75 + 0.25 * np.sin(2 * np.pi * np.arange(n) / SR / 9.0)
    return (hiss * slow + drops) * 0.8


def render(dur):
    n = int(dur * SR)
    pad_l = np.zeros(n)
    pno = np.zeros(n)
    sub = np.zeros(n)
    r = np.random.default_rng(3)
    for i, (root, q) in enumerate(PROG):
        t0 = i * BAR
        if t0 >= dur:
            break
        last = i == len(PROG) - 1 or (i + 1) * BAR >= dur
        d = BAR + 0.6 if not last else max(1.0, dur - t0)
        swell = 1.0 + 0.5 * max(0, min(1, (i - 10) / 3))  # bars 11-14 lift
        bright = 0.18 + 0.12 * (swell - 1) * 2
        for m in chord(root, q):
            A.add(pad_l, A.pad(m, d, bright) * 0.55 * swell, t0)
        A.add(pad_l, A.pad(root - 12, d, 0.1) * 0.35, t0)
        A.add(sub, A.bass(root - 24, min(d, 2.5)) * 0.35, t0)
        # sparse piano: a few chord tones an octave up, gently arpeggiated
        notes = chord(root + 12, q) + [root + 24]
        for k, beat in enumerate([0, 1.5, 2.5] if i % 2 == 0 else [0.5, 2]):
            m = notes[(k + i) % len(notes)]
            A.add(pno, piano(m, 2.4, 0.45 * (0.85 + 0.3 * r.random())), t0 + beat * 60 / BPM)
    # simple stereo-less reverb for the piano
    ir_n = int(1.8 * SR)
    ir = np.random.default_rng(11).standard_normal(ir_n) * np.exp(-np.arange(ir_n) / (0.45 * SR))
    ir = A.lp(ir, 3500) * 0.012
    from scipy.signal import fftconvolve
    pno = pno + fftconvolve(pno, ir)[:n] + fftconvolve(pad_l, ir)[:n] * 0.4
    mix = pad_l * 0.9 + pno + sub + rain(dur)
    mix = A.hp(mix, 35)
    fi, fo = int(1.2 * SR), int(2.5 * SR)
    mix[:fi] *= np.linspace(0, 1, fi)
    mix[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    return (mix / (np.max(np.abs(mix)) + 1e-9) * 0.8).astype(np.float32)


if __name__ == "__main__":
    import soundfile as sf
    sf.write("build/plant_poison_music_preview.wav", render(52), SR)
