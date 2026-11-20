"""Generate narration via Gemini TTS, one take per line (cached in assets/audio/tts/stroop).

usage: python -m episodes.stroop_challenge.make_voice [line_id ...]
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from cinecode import tts
from episodes.stroop_challenge.script import DIRECTION, L3_DIRECTION, L3_READ, LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "stroop")


def prompt(text, extra):
    return ("### DIRECTOR'S NOTES\n" + CFG["director_notes"] + "\n" + extra +
            "\n\n#### TRANSCRIPT\n" + text)


def path_for(lid, text, extra):
    return os.path.join(OUT, f"{lid}_{tts.text_hash(prompt(text, extra), CFG['voice'])}.wav")


def jobs():
    # "go3" is not synthesised: TTS degenerates on one-word input, so timeline.take()
    # slices the "Go!" out of the go1 take instead (same voice, same delivery).
    out = [(lid, text, DIRECTION) for lid, _, text in LINES if lid != "go3"]
    out.append(("l3read", L3_READ, L3_DIRECTION))
    return out


def trim(a, thr=0.012, pad=0.04):
    """Strip leading/trailing silence."""
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return a
    p = int(pad * tts.SR)
    return a[max(0, idx[0] - p): idx[-1] + p]


def make(job):
    lid, text, extra = job
    p = path_for(lid, text, extra)
    if os.path.exists(p):
        return lid, "cached"
    for model in [CFG["model"]] + CFG.get("fallback_models", []):
        try:
            a = tts.synth(prompt(text, extra), p + ".raw.wav", model, voice=CFG["voice"])
            tts.write_wav(p, trim(a))
            os.remove(p + ".raw.wav")
            return lid, f"{len(a)/tts.SR:.1f}s via {model}"
        except RuntimeError as e:
            print(f"  {lid} {model}: {str(e)[:120]}", flush=True)
    raise RuntimeError(f"{lid}: all TTS models exhausted")


def load(lid):
    for j in jobs():
        if j[0] == lid:
            return tts.read_wav(path_for(*j))
    raise KeyError(lid)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    sel = [j for j in jobs() if not sys.argv[1:] or j[0] in sys.argv[1:]]
    with ThreadPoolExecutor(3) as ex:
        for lid, msg in ex.map(make, sel):
            print(lid, msg, flush=True)
