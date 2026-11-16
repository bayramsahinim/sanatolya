"""Assemble and render "Can You Count the Jumps?" (Just Needy Short, 1080x1920, 30 fps).

usage:
  python -m episodes.count_the_jumps.episode timeline          # print the edit (and save build/.../timeline.json)
  python -m episodes.count_the_jumps.episode stills t1 t2 ...  # PNG previews
  python -m episodes.count_the_jumps.episode audio             # narration clips, word alignment, mix, SRT
  python -m episodes.count_the_jumps.episode video [--draft]   # render frames -> mp4 (needs audio)
  python -m episodes.count_the_jumps.episode all
"""
import json
import math
import multiprocessing as mp
import os
import subprocess
import sys
import time

import cairo
import numpy as np

from cinecode import audio as A
from cinecode import tts
from cinecode.captions import render_text
from cinecode.core import (OUTLINE, back_out, circle, clamp, ease_out, ellipse, fs, hexc, kf, line,
                           lerp, mix, prog, rrect, smooth, src)
from episodes.count_the_jumps import scene as sc
from episodes.count_the_jumps.split_take import LINES_DIR
from episodes.count_the_jumps.script import LINES, TEXT

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "count_the_jumps")
OUT = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_COUNT_THE_JUMPS_FINAL"
TITLE = "Can You Count the Jumps? | Just Needy"
W, H, FPS = sc.W, sc.H, 30
TEMPO = 1.05            # narration playback speed (formant-preserving), keeps the Short ~46 s
PRE, POST = 0.03, 0.08  # natural margins kept around each take's speech
CAP_Y = 690             # subtitle centre line (above the jumpers' heads, never over them)
CAP_SIZE = 76


# ================================================================== voice + timeline
def _voiced(a):
    from cinecode.align import envelope_db
    db = envelope_db(a)
    thr = np.percentile(db, 95) - 35
    v = np.where(db > thr)[0]
    return v[0] * 0.01, (v[-1] + 1) * 0.01


def load_clips():
    """lid -> (float32 @48k narration clip, [(word, t0, t1)] relative to clip start). Cached."""
    from cinecode.wordalign import align_words
    os.makedirs(BUILD, exist_ok=True)
    cache = os.path.join(BUILD, f"clips_{TEMPO}.npz")
    wcache = os.path.join(BUILD, f"words_{TEMPO}.json")
    if os.path.exists(cache) and os.path.exists(wcache):
        z = np.load(cache)
        words = json.load(open(wcache))
        if set(z.files) == set(TEXT) == set(words):
            return {k: (z[k], words[k]) for k in TEXT}
    clips, words = {}, {}
    for lid, text in LINES:
        raw = tts.read_wav(os.path.join(LINES_DIR, f"{lid}.wav"))
        y, sr = A.stretch(raw, tts.SR, TEMPO, BUILD)
        y = A.resample(np.asarray(y, np.float64), sr, A.SR).astype(np.float32)
        clips[lid] = y
        words[lid] = [(w, a_, b_) for w, a_, b_ in align_words(y, A.SR, text)]
    np.savez(cache, **clips)
    json.dump(words, open(wcache, "w"), indent=1)
    return {k: (clips[k], words[k]) for k in TEXT}


class Timeline:
    """Every time in the edit, derived from the real narration lengths."""

    def __init__(self, durs):
        m = {}
        t = 0.10
        m["hook"] = (t, t + durs["hook"])
        t = m["hook"][1] + 0.10
        m["go"] = (t, t + durs["go"])
        sc.set_go(t + 0.10)                      # the rope starts on "Go!"
        self.GO = sc.GO_T
        self.COUNT_END = sc.COUNT_END
        t = sc.COUNT_END + 0.08
        m["stop"] = (t, t + durs["stop"])
        t = m["stop"][1] + 0.30
        m["answer"] = (t, t + durs["answer"])
        self.R0 = m["answer"][1] + 0.30          # rewind
        self.R1 = self.R0 + 0.50                 # replay of the penguin starts
        t = self.R0 + 0.35
        m["penguin"] = (t, t + durs["penguin"])
        t = max(m["penguin"][1] + 0.25, self.R1 + 1.9)
        self.SKY = t
        m["sky"] = (t, t + durs["sky"])
        t = m["sky"][1] + 0.20
        self.SWAP = t
        m["swap"] = (t, t + durs["swap"])
        t = m["swap"][1] + 0.35
        self.SPOT = t
        m["spot"] = (t, t + durs["spot"])
        t = m["spot"][1] + 0.15
        m["name"] = (t, t + durs["name"])
        t = m["name"][1] + 0.35
        self.STUDY = t
        m["study"] = (t, t + durs["study"])
        t = m["study"][1] + 0.40
        self.ASK = t
        m["ask"] = (t, t + durs["ask"])
        self.END = m["ask"][1] + 0.80
        self.m = m
        # penguin replay: start 2.6 s into its walk (it is crossing behind the jumpers)
        self.REPLAY_FROM = sc.PENG_T0 + 2.4

    @property
    def duration(self):
        return self.END

    @property
    def nframes(self):
        return int(math.ceil(self.END * FPS))


