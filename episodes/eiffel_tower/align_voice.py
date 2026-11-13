"""Word-level forced alignment of the narration take (pocketsphinx, bundled en-us model)."""
import json
import re
import sys

import librosa
import numpy as np
import soundfile as sf
from pocketsphinx import Decoder

from episodes.eiffel_tower.script import LINES

NUM = {"1925": ["nineteen", "twenty", "five"]}


def script_words():
    """[(display_word, line_index, [align tokens])]"""
    out = []
    for li, line in enumerate(LINES):
        for w in line.replace("—", "— ").split():
            core = re.sub(r"[^A-Za-z0-9'é\-]", "", w)
            toks = []
            for part in core.split("-"):
                p = part.lower().replace("é", "e")
                toks += NUM.get(p, [p] if p else [])
            out.append((w, li, toks))
    return out


def align(wav):
    a, sr = sf.read(wav)
    if a.ndim > 1:
        a = a.mean(1)
    a16 = librosa.resample(a.astype(np.float32), orig_sr=sr, target_sr=16000)
    pcm = (np.clip(a16, -1, 1) * 32767).astype("<i2").tobytes()
    sw = script_words()
    toks = [t for _, _, ts in sw for t in ts]
    d = Decoder(samprate=16000, bestpath=False)
    d.set_align_text(" ".join(toks))
    d.start_utt()
    d.process_raw(pcm, full_utt=True)
    d.end_utt()
    segs = [(s.word, s.start_frame / 100.0, (s.end_frame + 1) / 100.0) for s in d.seg()]
    segs = [s for s in segs if s[0] not in ("<s>", "</s>", "<sil>", "[NOISE]") and not s[0].startswith("++")]
    segs = [(re.sub(r"\(\d+\)$", "", w), a0, b0) for w, a0, b0 in segs]
    assert [s[0] for s in segs] == toks, (len(segs), len(toks), [s[0] for s in segs][:40])
    words, k = [], 0
    for disp, li, ts in sw:
        n = len(ts)
        if n == 0:
            continue
        words.append({"w": disp, "line": li, "start": segs[k][1], "end": segs[k + n - 1][2]})
        k += n
    return words


if __name__ == "__main__":
    ws = align(sys.argv[1])
    json.dump(ws, open(sys.argv[2], "w"), indent=0)
    for w in ws:
        print(f"{w['start']:6.2f} {w['end']:6.2f} {w['line']:2d} {w['w']}")
