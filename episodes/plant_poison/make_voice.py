"""Generate the English narration as one continuous take (consistent voice), cached."""
import json
import os
import sys

from cinecode import tts
from episodes.plant_poison.script import LINES

CFG = json.load(open("config/narrator_voice.json"))
NOTES_V1 = (
    "Narrator of a short educational history/science video for YouTube Shorts. Voice: young adult "
    "American male, natural US accent, clear and confident, medium-fast pace, conversational but "
    "polished, slightly curious and informative. Engaging without sounding fake. Slightly dramatic "
    "only on the final reveal lines. Not deep, not a slow documentary voice, not a cartoon voice, "
    "no overacting, no fake excitement.\n"
    "Leave a short natural pause (about half a second) between paragraphs, a slightly longer one "
    "after the word 'nicotine'. Speak only the transcript below, nothing else."
)

# v2 direction (revision): crisper, more forward and energetic, medium-fast, conversational
NOTES = (
    "You are the narrator of a fast, punchy educational YouTube Shorts channel about history and "
    "science. Voice: young adult American male, natural General American accent, bright, crisp "
    "and forward, smiling slightly, like he's sharing a genuinely surprising fact with a friend. "
    "Medium-fast pace with energy and momentum, conversational but polished, slightly curious. "
    "Crisp consonants; articulate 'nicotine', 'insecticides' and 'paralyzes' clearly. "
    "Not deep, not breathy, not somber, not slow, not a documentary voice, not theatrical, not a "
    "cartoon voice. Keep the same energy and character from the first line to the last; a small, "
    "knowing beat before the final words 'smoke break'.\n"
    "Leave only a short natural pause (about a third of a second) between paragraphs. "
    "Speak only the transcript below, nothing else."
)


def main(take="b"):
    text = (NOTES if take != "a" else NOTES_V1) + "\n\nTranscript:\n" + "\n\n".join(l[0] for l in LINES)
    h = tts.text_hash(text, CFG["voice"], take)
    path = f"assets/audio/tts/plant_poison_{take}_{h}.wav"
    for model in [CFG["model"]] + CFG["fallback_models"]:
        try:
            a = tts.synth(text, path, model, voice=CFG["voice"])
            print(path, len(a) / tts.SR, "s via", model)
            return path
        except RuntimeError as e:
            print(model, "failed:", e, file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main(*(sys.argv[1:]))
