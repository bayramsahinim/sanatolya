"""Gemini TTS for the tight Ships documentary (Puck, energetic storyteller). One take per section.
usage (repo root): [TTS_MODEL=...] python3 -m episodes.ships_doc_en.make_voice [section ...]
"""
import json
import os
import sys

from cinecode import tts
from episodes.ships_doc_en.script import LINES

CFG = json.load(open('config/narrator_voice.json'))
VOICE = 'Puck'
NOTES = ("Narrator of a popular history YouTube channel telling a gripping true story. "
         "Voice: young adult American male, energetic, bright and engaging, a storyteller who is genuinely excited by this story. "
         "Brisk medium-fast pace with momentum, punchy delivery on short sentences, rising curiosity on questions, "
         "lean in with intrigue on the surprising moments. Short natural pauses, no long gaps. "
         "Serious about the history, but alive and never flat or sleepy. Not booming, not a movie-trailer voice, no shouting.\n"
         "Speak only the transcript below, nothing else.")
model = os.environ.get('TTS_MODEL', CFG['model'])
want = set(sys.argv[1:])
os.makedirs('assets/audio/tts_shipsdoc', exist_ok=True)
for sid, text in LINES:
    if want and sid not in want: continue
    txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + text
    p = f"assets/audio/tts_shipsdoc/{sid}_{model}_{tts.text_hash(txt, VOICE, model)}.wav"
    try:
        a = tts.synth(txt, p, model, voice=VOICE)
    except Exception as e:
        print(sid, 'ERR', str(e)[:120], flush=True); continue
    print(sid, p, round(len(a) / tts.SR, 2), flush=True)
