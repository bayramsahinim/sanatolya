"""Farmer-free background for the farm shot (reference-frame coords, 720x1280 BGR).

The farm shot is a 2D illustration under a slow camera pull-back, so it is analysed in the
stabilised reference frame (see farm_mascot.analyse: plate + camera track).
Behind the farmer, his arm, the watering can and the original spray there is only sky,
the horizon and the field (smooth horizontal bands under a radial vignette): those rows are
rebuilt from a separable model, colour(y) from the clean pixels either side x vignette(x).
The small area behind his feet (ground / plant edge) is inpainted; the new character's feet
stand there again.
"""
import cv2
import numpy as np

AIR_X0 = 236            # left edge of the rebuilt air zone (house wall ends at ~188)
BARREL_TOP = 735        # below this, the left neighbour is the barrel rim/body (not usable)
FEET = (984, 1056, 248, 352)   # y0, y1, x0, x1
MOUND_PITCH = 168       # the mounds are identical copies 168 px apart


def mounds(plate):
    """Plant mounds only (green + their ink outline, solid below each column's top edge)."""
    b, g, r = [plate[..., i].astype(np.int16) for i in range(3)]
    green = ((g - r > 16) & (g - b > 16)).astype(np.uint8)
    green[:925] = 0
    green = cv2.morphologyEx(green, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    lum = plate.astype(np.float32).mean(2)
    ink = ((lum < 95).astype(np.uint8) & cv2.dilate(green, np.ones((15, 15), np.uint8)))
    m = green | ink
    solid = np.zeros_like(m)
    for x in range(m.shape[1]):
        ys = np.nonzero(m[925:, x])[0]
        if len(ys):
            solid[925 + ys[0]:, x] = 1
    return cv2.dilate(m | solid, np.ones((3, 3), np.uint8))


def build(plate, plants=None):
    plants = mounds(plate)
    p = plate.astype(np.float32)
    H, W = p.shape[:2]
    lum = p.mean(2)
    # vignette profile from sky rows that are clean on both sides of the farmer
    left_cols = np.arange(194, 233)
    right_cols = np.arange(560, 716)
    rows = np.arange(560, 730)
    xs = np.concatenate([left_cols, right_cols])
    prof = (lum[rows][:, xs] / lum[rows][:, right_cols].mean(1, keepdims=True)).mean(0)
    cf = np.polyfit(xs, prof, 2)
    vig = np.polyval(cf, np.arange(W)).astype(np.float32)
    out = p.copy()
    zone = np.zeros((H, W), np.uint8)
    for y in range(505, FEET[0] + 1):
        # usable right-hand samples: not plants
        rc = right_cols[plants[y, right_cols] == 0]
        if len(rc) < 20:
            continue
        cr = (p[y, rc] / vig[rc, None]).mean(0)
        x1 = W
        row = cr[None, :] * vig[:, None]
        if 585 <= y < BARREL_TOP:   # above 585 the roof is in the left samples
            cl = (p[y, left_cols] / vig[left_cols, None]).mean(0)
            # blend so the left edge meets the sky between house and farmer exactly
            w = np.clip((np.arange(W) - 214) / (430 - 214), 0, 1)[:, None]
            row = (cl[None, :] * (1 - w) + cr[None, :] * w) * vig[:, None]
        sel = np.arange(AIR_X0 if y < BARREL_TOP else 253, x1)
        sel = sel[plants[y, sel] == 0]
        if y < 525:   # feather into the untouched sky above
            a = (y - 505) / 20
            out[y, sel] = row[sel] * a + p[y, sel] * (1 - a)
        else:
            out[y, sel] = row[sel]
        zone[y, sel] = 1
    # feet area: ground + the first mound's hidden left edge (rebuilt geometrically)
    y0, y1, x0, x1 = FEET
    feet = np.zeros((H, W), np.uint8)
    feet[y0:y1, x0:x1] = 1
    o8 = np.clip(out, 0, 255).astype(np.uint8).astype(np.float32)
    field = out[y0 - 3:y0, 300:340].reshape(-1, 3).mean(0)   # rebuilt field just above
    ground = p[1066:1072, 255:300].reshape(-1, 3).mean(0)
    shadow = p[1046:1052, 236:248].reshape(-1, 3).mean(0)
    for y in range(y0, y1):
        t = np.clip((y - 990) / 6.0, 0, 1)
        o8[y, x0:x1] = field * (1 - t) + ground * t
    # barrel shadow continues softly to the right of the barrel
    yy, xx = np.mgrid[y0:y1, x0:x1]
    sh = np.exp(-(((xx - 245) / 45.0) ** 2 + ((yy - 1050) / 12.0) ** 2))[..., None]
    o8[y0:y1, x0:x1] = o8[y0:y1, x0:x1] * (1 - 0.8 * sh) + shadow * 0.8 * sh
    # first mound's hidden lower-left = the second mound's lower-left, one pitch over; per row,
    # copy from the second mound's left outline inward (left of it stays ground)
    for y in range(996, 1047):
        row_l = lum[y, 470:520]
        dark = np.nonzero(row_l < 85)[0]
        if not len(dark):
            continue
        # first dark run = the second mound's left outline
        xs_src = 470 + dark[0]
        xd = xs_src - MOUND_PITCH
        if xd >= x1 or xd < 316:      # the first mound never starts left of ~318
            continue
        xd0 = max(xd, x0)
        o8[y, xd0:x1] = p[y, xd0 + MOUND_PITCH:x1 + MOUND_PITCH]
    # only what the farmer covered is rebuilt: legs (x 252-306) + shoes/socks/buckles/leg ink
    pb, pg, pr = [p[..., i] for i in range(3)]
    farmer = np.zeros((H, W), np.uint8)
    farmer[y0:1047, 252:306] = 1
    white = p.min(2) > 165
    yellow = (pr > 170) & (pg > 130) & (pb < 110)
    shoe = (lum < 85) & (pr - pg > 4)
    farmer |= ((white | yellow | shoe) & (feet > 0)).astype(np.uint8)
    farmer = cv2.dilate(farmer, np.ones((5, 5), np.uint8)) & feet
    o8 = cv2.GaussianBlur(o8, (3, 3), 0)
    o8 = o8 * farmer[..., None] + np.clip(out, 0, 255) * (1 - farmer[..., None])
    feet = farmer
    o8 = np.clip(o8, 0, 255).astype(np.uint8)
    # matching grain in rebuilt areas
    rng = np.random.default_rng(5)
    g = rng.normal(0, 1.4, (H, W, 1)).astype(np.float32)
    z = (zone | feet).astype(bool)
    o = o8.astype(np.float32)
    o[z] += g[z]
    return np.clip(o, 0, 255).astype(np.uint8), (zone | feet)
