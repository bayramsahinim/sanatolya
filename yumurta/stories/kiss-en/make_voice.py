"""Narration for the kiss story (same narrator as Troy / pink). usage (repo root): python3 yumurta/stories/<story>/make_voice.py [model]"""
import json, os, sys
sys.path.insert(0, '.')
from cinecode import tts
D = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a witty YouTube Shorts / Instagram Reels animation channel about mind-blowing science. "
         "Voice: young adult American male, energetic but natural, clean and bright, fast pace like a well-edited Short, "
         "lightly sarcastic and clever, a knowing smile in the voice. The first line is the hook: confident, a little provocative. "
         "'Don't believe me?' playful challenge. The zoom lines build in wonder, each one a step deeper; 'And at the very bottom... atoms.' hushed and amazed. "
         "'Boing.' as a short comic sound word. 'So the atoms never really meet.' a calm, satisfied beat. "
         "'You're hovering on that push.' amused. 'What you feel as touch... is electrons shoving electrons.' the big reveal, slow and clear. "
         "'So technically, that kiss never happened.' dry and funny; the last line cheeky, a call to action. "
         "Not deep, not booming, never shouting. Leave only short pauses between lines (about a quarter of a second).\n"
         "Speak only the transcript below, nothing else.")
lines = [l.strip() for l in open(os.path.join(D, 'voice', 'script.txt')) if l.strip()]
txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(lines)
model = sys.argv[1] if len(sys.argv) > 1 else CFG['model']
OUTD = 'assets/audio/tts_' + os.path.basename(D).replace('-en', '').replace('-', '_')
os.makedirs(OUTD, exist_ok=True)
p = f"{OUTD}/take_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
a = tts.synth(txt, p, model, voice=CFG['voice'])
print(p, len(a) / tts.SR)
