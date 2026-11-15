"""Soundtrack for "Can You Spot the Change?": narration + harbour ambience + light music + SFX.

Rules from the brief:
* the 12 s test has ambience only (no music, no narration, no cues tied to the colour change);
* gull calls are sparse, distant and scattered at fixed times independent of the hull animation;
* subtle suspense under the reveal, clean bed under the science, no outro sting.

usage: python -m episodes.spot_the_change.mix   -> build/spot_the_change/soundtrack.wav
"""
import json
import os

import numpy as np
import soundfile as sf

from cinecode import audio as A
from cinecode import tts
from episodes.spot_the_change.timeline import BUILD, ROOT

SR = A.SR


def place(buf, x, t, gain=1.0):
    A.add(buf, x * gain, t)


def gull_call(seed, dist=1.0):
    """Herring-gull style 'kyow' x 2-4, filtered for distance."""
    r = np.random.default_rng(seed)
    out = np.zeros(int(2.2 * SR))
    n = r.integers(2, 5)
    t = 0.0
    for k in range(n):
        d = 0.18 + r.random() * 0.12
        tt = A.t_arr(d)
        f0 = 1250 + r.random() * 300
        f = f0 * (1 - 0.35 * (tt / d) ** 0.7) * (1 + 0.03 * np.sin(2 * np.pi * 28 * tt))
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = sum(np.sin(h * ph) / h ** 1.4 for h in range(1, 7))
        x = x * (1 + 0.22 * np.sin(2 * np.pi * 90 * tt))         # slight roughness
        x = A.bp(x, 650, 3600) * A.env_adsr(len(tt), 0.015, 0.05, 0.7, 0.08)
        A.add(out, x, t)
        t += d + 0.08 + r.random() * 0.1
    out = A.lp(out, 3400 - 1600 * dist, order=4)
    # distance: a little smeared reverb
    ir = A.noise(0.6, seed + 1) * A.exp_env(int(0.6 * SR), 0.12) * 0.12
    wet = np.convolve(out, ir)[: len(out)]
    return A.norm(out * (1 - 0.5 * dist) + wet * dist, 0.5)


def water_amb(d, seed=3):
    t = A.t_arr(d)
    lap = A.bp(A.noise(d, seed), 150, 900) * (0.55 + 0.45 * np.sin(2 * np.pi * 0.31 * t) * np.sin(2 * np.pi * 0.13 * t + 1))
    slosh = A.bp(A.noise(d, seed + 1), 900, 3500) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.47 * t + 2)) ** 3 * 0.35
    wind = A.lp(A.noise(d, seed + 2), 350) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t)) * 0.7
    x = lap + slosh + wind
    return A.norm(x, 0.5)


