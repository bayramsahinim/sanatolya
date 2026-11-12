"""On-screen text, implemented exactly to the channel caption spec.

* Montserrat ExtraBold only. White #FFFFFF, highlight #FFC857 for [bracketed] words.
* Contour #0F0F12 at ~8.5% of font size (round joins) + soft dark shadow, ~5.5px down.
* Max two lines, centred, line height 1.18.
* Motion: in = 0.18s fade + scale 94%->100% (+8px upward settle for accents);
          out = 0.22s fade. Nothing else.
* Dialogue = speech-bubble plate #141419 @74%, radius 26, padding 30/18, tail to the
  speaker's head; placed above the head first, else right, else left; >=60px from edges;
  never over a face.
"""
import math
import re

import cairo
import numpy as np
from PIL import Image, ImageFilter

from .core import H, W, ease_out, prog, rrect, src

FONT = "Montserrat ExtraBold"
WHITE = (1, 1, 1, 1)
YELLOW = (1.0, 200 / 255, 87 / 255, 1)
CONTOUR = (15 / 255, 15 / 255, 18 / 255, 1)
PLATE = (20 / 255, 20 / 255, 25 / 255, 0.74)
LINE_H = 1.18
IN_T = 0.18
OUT_T = 0.22
EDGE = 60

_cache = {}


def _runs(line):
    """'Honey! Dinner's [ready!]' -> [(text, highlighted)]"""
    out = []
    for part in re.split(r"(\[[^\]]*\])", line):
        if not part:
            continue
        if part.startswith("["):
            out.append((part[1:-1], True))
        else:
            out.append((part, False))
    return out


def _measure(cx, s):
    return cx.text_extents(s).x_advance


def render_text(txt, size):
    """Return (cairo.ImageSurface, w, h, anchor_y) for caption text (\\n = line break)."""
    key = (txt, size)
    if key in _cache:
        return _cache[key]
    lines = txt.split("\n")[:2]
    tmp = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
    tc = cairo.Context(tmp)
    tc.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    tc.set_font_size(size)
    fe = tc.font_extents()
    widths = [sum(_measure(tc, r[0]) for r in _runs(l)) for l in lines]
    lh = size * LINE_H
    pad = int(size * 0.5) + 12
    w = int(max(widths) + 2 * pad)
    h = int(lh * len(lines) + 2 * pad)
    contour_w = size * 0.085 * 2  # stroke is centred: visible contour ~8.5% of size
    # text layer
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    cx = cairo.Context(surf)
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    # vertical metrics: centre cap height within each line box
    cap = tc.text_extents("H").height
    paths = []
    for i, (l, lw) in enumerate(zip(lines, widths)):
        x = (w - lw) / 2
        y = pad + i * lh + (lh + cap) / 2
        for seg, hi in _runs(l):
            paths.append((x, y, seg, hi))
            x += _measure(cx, seg)

    def text_path(c):
        c.new_path()
        for x, y, seg, hi in paths:
            c.move_to(x, y)
            c.text_path(seg)

    # shadow (blurred) on separate layer
    sh = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    sc = cairo.Context(sh)
    sc.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    sc.set_font_size(size)
    text_path(sc)
    sc.set_line_width(contour_w * 1.6)
    sc.set_line_join(cairo.LINE_JOIN_ROUND)
    sc.set_source_rgba(0, 0, 0, 1)
    sc.stroke_preserve()
    sc.fill()
    sh.flush()
    arr = np.ndarray((h, w, 4), np.uint8, sh.get_data(), strides=(sh.get_stride(), 4, 1))
    alpha = Image.fromarray(arr[:, :, 3].copy())
    alpha = alpha.filter(ImageFilter.GaussianBlur(radius=max(3, size * 0.09)))
    a = (np.asarray(alpha).astype(np.float32) * 0.42).astype(np.uint8)
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    oarr = np.ndarray((h, w, 4), np.uint8, out.get_data(), strides=(out.get_stride(), 4, 1))
    # shadow offset ~5.5 px downward (scaled with size for big accents)
    dy = int(round(5.5 * max(1.0, size / 64) ** 0.5))
    oarr[:, :, :] = 0
    oarr[dy:, :, 3] = a[: h - dy, :]
    out.mark_dirty()
    oc = cairo.Context(out)
    oc.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    oc.set_font_size(size)
    # contour
    text_path(oc)
    oc.set_source_rgba(*CONTOUR)
    oc.set_line_width(contour_w)
    oc.set_line_join(cairo.LINE_JOIN_ROUND)
    oc.set_line_cap(cairo.LINE_CAP_ROUND)
    oc.stroke()
    # fills
    for x, y, seg, hi in paths:
        oc.move_to(x, y)
        oc.text_path(seg)
        oc.set_source_rgba(*(YELLOW if hi else WHITE))
        oc.fill()
    res = (out, w, h, pad)
    _cache[key] = res
    return res


def _env(t, t0, t1):
    """alpha, scale, rise for a caption visible [t0,t1]."""
    if t < t0 or t > t1 + OUT_T:
        return 0.0, 1.0, 0.0
    a_in = ease_out(prog(t, t0, t0 + IN_T))
    a_out = 1 - prog(t, t1, t1 + OUT_T)
    alpha = min(a_in, a_out)
    scale = 0.94 + 0.06 * a_in
    rise = (1 - a_in) * 8
    return alpha, scale, rise


