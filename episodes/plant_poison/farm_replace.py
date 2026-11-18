"""Farm shot (source frames 412-645): the farmer is replaced by the official Just Needy
character, who holds the watering can and waters the plants himself.

Pipeline (all scene work in the stabilised reference frame 416, camera from farm_mascot):
  * background without the farmer, his can and the original spray: farm_bg.build
  * the can's motion is read from the original (ECC on the can region): hold until frame 529,
    a 34 deg tilt over ~11 frames, pouring to the end of the shot. The redrawn can follows that
    angle curve, held by the character's hand (it rises slightly as he tilts it).
  * entry (412-413, dissolve from the leaf shot): the change is added with the dissolve weight.
  * exit: 630 is a dissolve into a wider framing (631-645) where the farmer stands holding
    the can upright and fades out (sky regrades beige -> grey, a rusty can fades in). The
    character follows the same framing (affine fit per frame) and the farmer's measured
    opacity; the farmer is removed with a colour-matched background.
"""
import math
import os

import cairo
import cv2
import numpy as np

from episodes.plant_poison import farm_bg, farm_mascot, jn_character as J

REF = 416
FIRST, LAST = 412, 645
POUR_END = 629          # last frame of the farm framing
NEW0, NEW1 = 630, 645   # wider framing (farmer fading out); 630-633 also dissolve from 629
DISS = (630, 631, 632, 633)
CACHE = "build/plant_poison_farm_replace.npz"
FPS_SRC = 24.0

# character layout in reference coords (720x1280 source)
HEAD_C = (285.0, 656.0)
D = 160.0
GRIP_HOLD = (430.0, 790.0)
GRIP_RAISE = (6.0, -14.0)     # hand rises a little as the can tilts
GROUND_WATER = 955.0          # mound tops under the spout


def _gray(f, s):
    return cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), None, fx=s, fy=s).astype(np.float32)


def _ecc(tmpl, img, init, motion=cv2.MOTION_AFFINE, mask=None, gauss=3):
    try:
        cc, M = cv2.findTransformECC(tmpl, img, init.copy(), motion,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 150, 1e-7), mask, gauss)
        return cc, M
    except cv2.error:
        return -1.0, init


