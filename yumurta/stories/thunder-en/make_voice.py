"""Narration for the Thunder Stone story (same narrator as Troy). usage (repo root): python3 yumurta/stories/<story>/make_voice.py [model]
In a copied story, rewrite NOTES (the comic-timing beats name lines of that story's script)."""
import json, os, sys
sys.path.insert(0, '.')
from cinecode import tts
D = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a witty YouTube Shorts animation channel telling a wild true story to a friend. "
         "Voice: young adult American male, energetic but natural, clean and bright, fast pace like a well-edited Short, "
         "lightly sarcastic and clever, knowing smile on the twists. Real comic timing: a tiny beat before 'and then he sat down and waited for snow.', before 'he drops bronze balls.', a held breath before 'starts to roll.', and a knowing pause before 'Because a frozen swamp is a road.' The first line is a hook: punchy and intriguing. The last line, 'Today, Peter the Great still rides on top of it.', is quiet and dry. Not deep, not booming, not a documentary voice, never shouting. "
         "Leave only short pauses between lines (about a third of a second).\nSpeak only the transcript below, nothing else.")
lines = [l.strip() for l in open(os.path.join(D, 'voice', 'script.txt')) if l.strip()]
txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(lines)
model = sys.argv[1] if len(sys.argv) > 1 else CFG['model']
OUTD = 'assets/audio/tts_' + os.path.basename(D).replace('-en', '').replace('-', '_')
os.makedirs(OUTD, exist_ok=True)
p = f"{OUTD}/take_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
a = tts.synth(txt, p, model, voice=CFG['voice'])
print(p, len(a) / tts.SR)
