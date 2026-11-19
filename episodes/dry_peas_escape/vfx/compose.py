"""Composite the final Short from the ORIGINAL source frames.

The source picture is kept: backgrounds, guards, warden, camera, effects and timing are untouched.
Only the main prisoner is changed (head -> Just Needy's round white head and face; black/white striped
uniform -> orange, keeping the source's own shading and line work), the Turkish burned-in text is removed,
and the English captions/labels are set.

pass 1 (geometry):  python -m episodes.dry_peas_escape.vfx.compose geom
pass 2 (render):    python -m episodes.dry_peas_escape.vfx.compose render [--draft] [t0 t1]
stills:             python -m episodes.dry_peas_escape.vfx.compose stills T ...
"""
import json
import math
import multiprocessing as mp
import os
import subprocess
import sys
import time

import cairo
import cv2
import numpy as np

import episodes.dry_peas_escape  # noqa: F401  (vertical canvas for captions)
from cinecode import captions
from episodes.dry_peas_escape.vfx import textclean, track

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
WORK = os.environ.get("DRYPEAS_WORK", os.path.join(ROOT, "build", "dry_peas_vfx"))
FRAMES = os.path.join(WORK, "jpg")
MASKS = os.path.join(WORK, "masks")
GEOM = os.path.join(WORK, "geom.json")
SW, SH = 720, 1280           # source
OW, OH = 1080, 1920          # output
SC = OW / SW
FPS = 30
N_SRC = 2050

ORANGE = np.array([30, 122, 240], np.float32) / 255.0      # BGR of the uniform (#F07A1E)
SKIN_REF = np.array([150, 190, 236], np.float32)           # BGR of the source's skin in neutral light
OUTLINE = (0.16, 0.10, 0.07)                               # the source's dark-brown line colour

# ---------------------------------------------------------------- expressions (source time)
# eyes: open | half | closed | wide | tired ; mouth: smile | smirk | flat | o | grin | frown | tongue | drool
EXPR = [
    (0.0, 3.30, dict(eyes="half", brows="flat", mouth="smirk")),
    (3.30, 5.62, dict(eyes="half", brows="flat", mouth="smile")),
    (5.62, 8.00, dict(eyes="half", brows="flat", mouth="smirk")),
    (8.00, 10.45, dict(eyes="half", brows="flat", mouth="smile")),
    (10.45, 12.00, dict(eyes="closed", brows="up", mouth="smile")),
    (12.00, 14.00, dict(eyes="open", brows="skeptic", mouth="flat")),
    (14.00, 16.70, dict(eyes="half", brows="flat", mouth="flat")),
    (16.70, 18.75, dict(eyes="closed", brows="up", mouth="drool")),
    (18.75, 20.40, dict(eyes="half", brows="flat", mouth="smile")),
    (20.40, 21.50, dict(eyes="closed", brows="up", mouth="smile")),
    (26.60, 29.00, dict(eyes="half", brows="flat", mouth="flat")),
    (29.00, 31.00, dict(eyes="closed", brows="up", mouth="smile")),   # his tongue + spoon: source pixels
    (31.00, 31.60, dict(eyes="closed", brows="up", mouth="smile")),
    (31.60, 36.00, dict(eyes="open", brows="flat", mouth="smile")),
    (36.00, 39.20, dict(eyes="half", brows="flat", mouth="flat", tired=0.5)),
    (43.50, 46.45, dict(eyes="open", brows="flat", mouth="flat", tired=0.8)),
    (46.45, 54.00, dict(eyes="tired", brows="flat", mouth="flat", tired=1.0)),
    (54.00, 55.30, dict(eyes="open", brows="flat", mouth="o", tired=1.0)),
    (59.50, 61.80, dict(eyes="half", brows="flat", mouth="flat", tired=1.0)),
    (61.80, 62.70, dict(eyes="wide", brows="worried", mouth="frown", tired=1.0)),
    (65.70, 67.00, dict(eyes="wide", brows="up", mouth="o", tired=1.0)),
    (67.00, 67.62, dict(eyes="wide", brows="up", mouth="o", tired=1.0)),
    (67.62, 70.00, dict(eyes="closed", brows="up", mouth="smile", tired=1.0)),
]


