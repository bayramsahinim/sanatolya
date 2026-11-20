"""Typography: header block (label / value / sub), word-timed captions, pills."""
import json
import os
import re

import cairo

from cinecode.core import back_out, clamp, hexc, prog, rrect, smooth, src
from cinecode.align import syllables

FONT = "Montserrat ExtraBold"
W, H = 1080, 1920
YELLOW = hexc("#FFD60A")
WHITE = hexc("#FFFFFF")
INKC = hexc("#14141A")
CYAN = hexc("#7DD3F5")
CORAL = hexc("#FF6B6B")
PINK = hexc("#FF6FAE")
BLUE = hexc("#5AA6FF")


def font(cx, size):
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)


def text_w(cx, s, size, spacing=0.0):
    font(cx, size)
    return cx.text_extents(s).x_advance + spacing * max(0, len(s) - 1)


def draw_text(cx, s, x, y, size, c, align="center", spacing=0.0, alpha=1.0, shadow=0.0):
    font(cx, size)
    w = text_w(cx, s, size, spacing)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if shadow > 0:
        _show(cx, s, x, y + size * 0.06, spacing, (0, 0, 0, 0.55 * alpha * shadow))
    _show(cx, s, x, y, spacing, (*c[:3], c[3] * alpha if len(c) > 3 else alpha))
    return w


def _show(cx, s, x, y, spacing, c):
    src(cx, c)
    if spacing == 0:
        cx.move_to(x, y)
        cx.show_text(s)
        return
    for ch in s:
        cx.move_to(x, y)
        cx.show_text(ch)
        x += cx.text_extents(ch).x_advance + spacing


def pill(cx, s, x, y, size, bg, fg=INKC, alpha=1.0, pad=None, scale=1.0):
    """Centered rounded label at (x, y) = centre."""
    if alpha <= 0.003 or scale <= 0.01:
        return
    size *= scale
    pad = pad if pad is not None else size * 0.42
    w = text_w(cx, s, size) + pad * 2
    h = size * 1.35
    rrect(cx, x - w / 2, y - h / 2, w, h, h * 0.28)
    src(cx, bg, alpha)
    cx.fill()
    font(cx, size)
    ext = cx.text_extents(s)
    draw_text(cx, s, x, y + (ext.height / 2) - (ext.height + ext.y_bearing) / 2 + size * 0.02, size, fg, alpha=alpha)


# ------------------------------------------------------------------ header
HEADER_LABEL_Y = 214
HEADER_VALUE_Y = 306
HEADER_SUB_Y = 354


def header(cx, t, entries, alpha=1.0):
    """entries: [(t0, label, value, sub, color)] sorted; value may be callable(t)->str."""
    idx = -1
    for i, e in enumerate(entries):
        if t >= e[0]:
            idx = i
    if idx < 0:
        return
    cur = entries[idx]
    prev = entries[idx - 1] if idx > 0 else None
    a_in = smooth(prog(t, cur[0] + 0.08, cur[0] + 0.32))
    a_out = 1 - smooth(prog(t, cur[0], cur[0] + 0.1))
    # label
    if prev is not None and prev[1] != cur[1] and a_out > 0:
        draw_text(cx, prev[1], W / 2, HEADER_LABEL_Y, 27, WHITE, spacing=4.5, alpha=0.82 * alpha * a_out)
    la = a_in if (prev is None or prev[1] != cur[1]) else 1.0
    draw_text(cx, cur[1], W / 2, HEADER_LABEL_Y, 27, WHITE, spacing=4.5, alpha=0.82 * alpha * la)
    # value + sub
    for ent, a, new in ((prev, a_out, False), (cur, a_in, True)):
        if ent is None or a <= 0.003:
            continue
        if not new and prev is not None and callable(prev[2]) and prev[2] is cur[2]:
            continue
        v = ent[2](t) if callable(ent[2]) else ent[2]
        same_v = (prev is not None and not callable(cur[2]) and prev[2] == cur[2])
        k = prog(t, cur[0] + 0.08, cur[0] + 0.4)
        sc = 0.86 + 0.14 * back_out(k) if (new and not same_v) else 1.0
        av = alpha * (1.0 if same_v else a)
        if same_v and not new:
            continue
        cx.save()
        cx.translate(W / 2, HEADER_VALUE_Y - 26)
        cx.scale(sc, sc)
        size = 74
        while text_w(cx, v, size) > 1000 and size > 40:
            size -= 2
        draw_text(cx, v, 0, 26, size, ent[4], alpha=av, shadow=0.8)
        cx.restore()
        if ent[3]:
            same_s = prev is not None and prev[3] == cur[3]
            if same_s and not new:
                continue
            draw_text(cx, ent[3], W / 2, HEADER_SUB_Y, 27, CYAN, alpha=0.95 * alpha * (1.0 if same_s else a))


# ------------------------------------------------------------------ captions
def _weight(word):
    w = word.strip("*,.!?:;\"'")
    if re.search(r"\d", w):
        return 1.2 * len(re.findall(r"\d+", w)) + 0.6 * len(re.sub(r"\D", "", w)) / 3
    return max(1.0, syllables(w) - 1.5)


