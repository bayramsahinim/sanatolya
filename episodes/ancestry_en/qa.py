"""Pre-delivery checks for the English ancestry adaptation.

usage: python -m episodes.ancestry_en.qa output/Just_Needy_What_If_Every_Human_Is_Related_EN.mp4
"""
import json
import re
import subprocess
import sys

from episodes.ancestry_en import render as R
from episodes.ancestry_en.script import CAPTION, LINES

TURKISH = re.compile(r"[çğıöşüÇĞİÖŞÜ]|\b(ve|bir|yıl|önce|ata|kuşak|akraba|nüfus|hepimiz|soy|dünya)\b", re.I)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate:format=duration",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def main(path):
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + msg)
        ok &= bool(cond)

    info = probe(path)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    dur = float(info["format"]["duration"])
    check(v["width"] == 1080 and v["height"] == 1920, f"resolution {v['width']}x{v['height']}")
    check(v["r_frame_rate"] == "30/1", f"frame rate {v['r_frame_rate']}")
    check(any(s["codec_type"] == "audio" for s in info["streams"]), "audio track present")
    check(80 <= dur <= 87, f"duration {dur:.2f}s (target ~80-85)")
    # on-screen text: captions, headers, labels
    texts = [CAPTION[l] for l, _, _ in LINES]
    for e in R.header_entries():
        for t in (e[0] + 0.5, ):
            texts.append(e[1])
            texts.append(e[2](t) if callable(e[2]) else e[2])
            texts.append(e[3])
    texts += [n for n, *_ in R.LABELS] + [n for n, *_ in R.PINS] + ["JUST NEEDY", "Mitochondrial Eve", "Y-chromosomal Adam",
                                                                      "ANCESTOR SLOTS NEEDED", "PEOPLE ALIVE IN THE 1200s", "AFRICA"]
    bad = [t for t in texts if t and TURKISH.search(t)]
    check(not bad, f"no Turkish text on screen ({len(texts)} strings checked){' -> ' + str(bad) if bad else ''}")
    check("1,073,741,824" in " ".join(texts) or R.fmt(2 ** 30) == "1,073,741,824", "30-generation figure is 1,073,741,824")
    check(any("doubling model" in (t or "") for t in texts), "30-generation figure labelled as positions in a doubling model")
    check(any("not a couple" in (t or "") for t in texts), "Eve/Adam explicitly not a couple")
    # caption timing sanity
    for t0, t1, words, end in R.CAPS.chunks:
        if t1 - t0 < 0.25:
            check(False, f"caption chunk too short: {' '.join(w for w, _, _ in words)}")
    check(all(len(" ".join(w for w, _, _ in c[2])) <= 34 for c in R.CAPS.chunks), "caption chunks short (<= 34 chars)")
    # loudness
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)
    if m:
        check(-16 <= float(m[-1]) <= -12, f"integrated loudness {m[-1]} LUFS")
    if tp:
        check(float(tp[-1]) <= -0.5, f"true peak {tp[-1]} dBFS")
    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1]) else 1)
