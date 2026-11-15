"""Generate the narration as ONE continuous take (one voice, one model, one request) via Gemini TTS,
then split it into script lines with cinecode.align. Cached in assets/audio/tts/four_swallows.

usage: python -m episodes.four_swallows.make_voice
"""
import json, os
import numpy as np
from cinecode import tts, align
from episodes.four_swallows.script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "four_swallows")
MODELS = [CFG["model"], "gemini-2.5-pro-preview-tts", "gemini-2.5-flash-preview-tts"] + CFG["fallback_models"]

NOTES = ("Narrator of a curious, playful YouTube Shorts science channel. Voice: young adult American male, "
         "friendly and confident, clean and bright, medium-fast pace, slightly playful and curious. "
         "Not deep, not a documentary voice, never shouting, no cartoon voice.\n"
         "The single numbers One, Two, Three, Four are a calm, friendly countdown the viewer swallows along to.\n"
         "Leave a clear pause of about one second between paragraphs.\n"
         "Speak only the transcript below, nothing else.")


def take_text():
    return ("### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(l[1] for l in LINES))


def take_path():
    return os.path.join(OUT, f"take_{tts.text_hash(take_text(), CFG['voice'])}.wav")


def make_take():
    p = take_path()
    for model in MODELS:
        try:
            a = tts.synth(take_text(), p, model, voice=CFG["voice"])
            print(f"take: {len(a)/tts.SR:.1f}s ({model})")
            return a
        except RuntimeError as e:
            print(f"  {model}: {str(e)[:100]}")
    raise RuntimeError("all TTS models exhausted")


def split():
    a = make_take()
    a = a[: len(a) - int(0.25 * tts.SR)]          # drop the end-of-stream click some models append
    segs = align.align(a, [l[1] for l in LINES])
    out = {}
    for (lid, text, *_), (s, e) in zip(LINES, segs):
        clip = align.trim(a, s, e)
        fp = os.path.join(OUT, f"line_{lid}.wav")
        tts.write_wav(fp, clip)
        out[lid] = {"file": os.path.relpath(fp, ROOT), "dur": round(len(clip) / tts.SR, 3), "src": [s, e]}
        print(f"{lid:8s} {s:6.2f}-{e:6.2f}  {len(clip)/tts.SR:.2f}s  {text}")
    json.dump(out, open(os.path.join(OUT, "lines.json"), "w"), indent=1)


if __name__ == "__main__":
    split()
