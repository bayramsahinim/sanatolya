"""Gemini TTS take for the Empty Fort short (same narrator block as Troy).
usage (repo root): python3 -m episodes.fort_en.make_voice [model]
"""
import json
import os
import sys

from cinecode import tts
from episodes.fort_en.script import LINES

CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a witty YouTube Shorts animation channel telling a clever true history trick to a friend. "
         "Voice: young adult American male, energetic but natural, clean and bright, fast pace like a well-edited Short, "
         "lightly sarcastic and clever, knowing smile on the twists. The first sentence is punchy, with a tiny beat before 'And played a song.' "
         "'Run? Too slow. Fight? Impossible.' quick and clipped. The orders are read crisp, one after another. "
         "'Never.' flat and heavy, then 'So this has to be a trap.' as the general's conclusion. "
         "The last line slows a touch: 'Just cooks.' dry, a tiny beat, then 'And one very good actor.' with a smile. "
         "Not deep, not booming, not a documentary voice, no fake excitement. "
         "Leave only short pauses between paragraphs (about a third of a second).\n"
         "Speak only the transcript below, nothing else.")
txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(t for _, t in LINES)
model = sys.argv[1] if len(sys.argv) > 1 else CFG['model']
os.makedirs('assets/audio/tts_fort', exist_ok=True)
p = f"assets/audio/tts_fort/take_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
a = tts.synth(txt, p, model, voice=CFG['voice'])
print(p, len(a) / tts.SR)