def main():
    tl = json.load(open(os.path.join(BUILD, "timeline.json")))
    L = tl["lines"]
    dur = tl["duration"] + 0.3
    n = int(dur * SR)
    voice = np.zeros(n)
    amb = np.zeros(n)
    music = np.zeros(n)
    sfx = np.zeros(n)
    T0, T1 = tl["test"]

    # ---- narration (whole block takes keep their natural pauses)
    takes = json.load(open(os.path.join(ROOT, "assets", "audio", "tts", "spot_the_change", "takes.json")))
    for name, st in tl["blocks"].items():
        a = tts.read_wav(os.path.join(ROOT, takes[name]))
        a = A.resample(a.astype(np.float64), 24000, SR)
        a = A.hp(a, 75)
        # gentle level matching per take (speech RMS)
        act = a[np.abs(a) > 0.02]
        a = a * (0.16 / (np.sqrt(np.mean(act ** 2)) + 1e-9))
        place(voice, a, st)
    # soft knee limiter on the voice
    voice = np.tanh(voice * 1.6) / 1.6

    # ---- shots (mirror main.js key times)
    ex1 = L["e1"]["t0"] - 0.02
    words = L["e1"]["words"]
    ex2 = next(a for w, a, b in words if w.lower().strip(",.") == "or") - 0.06
    ex3 = L["e2"]["t0"] - 0.05
    end = L["n1"]["t0"] - 0.03
    sci = L["s1"]["t0"] - 0.02
    ba = L["p1"]["t0"] - 0.05
    replay = L["p2"]["t0"] + 0.2

    def env_between(a, b, fi=0.4, fo=0.4):
        t = np.arange(n) / SR
        return np.clip((t - a) / fi + 1, 0, 1) * np.clip((b - t) / fo + 1, 0, 1) * ((t >= a - fi) & (t <= b + fo))

    # ---- narration gate: 1 while the narrator speaks, smooth ramps, short gaps bridged (no pumping)
    t_ax = np.arange(n) / SR
    spans = sorted((d["t0"] - 0.25, d["t1"] + 0.35) for d in L.values())
    merged = []
    for a0, a1 in spans:
        if merged and a0 - merged[-1][1] < 0.9:
            merged[-1][1] = max(merged[-1][1], a1)
        else:
            merged.append([a0, a1])
    gate = np.zeros(n)
    for a0, a1 in merged:
        gate[max(0, int(a0 * SR)):min(n, int(a1 * SR))] = 1.0
    k = int(0.35 * SR)

    def boxcar(x):          # centred moving average via cumulative sum (O(n))
        c = np.concatenate([[0.0], np.cumsum(x)])
        lo = np.clip(np.arange(len(x)) - k // 2, 0, len(x)); hi = np.clip(lo + k, 0, len(x))
        return (c[hi] - c[lo]) / k
    gate = boxcar(boxcar(gate))                                         # ~0.7 s S-curve ramps

    # ---- harbour ambience
    NARR_DUCK_DB, TEST_DB, GULL_DB = -7.0, -3.5, -4.0
    wa = water_amb(dur)
    harbour = np.clip(env_between(0, ba, 0.01, 0.3) + env_between(sci, ex1, 0.3, 0.25) * 0.6 + env_between(end, dur, 0.25, 0.01), 0, 1)
    test_env = env_between(T0, T1, 0.6, 0.6)
    narr_gain = 1 - gate * (1 - 10 ** (NARR_DUCK_DB / 20))
    test_gain = 1 - np.clip(test_env, 0, 1) * (1 - 10 ** (TEST_DB / 20))
    water_old = wa * harbour * 0.30
    water_new = water_old * narr_gain * test_gain
    # distant gulls: fixed, sparse, unrelated to the hull animation; now only between narration lines
    rng = np.random.default_rng(77)
    gulls_old, gulls_new = np.zeros(n), np.zeros(n)
    tg = 0.8
    while tg < dur:
        in_h = tg < ba or (end < tg)
        if in_h:
            call = gull_call(int(tg * 100), dist=0.75 + 0.25 * rng.random())
            gain = 0.04 + 0.02 * rng.random()
            place(gulls_old, call, tg, gain)
            seg = gate[int(tg * SR):int((tg + 1.6) * SR)]
            if seg.size and seg.max() < 0.05:
                place(gulls_new, call, tg, gain * 10 ** (GULL_DB / 20))
        tg += 2.6 + rng.random() * 2.8
    amb += water_new + gulls_new
    # interior beds for the example sets
    room = A.amb_loop("room")
    rt = np.tile(room, n // len(room) + 1)[:n]
    amb += rt * env_between(ex1, end, 0.15, 0.15) * 0.35
    hum = np.sin(2 * np.pi * 120 * np.arange(n) / SR) * 0.012 + A.lp(A.noise(dur, 9), 600)[:n] * 0.03
    amb += hum * env_between(ex1, ex2, 0.1, 0.1)

    # ---- music (never during the test)
    m_play = A.track("quirky", dur)[:n]
    music += m_play * env_between(0.0, T0 - 0.6, 0.3, 0.6) * 0.55
    m_sus = A.track("suspense", dur)[:n]
    music += m_sus * env_between(L["r3"]["t0"], replay + 0.5, 1.2, 0.5) * 0.85
    m_warm = A.track("warm", dur)[:n]
    music += m_warm * env_between(sci + 0.3, ex1, 0.8, 0.2) * 0.55
    music += m_play * env_between(ex1, end, 0.2, 0.3) * 0.5
    music += m_warm * env_between(end, dur, 0.4, 1.2) * 0.45
    # duck under narration
    ve = A.envelope_follow(voice, 0.03, 0.4)
    duck = 1 - 0.55 * np.clip(ve / 0.08, 0, 1)
    music *= duck

    # ---- SFX
    for t in (sci, ex1, ex2, ex3, end, ba, replay):
        place(sfx, A.lp(A.sfx_whoosh(), 2500), t - 0.12, 0.15 if t == replay else 0.2)
    r0, r1 = L["r1"]["t0"] + 0.35, L["r2"]["t0"] + 0.12
    for i in range(9):
        place(sfx, A.sfx_pop(), r0 + (r1 - r0) * i / 8, 0.16)
    place(sfx, A.sfx_flashlight(), L["s2"]["t0"] - 0.05, 0.22)
    place(sfx, A.lp(A.sfx_flap(), 3000), 1.25, 0.05)          # opening flyby, very soft
    place(sfx, A.sfx_flashlight(), L["e3"]["t0"], 0.18)
    place(sfx, A.fade(A.lp(A.sfx_rewind(), 3500), 0.04, 0.1), L["n3"]["t0"] + 0.02, 0.15)
    place(sfx, A.sfx_ding(), L["n2"]["t0"] + 0.05, 0.12)
    for k in range(4):     # calendar page flips
        place(sfx, A.sfx_swish(), ex1 + 0.4 + k * 0.62, 0.08)

    mix = voice * 1.0 + amb + music * 0.22 + sfx           # linear: no clipper; peak control at the master stage
    fo = int(0.25 * SR)
    mix[-fo:] *= np.linspace(1, 0, fo)
    mix *= 10 ** (-3 / 20) / (np.max(np.abs(mix)) + 1e-9)    # -3 dBFS sample peak before loudness normalisation
    out = os.path.join(BUILD, "soundtrack.wav")
    sf.write(out, np.stack([mix, mix], 1).astype(np.float32), SR, subtype="FLOAT")

    def db(x, mask):
        return 20 * np.log10(np.sqrt(np.mean(x[mask] ** 2)) + 1e-12)
    harb = harbour > 0.99
    narr_m = (gate > 0.95) & harb & ~((t_ax > T0) & (t_ax < T1))
    test_m = (t_ax > T0 + 0.7) & (t_ax < T1 - 0.7)
    rep = {
        "water_change_under_narration_db": round(db(water_new, narr_m) - db(water_old, narr_m), 2),
        "water_change_in_test_db": round(db(water_new, test_m) - db(water_old, test_m), 2),
        "gull_calls_old": int(np.sum(np.diff((np.abs(gulls_old) > 1e-4).astype(int)) == 1)),
        "gull_level_change_db": round(db(gulls_new, np.abs(gulls_new) > 1e-6) - db(gulls_old, np.abs(gulls_old) > 1e-6), 2) if np.any(gulls_new) else None,
        "gulls_overlapping_narration": int(np.sum((np.abs(gulls_new) > 1e-4) & (gate > 0.05))),
        "voice_to_ambience_under_narration_db": round(db(voice, narr_m) - db(amb, narr_m), 2),
        "voice_to_ambience_before_db": round(db(voice, narr_m) - db(water_old + gulls_old, narr_m), 2),
    }
    json.dump(rep, open(os.path.join(BUILD, "mix_report.json"), "w"), indent=1)
    print(f"wrote {out}  {len(mix) / SR:.2f}s")
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
