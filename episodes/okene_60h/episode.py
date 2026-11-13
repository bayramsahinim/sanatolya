"""Assemble + render 'He Survived 60 Hours Underwater'.

    python -m episodes.okene_60h.voice              # narration stem + word timings
    python -m episodes.okene_60h.episode stills     # contact sheet of key frames
    python -m episodes.okene_60h.episode video      # render picture (parallel)
    python -m episodes.okene_60h.sound              # SFX, ambience, score, mix
    python -m episodes.okene_60h.episode final      # mux + SRT -> output/
"""
import math
import os
import subprocess
import sys
from multiprocessing import Process

import numpy as np

from cinecode.core import FPS, H, W
from . import shots_a as A
from . import shots_b as B
from .frame import Frame, Voice, caption_chunks, draw_caption
from . import look

BUILD = "build/okene"
OUT = "output"
NAME = "HE_SURVIVED_60_HOURS_UNDERWATER_FINAL"


def build_shots(V):
    w = V.w
    b = V.b
    cuts = [
        (A.S1a, 0.0, {}),
        (A.S1b, w("dead"), {}),
        (A.S1c, w("when") - 0.05, {"grab": w("grabbed")}),
        (A.S1d, w("his", after=w("grabbed")) + 0.06, {}),
        (A.S2, b("name") - 0.08, {}),
        (A.S3a, b("hours") - 0.05, {}),
        (A.S3b, w("nearly") - 0.02, {}),
        (A.S4, b("capsize") - 0.2, {}),
        (A.S5, w("capsized") - 0.05, {"roll": w("capsized") + 0.25}),
        (A.S6, b("pocket") - 0.1, {}),
        (A.S7a, w("Harrison", after=b("pocket")) - 0.05, {}),
        (A.S7b, w("trapped") - 0.1, {"breach": w("trapped") + 0.05}),
        (B.S8, b("reason") - 0.1, {"label_t": w("air", after=b("reason"))}),
        (B.S9a, b("science") - 0.1, {}),
        (B.S9b, w("trapped", after=b("science")) - 0.08, {}),
        (B.S9c, w("but", after=b("science")) - 0.08, {}),
        (B.S10, b("o2") - 0.08, {}),
        (B.S11, b("co2") - 0.08, {}),
        (B.S12, b("shrink") - 0.08, {}),
        (B.S13a, b("odds") - 0.1, {}),
        (B.S13b, w("made", after=b("odds")) - 0.05, {}),
        (B.S14a, b("wait") - 0.25, {"clank": w("until") - 0.1}),
        (B.S14b, w("until") + 0.08, {}),
        (B.S15, b("expect") - 0.1, {}),
        (B.S16, b("found") - 0.08, {}),
        (B.S17, w("they", after=b("found")) - 0.06, {"grab": w("survivor")}),
        (B.S18a, b("final") - 0.1, {}),
        (B.S18b, w("underwater", after=b("final")) - 0.05, {}),
    ]
    shots = []
    for i, (cls, t0, kw) in enumerate(cuts):
        t1 = cuts[i + 1][1] if i + 1 < len(cuts) else V.duration
        shots.append(cls(t0, t1, **kw))
    return shots


class Episode:
    def __init__(self):
        self.V = Voice()
        self.shots = build_shots(self.V)
        self.duration = self.V.duration
        self.nframes = int(round(self.duration * FPS))
        self.caps = caption_chunks(self.V.words)

    def shot_at(self, T):
        for s in reversed(self.shots):
            if T >= s.t0:
                return s
        return self.shots[0]

    def frame(self, i, captions=True):
        T = i / FPS
        s = self.shot_at(T)
        F = Frame(i, T, T - s.t0)
        s.render(F)
        img = F.compose()
        if captions:
            cur = None   # exactly one caption on screen at a time
            for c in self.caps:
                if c["t0"] <= T < c["t1"] + 0.05:
                    cur = c
            if cur is not None:
                img = draw_caption(img, cur, T)
        return img


