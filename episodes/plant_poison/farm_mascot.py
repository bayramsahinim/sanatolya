"""Place the animated mascot into the farm shot (source frames 412-632), behind the back row of
tobacco plants, to the right of the farmer.

* Camera: the shot slowly pulls back. Frame-to-frame affine ECC (farmer/can/spray area masked
  out) is chained into A_k: frame-k coords -> reference-frame (416) coords.
* Occlusion (in reference coords): plants (green + their ink outlines, from a temporal-median
  plate of the stabilised shot) and anything moving in front (watering can, falling water:
  |stabilised frame - plate|) are kept in front of the mascot.
* Look: the mascot is shaded with the shot's horizontal vignette, given matching grain and a
  touch of softness, and fades in/out with the shot's own cross-dissolves.
"""
import os

import cv2
import numpy as np

from episodes.plant_poison import mascot

REF = 416
FIRST, LAST = 412, 632            # frames touched (cross-dissolves at 412-414 and 629-632)
# opacity follows the shot's dissolves
ALPHA = {412: 0.35, 413: 0.8, 629: 0.75, 630: 0.45, 631: 0.2, 632: 0.0}
# placement in reference-frame coords (720x1280 source)
CX, HEAD_TOP, HEAD_D = 610.0, 670.0, 125.0
ART_HEAD_D, ART_HEAD_TOP = 792.0, 48.0
CACHE = "build/plant_poison_farm_track.npz"


def _gray(f, s=0.25):
    return cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), None, fx=s, fy=s).astype(np.float32)


