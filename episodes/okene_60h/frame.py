"""Per-frame state, shot base class, word-timing access and the caption system."""
import json
import math
import re

import cairo
import numpy as np

from cinecode import captions as capmod
from cinecode.core import FPS, H, W, Cam, clamp, ease_out, prog, smooth
from . import look

VOICE_JSON = "build/okene/voice.json"


class Voice:
    def __init__(self, path=VOICE_JSON):
        d = json.load(open(path))
        self.duration = d["duration"]
        self.words = d["words"]
        self.beats = d["beats"]

    def w(self, word, n=1, after=0.0):
        """start time of the n-th occurrence of `word` (case/punct-insensitive) after `after`."""
        k = 0
        key = re.sub(r"[^a-z0-9']", "", word.lower())
        for x in self.words:
            if x["t0"] < after:
                continue
            if re.sub(r"[^a-z0-9']", "", x["text"].lower()) == key:
                k += 1
                if k == n:
                    return x["t0"]
        raise KeyError(word)

    def wend(self, word, n=1, after=0.0):
        t0 = self.w(word, n, after)
        return next(x["t1"] for x in self.words if x["t0"] == t0)

    def b(self, beat):
        return self.beats[beat][0]


class Frame:
    def __init__(self, i, T, t):
        self.i, self.T, self.t = i, T, t
        self.alb = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        self.cx = cairo.Context(self.alb)
        self.add_s = None
        self._ax = None
        self.lights = look.Lights()
        self.fog = (0.02, 0.07, 0.08)
        self.fog_amt = 0.0
        self.depth_fog = None
        self.grade = ((0.005, 0.016, 0.02), (0.97, 1.0, 1.04), 0.92)
        self.bloom = 0.5
        self.vig = 0.55
        self.exposure = 1.0
        self.flash = 0.0
        self.flash_col = (1, 1, 1)
        self.black = 0.0
        self.shake = (0.0, 0.0)
        self.unlit = False

    @property
    def ax(self):
        if self._ax is None:
            self.add_s, self._ax = look.new_add()
        return self._ax

    def compose(self):
        alb = look.surf_to_rgb(self.alb)
        add = look.surf_to_rgb(self.add_s) if self.add_s is not None else None
        img = look.finish(alb, None if self.unlit else self.lights, add=add, fog=self.fog, fog_amt=self.fog_amt,
                          grade=self.grade, bloom_amt=self.bloom, vig=self.vig, frame_i=self.i,
                          exposure=self.exposure, depth_fog=self.depth_fog)
        img = look.flash(img, self.flash, self.flash_col)
        if self.black > 0:
            img *= (1 - clamp(self.black))
        return img


class Shot:
    t0 = 0.0
    t1 = 0.0
    punch = 0.0      # zoom-in punch on cut (0.04 = 4%)

    def __init__(self, t0, t1):
        self.t0, self.t1 = t0, t1

    @property
    def dur(self):
        return self.t1 - self.t0

    def cam(self, F):
        return Cam()

    def apply_cam(self, F, cam, ctx=None):
        """apply camera (+ cut punch + shake) to a cairo context."""
        ctx = ctx or F.cx
        z = 1 + self.punch * (1 - ease_out(prog(F.t, 0, 0.35)))
        c = Cam(cam.x - F.shake[0] / cam.zoom, cam.y - F.shake[1] / cam.zoom, cam.zoom * z, cam.rot)
        c.apply(ctx)
        return c

    def render(self, F):
        pass


# ------------------------------------------------------------------ captions
CAP_SIZE = 66
CAP_Y = int(H * 0.70)
MAX_CHARS = 13
_cap_cache = {}


def caption_chunks(words):
    chunks = []
    cur = []
    for k, w in enumerate(words):
        if cur:
            prev = cur[-1]
            txt = " ".join(x["text"] for x in cur + [w])
            if (re.search(r"[.,:;!?…]$", prev["text"]) or len(cur) >= 3 or len(txt) > MAX_CHARS
                    or w["t0"] - prev["t1"] > 0.25):
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        t0 = c[0]["t0"]
        end = c[-1]["t1"] + 0.18
        if i + 1 < len(chunks) and chunks[i + 1][0]["t0"] - c[-1]["t1"] < 0.45:
            end = chunks[i + 1][0]["t0"]
        out.append({"text": " ".join(x["text"] for x in c), "t0": t0, "t1": end})
    return out


def _cap_array(txt):
    if txt in _cap_cache:
        return _cap_cache[txt]
    surf, w, h, pad = capmod.render_text(txt, CAP_SIZE)
    surf.flush()
    a = np.ndarray((h, w, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1)).astype(np.float32) / 255
    rgb = a[:, :, 2::-1].copy()
    al = a[:, :, 3:4].copy()
    _cap_cache[txt] = (rgb, al, w, h)
    return _cap_cache[txt]


def draw_caption(img, chunk, T):
    rgb, al, w, h = _cap_array(chunk["text"])
    age = T - chunk["t0"]
    # quick, clean pop: 2 frames of 94%->100% scale + fade (no bounce)
    k = ease_out(prog(age, 0, 0.07))
    alpha = k * (1 - prog(T, chunk["t1"], chunk["t1"] + 0.05))
    if alpha <= 0:
        return img
    if k < 1:
        s = 0.94 + 0.06 * k
        from PIL import Image
        nw, nh = max(2, int(w * s)), max(2, int(h * s))
        rgb = np.asarray(Image.fromarray((rgb * 255).astype(np.uint8)).resize((nw, nh), Image.BILINEAR)) / 255.0
        al = np.asarray(Image.fromarray((al[:, :, 0] * 255).astype(np.uint8)).resize((nw, nh), Image.BILINEAR))[..., None] / 255.0
        w, h = nw, nh
    x0 = int(W / 2 - w / 2)
    y0 = int(CAP_Y - h / 2)
    xs0, ys0 = max(0, x0), max(0, y0)
    xs1, ys1 = min(W, x0 + w), min(H, y0 + h)
    sub_rgb = rgb[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
    sub_a = al[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0] * alpha
    reg = img[ys0:ys1, xs0:xs1]
    img[ys0:ys1, xs0:xs1] = reg * (1 - sub_a) + sub_rgb * alpha
    return img