_STATE = {}


def build():
    if "tl" not in _STATE:
        clips = load_clips()
        durs = {k: len(v[0]) / A.SR for k, v in clips.items()}
        tl = Timeline(durs)
        cues = []
        from cinecode.wordalign import group_words
        for lid, _ in LINES:
            t0 = tl.m[lid][0]
            for text, a, b in group_words(clips[lid][1], max_words=3, max_chars=16):
                cues.append({"text": text, "t0": t0 + a, "t1": t0 + b, "lid": lid})
        # make cues contiguous within a line, hold the last one a moment after speech
        for c, d in zip(cues, cues[1:]):
            if c["lid"] == d["lid"]:
                c["t1"] = d["t0"]
            else:
                c["t1"] = min(c["t1"] + 0.25, d["t0"] - 0.05)
        cues[-1]["t1"] += 0.4
        words = {lid: [(w, tl.m[lid][0] + a, tl.m[lid][0] + b) for w, a, b in clips[lid][1]]
                 for lid in TEXT}
        _STATE.update(tl=tl, cues=cues, clips=clips, words=words)
    return _STATE["tl"], _STATE["cues"], _STATE["words"]


def word_time(words, lid, needle, end=False):
    for w, a, b in words[lid]:
        if needle.lower() in w.lower():
            return b if end else a
    raise KeyError((lid, needle))


# ================================================================== overlay helpers
def caption(cx, t, cues):
    for i, c in enumerate(cues):
        nxt = cues[i + 1]["t0"] if i + 1 < len(cues) else 1e9
        if c["t0"] - 0.01 <= t < min(c["t1"] + 0.12, nxt):
            a_in = ease_out(prog(t, c["t0"], c["t0"] + 0.10))
            a_out = 1.0 if c["t1"] + 0.12 >= nxt else 1 - prog(t, c["t1"], c["t1"] + 0.12)
            al = min(a_in, a_out)
            if al <= 0:
                continue
            surf, w, h, pad = render_text(c["text"], CAP_SIZE)
            sc_ = 0.94 + 0.06 * a_in
            cx.save()
            cx.translate(W / 2, CAP_Y)
            cx.scale(sc_, sc_)
            cx.set_source_surface(surf, -w / 2, -h / 2)
            cx.paint_with_alpha(al)
            cx.restore()


def big_text(cx, t, txt, t0, t1, y, size, pop=True):
    if t < t0 or t > t1 + 0.25:
        return
    a_in = prog(t, t0, t0 + 0.22)
    al = min(ease_out(a_in), 1 - prog(t, t1, t1 + 0.25))
    s = (0.6 + 0.4 * back_out(a_in)) if pop else 1.0
    surf, w, h, pad = render_text(txt, size)
    cx.save()
    cx.translate(W / 2, y)
    cx.scale(s, s)
    cx.set_source_surface(surf, -w / 2, -h / 2)
    cx.paint_with_alpha(al)
    cx.restore()


def pill(cx, x, y, txt, size=34, alpha=1.0, scale=1.0, fg=(1, 1, 1, 1), bg=hexc("#120C26", 0.88),
         border=hexc("#8E86C9"), dots=None, rec=False):
    cx.save()
    cx.select_font_face("Montserrat ExtraBold")
    cx.set_font_size(size)
    ext = cx.text_extents(txt)
    extra = (size * 2.2 if dots else 0) + (size * 0.9 if rec else 0)
    pw, ph = ext.x_advance + size * 1.6 + extra, size * 1.9
    cx.translate(x, y)
    cx.scale(scale, scale)
    cx.push_group()
    rrect(cx, -pw / 2, -ph / 2, pw, ph, ph / 2)
    fs(cx, bg, border, 3.5)
    tx = -pw / 2 + size * 0.8 + (size * 0.9 if rec else 0)
    if rec:
        circle(cx, -pw / 2 + size * 0.95, 0, size * 0.26)
        fs(cx, hexc("#FF4D5E"), None, 0)
    cx.move_to(tx, size * 0.36)
    src(cx, fg)
    cx.show_text(txt)
    if dots:
        n, k = dots
        for i in range(n):
            dx = tx + ext.x_advance + size * 0.7 + i * size * 0.62
            circle(cx, dx, 0, size * 0.2)
            if i < k:
                fs(cx, sc.GOLD, None, 0)
            else:
                fs(cx, None, sc.GOLD, 2.5)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


