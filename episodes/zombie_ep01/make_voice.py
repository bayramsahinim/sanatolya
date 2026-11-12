"""Generate the Episode 1 narration take with the channel narrator voice (config/narrator_voice.json).

usage: python -m episodes.zombie_ep01.make_voice [--force]
The take is cached in assets/audio/tts/zombie_ep01/ (keyed by text hash) so re-renders never re-call TTS.
"""
import json
import os
import sys
import time

from cinecode import tts
from episodes.zombie_ep01.script import PARAGRAPHS, TEXT

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "zombie_ep01")

EPISODE_NOTES = (
    "This episode: a zombie-survival dark comedy told in first person, like a funny young guy recounting "
    "something unbelievable that happened to him on his family farm. Serious and immediate during danger, "
    "dry and sarcastic on the jokes, curious on the survival fact, quieter and tense near the end. "
    "Keep the energy natural; never shout.\nParagraph delivery, in order:\n"
)


def take_text():
    notes = EPISODE_NOTES + "\n".join(f"{i + 1}. {d}" for i, (_, d) in enumerate(PARAGRAPHS))
    body = "\n\n".join(" ".join(TEXT[l] for l in ids) for ids, _ in PARAGRAPHS)
    return "### DIRECTOR'S NOTES\n" + CFG["director_notes"] + "\n" + notes + "\n\n#### TRANSCRIPT\n" + body


def take_path():
    return os.path.join(OUT, f"narration_{tts.text_hash(take_text(), CFG['voice'], CFG['model'])}.wav")


def main(force=False):
    p = take_path()
    if os.path.exists(p) and not force:
        print("cached", p)
        return p
    if force and os.path.exists(p):
        os.remove(p)
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
    main("--force" in sys.argv)
