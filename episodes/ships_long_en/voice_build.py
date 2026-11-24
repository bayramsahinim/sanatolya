"""Join the per-section takes into one narration track with breathing room between sections, and merge word times.
usage (repo root): python3 -m episodes.ships_long_en.voice_build <words_dir>
  <words_dir>/<section>.json = episodes.fort_en.words output for each take.
Writes yumurta/stories/ships-long-en/voice/{voice.wav,words.json,sections.json,script.txt}.
"""
import glob
import json
import sys

import numpy as np
from cinecode import tts
from episodes.ships_long_en.script import LINES

WD = sys.argv[1]
ST = 'yumurta/stories/ships-long-en/voice'
LEAD = .6                                   # silence before the first word
GAP = {'hook': 3.4}                         # after the hook: title card sting
DEF_GAP = 1.4                               # between sections: a music beat / scene change
SR = tts.SR
out, words, secs, t = [np.zeros(int(LEAD * SR), np.float32)], [], [], LEAD
for sid, text in LINES:
    p = glob.glob(f'assets/audio/tts_shipslong/{sid}_gemini-3.1*.wav')[0]
    a = tts.read_wav(p)
    a = np.asarray(a, np.float32)
    ws = json.load(open(f'{WD}/{sid}.json'))['words']
    s0 = max(0, ws[0]['start'] - .08); s1 = min(len(a) / SR, ws[-1]['end'] + .25)
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
print(round(len(y) / SR, 2), 's,', len(words), 'words'); print(json.dumps(secs))
