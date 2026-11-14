"""Record the English narration with Gemini TTS (cached in assets/audio/tts/the_button_en).

usage: python -m episodes.the_button_en.make_voice [take_index ...]
"""
import json
import os
import sys
import time

from cinecode import tts
from episodes.the_button_en.script import LINES, TAKE_MOOD, TAKES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "the_button_en")

NOTES = (
    "Narrator of a short psychological-thriller story video. Voice: young adult American male, natural US "
    "accent, clear and confident, conversational, like someone telling a friend an unsettling true mystery. "
    "Medium-fast pace, crisp diction, short natural pauses and restrained dramatic emphasis. Emotionally "
    "controlled. Not robotic, not a booming documentary voice, not childish, no exaggerated acting, never shouting.\n"
    "Leave a clear pause of about half a second between sentences.\n"
    "Mood for this part: {mood}\n"
    "Speak only the transcript below, nothing else."
)


def take_text(i):
    return ("### DIRECTOR'S NOTES\n" + NOTES.format(mood=TAKE_MOOD[i]) + "\n\n#### TRANSCRIPT\n"
            + "\n".join(LINES[k][1] for k in TAKES[i]))


def take_path(i, model=None):
    return os.path.join(OUT, f"take_{i:02d}_{tts.text_hash(take_text(i), CFG['voice'])}.wav")


def make_take(i):
    p = take_path(i)
    if os.path.exists(p):
        print("cached", p)
        return
    for model in [CFG["model"]] + CFG.get("fallback_models", []):
        try:
            t = time.time()
            a = tts.synth(take_text(i), p, model, voice=CFG["voice"])
            print(f"take {i}: {len(a) / tts.SR:.1f}s via {model} in {time.time() - t:.0f}s")
            return
        except RuntimeError as e:
            print(f"take {i}: {model} failed: {str(e)[:200]}")
    raise SystemExit(f"take {i} failed on all models")


if __name__ == "__main__":
    idx = [int(a) for a in sys.argv[1:]] or range(len(TAKES))
    for i in idx:
        make_take(i)