def _worker(k, n, a, b, path):
    ep = Episode()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(a, b):
        p.stdin.write(look.rgb_to_bytes(ep.frame(i)))
        if k == 0 and (i - a) % 60 == 0:
            print(f"  worker0 {i - a}/{b - a}", flush=True)
    p.stdin.close()
    p.wait()


def video(nproc=4):
    ep = Episode()
    os.makedirs(BUILD, exist_ok=True)
    n = ep.nframes
    bounds = [round(n * k / nproc) for k in range(nproc + 1)]
    procs = []
    parts = []
    for k in range(nproc):
        path = f"{BUILD}/part{k}.mp4"
        parts.append(path)
        pr = Process(target=_worker, args=(k, nproc, bounds[k], bounds[k + 1], path))
        pr.start()
        procs.append(pr)
    for pr in procs:
        pr.join()
        if pr.exitcode:
            raise SystemExit("worker failed")
    with open(f"{BUILD}/parts.txt", "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{BUILD}/parts.txt",
                    "-c", "copy", f"{BUILD}/picture.mp4"], check=True)
    print("picture:", f"{BUILD}/picture.mp4", n, "frames")


def stills(times=None, out=f"{BUILD}/stills.jpg", cols=6, scale=0.25):
    from PIL import Image
    ep = Episode()
    if times is None:
        times = [s.t0 + min(0.6, s.dur * 0.5) for s in ep.shots]
    ims = []
    for T in times:
        img = ep.frame(int(T * FPS))
        ims.append(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((int(W * scale), int(H * scale))))
    rows = math.ceil(len(ims) / cols)
    sheet = Image.new("RGB", (int(W * scale) * cols, int(H * scale) * rows))
    for k, im in enumerate(ims):
        sheet.paste(im, ((k % cols) * int(W * scale), (k // cols) * int(H * scale)))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out, quality=88)
    return out


def still(T, out):
    from PIL import Image
    ep = Episode()
    img = ep.frame(int(T * FPS))
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(out)


# ------------------------------------------------------------------ SRT
def _ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def srt(path):
    V = Voice()
    cues = []
    cur = []
    for w in V.words:
        cur.append(w)
        txt = " ".join(x["text"] for x in cur)
        end_sentence = w["text"].endswith((".", "?", "!", "...", ":"))
        nxt = V.words[V.words.index(w) + 1] if w is not V.words[-1] else None
        long_pause = nxt is not None and nxt["t0"] - w["t1"] > 0.5
        if end_sentence or len(txt) > 34 or long_pause or (w["text"].endswith(",") and len(txt) > 18):
            cues.append(cur)
            cur = []
    if cur:
        cues.append(cur)
    lines = []
    for k, c in enumerate(cues):
        t0 = c[0]["t0"]
        t1 = c[-1]["t1"] + 0.25
        if k + 1 < len(cues):
            t1 = min(t1, cues[k + 1][0]["t0"] - 0.02)
        lines.append(f"{k + 1}\n{_ts(t0)} --> {_ts(t1)}\n{' '.join(x['text'] for x in c)}\n")
    open(path, "w").write("\n".join(lines))
    return len(cues)


def final():
    os.makedirs(OUT, exist_ok=True)
    mp4 = f"{OUT}/{NAME}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{BUILD}/picture.mp4", "-i", f"{BUILD}/mix.wav",
                    "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                    "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", mp4], check=True)
    n = srt(f"{OUT}/{NAME}.srt")
    print(mp4, f"SRT cues: {n}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stills"
    if cmd == "stills":
        print(stills())
    elif cmd == "still":
        still(float(sys.argv[2]), sys.argv[3])
    elif cmd == "video":
        video(int(sys.argv[2]) if len(sys.argv) > 2 else 4)
    elif cmd == "final":
        final()
    elif cmd == "srt":
        print(srt(f"{OUT}/{NAME}.srt"))
