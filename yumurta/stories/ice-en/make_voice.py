"""Narration for the ice-carrier story (same narrator as Troy / pink). usage (repo root): python3 yumurta/stories/<story>/make_voice.py [model]"""
import json, os, sys
sys.path.insert(0, '.')
from cinecode import tts
D = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open('config/narrator_voice.json'))
NOTES = ("Narrator of a witty YouTube Shorts animation channel telling a wild true story to a friend. "
         "Voice: young adult American male, energetic but natural, clean and bright, fast pace like a well-edited Short, "
         "lightly sarcastic and clever, knowing smile on the twists. Real comic timing: the first line is the hook, punchy and "
         "intriguing, with a tiny beat before 'and shot a block of ice.'; 'An aircraft carrier... made of ice.' with disbelief; "
         "the generals' line 'Ice? Ice sinks ships. It doesn't make them!' in a mocking, pompous old-general voice; "
         "a sneaky, secretive tone on 'with a secret ingredient.'; a dry beat on 'who is in his bath.'; a proud punch on 'And it doesn't melt.'; "
         "'Or so Mountbatten claimed.' quick and dry, an aside; a held breath on 'He aims at the second one...'; "
         "fast and excited on 'The bullet bounces right back'; a satisfied, quiet 'Nobody is laughing now.'; "
         "a knowing pause before 'Sawdust.'; the last line quiet and dry. Not deep, not booming, not a documentary voice, never shouting. "
         "Leave only short pauses between lines (about a third of a second).\nSpeak only the transcript below, nothing else.")
lines = [l.strip() for l in open(os.path.join(D, 'voice', 'script.txt')) if l.strip()]
txt = "### DIRECTOR'S NOTES\n" + NOTES + "\n\n#### TRANSCRIPT\n" + "\n\n".join(lines)
model = sys.argv[1] if len(sys.argv) > 1 else CFG['model']
OUTD = 'assets/audio/tts_' + os.path.basename(D).replace('-en', '').replace('-', '_')
os.makedirs(OUTD, exist_ok=True)
p = f"{OUTD}/take_{model}_{tts.text_hash(txt, CFG['voice'], model)}.wav"
a = tts.synth(txt, p, model, voice=CFG['voice'])
print(p, len(a) / tts.SR)
