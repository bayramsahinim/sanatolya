"""Generate the narration take via Gemini TTS (channel narrator config). Cached in assets/audio/tts.

usage: python -m episodes.dry_peas_escape.make_voice
"""
import json
import os
import time

from cinecode import tts
from episodes.dry_peas_escape.script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "dry_peas")

NOTES = (CFG["director_notes"] +
         "\nThis is a quick YouTube Short told like a funny story: curious, lightly amused, with a little "
         "suspense near the end. Quoted lines are read by the narrator with a hint of the character's attitude "
         "(a cheeky guard, a roaring warden, a calm prisoner), never a cartoon voice.")


def take_text():
    return "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(en for _, _, en, _ in LINES)


def take_path():
    return os.path.join(OUT, f"narration_{tts.text_hash(take_text(), CFG['voice'], CFG['model'])}.wav")


def main():
    p = take_path()
    if os.path.exists(p):
        print("cached", p)
        return p
    t = time.time()
    for model in [CFG["model"]] + CFG.get("fallback_models", []):
        try:
            a = tts.synth(take_text(), p, model, voice=CFG["voice"])
            print(f"{model}: {len(a) / tts.SR:.1f}s audio in {time.time() - t:.0f}s -> {p}")
            return p
        except RuntimeError as e:
            print(f"  {model}: {str(e)[:160]}")
    raise RuntimeError("all TTS models exhausted")


if __name__ == "__main__":
    main()
