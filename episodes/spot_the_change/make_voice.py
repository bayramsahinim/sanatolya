"""Record the narration (one Gemini TTS take per block, cached in assets/audio/tts/spot_the_change).

usage: python -m episodes.spot_the_change.make_voice [block ...] [--retake]
"""
import json
import os
import sys

from cinecode import tts
from episodes.spot_the_change.script import BLOCK_NOTES, BLOCKS, plain

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VOICE = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
CACHE = os.path.join(ROOT, "assets", "audio", "tts", "spot_the_change")

DIRECTION = (
    "Narrator of an interactive psychology YouTube Short. Voice: young adult American male, natural "
    "American accent, confident and conversational, clear bright tone, medium-fast but easy to follow, "
    "natural emphasis, minimal dramatic pauses. Not robotic, not a deep documentary voice, not childish, "
    "no fake excitement. Leave a short natural pause between sentences.\n"
)


def take_path(name, text, salt=""):
    return os.path.join(CACHE, f"{name}_{tts.text_hash(VOICE['voice'], text, salt)}.wav")


def prompt_for(name):
    lines = [plain(l) for _, l in dict(BLOCKS)[name]]
    text = " ".join(lines)
    return (DIRECTION + "Performance: " + BLOCK_NOTES[name] + "\nSpeak only the transcript below, nothing else.\n\n"
            "Transcript:\n" + text)


def record(name, salt=""):
    p = prompt_for(name)
    path = take_path(name, p, salt)
    models = [VOICE["model"]] + VOICE.get("fallback_models", [])
    last = None
    for m in models:
        try:
            a = tts.synth(p, path, m, voice=VOICE["voice"])
            print(f"{name}: {len(a) / tts.SR:.2f}s  ({m}) -> {os.path.relpath(path, ROOT)}")
            return path
        except RuntimeError as e:
            last = e
            print(f"{name}: {m} failed: {str(e)[:160]}")
    raise last


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    salt = "retake" if "--retake" in sys.argv else ""
    names = args or [n for n, _ in BLOCKS]
    takes = {}
    for n in names:
        takes[n] = os.path.relpath(record(n, salt), ROOT)
    idx = os.path.join(CACHE, "takes.json")
    old = json.load(open(idx)) if os.path.exists(idx) else {}
    old.update(takes)
    json.dump(old, open(idx, "w"), indent=1)
