"""Voice + music + SFX for the Thunder Stone story -> audio/mix.wav (-14 LUFS is set at the final mux).
Measured on the reference (r11): the music sits ~14 dB under the voice, and there is roughly one small SFX per second.
Every cue is pinned to a word of voice/words.json, like the picture.
usage (repo root): python3 yumurta/stories/thunder-en/mix.py
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


def bell(f=660, d=4.5, bright=1.0):
    """A struck church bell ("tin"): hum, prime, minor third, fifth, nominal and upper partials, each with its own
    decay, a short metallic strike transient and a slow beat between paired partials."""
    tt = np.arange(int(d * SR)) / SR
    parts = [(.5, .5, 3.2), (1, 1, 2.4), (1.19, .55, 1.9), (1.5, .35, 1.5), (2, .7, 1.3), (2.51, .3 * bright, .8),
             (2.66, .25 * bright, .7), (3.01, .22 * bright, .6), (4.07, .15 * bright, .35), (5.2, .1 * bright, .2)]
    x = np.zeros_like(tt)
    for r, a, tau in parts:
        ph = np.random.default_rng(int(r * 100)).uniform(0, 6.28)
        x += a * np.sin(2 * np.pi * f * r * tt + ph) * np.exp(-tt / tau) * (1 + .12 * np.sin(2 * np.pi * (1.3 + r * .4) * tt))
    strike = noise(.04, 2000, 9000, .001, .03, 11)
    x[:len(strike)] += strike * .6
    x *= np.minimum(1, tt / .002)
    return x / np.abs(x).max()


def crack(d=.6, seed=3):           # ice cracking: sharp clicks in a falling burst
    x = np.zeros(int(d * SR)); r = np.random.default_rng(seed)
    for k in range(14):
        i0 = int(r.uniform(0, d * .7) * SR); c = noise(.03, 1500, 8000, .0005, .025, seed + k); x[i0:i0 + len(c)] += c * r.uniform(.4, 1)
    return x


def rumble(d, seed=2):             # the rock grinding forward: low noise with a slow wobble
    tt = np.arange(int(d * SR)) / SR
    return noise(d, 40, 240, .3, .5, seed) * (.7 + .3 * np.sin(tt * 3.1))


def music(a, b, name, g):
    xf = .25; a0 = max(0, a - xf); seg = A.track(name, b - a0 + xf); m = len(seg); env = np.ones(m); k = int(xf * SR)
    env[:k] = np.linspace(0, 1, k); env[-k:] = np.linspace(1, 0, k); add(mus, seg * env, a0, g)


# ---- music: the hook rides on the bell and a low suspense bed; quirky for the plan and the laughter;
#      suspense as the swamp freezes; a chase while the mountain moves; suspense for the question; warm for the reveal
music(.6, W('You') - .1, 'suspense', .45)
music(W('You') - .1, W('then', 2) - .15, 'quirky', .55)
music(W('then', 2) - .15, W('starts'), 'suspense', .55)
music(W('starts'), W('why') - .1, 'chase', .5)
music(W('why') - .1, W('Because') - .05, 'suspense', .5)
music(W('Because') - .05, DUR, 'warm', .6)

# ---- the bell: "tin" at frame 0, and again when the statue appears today (the loop back to the hook)
add(sfx, bell(660), 0.0, 1.5)
add(sfx, bell(495, 5.0, .8), W('Peter', 2) - .75, 1.0)

# ---- SFX, about one per second, pinned to words
S('pop', W('Empress'), .4); S('whoosh', W('move') - .15, .5); add(sfx, rumble(1.2), W('rock'), .5)
S('ding', W('house'), .35)
S('whoosh', W('sat') - .3, .45); S('thud', W('sat') + .08, .7); S('wah', W('down') + .1, .25)
S('whoosh', W('waited') - .15, .4); S('sparkle', W('snow'), .55)
S('whoosh', W('You') - .15, .55); add(sfx, A.music_sting('dun'), W('Russia'), .45)
S('pop', W('Catherine'), .5); S('pop', W('pedestal') + .2, .4); S('boing', W('Peter') + .1, .3)
S('whoosh', W('swamp') - .2, .5); S('splash', W('swamp'), .35); S('step', W('outside'), .3); S('step', W('Petersburg'), .3)
S('ding', W('perfect'), .45); S('sparkle', W('rock', 2), .35)
S('whoosh', W('Locals') - .15, .45); S('thunder', W('Thunder') - .02, .9)
S('whoosh', W('problem') - .15, .45); S('thud', W('heaviest'), .6); S('splash', W('mud'), .55); S('gulp', W('mud') + .3, .4)
S('whoosh', W('engineers') - .15, .45); S('laugh', W('laugh') - .1, .55)
S('whoosh', W('Itll') - .15, .4); S('slide_down', W('sink'), .35)
S('whoosh', W('Marinos') - .15, .5); S('pop', W('Carburis'), .4)
for k in range(4): S('click', W('builds') + .1 + k * .18, .35)
S('thud', W('sledge'), .45)
S('whoosh', W('two') - .15, .45); S('slide_up', W('groove'), .3)
S('whoosh', W('into') - .15, .45)
for k, t0 in enumerate([W('drops') + .18, W('balls') + .23, W('balls') + .58, W('balls') + .88]):
    S('clank', t0, .45); S('ding', t0 + .02, .25)
S('whoosh', W('balls', 2) - .15, .5); S('boing', W('mountain'), .4)
S('laugh', W('Now') - .1, .5); S('murmur', W('city'), .35); S('laugh', W('laughing'), .5)
S('whoosh', W('then', 2) - .2, .55); S('freeze', W('winter'), .5)
S('whoosh', W('swamp', 2) - .15, .4); add(sfx, crack(.7), W('freezes'), .7); S('thud', W('solid'), .5)
S('whoosh', W('mountain', 2) - .15, .45); S('creak', W('starts'), .6)
add(sfx, rumble(W('why') - W('starts') - .2, 5), W('starts') + .1, .35); S('thud', W('roll'), .8)
S('whoosh', W('Hundreds') - .15, .45)
for k in range(5): S('creak', W('men') + k * .45, .3); S('creak', W('turn') + k * .4 + .2, .2)
S('whoosh', W('Drummers') - .15, .45)
for k in range(8): S('thud', W('Drummers') + .05 + k * .227, .45 if k % 2 == 0 else .3)
S('whoosh', W('Behind') - .15, .45)
for k in range(7): S('step', W('grab') + k * .2, .4)
S('clank', W('front'), .45)
S('whoosh', W('Stonemasons') - .15, .45)
for k in range(6): S('clank', W('carve') + k * .23, .3)
S('whoosh', W('January') - .15, .45); S('sparkle', W('Empress', 2), .4); S('ooh', W('glides'), .45)
S('whoosh', W('glides') - .3, .3)
S('whoosh', W('why') - .15, .45); S('sparkle', W('snow', 2), .4)
S('whoosh', W('Because') - .15, .5); S('ding', W('road'), .5)
S('whoosh', W('ball') - .15, .45); S('scratch', W('drag'), .5); S('slide_up', W('rolls'), .45); S('tada', W('rolls') + .25, .35)

mus_d = mus * 10 ** (-0 / 20)
env = A.envelope_follow(buf_v, .03, .4); env = env / (env.max() + 1e-9)
mus_d = mus * 10 ** (-9 * np.clip(env * 3, 0, 1) / 20)
mix = buf_v * 1.0 + mus_d * .2 + sfx * .5
mix = mix[:int(DUR * SR)]
mix *= .95 / np.abs(mix).max()
os.makedirs(os.path.join(D, 'audio'), exist_ok=True)
sf.write(os.path.join(D, 'audio', 'mix.wav'), np.stack([mix, mix], 1).astype(np.float32), SR)
print('mix', round(DUR, 2), 's')
