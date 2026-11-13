"""Build the final narration track from the chosen take, then word-align the FINAL audio.

1. Rubber Band tempo 0.95 (formant-preserving, R3 engine) for a slightly more measured read.
2. Cut at sentence boundaries and widen the gaps by hand-chosen beats (bigger before/after reveals).
3. Forced-align the final track -> build/words.json (drives captions, SRT and animation timing).
"""
import json
import os
import subprocess

import numpy as np
import soundfile as sf

from episodes.eiffel_tower.align_voice import align

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAKE = os.path.join(ROOT, "assets/audio/tts_eiffel/take_gemini-3.8-flash-lite-tts_21eda7dcd9.wav")
BUILD = os.path.join(ROOT, "build")
OUT_WAV = os.path.join(ROOT, "assets/audio/tts_eiffel/narration_final.wav")
WORDS = os.path.join(ROOT, "assets/audio/tts_eiffel/words.json")
TEMPO = 0.95
LEAD = 0.20
TAIL = 0.70
# extra silence inserted after each line (seconds)
BEATS = [0.15, 0.35, 0.45, 0.25, 0.25, 0.25, 0.35, 0.15, 0.40, 0.25,
         0.20, 0.35, 0.30, 0.45, 0.35, 0.40, 0.45, 0.30, 0.45]
SR = 48000


def main():
    os.makedirs(BUILD, exist_ok=True)
    st = os.path.join(BUILD, "narr_stretched.wav")
    up = os.path.join(BUILD, "narr_48k.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", TAKE, "-ar", str(SR), "-ac", "1", up], check=True)
    subprocess.run(["rubberband", "-q", "-3", "-F", "-T", str(TEMPO), up, st], check=True)
    a, sr = sf.read(st)
    w = align(st)
    # line spans
    lines = {}
    for x in w:
        s, e = lines.get(x["line"], (1e9, 0))
        lines[x["line"]] = (min(s, x["start"]), max(e, x["end"]))
    n = len(lines)
    cuts = [0.0]
    for i in range(n - 1):
        cuts.append((lines[i][1] + lines[i + 1][0]) / 2)
    cuts.append(len(a) / sr)
    first, last = lines[0][0], lines[n - 1][1]
    pieces = [np.zeros(int(LEAD * SR))]
    for i in range(n):
        s = max(cuts[i], first - 0.03) if i == 0 else cuts[i]
        e = min(cuts[i + 1], last + 0.35) if i == n - 1 else cuts[i + 1]
        seg = a[int(s * sr):int(e * sr)].copy()
        # tiny fades at cut points (cuts sit in silence; guards against clicks)
        f = int(0.008 * sr)
        seg[:f] *= np.linspace(0, 1, f)
        seg[-f:] *= np.linspace(1, 0, f)
        pieces.append(seg)
        if i < n - 1:
            pieces.append(np.zeros(int(BEATS[i] * SR)))
    pieces.append(np.zeros(int(TAIL * SR)))
    out = np.concatenate(pieces)
    out = out / (np.abs(out).max() + 1e-9) * 0.89
    sf.write(OUT_WAV, out.astype(np.float32), SR, subtype="PCM_16")
    ws = align(OUT_WAV)
    json.dump(ws, open(WORDS, "w"), indent=0)
    print(f"final narration {len(out)/SR:.2f}s, last word ends {ws[-1]['end']:.2f}s")


if __name__ == "__main__":
    main()