def ring(cx, x, y, rx, ry, t, t0, color=sc.GOLD, lw=7):
    """Highlight ring that draws itself on."""
    p = smooth(prog(t, t0, t0 + 0.35))
    if p <= 0:
        return
    cx.save()
    cx.translate(x, y)
    cx.scale(rx, ry)
    cx.new_path()
    cx.arc(-math.pi / 2, -math.pi / 2 + 2 * math.pi * p) if False else cx.arc(0, 0, 1, -math.pi / 2, -math.pi / 2 + 2 * math.pi * p)
    cx.restore()
    src(cx, (0, 0, 0, 0.45))
    cx.set_line_width(lw + 5)
    cx.set_line_cap(cairo.LINE_CAP_ROUND)
    cx.stroke_preserve()
    src(cx, color)
    cx.set_line_width(lw)
    cx.stroke()


def arrow_down(cx, x, y, t, alpha=1.0):
    b = math.sin(t * 6) * 10
    cx.save()
    cx.translate(x, y + b)
    cx.push_group()
    cx.move_to(-18, -70)
    cx.line_to(18, -70)
    cx.line_to(18, -22)
    cx.line_to(40, -22)
    cx.line_to(0, 18)
    cx.line_to(-40, -22)
    cx.line_to(-18, -22)
    cx.close_path()
    fs(cx, sc.GOLD, OUTLINE, 6)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


def number_badge(cx, x, y, r, txt, t, t0, fill=sc.GOLD, fg=OUTLINE, size=None):
    a = prog(t, t0, t0 + 0.3)
    if a <= 0:
        return
    s = back_out(a, 2.2)
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    circle(cx, 0, 6, r)
    src(cx, (0, 0, 0, 0.35))
    cx.fill()
    circle(cx, 0, 0, r)
    fs(cx, fill, OUTLINE, 7)
    circle(cx, 0, 0, r - 14)
    fs(cx, None, (1, 1, 1, 0.35), 3)
    cx.select_font_face("Montserrat ExtraBold")
    size = size or r * 1.05
    cx.set_font_size(size)
    e = cx.text_extents(txt)
    cx.move_to(-e.width / 2 - e.x_bearing, -e.height / 2 - e.y_bearing)
    src(cx, fg)
    cx.show_text(txt)
    cx.restore()


def dark_with_spot(cx, x_top, x_bot, y_bot, w_top, w_bot, amount):
    """Darken the frame except a soft spotlight cone (attention metaphor)."""
    cx.push_group()
    cx.rectangle(0, 0, W, H)
    src(cx, (0.02, 0.01, 0.05, 0.84 * amount))
    cx.fill()
    cx.set_operator(cairo.OPERATOR_DEST_OUT)
    for k, (grow, a) in enumerate([(1.35, 0.25), (1.18, 0.35), (1.0, 1.0)]):
        cx.new_path()
        cx.move_to(x_top - w_top * grow / 2, -20)
        cx.line_to(x_top + w_top * grow / 2, -20)
        cx.line_to(x_bot + w_bot * grow / 2, y_bot)
        cx.curve_to(x_bot + w_bot * grow / 2, y_bot + 60 * grow, x_bot - w_bot * grow / 2, y_bot + 60 * grow,
                    x_bot - w_bot * grow / 2, y_bot)
        cx.close_path()
        src(cx, (0, 0, 0, a * amount))
        cx.fill()
    cx.set_operator(cairo.OPERATOR_OVER)
    cx.pop_group_to_source()
    cx.paint()
    # warm light inside the cone
    cx.new_path()
    cx.move_to(x_top - w_top / 2, -20)
    cx.line_to(x_top + w_top / 2, -20)
    cx.line_to(x_bot + w_bot / 2, y_bot)
    cx.curve_to(x_bot + w_bot / 2, y_bot + 60, x_bot - w_bot / 2, y_bot + 60, x_bot - w_bot / 2, y_bot)
    cx.close_path()
    g = cairo.LinearGradient(0, 0, 0, y_bot)
    g.add_color_stop_rgba(0, 1, 0.92, 0.7, 0.22 * amount)
    g.add_color_stop_rgba(1, 1, 0.92, 0.7, 0.05 * amount)
    cx.set_source(g)
    cx.fill()


def spotlight_lamp(cx, x, y, alpha):
    cx.save()
    cx.translate(x, y)
    cx.rotate(0.12)
    cx.push_group()
    rrect(cx, -46, -40, 92, 70, 14)
    fs(cx, hexc("#3B3552"), OUTLINE, 6)
    rrect(cx, -40, 22, 80, 18, 6)
    fs(cx, sc.GOLD, OUTLINE, 5)
    cx.pop_group_to_source()
    cx.paint_with_alpha(alpha)
    cx.restore()


def scanlines(cx, amount):
    src(cx, (0, 0, 0, 0.18 * amount))
    for y in range(0, H, 6):
        cx.rectangle(0, y, W, 2)
    cx.fill()


