"""Build, preview, render and mix "The Number Above Their Head" (vertical, 1080x1920, 30 fps).

usage:
  python -m episodes.numbers_above.episode plan
  python -m episodes.numbers_above.episode still SHOTNAME t [out.png]   # t: seconds into shot
  python -m episodes.numbers_above.episode sheet out.png               # contact sheet, 1 frame/shot
  python -m episodes.numbers_above.episode audio
  python -m episodes.numbers_above.episode video [--draft]
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np

from .frame import draw_subtitle, srt, subtitle_cues
from . import look
from .look import FPS, H, W, Frame, make_grain, out_size

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "numbers")
OUT = os.path.join(ROOT, "output")
NAME = "The_Number_Above_Their_Head"
TARGET = 176.0     # seconds of film before the end card
END_CARD = 2.6


def shot_classes():
    from .shots_a import SHOTS_A
    try:
        from .shots_b import SHOTS_B
    except ImportError:
        SHOTS_B = []
    return SHOTS_A + SHOTS_B


def build(scale=None):
    shots = [cls() for cls in shot_classes()]
    if scale is None:
        # find a gap scale so the film lands on TARGET (only silences are scaled)
        lo, hi = 0.3, 2.5
        for _ in range(30):
            mid = (lo + hi) / 2
            t = 0
            for s in shots:
                t = s.build(t, mid)
            if t > TARGET:
                hi = mid
            else:
                lo = mid
        scale = lo
    t = 0
    for s in shots:
        t = s.build(t, scale)
    return shots, t, scale


SHOTS, FILM_END, SCALE = None, None, None
CUES = None
GRAIN = None


def _init():
    global SHOTS, FILM_END, SCALE, CUES, GRAIN
    if SHOTS is None:
        SHOTS, FILM_END, SCALE = build()
        CUES = subtitle_cues(SHOTS)
        GRAIN = make_grain()


def total():
    _init()
    return FILM_END + END_CARD


def _view(name):
    if not look.land():
        return None
    from .landscape import VIEWS
    return VIEWS[name]


def render_frame(gt, subs=True):
    _init()
    if gt >= FILM_END:
        f = Frame(_view("END"))
        from .shots_b import end_card
        end_card(f, gt - FILM_END, END_CARD)
        bright = 1.0
    else:
        sh = next(s for s in SHOTS if s.t0 <= gt < s.t0 + s.dur) if gt < FILM_END else SHOTS[-1]
        f = Frame(_view(type(sh).__name__))
        lt = gt - sh.t0
        f.save()
        sh.draw(f, lt)
        f.restore()
        bright = min(1.0, (lt / sh.fade_in) if sh.fade_in else 1.0, ((sh.dur - lt) / sh.fade_out) if sh.fade_out else 1.0)
        bright = max(0.0, bright) ** 1.5
    if subs:
        f.cx.save()
        f.cx.identity_matrix()   # subtitles live in output space
        draw_subtitle(f.cx, gt, CUES)
        f.cx.restore()
    grain = GRAIN[int(gt * FPS) % len(GRAIN)]
    rgb = f.to_rgb(grain=grain)
    if bright < 1.0:
        rgb = (rgb.astype(np.float32) * bright).astype(np.uint8)
    return rgb


def _render_range(args):
    i, f0, f1, path, crf, land = args
    if land:
        look.MODE["land"] = True
    ow, oh = out_size()
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{ow}x{oh}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(f0, f1):
        p.stdin.write(render_frame(fi / FPS).tobytes())
        if i == 0 and (fi - f0) % 300 == 0:
            print(f"  worker0 {fi - f0}/{f1 - f0}", flush=True)
    p.stdin.close()
    p.wait()
    return path


def video(draft=False, workers=4):
    _init()
    land = look.land()
    build = os.path.join(BUILD, "land") if land else BUILD
    os.makedirs(build, exist_ok=True)
    n = int(math.ceil(total() * FPS))
    seg = 8
    bounds = [round(n * k / seg) for k in range(seg + 1)]
    crf = 26 if draft else 21
    jobs = [(k, bounds[k], bounds[k + 1], os.path.join(build, f"seg_{k:02d}.mp4"), crf, land) for k in range(seg)]
    with Pool(workers) as pool:
        parts = pool.map(_render_range, jobs)
    lst = os.path.join(build, "segs.txt")
    with open(lst, "w") as fh:
        for p in parts:
            fh.write(f"file '{p}'\n")
    silent = os.path.join(build, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent], check=True)
    os.makedirs(OUT, exist_ok=True)
    final = os.path.join(OUT, NAME + ("_16x9" if land else "") + ("_draft" if draft else "") + ".mp4")
    mix = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", silent, "-i", mix, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", final], check=True)
    print("wrote", final)


def plan():
    _init()
    print(f"gap scale {SCALE:.3f}  film {FILM_END:.2f}s  total {total():.2f}s")
    for s in SHOTS:
        print(f"{s.t0:7.2f} {s.dur:6.2f}  {type(s).__name__:14s} {' '.join(s.lines)}")


def still(name, t, out):
    _init()
    sh = next(s for s in SHOTS if type(s).__name__ == name)
    from PIL import Image
    Image.fromarray(render_frame(sh.t0 + float(t))).save(out)


def sheet(out, frac=0.7, cols=6):
    _init()
    from PIL import Image
    tw, th_ = (480, 270) if look.land() else (270, 480)
    if look.land():
        cols = 5
    thumbs = []
    for s in SHOTS:
        rgb = render_frame(s.t0 + s.dur * frac)
        thumbs.append(Image.fromarray(rgb).resize((tw, th_)))
    rgb = render_frame(FILM_END + END_CARD * 0.5)
    thumbs.append(Image.fromarray(rgb).resize((tw, th_)))
    rows = (len(thumbs) + cols - 1) // cols
    im = Image.new("RGB", (cols * tw, rows * th_))
    for i, th in enumerate(thumbs):
        im.paste(th, ((i % cols) * tw, (i // cols) * th_))
    im.save(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--land" in a:          # 16:9 1920x1080 render of the same film
        look.MODE["land"] = True
        a.remove("--land")
    if a[0] == "plan":
        plan()
    elif a[0] == "still":
        still(a[1], a[2], a[3] if len(a) > 3 else os.path.join(BUILD, f"{a[1]}.png"))
    elif a[0] == "sheet":
        sheet(a[1], float(a[2]) if len(a) > 2 else 0.7)
    elif a[0] == "audio":
        from .mixdown import mixdown
        _init()
        mixdown(SHOTS, FILM_END, total(), CUES)
    elif a[0] == "video":
        video(draft="--draft" in a)
