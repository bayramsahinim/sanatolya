"""Narration for the chameleon-paradox story (same narrator as Troy / pink). usage (repo root): python3 yumurta/stories/<story>/make_voice.py [model]"""
import json, os, sys
sys.path.insert(0, '.')
from cinecode import tts
D = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a calm, curious psychology/philosophy Shorts channel (one paradox a day). "
         "Voice: young adult American male, warm and natural, clean and bright, medium pace, a sense of wonder, "
         "like telling a friend a thought late at night. The first line is a playful, rhythmic list (loud / quiet / serious / funny, "
         "each word coloured a little by its meaning); 'So, which one is the real you?' slower, curious; "
         "'This is the chameleon paradox.' a clear title. 'Psychologists call this self-monitoring' informative; "
         "'But here's the paradox.' lower, intriguing. 'The better you get at fitting in everywhere...' thoughtful, a little sad. "
         "'And one night, alone in your room, you wonder, who am I when no one's watching?' quiet and intimate. "
         "'Here's the twist.' a beat of drama. 'It's the one choosing the colors.' warm, uplifting. "
         "The last line friendly and upbeat, a question to the viewer. Never shouting, not a documentary voice. "
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
