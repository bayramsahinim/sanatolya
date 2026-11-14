"""Global timeline: where every narration block, caption group and key event lands.

All visual timing (renderer) and the audio mix read build/spot_the_change/timeline.json,
so picture, voice and captions come from one source of truth.

usage: python -m episodes.spot_the_change.timeline   -> timeline.json + output SRT
"""
import json
import os

from episodes.spot_the_change.script import BLOCKS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LINES = os.path.join(ROOT, "assets", "audio", "tts", "spot_the_change", "lines.json")
BUILD = os.path.join(ROOT, "build", "spot_the_change")
OUT = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_CAN_YOU_SPOT_THE_CHANGE"

FPS = 30
HOOK_AT = 0.20          # first word
GAP = 0.18              # silence between blocks (on top of each take's own lead-in)
TEST_LEN = 12.0         # the live attention test: one locked shot, continuous colour change
END_HOLD = 0.55         # after the last word


def build():
    L = json.load(open(LINES))
    order = [n for n, _ in BLOCKS]
    ids = {n: [lid for lid, _ in lines] for n, lines in BLOCKS}

    def first(n):
        return L[ids[n][0]]["start"]

    def last(n):
        return L[ids[n][-1]]["end"]

    starts = {}
    t = HOOK_AT - first("hook")
    starts["hook"] = t
    t = starts["hook"] + last("hook") + GAP + 0.08
    starts["task"] = t - first("task")
    go = starts["task"] + L["t4"]["start"]
    test0 = go + 0.15
    test1 = test0 + TEST_LEN
    starts["reveal"] = test1 + 0.05 - first("reveal") + 0.25
    t = starts["reveal"] + last("reveal")
    for n in order[3:]:
        starts[n] = t + GAP + 0.12 - first(n)
        t = starts[n] + last(n)
    end = t + END_HOLD

    lines, caps = {}, []
    for n in order:
        for lid in ids[n]:
            d = L[lid]
            s = starts[n] + d["start"]
            lines[lid] = {"t0": round(s, 3), "t1": round(starts[n] + d["end"], 3), "text": d["text"],
                          "words": [(w, round(s + a, 3), round(s + b, 3)) for w, a, b in d["words"]]}
            for g in d["groups"]:
                caps.append({"text": g["text"], "t0": round(s + g["t0"], 3), "t1": round(s + g["t1"], 3), "line": lid})
    # caption hand-off: each group stays until the next one starts (max 0.6 s overhang)
    for a, b in zip(caps, caps[1:]):
        a["t1"] = round(min(b["t0"], max(a["t1"], a["t0"] + 0.25) + 0.6) - 0.001, 3)
        if b["t0"] - a["t1"] < 0.05:
            a["t1"] = round(b["t0"] - 0.001, 3)
    caps[-1]["t1"] = round(end - 0.1, 3)

    tl = {"fps": FPS, "duration": round(end, 3), "nframes": int(round(end * FPS)),
          "blocks": {n: round(starts[n], 3) for n in order},
          "test": [round(test0, 3), round(test1, 3)],
          "lines": lines, "captions": caps}
    return tl


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(tl, path):
    """Readable CC cues: a sentence per cue, long sentences split at commas, from word timings."""
    cues = []
    for lid, ln in tl["lines"].items():
        words = ln["words"]
        chunk = []
        for i, (w, a, b) in enumerate(words):
            chunk.append((w, a, b))
            n = len(chunk)
            if i == len(words) - 1 or (w.endswith(",") and n >= 3) or n >= 8:
                cues.append([chunk[0][1], chunk[-1][2], " ".join(x[0] for x in chunk)])
                chunk = []
    for a, b in zip(cues, cues[1:]):
        a[1] = min(max(a[1] + 0.25, a[0] + 0.8), b[0] - 0.02)
    cues[-1][1] += 0.4
    with open(path, "w") as f:
        for i, (a, b, s) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{s}\n\n")
    return cues


if __name__ == "__main__":
    tl = build()
    os.makedirs(BUILD, exist_ok=True)
    json.dump(tl, open(os.path.join(BUILD, "timeline.json"), "w"), indent=1)
    cues = write_srt(tl, os.path.join(OUT, NAME + ".srt"))
    print("duration", tl["duration"], "frames", tl["nframes"], "test", tl["test"])
    for n, s in tl["blocks"].items():
        print(f"  {n:9s} {s:6.2f}")
    for c in tl["captions"]:
        print(f"  {c['t0']:6.2f}-{c['t1']:6.2f} {c['text']}")
    print(len(cues), "SRT cues")