# ================================================================== study scene (original 1999 study)
def draw_gorilla(cx, x, y, t, s=1.0, thump=0.0, walking=True):
    ph = t * 2.6 * 2 * math.pi if walking else 0
    bob = abs(math.sin(ph)) * 6 if walking else 0
    fur, fur_dk, face = hexc("#2A2630"), hexc("#1C1921"), hexc("#7A6E80")
    cx.save()
    cx.translate(x, y)
    cx.scale(s, s)
    ellipse(cx, 0, 4, 80, 12)
    src(cx, (0, 0, 0, 0.3))
    cx.fill()
    for side in (-1, 1):  # legs
        lift = max(0, math.sin(ph + (side + 1) * math.pi / 2)) * 12 if walking else 0
        rrect(cx, side * 30 - 22, -90 - lift, 44, 90, 18)
        fs(cx, fur_dk, OUTLINE, 5)
    cx.translate(0, -bob)
    # arms (long, knuckles near the ground) — raised in for the chest thump
    for side in (-1, 1):
        sw = math.sin(ph + (0 if side < 0 else math.pi)) * 0.15 if walking else 0
        cx.save()
        cx.translate(side * 62, -230)
        cx.rotate(side * (0.18 + sw) - side * thump * 1.6)
        rrect(cx, -22, 0, 44, 165 - thump * 60, 20)
        fs(cx, fur, OUTLINE, 5)
        cx.restore()
    ellipse(cx, 0, -180, 82, 105)       # body
    fs(cx, fur, OUTLINE, 6)
    ellipse(cx, 0, -168, 46, 58)        # chest
    fs(cx, hexc("#3A3542"), None, 0)
    circle(cx, 0, -300, 50)             # head
    fs(cx, fur, OUTLINE, 6)
    ellipse(cx, 0, -288, 34, 30)        # face
    fs(cx, face, OUTLINE, 3.5)
    for side in (-1, 1):
        ellipse(cx, side * 12, -298, 4.5, 6)
        fs(cx, OUTLINE, None, 0)
    line(cx, [(-24, -310), (24, -310)], fur_dk, 7)
    ellipse(cx, 0, -276, 12, 6)
    fs(cx, hexc("#4A3F52"), None, 0)
    cx.restore()


def draw_study(cx, t, tl, words):
    t0 = tl.STUDY
    lt = t - t0
    # gym backdrop
    g = cairo.LinearGradient(0, 0, 0, sc.FLOOR_Y)
    g.add_color_stop_rgba(0, *hexc("#1A1238"))
    g.add_color_stop_rgba(1, *hexc("#3A2A6E"))
    cx.rectangle(0, 0, W, H)
    cx.set_source(g)
    cx.fill()
    sc.draw_background(cx, t, sky=0.0)
    # six players, two teams, passing two balls in a loop
    xs = [110, 290, 450, 630, 790, 970]
    kinds = ["white", "dark", "white", "dark", "white", "dark"]
    ys = [sc.FLOOR_Y - 20, sc.FLOOR_Y + 40, sc.FLOOR_Y - 20, sc.FLOOR_Y + 40, sc.FLOOR_Y - 20, sc.FLOOR_Y + 40]
    pos = {}
    order = sorted(range(6), key=lambda i: ys[i])
    # gorilla walks in from the right, stops mid-court, thumps, leaves left
    g_x = kf(lt, [(0.4, 1260.0), (2.6, 560.0), (3.8, 560.0), (6.6, -260.0)], ease=lambda x: x)
    thump = pulse_thump(lt)
    walking = not (2.6 < lt < 3.8)
    for i in order:
        wob = math.sin(t * 2.0 + i) * 6
        a = draw_person(cx, xs[i] + wob, ys[i], t, kinds[i], seed=i)
        pos[i] = a
        if i == 2:
            draw_gorilla(cx, g_x, sc.FLOOR_Y + 14, t, s=1.45, thump=thump, walking=walking)
    # balls: white team passes among 0,2,4 ; dark team among 1,3,5
    for team, ids, off in (("w", [0, 2, 4], 0.0), ("d", [1, 3, 5], 0.33)):
        per = 0.75
        k = int((lt + off * per) / per)
        u = ((lt + off * per) / per) % 1
        a = pos[ids[k % 3]]["r"]
        b = pos[ids[(k + 1) % 3]]["l"]
        x = lerp(a[0], b[0], u)
        yb = lerp(a[1], b[1], u) - math.sin(math.pi * u) * 150
        circle(cx, x, yb, 24)
        fs(cx, hexc("#F08A2E") if team == "w" else hexc("#E4782A"), OUTLINE, 4)
        line(cx, [(x - 21, yb), (x + 21, yb)], OUTLINE, 2.5)
        line(cx, [(x, yb - 21), (x, yb + 21)], OUTLINE, 2.5)
    # labels: clearly the original study, not our penguin demo
    al = smooth(prog(lt, 0.0, 0.3))
    pill(cx, W / 2, 300, "ORIGINAL STUDY \u00b7 1999", size=40, alpha=al)
    cx.save()
    cx.select_font_face("Montserrat ExtraBold")
    cx.set_font_size(30)
    s_ = "Simons & Chabris"
    e = cx.text_extents(s_)
    cx.move_to(W / 2 - e.width / 2 - e.x_bearing, 375)
    src(cx, (1, 1, 1, 0.75 * al))
    cx.show_text(s_)
    cx.restore()
    th = word_time(words, "study", "half")
    big_text(cx, t, "ABOUT HALF\n[MISSED THE GORILLA]", th, tl.ASK - 0.25, 500, 66)


