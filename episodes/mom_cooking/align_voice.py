"""Word-level alignment of the takes -> assets/audio/tts/mom_cooking/lines.json
(reuses the marker-transcript aligner from the Rome episode).

usage: python -m episodes.mom_cooking.align_voice
"""
import json
import os

from cinecode import tts
from episodes.mom_cooking.make_voice import OUT, ROOT, take_path
from episodes.mom_cooking.script import DIALOGUE, NARRATION
from episodes.rome_7_days import align_voice as rav

LINES_JSON = os.path.join(OUT, "lines.json")
rav.OUT = OUT   # marker transcript caches live next to this episode's takes


def main():
    lines = {}
    groups = {
        "narration": NARRATION,
        "me": [(l, t) for l, w, t in DIALOGUE if w == "Me"],
        "mom": [(l, t) for l, w, t in DIALOGUE if w == "Mom"],
    }
    for name, items in groups.items():
        p = take_path(name)
        audio = tts.read_wav(p)
        res = rav.align_take(f"mom_{name}", audio, [l for l, _ in items], [t for _, t in items])
        for lid, r in res.items():
            r["file"] = os.path.relpath(p, ROOT)
            print(f"{lid:4s} {r['start']:6.2f} {r['end']:6.2f}  {r['heard']}")
        lines.update(res)
    json.dump(lines, open(LINES_JSON, "w"), indent=1)


if __name__ == "__main__":
    main()
