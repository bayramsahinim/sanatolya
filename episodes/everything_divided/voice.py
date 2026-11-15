"""Build the narration track: align the take word-by-word, tighten pauses, and export
voice.wav (48 kHz) + timing.json (lines, words, caption groups on the final timeline).

usage: python -m episodes.everything_divided.voice
"""
import json
import os

import numpy as np

from cinecode import audio as A
from cinecode import tts, wordalign
from episodes.everything_divided.make_voice import take_path
from episodes.everything_divided.script import CAPTIONS, LINES, PARA_AFTER

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "everything")
TIMING = os.path.join(ROOT, "episodes", "everything_divided", "timing.json")
TAKE = 0
LEAD = 0.30          # silence before the first word
GAP_WORD = 0.16      # max pause inside a sentence
GAP_LINE = 0.30      # max pause between lines
GAP_PARA = 0.46      # max pause between paragraphs (scene changes)
TEMPO = 1.0


def caption_groups():
    out = []
    for lid, spoken, _ in LINES:
        n_line = len(wordalign.tokens(spoken))
        n = 0
        for g in CAPTIONS[lid]:
            disp, sp = (g.split("=", 1) + [None])[:2] if "=" in g else (g, g)
            k = len(wordalign.tokens(sp))
            out.append({"line": lid, "text": disp, "nwords": k})
            n += k
        assert n == n_line, (lid, n, n_line)
    return out


def build():
    take = tts.read_wav(take_path(TAKE))
    words, pcs, owner = wordalign.align_pieces(take, tts.SR, [s for _, s, _ in LINES])
    # map each piece onto the new timeline with capped pauses
    word_line = [w[3] for w in words]
    piece_last_line = {}
    piece_first_line = {}
    for k, o in enumerate(owner):
        piece_last_line[o] = word_line[k]
        piece_first_line.setdefault(o, word_line[k])
    shift = {}
    t = LEAD
    used = sorted(set(owner))
    segs = []
    for i, pi in enumerate(used):
        a, b = pcs[pi]
        if i > 0:
            prev = used[i - 1]
            orig_gap = a - pcs[prev][1]
            l_prev, l_next = piece_last_line[prev], piece_first_line[pi]
            if l_prev != l_next:
                cap = GAP_PARA if LINES[l_prev][0] in PARA_AFTER else GAP_LINE
            else:
                cap = GAP_WORD
            t += min(orig_gap, cap)
        shift[pi] = t - a
        segs.append((a, b, t))
        t += b - a
    total = t
    sr_out = A.SR
    y = np.zeros(int((total + 1.0) * sr_out), dtype=np.float32)
    src48 = A.resample(take, tts.SR, sr_out)
    pre, post = 0.025, 0.06
    for a, b, t0 in segs:
        i0, i1 = int((a - pre) * sr_out), int((b + post) * sr_out)
        clip = src48[max(0, i0):i1].copy()
        f = int(0.012 * sr_out)
        clip[:f] *= np.linspace(0, 1, f)
        clip[-f:] *= np.linspace(1, 0, f)
        j = int((t0 - pre) * sr_out)
        y[j:j + len(clip)] += clip[: len(y) - j]
    os.makedirs(BUILD, exist_ok=True)
    import soundfile as sf
    sf.write(os.path.join(BUILD, "voice.wav"), y, sr_out)
    # final word times
    fw = []
    for (w, s, e, li), o in zip(words, owner):
        fw.append({"w": w, "t0": round(s + shift[o], 3), "t1": round(e + shift[o], 3), "line": LINES[li][0]})
    lines = {}
    for x in fw:
        L = lines.setdefault(x["line"], {"t0": x["t0"], "t1": x["t1"]})
        L["t1"] = x["t1"]
    groups = caption_groups()
    k = 0
    for g in groups:
        ws = fw[k:k + g["nwords"]]
        g["t0"], g["t1"] = ws[0]["t0"], ws[-1]["t1"]
        g["words"] = [x["w"] for x in ws]
        k += g["nwords"]
    json.dump({"duration_voice": round(total, 3), "lines": lines, "words": fw, "captions": groups},
              open(TIMING, "w"), indent=1)
    print(f"voice: {total:.2f}s ({len(fw)} words, {len(groups)} caption groups) -> {TIMING}")
    for lid, v in lines.items():
        print(f"  {lid:6s} {v['t0']:6.2f} - {v['t1']:6.2f}")


if __name__ == "__main__":
    build()