def pulse_thump(lt):
    if not (2.6 < lt < 3.8):
        return 0.0
    return 0.5 + 0.5 * math.sin((lt - 2.6) * 2 * math.pi * 3.2 - math.pi / 2)


def draw_person(cx, x, y, t, kind, seed=0):
    return sc.draw_person(cx, x, y, t, kind=kind, s=1.32, seed=seed)


# ================================================================== frame
def render(cx, t):
    tl, cues, words = build()
    if t < tl.R0:
        _live(cx, t, tl)
    elif t < tl.R1:
        _rewind(cx, t, tl)
    elif t < tl.SKY:
        _replay(cx, t, tl)
    elif t < tl.SWAP:
        _sky(cx, t, tl)
    elif t < tl.SPOT:
        _swap(cx, t, tl)
    elif t < tl.STUDY:
        _spot(cx, t, tl, words)
    elif t < tl.ASK:
        draw_study(cx, t, tl, words)
    else:
        _ask(cx, t, tl, words)
    caption(cx, t, cues)


def _live(cx, t, tl):
    sc.draw_background(cx, t)
    face = "focus" if t < tl.m["answer"][0] else "happy"
    a = sc.draw_lineup(cx, t, hero_face=face)
    # hook graphics
    al = 1 - smooth(prog(t, tl.GO - 0.05, tl.GO + 0.25))
    if al > 0:
        hx, hy = a["hero"]
        arrow_down(cx, hx, hy - 125, t, al)
        surf, w, h, pad = render_text("COUNT THE\n[JUMPS]", 128)
        cx.set_source_surface(surf, W / 2 - w / 2, 430 - h / 2)
        cx.paint_with_alpha(al)
    # level badge
    if tl.GO + 0.25 <= t <= tl.COUNT_END + 0.5:
        k = sum(1 for s_ in sc.LEVEL_START if t >= s_ - 0.05)
        k = max(1, k)
        t_pop = max(sc.LEVEL_START[k - 1] - 0.05, tl.GO + 0.25)
        pop = back_out(prog(t, t_pop, t_pop + 0.28), 2.5)
        al = smooth(prog(t, tl.GO + 0.25, tl.GO + 0.45)) * (1 - prog(t, tl.COUNT_END + 0.2, tl.COUNT_END + 0.5))
        pill(cx, W / 2, 480, f"LEVEL {k}", size=40, alpha=al, scale=0.75 + 0.25 * pop, dots=(3, k))
    # STOP! / 21
    big_text(cx, t, "[STOP!]", tl.m["stop"][0], tl.m["stop"][0] + 0.7, 480, 120)
    if t >= tl.m["stop"][0] + 0.75 and t < tl.m["answer"][0]:
        number_badge(cx, W / 2, 480, 78, "?", t, tl.m["stop"][0] + 0.75, fill=hexc("#120C26"), fg=sc.GOLD)
    if t >= tl.m["answer"][0]:
        number_badge(cx, W / 2, 470, 125, "21", t, tl.m["answer"][0])


def _rewind(cx, t, tl):
    u = smooth(prog(t, tl.R0, tl.R1))
    st = lerp(tl.R0, tl.REPLAY_FROM, u)
    sc.draw_background(cx, st)
    sc.draw_lineup(cx, st)
    scanlines(cx, 1.0)
    cx.rectangle(0, 0, W, H)
    src(cx, (0.05, 0.02, 0.1, 0.25))
    cx.fill()
    # rewind icon
    cx.save()
    cx.translate(W / 2, 480)
    for dx in (-36, 30):
        cx.move_to(dx + 30, -36)
        cx.line_to(dx - 30, 0)
        cx.line_to(dx + 30, 36)
        cx.close_path()
    fs(cx, (1, 1, 1, 0.95), OUTLINE, 5)
    cx.restore()


def _replay(cx, t, tl):
    st = tl.REPLAY_FROM + (t - tl.R1)
    sc.draw_background(cx, st)
    a = sc.draw_lineup(cx, st, dim_others=0.45, hero_alpha=0.55)
    pill(cx, 170, 140, "REPLAY", size=34, rec=True)
    if "penguin" in a:
        px, py = a["penguin"]
        ring(cx, px - 10, py - 25, 175, 250, t, tl.R1 + 0.1, lw=8)


