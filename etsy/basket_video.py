"""Etsy product video for the sage-green crochet organizer basket.

The camera move (push-in -> slide right to an angled view -> rise to reveal the
whole product) is rendered directly from the reference photo with sub-pixel
perspective warps, so the basket, its colour, stitches, four compartments and
every item inside stay exactly as photographed.

    python -m etsy.basket_video <reference.png> output/etsy_basket_8s_4k.mp4
"""
import subprocess
import sys

import cv2
import numpy as np

FPS = 30
DURATION = 8.0
SIZE = 2160  # 1:1 4K (2160 x 2160)

# Keyframes: time, centre x/y (0-1 of source), zoom, yaw (orbit), pitch (crane).
KEYS = np.array([
    # t     cx     cy     zoom  yaw    pitch
    [0.0, 0.500, 0.520, 1.04, 0.000, 0.000],   # wide establishing frame
    [3.0, 0.505, 0.530, 1.28, 0.000, 0.000],   # slow push-in on the basket
    [5.5, 0.600, 0.530, 1.32, 0.035, 0.005],   # slide right, angled view
    [8.0, 0.520, 0.510, 1.08, 0.015, 0.030],   # rise up, whole product
])


def catmull_rom(t):
    """Smooth C1 interpolation through the keyframes (no stops between moves)."""
    ts = KEYS[:, 0]
    pts = np.vstack([KEYS[0], KEYS, KEYS[-1]])[:, 1:]
    i = int(np.clip(np.searchsorted(ts, t, side="right") - 1, 0, len(ts) - 2))
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    p0, p1, p2, p3 = pts[i], pts[i + 1], pts[i + 2], pts[i + 3]
    m1 = (p2 - p0) * 0.5 * (ts[i + 1] - ts[i]) / max(ts[min(i + 1, len(ts) - 1)] - ts[max(i - 1, 0)], 1e-6) * 2
    m2 = (p3 - p1) * 0.5 * (ts[i + 1] - ts[i]) / max(ts[min(i + 2, len(ts) - 1)] - ts[i], 1e-6) * 2
    if i == 0:
        m1 = np.zeros_like(m1)          # ease in at the very start
    if i == len(ts) - 2:
        m2 = np.zeros_like(m2)          # ease out at the very end
    u2, u3 = u * u, u * u * u
    return ((2 * u3 - 3 * u2 + 1) * p1 + (u3 - 2 * u2 + u) * m1
            + (-2 * u3 + 3 * u2) * p2 + (u3 - u2) * m2)


def source_quad(cx, cy, zoom, yaw, pitch, w, h):
    """Source-image quad seen by the virtual camera (TL, TR, BR, BL)."""
    hw = 0.5 / zoom
    tl = [cx - hw * (1 + pitch), cy - hw * (1 + yaw)]
    tr = [cx + hw * (1 + pitch), cy - hw * (1 - yaw)]
    br = [cx + hw * (1 - pitch), cy + hw * (1 - yaw)]
    bl = [cx - hw * (1 - pitch), cy + hw * (1 + yaw)]
    q = np.array([tl, tr, br, bl], dtype=np.float64)
    # Keep the view inside the photo: shift back if any corner leaves it.
    for axis in (0, 1):
        lo, hi = q[:, axis].min(), q[:, axis].max()
        if lo < 0:
            q[:, axis] -= lo
        if hi > 1:
            q[:, axis] -= hi - 1
    q[:, 0] *= w
    q[:, 1] *= h
    return q.astype(np.float32)


def main(src_path, out_path):
    src = cv2.imread(src_path, cv2.IMREAD_COLOR)
    h, w = src.shape[:2]
    dst = np.array([[0, 0], [SIZE, 0], [SIZE, SIZE], [0, SIZE]], dtype=np.float32)
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{SIZE}x{SIZE}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-colorspace", "bt709", "-movflags", "+faststart", "-an", out_path,
    ], stdin=subprocess.PIPE)
    n = int(round(DURATION * FPS))
    for f in range(n):
        cx, cy, zoom, yaw, pitch = catmull_rom(f / FPS)
        H = cv2.getPerspectiveTransform(source_quad(cx, cy, zoom, yaw, pitch, w, h), dst)
        frame = cv2.warpPerspective(src, H, (SIZE, SIZE), flags=cv2.INTER_LANCZOS4,
                                    borderMode=cv2.BORDER_REFLECT)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    sys.exit(ff.wait())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
