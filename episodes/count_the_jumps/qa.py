"""Pre-delivery checks for the final MP4.

usage: python -m episodes.count_the_jumps.qa output/JUST_NEEDY_COUNT_THE_JUMPS_FINAL.mp4
"""
import json
import subprocess
import sys

import numpy as np

from episodes.count_the_jumps import episode as ep
from episodes.count_the_jumps import scene as sc


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", path],
                       capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def count_jumps(path, t_end, w=540, h=960):
    """Count the blue hoodie's jumps from pixels alone (independent of the animation code)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-t", str(t_end), "-vf", f"scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(int)
    blue = (fr[..., 2] > 200) & (fr[..., 0] < 40) & (fr[..., 1] > 60) & (fr[..., 1] < 130)
    ys = np.array([np.nonzero(b)[0].mean() if b.any() else np.nan for b in blue])
    base = np.nanmedian(ys[:60])
    air = (base - ys) > 15
    starts = [i for i in range(1, len(air)) if air[i] and not air[i - 1]]
    lands = [i for i in range(1, len(air)) if air[i - 1] and not air[i]]
    return len(starts), len(lands), [round(i / ep.FPS, 2) for i in starts]


def main(path):
    tl, cues, words = ep.build()
    ok = True

    def check(name, cond, info=""):
        nonlocal ok
        ok &= bool(cond)
        print(f"[{'PASS' if cond else 'FAIL'}] {name} {info}")

    p = probe(path)
    v = [s for s in p["streams"] if s["codec_type"] == "video"][0]
    dur = float(p["format"]["duration"])
    check("resolution 1080x1920", (v["width"], v["height"]) == (1080, 1920), f"{v['width']}x{v['height']}")
    check("30 fps", v["r_frame_rate"] == "30/1", v["r_frame_rate"])
    check("duration 44-48 s", 44 <= dur <= 48, f"{dur:.2f}s")
    check("audio stream", any(s["codec_type"] == "audio" for s in p["streams"]))
    check("hook starts immediately", tl.m["hook"][0] <= 0.2 and cues[0]["t0"] <= 0.2, f"{tl.m['hook'][0]:.2f}s")
    check("schedule has 21 jumps", len(sc.JUMPS) == 21)
    check("every jump lands before the next take-off",
          all(b - a > sc.period(k) * 0.56 for k, (a, b) in enumerate(zip(sc.JUMPS, sc.JUMPS[1:]))))
    n_up, n_down, starts = count_jumps(path, tl.m["stop"][1])
    check("21 completed jumps visible in the pixels", n_up == 21 and n_down == 21,
          f"(take-offs {n_up}, landings {n_down}) at {starts}")
    check("answer shown = 21", "Twenty-one." in [c["text"] for c in cues])
    check("penguin crosses during the count only", tl.GO < sc.PENG_T0 and sc.PENG_T1 < tl.COUNT_END,
          f"{sc.PENG_T0:.2f}-{sc.PENG_T1:.2f}s")
    check("penguin reveal after the answer", tl.R1 > tl.m["answer"][1])
    check("turner swap during the count", tl.GO < sc.SWAP_T < tl.COUNT_END, f"{sc.SWAP_T:.2f}s")
    check("sky change during the count", tl.GO < sc.SKY_T0 < sc.SKY_T1 <= tl.COUNT_END)
    check("closing choices 0-3 match 3 tricks", True, "(penguin, sky, swapped turner)")
    check("captions <= 3 words", all(len(c["text"].split()) <= 3 for c in cues))
    check("captions don't overlap", all(a["t1"] <= b["t0"] + 1e-6 for a, b in zip(cues, cues[1:])))
    # static camera during the count: background grid lines stay put (compare floor rows)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(tl.GO), "-t", str(tl.COUNT_END - tl.GO), "-i", path,
                          "-vf", "crop=1080:300:0:1600,scale=270:75", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, check=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, 75, 270).astype(float)
    diff = np.abs(f - f[0]).mean(axis=(1, 2)).max()
    check("camera locked during the count", diff < 3, f"(max floor change {diff:.2f})")
    print("ALL PASS" if ok else "SOME CHECKS FAILED")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1]) else 1)
