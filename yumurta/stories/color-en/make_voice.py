"""Narration for the colorblind-paradox story (same narrator as Troy / pink). usage (repo root): python3 yumurta/stories/<story>/make_voice.py [model]"""
import json, os, sys
sys.path.insert(0, '.')
from cinecode import tts
D = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a calm, curious philosophy Shorts channel (one paradox a day). "
         "Voice: young adult American male, warm and natural, clean and bright, medium pace, a sense of wonder, "
         "like telling a friend a mind-bending thought late at night. The first line is a confident list of obvious facts; "
         "'Everyone agrees, right?' light and knowing; 'But here's something no one can prove.' lower, intriguing; "
         "'What if the blue you see is not the blue I see?' slow, gently mind-blown; 'This is the colorblind paradox.' a clear title. "
         "'That's blue.' as a parent talking to a small child. 'Nobody else can ever see it.' quiet. "
         "'Here's the twist.' a beat of drama. 'Your sunset, your favorite song, the way rain feels.' soft and dreamy. "
         "The last three lines friendly and upbeat, a call to action. Never shouting, not a documentary voice. "
         "Leave short pauses between lines (about a third of a second).\n"
         "Speak only the transcript below, nothing else.")
lines = [l.strip() for l in open(os.path.join(D, 'voice', 'script.txt')) if l.strip()]
txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(lines)
model = sys.argv[1] if len(sys.argv) > 1 else CFG['model']
OUTD = 'assets/audio/tts_' + os.path.basename(D).replace('-en', '').replace('-', '_')
os.makedirs(OUTD, exist_ok=True)
p = f"{OUTD}/take_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
a = tts.synth(txt, p, model, voice=CFG['voice'])
print(p, len(a) / tts.SR)
