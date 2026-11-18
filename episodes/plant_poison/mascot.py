"""The Just Needy blue-hoodie mascot, built from the official reference art
(assets/characters/just_needy_mascot.png, bust only).

prepare():  cut the character from its white background (flood fill from the border, clean
            dark anti-aliased rim), lift the face features (eyes / brows / mouth) onto their own
            layers and repaint the bare head, and extend the hoodie downward (the extension is
            what stands behind the tobacco plants, so only its top shows).
render():   draw one animation frame at art resolution: breathing, a small head turn (the face
            features slide/tilt over the round head), eye glances and blinks.
"""
import functools

import cv2
import numpy as np

ART = "assets/characters/just_needy_mascot.png"
EXT = 1500          # px of hoodie added below the bust (art resolution)
FACE_BOX = (190, 650, 450, 925)   # y0, y1, x0, x1: contains only eyes, brows and mouth
HEAD_C = (628.0, 440.0)           # head centre (art px), used as the tilt pivot


@functools.lru_cache(maxsize=None)
def prepare():
    rgb = cv2.cvtColor(cv2.imread(ART), cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    lum = rgb.astype(np.float32).mean(2)
    # background = near-white region connected to the top/left/right border
    near_white = (rgb.min(2) > 232).astype(np.uint8)
    ff = np.zeros((h + 2, w + 2), np.uint8)
    bg = np.zeros((h, w), np.uint8)
    for seed in [(0, 0), (w - 1, 0), (0, h // 2), (w - 1, h // 2)]:
        if near_white[seed[1], seed[0]] and not bg[seed[1], seed[0]]:
            m = near_white.copy()
            cv2.floodFill(m, ff, seed, 2)
            bg |= (m == 2).astype(np.uint8)
            ff[:] = 0
    alpha = 1.0 - bg.astype(np.float32)
    # rim: pixels near the background take black ink with alpha from darkness (no white fringe)
    rim = (cv2.dilate(bg, np.ones((5, 5), np.uint8)) > 0) & (bg == 0)
    out = np.dstack([rgb.astype(np.float32) / 255, alpha])
    dark = np.clip((255 - lum) / 200, 0, 1)
    out[rim, :3] = 0.0
    out[rim, 3] = dark[rim]
    # face features -> own layers; repaint the bare head
    y0, y1, x0, x1 = FACE_BOX
    feat = np.zeros((h, w), np.uint8)
    feat[y0:y1, x0:x1] = (lum[y0:y1, x0:x1] < 170)
    n, lab, st, _ = cv2.connectedComponentsWithStats(feat, 8)
    # keep only blobs fully inside the box (the head outline grazes its corners)
    inside = [i for i in range(1, n) if st[i, 0] > x0 + 1 and st[i, 1] > y0 + 1 and
              st[i, 0] + st[i, 2] < x1 - 1 and st[i, 1] + st[i, 3] < y1 - 1 and st[i, 4] > 30]
    feat = np.isin(lab, inside).astype(np.uint8)
    order = sorted(inside, key=lambda i: -st[i, 4])
    eyes = sorted(order[:2], key=lambda i: st[i, 0])      # two big filled ovals, left->right
    ink = np.clip((235 - lum) / 200, 0, 1) * (cv2.dilate(feat, np.ones((5, 5), np.uint8)) > 0)
    def layer(ids):
        m = np.isin(lab, ids).astype(np.uint8)
        m = cv2.dilate(m, np.ones((5, 5), np.uint8)) > 0
        L = np.zeros((h, w, 4), np.float32)
        L[..., 3] = ink * m
        return L
    eyeL, eyeR = layer([eyes[0]]), layer([eyes[1]])
    lines = layer([i for i in order if i not in eyes])
    eye_c = [tuple(st[i, :2] + st[i, 2:4] / 2) for i in eyes]
    hole = (cv2.dilate(feat, np.ones((9, 9), np.uint8)) * 255)
    bare = cv2.inpaint(rgb, hole, 9, cv2.INPAINT_TELEA)
    out[..., :3] = np.where(hole[..., None] > 0, bare.astype(np.float32) / 255, out[..., :3])
    # extend the hoodie: repeat the last rows (arms + torso continue straight down)
    last = out[h - 6:h - 2]
    ext = np.repeat(last.mean(0, keepdims=True), EXT, 0)
    full = np.concatenate([out[:h - 2], ext], 0)
    pad = lambda L: np.concatenate([L[:h - 2], np.zeros((EXT, w, 4), np.float32)], 0)
    return dict(base=full, eyeL=pad(eyeL), eyeR=pad(eyeR), lines=pad(lines), eye_c=eye_c, size=full.shape[:2])


def _over(dst, src):
    a = src[..., 3:4]
    dst[..., :3] = src[..., :3] * a + dst[..., :3] * (1 - a)
    dst[..., 3:4] = a + dst[..., 3:4] * (1 - a)


def _warp(L, M, shape):
    return cv2.warpAffine(L, M, (shape[1], shape[0]), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))


def render(face_dx=0.0, face_dy=0.0, tilt=0.0, eye_dx=0.0, eye_dy=0.0, blink=0.0):
    """One frame at art resolution, RGBA float32. Offsets in art px, tilt in degrees,
    blink 0 (open) .. 1 (closed)."""
    P = prepare()
    out = P["base"].copy()
    shape = out.shape[:2]
    R = cv2.getRotationMatrix2D(HEAD_C, tilt, 1.0)
    R[:, 2] += (face_dx, face_dy)
    ink = np.zeros_like(out)
    lines = _warp(P["lines"], R, shape)
    ink[..., 3] = np.maximum(ink[..., 3], lines[..., 3])
    for key, (cx, cy) in zip(("eyeL", "eyeR"), P["eye_c"]):
        sy = max(0.08, 1.0 - blink)
        E = np.array([[1, 0, eye_dx], [0, sy, eye_dy + cy * (1 - sy)]], np.float32)
        E3 = np.vstack([E, [0, 0, 1]])
        M = (np.vstack([R, [0, 0, 1]]) @ E3)[:2]
        e = _warp(P[key], M.astype(np.float32), shape)
        ink[..., 3] = np.maximum(ink[..., 3], e[..., 3])
    ink[..., :3] = 0.04
    _over(out, ink)
    return out
