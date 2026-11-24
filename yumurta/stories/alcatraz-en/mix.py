"""Voice + music + SFX for the Alcatraz story -> audio/mix.wav (-14 LUFS is set at the final mux).
Measured on the reference (r11): the music sits ~14 dB under the voice, and there is roughly one small SFX per second.
Every cue is pinned to a word of voice/words.json, like the picture.
usage (repo root): python3 yumurta/stories/alcatraz-en/mix.py
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


def drill(d):                      # a vacuum motor with a bit in concrete: a buzzing saw tone, grit on top
    tt = np.arange(int(d * SR)) / SR; f = 118 + 6 * np.sin(tt * 13)
    saw = 2 * ((np.cumsum(f) / SR) % 1) - 1
    x = .6 * A.lp(saw, 1800) + .35 * noise(d, 1500, 5000, seed=4)
    return x * np.minimum(1, tt / .05) * np.minimum(1, (d - tt) / .1)


def music(a, b, name, g):
    xf = .25; a0 = max(0, a - xf); seg = A.track(name, b - a0 + xf); m = len(seg); env = np.ones(m); k = int(xf * SR)
    env[:k] = np.linspace(0, 1, k); env[-k:] = np.linspace(1, 0, k); add(mus, seg * env, a0, g)


# ---- music: sneaky quirky bed, the accordion hour (a bright festival bed), suspense at night, a chase on the roof,
#      suspense for the count, silence for the roll, then a low end
music(0, W('evening') - .4, 'quirky', .55)
music(W('evening') - .4, W('Then') - .1, 'festival', .75)
music(W('Then') - .1, W('fourth') - .3, 'quirky', .55)
music(W('fourth') - .3, W('three', 2) - .1, 'suspense', .6)
music(W('three', 2) - .1, W('All') - .1, 'chase', .55)
music(W('All') - .1, W('rolled') - .1, 'suspense', .55)
music(W('were') - .3, DUR, 'rain', .5)

# ---- SFX, one or so per second
S('whoosh', 0.0, .4); S('scratch', .7, .25); S('scratch', 1.5, .25)
S('swish', W('soap') - .15, .5); S('pop', W('hair'), .6); S('sparkle', W('hair') + .1, .3)
S('whoosh', W('barbershop') - .15, .5)
for k in range(4): S('step', W('barbershop') + k * .38, .35)
S('whoosh', W('see') - .15, .55); add(sfx, A.music_sting('dun'), W('Alcatraz'), .5)
for w in ['caught', 'shot', 'drowned']: S('thud', W(w), .7)
S('splash', W('drowned') + .1, .3)
S('whoosh', W('Frank') - .15, .5); S('pop', W('Frank'), .5); S('pop', W('Anglin'), .5); S('pop', W('Anglin') + .15, .4)
S('whoosh', W('stole') - .15, .45); S('sparkle', W('spoons'), .45); S('ding', W('spoons') + .1, .35)
S('whoosh', W('scraped') - .15, .45)
for k in range(6): S('scratch', W('scraped') + .05 + k * .33, .35)
S('freeze', W('Too') - .05, .55)
S('whoosh', W('evening') - .55, .45)
S('whoosh', W('Then') - .15, .45); add(sfx, drill(2.3), W('drill') - .05, .45)
S('whoosh', W('hid') - .15, .45); S('click', W('hid') + .3, .6)
for k in range(4): S('swish', W('painted') + k * .2, .25)
S('ding', W('match'), .45)
S('whoosh', W('Next') - .15, .5)
for k in range(8): S('flap', W('Next') + .1 + k * .14, .3)
S('pop', W('fifty'), .5)
S('whoosh', W('stitched') - .15, .45)
for k in range(5): S('click', W('stitched') + k * .17, .3)
S('whoosh', W('sealed') - .15, .45); add(sfx, noise(1.6, 3000, 9000, .05, .4, 7), W('steam') - .1, .3)
S('boing', W('blow') + .1, .45)
S('whoosh', W('accordion', 2) - .15, .45)
for k in range(5): S('suck', W('accordion', 2) + .1 + k * .3, .3)
S('slide_up', W('pump') - .2, .45); S('cheer', W('pump') + .35, .35)
S('whoosh', W('fourth') - .45, .45)
for k in range(4): S('clank', W('couldnt') + k * .3, .35)
add(sfx, A.music_sting('wah'), W('left') + .05, .5)
S('whoosh', W('night') - .5, .45); add(sfx, A.music_sting('dun'), W('June'), .45); S('crickets', W('night'), .25)
S('whoosh', W('three', 2) - .15, .5)
for k in range(5): S('step', W('three', 2) + k * .22, .4)
S('slide_down', W('down') - .05, .45)
S('splash', W('paddled'), .5); S('splash', W('paddled') + .8, .35)
S('whoosh', W('All') - .15, .45)
for w, n in [('counted', 1), ('three', 3), ('sleeping', 1)]: S('flashlight', W(w, n) - .1, .4); S('ding', W(w, n), .3)
S('whoosh', W('morning') - .15, .45); S('creak', W('reached'), .4)
roll = W('rolled') - .1
S('slide_down', roll, .35); S('thud', roll + .32, .8); S('bonk', roll + .6, .4); S('bonk', roll + .85, .25)
S('gasp', W('floor', 2) + .05, .55); add(sfx, A.music_sting('dun'), W('floor', 2) + .1, .55)
S('whoosh', W('were') - .45, .45); S('splash', W('never'), .2)

mus_d = mus * 10 ** (-0 / 20)
env = A.envelope_follow(buf_v, .03, .4); env = env / (env.max() + 1e-9)
mus_d = mus * 10 ** (-9 * np.clip(env * 3, 0, 1) / 20)
mix = buf_v * 1.0 + mus_d * .2 + sfx * .5
mix = mix[:int(DUR * SR)]
mix *= .95 / np.abs(mix).max()
os.makedirs(os.path.join(D, 'audio'), exist_ok=True)
sf.write(os.path.join(D, 'audio', 'mix.wav'), np.stack([mix, mix], 1).astype(np.float32), SR)
print('mix', round(DUR, 2), 's')
