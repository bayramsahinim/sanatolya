"""Voice + music + SFX for the pink-prison story -> audio/mix.wav (-14 LUFS is set at the final mux).
Measured on the reference (r11): the music sits ~14 dB under the voice, and there is roughly one small SFX per second.
Every cue is pinned to a word of voice/words.json, like the picture.
usage (repo root): python3 yumurta/stories/pink-en/mix.py
"""
import json, os, re, sys
import numpy as np
import soundfile as sf
sys.path.insert(0, os.getcwd())
from cinecode import audio as A

D = os.path.dirname(os.path.abspath(__file__))
SR = A.SR
WORDS = json.load(open(os.path.join(D, 'voice', 'words.json')))['words']
norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())


def W(w, n=1):
    k = 0
    for x in WORDS:
        if norm(x['word']) == norm(w):
            k += 1
            if k == n:
                return x['start']
    raise KeyError(w)


def load(p):
    x, s = sf.read(p, always_2d=True)
    x = x.mean(1)
    return A.resample(x, s, SR) if s != SR else x


voice = load(os.path.join(D, 'voice', 'voice.wav'))
DUR = WORDS[-1]['end'] + 1.6
N = int(DUR * SR) + SR
buf_v = np.zeros(N); buf_v[:len(voice)] = voice[:N]
mus = np.zeros(N); sfx = np.zeros(N)


def add(buf, x, t, g=1.0):
    i0 = int(max(0, t) * SR); m = min(len(x), N - i0)
    if m > 0: buf[i0:i0 + m] += np.asarray(x[:m]) * g


def S(name, t, g=.6): add(sfx, A.get_sfx(name), t, g)


def noise(d, lo, hi, a=.01, r=.1, seed=1):
    n = int(d * SR); x = np.random.default_rng(seed).standard_normal(n)
    x = A.bp(x, lo, hi) if hasattr(A, 'bp') else x
    e = np.minimum(1, np.arange(n) / (a * SR + 1)) * np.minimum(1, (n - np.arange(n)) / (r * SR + 1))
    return x / (np.abs(x).max() + 1e-9) * e


def bell(f=660, d=4.5, bright=1.0, k=1.0):
    """A struck church bell ("tin"): hum, prime, minor third, fifth, nominal and upper partials, each with its own
    decay, a short metallic strike transient and a slow beat between paired partials. k scales every decay
    (k<1 = a short "tin" that dies fast); the last 40 % of d is faded out so nothing is cut."""
    tt = np.arange(int(d * SR)) / SR
    parts = [(.5, .5, 3.2), (1, 1, 2.4), (1.19, .55, 1.9), (1.5, .35, 1.5), (2, .7, 1.3), (2.51, .3 * bright, .8),
             (2.66, .25 * bright, .7), (3.01, .22 * bright, .6), (4.07, .15 * bright, .35), (5.2, .1 * bright, .2)]
    x = np.zeros_like(tt)
    for r, a, tau in parts:
        ph = np.random.default_rng(int(r * 100)).uniform(0, 6.28)
        x += a * np.sin(2 * np.pi * f * r * tt + ph) * np.exp(-tt / (tau * k)) * (1 + .12 * np.sin(2 * np.pi * (1.3 + r * .4) * tt))
    strike = noise(.04, 2000, 9000, .001, .03, 11)
    x[:len(strike)] += strike * .6
    x *= np.minimum(1, tt / .002) * np.clip((d - tt) / (.4 * d), 0, 1)
    return x / np.abs(x).max()


def hiss(d, seed=4):               # steam out of an angry man's ears
    tt = np.arange(int(d * SR)) / SR
    return noise(d, 2500, 9000, .1, .3, seed) * (.75 + .25 * np.sin(tt * 17))


def music(a, b, name, g):
    xf = .25; a0 = max(0, a - xf); seg = A.track(name, b - a0 + xf); m = len(seg); env = np.ones(m); k = int(xf * SR)
    env[:k] = np.linspace(0, 1, k); env[-k:] = np.linspace(1, 0, k); add(mus, seg * env, a0, g)


# ---- music: suspense under the hook; quirky while the idea spreads; suspense from California to the question;
#      warm for the reveal
music(.6, W('You') - .1, 'suspense', .45)
music(W('You') - .1, W('Then', 2) - .15, 'quirky', .55)
music(W('Then', 2) - .15, W('Not', 2) - .1, 'suspense', .5)
music(W('Not', 2) - .1, DUR, 'warm', .6)

# ---- the bell: a short "tin" at frame 0, and a softer one when we land back in Iowa (user: short and quiet)
add(sfx, bell(660, .6, k=.15), 0.0, .5)
add(sfx, bell(495, .7, .8, k=.15), W('But', 2) - .1, .35)

