"""Timeline + subtitles for the vertical short.

Shots declare which narration lines they hold; timing comes from the real voice clips.
"""
import json
import math
import os
import re

from cinecode.align import syllables
from .look import BLUE_L, GREY2, H, W, WHITE, clamp, font, hexc, prog, src, text_w
from .script import SUB

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DUR = json.load(open(os.path.join(ROOT, "assets", "audio", "tts_numbers", "lines", "durations.json")))


class Shot:
    lines = []
    lead = 0.35       # silence before the first line
    tail = 0.35       # silence after the last line
    gap = 0.45        # default gap between lines in the shot
    gaps = {}         # lid -> gap before that line
    hold = {}         # lid -> extra silence after that line
    fade_in = 0.18
    fade_out = 0.18

    def build(self, t0, scale=1.0):
        self.t0 = t0
        self.T = {}
        t = self.lead * scale
        for i, lid in enumerate(self.lines):
            if i:
                t += self.gaps.get(lid, self.gap) * scale
            self.T[lid] = (t, t + DUR[lid])
            t += DUR[lid] + self.hold.get(lid, 0.0)
        self.dur = t + self.tail * scale
        return t0 + self.dur

    def s(self, lid, frac=0.0):
        a, b = self.T[lid]
        return a + (b - a) * frac

    def e(self, lid):
        return self.T[lid][1]

    def word_t(self, lid, word_index):
        """Approximate local time at which word `word_index` of the line is spoken."""
        return self.T[lid][0] + _word_times(lid)[word_index] * (self.T[lid][1] - self.T[lid][0])

    def sfx(self):
        return []

    def draw(self, f, t):
        raise NotImplementedError


def _word_times(lid):
    words = SUB[lid].split()
    w = [syllables(x) - 1.3 for x in words]  # syllables() adds +1.5 baseline; keep punctuation weight
    tot = sum(w)
    out, acc = [], 0.0
    for x in w:
        out.append(acc / tot)
        acc += x
    return out


# ------------------------------------------------------------------ subtitles
SUB_Y = 1420
SUB_SIZE = 50
SUB_MAXW = 900
# landscape: lower third, slightly smaller type, wider line
SUB_LAND = dict(y=968, size=46, maxw=1400)


def _sub_params():
    from .look import land
    if land():
        return SUB_LAND["y"], SUB_LAND["size"], SUB_LAND["maxw"]
    return SUB_Y, SUB_SIZE, SUB_MAXW


def chunks(lid):
    """Split a subtitle line into on-screen chunks (<= ~34 chars, broken at punctuation)."""
    words = SUB[lid].split()
    times = _word_times(lid)
    out, cur, cur_i = [], [], []
    for i, wd in enumerate(words):
        cur.append(wd)
        cur_i.append(i)
        txt = " ".join(cur)
        end_punct = re.search(r"[.?!:]\"?$", wd) is not None
        soft = re.search(r"[,]\"?$", wd) is not None
        nxt = len(txt) + (len(words[i + 1]) + 1 if i + 1 < len(words) else 0)
        if end_punct and len(txt) >= 10 or (soft and len(txt) >= 26) or nxt > 44:
            out.append((cur_i[0], cur_i[-1]))
            cur, cur_i = [], []
    if cur:
        out.append((cur_i[0], cur_i[-1]))
    # merge tiny trailing chunks
    merged = []
    for a, b in out:
        if merged and len(" ".join(words[a:b + 1])) < 12 and len(" ".join(words[merged[-1][0]:b + 1])) <= 54 \
                and not re.search(r"[.?!]\"?$", words[merged[-1][1]]):
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    res = []
    for k, (a, b) in enumerate(merged):
        ts = times[a]
        te = times[merged[k + 1][0]] if k + 1 < len(merged) else 1.0
        res.append((a, b, ts, te))
    return words, times, res


