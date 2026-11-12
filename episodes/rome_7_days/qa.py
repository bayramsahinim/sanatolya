"""Pre-delivery checks for the episode (duration, coverage, dead air, text, subtitles)."""
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

from episodes.rome_7_days.episode import BUILD, OUT, build_episode
from episodes.rome_7_days.script import DIALOGUE, NARRATION


def main(video=None):
    ep = build_episode()
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + msg)
        ok &= bool(cond)

    check(480 <= ep.duration <= 540, f"timeline duration {ep.duration:.1f}s ({ep.duration / 60:.2f} min) within 8-9 min")
    said = [c["id"] for c in ep.cues if c["type"] in ("narr", "dlg")]
    want = [lid for s in NARRATION.values() for lid, _ in s] + [d[0] for d in DIALOGUE]
    check(sorted(said) == sorted(want) and len(said) == len(set(said)),
          f"every script line used exactly once ({len(said)}/{len(want)})")
    order = [c["id"] for c in sorted(ep.cues, key=lambda c: c["t0"]) if c["type"] == "narr"]
    check(order == [lid for s in NARRATION.values() for lid, _ in s], "narration plays in script order")
    scenes = [sh.scene for sh in ep.shots]
    check(all(f"s{i}" in scenes for i in range(1, 11)), "all 10 scenes present")
    check(not ep.voice.estimated, f"all voice lines have real audio (estimated: {len(ep.voice.estimated)})")
    # overlapping speech
    sp = sorted([(c["t0"], c["t0"] + c["dur"], c["id"]) for c in ep.cues if c["type"] in ("narr", "dlg")])
    ov = [(a[2], b[2]) for a, b in zip(sp, sp[1:]) if b[0] < a[1] - 0.01]
    check(not ov, f"no overlapping voice lines {ov[:3]}")
    # longest stretch with no voice
    gaps = [(b[0] - a[1], a[2], b[2]) for a, b in zip(sp, sp[1:])]
    gaps.sort(reverse=True)
    print("     longest voice gaps:", ", ".join(f"{g:.1f}s after {a}" for g, a, b in gaps[:5]))
    check(gaps[0][0] < 6.0, "no voice gap longer than 6s (deliberate visual beats only)")
    acc = [c for c in ep.cues if c["type"] == "accent"]
    check(all(64 <= c["size"] <= 140 for c in acc), f"accent sizes within 64-140px ({len(acc)} accents)")
    check(all(len(c["text"].split("\n")) <= 2 for c in acc), "accents max two lines")
    bub = [c for c in ep.cues if c["type"] == "bubble"]
    check(all(c["size"] == 60 for c in bub), f"dialogue bubbles at 60px ({len(bub)})")
    per5 = len([c for c in acc if not re.match(r"DAY \d", c["text"])]) / (ep.duration / 300)
    print(f"     non-day-marker accents per 5 min: {per5:.1f}")
    # audio
    mix = os.path.join(BUILD, "mix.wav")
    if os.path.exists(mix):
        x, sr = sf.read(mix)
        if x.ndim > 1:
            x = x.mean(axis=1)
        check(abs(len(x) / sr - ep.duration) < 0.5, f"mix length {len(x) / sr:.1f}s matches timeline")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", mix, "-af", "ebur128=peak=true", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        i_lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
        tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1])
        check(-16.5 <= i_lufs <= -13.0, f"integrated loudness {i_lufs} LUFS")
        check(tp <= -1.0, f"true peak {tp} dBFS")
        # dead air: 2s windows that are near-silent
        win = int(sr * 2)
        rms = [np.sqrt((x[i:i + win] ** 2).mean()) for i in range(0, len(x) - win, win // 2)]
        silent = [i * 1.0 for i, v in enumerate(rms) if v < 10 ** (-50 / 20)]
        allowed = [(ep.starts[k], ep.starts[k] + ep.shots[k].dur) for k, sh in enumerate(ep.shots)
                   if type(sh).__name__ in ("S10Black",)]
        bad = [s for s in silent if not any(a - 1 <= s <= b + 1 for a, b in allowed)]
        check(not bad, f"no unintended dead air (silent 2s windows at {bad[:5]})")
    # srt
    srt = os.path.join(OUT, "I_Got_Stuck_in_Ancient_Rome_for_7_Days.en.srt")
    if os.path.exists(srt):
        blocks = open(srt).read().strip().split("\n\n")
        times = []
        for b in blocks:
            m = re.search(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", b)
            v = [int(g) for g in m.groups()]
            t0 = v[0] * 3600 + v[1] * 60 + v[2] + v[3] / 1000
            t1 = v[4] * 3600 + v[5] * 60 + v[6] + v[7] / 1000
            times.append((t0, t1))
        check(len(blocks) == len(want), f"SRT has {len(blocks)} cues")
        check(all(a < b for a, b in times) and all(p[1] <= q[0] for p, q in zip(times, times[1:])),
              "SRT cues ordered, non-overlapping")
    if video and os.path.exists(video):
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                                 capture_output=True, text=True).stdout)
        check(abs(d - ep.duration) < 0.6, f"video file duration {d:.1f}s ({d / 60:.2f} min)")
    print("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1] if len(sys.argv) > 1 else None) else 1)
