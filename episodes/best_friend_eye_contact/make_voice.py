"""Record the English narration as one take with the channel narrator voice (cached).

usage: python -m episodes.best_friend_eye_contact.make_voice
"""
import json
import os

from cinecode import tts
from episodes.best_friend_eye_contact.script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "best_friend_eye_contact")

SHORTS_NOTE = ("This is a 36-second vertical Short, so the read is brisk: a quick, snappy Shorts pace "
               "(around three and a half words per second), conversational, with a light, knowing smile "
               "in the voice. Keep the pause between paragraphs at about one second, but no lingering "
               "inside a line.")


def take_text():
    return ("### DIRECTOR'S NOTES\n" + CFG["director_notes"] + "\n" + SHORTS_NOTE +
            "\n\n#### TRANSCRIPT\n" + "\n\n".join(l[4] for l in LINES))


def take_path():
    return os.path.join(OUT, f"take_{tts.text_hash(take_text(), CFG['voice'], CFG['model'])}.wav")


def make():
    p = take_path()
    if os.path.exists(p):
        return tts.read_wav(p)
    for model in [CFG["model"]] + CFG.get("fallback_models", []):
        try:
            a = tts.synth(take_text(), p, model, voice=CFG["voice"])
            print(f"{model}: {len(a)/tts.SR:.1f}s -> {p}")
            return a
        except RuntimeError as e:
            print(f"  {model}: {str(e)[:160]}")
    raise RuntimeError("all TTS models exhausted")


if __name__ == "__main__":
    make()
