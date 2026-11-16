"""Record the whole narration as ONE take (one consistent voice), then split it into
per-line clips at the paragraph pauses. Both the take and the clips are cached."""
import json
import os

import numpy as np

from cinecode import align, tts
from .script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "assets", "audio", "tts", "kohnstamm")
VOICE = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json")))
MODEL = "gemini-2.5-flash-preview-tts"   # the 3.x TTS models were out of daily quota
NOTES = ("Read this as the narrator of a curious, friendly science YouTube Short. "
         "Young adult American male, natural and conversational, medium-fast pace, clear articulation, "
         "curious and slightly playful. Not deep, not a movie-trailer voice, no shouting, not a kids-show voice. "
         "Leave a clear pause of about one second between paragraphs:")


def take_text():
    return NOTES + "\n\n" + "\n\n".join(t for _, t in LINES)


def take_path():
    return os.path.join(CACHE, f"take_{tts.text_hash(MODEL, VOICE['voice'], take_text())}.wav")


def clip_path(i):
    return os.path.join(CACHE, f"line_{i:02d}.wav")


def main():
    audio = tts.synth(take_text(), take_path(), MODEL, voice=VOICE["voice"])
    print(f"take: {len(audio) / tts.SR:.2f}s")
    segs = align.align(audio, [t for _, t in LINES])
    meta = []
    for i, ((s, e), (_, text)) in enumerate(zip(segs, LINES)):
        clip = align.trim(audio, s, e)
        tts.write_wav(clip_path(i), clip)
        meta.append({"i": i, "src": [round(s, 3), round(e, 3)], "dur": round(len(clip) / tts.SR, 3), "text": text})
        print(f"{i:02d} {s:6.2f}-{e:6.2f} ({e - s:4.2f}s)  {text}")
    json.dump(meta, open(os.path.join(CACHE, "lines.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
