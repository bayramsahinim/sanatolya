"""Generate narration (and dialogue) audio via Gemini TTS. Cached in assets/audio/tts.

usage: python -m episodes.rome_7_days.make_voice [chunk_index ...] [--dialogue]
"""
import json
import os
import sys
import time

from cinecode import tts
from episodes.rome_7_days.script import DIALOGUE, NARRATION, TTS_CHUNKS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
OUT = os.path.join(ROOT, "assets", "audio", "tts")

DIALOGUE_MODEL = "gemini-3.8-flash-lite-tts"
DIALOGUE_VOICES = {"Maximus": "Algenib", "Lucia": "Kore", "Boy": "Leda"}


def chunk_text(scenes):
    lines = [t for s in scenes for _, t in NARRATION[s]]
    return CFG["style_prompt"] + "\n\n" + "\n\n".join(lines)


def chunk_path(i):
    return os.path.join(OUT, f"narration_{i:02d}_{tts.text_hash(chunk_text(TTS_CHUNKS[i]), CFG['voice'], CFG['model'])}.wav")


def make_chunk(i):
    p = chunk_path(i)
    if os.path.exists(p):
        print("cached", p)
        return
    t = time.time()
    a = tts.synth(chunk_text(TTS_CHUNKS[i]), p, CFG["model"], voice=CFG["voice"])
    print(f"chunk {i}: {len(a)/tts.SR:.1f}s audio in {time.time()-t:.0f}s -> {p}")


def dialogue_take_text():
    body = "\n".join(f"{who}: {text}" for _, who, text in DIALOGUE)
    return ("TTS the following lines from a cartoon. Maximus is a huge, loud, gruff Roman soldier, "
            "booming and dramatic. Boy is an excited, playful young boy. Leave a one second pause "
            "between lines.\n\n" + body)


def dialogue_path():
    return os.path.join(OUT, f"dialogue_{tts.text_hash(dialogue_take_text())}.wav")


def make_dialogue():
    p = dialogue_path()
    if os.path.exists(p):
        print("cached", p)
        return
    a = tts.synth(dialogue_take_text(), p, DIALOGUE_MODEL,
                  speakers={"Maximus": DIALOGUE_VOICES["Maximus"], "Boy": DIALOGUE_VOICES["Boy"]})
    print(f"dialogue take: {len(a)/tts.SR:.1f}s")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--dialogue" in args:
        make_dialogue()
        args.remove("--dialogue")
        if not args:
            sys.exit(0)
    idx = [int(a) for a in args] if args else range(len(TTS_CHUNKS))
    for n, i in enumerate(idx):
        if n:
            time.sleep(25)
        make_chunk(i)
