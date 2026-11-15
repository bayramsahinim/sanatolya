"""Frame compositor: picks the scene(s) for time t, crossfades, draws captions.

usage: python -m episodes.everything_divided.render stills t1 t2 ...
"""
import os
import sys

import cairo

from episodes.everything_divided import common as C

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "everything")


def scene_table():
    from episodes.everything_divided import scene_cake
    table = [(-1.0, scene_cake.T_OUT + 0.2, scene_cake.draw)]
    try:
        from episodes.everything_divided import scene_island
        table.append((scene_cake.T_OUT - 0.25, C.L0("star1") + 0.0, scene_island.draw))
    except ImportError:
        pass
    try:
        from episodes.everything_divided import scene_space
        table.append((C.L0("star1") - 0.01, C.DURATION + 1, scene_space.draw))
    except ImportError:
        pass
    return table


_TABLE = None


T_RW0 = C.L1("end4") + 0.15        # rewind starts after the last word
T_RW1 = C.DURATION - 0.2             # ...and lands on the very first frame (loop point)


def rewind_source_time(t):
    u = C.prog(t, T_RW0, T_RW1)
    return T_RW0 * (1 - (u * u * (3 - 2 * u)))


def frame(t):
    if t > T_RW0:
        return rewind_frame(t)
    return frame_core(t)


def rewind_frame(t):
    import math
    tt = rewind_source_time(t)
    s = frame_core(tt, captions=False)
    if t >= T_RW1:
        return s
    cx = cairo.Context(s)
    k = math.sin(math.pi * C.prog(t, T_RW0, T_RW1))
    # tape-rewind look: horizontal tracking bands + slight wash, and a rewind badge
    for i in range(3):
        y = (t * 1700 + i * 640) % (C.H + 200) - 100
        g = cairo.LinearGradient(0, y - 40, 0, y + 40)
        g.add_color_stop_rgba(0, 1, 1, 1, 0)
        g.add_color_stop_rgba(0.5, 1, 1, 1, 0.22 * k)
        g.add_color_stop_rgba(1, 1, 1, 1, 0)
        cx.rectangle(0, y - 40, C.W, 80)
        cx.set_source(g)
        cx.fill()
    cx.set_source_rgba(0.1, 0.12, 0.3, 0.18 * k)
    cx.paint()
    x0, y0 = C.W / 2, C.H / 2
    cx.save()
    cx.translate(x0, y0)
    for dx in (-38, 22):
        cx.move_to(dx + 30, -42)
        cx.line_to(dx - 30, 0)
        cx.line_to(dx + 30, 42)
        cx.close_path()
    cx.set_source_rgba(0, 0, 0, 0.35 * k)
    cx.set_line_width(14)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke_preserve()
    cx.set_source_rgba(1, 1, 1, 0.92 * k)
    cx.fill()
    cx.restore()
    return s


def frame_core(t, captions=True):
    global _TABLE
    if _TABLE is None:
        _TABLE = scene_table()
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, C.W, C.H)
    cx = cairo.Context(s)
    cx.set_source_rgb(0, 0, 0)
    cx.paint()
    active = [(a, b, f) for a, b, f in _TABLE if a <= t <= b]
    for i, (a, b, f) in enumerate(active):
        if i == 0:
            f(cx, t)
        else:
            # crossfade the later scene in over the overlap
            prev_end = active[i - 1][1]
            al = C.smooth(C.prog(t, a, prev_end)) if prev_end > a else 1.0
            cx.push_group()
            f(cx, t)
            cx.pop_group_to_source()
            cx.paint_with_alpha(al)
    if captions:
        C.draw_captions(cx, t)
    return s


def stills(times, prefix="still"):
    os.makedirs(os.path.join(BUILD, "stills"), exist_ok=True)
    out = []
    for t in times:
        p = os.path.join(BUILD, "stills", f"{prefix}_{t:06.2f}.png")
        frame(t).write_to_png(p)
        out.append(p)
    return out


def contact(paths, out, cols=4, scale=0.25):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = int(C.W * scale), int(C.H * scale)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), (40, 40, 40))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
    sheet.save(out)
    return out


if __name__ == "__main__":
    if sys.argv[1] == "stills":
        ts = [float(x) for x in sys.argv[2:]]
        ps = stills(ts)
        print(contact(ps, os.path.join(BUILD, "contact.png"), cols=min(4, len(ps))))
