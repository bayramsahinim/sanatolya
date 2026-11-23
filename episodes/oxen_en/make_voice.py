"""Gemini TTS take for the Fire Oxen short (same narrator block as Troy).
usage (repo root): python3 -m episodes.oxen_en.make_voice [model]
"""
import json
import os
import sys

from cinecode import tts
from episodes.oxen_en.script import LINES

CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a witty YouTube Shorts animation channel telling a clever true history trick to a friend. "
         "Voice: young adult American male, energetic but natural, clean and bright, fast pace like a well-edited Short, "
         "lightly sarcastic and clever, knowing smile on the twists, comic timing on 'having a barbecue?' "
         "and the last line, where 'two thousand very confused cows' lands deadpan after a tiny beat. "
         "Quoted lines are read by the same narrator with a little character flavor (no different voices); "
         "'The fox is in the trap' is smug and slow, 'They're escaping over the mountain! After them!' is a panicked shout. "
         "Not deep, not booming, not a documentary voice, no fake excitement. "
         "Leave only short pauses between paragraphs (about a third of a second).\n"
         "Speak only the transcript below, nothing else.")
txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(t for _, t in LINES)
model = sys.argv[1] if len(sys.argv) > 1 else CFG['model']
os.makedirs('assets/audio/tts_oxen', exist_ok=True)
p = f"assets/audio/tts_oxen/take_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
a = tts.synth(txt, p, model, voice=CFG['voice'])
print(p, len(a) / tts.SR)
