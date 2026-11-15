"""Soundtrack for the vertical short: procedural score, ambience, SFX, voice; plus the SRT.

python -m episodes.japan_johatsu.mix OUT.wav OUT.srt
"""
import json
import math
import re
import sys

import numpy as np
import soundfile as sf

from cinecode import audio as A
from cinecode import tts
from episodes.japan_johatsu.shots import END
from episodes.japan_johatsu.timing import TAKE, words

SR = A.SR
N = int(END * SR)


def db(x):
    return 10 ** (x / 20)


# ---------------------------------------------------------------- instruments
def piano(m, d=2.5, vel=0.6):
    """Soft felt piano: a few slightly inharmonic partials, fast attack, warm decay."""
    t = A.t_arr(d)
    f = A.midi_f(m)
    x = np.zeros_like(t)
    for k, (amp, dec) in enumerate(((1.0, 1.6), (0.45, 0.9), (0.22, 0.6), (0.1, 0.35), (0.05, 0.25))):
        fk = f * (k + 1) * (1 + 0.0004 * (k + 1) ** 2)
        x += amp * np.sin(2 * np.pi * fk * t) * np.exp(-t / dec)
    att = np.clip(t / 0.006, 0, 1)
    hammer = A.lp(A.noise(0.03, int(m)), 1200) * np.exp(-np.arange(int(0.03 * SR)) / (0.006 * SR)) * 0.15
    x = x * att
    x[:len(hammer)] += hammer
    return A.fade(A.lp(x, 2600) * vel * 0.32, 0.001, 0.3)


def warm_pad(notes, d, bright=0.25, amp=0.18):
    t = A.t_arr(d)
    x = np.zeros_like(t)
    for m in notes:
        for det in (-0.06, 0.05):
            f = A.midi_f(m) * 2 ** (det / 12)
            x += np.sin(2 * np.pi * f * t + np.sin(2 * np.pi * 0.2 * t) * 0.5)
            x += 0.35 * (2 * ((f * t) % 1) - 1)
    x = A.lp(x, 300 + 1500 * bright)
    e = A.env_adsr(len(t), min(1.2, d * 0.4), 0.3, 0.9, min(1.5, d * 0.4))
    return x * e * amp / max(1, len(notes))


def pulse(f=49.0, d=0.5, amp=0.5):
    t = A.t_arr(d)
    x = np.sin(2 * np.pi * f * t * (1 + 0.15 * np.exp(-t * 20))) * np.exp(-t * 7)
    return x * amp


def koto(m, d=1.6, vel=0.5):
    return A.pluck(m, d, bright=0.35, seed=m) * vel


# ---------------------------------------------------------------- score
BPM = 84
BEAT = 60 / BPM
# chord roots / voicings (D minor colour), 1 chord per bar (4 beats)
CHORDS = [
    [50, 57, 62, 65], [46, 53, 58, 62], [43, 50, 55, 58], [45, 52, 57, 61],   # Dm Bb Gm A
    [50, 57, 62, 65], [46, 53, 58, 65], [48, 55, 60, 64], [45, 52, 57, 64],   # Dm Bb C Asus
]
MOTIF = [(0, 74), (1, 72), (1.5, 69), (2, 70), (3, 69)]  # beat offsets in bar, midi


