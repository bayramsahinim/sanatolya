"""Generate narration + dialogue takes with Gemini TTS (cached in assets/audio/tts/mom_cooking).

usage: python -m episodes.mom_cooking.make_voice
"""
import json
import os
import time

from cinecode import tts
from episodes.mom_cooking.script import DIALOGUE, NARRATION, PARAGRAPHS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "mom_cooking")
MOM_VOICE = "Sulafat"      # warm, calm adult female
TEXT = dict(NARRATION)


def narration_text():
    paras = [" ".join(TEXT[l] for l in p) for p in PARAGRAPHS]
    return "### DIRECTOR'S NOTES\n" + CFG["director_notes"] + "\n\n#### TRANSCRIPT\n" + "\n\n".join(paras)


ME_NOTES = (CFG["director_notes"].split("\nLeave")[0] +
            "\nThis is the narrator speaking as himself at the dinner table. Two separate lines with a pause of "
            "about one second between them.\nLine 1: genuinely overjoyed, big and bright, but not screaming.\n"
            "Line 2: completely dry, calm, deadpan and confident, quiet, almost smug. Not shouted.\n"
            "Speak only the transcript below, nothing else.")
MOM_NOTES = ("A natural, calm adult American mother at the dinner table. Warm, relaxed, lightly amused, "
             "conversational, not theatrical. Leave a pause of about one second between the two lines.\n"
             "Speak only the transcript below, nothing else.")


def me_text():
    return "### DIRECTOR'S NOTES\n" + ME_NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(
        t for _, w, t in DIALOGUE if w == "Me")


def mom_text():
    return "### DIRECTOR'S NOTES\n" + MOM_NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(
        t for _, w, t in DIALOGUE if w == "Mom")


TAKES = {
    "narration": (narration_text, CFG["voice"]),
    "me": (me_text, CFG["voice"]),
    "mom": (mom_text, MOM_VOICE),
}


def take_path(name):
    fn, voice = TAKES[name]
    return os.path.join(OUT, f"{name}_{tts.text_hash(fn(), voice, CFG['model'])}.wav")


def make(name):
    p = take_path(name)
    if os.path.exists(p):
        print("cached", p)
        return
    fn, voice = TAKES[name]
    for model in [CFG["model"]] + CFG.get("fallback_models", []):
        try:
            a = tts.synth(fn(), p, model, voice=voice)
            print(f"{name}: {len(a) / tts.SR:.1f}s ({model}) -> {p}")
            return
        except RuntimeError as e:
            print(f"  {model}: {str(e)[:160]}")
    raise RuntimeError("all TTS models failed")


if __name__ == "__main__":
    for i, n in enumerate(TAKES):
        if i:
            time.sleep(3)
        make(n)
