"""Frame renderer + video encode for the vertical short.

python -m episodes.japan_johatsu.render sheet            # contact sheet of every shot (QA)
python -m episodes.japan_johatsu.render video OUT.mp4    # silent 1080x1920 30 fps render (multiprocess)
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cairo
import numpy as np
from PIL import Image, ImageFilter

from cinecode.captions import render_text
from episodes.japan_johatsu.art import FPS, H, W, arr, eout, grain, lerp, prog, surface, vignette
from episodes.japan_johatsu.shots import END, SHOTS

CUES_PATH = "assets/audio/tts/johatsu/cues.json"
CAP_SIZE = 86
CAP_Y = 1330  # caption centre: lower-middle, clear of phone UI / cards
_cues = None


def cues():
    global _cues
    if _cues is None:
        if not os.path.exists(CUES_PATH):
            from episodes.japan_johatsu.timing import caption_groups
            json.dump(caption_groups(), open(CUES_PATH, "w"), indent=1, ensure_ascii=False)
        _cues = json.load(open(CUES_PATH))
    return _cues


def draw_shot(i, T):
    s0, s1, fn, _ = SHOTS[i]
    s, cx = surface()
    cx.save()
    fn(cx, T - s0, s1 - s0, T)
    cx.restore()
    return arr(s)[:, :, :3].astype(np.float32)  # BGR (cairo ARGB little-endian)


def scene_rgb(T):
    idx = max(i for i, sh in enumerate(SHOTS) if sh[0] <= T or i == 0)
    img = draw_shot(idx, T)
    xf = SHOTS[idx][3]
    if xf and idx > 0 and T - SHOTS[idx][0] < xf:
        k = (T - SHOTS[idx][0]) / xf
        k = k * k * (3 - 2 * k)
        prev = draw_shot(idx - 1, T)
        img = prev * (1 - k) + img * k
    return img


def post(img, fi):
    # bloom
    small = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    b = np.asarray(small).astype(np.float32)
    b = np.clip(b - 170, 0, None) * 1.6
    b = np.asarray(Image.fromarray(np.clip(b, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))
                   .resize((W, H), Image.BILINEAR)).astype(np.float32)
    img = img + b * 0.55
    img = img * vignette(0.55)
    img = img + grain(fi, 4.0)
    return img


def caption_layer(cx, T):
    for c in cues():
        if c["s"] - 0.02 <= T < c["e"]:
            k = eout(prog(T, c["s"] - 0.02, c["s"] + 0.1))
            out = 1 - prog(T, c["e"] - 0.06, c["e"])
            surf, w, h, pad = render_text(c["text"].upper() if False else c["text"], CAP_SIZE)
            sc = lerp(0.94, 1.0, k)
            cx.save()
            cx.translate(W / 2, CAP_Y)
            cx.scale(sc, sc)
            cx.set_source_surface(surf, -w / 2, -h / 2)
            cx.paint_with_alpha(k * out)
            cx.restore()


def frame(fi):
    T = fi / FPS
    img = post(scene_rgb(T), fi)
    s, cx = surface()
    a = arr(s)
    a[:, :, :3] = np.clip(img, 0, 255).astype(np.uint8)
    a[:, :, 3] = 255
    s.mark_dirty()
    caption_layer(cx, T)
    out = arr(s)
    return out[:, :, [2, 1, 0]].copy()  # BGR->RGB


def sheet(path, times=None):
    times = times or [round((a + b) / 2, 2) for a, b, _, _ in SHOTS]
    th = []
    for T in times:
        im = Image.fromarray(frame(int(T * FPS))).resize((270, 480))
        th.append(im)
    cols = 9
    rows = math.ceil(len(th) / cols)
    out = Image.new("RGB", (270 * cols, 480 * rows))
    for i, im in enumerate(th):
        out.paste(im, ((i % cols) * 270, (i // cols) * 480))
    out.save(path, quality=85)


def _chunk(args):
    a, b = args
    return [frame(i).tobytes() for i in range(a, b)]


def video(out, start=0.0, end=END, procs=4):
    n0, n1 = int(start * FPS), int(end * FPS)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    step = 15
    chunks = [(i, min(i + step, n1)) for i in range(n0, n1, step)]
    with Pool(procs) as pool:
        for k, frames in enumerate(pool.imap(_chunk, chunks)):
            for f in frames:
                p.stdin.write(f)
            if k % 10 == 0:
                print(f"{chunks[k][1] / FPS:6.1f}s / {end:.1f}", flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    if sys.argv[1] == "sheet":
        sheet(sys.argv[2], [float(x) for x in sys.argv[3:]] or None)
    elif sys.argv[1] == "frame":
        Image.fromarray(frame(int(float(sys.argv[3]) * FPS))).save(sys.argv[2])
    else:
        video(sys.argv[2], *(float(x) for x in sys.argv[3:]))
