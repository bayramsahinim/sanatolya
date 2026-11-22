"""Frame renderer: shots + one-word captions + joke tags. Parallel encode.

usage: python -m episodes.troy_en.render stills [t1 t2 ...]   # PNGs + contact sheet in build/troy_en/stills
       python -m episodes.troy_en.render video                # build/troy_en/video_silent.mp4
"""
import math
import os
import re
import subprocess
import sys
from multiprocessing import Pool

import cairo

from cinecode.core import back_out, hexc, prog, src
from episodes.troy_en import gfx
from episodes.troy_en.gfx import FPS, H, W
from episodes.troy_en.script import HIGHLIGHT, LINES
from episodes.troy_en.shots import DUR, SHOTS, TIMING, shot_at

BUILD = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "build", "troy_en")
FONT = "Montserrat ExtraBold"
WHITE = (1, 1, 1, 1)
YELLOW = hexc("#FFD60A")
CAP_Y = int(H * 0.70)


# ------------------------------------------------------------------ caption words
def caption_words():
    """Recognised word timings, with the script's spelling (quotes stripped)."""
    toks = []
    for lid, txt in LINES:
        for w in txt.split():
            w = w.replace('"', "").replace("“", "").replace("”", "")
            if w.strip(".,!?:;…") or w == "...":
                toks.append(w.replace("...", "…"))
    toks = [t for t in toks if t not in ("…",)]
    words = TIMING["words"]
    out = []
    if len(toks) == len(words):
        for (s, e, _, _), t in zip(words, toks):
            out.append((s, e, t))
    else:  # fall back to recognised text
        print(f"caption token mismatch: script {len(toks)} vs audio {len(words)}")
        out = [(s, e, w) for s, e, w, _ in words]
    cues = []
    for i, (s, e, w) in enumerate(out):
        nxt = out[i + 1][0] if i + 1 < len(out) else e + 0.6
        end = nxt if nxt - e < 0.45 else e + 0.3
        cues.append((s, end, w))
    return cues


CUES = caption_words()


def draw_caption(cx, T):
    for s, e, w in CUES:
        if s <= T < e:
            break
    else:
        return
    k = back_out(prog(T, s, s + 0.09), 2.2)
    size = 118
    key = re.sub(r"[^a-zö']", "", w.lower())
    col = YELLOW if key in HIGHLIGHT else WHITE
    cx.save()
    cx.select_font_face(FONT)
    cx.set_font_size(size)
    ext = cx.text_extents(w)
    if ext.width > W - 120:
        size = size * (W - 120) / ext.width
        cx.set_font_size(size)
        ext = cx.text_extents(w)
    cx.translate(W / 2, CAP_Y)
    sc = 0.82 + 0.18 * k
    cx.scale(sc, sc)
    x = -ext.width / 2 - ext.x_bearing
    y = size * 0.36
    # soft shadow: stacked wide strokes
    for lw, a in ((34, 0.10), (24, 0.16), (16, 0.24)):
        cx.move_to(x + 4, y + 7)
        cx.text_path(w)
        src(cx, (0, 0, 0, a))
        cx.set_line_width(lw)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.stroke()
    cx.move_to(x, y)
    cx.text_path(w)
    src(cx, (0.05, 0.04, 0.04, 1))
    cx.set_line_width(9)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke_preserve()
    src(cx, col)
    cx.fill()
    cx.restore()


def draw_tag(cx, name, txt, k):
    """Yellow speaker label over a black box with white caps (joke caption)."""
    y = int(H * 0.235)
    cx.save()
    cx.select_font_face(FONT)
    cx.set_font_size(54)
    e = cx.text_extents(txt)
    bw, bh = e.width + 44, 82
    cx.translate(W / 2, y)
    cx.scale(0.9 + 0.1 * k, 0.9 + 0.1 * k)
    cx.rectangle(-bw / 2, 0, bw, bh)
    src(cx, (0, 0, 0, 0.86 * k))
    cx.fill()
    cx.move_to(-e.width / 2 - e.x_bearing, bh / 2 + 19)
    src(cx, (1, 1, 1, k))
    cx.show_text(txt)
    cx.set_font_size(44)
    e2 = cx.text_extents(name)
    cx.move_to(-bw / 2 + 4, -16)
    cx.text_path(name)
    src(cx, (0, 0, 0, 0.8 * k))
    cx.set_line_width(8)
    cx.stroke_preserve()
    src(cx, (*YELLOW[:3], k))
    cx.fill()
    cx.restore()


_TAG_START = {}


def render_frame(T):
    sh = shot_at(T)
    t = T - sh.t0
    s = sh.render(t)
    cx = cairo.Context(s)
    tags = sh.tags(t)
    if tags:
        name, txt = tags[0]
        key = (id(sh), txt)
        # find first active time by scanning back (deterministic, frame-independent)
        t_on = t
        while t_on - 1 / FPS >= 0 and sh.tags(t_on - 1 / FPS):
            t_on -= 1 / FPS
        draw_tag(cx, name, txt, back_out(prog(t - t_on, 0, 0.2)) if t - t_on < 0.2 else 1.0)
    draw_caption(cx, T)
    return s


# ------------------------------------------------------------------ outputs
def stills(times):
    d = os.path.join(BUILD, "stills")
    os.makedirs(d, exist_ok=True)
    paths = []
    for T in times:
        p = os.path.join(d, f"f_{T:06.2f}.png")
        render_frame(T).write_to_png(p)
        paths.append(p)
    return paths


def _chunk(args):
    i, f0, f1 = args
    out = os.path.join(BUILD, f"part_{i:02d}.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-vf", "noise=alls=3:allf=t", "-c:v", "libx264",
                          "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        s = render_frame(f / FPS)
        s.flush()
        p.stdin.write(bytes(s.get_data()))
    p.stdin.close()
    p.wait()
    return out


def video(workers=4):
    n = int(math.ceil(DUR * FPS))
    k = math.ceil(n / (workers * 3))
    jobs = [(i, f0, min(n, f0 + k)) for i, f0 in enumerate(range(0, n, k))]
    with Pool(workers) as pool:
        parts = pool.map(_chunk, jobs, chunksize=1)
    lst = os.path.join(BUILD, "parts.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    out = os.path.join(BUILD, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out],
                   check=True)
    for p in parts:
        os.remove(p)
    print("wrote", out, n, "frames")


if __name__ == "__main__":
    os.makedirs(BUILD, exist_ok=True)
    if sys.argv[1] == "stills":
        ts = [float(x) for x in sys.argv[2:]] or [round((s.t0 + s.t1) / 2, 2) for s in SHOTS]
        ps = stills(ts)
        cols = 7
        rows = math.ceil(len(ps) / cols)
        args = []
        for p in ps:
            args += ["-i", p]
        fc = "".join(f"[{i}]scale=270:-1[v{i}];" for i in range(len(ps)))
        blank = rows * cols - len(ps)
        fc += "".join(f"[v{i}]" for i in range(len(ps)))
        if blank:
            fc = fc.replace(f"[v{len(ps) - 1}]", f"[v{len(ps) - 1}]", 1)
            for j in range(blank):
                args += ["-f", "lavfi", "-i", "color=c=black:s=270x480"]
                fc += f"[{len(ps) + j}]"
        fc += f"xstack=inputs={rows * cols}:layout=" + "|".join(
            f"{(i % cols) * 270}_{(i // cols) * 480}" for i in range(rows * cols))
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + args + ["-filter_complex", fc, "-frames:v", "1",
                                                                  os.path.join(BUILD, "sheet.png")], check=True)
        print("sheet", os.path.join(BUILD, "sheet.png"))
    else:
        video()
