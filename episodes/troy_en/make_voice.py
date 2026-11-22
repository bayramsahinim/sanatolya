import json,sys,os
sys.path.insert(0, '.')  # run from repo root: python episodes/troy_en/make_voice.py <tts-model>
from cinecode import tts
from episodes.troy_en.script import LINES
CFG=json.load(open('config/narrator_voice.json'))
NOTES=("Narrator of a witty YouTube Shorts animation channel telling a wild true-ish history story to a friend. "
 "Voice: young adult American male, energetic but natural, clean and bright, fast pace like a well-edited Short, "
 "lightly sarcastic and clever, knowing smile on the twists, comic timing on 'hollow', 'Message received' and the last line. "
 "Quoted lines are read by the same narrator with a little character flavor (no different voices). "
 "Not deep, not booming, not a documentary voice, never shouting, no fake excitement. "
 "Leave only short pauses between paragraphs (about a third of a second).\n"
 "Pronounce Laocoön as 'lay-OCK-oh-on'. Speak only the transcript below, nothing else.")
txt="### DIRECTOR'S NOTES\n"+NOTES+"\n\n#### TRANSCRIPT\n"+"\n\n".join(t for _,t in LINES)
model=sys.argv[1]
p=f"assets/audio/tts_troy/take_{model}_{tts.text_hash(txt,CFG['voice'],model)}.wav"
a=tts.synth(txt,p,model,voice=CFG['voice'])
print(p, len(a)/tts.SR)