def score():
    mus = np.zeros(N + SR * 3)
    bar = 4 * BEAT
    nbars = int(END / bar) + 2
    for b in range(nbars):
        t0 = b * bar
        ch = CHORDS[b % len(CHORDS)]
        # section intensities
        sec_pulse = 1.0 if 12.1 <= t0 < 60.0 else (0.5 if 60 <= t0 < 63 else 0.0)
        A.add(mus, warm_pad(ch, bar + 0.8, bright=0.18 + 0.15 * (40 < t0 < 60), amp=0.22), t0)
        # bass note
        A.add(mus, warm_pad([ch[0] - 12], bar + 0.5, bright=0.1, amp=0.25), t0)
        # felt piano motif every other bar, sparser during the search
        if t0 < 63 and b % 2 == 0:
            for off, m in MOTIF:
                tm = t0 + off * BEAT
                if tm < END - 1:
                    A.add(mus, piano(m - (0 if b % 4 == 0 else 2), 2.4, 0.5), tm)
        elif t0 < 63:
            for k, m in enumerate(ch[1:]):
                A.add(mus, piano(m + 12, 2.0, 0.28), t0 + k * BEAT * 0.5 + BEAT)
        # heartbeat pulse
        if sec_pulse:
            for k in range(4):
                tb = t0 + k * BEAT
                if 12.1 <= tb < 63:
                    A.add(mus, pulse(46, 0.6, 0.55 * sec_pulse), tb)
                    A.add(mus, pulse(46, 0.4, 0.25 * sec_pulse), tb + 0.22)
        # koto colour in the Japan/map section
        if 44.5 <= t0 < 60:
            for k, m in enumerate((ch[1] + 12, ch[2] + 12, ch[3] + 12)):
                A.add(mus, koto(m, 1.4, 0.18), t0 + (k * 1.5 + 0.5) * BEAT)
    # final: unresolved held piano + pad on the last line
    A.add(mus, piano(62, 5.0, 0.55), 63.25)
    A.add(mus, piano(69, 5.0, 0.35), 63.25)
    A.add(mus, piano(70, 5.0, 0.4), 64.5)
    A.add(mus, warm_pad([46, 53, 58, 62, 69], 4.5, bright=0.15, amp=0.3), 63.2)
    mus = mus[:N]
    # global music envelope: lift slightly over the map/jōhatsu section, dip under the report reveal
    t = np.arange(N) / SR
    env = np.interp(t, [0, 3, 12, 27, 33, 44, 52, 58, 60.2, 63.0, 66.5, END],
                    [0.75, 0.8, 0.85, 0.9, 0.8, 0.85, 1.0, 1.05, 0.75, 0.6, 0.9, 0.0])
    return A.lp(mus, 7000) * env


# ---------------------------------------------------------------- ambience
def amb_bed():
    t = np.arange(N) / SR
    room = A.lp(A.noise(END, 301), 220) * 0.05
    city = A.bp(A.noise(END, 302), 80, 600) * 0.06 * (0.7 + 0.3 * np.sin(2 * np.pi * 0.07 * t))
    night = np.zeros(N)
    # crickets-ish distant chirps for night exteriors
    rng = np.random.default_rng(3)
    for k in range(260):
        tt = rng.uniform(0, END)
        d = 0.05
        tc = A.t_arr(d)
        ch = np.sin(2 * np.pi * 4300 * tc) * np.sin(np.pi * tc / d) ** 2 * 0.012
        A.add(night, ch, tt)
    # neon buzz in neon/office shots
    hum = (np.sin(2 * np.pi * 120 * t) + 0.4 * np.sin(2 * np.pi * 240 * t)) * 0.012
    def gate(spans):
        g = np.zeros(N)
        for a, b in spans:
            i0, i1 = int(a * SR), int(b * SR)
            g[i0:i1] = 1
        k = int(0.15 * SR)
        g = np.convolve(g, np.ones(k) / k, mode="same")
        return g
    day = A.bp(A.noise(END, 303), 200, 2500) * 0.035
    out = room + city * gate([(0, 30.88), (39.5, END)]) + night * gate([(0, 21.9), (60, END)]) \
        + hum * gate([(3.34, 6.86), (21.9, 27.0)]) + day * gate([(29.2, 38.5)]) * 1.0
    return out


# ---------------------------------------------------------------- sfx
def noise_burst(d, lo, hi, tau, seed):
    return A.bp(A.noise(d, seed), lo, hi) * A.exp_env(int(d * SR), tau)


def tone(f, d, amp=0.2, att=0.005, rel=0.1, kind="sine"):
    t = A.t_arr(d)
    x = np.sin(2 * np.pi * f * t) if kind == "sine" else np.sign(np.sin(2 * np.pi * f * t)) * 0.5
    return A.fade(x * amp, att, rel)


