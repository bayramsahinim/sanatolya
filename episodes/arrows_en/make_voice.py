"""Gemini TTS take for the Straw Boats short (same narrator block as Troy).
usage (repo root): python3 -m episodes.arrows_en.make_voice [model]
"""
import json
import os
import sys

from cinecode import tts
from episodes.arrows_en.script import LINES

CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a witty YouTube Shorts animation channel telling a clever true-ish history trick to a friend. "
         "Voice: young adult American male, energetic but natural, clean and bright, fast pace like a well-edited Short, "
         "lightly sarcastic and clever, knowing smile on the twists, comic timing on 'I only need three', 'scaring crows?' "
         "and the last line, which is a cheeky shout back across the water. "
         "Quoted lines are read by the same narrator with a little character flavor (no different voices); "
         "'Fail, and you lose your head' is cold and smug, 'Archers! Shoot at the drums!' is a barked order. "
         "Not deep, not booming, not a documentary voice, no fake excitement. "
         "Leave only short pauses between paragraphs (about a third of a second).\n"
         "Speak only the transcript below, nothing else.")
txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(t for _, t in LINES)
model = sys.argv[1] if len(sys.argv) > 1 else CFG['model']
os.makedirs('assets/audio/tts_arrows', exist_ok=True)
p = f"assets/audio/tts_arrows/take_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
a = tts.synth(txt, p, model, voice=CFG['voice'])
print(p, len(a) / tts.SR)