def expr_at(t):
    for a, b, e in EXPR:
        if a <= t < b:
            return e
    return dict(eyes="open", brows="flat", mouth="smile")


# ---------------------------------------------------------------- masks
_seg_cache = {}


def seg_for(f):
    for name, (f0, f1, _, _) in track.SEGMENTS.items():
        if f0 <= f < f1 and os.path.exists(os.path.join(MASKS, f"{name}.npz")):
            return name
    return None


def masks_for(f):
    """(head, body) bool masks at source resolution, or (None, None)."""
    name = seg_for(f)
    if name is None:
        return None, None
    if name not in _seg_cache:
        _seg_cache.clear()
        try:
            _seg_cache[name] = track.load(MASKS, name)
        except Exception:          # being written right now
            return None, None
    f0, arr = _seg_cache[name]
    m = arr[f - f0]
    head = _clean(m[0], keep_largest=True)
    body = _clean(m[1] | m[2] | m[3]) & ~cv2.dilate(head.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    return head, body


def _clean(m, keep_largest=False):
    m = m.astype(np.uint8)
    if not m.any():
        return m.astype(bool)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        return m.astype(bool)
    if keep_largest:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        return lab == k
    keep = np.zeros(n, bool)
    big = st[1:, cv2.CC_STAT_AREA].max()
    keep[1:] = st[1:, cv2.CC_STAT_AREA] >= max(20, 0.03 * big)
    return keep[lab]


# ---------------------------------------------------------------- pass 1: geometry
EGG_RATIO = 0.80   # width / height of the source's head incl. cap


def head_geom(img, head):
    if head is None or head.sum() < 40:
        return None
    ys, xs = np.nonzero(head)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    cut_l, cut_r = x0 <= 1, x1 >= SW - 2
    cut_t, cut_b = y0 <= 1, y1 >= SH - 2
    if (cut_t or cut_b) and not (cut_l or cut_r):
        h_est = max(h, w / EGG_RATIO)
    else:
        h_est = h
    w_est = max(w, EGG_RATIO * h_est) if (cut_l or cut_r) else w
    cx = (x0 + x1) / 2
    if cut_l and not cut_r:
        cx = x1 - w_est / 2
    elif cut_r and not cut_l:
        cx = x0 + w_est / 2
    cy = (y0 + y1) / 2
    if cut_t and not cut_b:
        cy = y1 - h_est / 2
    elif cut_b and not cut_t:
        cy = y0 + h_est / 2
    R = 0.455 * h_est
    # face direction: dark features below the cap, inside the head
    er = max(2, int(0.07 * w_est))
    inner = cv2.erode(head.astype(np.uint8), np.ones((er, er), np.uint8)).astype(bool)
    inner[: int(y0 + 0.36 * h_est)] = False
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    dark = inner & (hsv[..., 2] < 75)
    fx = fy = None
    if dark.sum() > 6:
        dy, dx = np.nonzero(dark)
        fx = float(np.clip((dx.mean() - cx) / (0.5 * w_est), -0.9, 0.9))
        fy = float(np.clip((dy.mean() - cy) / (0.5 * h_est), -0.5, 0.6))
    # scene light from the source skin
    skin = inner & (hsv[..., 0] >= 3) & (hsv[..., 0] <= 25) & (hsv[..., 1] > 50) & (hsv[..., 2] > 60)
    light = None
    if skin.sum() > 15:
        med = np.median(img[skin].astype(np.float32), axis=0)
        light = [float(v) for v in np.clip(med / SKIN_REF, 0.2, 1.25)]
    return dict(cx=float(cx), cy=float(cy), R=float(R), fx=fx, fy=fy, light=light,
                box=[int(x0), int(y0), int(x1), int(y1)], area=int(head.sum()))


def geometry():
    out = {}
    for name, (f0, f1, _, _) in track.SEGMENTS.items():
        if not os.path.exists(os.path.join(MASKS, f"{name}.npz")):
            continue
        rows = {}
        for f in range(f0, f1):
            img = cv2.imread(os.path.join(FRAMES, f"{f:05d}.jpg"))
            head, body = masks_for(f)
            g = head_geom(img, head)
            if g:
                rows[f] = g
        # temporal smoothing within the segment (positions, size, face direction, light)
        fs = sorted(rows)
        # ghost masks: after he leaves the frame SAM can keep a tiny blob - drop frames whose head area
        # collapses against the recent frames
        for f in list(fs):
            prev = [rows[g]["area"] for g in range(f - 10, f) if g in rows]
            if prev and rows[f]["area"] < 0.2 * max(prev):
                del rows[f]
        fs = sorted(rows)
        # single-frame spikes (a bad mask) take their neighbours' mean; real fast moves are kept
        for f in fs:
            if f - 1 in rows and f + 1 in rows:
                a_, b_ = rows[f - 1], rows[f + 1]
                for k, tol in (("R", 0.22), ("cx", 0.35), ("cy", 0.35)):
                    nb = (a_[k] + b_[k]) / 2
                    ref = (a_["R"] + b_["R"]) / 2
                    if abs(a_[k] - b_[k]) < 0.5 * tol * ref and abs(rows[f][k] - nb) > tol * ref:
                        rows[f][k] = nb
        for key, win in (("cx", 1), ("cy", 1), ("R", 2), ("fx", 4), ("fy", 4)):
            vals = {f: rows[f][key] for f in fs if rows[f][key] is not None}
            for f in fs:
                near = [vals[g] for g in range(f - win, f + win + 1) if g in vals]
                if near:
                    rows[f][key + "_s"] = float(np.mean(near))
                else:
                    prev = [vals[g] for g in fs if g in vals and abs(g - f) < 30]
                    rows[f][key + "_s"] = float(np.mean(prev)) if prev else 0.0
        lights = [rows[f]["light"] for f in fs if rows[f]["light"]]
        seg_light = np.median(np.array(lights), axis=0).tolist() if lights else [0.9, 0.9, 0.9]
        for f in fs:
            near = [rows[g]["light"] for g in range(f - 6, f + 7) if g in rows and rows[g]["light"]]
            rows[f]["light_s"] = np.median(np.array(near), axis=0).tolist() if len(near) >= 3 else seg_light
        for f in fs:
            out[f] = rows[f]
        print(name, len(fs), "head frames", flush=True)
    json.dump({str(k): v for k, v in out.items()}, open(GEOM, "w"))
    return out


# ---------------------------------------------------------------- pass 2: render helpers
def recolor_uniform(img, body, light):
    """img: float32 BGR 0..1 (output res); body: bool mask (output res)."""
    if body is None or body.sum() < 30:
        return img
    ys, xs = np.nonzero(body)
    bh = ys.max() - ys.min() + 1
    k = int(np.clip(0.05 * bh, 7, 45)) | 1
    y0, y1 = max(0, ys.min() - k), min(OH, ys.max() + k + 1)
    x0, x1 = max(0, xs.min() - k), min(OW, xs.max() + k + 1)
    sub = img[y0:y1, x0:x1]
    m = body[y0:y1, x0:x1]
    L = sub.mean(axis=2)
    # white-stripe level = local lighting (per channel, so coloured light carries over)
    src_for_max = np.where(m[..., None], sub, 0).astype(np.float32)
    V = cv2.dilate(src_for_max, np.ones((k, k), np.uint8))
    Vl = V.mean(axis=2) + 1e-4
    rel = np.clip(L / Vl, 0, 1)
    new = ORANGE[None, None, :] * V * (0.90 + 0.10 * rel)[..., None]
    # keep the source's outline: dark pixels on the rim of the mask
    mu = m.astype(np.uint8)
    rim = mu.astype(bool) & ~cv2.erode(mu, np.ones((7, 7), np.uint8)).astype(bool)
    keep = rim & (L < 0.33)
    # hands: source skin -> Just Needy white
    hsv = cv2.cvtColor((sub * 255).astype(np.uint8), cv2.COLOR_BGR2HSV)
    skin = m & (hsv[..., 0] >= 3) & (hsv[..., 0] <= 25) & (hsv[..., 1] > 60) & (hsv[..., 2] > 70)
    white = np.clip(sub.max(axis=2, keepdims=True) * 1.12, 0, 1) * np.array(light, np.float32)[None, None, :] ** 0.3
    white = np.repeat(np.clip(white, 0, 1), 1, axis=2)
    out = sub.copy()
    sel = m & ~keep
    out[sel] = new[sel]
    out[skin & ~keep] = np.clip(np.broadcast_to(white, sub.shape)[skin & ~keep] * 0.97, 0, 1)
    # soft edge: blend 1px rim
    img[y0:y1, x0:x1] = out
    return img


def _cairo_from(img):
    """float BGR (OH,OW,3) -> cairo ARGB32 surface."""
    a = np.empty((OH, OW, 4), np.uint8)
    a[..., :3] = np.clip(img * 255, 0, 255).astype(np.uint8)
    a[..., 3] = 255
    s = cairo.ImageSurface.create_for_data(memoryview(a), cairo.FORMAT_ARGB32, OW, OH)
    return s, a


def draw_head(cx_, g, t, f):
    """Just Needy's head + face, lit like the shot."""
    from cinecode.core import circle, curve, ellipse, line
    X, Y, R = g["cx_s"] * SC, g["cy_s"] * SC, g["R_s"] * SC
    fx = g.get("fx_s", 0.0) or 0.0
    fy = g.get("fy_s", 0.0) or 0.0
    lb, lg, lr = g["light_s"]
    # keep him a WHITE head: only part of the shot's light level/tint is applied
    lum = max(0.05, (lr + lg + lb) / 3)
    level = 0.42 + 0.58 * min(1.0, lum) ** 0.7       # white in normal light, dimmer in dark shots
    lit = tuple(level * min(1.0, (c / lum) ** 0.35) for c in (lr, lg, lb))
    e = expr_at(t)
    # --- head ball: white, sphere shading in the scene's light
    grad = cairo.RadialGradient(X - 0.35 * R, Y - 0.40 * R, 0.1 * R, X, Y, 1.05 * R)
    base = [0.985 * c for c in lit]
    grad.add_color_stop_rgb(0, *[min(1, c * 1.02) for c in base])
    grad.add_color_stop_rgb(0.65, *base)
    grad.add_color_stop_rgb(1, *[c * 0.80 for c in base])
    cx_.new_sub_path()
    cx_.arc(X, Y, R, 0, 2 * math.pi)
    cx_.set_source(grad)
    cx_.fill()
    # outer light rim + dark brown outline (the source's character line style)
    cx_.new_sub_path()
    cx_.arc(X, Y, R + 0.035 * R, 0, 2 * math.pi)
    cx_.set_source_rgba(1.0 * lit[0], 0.96 * lit[1], 0.88 * lit[2], 0.85)
    cx_.set_line_width(0.035 * R)
    cx_.stroke()
    cx_.new_sub_path()
    cx_.arc(X, Y, R, 0, 2 * math.pi)
    oc = tuple(c * (0.6 + 0.4 * l) for c, l in zip(OUTLINE, lit))
    cx_.set_source_rgb(*oc)
    cx_.set_line_width(0.055 * R)
    cx_.stroke()
    # --- face
    ink = tuple(0.09 + 0.0 * l for l in lit)
    ox = fx * 0.42 * R
    oy = fy * 0.25 * R
    squeeze = 1 - 0.28 * abs(fx)
    ex, ey = 0.30 * R * squeeze, -0.06 * R + oy
    erx, ery = 0.10 * R, 0.155 * R
    eyes = e["eyes"]
    blink = (t * 1.7 + f * 0.0) % 3.3 < 0.12 and eyes in ("open", "half", "wide", "tired")
    if blink:
        eyes = "closed"
    lw = 0.045 * R
    for s in (-1, 1):
        x = X + ox + s * ex * (1 + 0.12 * fx * s)
        y = Y + ey
        if eyes in ("open", "wide", "half", "tired"):
            k = 1.18 if eyes == "wide" else 1.0
            ellipse(cx_, x, y, erx * k, ery * k)
            cx_.set_source_rgb(*ink)
            cx_.fill()
            ellipse(cx_, x - 0.3 * erx, y - 0.42 * ery, 0.3 * erx, 0.22 * ery)
            cx_.set_source_rgba(1, 1, 1, 0.9)
            cx_.fill()
            if eyes in ("half", "tired"):
                # upper lid: skin-coloured cap over the top half + lid line
                cx_.save()
                ellipse(cx_, x, y, erx * 1.15, ery * 1.15)
                cx_.clip()
                cx_.rectangle(x - 2 * erx, y - 2 * ery, 4 * erx, 2 * ery - 0.05 * ery)
                cx_.set_source_rgb(*base)
                cx_.fill()
                cx_.restore()
                line(cx_, [(x - erx * 1.15, y), (x + erx * 1.15, y)], ink, lw * 0.8)
            if eyes == "tired" or e.get("tired", 0) > 0.6:
                curve(cx_, (x - erx, y + ery * 1.35), (x - erx * 0.4, y + ery * 1.7), (x + erx * 0.4, y + ery * 1.7),
                      (x + erx, y + ery * 1.35), (*ink, 0.35), lw * 0.55)
        else:  # closed: happy arcs
            curve(cx_, (x - erx * 1.2, y + ery * 0.2), (x - erx * 0.5, y - ery * 0.75),
                  (x + erx * 0.5, y - ery * 0.75), (x + erx * 1.2, y + ery * 0.2), ink, lw)
    # brows
    by = Y + ey - 0.24 * R
    for s in (-1, 1):
        x = X + ox + s * ex * (1 + 0.12 * fx * s)
        inner, outer = x - s * 0.08 * R, x + s * 0.08 * R
        kind = e.get("brows", "flat")
        if kind == "up":
            pts = [(inner, by - 0.07 * R), (outer, by - 0.09 * R)]
        elif kind == "worried":
            pts = [(inner, by - 0.08 * R), (outer, by + 0.0 * R)]
        elif kind == "skeptic":
            pts = [(inner, by - (0.09 * R if s > 0 else 0)), (outer, by - (0.12 * R if s > 0 else -0.01 * R))]
        else:
            pts = [(inner, by), (outer, by - 0.015 * R)]
        line(cx_, pts, ink, lw * 1.05)
    # mouth
    mx, my = X + ox * 1.1, Y + 0.34 * R + oy
    mw = 0.18 * R
    mouth = e["mouth"]
    talking = False
    from episodes.dry_peas_escape.timing import WORDS
    for lid in ("L16",):
        ws = WORDS[lid]
        if ws[0][1] <= t <= ws[-1][2]:
            talking = True
    if talking:
        op = 0.5 + 0.5 * abs(math.sin(t * 15) * math.sin(t * 5.3 + 1))
        ellipse(cx_, mx, my + 0.02 * R, 0.09 * R, (0.04 + 0.08 * op) * R)
        cx_.set_source_rgb(0.23, 0.10, 0.10)
        cx_.fill_preserve()
        cx_.set_source_rgb(*ink)
        cx_.set_line_width(lw * 0.7)
        cx_.stroke()
    elif mouth in ("smile", "drool", "tongue"):
        curve(cx_, (mx - mw, my - 0.02 * R), (mx - 0.5 * mw, my + 0.09 * R), (mx + 0.5 * mw, my + 0.09 * R),
              (mx + mw, my - 0.02 * R), ink, lw)
        if mouth == "tongue":
            ph = abs(math.sin(t * 7))
            tx = mx + (0.10 + 0.12 * ph) * R * (1 if fx >= 0 else -1)
            cx_.save()
            cx_.translate(mx + 0.02 * R * (1 if fx >= 0 else -1), my + 0.05 * R)
            cx_.rotate(-0.35 if fx >= 0 else 0.35)
            from cinecode.core import rrect
            L = (0.16 + 0.10 * ph) * R
            rrect(cx_, -0.02 * R if fx >= 0 else -L, -0.045 * R, L + 0.02 * R, 0.09 * R, 0.045 * R)
            cx_.set_source_rgb(0.95, 0.47, 0.56)
            cx_.fill_preserve()
            cx_.set_source_rgb(*ink)
            cx_.set_line_width(lw * 0.6)
            cx_.stroke()
            cx_.restore()
        if mouth == "drool":
            u = 0.6 + 0.4 * math.sin(t * 2.0)
            dx = mx - 0.05 * R
            L = 0.55 * R * u
            cx_.move_to(dx - 0.02 * R, my + 0.05 * R)
            cx_.curve_to(dx - 0.025 * R, my + L * 0.7, dx - 0.01 * R, my + L, dx, my + L)
            cx_.curve_to(dx + 0.01 * R, my + L, dx + 0.025 * R, my + L * 0.7, dx + 0.02 * R, my + 0.05 * R)
            cx_.set_source_rgba(0.72, 0.88, 1.0, 0.95)
            cx_.fill_preserve()
            cx_.set_source_rgb(*ink)
            cx_.set_line_width(lw * 0.45)
            cx_.stroke()
            circle(cx_, dx, my + L + 0.03 * R, 0.035 * R)
            cx_.set_source_rgba(0.72, 0.88, 1.0, 0.95)
            cx_.fill()
    elif mouth == "smirk":
        curve(cx_, (mx - 0.8 * mw, my + 0.03 * R), (mx - 0.1 * mw, my + 0.07 * R), (mx + 0.5 * mw, my + 0.04 * R),
              (mx + mw, my - 0.04 * R), ink, lw)
    elif mouth == "flat":
        line(cx_, [(mx - 0.7 * mw, my + 0.02 * R), (mx + 0.7 * mw, my + 0.02 * R)], ink, lw)
    elif mouth == "frown":
        curve(cx_, (mx - 0.8 * mw, my + 0.06 * R), (mx - 0.4 * mw, my - 0.02 * R), (mx + 0.4 * mw, my - 0.02 * R),
              (mx + 0.8 * mw, my + 0.06 * R), ink, lw)
    elif mouth == "o":
        ellipse(cx_, mx, my + 0.03 * R, 0.07 * R, 0.10 * R)
        cx_.set_source_rgb(0.23, 0.10, 0.10)
        cx_.fill_preserve()
        cx_.set_source_rgb(*ink)
        cx_.set_line_width(lw * 0.8)
        cx_.stroke()


# ---------------------------------------------------------------- captions (English)
_chunks = None


def chunks():
    global _chunks
    if _chunks is None:
        from episodes.dry_peas_escape.episode import subtitle_chunks
        cs = subtitle_chunks()
        # keep a caption on screen until the next one (the source always shows a word, and our caption
        # sits where the Turkish one was)
        for i, c in enumerate(cs):
            nxt = cs[i + 1]["t0"] if i + 1 < len(cs) else c["t1"] + 0.6
            c["t1"] = max(c["t1"], nxt - 0.02) if nxt - c["t1"] < 2.5 else c["t1"] + 0.6
        _chunks = cs
    return _chunks


SUB_SIZE = 66
SUB_Y = int(0.766 * OH)


def draw_captions(cx_, t):
    from episodes.dry_peas_escape.episode import _wrap
    for c in chunks():
        if c["t0"] <= t < c["t1"]:
            txt = _wrap(c["text"], SUB_SIZE)
            s, w, h, pad = captions.render_text(txt, SUB_SIZE)
            cx_.set_source_surface(s, OW / 2 - w / 2, SUB_Y - h / 2)
            cx_.paint()
            break
    # translated on-screen gag labels at the source's positions and times
    if 13.95 <= t <= 16.45:
        s, w, h, pad = captions.render_text("[Prisoner:]", 34)
        cx_.set_source_surface(s, OW / 2 - w / 2, 350 * SC - h / 2)
        cx_.paint()
        s, w, h, pad = captions.render_text("*DOESN'T EVEN FLINCH*", 50)
        cx_.set_source_surface(s, OW / 2 - w / 2, 405 * SC - h / 2)
        cx_.paint()
    if 44.95 <= t <= 45.75:
        s, w, h, pad = captions.render_text("*WORST STASH EVER*", 50)
        cx_.set_source_surface(s, OW / 2 - w / 2, 835 * SC - h / 2)
        cx_.paint()


# ---------------------------------------------------------------- frame
_geom = None


def geom():
    global _geom
    if _geom is None:
        _geom = {int(k): v for k, v in json.load(open(GEOM)).items()} if os.path.exists(GEOM) else {}
    return _geom


def frame(fo):
    """output frame index -> uint8 BGRA (OH, OW, 4)."""
    t = fo / FPS
    f = min(fo, N_SRC - 1)
    img = cv2.imread(os.path.join(FRAMES, f"{f:05d}.jpg"))
    head, body = masks_for(f)
    g = geom().get(f)
    # 1. Turkish text out
    img, _ = textclean.clean(img, f / FPS)
    # 2. source head pixels not covered by the new (round) head: fill from surroundings
    if g is not None and head is not None:
        circ = np.zeros((SH, SW), np.uint8)
        cv2.circle(circ, (int(round(g["cx_s"])), int(round(g["cy_s"]))), max(1, int(g["R_s"] * 0.98)), 255, -1)
        left = (head & (circ == 0)).astype(np.uint8) * 255
        if left.any():
            left = cv2.dilate(left, np.ones((9, 9), np.uint8))
            left[circ > 0] = 0
            img = cv2.inpaint(img, left, 5, cv2.INPAINT_TELEA)
    # 3. upscale to native 1080x1920
    big = cv2.resize(img, (OW, OH), interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255.0
    if body is not None:
        bm = cv2.resize(body.astype(np.uint8) * 255, (OW, OH), interpolation=cv2.INTER_LINEAR) > 127
        light = g["light_s"] if g else [0.9, 0.9, 0.9]
        big = recolor_uniform(big, bm, light)
    occ = None
    mode = next((m for a, b, m in OCCLUDER_SHOTS if a <= t < b), None)
    if g is not None and head is not None and head.any() and mode:
        occ = occluders(head, g, img, mode)
        if occ is not None:
            occ_big = cv2.resize(occ.astype(np.uint8) * 255, (OW, OH), interpolation=cv2.INTER_LINEAR)
            occ_pix = big.copy()
    surf, arr = _cairo_from(big)
    cx_ = cairo.Context(surf)
    if g is not None:
        draw_head(cx_, g, t, f)
    surf.flush()
    if occ is not None:
        a = (occ_big.astype(np.float32) / 255.0)[..., None]
        arr[..., :3] = (arr[..., :3] * (1 - a) + np.clip(occ_pix * 255, 0, 255) * a).astype(np.uint8)
        surf.mark_dirty()
    draw_captions(cx_, t)
    surf.flush()
    return arr


# shots where something really is in front of the prisoner's head (cell bars, the spoon, the bunny)
OCCLUDER_SHOTS = [(14.0, 16.7, "red"), (29.0, 31.0, "lick"), (31.6, 36.0, "bars"), (43.5, 46.5, "bars"),
                  (59.5, 60.4, "bars"), (66.9, 67.62, "pink"), (67.62, 70.0, "bunny")]


def occluders(head, g, img, mode):
    """pixels of objects in front of the source head: 'hull' = inside the head's outline but not head;
    'red' = the sausage (red) inside the new head's disc."""
    hu = head.astype(np.uint8)
    disc = np.zeros_like(hu)
    cv2.circle(disc, (int(round(g["cx_s"])), int(round(g["cy_s"]))), int(g["R_s"] * 1.06), 1, -1)
    if mode == "red":
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        red = ((hsv[..., 0] <= 12) | (hsv[..., 0] >= 170)) & (hsv[..., 1] > 110) & (hsv[..., 2] > 90)
        red &= disc > 0
        if red.sum() < 20:
            return None
        n, lab, st, _ = cv2.connectedComponentsWithStats(red.astype(np.uint8), 8)
        if n <= 1:
            return None
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))     # the sausage = the largest red blob
        if st[k, cv2.CC_STAT_WIDTH] < 0.35 * g["R_s"]:
            return None
        m = lab == k
        return cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    cnts, _ = cv2.findContours(hu, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    hull = np.zeros_like(hu)
    cv2.drawContours(hull, [cv2.convexHull(np.vstack(cnts))], -1, 1, -1)
    hull = cv2.erode(hull, np.ones((5, 5), np.uint8))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    H_, S_, V_ = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    notme = (hu == 0) & (disc > 0)
    pink = ((H_ >= 150) | (H_ <= 4)) & (S_ > 70) & (V_ > 110)
    if mode == "lick":          # his own tongue (pink) and the spoon (tan) from the source
        tan = (H_ >= 6) & (H_ <= 24) & (S_ > 70) & (V_ > 90)
        cand = notme & (pink | tan)
        minar = 40
    elif mode == "pink":        # the pink sparkle
        cand = notme & (H_ >= 140) & (H_ <= 175) & (S_ > 60) & (V_ > 100)
        minar = 25
    elif mode == "bunny":       # white bunny + pink heart, inside the old head outline
        white = (S_ < 45) & (V_ > 185)
        cand = notme & (hull > 0) & (white | pink)
        minar = 40
    else:                       # cell bars: long thin dark verticals
        cand = (hull > 0) & (hu == 0) & (V_ < 120) & (S_ < 120)
        minar = 25
    if not cand.any():
        return None
    n, lab, st, _ = cv2.connectedComponentsWithStats(cand.astype(np.uint8), 8)
    keep = np.zeros(n, bool)
    for k in range(1, n):
        a, w, h = st[k, cv2.CC_STAT_AREA], st[k, cv2.CC_STAT_WIDTH], st[k, cv2.CC_STAT_HEIGHT]
        if a < minar:
            continue
        if mode == "bars" and not (h > 0.7 * g["R_s"] and w < 0.45 * g["R_s"]):
            continue
        keep[k] = True
    m = keep[lab]
    m &= disc > 0
    return cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) if m.any() else None


