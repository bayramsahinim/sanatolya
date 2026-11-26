"""Narration for the kiss story (same narrator as Troy / pink). usage (repo root): python3 yumurta/stories/<story>/make_voice.py [model]"""
import json, os, sys
sys.path.insert(0, '.')
from cinecode import tts
D = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a witty YouTube Shorts / Instagram Reels animation channel about mind-blowing science. "
         "Voice: young adult American male, natural, clean and bright, a knowing smile in the voice. The first line is the hook: confident, intriguing. "
         "'Watch.' quiet. 'Two centimeters... eight millimeters... contact.' slow, like counting down, a held breath; 'Or is it?' playful. "
         "Each 'Closer.' is short and hushed, getting quieter and more amazed as we go deeper; each step a calm, wondering beat. "
         "'And here, the gap stops shrinking.' slow and still. 'The electrons push back...' clear and simple, the reveal. "
         "'Even in a kiss, there's always a tiny space between you.' warm and soft; the last line light and cheeky. "
         "Not deep, not booming, never shouting. Leave short pauses between lines (about half a second).\n"
         "Speak only the transcript below, nothing else.")
lines = [l.strip() for l in open(os.path.join(D, 'voice', 'script.txt')) if l.strip()]
txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(lines)
model = sys.argv[1] if len(sys.argv) > 1 else CFG['model']
OUTD = 'assets/audio/tts_' + os.path.basename(D).replace('-en', '').replace('-', '_')
os.makedirs(OUTD, exist_ok=True)
p = f"{OUTD}/take_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
a = tts.synth(txt, p, model, voice=CFG['voice'])
print(p, len(a) / tts.SR)
