"""Split the narration take into per-line clips (word-level marker alignment, shared with the
channel pipeline) -> assets/audio/tts/zombie_ep01/lines.json

usage: python -m episodes.zombie_ep01.align_voice
"""
import json
import os

from cinecode import tts
from episodes.rome_7_days.align_voice import align_take
from episodes.zombie_ep01.make_voice import OUT, ROOT, take_path
from episodes.zombie_ep01.script import LINES

LINES_JSON = os.path.join(OUT, "lines.json")

# Lines taken from an earlier take of the same voice, because the main take slurs a scripted word.
# l13: the main take is ambiguous between "our rooster" / "a rooster"; this take says "our" clearly.
ALT_TAKE = os.path.join(OUT, "narration_e35f764455.wav")
FROM_ALT = ["l13"]


def main():
    p = take_path()
    audio = tts.read_wav(p)
    res = align_take("zombie_ep01_" + os.path.basename(p)[:-4], audio, [l for l, _ in LINES], [t for _, t in LINES])
    for lid, r in res.items():
        r["file"] = os.path.relpath(p, ROOT)
    if FROM_ALT and os.path.exists(ALT_TAKE):
        alt = align_take("zombie_ep01_" + os.path.basename(ALT_TAKE)[:-4], tts.read_wav(ALT_TAKE),
                         [l for l, _ in LINES], [t for _, t in LINES])
        for lid in FROM_ALT:
            res[lid] = dict(alt[lid], file=os.path.relpath(ALT_TAKE, ROOT))
    json.dump(res, open(LINES_JSON, "w"), indent=1)
    for lid, t in LINES:
        r = res[lid]
        print(f"{lid} {os.path.basename(r['file'])[10:20]} {r['start']:6.2f}-{r['end']:6.2f} ({r['end'] - r['start']:4.2f}s)  {r['heard']}")


if __name__ == "__main__":
    main()
