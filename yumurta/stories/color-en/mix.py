"""Voice + music + SFX for the short-people story -> audio/mix.wav (-14 LUFS is set at the final mux).
Measured on the reference (r11): the music sits ~14 dB under the voice, and there is roughly one small SFX per second.
Every cue is pinned to a word of voice/words.json, like the picture.
usage (repo root): python3 yumurta/stories/short-en/mix.py
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


def music(a, b, name, g):
    xf = .25; a0 = max(0, a - xf); seg = A.track(name, b - a0 + xf); m = len(seg); env = np.ones(m); k = int(xf * SR)
    env[:k] = np.linspace(0, 1, k); env[-k:] = np.linspace(1, 0, k); add(mus, seg * env, a0, g)


# ---- music: dreamy/curious under the paradox; a hush ("room") for "inside your head"; suspense for the twist; warm at the end
music(.4, W('But', 2) - .1, 'quirky', .5)
music(W('But', 2) - .1, W('Heres', 2) - .1, 'room', .5)
music(W('Heres', 2) - .1, W('Your', 4) - .2, 'suspense', .5)
music(W('Your', 4) - .2, DUR, 'warm', .6)

# ---- the bell: the same short quiet "tin" at frame 0
add(sfx, bell(660, .6, k=.15), 0.0, .5)

# ---- rain under "the way rain feels"
rn = noise(W('All', 2) - W('way', 2) + .4, 1500, 8000, .15, .25, 31); add(sfx, rn, W('way', 2) - .2, .12)

# ---- SFX, about one per second, pinned to words
S('pop', W('sky') + .1, .35); S('whoosh', W('grass') - .14, .4); S('swish', W('green'), .3)
S('whoosh', W('fire') - .14, .45); add(sfx, noise(1.2, 300, 3000, .05, .5, 7), W('fire'), .15)
S('whoosh', W('Everyone') - .14, .45); S('murmur', W('Everyone'), .3); S('pop', W('right'), .3)
S('whoosh', W('But') - .14, .45); S('dun', W('prove'), .4)
S('whoosh', W('What') - .14, .4); S('pop', W('blue', 2), .35); S('pop', W('blue', 3), .4); S('wah', W('see', 2) + .1, .25)
S('whoosh', W('This') - .14, .5); S('portal', W('colorblind') - .1, .3); S('tada', W('paradox'), .35)
S('whoosh', W('Since') - .14, .45); S('slide_up', W('pointed'), .3); S('pop', W('Thats'), .4)
S('whoosh', W('So') - .14, .45); S('ding', W('word'), .35)
S('whoosh', W('But', 2) - .14, .45); S('sparkle', W('actually'), .35)
S('swish', W('Nobody') - .1, .3); S('ooh', W('see', 3), .3)
S('whoosh', W('Your', 2) - .14, .45); S('pop', W('blue', 5), .35); S('pop', W('green', 2), .4)
S('whoosh', W('Your', 3) - .14, .45); S('pop', W('red'), .35); S('pop', W('purple'), .4)
S('whoosh', W('Wed') - .14, .4); S('boing', W('never'), .3)
S('whoosh', W('Heres', 2) - .12, .5); S('dun', W('twist'), .5); S('gasp', W('twist') + .15, .35)
for k in range(4): S('pop', W('just') - .1 + k * .12, .25)
S('whoosh', W('Maybe') - .14, .45); S('flashlight', W('experiences'), .35); S('sparkle', W('world'), .3)
S('whoosh', W('sunset') - .25, .45); S('sparkle', W('sunset'), .35)
S('whoosh', W('your', 5) - .14, .4); S('ding', W('song'), .3)
S('whoosh', W('way', 2) - .25, .4); S('drip', W('rain'), .35)
S('whoosh', W('All', 2) - .14, .45); S('pop', W('yours'), .3); S('pop', W('else', 2), .35)
S('whoosh', W('So', 2) - .14, .5)
for k in range(3): S('splash', W('So', 2) + k * .15, .15)
S('pop', W('colors', 2), .35)
S('whoosh', W('Comment') - .2, .4); S('pop', W('yes'), .4); S('pop', W('no', 3), .4)
S('click', W('Follow'), .45); S('ding', W('paradox', 2) + .2, .4)

mus_d = mus * 10 ** (-0 / 20)
env = A.envelope_follow(buf_v, .03, .4); env = env / (env.max() + 1e-9)
mus_d = mus * 10 ** (-9 * np.clip(env * 3, 0, 1) / 20)
mix = buf_v * 1.0 + mus_d * .2 + sfx * .5
mix = mix[:int(DUR * SR)]
mix *= .95 / np.abs(mix).max()
os.makedirs(os.path.join(D, 'audio'), exist_ok=True)
sf.write(os.path.join(D, 'audio', 'mix.wav'), np.stack([mix, mix], 1).astype(np.float32), SR)
print('mix', round(DUR, 2), 's')
