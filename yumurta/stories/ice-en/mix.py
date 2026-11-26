"""Voice + music + SFX for the ice-carrier story -> audio/mix.wav (-14 LUFS is set at the final mux).
Measured on the reference (r11): the music sits ~14 dB under the voice, and there is roughly one small SFX per second.
Every cue is pinned to a word of voice/words.json, like the picture.
usage (repo root): python3 yumurta/stories/ice-en/mix.py
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


def gunshot(seed=5):              # a pistol crack: a sharp noise burst, a low thump, a short room tail
    n = int(.9 * SR); tt = np.arange(n) / SR
    x = noise(.9, 300, 9000, .0005, .5, seed) * np.exp(-tt / .05) * 1.0
    x += np.sin(2 * np.pi * 70 * tt) * np.exp(-tt / .06) * .8
    x += noise(.9, 400, 3000, .01, .6, seed + 1) * np.exp(-tt / .25) * .18
    return x / np.abs(x).max()


def ricochet(d=.9, seed=6):        # the "pew-iiiooo" whine of a bouncing bullet
    tt = np.arange(int(d * SR)) / SR
    f = 3200 * np.exp(-tt * 1.6) + 900
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / (d * .5))
    x[:int(.03 * SR)] += noise(.03, 2000, 9000, .001, .01, seed) * .8
    return x / np.abs(x).max()


def shatter(seed=7):               # ice breaking: a crack, then many tiny glassy tinkles
    d = 1.6; n = int(d * SR); tt = np.arange(n) / SR; R = np.random.default_rng(seed)
    x = noise(d, 1500, 9000, .001, .4, seed) * np.exp(-tt / .08)
    for k in range(40):
        t0 = R.uniform(0, 1.2); f = R.uniform(2500, 7000); i0 = int(t0 * SR); m = int(.15 * SR)
        if i0 + m < n: x[i0:i0 + m] += np.sin(2 * np.pi * f * np.arange(m) / SR) * np.exp(-np.arange(m) / SR / .03) * R.uniform(.1, .35)
    return x / np.abs(x).max()


def buzz(d, seed=8):               # an angry bee: a rough 220 Hz saw, wobbling in pitch and loudness
    tt = np.arange(int(d * SR)) / SR
    f = 230 + 40 * np.sin(2 * np.pi * 7 * tt) + 25 * np.sin(2 * np.pi * 2.3 * tt)
    ph = np.cumsum(f) / SR; x = 2 * (ph % 1) - 1
    x = A.lp(x, 2500) if hasattr(A, 'lp') else x
    return x * (.7 + .3 * np.sin(2 * np.pi * 11 * tt)) * np.minimum(1, tt / .05) * np.minimum(1, (d - tt) / .1)


def ping():                        # sonar
    tt = np.arange(int(1.4 * SR)) / SR
    return np.sin(2 * np.pi * 1180 * tt) * np.exp(-tt / .35) * np.minimum(1, tt / .005)


def drone(d, seed=9):              # a distant propeller plane
    tt = np.arange(int(d * SR)) / SR
    x = np.sin(2 * np.pi * 95 * tt) * (.6 + .4 * np.sin(2 * np.pi * 24 * tt)) + noise(d, 80, 600, .3, .4, seed) * .3
    return x * np.minimum(1, tt / .4) * np.minimum(1, (d - tt) / .5)


def music(a, b, name, g):
    xf = .25; a0 = max(0, a - xf); seg = A.track(name, b - a0 + xf); m = len(seg); env = np.ones(m); k = int(xf * SR)
    env[:k] = np.linspace(0, 1, k); env[-k:] = np.linspace(1, 0, k); add(mus, seg * env, a0, g)


# ---- music: suspense under the hook and the war; quirky for Pyke, the laugh and the meat locker; a hush in the bath;
#      suspense for Quebec; warm for the reveal
music(.6, W('So') - .1, 'suspense', .45)
music(W('So') - .1, W('Then') - .1, 'quirky', .55)
music(W('Then') - .1, W('Now') - .1, 'room', .5)
music(W('Now') - .1, W('secret', 2) - .2, 'suspense', .5)
music(W('secret', 2) - .2, DUR, 'warm', .6)

# ---- the bell: a short quiet "tin" at frame 0 (user: very short, very quiet), and a softer one at the lake
add(sfx, bell(660, .6, k=.15), 0.0, .5)
add(sfx, bell(495, .7, .8, k=.15), W('But', 2) - .1, .35)

# ---- SFX, about one per second, pinned to words
S('click', W('admiral'), .35)
S('whoosh', W('pulled') - .15, .45); S('clank', W('pistol'), .4)
S('whoosh', W('front') - .15, .45); S('gasp', W('generals') - .05, .45)
S('whoosh', W('shot') - .2, .4); add(sfx, gunshot(1), W('shot') + .04, .9); S('thud', W('shot') + .06, .5)
S('whoosh', W('You') - .15, .55); add(sfx, ping(), W('German'), .35); S('splash', W('sinking'), .45)
add(sfx, drone(W('Britain') - W('Atlantic') + .3), W('Atlantic') - .3, .25)
S('boing', W('reach'), .3)
S('whoosh', W('Britain') - .2, .45); S('clank', W('steel'), .45); S('wah', W('steel') + .25, .35)
S('whoosh', W('So') - .15, .5); S('pop', W('Geoffrey'), .4); S('ding', W('crazy'), .5); S('sparkle', W('idea'), .4)
S('whoosh', W('aircraft') - .15, .55); S('freeze', W('made'), .5); add(sfx, A.music_sting('dun'), W('ice', 2), .35)
S('whoosh', W('Two') - .15, .45); S('slide_up', W('thousand'), .4)
S('whoosh', W('generals', 2) - .15, .45); S('laugh', W('laugh') - .1, .6); S('laugh', W('ships') , .35)
S('whoosh', W('ice', 3) - .15, .35)
S('whoosh', W('But') - .15, .5); S('creak', W('hidden'), .4); S('freeze', W('frozen'), .4)
S('whoosh', W('scientists') - .15, .45)
for k in range(3): S('swish', W('freezing') + k * .3, .25)
S('whoosh', W('secret') - .15, .4); S('ooh', W('ingredient'), .35)
S('whoosh', W('Then') - .15, .5)
for k in range(4): S('step', W('Lord') + k * .3, .3)
S('pop', W('Mountbatten'), .35); S('whoosh', W('who') - .15, .4); S('bonk', W('bath'), .3)
S('whoosh', W('Splash') - .25, .4); S('splash', W('Splash') - .05, .9); S('drip', W('hot'), .4)
S('whoosh', W('doesnt', 2) - .32, .35); S('sparkle', W('melt'), .5); S('tada', W('melt') + .2, .3)
S('whoosh', W('Or') - .15, .35); S('scratch', W('claimed'), .4)
S('whoosh', W('Now') - .15, .55); add(sfx, A.music_sting('dun'), W('Quebec'), .4)
S('whoosh', W('blocks') - .15, .4); S('pop', W('blocks'), .35); S('pop', W('table'), .35)
S('whoosh', W('He') - .15, .4); add(sfx, gunshot(3), W('shoots') + .06, .9); add(sfx, shatter(), W('shoots') + .08, .7)
S('whoosh', W('Plain') - .15, .35)
S('whoosh', W('aims') - .15, .4); S('heartbeat', W('aims'), .5)
S('whoosh', W('bullet') - .16, .35); add(sfx, gunshot(4), W('bullet') - .08, .9); add(sfx, ricochet(), W('bounces'), .7)
S('whoosh', W('buzzes') - .15, .4); add(sfx, buzz(W('Nobody') - W('buzzes') - .1), W('buzzes'), .35)
for k in range(4): S('bonk', W('around') + k * .35, .3)
S('whoosh', W('Nobody') - .12, .45); S('crickets', W('Nobody'), .35)
S('whoosh', W('secret', 2) - .25, .5); S('slide_down', W('Sawdust') - .3, .4); S('tada', W('Sawdust'), .45)
S('sparkle', W('Wood'), .35); S('pop', W('together'), .35); S('freeze', W('barely'), .35)
S('whoosh', W('ship') - .4, .5); S('scratch', W('never'), .45); S('poof', W('built'), .4)
S('whoosh', W('But', 2) - .2, .5); S('splash', W('bottom') - .3, .5); S('suck', W('bottom'), .3); S('ding', W('Canada'), .4)

mus_d = mus * 10 ** (-0 / 20)
env = A.envelope_follow(buf_v, .03, .4); env = env / (env.max() + 1e-9)
mus_d = mus * 10 ** (-9 * np.clip(env * 3, 0, 1) / 20)
mix = buf_v * 1.0 + mus_d * .2 + sfx * .5
mix = mix[:int(DUR * SR)]
mix *= .95 / np.abs(mix).max()
os.makedirs(os.path.join(D, 'audio'), exist_ok=True)
sf.write(os.path.join(D, 'audio', 'mix.wav'), np.stack([mix, mix], 1).astype(np.float32), SR)
print('mix', round(DUR, 2), 's')