def hook_sfx(add):
    """Revised opening (0-3.34 s): counting notes -> payment -> footsteps, door latch."""
    from episodes.japan_johatsu.hook import CARRY, FLICKS
    for k, f in enumerate(FLICKS):
        snap = noise_burst(0.06, 2500, 9000, 0.010, 400 + k) + noise_burst(0.06, 700, 2500, 0.006, 410 + k) * 0.6
        add(snap, max(0.0, f + 0.01), -20)                      # note peeled off the stack
        add(A.lp(A.noise(0.08, 420 + k), 1800) * A.exp_env(int(0.08 * SR), 0.015), f + CARRY, -27)  # lands
    d = 0.42
    sl = A.bp(A.noise(d, 430), 1200, 5000) * np.sin(np.linspace(0, np.pi, int(d * SR))) ** 1.5
    add(sl * 0.5, 0.82, -19)                                    # stack slid across the wood
    add(A.bp(A.noise(0.12, 431), 300, 1400) * A.exp_env(int(0.12 * SR), 0.04), 1.42, -22)   # glove grabs
    add(A.sfx_whoosh(0.3, 400, 1800), 1.47, -30)
    for k, (tt, g) in enumerate(((1.76, -24), (1.97, -25), (2.19, -27), (2.42, -29), (2.64, -31))):
        add(A.sfx_step(k + 20), tt, g)                          # quiet footsteps
    add(A.bp(A.noise(0.25, 432), 150, 700) * np.sin(np.linspace(0, np.pi, int(0.25 * SR))), 2.22, -30)
    add(A.sfx_click(), 2.46, -15)                               # latch
    add(A.sfx_thud(95, 0.25), 2.46, -21)


AMB_DIP = (2.46, 2.95, -7.0)  # brief drop in ambience after the door shuts


def amb_dip():
    t = np.arange(N) / SR
    a, b, g = AMB_DIP
    k = np.clip(np.minimum((t - a) / 0.05, (b - t) / 0.25), 0, 1)
    return 1 - (1 - db(g)) * k


