"""Replace the opening line of the yumurta Troy story with the new paradox hook.

Builds, from the original files (kept as *_orig):
  yumurta/stories/troy-en/voice/voice.wav, voice/words.json, audio/mix.wav
The new hook take is sped up a little, the old narration from "The Trojans rush..." follows it, and every later word
time is shifted by the same delta. The hook gets its own music bed (the old music from t=0) plus impact SFX.

usage (repo root): python3 -m episodes.troy_en.splice_hook
"""
import json
import os
import shutil
import subprocess

import numpy as np
import soundfile as sf

from cinecode import audio as A
from episodes.troy_en.mix import duck, music_track

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ST = os.path.join(ROOT, "yumurta", "stories", "troy-en")
TAKE = os.path.join(ROOT, "assets", "audio", "tts_troy", "hook_v0.wav")
TEMPO = 1.12
CUT = 5.84            # old timeline: between "home." (ends 5.66) and "The" (6.02)
GAP = 0.2
HOOK = ("Troy survived ten years of war, then tore down its own walls for a wooden horse. "
        "You see, the Greeks left it on the beach, and sailed home.").split()


def orig(p):
    o = p.replace(".", "_orig.", 1) if p.endswith(".json") else p[:-4] + "_orig.wav"
    if not os.path.exists(o):
        shutil.copy(p, o)
    return o


def load(p, sr):
    x, s = sf.read(p, always_2d=True)
    x = x.mean(1)
    if s != sr:
        x = A.resample(x, s, sr) if hasattr(A, "resample") else np.interp(np.arange(int(len(x) * sr / s)) / sr, np.arange(len(x)) / s, x)
    return x


def main():
    vpath, wpath, mpath = (os.path.join(ST, "voice", "voice.wav"), os.path.join(ST, "voice", "words.json"),
                           os.path.join(ST, "audio", "mix.wav"))
    vo, wo = orig(vpath), orig(wpath)
    mo = os.path.join(ST, "audio", "mix_noboom.wav")          # the old mix before the boom was added
    # --- the hook take, sped up
    tmp = TAKE[:-4] + "_fast.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", TAKE, "-af", f"atempo={TEMPO}", tmp], check=True)
    hw = json.load(open(TAKE + ".words.json"))
    assert len(hw) == len(HOOK), (len(hw), len(HOOK))
    # --- voice
    vsr = sf.info(vo).samplerate
    old_v = load(vo, vsr)
    hook_v = load(tmp, vsr)
    end_last = hw[-1][1] / TEMPO
    hook_v = hook_v[: int((end_last + 0.12) * vsr)]
    LH = len(hook_v) / vsr
    delta = LH + GAP - CUT
    new_v = np.concatenate([hook_v, np.zeros(int(GAP * vsr)), old_v[int(CUT * vsr):]])
    sf.write(vpath, new_v.astype(np.float32), vsr)
    # --- words
    W = json.load(open(wo))["words"]
    words = [{"word": HOOK[i], "start": round(s / TEMPO, 3), "end": round(e / TEMPO, 3)} for i, (s, e, _) in enumerate(hw)]
    words += [{"word": w["word"], "start": round(w["start"] + delta, 3), "end": round(w["end"] + delta, 3)} for w in W[17:]]
    json.dump({"words": words}, open(wpath, "w"))
    # --- mix: hook bed (voice + music from t=0 + sfx), then the old mix from CUT
    msr = sf.info(mo).samplerate
    old_m, _ = sf.read(mo, always_2d=True)
    hv = load(tmp, msr)[: int((LH + GAP) * msr)]
    n = int((LH + GAP) * msr)
    voice = np.zeros(n); voice[: len(hv)] = hv
    music = music_track(int(n * A.SR / msr) + 10)
    music = np.interp(np.arange(n) / msr, np.arange(len(music)) / A.SR, music)
    music = duck(music, voice)
    sfx = np.zeros(n)
    hs = lambda i: words[i]["start"]

    def put(x, t, g=1.0):
        x = np.asarray(x, dtype=np.float64)
        x = np.interp(np.arange(int(len(x) * msr / A.SR)) / msr, np.arange(len(x)) / A.SR, x)
        i0 = int(t * msr); m = min(len(x), n - i0)
        if m > 0:
            sfx[i0:i0 + m] += x[:m] * g
    put(A.get_sfx("thud"), 0.0, 1.0)                     # the wall stands: a ram bounces off
    put(A.get_sfx("bonk"), hs(2) - 0.05, 0.6)
    put(A.get_sfx("whoosh"), hs(6) - 0.15, 0.7)
    put(A.get_sfx("crash_wood"), hs(8) + 0.1, 0.8)        # "tore down"
    put(A.get_sfx("whoosh"), hs(12) - 0.15, 0.6)
    put(A.music_sting("dun"), hs(14) + 0.05, 0.7)         # "...wooden horse."
    put(A.get_sfx("whoosh"), hs(16) - 0.15, 0.6)
    put(A.get_sfx("splash"), hs(25), 0.35)
    mixw = voice * 1.0 + music * 0.22 + sfx * 0.55
    hook_m = np.stack([mixw, mixw], 1)
    tail = old_m[int(CUT * msr):]
    xf = int(0.08 * msr)
    out = np.concatenate([hook_m, tail])
    k = np.linspace(0, 1, xf)[:, None]                     # crossfade into the old mix just before the cut (silent voice there)
    c0 = int(CUT * msr)
    out[n - xf:n] = hook_m[-xf:] * (1 - k) + old_m[c0 - xf:c0] * k
    # --- the boom at the punchline (same synthesis as before)
    from scipy.signal import butter, lfilter
    tb = words[[w["word"] for w in words].index("afternoon.")]["start"] + 0.62
    nb = int(msr * 2.4); t = np.arange(nb) / msr; rng = np.random.default_rng(3); noise = rng.standard_normal(nb)
    b, a = butter(2, 180 / (msr / 2)); rum = lfilter(b, a, noise); rum /= np.abs(rum).max()
    b2, a2 = butter(2, [300 / (msr / 2), 3000 / (msr / 2)], "band"); crack = lfilter(b2, a2, noise); crack /= np.abs(crack).max()
    thump = np.sin(2 * np.pi * np.cumsum(np.linspace(70, 28, nb)) / msr)
    boom = .9 * rum * np.exp(-t * 1.6) * (1 - np.exp(-t * 80)) + .6 * thump * np.exp(-t * 3) + .35 * crack * np.exp(-t * 7) * (1 - np.exp(-t * 200))
    boom = boom / np.abs(boom).max() * .9
    i0 = int(tb * msr); e = min(len(out), i0 + nb)
    out[i0:e] = out[i0:e] * .6 + boom[: e - i0, None]
    out *= min(1.0, .98 / np.abs(out).max())
    sf.write(mpath, out.astype(np.float32), msr)
    print(f"hook {LH:.2f}s  delta {delta:+.2f}s  words {len(words)}  boom {tb:.2f}  total {len(out)/msr:.2f}s")


if __name__ == "__main__":
    main()
