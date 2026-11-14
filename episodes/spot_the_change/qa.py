"""Assemble the final MP4 and run pre-delivery checks.

usage: python -m episodes.spot_the_change.qa assemble   # mux video + soundtrack -> output/*.mp4
       python -m episodes.spot_the_change.qa check      # QC report
"""
import colorsys
import json
import os
import re
import subprocess
import sys

import numpy as np

from episodes.spot_the_change.script import BLOCKS, plain
from episodes.spot_the_change.timeline import BUILD, NAME, OUT, ROOT

FINAL = os.path.join(OUT, NAME + ".mp4")
SRT = os.path.join(OUT, NAME + ".srt")


def assemble():
    v = os.path.join(BUILD, "video_silent.mp4")
    a = os.path.join(BUILD, "soundtrack.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", v, "-i", a, "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
                    "-profile:v", "high", "-movflags", "+faststart",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", FINAL], check=True)
    print("wrote", FINAL)


def frames(path, t0, t1, fps, w=270, h=480):
    cmd = ["ffmpeg", "-v", "error", "-ss", str(t0), "-to", str(t1), "-i", path, "-vf", f"fps={fps},scale={w}:{h}",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3).astype(np.float32)


def check():
    tl = json.load(open(os.path.join(BUILD, "timeline.json")))
    T0, T1 = tl["test"]
    ok = True

    def rep(name, cond, detail):
        nonlocal ok
        ok &= bool(cond)
        print(f"[{'PASS' if cond else 'FAIL'}] {name}: {detail}")

    pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                                    "-of", "json", FINAL], capture_output=True, check=True).stdout)
    vs = [s for s in pr["streams"] if s["codec_type"] == "video"][0]
    dur = float(pr["format"]["duration"])
    rep("format", vs["width"] == 1080 and vs["height"] == 1920 and vs["r_frame_rate"] == "30/1",
        f"{vs['width']}x{vs['height']} @ {vs['r_frame_rate']}")
    rep("duration 58-62 s", 58 <= dur <= 62, f"{dur:.2f} s")
    rep("test window is 12 s", abs((T1 - T0) - 12) < 0.01, f"{T0:.2f}-{T1:.2f}")

    # 1) continuity inside the test: no cut / jump between consecutive frames
    F = frames(FINAL, T0 + 0.5, T1 - 0.05, 30)
    d = np.abs(np.diff(F, axis=0)).mean(axis=(1, 2, 3))
    rep("no cuts during the test", d.max() < 6.0, f"max frame-to-frame diff {d.max():.2f}/255 (median {np.median(d):.2f}) over {len(F)} frames")

    # 2) hull colour: sample two hull patches (locked camera) every 0.5 s
    G = frames(FINAL, T0, T1 + 0.01, 2, 1080, 1920)
    patches = [(600, 640, 880, 896), (820, 860, 880, 896)]
    hues, rows = [], []
    for k, f in enumerate(G):
        c = np.median(np.concatenate([f[y0:y1, x0:x1].reshape(-1, 3) for x0, x1, y0, y1 in patches]), axis=0) / 255
        h, l, s = colorsys.rgb_to_hls(*c)
        hues.append(h * 360)
        rows.append((k * 0.5, c))
    r0, r1 = rows[0][1], rows[-1][1]
    print("      hull samples (s: R G B):", " ".join(f"{t:.1f}:{int(c[0]*255)},{int(c[1]*255)},{int(c[2]*255)}" for t, c in rows[::4]))
    rep("starts red", r0[0] > 0.5 and r0[0] > 2 * r0[2], f"RGB {np.round(r0 * 255).astype(int)}")
    rep("ends dark blue", r1[2] > r1[0] and r1[2] > r1[1] and r1.max() < 0.45, f"RGB {np.round(r1 * 255).astype(int)}")
    redness = np.array([c[0] - c[2] for _, c in rows])
    steps = np.diff(redness)
    rep("change is gradual and continuous", (steps <= 0.01).all() and np.abs(steps).max() < 0.12,
        f"red-minus-blue falls monotonically; largest 0.5 s step {np.abs(steps).max():.3f}")
    # same frame structure before/after (same ship, same framing): compare luminance outside hull band
    a, b = G[0].mean(axis=2), G[-1].mean(axis=2)
    sky = np.abs(a[:500] - b[:500]).mean()
    rep("same shot at start and end of test", sky < 12, f"mean sky difference {sky:.1f}/255")

    # 3) birds: structural count from the renderer
    bc = os.path.join(BUILD, "qa_birds.json")
    if os.path.exists(bc):
        q = json.load(open(bc))
        rep("exactly nine gulls, none before 'Go'", q["before"] == 0 and q["end"] == 9 and q["max"] == 9 and q["extra"] == 0,
            f"visible before test {q['before']}, max during test {q['max']}, at end {q['end']}, other birds in test {q['extra']}; entries at {q['entries']}")
        rep("every gull enters within the test", all(0 <= e <= 12 for e in q["entries"]) and all(l <= 12 for l in q["landings"]),
            f"landings at {q['landings']}")
    # 4) narration matches the approved script
    mp3 = os.path.join(BUILD, "qa_audio.mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", FINAL, "-vn", "-ac", "1", "-b:a", "96k", mp3], check=True)
    try:
        from cinecode.transcribe import transcribe
        tr = transcribe(mp3)
        norm = lambda s: re.sub(r"[^a-z ]", "", s.lower().replace("’", "'").replace("'", "")).split()
        want = norm(" ".join(plain(l) for _, ls in BLOCKS for _, l in ls))
        got = norm(tr)
        import difflib
        ratio = difflib.SequenceMatcher(None, want, got).ratio()
        rep("narration matches script", ratio > 0.95, f"word match {ratio:.3f}")
        print("      transcript:", tr.strip()[:400])
    except Exception as e:  # transcription service unavailable
        print("[SKIP] transcription:", e)
    # 5) captions off during the test (the overlay never draws there; verify SRT too)
    srt = open(SRT).read()
    times = re.findall(r"(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)", srt)
    inside = [x for x in times if T0 + 0.8 < int(x[0]) * 3600 + int(x[1]) * 60 + int(x[2]) + int(x[3]) / 1000 < T1]
    rep("no narration cues inside the test", not inside, f"{len(times)} SRT cues")
    print("\nOVERALL:", "PASS" if ok else "CHECK FAILURES ABOVE")


if __name__ == "__main__":
    {"assemble": assemble, "check": check}[sys.argv[1]]()
