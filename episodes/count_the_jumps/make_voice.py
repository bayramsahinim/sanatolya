"""Synthesize each narration line with the channel narrator voice (cached in assets/audio/tts/jumps).

usage: python -m episodes.count_the_jumps.make_voice
"""
import json
import os
import time

from cinecode import tts
from episodes.count_the_jumps.script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "jumps")
MODELS = ["gemini-3.1-flash-tts-preview", CFG["model"]]  # one model for every line -> one consistent voice
NOTES = CFG["director_notes"].replace("Leave a clear pause of about one second between paragraphs.\n", "") + \
    "\nThis is a short attention-test video: confident, conversational, slightly playful, intelligent."


STYLE = ("Read this line aloud exactly as written, adding nothing before or after it. "
         "Voice: young adult American male, natural accent, confident and conversational, slightly "
         "playful and curious, medium-fast pace, clean pronunciation. Not deep, not booming, not a "
         "kids-show voice, no fake excitement")


def prompt(text):
    return STYLE + ": " + text


def path(lid, text):
    return os.path.join(OUT, f"{lid}_{tts.text_hash(prompt(text), CFG['voice'])}.wav")


def main(only=()):
    for lid, text in LINES:
        p = path(lid, text)
        if os.path.exists(p) or (only and lid not in only):
            continue
        for model in MODELS:
            try:
                a = tts.synth(prompt(text), p, model, voice=CFG["voice"])
                print(f"{lid}: {len(a)/tts.SR:.2f}s ({model})", flush=True)
                break
            except RuntimeError as e:
                print(f"  {lid} {model}: {str(e)[:150]}", flush=True)
        time.sleep(3)


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])


# ---------------------------------------------------------------- single-take mode
# The whole script in ONE request (one model, one performance => one consistent voice),
# later split into lines at the pauses (episodes.count_the_jumps.split_take).
TAKE_MODELS = ["gemini-2.5-pro-preview-tts", "gemini-2.5-flash-preview-tts"]
TAKE_STYLE = ("Read the following script aloud exactly as written, adding nothing. Voice: young adult "
              "American male, natural accent, confident and conversational, slightly playful and curious, "
              "medium-fast pace, clean pronunciation. Not deep, not booming, not a kids-show voice, no fake "
              "excitement. Leave a clear pause of about one second between lines.\n\n")


def take_text():
    return TAKE_STYLE + "\n\n".join(t for _, t in LINES)


def take_path(model):
    return os.path.join(OUT, f"take_{model}_{tts.text_hash(take_text(), CFG['voice'])}.wav")


def make_take():
    for model in TAKE_MODELS:
        p = take_path(model)
        if os.path.exists(p):
            return p
        try:
            a = tts.synth(take_text(), p, model, voice=CFG["voice"], retries=2)
            print(f"take: {len(a)/tts.SR:.1f}s ({model})")
            return p
        except RuntimeError as e:
            print(f"  {model}: {str(e)[:200]}")
    raise RuntimeError("no take")
