"""Narration for the short-people story (same narrator as Troy / pink). usage (repo root): python3 yumurta/stories/<story>/make_voice.py [model]"""
import json, os, sys
sys.path.insert(0, '.')
from cinecode import tts
D = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a witty YouTube Shorts / Instagram Reels animation channel, a playful countdown of funny facts. "
         "Voice: young adult American male, energetic but natural, clean and bright, fast pace like a well-edited Short, "
         "lightly sarcastic and clever, a knowing smile in the voice. The first line is the hook: punchy, intriguing, a little proud. "
         "Each number ('One:', 'Two:', 'Three:') is a quick upbeat title. 'Cold feet... or cold shoulders.' as a tragic dilemma; "
         "'Short people? They vanish under it.' smug; 'They even plant a flag on top.' with mock pride; "
         "'Risk of getting cropped out: zero.' deadpan; 'When the teacher picks someone for the board...' a tense whisper; "
         "'A human shield... against math.' dramatic, like a movie trailer; the last line warm and cheeky, a call to action. "
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
