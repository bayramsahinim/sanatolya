"""Generate the narration take(s) with the channel narrator voice (Gemini TTS, cached).

usage: python -m episodes.everything_divided.make_voice [n_takes]
Several takes can be generated; pick one with VOICE_TAKE in common.py.
"""
import json
import os
import sys

from cinecode import tts
from episodes.everything_divided.script import take_text

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts_everything")


def take_path(k):
    h = tts.text_hash(take_text(), CFG["voice"], CFG["model"], str(k))
    return os.path.join(OUT, f"take_{k}_{h}.wav")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    for k in range(n):
        p = take_path(k)
        for model in [CFG["model"]] + CFG.get("fallback_models", []):
            try:
                a = tts.synth(take_text(), p, model, voice=CFG["voice"])
                print(f"take {k}: {len(a) / tts.SR:.2f}s ({model}) -> {p}")
                break
            except RuntimeError as e:
                print(f"  {model}: {str(e)[:160]}")


if __name__ == "__main__":
    main()
