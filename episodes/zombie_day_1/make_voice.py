"""Record the Day 1 narration as ONE take (consistent voice), cached in assets/audio/tts."""
import json
import os

from cinecode import tts
from episodes.zombie_day_1.script import DIRECTOR_NOTES, LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts")


def take_text():
    return "### DIRECTOR'S NOTES\n" + DIRECTOR_NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(LINES)


def take_path():
    return os.path.join(OUT, f"zombie_d1_{tts.text_hash(take_text(), CFG['voice'], CFG['model'])}.wav")


if __name__ == "__main__":
    p = take_path()
    for model in [CFG["model"]] + CFG.get("fallback_models", []):
        try:
            a = tts.synth(take_text(), p, model, voice=CFG["voice"])
            print(model, f"{len(a)/tts.SR:.1f}s", p)
            break
        except RuntimeError as e:
            print(model, str(e)[:200])