# ---- SFX, about one per second, pinned to words
S('pop', W('calm'), .35)
S('whoosh', W('violent') - .15, .45); S('clank', W('violent'), .5); S('clank', W('violent') + .28, .35)
add(sfx, hiss(W('with') - W('violent'), 1), W('violent'), .25)
S('clank', W('bucket'), .3); S('whoosh', W('pink') - .25, .55); S('splash', W('pink') - .05, .85); S('boing', W('paint') + .15, .35)
S('whoosh', W('You') - .15, .55); add(sfx, A.music_sting('dun'), W('1979'), .45)
S('pop', W('Alexander'), .4); S('sparkle', W('colors'), .4)
S('whoosh', W('He') - .15, .45)
t, rate = W('stares'), 96.0
while t < W('So') - .25:                                   # his heartbeat, slowing from 96 to 62
    S('thud', t, .32); S('thud', t + .16, .2)
    k = min(1, max(0, (t - W('heart')) / (W('down', 2) + .4 - W('heart')))); rate = 96 - 34 * k; t += 60 / rate
S('whoosh', W('So') - .15, .5)
for k in range(4): S('step', W('walks') + k * .28, .3)
S('ding', W('Seattle'), .4)
S('whoosh', W('asks') - .15, .45); S('pop', W('Baker'), .4); S('pop', W('Miller'), .4); S('boing', W('pink', 3), .35)
S('whoosh', W('Not') - .15, .5); S('clank', W('alone'), .55)
add(sfx, hiss(W('guards') - W('room'), 2), W('room'), .2)
S('whoosh', W('guards') - .15, .45); S('laugh', W('laugh') - .1, .55)
S('whoosh', W('Pink', 4) - .15, .35); S('laugh', W('guys') + .25, .35)
S('whoosh', W('But') - .15, .5); S('swish', W('report'), .45); S('thud', W('None'), .6); S('ding', W('None') + .05, .45)
S('whoosh', W('color') - .15, .45); S('sparkle', W('name'), .45); S('pop', W('Pink', 5), .4)
S('whoosh', W('Jails') - .15, .45)
for k in range(6): S('swish', W('Jails') + .15 + k * .35, .3)
S('whoosh', W('football') - .15, .45); S('pop', W('Iowa'), .4)
for k in range(3): S('swish', W('paints') + k * .4, .35)
S('boing', W('pink', 6) + .05, .35)
S('whoosh', W('Then', 2) - .15, .5); add(sfx, A.music_sting('dun'), W('California'), .4); S('click', W('month'), .4)
S('whoosh', W('fights') - .15, .4)
for k in range(4): S('bonk', W('fights') + .05 + k * .26, .45)
S('wah', W('up'), .35)
S('whoosh', W('So', 2) - .15, .5); S('ding', W('Switzerland'), .4); S('click', W('test'), .35)
S('whoosh', W('Fiftynine') - .15, .45); S('murmur', W('Fiftynine'), .4)
S('pop', W('Half'), .4); S('pop', W('Half', 2), .4); S('ding', W('white'), .35)
S('whoosh', W('Three') - .12, .45); S('sparkle', W('calmer'), .45); S('ding', W('same'), .5)
S('whoosh', W('So', 3) - .15, .45); S('boing', W('calmed'), .3)
S('whoosh', W('Not', 2) - .15, .5); S('scratch', W('paint', 4) + .1, .55); S('ding', W('Time'), .55)
S('whoosh', W('An') - .12, .4)
t = W('An') + .1
while t < W('whatever') - .1: S('click', t, .22); t += .5      # the clock ticking while he cools off
add(sfx, hiss(W('cools') - W('An'), 3) * np.linspace(1, 0, int((W('cools') - W('An')) * SR)), W('An'), .2)
for k in range(4): S('pop', W('whatever') - .05 + k * (W('are', 2) + .25 - W('whatever')) / 4, .35)
S('whoosh', W('But', 2) - .2, .5); S('sparkle', W('still'), .4); S('tada', W('pink', 8) + .15, .3)

mus_d = mus * 10 ** (-0 / 20)
env = A.envelope_follow(buf_v, .03, .4); env = env / (env.max() + 1e-9)
mus_d = mus * 10 ** (-9 * np.clip(env * 3, 0, 1) / 20)
mix = buf_v * 1.0 + mus_d * .2 + sfx * .5
mix = mix[:int(DUR * SR)]
mix *= .95 / np.abs(mix).max()
os.makedirs(os.path.join(D, 'audio'), exist_ok=True)
sf.write(os.path.join(D, 'audio', 'mix.wav'), np.stack([mix, mix], 1).astype(np.float32), SR)
print('mix', round(DUR, 2), 's')
