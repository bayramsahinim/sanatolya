"""Narration for Day 2 (rebuilt): ONE Gemini TTS request for the whole script, channel narrator voice.
The free tier allows ~10 requests per model per day, so never one request per line.

usage: python -m episodes.zombie_day_2_rebuilt.make_voice [--model MODEL] [--retake]
"""
import json
import os
import sys

from cinecode import tts
from episodes.zombie_day_2_rebuilt.script import NARRATION, PERFORMANCE

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "zombie_day_2_rebuilt")


def notes():
    n = CFG["director_notes"].replace("Narrator of a witty YouTube animation channel.", "Narrator of a YouTube animation series.")
    # the channel note is tuned for comedy; this episode is a restrained thriller
    n = n.replace("energetic but natural, clean and bright, medium-fast pace, lightly sarcastic and clever",
                  "natural and clear, medium-fast pace, intelligent and slightly tense")
    n = n.replace("Natural pauses and comic timing.", "Natural pauses and subtle dramatic timing.")
    return n.replace("Speak only", PERFORMANCE + "\nSpeak only")


def take_text():
    return "### DIRECTOR'S NOTES\n" + notes() + "\n\n#### TRANSCRIPT\n" + "\n\n".join(t for _, t in NARRATION)


def take_path(model):
    return os.path.join(OUT, f"take_{tts.text_hash(take_text(), CFG['voice'], model)}.wav")


def existing_take():
    for model in [CFG["model"]] + CFG.get("fallback_models", []):
        if os.path.exists(take_path(model)):
            return take_path(model)
    return None


if __name__ == "__main__":
    args = sys.argv[1:]
    models = [CFG["model"]] + CFG.get("fallback_models", [])
    if "--model" in args:
        models = [args[args.index("--model") + 1]]
    if "--retake" in args and existing_take():
        os.rename(existing_take(), existing_take() + ".rejected")
    if existing_take():
        print("cached", existing_take())
        sys.exit(0)
    for m in models:
        try:
            a = tts.synth(take_text(), take_path(m), m, voice=CFG["voice"])
            print(f"{len(a) / tts.SR:.1f}s", m, take_path(m))
            break
        except RuntimeError as e:
            print(m, str(e)[:200])
    else:
        sys.exit("all TTS models refused")