def _split(cx, t, tl, left_t, right_t, wipe):
    # left half: early in the count (purple); right half: late (orange)
    xdiv = lerp(W, W / 2, wipe)
    cx.save()
    cx.rectangle(0, 0, xdiv, H)
    cx.clip()
    sc.draw_background(cx, left_t)
    sc.draw_lineup(cx, left_t, penguin=False)
    cx.restore()
    cx.save()
    cx.rectangle(xdiv, 0, W - xdiv, H)
    cx.clip()
    sc.draw_background(cx, right_t)
    sc.draw_lineup(cx, right_t, penguin=False)
    cx.restore()
    line(cx, [(xdiv, 0), (xdiv, H)], (1, 1, 1, 0.95), 6)
    return xdiv


def _sky(cx, t, tl):
    lt = t - tl.SKY
    wipe = smooth(prog(lt, 0.0, 0.4))
    xdiv = _split(cx, t, tl, sc.LEVEL_START[0] + 0.3 + lt, sc.LEVEL_START[2] + 0.6 + lt, wipe)
    al = smooth(prog(lt, 0.25, 0.5))
    pill(cx, xdiv / 2, 480, "START", size=38, alpha=al)
    pill(cx, xdiv + (W - xdiv) / 2, 480, "END", size=38, alpha=al)


def _swap(cx, t, tl):
    lt = t - tl.SWAP
    st = sc.LEVEL_START[2] + 0.3 + lt
    sc.draw_background(cx, st)
    a = sc.draw_lineup(cx, st, penguin=False, dim_others=0.0)
    hx, hy = a["turner_l"]
    ring(cx, hx, hy, 112, 112, t, tl.SWAP + 0.15)
    # before / after insets
    al = smooth(prog(lt, 0.2, 0.5))
    for k, (x, label, swapped, st_) in enumerate([(320, "BEFORE", False, 6.0), (760, "AFTER", True, st)]):
        cy = 430
        cx.save()
        cx.push_group()
        circle(cx, x, cy, 125)
        fs(cx, hexc("#120C26"), sc.GOLD if swapped else hexc("#8E86C9"), 7)
        cx.save()
        circle(cx, x, cy, 120)
        cx.clip()
        sc.draw_person(cx, x, cy + 270 * 2.0 + 25, st_, swapped=swapped, s=2.0, seed=3,
                       arms={"r": (60, 40)}, look=(0.4, 0))
        cx.restore()
        circle(cx, x, cy, 125)
        fs(cx, None, sc.GOLD if swapped else hexc("#8E86C9"), 7)
        cx.pop_group_to_source()
        cx.paint_with_alpha(al)
        cx.restore()
        pill(cx, x, cy + 140, label, size=30, alpha=al)
    # arrow between
    if al > 0:
        cx.save()
        cx.push_group()
        line(cx, [(482, 430), (592, 430)], (1, 1, 1, 1), 10)
        cx.move_to(612, 430)
        cx.line_to(580, 406)
        cx.line_to(580, 454)
        cx.close_path()
        fs(cx, (1, 1, 1, 1), None, 0)
        cx.pop_group_to_source()
        cx.paint_with_alpha(al)
        cx.restore()


def _spot(cx, t, tl, words):
    lt = t - tl.SPOT
    st = sc.PENG_T0 + 0.6 + lt                 # the count again, penguin crossing in the dark
    sc.draw_background(cx, st)
    a = sc.draw_lineup(cx, st)
    amt = smooth(prog(lt, 0.0, 0.6))
    hx = sc.X_HERO
    dark_with_spot(cx, hx - 40, hx, sc.FLOOR_Y + 10, 120, 250, amt)
    spotlight_lamp(cx, hx - 40, 40, amt)
    # the penguin is right there, in the dark (subtle dashed outline, after the reveal it is fair to show)
    if "penguin" in a and t > word_time(words, "spot", "Whatever"):
        px, py = a["penguin"]
        cx.save()
        cx.set_dash([18, 14], t * 40)
        ring(cx, px - 10, py - 25, 175, 250, t, word_time(words, "spot", "Whatever"), color=hexc("#B9B2E8"),
             lw=5)
        cx.restore()
    # term card
    tn = tl.m["name"][0]
    big_text(cx, t, "INATTENTIONAL\n[BLINDNESS]", tn + 0.05, tl.STUDY - 0.2, 470, 80)


