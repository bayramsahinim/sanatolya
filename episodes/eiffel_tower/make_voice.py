"""Generate several narration takes (cached). usage: python -m episodes.eiffel_tower.make_voice N"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from cinecode import tts
from episodes.eiffel_tower.script import tts_prompt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "audio", "tts_eiffel")
VOICE = "Puck"
MODELS = ["gemini-3.8-flash-tts", "gemini-2.5-pro-preview-tts"]


def take(i):
    model = MODELS[i % len(MODELS)]
    p = os.path.join(OUT, f"take_{i:02d}_{model}_{tts.text_hash(tts_prompt(), VOICE, model, str(i))}.wav")
    try:
        a = tts.synth(tts_prompt(), p, model, voice=VOICE)
        return f"{p}: {len(a)/tts.SR:.2f}s"
    except Exception as e:
        return f"take {i} {model}: {e}"


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    with ThreadPoolExecutor(n) as ex:
        for r in ex.map(take, range(n)):
            print(r)