def subtitle_cues(shots):
    """[(start, end, text, words, word_times_abs)] in global seconds."""
    cues = []
    for sh in shots:
        for lid in sh.lines:
            a, b = sh.T[lid]
            words, times, ch = chunks(lid)
            d = b - a
            for (i0, i1, ts, te) in ch:
                st = sh.t0 + a + ts * d
                en = sh.t0 + a + te * d
                wt = [sh.t0 + a + times[i] * d for i in range(i0, i1 + 1)]
                cues.append([st, en, " ".join(words[i0:i1 + 1]), words[i0:i1 + 1], wt])
    # extend each cue to just before the next (but not over long silences)
    for k, c in enumerate(cues):
        nxt = cues[k + 1][0] if k + 1 < len(cues) else c[1] + 1.0
        c[1] = min(max(c[1] + 0.35, c[1]), nxt - 0.02)
    return cues


def _layout(c, words, size, maxw=None):
    SUB_MAXW = maxw or _sub_params()[2]
    font(c, "Inter", "bold", size)
    sp = c.text_extents(" ").x_advance
    lines, cur, w = [], [], 0
    for wd in words:
        ww = c.text_extents(wd).x_advance
        if cur and w + sp + ww > SUB_MAXW:
            lines.append((cur, w))
            cur, w = [], 0
        cur.append((wd, ww))
        w = ww if len(cur) == 1 else w + sp + ww
    if cur:
        lines.append((cur, w))
    # balance two lines (vertical only; widescreen keeps one line whenever it fits)
    from .look import land
    if not land() and len(lines) == 1 and lines[0][1] > SUB_MAXW * 0.72 and len(words) > 3:
        tot = lines[0][1]
        acc, cut = 0, 1
        for i, (wd, ww) in enumerate(lines[0][0]):
            acc += ww + sp
            if acc > tot / 2:
                cut = max(1, i)
                break
        a, b = lines[0][0][:cut + 1], lines[0][0][cut + 1:]
        if b:
            lines = [(a, sum(x[1] for x in a) + sp * (len(a) - 1)), (b, sum(x[1] for x in b) + sp * (len(b) - 1))]
    return lines, sp


def draw_subtitle(c, gt, cues):
    for st, en, txt, words, wt in cues:
        if not (st - 0.12 <= gt <= en + 0.12):
            continue
        a = clamp(min((gt - st + 0.12) / 0.16, (en + 0.12 - gt) / 0.16))
        rise = (1 - clamp((gt - st + 0.12) / 0.22)) * 10
        SUB_Y, SUB_SIZE, SUB_MAXW = _sub_params()
        ow = c.get_target().get_width()
        lines, sp = _layout(c, words, SUB_SIZE, SUB_MAXW)
        lh = SUB_SIZE * 1.28
        y0 = SUB_Y - (len(lines) - 1) * lh / 2 + rise
        # soft dark band so text stays readable over any scene
        import cairo
        bw = max(l[1] for l in lines) + 160
        bh = len(lines) * lh + 70
        cy = y0 - SUB_SIZE * 0.35 + (len(lines) - 1) * lh / 2
        c.save()
        c.translate(ow / 2, cy)
        c.scale(bw / 2, bh / 2)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        g.add_color_stop_rgba(0, 0, 0, 0, 0.55 * a)
        g.add_color_stop_rgba(0.6, 0, 0, 0, 0.42 * a)
        g.add_color_stop_rgba(1, 0, 0, 0, 0)
        c.set_source(g)
        c.arc(0, 0, 1, 0, 6.2832)
        c.fill()
        c.restore()
        k = 0
        for li, (ln, lw_) in enumerate(lines):
            x = ow / 2 - lw_ / 2
            y = y0 + li * lh
            for wd, ww in ln:
                spoken = gt >= wt[k] - 0.05
                lit = clamp((gt - wt[k] + 0.05) / 0.12)
                # soft shadow
                c.move_to(x, y)
                c.text_path(wd)
                src(c, (0, 0, 0, 1), 0.55 * a)
                c.set_line_width(9)
                c.stroke()
                col = tuple(GREY2[i] + (WHITE[i] - GREY2[i]) * lit for i in range(3))
                c.move_to(x, y)
                src(c, col, a)
                c.show_text(wd)
                x += ww + sp
                k += 1
                _ = spoken
        return


def srt(cues, path):
    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(path, "w") as fh:
        for i, (st, en, txt, _, _) in enumerate(cues, 1):
            fh.write(f"{i}\n{ts(st)} --> {ts(en)}\n{txt}\n\n")
