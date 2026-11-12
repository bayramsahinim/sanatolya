"""Split narration takes into per-line clips -> assets/audio/tts/lines.json

usage: python -m episodes.rome_7_days.align_voice [chunk ...]
"""
import glob
import json
import os
import subprocess
import sys

from cinecode import align, tts
from cinecode.transcribe import transcribe
from episodes.rome_7_days.make_voice import ROOT, OUT, chunk_path, dialogue_path
from episodes.rome_7_days.script import DIALOGUE, NARRATION, TTS_CHUNKS

LINES_JSON = os.path.join(OUT, "lines.json")


def _mp3(wav_audio, path):
    tmp = path + ".wav"
    tts.write_wav(tmp, wav_audio)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-b:a", "64k", path], check=True)
    os.remove(tmp)


def marker_transcript(name, audio):
    segs = align.pieces(audio)
    cache = os.path.join(OUT, f"markers_{name}.json")
    if os.path.exists(cache):
        d = json.load(open(cache))
        if d["pieces"] == [[round(s, 3), round(e, 3)] for s, e in segs]:
            return segs, d["transcript"]
    mp3 = f"/tmp/markers_{name}.mp3"
    good = False
    for attempt, gain in enumerate([0.3, 0.6, 0.45, 0.8, 0.3, 0.6]):
        align.MARKER_GAIN = gain
        _mp3(align.marker_audio(audio, segs), mp3)
        tr = transcribe(mp3)
        pw = align.parse_marked_transcript(tr, len(segs))
        if sum(1 for w in pw if w) >= 0.5 * len(segs):
            good = True
            break
        print(f"  {name}: markers missing from transcript (gain {gain}), retrying")
    if not good:
        raise RuntimeError(f"{name}: could not get a marker transcript")
    json.dump({"pieces": [[round(s, 3), round(e, 3)] for s, e in segs], "transcript": tr},
              open(cache, "w"), indent=1)
    return segs, tr


def align_take(name, audio, ids, texts):
    """Word-level timing: every transcribed word gets a span inside its piece (proportional to
    its length), words are matched to the script, and each line runs from its first to its last
    word. Boundaries between lines that share a piece are snapped to the quietest point."""
    import difflib
    segs, tr = marker_transcript(name, audio)
    pw = align.parse_marked_transcript(tr, len(segs))
    words = []  # (word, t0, t1, piece)
    for k, ((ps, pe), ws) in enumerate(zip(segs, pw)):
        if not ws:
            continue
        wts = [len(w) + 2 for w in ws]
        tot = sum(wts)
        t = ps
        for w, wt in zip(ws, wts):
            d = (pe - ps) * wt / tot
            words.append((w, t, t + d, k))
            t += d
    line_words = [align._words(x) for x in texts]
    flat = [w for ws in line_words for w in ws]
    owner = [li for li, ws in enumerate(line_words) for _ in ws]
    sm = difflib.SequenceMatcher(a=[w[0] for w in words], b=flat, autojunk=False)
    hits = {}
    for i, j, n in sm.get_matching_blocks():
        for q in range(n):
            hits.setdefault(owner[j + q], []).append(i + q)
    # a line with no matching words (e.g. "Catch!" heard as "Cat.") takes the unmatched
    # transcript words between its neighbours
    for li in range(len(ids)):
        if li in hits:
            continue
        lo = max(hits[li - 1]) + 1 if li - 1 in hits else 0
        nxt = next((min(hits[j]) for j in range(li + 1, len(ids)) if j in hits), len(words))
        if lo < nxt:
            hits[li] = list(range(lo, nxt))
    spans = []
    for li, lid in enumerate(ids):
        if li not in hits:
            raise RuntimeError(f"{name}: no audio found for {lid}: {texts[li]}")
        i0, i1 = min(hits[li]), max(hits[li])
        # include unmatched transcript words that sit between this line's matches
        spans.append([words[i0][1], words[i1][2], words[i0][3], words[i1][3], i0, i1])
    # unmatched transcript words between two lines: give them to the line that is missing words
    for li in range(len(spans) - 1):
        a_, b_ = spans[li], spans[li + 1]
        gap = list(range(a_[5] + 1, b_[4]))
        if not gap:
            continue
        a_full = len(hits[li]) >= len(line_words[li])
        if a_full:
            b_[4] = gap[0]
            b_[0] = words[gap[0]][1]
            b_[2] = words[gap[0]][3]
        else:
            a_[5] = gap[-1]
            a_[1] = words[gap[-1]][2]
            a_[3] = words[gap[-1]][3]
    for li in range(len(spans) - 1):
        a_, b_ = spans[li], spans[li + 1]
        if a_[3] == b_[2]:  # same piece: cut at the quietest point between them
            k = a_[3]
            ps, pe = segs[k]
            guess = (a_[1] + b_[0]) / 2
            cut = align.split_point(audio, ps, pe, (guess - ps) / max(pe - ps, 1e-3), window=0.15)
            cut = min(max(cut, a_[0] + 0.25), b_[1] - 0.25)
            a_[1] = cut
            b_[0] = cut + 0.02
    out = {}
    for li, lid in enumerate(ids):
        s0, e0, k0, k1, i0, i1 = spans[li]
        heard = " ".join(w[0] for w in words[i0:i1 + 1])
        out[lid] = {"take": name, "start": round(s0, 3), "end": round(e0, 3), "heard": heard}
    return out


def main(which=None):
    lines = json.load(open(LINES_JSON)) if os.path.exists(LINES_JSON) else {}
    for i, scenes in enumerate(TTS_CHUNKS):
        if which and i not in which:
            continue
        p = chunk_path(i)
        if not os.path.exists(p):
            print("missing take", i)
            continue
        audio = tts.read_wav(p)
        ids = [lid for s in scenes for lid, _ in NARRATION[s]]
        texts = [t for s in scenes for _, t in NARRATION[s]]
        res = align_take(f"narration_{i:02d}", audio, ids, texts)
        for lid, r in res.items():
            r["file"] = os.path.relpath(p, ROOT)
        lines.update(res)
        json.dump(lines, open(LINES_JSON, "w"), indent=1)
        print(f"take {i}: aligned {len(res)} lines")
    dp = dialogue_path()
    if os.path.exists(dp) and (not which or -1 in which):
        audio = tts.read_wav(dp)
        res = align_take("dialogue", audio, [d[0] for d in DIALOGUE], [d[2] for d in DIALOGUE])
        for lid, r in res.items():
            r["file"] = os.path.relpath(dp, ROOT)
        lines.update(res)
        print("dialogue aligned")
    json.dump(lines, open(LINES_JSON, "w"), indent=1)


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or None)
