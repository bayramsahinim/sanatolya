"""Gemini TTS for the long-form Ships documentary: one take per section (long single takes drift), same narrator voice.
usage (repo root): python3 -m episodes.ships_long_en.make_voice [section ...]
"""
import json
import os
import sys

from cinecode import tts
from episodes.ships_long_en.script import LINES

CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a history YouTube channel telling a true story in a long-form animated documentary. "
         "Voice: young adult American male, warm, clean and bright, confident storyteller, calm measured documentary pace (noticeably slower than a Short), clear and engaging. "
         "Serious and informative, with quiet wonder at the remarkable moments, never jokey or sarcastic. "
         "Dates and numbers are read clearly. Natural pauses between sentences, a slightly longer beat after each date. "
         "Not deep, not booming, not a trailer voice, no fake excitement.\n"
         "Speak only the transcript below, nothing else.")
model = os.environ.get('TTS_MODEL', CFG['model'])
want = set(sys.argv[1:])
os.makedirs('assets/audio/tts_shipslong', exist_ok=True)
for sid, text in LINES:
    if want and sid not in want: continue
    txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + text
    p = f"assets/audio/tts_shipslong/{sid}_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
    a = tts.synth(txt, p, model, voice=CFG['voice'])
    print(sid, p, round(len(a) / tts.SR, 2), flush=True)