def analyse(frames):
    """frames: list of all source frames (BGR 720x1280). Cached."""
    if os.path.exists(CACHE):
        d = np.load(CACHE)
        out = {k: d[k] for k in d.files}
        set_ref(frames, out)
        return out
    an = farm_mascot.analyse(frames)
    A = an["A"]                       # frame k -> ref, k in [412, 632]
    def stab(k):
        Ak = A[min(k, farm_mascot.LAST) - farm_mascot.FIRST]
        return cv2.warpAffine(frames[k], np.linalg.inv(Ak)[:2], (720, 1280),
                              flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    bg, zone = farm_bg.build(an["plate"])
    ref = stab(REF)
    # farmer (+ his can) silhouette in ref coords, hold pose
    diff = np.abs(ref.astype(np.int16) - bg.astype(np.int16)).max(2) > 14
    box = np.zeros_like(diff)
    box[520:1052, 225:525] = True
    fm = (diff & box).astype(np.uint8)
    fm = cv2.morphologyEx(fm, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(fm, 8)
    keep = [i for i in range(1, n) if st[i, 4] > 400]
    fm = np.isin(lab, keep).astype(np.uint8)
    fm = cv2.dilate(fm, np.ones((7, 7), np.uint8))
    fm = fm & (1 - farm_bg.mounds(an["plate"]))       # live plants stay live (pest dots vanish)
    # can angle curve (ECC on the can region, relative to frame 420)
    s, PAD = 1.0, 60
    y0, y1, x0, x1 = 735, 860, 340, 530
    can_m = np.zeros((1280, 720), np.uint8)
    can_m[y0 + 10:y1 - 5, x0 + 30:x1] = 1
    cv2.circle(can_m, (378, 765), 26, 0, -1)          # farmer's hand
    sub = lambda img: cv2.GaussianBlur(cv2.cvtColor(img[y0 - PAD:y1 + PAD, x0 - PAD:x1 + PAD], cv2.COLOR_BGR2GRAY)
                                       .astype(np.float32), (0, 0), 1.0)
    tmpl = sub(stab(420))
    tm = np.ascontiguousarray(can_m[y0 - PAD:y1 + PAD, x0 - PAD:x1 + PAD])
    ang = np.zeros(LAST + 1)
    M = np.eye(2, 3, dtype=np.float32)
    for k in range(420, POUR_END + 1):
        _, M = _ecc(sub(stab(k)), tmpl, M, cv2.MOTION_EUCLIDEAN, tm)
        Mi = cv2.invertAffineTransform(M)
        ang[k] = math.degrees(math.atan2(Mi[1, 0], Mi[0, 0]))
    ang[:420] = ang[420]
    # dissolve weights (farm framing 629 -> wider framing, by 634), farmer areas excluded
    f32 = lambda x: x.astype(np.float32)
    Mold = np.linalg.inv(A[POUR_END - farm_mascot.FIRST])
    excl = cv2.warpAffine(cv2.dilate(fm, np.ones((41, 41), np.uint8)), Mold[:2], (720, 1280),
                          flags=cv2.INTER_NEAREST)
    B = np.zeros((LAST + 1, 3, 3))
    sc = 0.5
    init = np.array([[0.897, 0, 34.3 * sc], [0, 0.896, 41.9 * sc]], np.float32)
    _, Mm = _ecc(_gray(ref, sc), _gray(frames[634], sc), init, gauss=5)
    B634 = Mm.astype(np.float64); B634[:, 2] /= sc
    excl |= cv2.warpAffine(cv2.dilate(fm, np.ones((41, 41), np.uint8)), B634, (720, 1280),
                           flags=cv2.INTER_NEAREST)
    keep = excl == 0
    wts = np.ones(LAST + 1)
    pure = {}
    for k in DISS:
        f_, a_, b_ = [f32(x)[keep] for x in (frames[k], frames[POUR_END], frames[634])]
        wts[k] = float(np.clip(((f_ - a_) * (b_ - a_)).sum() / max(((b_ - a_) ** 2).sum(), 1e-6), 0.05, 1))
        pure[k] = np.clip((f32(frames[k]) - (1 - wts[k]) * f32(frames[POUR_END])) / wts[k], 0, 255).astype(np.uint8)
    newf = lambda k: pure.get(k, frames[k])
    # wider framing: ref -> frame k (affine), per frame (on the pure new-framing image)
    for k in range(NEW1, NEW0 - 1, -1):
        _, Mm = _ecc(_gray(ref, sc), _gray(newf(k), sc), init, gauss=5)
        init = Mm
        Mm = Mm.astype(np.float64)
        Mm[:, 2] /= sc
        B[k] = np.vstack([Mm, [0, 0, 1]])
    # farmer opacity in the wider framing + colour-matched clean background per frame
    g = np.zeros(LAST + 1)
    for k in range(NEW0, NEW1 + 1):
        clean, farmer_c = _clean_new(newf(k), bg, ref, fm, B[k])
        mk = cv2.warpAffine(cv2.erode(fm, np.ones((9, 9), np.uint8)), B[k][:2], (720, 1280),
                            flags=cv2.INTER_NEAREST).astype(bool)
        f, c, F = [x.astype(np.float32)[mk] for x in (newf(k), clean, farmer_c)]
        g[k] = float(np.clip(((f - c) * (F - c)).sum() / max(((F - c) ** 2).sum(), 1e-6), 0, 1))
    # dissolve in (leaf -> farm)
    def w_of(f, a, b):
        f, a, b = [x.astype(np.float32) for x in (f, a, b)]
        return float(np.clip(((f - a) * (b - a)).sum() / max(((b - a) ** 2).sum(), 1e-6), 0, 1))
    for k in (412, 413):
        wts[k] = w_of(frames[k], frames[411], frames[414])
    g = np.clip((g - 0.05) / 0.95, 0, 1)          # remove the estimator's noise floor
    g[640:] = 0.0                                  # the farmer is gone by 640 in the original
    g[NEW0:634] = np.maximum(g[NEW0:634], g[634])
    out = dict(A=A, bg=bg, zone=zone.astype(np.uint8), farmer=fm, ang=ang, B=B, g=g, w=wts,
               plate_new=frames[NEW1].copy())
    np.savez_compressed(CACHE, **out)
    set_ref(frames, out)
    return out


def _clean_new(frame, bg, ref, fm, Bk, plate_new=None, Bplate=None):
    """Wider framing: the farmer-free background in frame k colours.
    With plate_new (frame 645, farmer gone): that plate, camera-matched, plus per-row colour
    offsets measured beside the farmer (the sky regrade sweeps vertically). Without it
    (analysis): the farm background warped in, plus a smooth inpainted colour-difference field."""
    m = cv2.warpAffine(fm, Bk[:2], (720, 1280), flags=cv2.INTER_NEAREST)
    if plate_new is not None:
        rel = Bk @ np.linalg.inv(Bplate)
        wp = cv2.warpAffine(plate_new, rel[:2], (720, 1280), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        md = cv2.dilate(m, np.ones((9, 9), np.uint8))
        band = cv2.dilate(md, np.ones((1, 121), np.uint8)) & (1 - md)
        diff = frame.astype(np.float32) - wp.astype(np.float32)
        off = np.zeros((1280, 3), np.float32)
        ys = np.nonzero(band.any(1))[0]
        for y in ys:
            sel = band[y].astype(bool)
            off[y] = np.median(diff[y, sel], axis=0)
        if len(ys):
            off[:ys.min()] = off[ys.min()]
            off[ys.max():] = off[ys.max()]
        off = cv2.GaussianBlur(off[:, None, :], (1, 0), sigmaX=0.1, sigmaY=4)[:, 0, :] if False else \
            cv2.GaussianBlur(off.reshape(1280, 1, 3), (1, 9), 0).reshape(1280, 3)
        clean = np.clip(wp + off[:, None, :], 0, 255).astype(np.uint8)
        return clean, None
    wb = cv2.warpAffine(bg, Bk[:2], (720, 1280), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    wr = cv2.warpAffine(ref, Bk[:2], (720, 1280), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    m = cv2.dilate(m, np.ones((15, 15), np.uint8))
    d = np.clip(frame.astype(np.int16) - wb.astype(np.int16) + 128, 0, 255).astype(np.uint8)
    d = cv2.GaussianBlur(d, (0, 0), 3)
    d = cv2.inpaint(d, m * 255, 15, cv2.INPAINT_TELEA).astype(np.int16) - 128
    d = cv2.GaussianBlur(d.astype(np.float32), (0, 0), 6)
    clean = np.clip(wb + d, 0, 255).astype(np.uint8)
    farmer_c = np.clip(wr + d, 0, 255).astype(np.uint8)
    return clean, farmer_c


# ------------------------------------------------------------------ animation
def _sm(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


BLINKS = [1.1, 3.3, 6.0, 8.1]


def pose(ts, an, upright=False):
    """Character pose at fractional source time ts (s). upright: the wider framing (can held
    level, as the farmer does there)."""
    kf = ts * FPS_SRC
    k0 = int(np.clip(math.floor(kf), FIRST, POUR_END))
    k1 = min(k0 + 1, POUR_END)
    fr = kf - math.floor(kf)
    ang = 0.0 if upright else float(an["ang"][k0] * (1 - fr) + an["ang"][k1] * fr)
    ang = max(0.0, ang)
    t = ts - FIRST / FPS_SRC                      # seconds since the shot appeared
    tilt = ang / 34.0
    pour = _sm((ang - 14) / 14)
    bob = math.sin(2 * math.pi * 1.25 * t) * pour
    grip = (GRIP_HOLD[0] + GRIP_RAISE[0] * tilt, GRIP_HOLD[1] + GRIP_RAISE[1] * tilt + 1.6 * bob)
    breath = math.sin(2 * math.pi * t / 3.2)
    lean = 3.0 * tilt + 0.4 * breath
    # gaze: at the can while holding (with a look at the plants), down at the plants while pouring
    look_plants = _sm((t - 2.0) / 0.4) * (1 - _sm((t - 3.6) / 0.4))
    face = (0.015 + 0.025 * max(look_plants, pour), 0.02 + 0.035 * max(look_plants, pour))
    blink = 0.0
    for b in BLINKS:
        if abs(t - b) < 0.09:
            blink = max(blink, 1 - abs(t - b) / 0.09)
    return dict(grip=grip, can_angle=ang + 1.2 * bob, lean=lean, breath=breath, face=face, blink=blink,
                flow=pour, t=t)


def _draw_character(surface_w, surface_h, scale, p, water=True):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, surface_w, surface_h)
    cx = cairo.Context(surf)
    cx.scale(scale, scale)
    J.draw_character(cx, HEAD_C, D, p["grip"], p["can_angle"], lean=p["lean"], breath=p["breath"],
                     face=p["face"], blink=p["blink"], can_scale=1.0, flow=p["flow"] if water else 0.0,
                     t=p["t"], ground_y=GROUND_WATER, lw_can=3.0)
    surf.flush()
    a = np.ndarray((surface_h, surface_w, 4), np.uint8, surf.get_data(), strides=(surf.get_stride(), 4, 1))
    return a.astype(np.float32) / 255.0       # premultiplied BGRA


_bg_cache = {}


def _bg_up(an, W, H):
    key = (W, H)
    if key not in _bg_cache:
        bgu = cv2.resize(an["bg"], (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255
        z = cv2.resize(an["zone"].astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
        fm = cv2.resize(an["farmer"].astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
        _bg_cache[key] = (bgu, np.clip(np.maximum(z, fm), 0, 1))
    return _bg_cache[key]


def _farm_layer(an, ts, W, H):
    """Reference-space layers: rebuilt background, its coverage, premultiplied character."""
    bgu, zone = _bg_up(an, W, H)
    ch = _draw_character(W, H, W / 720.0, pose(ts, an))
    return bgu, zone, ch


def _compose_farm(frame_f, an, ts, M, W, H, seed):
    """frame_f: float BGR 0..1 in frame coords; M: ref -> frame (720 coords)."""
    bgu, zone, ch = _farm_layer(an, ts, W, H)
    scale = W / 720.0
    zw = _warp(zone, M, W, H, scale)[..., None]
    bw = _warp(bgu, M, W, H, scale)
    rng = np.random.default_rng(seed)
    bw = bw + rng.normal(0, 1.1 / 255, bw.shape).astype(np.float32)
    base = bw * zw + frame_f * (1 - zw)
    cw = _warp(ch, M, W, H, scale)
    return cw[..., :3] + base * (1 - cw[..., 3:4])


def _warp(img, M, W, H, scale):
    S = np.diag([scale, scale, 1.0])
    Mo = S @ M @ np.linalg.inv(S)
    return cv2.warpAffine(img, Mo[:2], (W, H), flags=cv2.INTER_LINEAR, borderValue=0)


def render(frame_out, frames, k, ts, an, seed=0):
    """Replace the farmer in output frame (BGR uint8, WxH, = upscaled source frame k)."""
    if not (FIRST <= k <= LAST):
        return
    H, W = frame_out.shape[:2]
    scale = W / 720.0
    up = lambda f: cv2.resize(f, (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255
    if k < 414:         # dissolve in from the leaf shot: add the change with the farm shot's weight
        M = np.linalg.inv(an["A"][414 - farm_mascot.FIRST])
        base = up(frames[414])
        new = _compose_farm(base, an, 414 / FPS_SRC, M, W, H, seed)
        out = frame_out.astype(np.float32) / 255 + an["w"][k] * (new - base)
        frame_out[:] = np.clip(out * 255, 0, 255).astype(np.uint8)
        return
    if k <= POUR_END:
        M = np.linalg.inv(an["A"][k - farm_mascot.FIRST])
        out = _compose_farm(frame_out.astype(np.float32) / 255, an, ts, M, W, H, seed)
        frame_out[:] = np.clip(out * 255, 0, 255).astype(np.uint8)
        return
    if k in DISS:       # dissolve out: synthesise from our two clean framings, shot's weights
        w = an["w"][k]
        M = np.linalg.inv(an["A"][POUR_END - farm_mascot.FIRST])
        out629 = _compose_farm(up(frames[POUR_END]), an, (POUR_END + 0.99) / FPS_SRC, M, W, H, seed)
        new = (up(frames[634]) * 255).astype(np.uint8)
        _render_new(new, frames[634], 634, ts, an, seed, g_override=an["g"][k])
        out = (1 - w) * out629 + w * new.astype(np.float32) / 255
        frame_out[:] = np.clip(out * 255, 0, 255).astype(np.uint8)
        return
    _render_new(frame_out, frames[k], k, ts, an, seed)


def _render_new(frame_out, src_frame, k, ts, an, seed, g_override=None):
    H, W = frame_out.shape[:2]
    scale = W / 720.0
    # wider framing: remove the fading farmer, draw the character at the farmer's opacity
    Bk = an["B"][k]
    fm = an["farmer"].copy()
    y0, y1, x0, x1 = farm_bg.FEET
    fm[y0:y1, x0:x1] = 1                      # his shoes stand in front of the first mound
    clean, _ = _clean_new(src_frame, an["bg"], _REF["ref"], fm, Bk, an["plate_new"], an["B"][NEW1])
    m = cv2.warpAffine(fm.astype(np.float32), Bk[:2], (720, 1280), flags=cv2.INTER_LINEAR)
    m = cv2.GaussianBlur(cv2.dilate(m, np.ones((5, 5), np.uint8)), (0, 0), 1.0)
    cu = cv2.resize(clean, (W, H), interpolation=cv2.INTER_LANCZOS4).astype(np.float32) / 255
    mu = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]
    out = cu * mu + frame_out.astype(np.float32) / 255 * (1 - mu)
    g = an["g"][k] if g_override is None else g_override
    if g > 0.01:
        ch = _draw_character(W, H, scale, pose(ts, an, upright=True), water=False)
        rgb, a = ch[..., :3], ch[..., 3:4]
        # character layer (premultiplied) -> straight, warp, composite with the farmer's opacity
        straight = np.where(a > 1e-4, rgb / np.maximum(a, 1e-4), 0)
        rgb_w = _warp(straight, Bk, W, H, scale)
        a_w = _warp(a[..., 0], Bk, W, H, scale)[..., None] * g
        out = rgb_w * a_w + out * (1 - a_w)
    frame_out[:] = np.clip(out * 255, 0, 255).astype(np.uint8)


_REF = {}


def set_ref(frames, an):
    Ak = an["A"][REF - farm_mascot.FIRST]
    _REF["ref"] = cv2.warpAffine(frames[REF], np.linalg.inv(Ak)[:2], (720, 1280),
                                 flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