def sfx_bed():
    fx = np.zeros(N + SR * 4)
    add = lambda x, t, g=0.0: A.add(fx, x * db(g), t)
    hook_sfx(add)
    # neon flicker + card
    for k, tt in enumerate((3.4, 3.48, 3.62)):
        add(noise_burst(0.05, 1500, 6000, 0.01, 40 + k), tt, -26)
    add(A.sfx_swish(), 5.55, -20)
    # job box thump
    add(A.sfx_thud(90, 0.3), 6.9, -24)
    # debt papers slide + stamps
    for k, tt in enumerate((7.9, 8.22, 8.57)):
        add(A.sfx_whoosh(0.3, 1500, 5000), tt, -24)
        add(A.sfx_thud(110, 0.25), tt + 0.36, -18)
    # phone ringback (Japanese style: 400 Hz, 16 Hz warble)
    t = A.t_arr(1.0)
    ring = np.sin(2 * np.pi * 400 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 16 * t)) * 0.12
    add(A.fade(ring, 0.01, 0.05), 11.15, -10)
    # midnight tick + notification chime
    add(A.sfx_click(), 12.44, -18)
    add(tone(1318, 0.5, 0.15, rel=0.4) + tone(1760, 0.5, 0.1, rel=0.4), 12.58, -14)
    # van: approach rumble + tyres, light click, engine off
    d = 2.7
    t = A.t_arr(d)
    env = np.interp(t, [0, 1.4, 1.6, 2.0, d], [0.2, 1.0, 0.9, 0.3, 0.0])
    eng = (np.sin(2 * np.pi * 42 * t) + 0.5 * np.sin(2 * np.pi * 84 * t)) * 0.2 + A.lp(A.noise(d, 9), 300) * 0.5
    tyres = A.bp(A.noise(d, 10), 300, 2500) * 0.15
    add((eng + tyres) * env, 12.95, -12)
    add(A.sfx_click(), 14.15, -16)
    # crew: door slide, soft steps
    add(A.bp(A.noise(0.6, 11), 300, 2000) * np.sin(np.linspace(0, np.pi, int(0.6 * SR))) * 0.5, 15.65, -18)
    for k in range(8):
        add(A.sfx_step(k), 15.85 + k * 0.2, -28)
    # packing: tape rips and box drops
    for k, tt in enumerate((17.55, 17.95, 18.3, 18.75)):
        add(noise_burst(0.35, 2000, 8000, 0.12, 60 + k), tt, -24)
        add(A.sfx_thud(80, 0.3), tt + 0.15, -24)
    # marker scribble on label
    for k in range(10):
        add(noise_burst(0.06, 2500, 7000, 0.02, 80 + k), 19.4 + k * 0.06, -30)
    # line cancelled: descending error tone
    sw = A.sweep(520, 260, 0.45) * A.exp_env(int(0.45 * SR), 0.2) * 0.25
    add(sw, 20.2, -12)
    # fee card + counter ticks + settle
    add(A.sfx_swish(), 21.95, -20)
    add(A.sfx_click(), 22.86, -16)
    for k in range(12):
        add(A.sfx_click(), 23.9 + k * 0.06, -24)
    add(tone(880, 0.6, 0.12, rel=0.5), 24.6, -16)
    # flipboard clatter
    for k in range(28):
        add(noise_burst(0.03, 1500, 7000, 0.006, 100 + k), 27.2 + k * 0.05, -22)
    # highway pass
    add(A.sfx_whoosh(1.6, 150, 1200), 27.3, -18)
    # morning: birds
    for k in range(5):
        tt = 29.3 + k * 0.33
        add(A.sweep(3200, 4200, 0.08) * 0.1, tt, -22)
    # mom's hurried steps
    for k in range(11):
        add(A.sfx_step(k + 3), 30.95 + k * 0.21, -26)
    # checklist
    add(A.sfx_swish(), 33.45, -22)
    add(tone(1046, 0.18, 0.12), 33.83, -18)
    add(tone(1046, 0.18, 0.12), 34.68, -18)
    add(tone(196, 0.3, 0.2, kind="sq"), 36.27, -26)
    add(A.sfx_thud(60, 0.5), 37.42, -18)
    # drawer slam
    add(A.sfx_clank(), 39.15, -18)
    add(A.sfx_thud(70, 0.4), 39.15, -14)
    # detective office: clock ticks
    for k in range(5):
        add(A.sfx_click(), 39.7 + k * 0.5, -32)
    # access denied buzz
    for k in range(2):
        add(tone(150, 0.16, 0.25, kind="sq"), 42.3 + k * 0.24, -22)
    # map: swell + dot blips + counter
    add(A.sfx_whoosh(1.2, 100, 900), 44.4, -22)
    rng = np.random.default_rng(8)
    for k in range(40):
        add(tone(rng.uniform(900, 1500), 0.05, 0.08, rel=0.04), 45.0 + k * 0.12, -30)
    # found chimes, vanish air
    for k, m in enumerate((72, 76, 79)):
        add(piano(m, 1.5, 0.25), 52.0 + k * 0.2, -10)
    add(A.sfx_whoosh(1.4, 3000, 400), 54.3, -24)
    # jōhatsu: steam hiss on "evaporated"
    hs = A.hp(A.noise(1.6, 120), 3000) * np.sin(np.linspace(0, np.pi, int(1.6 * SR))) ** 2 * 0.25
    add(hs, 58.9, -16)
    # kitchen clock
    for k in range(6):
        add(A.sfx_click(), 60.3 + k * 0.5, -34)
    # typewriter keys, one per visible character
    for s_, a_, b_ in (("Your son", 63.25, 64.1), ("chose to leave.", 64.5, 65.6)):
        n = len(s_)
        for k in range(n):
            tt = a_ + (b_ - a_) * k / n
            add(noise_burst(0.05, 1200, 6000, 0.008, 200 + k) + A.sfx_thud(220, 0.05)[:2400] * 0.3, tt, -20)
    return fx[:N]