def _ask(cx, t, tl, words):
    lt = t - tl.ASK
    st = sc.COUNT_END + 1.0 + lt
    sc.draw_background(cx, st)
    a = sc.draw_lineup(cx, st, penguin=False, hero_face="happy")
    # answer choices pop in on "Zero ... three"
    tz = word_time(words, "ask", "Zero")
    t3 = word_time(words, "ask", "three")
    xs = [W / 2 + (i - 1.5) * 190 for i in range(4)]
    for i, x in enumerate(xs):
        t_i = tz + (t3 - tz) * i / 3 if i else tz
        t_i = min(t_i, tz + 0.15 * i + 0.01) if t3 - tz < 0.45 else t_i
        number_badge(cx, x, 480, 76, str(i), t, t_i, fill=hexc("#120C26"), fg=(1, 1, 1, 1), size=72)
    # comment bubble above the hero on "comments"
    tc = word_time(words, "ask", "comments")
    p = back_out(prog(t, tc - 0.15, tc + 0.15), 2)
    if p > 0:
        hx, hy = a["hero"]
        cx.save()
        cx.translate(hx + 120, hy - 140)
        cx.scale(p, p)
        rrect(cx, -70, -45, 140, 90, 30)
        cx.move_to(-40, 40)
        cx.line_to(-70, 75)
        cx.line_to(-10, 44)
        fs(cx, (1, 1, 1, 1), OUTLINE, 6)
        for k in (-1, 0, 1):
            circle(cx, k * 34, 0, 10)
            fs(cx, OUTLINE, None, 0)
        cx.restore()


# ================================================================== stills / video
def new_ctx():
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(s)
    cx.set_source_rgb(0, 0, 0)
    cx.paint()
    return s, cx


def stills(times, prefix="still"):
    os.makedirs(os.path.join(BUILD, "stills"), exist_ok=True)
    for t in times:
        s, cx = new_ctx()
        render(cx, t)
        p = os.path.join(BUILD, "stills", f"{prefix}_{t:06.2f}.png")
        s.write_to_png(p)
        print(p)


def _worker(args):
    a, b, path, scale = args
    w, h = int(W * scale), int(H * scale)
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium" if scale == 1 else "veryfast",
           "-crf", "18" if scale == 1 else "26", "-tune", "animation", "-pix_fmt", "yuv420p", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    for i in range(a, b):
        cx = cairo.Context(s)
        cx.set_source_rgb(0, 0, 0)
        cx.paint()
        if scale != 1:
            cx.scale(scale, scale)
        render(cx, i / FPS)
        s.flush()
        pr.stdin.write(bytes(s.get_data()))
    pr.stdin.close()
    pr.wait()
    return path


def render_video(draft=False, workers=4):
    tl, _, _ = build()
    os.makedirs(OUT, exist_ok=True)
    n = tl.nframes
    chunks = workers * 4
    step = (n + chunks - 1) // chunks
    jobs = []
    for k in range(chunks):
        a, b = k * step, min(n, (k + 1) * step)
        if a < b:
            jobs.append((a, b, os.path.join(BUILD, f"part_{k:03d}.mp4"), 0.5 if draft else 1.0))
    t = time.time()
    with mp.Pool(workers) as pool:
        for i, _ in enumerate(pool.imap(_worker, jobs)):
            print(f"  chunk {i + 1}/{len(jobs)}  {time.time() - t:.0f}s", flush=True)
    lst = os.path.join(BUILD, "parts.txt")
    with open(lst, "w") as f:
        for _, _, p, _ in jobs:
            f.write(f"file '{p}'\n")
    silent = os.path.join(BUILD, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    silent], check=True)
    mixp = os.path.join(BUILD, "mix.wav")
    final = os.path.join(OUT, f"{NAME}_draft.mp4" if draft else f"{NAME}.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", mixp, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                    "-metadata", f"title={TITLE}", final], check=True)
    print("wrote", final, f"{time.time() - t:.0f}s")
    return final


# ================================================================== audio
def sfx_rope(seed):
    """Soft rope whoosh as it slaps past the floor."""
    d = 0.16
    x = A.bp(A.noise(d, 300 + seed), 900, 4200) * A.exp_env(int(d * A.SR), 0.05)
    tick = A.hp(A.noise(0.012, 400 + seed), 2500) * 0.6
    out = np.zeros(int(d * A.SR))
    out[: len(x)] += x
    A.add(out, tick, 0.035)
    return A.fade(out, 0.01, 0.03) * 0.5


def sfx_land(seed):
    return A.lp(A.noise(0.06, 500 + seed), 400) * A.exp_env(int(0.06 * A.SR), 0.02) * 0.9


def sfx_soft_pop(f=660):
    d = 0.14
    tt = A.t_arr(d)
    x = np.sin(2 * np.pi * f * tt * (1 + 0.6 * np.exp(-tt * 40))) * A.exp_env(len(tt), 0.04)
    return A.fade(x, 0.002, 0.02) * 0.6