class Captions:
    def __init__(self, timing, captions, lines_order):
        self.chunks = []  # (t_show, t_hide, [(word, highlighted, t_word)])
        for lid in lines_order:
            info = timing[lid]
            s, e = info["start"], info["end"]
            pauses = [(s + a, s + b) for a, b in info["pauses"]]
            words = []
            for ci, chunk in enumerate(captions[lid].split("|")):
                hl = False
                for tok in chunk.split():
                    starts_hl = tok.startswith("*")
                    if starts_hl:
                        hl = True
                    clean = tok.replace("*", "")
                    words.append((ci, clean, hl))
                    if tok.endswith("*") or tok.endswith("*,") or tok.endswith("*.") or re.search(r"\*[,.!?:]*$", tok):
                        hl = False
            # speech intervals
            segs, cur = [], s + 0.04
            for a, b in pauses:
                segs.append((cur, a))
                cur = b
            segs.append((cur, e - 0.08))
            total = sum(b - a for a, b in segs)
            wts = [_weight(w) for _, w, _ in words]
            ws = sum(wts)
            times, acc = [], 0.0
            for wt in wts:
                times.append(self._at(segs, acc / ws * total))
                acc += wt
            n_chunks = words[-1][0] + 1
            for ci in range(n_chunks):
                idx = [k for k, w in enumerate(words) if w[0] == ci]
                self.chunks.append([times[idx[0]] - 0.06, None, [(words[k][1], words[k][2], times[k]) for k in idx], e])
        for i, c in enumerate(self.chunks):
            nxt = self.chunks[i + 1][0] if i + 1 < len(self.chunks) else 1e9
            c[1] = min(nxt, c[3] + 0.55)

    @staticmethod
    def _at(segs, x):
        for a, b in segs:
            if x <= b - a:
                return a + x
            x -= b - a
        return segs[-1][1]

    def srt_cues(self):
        """Group chunks into readable subtitle cues (<= 42 chars)."""
        cues, cur = [], None
        for t0, t1, words, _ in self.chunks:
            txt = " ".join(w for w, _, _ in words)
            if cur and len(cur[2]) + 1 + len(txt) <= 42 and t0 - cur[1] < 0.25:
                cur[1] = t1
                cur[2] += " " + txt
            else:
                if cur:
                    cues.append(cur)
                cur = [t0, t1, txt]
        cues.append(cur)
        return cues

    def draw(self, cx, t, y, alpha=1.0, size=60):
        for t0, t1, words, _ in self.chunks:
            if t0 <= t < t1:
                self._draw_chunk(cx, t, t0, t1, words, y, alpha, size)

    def _draw_chunk(self, cx, t, t0, t1, words, y, alpha, size):
        fade = 1 - smooth(prog(t, t1 - 0.12, t1))
        sp = size * 0.27
        pad = size * 0.2
        widths = [text_w(cx, w, size) for w, _, _ in words]
        # extra room at the edges of each highlighted run
        def extra(k):
            hl = words[k][1]
            if not hl:
                return 0.0, 0.0
            first = k == 0 or not words[k - 1][1]
            last = k == len(words) - 1 or not words[k + 1][1]
            return (pad if first else 0.0), (pad if last else 0.0)
        lines, cur, cw = [], [], 0
        for k, wd in enumerate(widths):
            l_, r_ = extra(k)
            add = wd + l_ + r_ + (sp if cur else 0)
            if cur and cw + add > 960:
                lines.append(cur)
                cur, cw = [], 0
                add -= sp
            cur.append(k)
            cw += add
        lines.append(cur)
        lh = size * 1.34
        y0 = y - (len(lines) - 1) * lh / 2
        for li, ln in enumerate(lines):
            tw = sum(widths[k] + sum(extra(k)) for k in ln) + sp * (len(ln) - 1)
            x = W / 2 - tw / 2
            yy = y0 + li * lh
            pos = []
            for k in ln:
                l_, r_ = extra(k)
                pos.append((k, x + l_))
                x += l_ + widths[k] + r_ + sp
            alphas = {k: smooth(prog(t, words[k][2] - 0.05, words[k][2] + 0.07)) * fade * alpha for k in ln}
            # highlight boxes: one continuous box per run, growing as words appear
            run = []
            for idx, (k, wx) in enumerate(pos + [(None, 0)]):
                if k is not None and words[k][1]:
                    run.append((k, wx))
                    continue
                if run:
                    vis = [(k2, x2) for k2, x2 in run if alphas[k2] > 0.003]
                    if vis:
                        a0 = alphas[run[0][0]]
                        bx0 = run[0][1] - pad
                        kk, xx = vis[-1]
                        bx1 = xx + widths[kk] + pad
                        rrect(cx, bx0, yy - size * 0.86, bx1 - bx0, size * 1.14, size * 0.16)
                        src(cx, (0, 0, 0, 0.35 * a0))
                        cx.fill()
                        rrect(cx, bx0, yy - size * 0.92, bx1 - bx0, size * 1.14, size * 0.16)
                        src(cx, YELLOW, a0)
                        cx.fill()
                    run = []
            for k, wx in pos:
                a = alphas[k]
                if a <= 0.003:
                    continue
                rise = (1 - ease(prog(t, words[k][2] - 0.05, words[k][2] + 0.12))) * 8
                if words[k][1]:
                    draw_text(cx, words[k][0], wx, yy + rise, size, INKC, align="left", alpha=a)
                else:
                    _outlined(cx, words[k][0], wx, yy + rise, size, a)


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def _outlined(cx, s, x, y, size, a):
    font(cx, size)
    cx.move_to(x, y + size * 0.07)
    cx.text_path(s)
    src(cx, (0, 0, 0, 0.45 * a))
    cx.fill()
    cx.move_to(x, y)
    cx.text_path(s)
    src(cx, (0.05, 0.06, 0.12, 0.9 * a))
    cx.set_line_width(size * 0.12)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke_preserve()
    src(cx, WHITE, a)
    cx.fill()


def load_timing(build_dir):
    return json.load(open(os.path.join(build_dir, "timing.json")))
