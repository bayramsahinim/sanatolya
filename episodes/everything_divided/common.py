"""Shared bits for the vertical Short: canvas, timing marks, header labels, captions."""
import json
import math
import os

import cairo

from cinecode import captions as CAP
from cinecode.core import clamp, ease_out, prog, rrect, smooth, src

W, H = 1080, 1920
FPS = 30
FONT = "Montserrat ExtraBold"
YELLOW = (1.0, 200 / 255, 87 / 255, 1)
WHITE = (1, 1, 1, 1)
INK = (15 / 255, 15 / 255, 18 / 255, 1)

HERE = os.path.dirname(os.path.abspath(__file__))
TIMING = json.load(open(os.path.join(HERE, "timing.json")))
TAIL = 1.35                                     # rewind-to-cake outro after the last word
DURATION = round(TIMING["duration_voice"] + TAIL, 2)

LINE = TIMING["lines"]                          # lid -> {t0, t1}
WORDS = TIMING["words"]
CAPS = TIMING["captions"]

CAPTION_Y = 1475
CAPTION_SIZE = 74


def L0(lid):
    return LINE[lid]["t0"]


def L1(lid):
    return LINE[lid]["t1"]


def word_t(lid, word, nth=0):
    """start time of the nth occurrence of `word` (case-insensitive) inside line lid."""
    k = 0
    for w in WORDS:
        if w["line"] == lid and w["w"].lower().strip("'") == word.lower():
            if k == nth:
                return w["t0"]
            k += 1
    raise KeyError((lid, word, nth))


def word_end(lid, word, nth=0):
    k = 0
    for w in WORDS:
        if w["line"] == lid and w["w"].lower() == word.lower():
            if k == nth:
                return w["t1"]
            k += 1
    raise KeyError((lid, word, nth))


# ------------------------------------------------------------------ text helpers
def text_w(cx, s, size):
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    return cx.text_extents(s).x_advance


def outlined(cx, s, x, y, size, fill=WHITE, outline=INK, ow=None, align="center", alpha=1.0, spacing=0.0,
             shadow=True):
    """Bold text with round-join contour + soft shadow. y = baseline."""
    cx.save()
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    if spacing:
        widths = [cx.text_extents(ch).x_advance + spacing for ch in s]
        tw = sum(widths) - spacing
    else:
        tw = cx.text_extents(s).x_advance
    x0 = x - tw / 2 if align == "center" else (x - tw if align == "right" else x)
    cx.new_path()
    if spacing:
        xx = x0
        for ch, wv in zip(s, widths):
            cx.move_to(xx, y)
            cx.text_path(ch)
            xx += wv
    else:
        cx.move_to(x0, y)
        cx.text_path(s)
    path = cx.copy_path()
    ow = size * 0.17 if ow is None else ow
    if shadow:
        cx.save()
        cx.translate(0, size * 0.07)
        cx.new_path()
        cx.append_path(path)
        cx.set_source_rgba(0, 0, 0, 0.35 * alpha)
        cx.set_line_width(ow * 1.3)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.stroke_preserve()
        cx.fill()
        cx.restore()
    if ow > 0:
        cx.new_path()
        cx.append_path(path)
        src(cx, outline, alpha)
        cx.set_line_width(ow)
        cx.set_line_join(cairo.LINE_JOIN_ROUND)
        cx.stroke()
    cx.new_path()
    cx.append_path(path)
    src(cx, fill, alpha)
    cx.fill()
    cx.restore()
    return tw


def fit_size(cx, s, size, maxw):
    w = text_w(cx, s, size)
    return size if w <= maxw else size * maxw / w


# ------------------------------------------------------------------ header labels
HEAD_Y = 205


