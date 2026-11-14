"""Pre-delivery checks for THE BUTTON (English).

usage: python -m episodes.the_button_en.qa output/JUST_NEEDY_THE_BUTTON_ENGLISH.mp4 [sheet.jpg]
* container: 1080x1920, 30 fps, H.264 + AAC, duration close to the source
* every planned line is present and in source order; caption groups never overlap
* caption text == narration text (word for word, after display mapping)
* writes a contact sheet (one frame per Turkish sentence slot) for scene-by-scene visual review
"""
import json
import os
import re
import subprocess
import sys

import cv2
import numpy as np

from episodes.the_button_en.script import LINES

HERE = os.path.dirname(os.path.abspath(__file__))


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_name,width,height,r_frame_rate:format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def norm_words(s):
    s = s.replace("$50,000", "fifty thousand dollars").replace("$25,000", "twenty-five-thousand-dollar")
    s = s.replace("8 p.m.", "eight p.m.")
    return [w for w in re.sub(r"[^\w'$,-]+", " ", s.lower()).replace(",", " ").split()]


def main(path, sheet=None):
    ok = True
    info = probe(path)
    v = [s for s in info["streams"] if s["codec_name"] == "h264"][0]
    a = [s for s in info["streams"] if s["codec_name"] == "aac"]
    dur = float(info["format"]["duration"])
    print(f"video {v['width']}x{v['height']} @ {v['r_frame_rate']}, audio {'yes' if a else 'NO'}, {dur:.2f}s")
    ok &= (v["width"], v["height"]) == (1080, 1920) and v["r_frame_rate"] == "30/1" and bool(a)
    ok &= abs(dur - 139.3) / 139.3 < 0.10
    tl = json.load(open(os.path.join(HERE, "timeline.json")))
    caps, lines = tl["captions"], tl["plan"]["lines"]
    ok &= [ln["i"] for ln in lines] == list(range(len(LINES)))
    for x, y in zip(caps, caps[1:]):
        if x["end"] > y["start"] + 1e-6:
            print("overlap", x, y)
            ok = False
    for ln in lines:
        shown = " ".join(c["text"] for c in caps if c["line"] == ln["i"])
        if norm_words(shown) != norm_words(LINES[ln["i"]][1]):
            print("caption/narration mismatch", ln["i"], shown, "|", LINES[ln["i"]][1])
            ok = False
    longest = max(len(c["text"].split()) for c in caps)
    print(f"{len(caps)} caption groups, max {longest} words/group")
    if sheet:
        cap = cv2.VideoCapture(path)
        tiles = []
        for ln in lines:
            t = (ln["start"] + ln["end"]) / 2
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            _, f = cap.read()
            f = cv2.resize(f, (216, 384))
            cv2.putText(f, f"{ln['i']} {t:.1f}s", (6, 376), 0, 0.5, (0, 255, 255), 1)
            tiles.append(f)
        while len(tiles) % 8:
            tiles.append(np.zeros_like(tiles[0]))
        cv2.imwrite(sheet, np.vstack([np.hstack(tiles[i:i + 8]) for i in range(0, len(tiles), 8)]))
    print("QA", "PASSED" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(*sys.argv[1:]) else 1)