def analyse(frames):
    """Tracking, plate and plant mask (cached)."""
    if os.path.exists(CACHE):
        d = np.load(CACHE)
        return {k: d[k] for k in d.files}
    s = 0.25
    A = {REF: np.eye(3)}
    def step(k_from, k_to):  # matrix mapping k_to coords -> k_from coords
        a, b = _gray(frames[k_from]), _gray(frames[k_to])
        valid = np.ones(b.shape, np.uint8)
        valid[int(500 * s):int(1060 * s), int(200 * s):int(560 * s)] = 0
        M = np.eye(2, 3, dtype=np.float32)
        try:
            _, M = cv2.findTransformECC(b, a, M, cv2.MOTION_AFFINE,
                                        (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 80, 1e-6), valid, 3)
        except cv2.error:
            pass
        M = M.astype(np.float64)
        M[:, 2] /= s
        return np.vstack([M, [0, 0, 1]])
    for k in range(REF + 1, 630):          # forward: A_k = A_{k-1} @ M_k
        A[k] = A[k - 1] @ step(k - 1, k)
    for k in range(REF - 1, 414 - 1, -1):  # backward to the end of the dissolve
        A[k] = A[k + 1] @ step(k + 1, k)
    for k in range(FIRST, 414):
        A[k] = A[414]
    for k in range(630, LAST + 1):         # dissolve out: hold the last solid frame's camera
        A[k] = A[629]
    # stabilised temporal-median plate (static scene without moving parts)
    stab = [cv2.warpAffine(frames[k], np.linalg.inv(A[k])[:2], (720, 1280),
                           flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
            for k in range(420, 628, 3)]
    plate = np.median(np.stack(stab), 0).astype(np.uint8)
    b, g, r = [plate[..., i].astype(np.int16) for i in range(3)]
    green = ((g - r > 16) & (g - b > 16)).astype(np.uint8)
    green = cv2.morphologyEx(green, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    lum = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
    ink = (lum < 95).astype(np.uint8) & cv2.dilate(green, np.ones((13, 13), np.uint8))
    plants = cv2.dilate(green | ink, np.ones((3, 3), np.uint8))
    # the mounds are solid: from each column's first plant pixel (below the horizon) downward,
    # everything is in front of the mascot (fills pale leaf centres / pest dots)
    solid = np.zeros_like(plants)
    for x in range(720):
        ys = np.nonzero(plants[860:, x])[0]
        if len(ys):
            solid[860 + ys[0]:, x] = 1
    plants = plants | solid
    # the watering can (grey body + ink) in the static plate also stays in front
    pb, pg, pr = [plate[..., i].astype(np.int16) for i in range(3)]
    grey = ((np.abs(pr - pg) < 10) & (np.abs(pg - pb) < 12) & (lum > 95) & (lum < 175)).astype(np.uint8)
    can = cv2.dilate(grey, np.ones((5, 5), np.uint8)) & ((lum < 175) & ~((pg - pr > 16))).astype(np.uint8)
    can[:, 560:] = 0
    can[:700] = 0
    can[900:] = 0
    plants = plants | cv2.morphologyEx(can, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    # vignette: sky luminance per column on a row above the farmer's head
    sky = cv2.GaussianBlur(lum.astype(np.float32), (0, 0), 6)[520]
    vign = np.clip(sky / sky[300:420].mean(), 0.75, 1.0)
    # strong static edges of the plate (horizon, outlines): ignore 1-px drift there
    gx = cv2.Sobel(lum.astype(np.float32), cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(lum.astype(np.float32), cv2.CV_32F, 0, 1)
    edges = cv2.dilate((np.hypot(gx, gy) > 40).astype(np.uint8), np.ones((5, 5), np.uint8))
    Ak = np.stack([A[k] for k in range(FIRST, LAST + 1)])
    out = dict(A=Ak, plate=plate, plants=plants, vign=vign, edges=edges)
    np.savez_compressed(CACHE, **out)
    return out


def front_mask(frame, k, an):
    """Foreground (in front of the mascot) in reference coords, float 0..1, 720x1280."""
    A = an["A"][k - FIRST]
    m = an["plants"].astype(np.float32)
    if 415 <= k <= 628:
        stab = cv2.warpAffine(frame, np.linalg.inv(A)[:2], (720, 1280),
                              flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
        d = np.abs(stab.astype(np.int16) - an["plate"].astype(np.int16)).max(2)
        dyn = (d > 24).astype(np.uint8) & (1 - an["edges"])
        dyn = cv2.morphologyEx(dyn, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        # drop thin horizontal streaks (layer drift along the horizon), keep drops / can
        n, lab, st, _ = cv2.connectedComponentsWithStats(dyn, 8)
        bad = [i for i in range(1, n) if st[i, 2] > 10 and st[i, 2] > 3 * st[i, 3]]
        if bad:
            dyn[np.isin(lab, bad)] = 0
        dyn = cv2.dilate(dyn, np.ones((3, 3), np.uint8))
        m = np.maximum(m, dyn.astype(np.float32))
    return cv2.GaussianBlur(m, (3, 3), 0)


# ------------------------------------------------------------------ animation
def _smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


# poses: (face_dx, face_dy, tilt, eye_dx, eye_dy) in art px / degrees
POSES = {
    "plants": (-16, 8, -2.5, -12, 14),
    "farmer": (-30, -2, 0.5, -20, -4),
    "water": (-20, 10, -3.5, -14, 20),
    "front": (0, 0, 0, 0, 0),
}
# (time since the shot appears [s], pose); 0.35 s eased moves between holds
TIMELINE = [(0.0, "plants"), (2.1, "farmer"), (3.9, "water"), (6.6, "farmer"), (8.4, "plants")]
BLINKS = [1.5, 4.9, 7.6]


def pose_at(t):
    cur = POSES[TIMELINE[0][1]]
    for i, (t0, name) in enumerate(TIMELINE):
        if t >= t0:
            prev = POSES[TIMELINE[i - 1][1]] if i else POSES[name]
            w = _smooth((t - t0) / 0.35)
            cur = tuple(p + (q - p) * w for p, q in zip(prev, POSES[name]))
    blink = 0.0
    for b in BLINKS:
        dt = abs(t - b)
        if dt < 0.09:
            blink = max(blink, 1 - dt / 0.09)
    return cur, blink


def draw(frame_out, src_frame, k, t, an, scale_out=1.5, seed=0):
    """Composite the mascot into an output frame (BGR uint8, 1080x1920) in place.
    k = source frame index, t = seconds since the shot appeared (drives the animation)."""
    if not (FIRST <= k <= LAST):
        return
    alpha_shot = ALPHA.get(k, 1.0)
    if alpha_shot <= 0:
        return
    (fdx, fdy, tilt, edx, edy), blink = pose_at(t)
    art = mascot.render(fdx, fdy, tilt, edx, edy, blink)
    s = HEAD_D / ART_HEAD_D * scale_out
    breath = np.sin(2 * np.pi * t / 3.4)
    sx, sy = s, s * (1 + 0.006 * breath)
    small = cv2.resize(art, None, fx=sx, fy=sy, interpolation=cv2.INTER_AREA)
    H, W = frame_out.shape[:2]
    canvas = np.zeros((H, W, 4), np.float32)
    x0 = int(round(CX * scale_out - small.shape[1] / 2 + 1.2 * np.sin(2 * np.pi * t / 5.1)))
    y0 = int(round(HEAD_TOP * scale_out - ART_HEAD_TOP * sy - 2.0 * breath))
    h = min(small.shape[0], H - y0)
    w = min(small.shape[1], W - x0)
    canvas[y0:y0 + h, x0:x0 + w] = small[:h, :w]
    # match the shot: vignette shading, softness, grain
    vign = cv2.resize(an["vign"][None, :].astype(np.float32), (W, 1))[0]
    canvas[..., :3] *= vign[None, :, None]
    canvas = cv2.GaussianBlur(canvas, (0, 0), 0.7)
    rng = np.random.default_rng(seed)
    canvas[..., :3] += rng.normal(0, 0.012, canvas[..., :3].shape).astype(np.float32)
    # occlusion in reference coords
    fm = cv2.resize(front_mask(src_frame, k, an), (W, H), interpolation=cv2.INTER_LINEAR)
    canvas[..., 3] *= (1 - fm) * alpha_shot
    # camera: reference -> frame k  (dst(x) = canvas(A_k x)), conjugated to output scale
    S = np.diag([scale_out, scale_out, 1.0])
    A = S @ an["A"][k - FIRST] @ np.linalg.inv(S)
    warped = cv2.warpAffine(canvas, A[:2], (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                            borderValue=(0, 0, 0, 0))
    a = np.clip(warped[..., 3:4], 0, 1)
    rgb = np.clip(warped[..., [2, 1, 0]], 0, 1) * 255  # art is RGB -> frame BGR
    frame_out[:] = (rgb * a + frame_out.astype(np.float32) * (1 - a)).astype(np.uint8)
