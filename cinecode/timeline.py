"""Shot planning + episode assembly.

A Shot implements:
    plan(self, P)        -> place narration/dialogue/sfx/captions, set marks
    draw(self, cx, t)    -> draw the full frame at shot-local time t
Narration durations come from the actual voice clips, so animation beats are
timed against the words. Marks are available as self.m[name] = (start, end).
"""
import json
import math

import cairo

from . import captions
from .core import FPS, H, W, Cam, clamp, prog, smooth, src


class VoiceDB:
    """Per-line clip durations (after tempo change). Unknown lines are estimated."""

    def __init__(self, durations, texts, tempo):
        self.d = durations      # lid -> seconds (final, stretched)
        self.texts = texts      # lid -> text
        self.tempo = tempo
        self.estimated = set()

    def dur(self, lid):
        if lid in self.d:
            return self.d[lid]
        from .align import syllables
        self.estimated.add(lid)
        return syllables(self.texts[lid]) * 0.215 / self.tempo + 0.15


class Planner:
    def __init__(self, shot, voice):
        self.shot = shot
        self.voice = voice
        self.t = 0.0
        self.cues = []
        self.m = shot.m

    # -- narration / dialogue
    def say(self, lid, gap=0.45, lead=0.0):
        self.t += lead
        d = self.voice.dur(lid)
        self.cues.append({"type": "narr", "id": lid, "t0": self.t, "dur": d})
        self.m[lid] = (self.t, self.t + d)
        start = self.t
        self.t += d + gap
        return start

    def dlg(self, lid, who, text, gap=0.4, lead=0.0, prefer=None, size=60):
        self.t += lead
        d = self.voice.dur(lid)
        self.cues.append({"type": "dlg", "id": lid, "t0": self.t, "dur": d})
        self.cues.append({"type": "bubble", "who": who, "text": text, "t0": self.t,
                          "t1": self.t + d + 0.4, "size": size, "prefer": prefer})
        self.m[lid] = (self.t, self.t + d)
        start = self.t
        self.t += d + gap
        return start

    def wait(self, s):
        self.t += s
        return self.t

    def mark(self, name, t=None):
        t = self.t if t is None else t
        self.m[name] = (t, t)
        return t

    def sfx(self, name, t=None, vol=1.0, **kw):
        self.cues.append({"type": "sfx", "name": name, "t0": self.t if t is None else t, "vol": vol, **kw})

    def accent(self, text, t=None, dur=2.2, size=96, pos=(W / 2, 200)):
        t0 = self.t if t is None else t
        self.cues.append({"type": "accent", "text": text, "t0": t0, "t1": t0 + dur, "size": size, "pos": pos})


class Shot:
    trans_in = None       # None | ("dip", secs) | ("flash", secs) | ("white", secs)
    music = None          # music track name
    music_gain = 1.0
    amb = None            # ambience bed name
    amb_gain = 1.0
    tail = 0.0            # extra hold after planned content
    scene = ""

    def __init__(self):
        self.m = {}
        self.heads = {}
        self.dur = 0.0
        self.cues = []

    def plan(self, P):
        pass

    def draw(self, cx, t):
        pass

    # helpers
    def mt(self, name, which=0):
        return self.m[name][which]

    def track(self, who, J, cam):
        """record a character's head (screen space) for speech bubbles."""
        x, y = cam.to_screen(*J["head"])
        self.heads[who] = (x, y, J["head_rad"] * cam.zoom)


