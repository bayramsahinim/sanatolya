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
    segs, tr = marker_transcript(name, audio)
    pw = align.parse_marked_transcript(tr, len(segs))
    assign, votes = align.assign_pieces(pw, texts)
    spans = {}
    for li in range(len(texts)):
        ks = [k for k in range(len(segs)) if assign[k] == li and votes[k]]
        if ks:
            spans[li] = [segs[ks[0]][0], segs[ks[-1]][1], ks]
    # lines with no piece of their own share a piece with a neighbour: split it
    for li in range(len(texts)):
        if li in spans:
            continue
        # find the piece voted for this line
        k = next((k for k in range(len(segs)) if li in votes[k]), None)
        if k is None:
            raise RuntimeError(f"{name}: no audio found for {ids[li]}: {texts[li]}")
        owner = assign[k]
        ps, pe = segs[k]
        n_this = votes[k][li]
        n_all = sum(votes[k].values())
        if owner > li:  # this line is the first part of the piece
            cut = align.split_point(audio, ps, pe, n_this / n_all)
            spans[li] = [ps, cut, [k]]
            if spans[owner][0] == ps:
                spans[owner][0] = cut + 0.02
        else:  # this line is the tail of the piece
            cut = align.split_point(audio, ps, pe, 1 - n_this / n_all)
            spans[li] = [cut + 0.02, pe, [k]]
            if spans[owner][1] == pe:
                spans[owner][1] = cut
    out = {}
    for li, (lid, text) in enumerate(zip(ids, texts)):
        s, e, ks = spans[li]
        heard = " ".join(w for k in range(ks[0], ks[-1] + 1) for w in pw[k])
        out[lid] = {"take": name, "start": round(s, 3), "end": round(e, 3), "heard": heard}
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