def stills(ts, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ps = []
    for t in ts:
        a = frame(int(round(t * FPS)))
        p = os.path.join(out_dir, f"vfx_{t:06.2f}.png")
        cv2.imwrite(p, a[..., :3])
        ps.append(p)
    return ps


def _worker(args):
    a, b, path, scale = args
    w, h = int(OW * scale) // 2 * 2, int(OH * scale) // 2 * 2
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r",
           str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium" if scale == 1 else "veryfast", "-crf",
           "17" if scale == 1 else "26", "-pix_fmt", "yuv420p", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(a, b):
        fr = frame(i)
        if scale != 1:
            fr = cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA)
        pr.stdin.write(fr.tobytes())
    pr.stdin.close()
    pr.wait()
    return path


def render(n_frames, out_path, draft=False, workers=4, f0=0, f1=None):
    f1 = n_frames if f1 is None else f1
    os.makedirs(WORK, exist_ok=True)
    n = f1 - f0
    k = workers * 4
    step = (n + k - 1) // k
    jobs = [(f0 + i * step, min(f1, f0 + (i + 1) * step), os.path.join(WORK, f"part_{i:03d}.mp4"),
             0.5 if draft else 1.0) for i in range(k) if f0 + i * step < f1]
    t = time.time()
    with mp.Pool(workers) as pool:
        for i, _ in enumerate(pool.imap(_worker, jobs)):
            print(f"  chunk {i + 1}/{len(jobs)}  {time.time() - t:.0f}s", flush=True)
    lst = os.path.join(WORK, "parts.txt")
    with open(lst, "w") as fh:
        for j in jobs:
            fh.write(f"file '{j[2]}'\n")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    out_path], check=True)
    return out_path


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "geom":
        geometry()
    elif cmd == "stills":
        for p in stills([float(a) for a in sys.argv[2:]], os.path.join(WORK, "stills")):
            print(p)