class Episode:
    def __init__(self, shots, voice):
        self.shots = shots
        self.voice = voice
        self.starts = []
        self.cues = []
        t = 0.0
        for sh in shots:
            P = Planner(sh, voice)
            sh.plan(P)
            sh.dur = P.t + sh.tail
            sh.cues = P.cues
            self.starts.append(t)
            for c in P.cues:
                c = dict(c)
                c["t0"] += t
                if "t1" in c:
                    c["t1"] += t
                c["shot"] = len(self.starts) - 1
                self.cues.append(c)
            t += sh.dur
        self.duration = t
        self.nframes = int(math.ceil(self.duration * FPS))
        self._bubble_state = {}

    def shot_at(self, gt):
        lo, hi = 0, len(self.shots) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self.starts[mid] <= gt:
                lo = mid
            else:
                hi = mid - 1
        return lo

    def render(self, cx, gt):
        i = self.shot_at(gt)
        sh = self.shots[i]
        lt = gt - self.starts[i]
        sh.heads = {}
        cx.save()
        sh.draw(cx, lt)
        cx.restore()
        # transitions
        nxt = self.shots[i + 1] if i + 1 < len(self.shots) else None
        a = 0.0
        if sh.trans_in and sh.trans_in[0] == "dip":
            a = max(a, 1 - smooth(prog(lt, 0, sh.trans_in[1])))
        if nxt is not None and nxt.trans_in and nxt.trans_in[0] == "dip":
            d = nxt.trans_in[1]
            a = max(a, smooth(prog(lt, sh.dur - d, sh.dur)))
        if a > 0:
            cx.rectangle(0, 0, W, H)
            src(cx, (0, 0, 0, a))
            cx.fill()
        if sh.trans_in and sh.trans_in[0] in ("flash", "white"):
            fa = 1 - smooth(prog(lt, 0, sh.trans_in[1]))
            if fa > 0:
                cx.rectangle(0, 0, W, H)
                src(cx, (1, 1, 1, fa))
                cx.fill()
        if nxt is not None and nxt.trans_in and nxt.trans_in[0] == "white":
            d = nxt.trans_in[1] * 0.5
            fa = smooth(prog(lt, sh.dur - d, sh.dur))
            if fa > 0:
                cx.rectangle(0, 0, W, H)
                src(cx, (1, 1, 1, fa))
                cx.fill()
        # captions
        faces = list(sh.heads.values())
        for k, c in enumerate(self.cues):
            if c["type"] == "accent" and c["t0"] - 0.01 <= gt <= c["t1"] + captions.OUT_T:
                captions.draw_accent(cx, gt, c)
            elif c["type"] == "bubble" and c["t0"] - 0.01 <= gt <= c["t1"] + captions.OUT_T:
                head = sh.heads.get(c["who"])
                if k not in self._bubble_state:
                    # choose placement from the head position at the cue start, so every
                    # render worker (whatever frame it starts on) places the bubble identically
                    self._bubble_state[k] = self._initial_bubble_state(c)
                st = self._bubble_state[k]
                captions.draw_bubble(cx, gt, c, head, faces, st)

    def _initial_bubble_state(self, c):
        i = self.shot_at(c["t0"])
        sh = self.shots[i]
        scratch = cairo.ImageSurface(cairo.FORMAT_ARGB32, 64, 36)
        cx = cairo.Context(scratch)
        cx.scale(64 / W, 36 / H)
        sh.heads = {}
        sh.draw(cx, c["t0"] - self.starts[i])
        head = sh.heads.get(c["who"])
        faces = list(sh.heads.values())
        st = {}
        if head is not None:
            from .captions import place_bubble, render_text
            full, fw, fh, fpad = render_text(c["text"], c.get("size", 60))
            pw = fw - 2 * fpad + 60
            ph = (fh - 2 * fpad) + 36
            others = [f for f in faces if f is not head]
            mode, rect = place_bubble(head, pw, ph, others + [head], c.get("prefer"))
            st = {"mode": mode, "off": (rect[0] - head[0], rect[1] - head[1])}
        sh.heads = {}
        return st

    def summary(self):
        out = []
        for sh, st in zip(self.shots, self.starts):
            out.append(f"{st:7.2f}  {sh.dur:6.2f}  {sh.scene:4s} {type(sh).__name__}")
        return "\n".join(out)
