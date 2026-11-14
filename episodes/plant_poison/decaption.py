"""Remove the Turkish burned-in captions from the source video (720x1280, 24 fps).

    python episodes/plant_poison/decaption.py SOURCE.mp4 OUT_CLEAN.mp4

Glyph detection (tools: local median contrast + dark-pixel components inside the caption
band, filtered by shape), sticky per caption block; pass 2 unions each mask with the next frames
(fade-ins) and fills: motion-compensated copy of the previous cleaned frame during camera
moves, else Telea inpainting."""
import subprocess
import sys

import cv2
import numpy as np

Y0, Y1 = 180, 330   # caption band in 720x1280
X0, X1 = 30, 690

def _filter(m):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m); H, W = m.shape
    ok = np.zeros(n, bool)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if h > 46 or w > 420 or a < 3: continue
        if y <= 1 or y + h >= H - 1 or x <= 1 or x + w >= W - 1: continue
        if h < 7 and w > 14: continue   # thin streaks (wood grain)
        ok[i] = True
    return ok[lab].astype(np.uint8)

def detect(img, thr=11):
    band = img[Y0:Y1, X0:X1]
    g = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY)
    bg = cv2.medianBlur(g, 25).astype(np.int16)
    d = np.abs(g.astype(np.int16) - bg)
    m = _filter((d > thr).astype(np.uint8)) | _filter((g < 75).astype(np.uint8))
    full = np.zeros(img.shape[:2], np.uint8); full[Y0:Y1, X0:X1] = m
    return full, g, bg

class Cleaner:
    """Captions are screen-fixed and only grow within a block, so remember glyph pixels
    and keep masking them while they still look like text (dark vs local background)."""
    def __init__(self): self.acc = None; self.tail = None; self.tail_n = 0
    def mask(self, img):
        d, g, bg = detect(img)
        if self.acc is not None:
            a = self.acc[Y0:Y1, X0:X1].astype(bool)
            still = (bg - g.astype(np.int16) > 10) | (g < 75)
            frac = (still & a).sum() / max(1, a.sum())
            if frac < 0.35:
                self.tail, self.tail_n = self.acc, 9   # keep covering the fade-out
                self.acc = None
            else:
                carry = np.zeros_like(d); carry[Y0:Y1, X0:X1] = (a & still)
                d = d | carry
        if d.sum():
            self.acc = d if self.acc is None else (self.acc | d)
        if self.tail_n > 0:
            self.tail_n -= 1; d = d | self.tail
        return d
    def __call__(self, img):
        d = self.mask(img)
        if d.sum() == 0: return img, d
        m = cv2.dilate(d, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 21)), anchor=(8, 8))
        return cv2.inpaint(img, m * 255, 6, cv2.INPAINT_TELEA), m


src, out = sys.argv[1], sys.argv[2]
LOOK = 7
# the one real camera move under the captions (push-in on the plant, frames 240-284);
# everywhere else (static shots, cross-fades) spatial inpainting is cleaner
ZOOM = range(240, 285)

cap = cv2.VideoCapture(src); frames = []; masks = []
mk = Cleaner()
while True:
    ok, f = cap.read()
    if not ok: break
    frames.append(f)
    d = mk.mask(f)
    masks.append(d[Y0:Y1, X0:X1].astype(bool))

def full(b):
    m = np.zeros((1280, 720), np.uint8); m[Y0:Y1, X0:X1] = b; return m

p = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s","720x1280","-r","24","-i","-",
    "-c:v","libx264","-crf","12","-preset","medium","-pix_fmt","yuv420p",out], stdin=subprocess.PIPE)
prev = prev_raw = None
KER = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 21))
for k, f in enumerate(frames):
    u = masks[k].copy()
    for j in range(k + 1, min(len(frames), k + 1 + LOOK)): u |= masks[j]
    m = full(u)
    outf = f
    if m.any():
        m = cv2.dilate(m, KER, anchor=(8, 8))
        outf = cv2.inpaint(f, m * 255, 6, cv2.INPAINT_TELEA)
        if prev is not None and k in ZOOM:
            s = 0.25
            a = cv2.resize(cv2.cvtColor(prev_raw, cv2.COLOR_BGR2GRAY), None, fx=s, fy=s).astype(np.float32)
            b = cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), None, fx=s, fy=s).astype(np.float32)
            valid = np.ones(b.shape, np.uint8); valid[int(Y0*s)-2:int(Y1*s)+2, :] = 0
            M = np.eye(2, 3, dtype=np.float32)
            try:
                _, M = cv2.findTransformECC(b, a, M, cv2.MOTION_AFFINE,
                        (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 60, 1e-5), valid, 3)
                M[:, 2] /= s
                motion = np.abs(M[:, :2] - np.eye(2)).max() * 720 + np.abs(M[:, 2]).max()
                if motion > 0.6:
                    warped = cv2.warpAffine(prev, M, (720, 1280), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                            borderMode=cv2.BORDER_REPLICATE)
                    ring = (cv2.dilate(m, np.ones((11, 11), np.uint8)) & (1 - m)).astype(bool)
                    err = np.abs(warped.astype(np.int16) - f.astype(np.int16)).mean(2)[ring].mean()
                    if err < 12:
                        mm = np.clip(cv2.GaussianBlur(m.astype(np.float32), (9, 9), 0) * 1.5, 0, 1)[..., None]
                        outf = (warped * mm + f * (1 - mm)).astype(np.uint8)
            except cv2.error:
                pass
    prev, prev_raw = outf, f
    p.stdin.write(outf.tobytes())
p.stdin.close(); p.wait()
