"""Render Day 1 (remastered) video frames -> H.264 segments -> one silent video.

usage: python -m episodes.zombie_day_1.render [--still t1,t2,...] [--draft]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import cairo
import numpy as np

from . import shots
from . import world as Wd

FPS = 30
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "zombie_day_1")

_rng = np.random.default_rng(7)
GRAIN = [(_rng.normal(0, 1, (Wd.FH // 2, Wd.FW // 2)) * 5.5).astype(np.int16) for _ in range(6)]


def frame(t, scale=1.0):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(Wd.FW * scale), int(Wd.FH * scale))
    cx = cairo.Context(surf)
    if scale != 1.0:
        cx.scale(scale, scale)
    Wd.paint_rect(cx, Wd.CHARCOAL)
    cx.save()
    shots.shot_at(t)(cx, t)
    cx.restore()
    for txt, a, b, kind in shots.ACCENTS:
        Wd.accent(cx, txt, t, a, b, kind)
    surf.flush()
    arr = np.ndarray((surf.get_height(), surf.get_width(), 4), np.uint8, surf.get_data(),
                     strides=(surf.get_stride(), 4, 1))
    rgb = arr[:, :, 2::-1].astype(np.int16)
    # film grain (2x2 blocks), cycled
    g = GRAIN[int(t * FPS) % len(GRAIN)]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[: rgb.shape[0], : rgb.shape[1]]
    rgb += g[:, :, None]
    return np.clip(rgb, 0, 255).astype(np.uint8)


def render_segment(args):
    i, f0, f1, crf = args
    out = os.path.join(BUILD, f"seg_{i:03d}.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{Wd.FW}x{Wd.FH}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(f0, f1):
        p.stdin.write(frame(n / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return out


def main():
    os.makedirs(BUILD, exist_ok=True)
    args = sys.argv[1:]
    if args and args[0] == "--tail":
        render_tail()
        return
    if args and args[0] == "--still":
        from PIL import Image
        for ts in args[1].split(","):
            t = float(ts)
            Image.fromarray(frame(t)).resize((540, 960)).save(os.path.join(BUILD, f"still_{t:06.2f}.png"))
        return
    total = int(round(shots.DURATION * FPS))
    segs = 24
    per = (total + segs - 1) // segs
    jobs = [(i, i * per, min(total, (i + 1) * per), 17) for i in range(segs) if i * per < total]
    with Pool(4) as pool:
        outs = pool.map(render_segment, jobs)
    lst = os.path.join(BUILD, "segs.txt")
    with open(lst, "w") as f:
        for o in outs:
            f.write(f"file '{o}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    os.path.join(BUILD, "video_silent.mp4")], check=True)
    print("ok", os.path.join(BUILD, "video_silent.mp4"))



def render_tail(first_frame=1743, kept_segments=21):
    """Re-render only the frames from `first_frame` to the end (ending revision) and concat them
    after the untouched seg_000..seg_{kept_segments-1}."""
    total = int(round(shots.DURATION * FPS))
    n = total - first_frame
    parts = 4
    per = (n + parts - 1) // parts
    jobs = [(100 + i, first_frame + i * per, min(total, first_frame + (i + 1) * per), 17) for i in range(parts)]
    with Pool(4) as pool:
        tail = pool.map(render_segment, jobs)
    lst = os.path.join(BUILD, "segs_v2.txt")
    with open(lst, "w") as f:
        for i in range(kept_segments):
            f.write(f"file '{os.path.join(BUILD, f'seg_{i:03d}.mp4')}'\n")
        for o in tail:
            f.write(f"file '{o}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    os.path.join(BUILD, "video_silent.mp4")], check=True)
    print("ok tail", os.path.join(BUILD, "video_silent.mp4"))


if __name__ == "__main__":
    main()
