"""Build the final narration track from the single Fenrir take.

The take is force-aligned word by word, cut into beats at word boundaries (breaths in the
gaps are dropped), and the beats are re-placed with deliberate gaps. Output: a 48 kHz
narration stem plus build/okene/voice.json with every word's final on-screen time."""
import json
import os

import numpy as np
from scipy.signal import resample_poly

from cinecode import tts
from cinecode.wordalign import align
from episodes.okene_60h.script import BEATS, DISPLAY

TAKE = "assets/audio/tts/okene/take3_302d7f36cf.wav"
BUILD = "build/okene"
SR = 48000

LEAD = 0.15
# silence BEFORE each beat (index-aligned with BEATS; first entry unused)
GAP = {"name": 0.75, "hours": 0.35, "capsize": 0.80, "pocket": 0.70, "reason": 0.45,
       "science": 0.55, "o2": 0.45, "co2": 0.25, "shrink": 0.30, "odds": 0.70,
       "wait": 1.00, "expect": 0.60, "found": 0.70, "final": 0.90}
# max internal pause inside a beat (ellipses), per beat
INTERNAL = {"hook": 0.62, "found": 0.50, "science": 0.38, "wait": 0.50}
END_HOLD = 3.0
PRE, POST = 0.035, 0.11


def build():
    take24 = tts.read_wav(TAKE)
    text = " ".join(b for _, b in BEATS)
    words = align(TAKE, text)
    toks = text.split()
    beat_of = []
    for k, (_, b) in enumerate(BEATS):
        beat_of += [k] * len(b.split())
    # split each beat into runs at internal pauses so they can be tightened
    out = []
    t = LEAD
    placed = []
    for k, (lid, _) in enumerate(BEATS):
        ws = [w for w in words if beat_of[w["idx"]] == k]
        if k:
            t += GAP[lid]
        runs = [[ws[0]]]
        for a, b in zip(ws, ws[1:]):
            if b["t0"] - a["t1"] > 0.15:
                runs.append([b])
            else:
                runs[-1].append(b)
        beat_t0 = t
        for ri, run in enumerate(runs):
            if ri:
                gap = run[0]["t0"] - runs[ri - 1][-1]["t1"]
                t += min(gap, INTERNAL.get(lid, 0.30))
            s0, s1 = run[0]["t0"] - PRE, run[-1]["t1"] + POST
            placed.append((t - PRE, s0, s1))
            for w in run:
                out.append({"w": w["w"], "idx": w["idx"], "beat": lid,
                            "t0": round(t + (w["t0"] - run[0]["t0"]), 3),
                            "t1": round(t + (w["t1"] - run[0]["t0"]), 3)})
            t += run[-1]["t1"] - run[0]["t0"]
        out_beat = (beat_t0, t)
        for w in out:
            if w["beat"] == lid:
                w["beat_t0"], w["beat_t1"] = round(out_beat[0], 3), round(out_beat[1], 3)
    total = t + END_HOLD
    n = int(round(total * 24000)) + 24000
    track = np.zeros(n, np.float32)
    for dst, s0, s1 in placed:
        a, b = int(round(s0 * 24000)), int(round(s1 * 24000))
        clip = take24[a:b].copy()
        f_in, f_out = int(0.012 * 24000), int(0.05 * 24000)
        clip[:f_in] *= np.linspace(0, 1, f_in)
        clip[-f_out:] *= np.linspace(1, 0, f_out)
        d = int(round(dst * 24000))
        track[d:d + len(clip)] += clip
    track = track[: int(round(total * 24000))]
    track48 = resample_poly(track, 2, 1).astype(np.float32)
    os.makedirs(BUILD, exist_ok=True)
    import soundfile as sf
    sf.write(f"{BUILD}/narration.wav", track48, SR)
    # display words (punctuation + caption spelling) attached to the first spoken token
    disp = []
    for i, tok in enumerate(toks):
        ws = [w for w in out if w["idx"] == i]
        core = tok.strip(".,:;!?")
        shown = tok.replace(core, DISPLAY.get(core, core)) if core else tok
        disp.append({"text": shown, "t0": ws[0]["t0"], "t1": ws[-1]["t1"], "beat": ws[0]["beat"]})
    beats = {}
    for w in out:
        beats.setdefault(w["beat"], [w["beat_t0"], w["beat_t1"]])
    json.dump({"duration": round(total, 3), "words": disp, "beats": beats}, open(f"{BUILD}/voice.json", "w"), indent=1)
    return total, beats


if __name__ == "__main__":
    total, beats = build()
    print("duration", total)
    for k, v in beats.items():
        print(f"{k:8s} {v[0]:6.2f} {v[1]:6.2f}")