def draw_accent(cx, t, cue):
    alpha, scale, rise = _env(t, cue["t0"], cue["t1"])
    if alpha <= 0:
        return
    surf, w, h, pad = render_text(cue["text"], cue.get("size", 96))
    x, y = cue.get("pos", (W / 2, 220))
    cx.save()
    cx.translate(x, y + rise)
    cx.scale(scale, scale)
    cx.set_source_surface(surf, -w / 2, -h / 2)
    cx.paint_with_alpha(alpha)
    cx.restore()


def _overlaps(rect, circles, margin=20):
    x0, y0, x1, y1 = rect
    for (cx_, cy_, r) in circles:
        nx = min(max(cx_, x0), x1)
        ny = min(max(cy_, y0), y1)
        if (nx - cx_) ** 2 + (ny - cy_) ** 2 < (r + margin) ** 2:
            return True
    return False


def place_bubble(head, bw, bh, faces, prefer=None):
    """head = (x, y, r) in screen px. Returns (mode, rect)."""
    hx, hy, r = head
    tail = 26
    gap = 18
    cands = []
    above = (hx - bw / 2, hy - r - gap - tail - bh, hx + bw / 2, hy - r - gap - tail)
    right = (hx + r + gap + tail, hy - r * 0.6 - bh / 2, hx + r + gap + tail + bw, hy - r * 0.6 + bh / 2)
    left = (hx - r - gap - tail - bw, hy - r * 0.6 - bh / 2, hx - r - gap - tail, hy - r * 0.6 + bh / 2)
    order = [("above", above), ("right", right), ("left", left)]
    if prefer:
        order.sort(key=lambda m: m[0] != prefer)
    for mode, rc in order:
        x0, y0, x1, y1 = rc
        # allow horizontal shift for 'above' to respect edges
        if mode == "above":
            shift = 0
            if x0 < EDGE:
                shift = EDGE - x0
            if x1 + shift > W - EDGE:
                shift = (W - EDGE) - x1
            x0, x1 = x0 + shift, x1 + shift
        if y0 < EDGE or y1 > H - EDGE or x0 < EDGE or x1 > W - EDGE:
            continue
        if _overlaps((x0, y0, x1, y1), faces):
            continue
        return mode, (x0, y0, x1, y1)
    # fallback: above, clamped
    x0, y0, x1, y1 = above
    shift = max(EDGE - x0, min(0, (W - EDGE) - x1))
    dy = max(0, EDGE - y0)
    return "above", (x0 + shift, y0 + dy, x1 + shift, y1 + dy)


def draw_bubble(cx, t, cue, head, faces, state):
    """state: dict persisted per cue (placement mode chosen once, then follows head)."""
    alpha, scale, rise = _env(t, cue["t0"], cue["t1"])
    if alpha <= 0 or head is None:
        return
    size = cue.get("size", 60)
    txt = cue["text"]
    # two-line captions: second line appears when its first word is spoken
    if "\n" in txt and cue.get("t_line2") and t < cue["t_line2"]:
        shown = txt.split("\n")[0]
    else:
        shown = txt
    full, fw, fh, fpad = render_text(txt, size)
    surf, w, h, pad = render_text(shown, size)
    pw = fw - 2 * fpad + 2 * 30
    ph = (fh - 2 * fpad) + 2 * 18
    if "mode" not in state:
        others = [f for f in faces if abs(f[0] - head[0]) > 1 or abs(f[1] - head[1]) > 1]
        mode, rect = place_bubble(head, pw, ph, others + [head], cue.get("prefer"))
        state["mode"] = mode
        state["off"] = (rect[0] - head[0], rect[1] - head[1])
    ox, oy = state["off"]
    x0 = head[0] + ox
    y0 = head[1] + oy
    x0 = min(max(x0, EDGE), W - EDGE - pw)
    y0 = min(max(y0, EDGE), H - EDGE - ph)
    ccx, ccy = x0 + pw / 2, y0 + ph / 2
    cx.save()
    cx.translate(ccx, ccy + rise * 0.0)
    cx.scale(scale, scale)
    cx.translate(-ccx, -ccy)
    cx.push_group()
    rrect(cx, x0, y0, pw, ph, 26)
    # tail toward head
    hx, hy, r = head
    mode = state["mode"]
    if mode == "above":
        bx = min(max(hx, x0 + 40), x0 + pw - 40)
        cx.move_to(bx - 18, y0 + ph - 1)
        cx.line_to(hx + (bx - hx) * 0.35, hy - r - 10)
        cx.line_to(bx + 18, y0 + ph - 1)
    elif mode == "right":
        by = min(max(hy - r * 0.3, y0 + 30), y0 + ph - 30)
        cx.move_to(x0 + 1, by - 16)
        cx.line_to(hx + r + 8, hy - r * 0.3)
        cx.line_to(x0 + 1, by + 16)
    else:
        by = min(max(hy - r * 0.3, y0 + 30), y0 + ph - 30)
        cx.move_to(x0 + pw - 1, by - 16)
        cx.line_to(hx - r - 8, hy - r * 0.3)
        cx.line_to(x0 + pw - 1, by + 16)
    cx.close_path()
    src(cx, (PLATE[0], PLATE[1], PLATE[2], 1))
    cx.fill()
    cx.pop_group_to_source()
    cx.paint_with_alpha(PLATE[3] * alpha)
    # text: anchor first line at top so line 2 appearing doesn't shift line 1
    cx.set_source_surface(surf, ccx - w / 2, y0 + 18 - pad)
    cx.paint_with_alpha(alpha)
    cx.restore()
