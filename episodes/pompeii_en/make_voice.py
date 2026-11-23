"""Gemini TTS take for the Pompeii short (same narrator block as Troy).
usage (repo root): python3 -m episodes.pompeii_en.make_voice [model]
"""
import json
import os
import sys

from cinecode import tts
from episodes.pompeii_en.script import LINES

CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a witty YouTube Shorts animation channel telling a wild true history story to a friend. "
         "Voice: young adult American male, energetic but natural, clean and bright, fast pace like a well-edited Short, "
         "lightly sarcastic and clever, knowing smile on the twists, comic timing on 'Same spot', 'It always shakes', "
         "'never realized' and the last line. A quieter, serious beat on 'He never came back.' "
         "Quoted lines are read by the same narrator with a little character flavor (no different voices). "
         "Not deep, not booming, not a documentary voice, never shouting, no fake excitement. "
         "Leave only short pauses between paragraphs (about a third of a second).\n"
         "Read 62 as 'sixty-two', 79 as 'seventy-nine', 1599 as 'fifteen ninety-nine'. Pompeii is 'pom-PAY'. "
         "Speak only the transcript below, nothing else.")
txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(t for _, t in LINES)
model = sys.argv[1] if len(sys.argv) > 1 else CFG['model']
os.makedirs('assets/audio/tts_pompeii', exist_ok=True)
p = f"assets/audio/tts_pompeii/take_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
a = tts.synth(txt, p, model, voice=CFG['voice'])
print(p, len(a) / tts.SR)
