"""Remove the source's burned-in Turkish text (720x1280 frames).

* Narration captions: one white bold word with a dark glow, centred, around 74-80% of the frame height.
  Letters are found as bright, unsaturated blobs of letter size sitting on one shared baseline near the
  centre; their dilated footprint is inpainted.
* Gag labels ("Mahkum: *BANA MISIN DEMIYOR*", "*EN KÖTÜ ZULA*", "all skin") at fixed places/times:
  every bright (or yellow, for the "Mahkum:" header) pixel in their box is inpainted.
"""
import cv2
import numpy as np

W, H = 720, 1280
BAND = (int(0.70 * H), int(0.85 * H))

# (t0, t1, box x0, y0, x1, y1) in 720x1280 pixels.  ("all skin" at 47.3-47.7 s is English already: kept.)
LABEL_BOXES = [
    (13.95, 16.45, 0, 340, 720, 432),     # Mahkum: *BANA MISIN DEMIYOR*  (yellow header + white line)
    (44.95, 45.75, 0, 800, 720, 875),     # *EN KÖTÜ ZULA*
]


def _bright(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return (hsv[..., 2] > 205) & (hsv[..., 1] < 70)


def caption_box(img):
    """(x0, y0, x1, y1) of the Turkish narration caption word, or None."""
    y0, y1 = BAND
    band = img[y0:y1]
    b = _bright(band).astype(np.uint8)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(b, 8)
    comps = []
    for k in range(1, n):
        x, y, w, h, a = stats[k]
        if 7 <= h <= 46 and w <= 1.8 * h and a >= 8:
            comps.append((x, y, w, h, cent[k][1]))
    # also tiny dots / accents are fine to miss: the dilation covers them
    comps.sort()
    best = []
    for i in range(len(comps)):
        chain = [comps[i]]
        for c in comps[i + 1:]:
            p = chain[-1]
            gap = c[0] - (p[0] + p[2])
            if gap > 1.7 * max(p[3], c[3]):
                break
            if abs(c[4] - p[4]) < 13 and max(c[3], p[3]) / min(c[3], p[3]) < 3.2:
                chain.append(c)
        if len(chain) >= 2:
            xa, xb = chain[0][0], max(c[0] + c[2] for c in chain)
            if abs((xa + xb) / 2 - W / 2) < 0.25 * W and len(chain) > len(best):
                best = chain
    if not best:
        return _central_row(img)
    xa = min(c[0] for c in best)
    xb = max(c[0] + c[2] for c in best)
    ya = min(c[1] for c in best)
    yb = max(c[1] + c[3] for c in best)
    return xa - 14, y0 + ya - 12, xb + 14, y0 + yb + 14


def _central_row(img):
    """fallback: the caption is always centred - find a bright text row crossing the frame centre."""
    y0, y1 = BAND
    b = _bright(img[y0:y1])
    centre = b[:, W // 2 - 45:W // 2 + 45].sum(1)
    if centre.max() < 6:
        return None
    yc = int(np.argmax(np.convolve(centre, np.ones(25), "same")))
    rows = b[max(0, yc - 26):yc + 26]
    cols = np.where(rows.any(0))[0]
    if not len(cols):
        return None
    xa = xb = W // 2
    for x in range(W // 2, -1, -1):          # grow left until a 30 px empty run
        if rows[:, max(0, x - 30):x].any() or x > W // 2 - 50:
            xa = x
        else:
            break
    for x in range(W // 2, W):
        if rows[:, x:x + 30].any() or x < W // 2 + 50:
            xb = x
        else:
            break
    if xb - xa > 0.85 * W:
        return None
    return xa - 10, y0 + yc - 30, xb + 10, y0 + yc + 30


def caption_mask(img):
    """mask (uint8 0/255) of the Turkish narration caption: letters + their black contour."""
    full = np.zeros(img.shape[:2], np.uint8)
    bx = caption_box(img)
    if bx is None:
        return full
    x0, y0, x1, y1 = [int(v) for v in bx]
    x0, y0 = max(0, x0), max(0, y0)
    sub = _bright(img[y0:y1, x0:x1]).astype(np.uint8) * 255
    full[y0:y1, x0:x1] = cv2.dilate(sub, np.ones((11, 11), np.uint8))
    return full


def label_mask(img, t):
    full = np.zeros(img.shape[:2], np.uint8)
    for t0, t1, x0, y0, x1, y1 in LABEL_BOXES:
        if t0 <= t <= t1:
            sub = img[y0:y1, x0:x1]
            hsv = cv2.cvtColor(sub, cv2.COLOR_BGR2HSV)
            bright = (hsv[..., 2] > 135) & (hsv[..., 1] < 90)
            yellow = (hsv[..., 0] > 15) & (hsv[..., 0] < 40) & (hsv[..., 1] > 90) & (hsv[..., 2] > 150)
            m = ((bright | yellow).astype(np.uint8)) * 255
            m = cv2.dilate(m, np.ones((5, 5), np.uint8))
            full[y0:y1, x0:x1] = np.maximum(full[y0:y1, x0:x1], m)
    return full


def clean(img, t, protect=None):
    """inpaint Turkish text; `protect` = mask of pixels that must not be treated as text (e.g. the prisoner,
    whose white stripes would otherwise look like letters)."""
    m = caption_mask(img) | label_mask(img, t)
    if protect is not None:
        m[protect > 0] = 0
    if not m.any():
        return img, m
    return cv2.inpaint(img, m, 7, cv2.INPAINT_TELEA), m
