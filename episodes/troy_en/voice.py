"""Narration: one Gemini TTS take -> tightened pauses -> voice.wav + word timing.

usage: python -m episodes.troy_en.voice
Writes build/troy_en/voice.wav and build/troy_en/timing.json:
  {"duration": s, "words": [[start, end, word, line_id], ...], "lines": {id: [start, end]}}
"""
import json
import os
import re

import numpy as np

from cinecode import tts
from episodes.troy_en.script import LINES

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAKE = os.path.join(ROOT, "assets", "audio", "tts_troy", "take_gemini-3.8-flash-tts_25f0cc36ca.wav")
BUILD = os.path.join(ROOT, "build", "troy_en")
LEAD_IN = 0.12
TAIL = 2.2
SR = tts.SR

KEEP_SENT = 0.36     # max pause after . ? !
KEEP_COMMA = 0.22    # max pause after , : ;
KEEP_WORD = 0.16     # max pause between words
KEEP_AFTER = {"hollow.": 0.55, "sacred.": 0.45, "back.": 0.55, "walls.": 0.40}


def norm(w):
    return re.sub(r"[^a-z0-9öü']", "", w.lower().replace("’", "'"))


def map_lines(words):
    """Assign each recognised word to a script line by walking the script tokens."""
    toks = []
    for lid, txt in LINES:
        for w in txt.split():
            n = norm(w)
            if n:
                toks.append((n, lid))
    out, j = [], 0
    for s, e, w in words:
        n = norm(w)
        # numbers may be recognised as digits ("10" for "ten")
        while j < len(toks) - 1 and toks[j][0] != n and not (n.isdigit() and toks[j][0] == "ten"):
            # tolerate small mismatches: stay put unless the next token matches
            if toks[j + 1][0] == n:
                j += 1
                break
            break
        out.append([s, e, w, toks[min(j, len(toks) - 1)][1]])
        j += 1
    return out


def build():
    a = tts.read_wav(TAKE)
    W = json.load(open(TAKE + ".words.json"))
    pieces, words = [], []
    t_out = LEAD_IN
    pieces.append(np.zeros(int(LEAD_IN * SR), np.float32))
    cur = max(0.0, W[0][0] - 0.06)
    for i, (s, e, w) in enumerate(W):
        if i + 1 < len(W):
            gap = W[i + 1][0] - e
            if w in KEEP_AFTER:
                keep = KEEP_AFTER[w]
            elif w[-1] in ".?!":
                keep = KEEP_SENT
            elif w[-1] in ",:;":
                keep = KEEP_COMMA
            else:
                keep = KEEP_WORD
            if gap > keep:
                # cut the middle of the gap, keep half the allowance on each side
                c0, c1 = e + keep / 2, W[i + 1][0] - keep / 2
                seg = a[int(cur * SR):int(c0 * SR)]
                pieces.append(seg)
                words.append([t_out + (s - cur), t_out + (e - cur), w])
                t_out += len(seg) / SR
                cur = c1
                continue
        words.append([t_out + (s - cur), t_out + (e - cur), w])
    seg = a[int(cur * SR):int((W[-1][1] + 0.35) * SR)]
    pieces.append(seg)
    t_out += len(seg) / SR
    # short crossfades at every join to avoid clicks
    out = pieces[0]
    xf = int(0.012 * SR)
    for p in pieces[1:]:
        if len(out) > xf and len(p) > xf:
            r = np.linspace(0, 1, xf, dtype=np.float32)
            out = np.concatenate([out[:-xf], out[-xf:] * (1 - r) + p[:xf] * r, p[xf:]])
        else:
            out = np.concatenate([out, p])
    out = np.concatenate([out, np.zeros(int(TAIL * SR), np.float32)])
    # level: active-speech RMS to -20 dBFS
    act = np.abs(out) > 0.02
    rms = np.sqrt((out[act] ** 2).mean())
    out = out * (10 ** (-20 / 20) / rms)
    dur = len(out) / SR
    words = map_lines([(round(s, 3), round(e, 3), w) for s, e, w in words])
    lines = {}
    for s, e, w, lid in words:
        lines.setdefault(lid, [s, e])
        lines[lid][1] = e
    os.makedirs(BUILD, exist_ok=True)
    tts.write_wav(os.path.join(BUILD, "voice.wav"), out)
    json.dump({"duration": round(dur, 3), "words": words, "lines": lines},
              open(os.path.join(BUILD, "timing.json"), "w"), indent=0)
    print(f"voice {dur:.2f}s (take {len(a) / SR:.2f}s)")
    for lid, (s, e) in lines.items():
        print(f"  {lid:7s} {s:6.2f} - {e:6.2f}")


if __name__ == "__main__":
    build()
