"""Join the per-section takes into one narration track (tight gaps) and merge word times.
usage (repo root): python3 -m episodes.ships_doc_en.voice_build <words_dir>
  Takes: assets/audio/tts_shipsdoc/<section>_gemini-3.8-flash-tts_*.wav (main model), else the 3.1 preview take, else a
  silent placeholder with evenly spaced words (preview only). <words_dir>/<section>.json = episodes.fort_en.words output.
Writes yumurta/stories/ships-doc-en/voice/{voice.wav,words.json,sections.json,script.txt}.
"""
import glob
import json
import os
import sys

import numpy as np
from cinecode import tts
from episodes.ships_doc_en.script import LINES

WD = sys.argv[1]
ST = 'yumurta/stories/ships-doc-en/voice'
os.makedirs(ST, exist_ok=True)
LEAD = .5
GAP = {'hook': 2.6}                         # after the hook: the title card
DEF_GAP = .75                               # between sections: a short music beat
SR = tts.SR
out, words, secs, t, used = [np.zeros(int(LEAD * SR), np.float32)], [], [], LEAD, {}
for sid, text in LINES:
    takes = glob.glob(f'assets/audio/tts_shipsdoc/{sid}_gemini-3.8-flash-tts_*.wav') or glob.glob(f'assets/audio/tts_shipsdoc/{sid}_gemini-3.1*.wav')
    if takes and os.path.exists(f'{WD}/{sid}.json'):
        a = np.asarray(tts.read_wav(takes[0]), np.float32); used[sid] = os.path.basename(takes[0])
        ws = json.load(open(f'{WD}/{sid}.json'))['words']
    else:
        n = len(text.split()); a = np.zeros(int(n * .36 * SR + SR * .3), np.float32); used[sid] = 'PLACEHOLDER'
        ws = [{'word': w, 'start': .1 + i * .36, 'end': .1 + i * .36 + .3} for i, w in enumerate(text.split())]
    s0 = max(0, ws[0]['start'] - .08); s1 = min(len(a) / SR, ws[-1]['end'] + .22)
    seg = a[int(s0 * SR):int(s1 * SR)]
    for w in ws:
        words.append({'word': w['word'], 'start': round(t + w['start'] - s0, 3), 'end': round(t + w['end'] - s0, 3), 'sec': sid})
    secs.append({'id': sid, 'start': round(t, 3), 'end': round(t + len(seg) / SR, 3)})
    out.append(seg); t += len(seg) / SR
    g = GAP.get(sid, DEF_GAP)
    out.append(np.zeros(int(g * SR), np.float32)); t += g
y = np.concatenate(out)
tts.write_wav(f'{ST}/voice.wav', y)
json.dump({'words': words}, open(f'{ST}/words.json', 'w'), indent=0)
json.dump(secs, open(f'{ST}/sections.json', 'w'), indent=1)
open(f'{ST}/script.txt', 'w').write('\n\n'.join(t for _, t in LINES))
print(round(len(y) / SR, 2), 's,', len(words), 'words'); print(json.dumps(used)); print(json.dumps(secs))
