"""Record the full narration as one continuous Fenrir take (cached), validated by recognition."""
import json
import os
import sys

from cinecode import tts
from episodes.okene_60h.script import BEATS, DIRECTOR_NOTES

OUT = "assets/audio/tts/okene"
VOICE = "Fenrir"
MODELS = ["gemini-3.8-flash-tts", "gemini-3.1-flash-tts-preview", "gemini-2.5-pro-preview-tts"]


def transcript():
    return "\n".join(t for _, t in BEATS)


def take(n):
    text = DIRECTOR_NOTES + transcript()
    h = tts.text_hash(text, VOICE, str(n))
    path = f"{OUT}/take{n}_{h}.wav"
    last = None
    for m in MODELS:
        try:
            a = tts.synth(text, path, m, voice=VOICE, retries=3)
            return path, m, len(a) / tts.SR
        except Exception as e:
            last = e
    raise RuntimeError(last)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for n in map(int, sys.argv[1:] or ["1"]):
        print(take(n), flush=True)
