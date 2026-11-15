"""Narration for 'Check Your Lungs': one take with the channel narrator voice,
then split into lines on the pauses (see split_voice in short.py).

usage: python -m episodes.check_your_lungs.make_voice
"""
import json
import os
import time

from cinecode import tts

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts", "check_your_lungs")

LINES = [
    ("open", "Can you follow this breathing challenge?"),
    ("inhale", "Breathe in..."),
    ("hold", "Ready? Hold."),
    ("end", "Breathe out. How far did you get?"),
]


def take_text():
    return ("### DIRECTOR'S NOTES\n" + CFG["director_notes"] +
            "\nThis is a short breathing-challenge video: keep it calm, friendly and curious; "
            "'Breathe in' is slow and relaxed."
            "\n\n#### TRANSCRIPT\n" + "\n\n".join(t for _, t in LINES))


def take_path():
    return os.path.join(OUT, f"take_{tts.text_hash(take_text(), CFG['voice'])}.wav")


def main():
    p = take_path()
    if os.path.exists(p):
        print("cached", p)
        return
    for i, model in enumerate([CFG["model"]] + CFG.get("fallback_models", [])):
        try:
            a = tts.synth(take_text(), p, model, voice=CFG["voice"])
            print(f"{model}: {len(a) / tts.SR:.1f}s -> {p}")
            return
        except RuntimeError as e:
            print(f"  {model}: {str(e)[:120]}")
            time.sleep(5)
    raise RuntimeError("all TTS models exhausted")


if __name__ == "__main__":
    main()