# ---------------------------------------------------------------- voice + master
def voice():
    v = tts.read_wav(TAKE).astype(np.float64)
    v = A.resample(v, tts.SR, SR)
    v = A.hp(v, 75)
    # gentle presence + soft compression
    v = v + A.bp(v, 2500, 6000) * 0.12
    env = A.envelope_follow(v, 0.005, 0.12)
    thr = 0.18
    gain = np.where(env > thr, (thr + (env - thr) * 0.4) / np.maximum(env, 1e-9), 1.0)
    v = v * gain
    out = np.zeros(N)
    out[:min(N, len(v))] = v[:N]
    return out


def stems_st(sfx_fn=None, dip=True):
    """Stereo mix before the final peak normalisation (shared by mix() and the hook splice)."""
    v = voice()
    mus = score()
    amb = amb_bed()
    fx = (sfx_fn or sfx_bed)()
    # duck music under the voice
    venv = A.envelope_follow(v, 0.05, 0.6)
    duck = 1 - 0.45 * np.clip(venv / (np.percentile(venv, 90) + 1e-9), 0, 1)
    v = v / (np.percentile(np.abs(v), 99.5) + 1e-9) * 0.62
    mus = mus / (np.percentile(np.abs(mus), 99.5) + 1e-9) * 0.62 * db(-15) * duck
    amb = amb / (np.percentile(np.abs(amb), 99.5) + 1e-9) * db(-27)
    if dip:
        amb = amb * amb_dip()
    fx = fx / (np.max(np.abs(fx)) + 1e-9) * db(-11)
    dry = v + mus + amb + fx
    # stereo: music/amb slightly wide, voice centred
    wide_l = A.lp(mus + amb, 9000)
    wide_r = np.roll(mus + amb, int(0.011 * SR))
    L = v + fx + wide_l
    R = v + fx + wide_r
    return np.stack([L, R], 1)


def mix(out_wav):
    st = stems_st()
    st = st / (np.max(np.abs(st)) + 1e-9) * 0.89
    # tail fade
    t = np.arange(N) / SR
    st *= np.clip((END - t) / 0.6, 0, 1)[:, None]
    sf.write(out_wav, st.astype(np.float32), SR, subtype="PCM_24")


# ---------------------------------------------------------------- SRT (phrase level)
def srt(path):
    ws = words()
    sents, cur = [], []
    for w in ws:
        cur.append(w)
        if re.search(r"[.?]$", w["w"]):
            sents.append(cur)
            cur = []
    if cur:
        sents.append(cur)

    def tlen(g):
        return len(" ".join(x["w"] for x in g))
    phrases = []
    for g in sents:
        if tlen(g) <= 84:
            phrases.append(g)
            continue
        # split a long sentence at the comma nearest its middle
        best = min((i for i in range(1, len(g)) if g[i - 1]["w"].endswith(",")),
                   key=lambda i: abs(tlen(g[:i]) - tlen(g[i:])), default=len(g) // 2)
        phrases += [g[:best], g[best:]]

    def two_lines(txt):
        if len(txt) <= 42:
            return txt
        ws_ = txt.split()
        best = min(range(1, len(ws_)), key=lambda i: abs(len(" ".join(ws_[:i])) - len(" ".join(ws_[i:]))))
        return " ".join(ws_[:best]) + "\n" + " ".join(ws_[best:])

    def ts(x):
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lines = []
    for i, p in enumerate(phrases):
        txt = " ".join(x["w"] for x in p)
        txt = two_lines(txt
               .replace("fifty thousand yen", "¥50,000").replace("three hundred thousand", "¥300,000")
               .replace("eighty thousand", "80,000"))
        txt = (txt.replace("fifty thousand yen", "¥50,000").replace("three hundred thousand", "¥300,000")
               .replace("eighty thousand", "80,000"))
        s = p[0]["s"]
        e = min(p[-1]["e"] + 0.25, phrases[i + 1][0]["s"] - 0.02) if i + 1 < len(phrases) else p[-1]["e"] + 0.6
        lines.append(f"{i + 1}\n{ts(s)} --> {ts(e)}\n{txt}\n")
    open(path, "w", encoding="utf-8").write("\n".join(lines))


if __name__ == "__main__":
    mix(sys.argv[1])
    srt(sys.argv[2])
