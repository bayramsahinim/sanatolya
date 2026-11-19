"""Second Gemini pass: boxes for the prisoner's striped arms on keyframes where he is visible."""
import concurrent.futures as cf
import json
import os
import sys

from episodes.dry_peas_escape.vfx import detect

PROMPT = """This is a frame from a cartoon. The MAIN PRISONER wears a black-and-white striped uniform; his
arms are long thin black-and-white striped sleeves. Guards (green) and the warden (red) are NOT the prisoner.
Return JSON only: a list {"label": "arm", "box_2d": [ymin, xmin, ymax, xmax]} (0-1000) with one tight box
per visible striped prisoner ARM (from shoulder to hand). Return [] if no prisoner arm is visible."""


def main(frames, det_json, out):
    det = json.load(open(det_json))
    res = json.load(open(out)) if os.path.exists(out) else {}
    todo = [k for k, v in sorted(det.items()) if v and k not in res]
    detect.PROMPT = PROMPT
    with cf.ThreadPoolExecutor(3) as ex:
        for k, r in zip(todo, ex.map(lambda k: detect.call(os.path.join(frames, k)), todo)):
            res[k] = r
            json.dump(res, open(out, "w"), indent=0, sort_keys=True)
    print(len(res), "frames")


if __name__ == "__main__":
    main(*sys.argv[1:4])
