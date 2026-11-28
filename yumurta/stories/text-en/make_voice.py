"""Narration for the how-to-text-back story (same narrator as Troy / pink). usage (repo root): python3 yumurta/stories/<story>/make_voice.py [model]"""
import json, os, sys
sys.path.insert(0, '.')
from cinecode import tts
D = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a dry, deadpan comedy Shorts channel. Voice: young adult American male, warm, clean and bright. "
         "Read it like a calm, slightly patronising instructional video for a very simple task, completely straight-faced. "
         "'How to text back.' a clear title. Each 'Step one:', 'Step two:' ... said like a tutorial heading, then a short pause, "
         "then the instruction, flat and matter-of-fact. 'Step five: Do this within the same week.' a touch slower and more pointed, "
         "the joke. 'Congratulations, you have texted back.' proud and over-the-top sincere, like awarding a medal. "
         "Never shouting. Leave short pauses between lines (about a third of a second).\n"
         "Speak only the transcript below, nothing else.")
lines = [l.strip() for l in open(os.path.join(D, 'voice', 'script.txt')) if l.strip()]
txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(lines)
model = sys.argv[1] if len(sys.argv) > 1 else CFG['model']
OUTD = 'assets/audio/tts_' + os.path.basename(D).replace('-en', '').replace('-', '_')
os.makedirs(OUTD, exist_ok=True)
p = f"{OUTD}/take_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
a = tts.synth(txt, p, model, voice=CFG['voice'])
print(p, len(a) / tts.SR)
