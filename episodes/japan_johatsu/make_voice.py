"""Record the narration as one continuous take (natural flow), cached under assets/audio/tts."""
import json
import os
import sys

from cinecode import tts
from episodes.japan_johatsu.script import LINES, DIRECTOR

CFG = json.load(open("config/narrator_voice.json"))
OUT = "assets/audio/tts/johatsu"


def main(take=0):
    text = DIRECTOR + "\n\n" + "\n".join(LINES)
    h = tts.text_hash(text, CFG["voice"], str(take))
    path = f"{OUT}/narration_{h}.wav"
    for m in [CFG["model"]] + CFG["fallback_models"]:
        try:
            a = tts.synth(text, path, m, voice=CFG["voice"])
            print(path, m, len(a) / tts.SR)
            return path
        except Exception as e:
            print("fail", m, e)
    sys.exit(1)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
