"""Pre-delivery checks for Episode 1 (duration, format, script coverage, voice level, loudness, SRT).

usage: python -m episodes.zombie_ep01.qa
"""
import episodes.zombie_ep01  # noqa: F401

import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

from episodes.zombie_ep01.episode import BUILD, MIX, SRT, VIDEO, build_episode
from episodes.zombie_ep01.script import LINES, TEXT


def main():
    ep = build_episode()
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + msg)
        ok &= bool(cond)

    check(58 <= ep.duration <= 62, f"timeline duration {ep.duration:.2f}s within 58-62s")
    order = [c["id"] for c in sorted(ep.cues, key=lambda c: c["t0"]) if c["type"] == "narr"]
    check(order == [l for l, _ in LINES], f"all {len(LINES)} script lines used once, in order")
    check(not ep.voice.estimated, "every line has real recorded audio")
    first = min(c["t0"] for c in ep.cues if c["type"] == "narr")
    check(first < 0.3, f"hook starts immediately (first word at {first:.2f}s)")
    sp = sorted((c["t0"], c["t0"] + c["dur"], c["id"]) for c in ep.cues if c["type"] == "narr")
    check(all(b[0] >= a[1] - 0.01 for a, b in zip(sp, sp[1:])), "no overlapping narration")
    gaps = max(b[0] - a[1] for a, b in zip(sp, sp[1:]))
    check(gaps < 2.0, f"no long silences between lines (max gap {gaps:.2f}s)")
    acc = [c["text"] for c in ep.cues if c["type"] == "accent"]
    check(len(acc) <= 5, f"on-screen text limited to accents: {acc}")
    # audio
    x, sr = sf.read(MIX)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", MIX, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    i_lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
    check(-15.5 <= i_lufs <= -13.0, f"integrated loudness {i_lufs} LUFS (YouTube target -14)")
    check(tp <= -1.0, f"true peak {tp} dBFS")
    v, _ = sf.read(os.path.join(BUILD, "stem_voice.wav"))
    b, _ = sf.read(os.path.join(BUILD, "stem_bg.wav"))
    w = int(0.5 * sr)
    margins = []
    for i in range(0, len(v) - w, w):
        rv = np.sqrt((v[i:i + w] ** 2).mean())
        rb = np.sqrt((b[i:i + w] ** 2).mean())
        if rv > 0.05:
            margins.append(20 * np.log10(rv / (rb + 1e-9)))
    check(min(margins) > 3 and np.median(margins) > 12,
          f"voice above music/SFX while speaking (min {min(margins):.1f} dB, median {np.median(margins):.1f} dB)")
    # SRT
    blocks = open(SRT, encoding="utf-8").read().strip().split("\n\n")
    times, texts = [], []
    for blk in blocks:
        ls = blk.split("\n")
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", ls[1])
        g = [int(q) for q in m.groups()]
        times.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000, g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000))
        texts.append(" ".join(ls[2:]))
    check(len(blocks) == len(LINES), f"SRT has {len(blocks)} cues")
    check(texts == [TEXT[l] for l, _ in LINES], "SRT text matches the narration script exactly")
    check(all(a < b for a, b in times) and all(p[1] <= q[0] for p, q in zip(times, times[1:])),
          "SRT cues ordered and non-overlapping")
    sync = max(abs(t[0] - (c[0] + 0.03)) for t, c in zip(times, sp))
    check(sync < 0.06, f"SRT cue starts match the voice clips in the final mix (max offset {sync * 1000:.0f} ms)")
    # video
    if os.path.exists(VIDEO):
        pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
                                        VIDEO], capture_output=True, text=True).stdout)
        vs = [s for s in pr["streams"] if s["codec_type"] == "video"][0]
        aus = [s for s in pr["streams"] if s["codec_type"] == "audio"]
        d = float(pr["format"]["duration"])
        check((vs["width"], vs["height"]) == (1080, 1920), f"video {vs['width']}x{vs['height']} (9:16)")
        check(vs["r_frame_rate"] == "30/1", f"frame rate {vs['r_frame_rate']}")
        check(aus and aus[0]["codec_name"] == "aac", "AAC audio track present")
        check(abs(d - ep.duration) < 0.15, f"file duration {d:.2f}s")
    else:
        check(False, "final video exists")
    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