def header(cx, t, items, y=HEAD_Y):
    """items: list of dicts {t0, t1, kick, main, sub, color}. Crossfades between consecutive items.
    main may be a callable(t) -> str (for counters)."""
    for it in items:
        a = it["t0"]
        b = it.get("t1", 1e9)
        if t < a - 0.01 or t > b + 0.25:
            continue
        ain = ease_out(prog(t, a, a + 0.22))
        aout = 1 - smooth(prog(t, b, b + 0.2))
        al = min(ain, aout)
        if al <= 0:
            continue
        sc = 0.9 + 0.1 * ain
        main = it["main"](t) if callable(it["main"]) else it["main"]
        col = it.get("color", YELLOW)
        cx.save()
        cx.translate(W / 2, y + 60)
        cx.scale(sc, sc)
        cx.translate(-W / 2, -(y + 60))
        if it.get("kick"):
            outlined(cx, it["kick"], W / 2, y, 30, fill=(0.82, 0.88, 1.0, 1), ow=7, alpha=al, spacing=4)
        size = fit_size(cx, main, it.get("size", 84), 960)
        if it.get("pop"):
            # small bump whenever the value changes is handled by caller; static pop on entry here
            pass
        outlined(cx, main, W / 2, y + 95, size, fill=col, ow=size * 0.17, alpha=al)
        if it.get("sub"):
            for k, ln in enumerate(it["sub"].split("\n")):
                ss = fit_size(cx, ln, 31, 960)
                outlined(cx, ln, W / 2, y + 150 + k * 40, ss, fill=(0.93, 0.95, 1.0, 1), ow=7, alpha=al * 0.95)
        cx.restore()


def pill(cx, x, y, s, size=34, fill=YELLOW, txt=INK, alpha=1.0, scale=1.0):
    """Small rounded label (for recap tags)."""
    if alpha <= 0:
        return
    cx.save()
    cx.translate(x, y)
    cx.scale(scale, scale)
    w = text_w(cx, s, size) + size * 0.9
    h = size * 1.45
    rrect(cx, -w / 2, -h / 2 + 3, w, h, h / 2)
    cx.set_source_rgba(0, 0, 0, 0.3 * alpha)
    cx.fill()
    rrect(cx, -w / 2, -h / 2, w, h, h / 2)
    src(cx, fill, alpha)
    cx.fill_preserve()
    src(cx, INK, alpha)
    cx.set_line_width(4)
    cx.stroke()
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    e = cx.text_extents(s)
    cx.move_to(-e.x_advance / 2, size * 0.36)
    src(cx, txt, alpha)
    cx.show_text(s)
    cx.restore()


# ------------------------------------------------------------------ narration captions
def caption_windows():
    """[(t0, t1, text)] - each group shows from its first word until the next group starts
    (or a short hold after its last word if there is a pause)."""
    out = []
    for i, g in enumerate(CAPS):
        t0 = g["t0"] - 0.04
        nxt = CAPS[i + 1]["t0"] - 0.04 if i + 1 < len(CAPS) else 1e9
        t1 = min(nxt, g["t1"] + 0.42)
        out.append((t0, t1, g["text"]))
    return out


CAP_WIN = caption_windows()


def draw_captions(cx, t, y=CAPTION_Y, alpha_mul=1.0):
    for t0, t1, txt in CAP_WIN:
        if t0 - 0.01 <= t <= t1:
            ain = ease_out(prog(t, t0, t0 + 0.1))
            aout = 1 - prog(t, t1 - 0.06, t1)
            al = min(ain, aout) * alpha_mul
            if al <= 0:
                continue
            surf, w, h, pad = CAP.render_text(txt, CAPTION_SIZE)
            sc = 0.94 + 0.06 * ain
            if w * sc > W - 90:
                sc *= (W - 90) / (w * sc)
            cx.save()
            cx.translate(W / 2, y)
            cx.scale(sc, sc)
            cx.set_source_surface(surf, -w / 2, -h / 2)
            cx.paint_with_alpha(al)
            cx.restore()


def caption_srt_rows():
    return [(t0 + 0.04, t1, txt) for t0, t1, txt in CAP_WIN]