def mix_audio():
    tl, cues, words = build()
    clips = _STATE["clips"]
    n = int(tl.END * A.SR) + A.SR
    voice, music, fx = np.zeros(n), np.zeros(n), np.zeros(n)
    for lid, _ in LINES:
        x = clips[lid][0].astype(np.float64)
        v = x[np.abs(x) > 0.02]
        x = x * (0.16 / (np.sqrt((v ** 2).mean()) + 1e-9))
        A.add(voice, x, tl.m[lid][0])
    # --- opening + experiment: light rhythmic bed, rope + minimal landings, nothing for the tricks
    bed = A.track("room", tl.COUNT_END + 0.6)
    k = int(0.5 * A.SR)
    bed[-k:] *= np.linspace(1, 0, k)
    A.add(music, bed * 1.0, 0.0)
    for i, tb in enumerate(sc.JUMPS):
        A.add(fx, sfx_rope(i) * 0.55, tb - 0.04)
        per = sc.period(i)
        A.add(fx, sfx_land(i) * 0.45, tb + per * 0.28)
    # --- stop / answer / reveal
    A.add(fx, A.get_sfx("whoosh") * 0.25, tl.m["stop"][0] - 0.05)
    A.add(fx, A.get_sfx("ding") * 0.55, tl.m["answer"][0])
    A.add(fx, A.get_sfx("rewind") [: int(0.55 * A.SR)] * 0.5, tl.R0)
    dun = A.music_sting("dun")
    A.add(fx, dun * 0.42, word_time(words, "penguin", "penguin") - 0.05)   # the one dramatic accent
    A.add(fx, A.get_sfx("whoosh") * 0.25, tl.SKY)
    A.add(fx, A.get_sfx("pop") * 0.35, tl.SWAP + 0.15)
    # --- explanation: gentle atmospheric bed
    d = tl.END - tl.SKY + 0.5
    bed2 = A.track("warm", d)
    k = int(0.8 * A.SR)
    bed2[:k] *= np.linspace(0, 1, k)
    bed2[-k:] *= np.linspace(1, 0, k)
    A.add(music, bed2 * 0.85, tl.SKY - 0.2)
    A.add(fx, A.get_sfx("flashlight") * 0.35, tl.SPOT)
    # --- ending: four soft pops for 0-1-2-3
    tz = word_time(words, "ask", "Zero")
    t3 = word_time(words, "ask", "three")
    for i in range(4):
        t_i = tz + (t3 - tz) * i / 3 if i else tz
        A.add(fx, sfx_soft_pop(620 + 90 * i) * 0.5, t_i)
    A.add(fx, A.get_sfx("pop") * 0.3, word_time(words, "ask", "comments") - 0.1)
    # --- mix: music ducks under the voice, voice stays on top
    env = A.envelope_follow(voice, 0.03, 0.4)
    duck = 1.0 - 0.6 * np.clip(env / 0.08, 0, 1)
    total = voice * 1.0 + music * 10 ** (-14 / 20) * duck + fx * 10 ** (-8 / 20)
    total = np.tanh(total * 0.95) / 0.95
    import soundfile as sf
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, total[: int(tl.END * A.SR)].astype(np.float32), A.SR, subtype="FLOAT")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true")
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    # stems for QA (voice vs. everything else)
    sf.write(os.path.join(BUILD, "stem_voice.wav"), voice[: int(tl.END * A.SR)].astype(np.float32), A.SR)
    sf.write(os.path.join(BUILD, "stem_bg.wav"),
             (music * 10 ** (-14 / 20) * duck + fx * 10 ** (-8 / 20))[: int(tl.END * A.SR)].astype(np.float32), A.SR)
    print("wrote", out)
    return out


def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt():
    _, cues, _ = build()
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, f"{NAME}.srt")
    with open(p, "w") as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{fmt(c['t0'])} --> {fmt(c['t1'])}\n{c['text']}\n\n")
    print("wrote", p)


def print_timeline():
    tl, cues, words = build()
    print(f"GO {tl.GO:.2f}  first jump {sc.JUMPS[0]:.2f}  last {sc.JUMPS[-1]:.2f}  count end {tl.COUNT_END:.2f}")
    print(f"levels {[round(x, 2) for x in sc.LEVEL_START]}  penguin {sc.PENG_T0:.2f}-{sc.PENG_T1:.2f} "
          f" swap {sc.SWAP_T:.2f}  sky {sc.SKY_T0:.2f}-{sc.SKY_T1:.2f}")
    print(f"rewind {tl.R0:.2f}-{tl.R1:.2f}  sky {tl.SKY:.2f}  swap {tl.SWAP:.2f}  spot {tl.SPOT:.2f}  "
          f"study {tl.STUDY:.2f}  ask {tl.ASK:.2f}  END {tl.END:.2f}")
    for lid, _ in LINES:
        print(f"  {lid:8s} {tl.m[lid][0]:6.2f} - {tl.m[lid][1]:6.2f}")
    json.dump({"marks": tl.m, "jumps": sc.JUMPS, "end": tl.END, "cues": cues},
              open(os.path.join(BUILD, "timeline.json"), "w"), indent=1)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "timeline":
        print_timeline()
    elif cmd == "stills":
        stills([float(x) for x in sys.argv[2:]])
    elif cmd == "audio":
        mix_audio()
        write_srt()
    elif cmd == "video":
        render_video(draft="--draft" in sys.argv)
    elif cmd == "all":
        print_timeline()
        mix_audio()
        write_srt()
        render_video()
