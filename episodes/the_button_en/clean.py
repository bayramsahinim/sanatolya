"""Remove the burned-in Turkish captions from the source video (mask + inpaint the caption band)."""
import cv2
import numpy as np

Y0, Y1 = 178, 282          # caption band in the 720x1280 source (text sits at ~y 205-252)


def caption_mask(band):
    """Mask of caption pixels (white/grey words, red highlight box, soft shadow) in a BGR band."""
    lab = cv2.cvtColor(band, cv2.COLOR_BGR2LAB)
    L = lab[..., 0].astype(np.int16)
    bg = cv2.medianBlur(band, 45).astype(np.int16)
    diff = np.abs(band.astype(np.int16) - bg).max(axis=2)
    # strong glyph pixels: much brighter than the local background, or saturated red (highlight box)
    bgL = cv2.cvtColor(bg.astype(np.uint8), cv2.COLOR_BGR2LAB)[..., 0].astype(np.int16)
    b, g, r = [band[..., c].astype(np.int16) for c in range(3)]
    redbox = (r - np.maximum(g, b) > 45) & (r > 110)
    glyph = ((L - bgL > 28) & (diff > 22)) | redbox
    rows = np.zeros_like(glyph)
    rows[18:84] = True
    glyph &= rows
    if glyph.sum() < 30:
        return None
    # caption extent: columns that contain glyph pixels, grouped into one horizontal span
    cols = np.where(glyph.any(axis=0))[0]
    x0, x1 = max(0, cols.min() - 14), min(band.shape[1], cols.max() + 15)
    box = np.zeros_like(glyph)
    box[12:92, x0:x1] = True
    # soft halo / drop shadow: anything that differs from the local background near a glyph
    near = cv2.dilate(glyph.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (29, 29))).astype(bool)
    soft = ((diff > 7) | glyph) & box & near
    m = cv2.dilate(glyph.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
    m |= cv2.dilate(soft.astype(np.uint8), np.ones((5, 5), np.uint8))
    # the highlight box (and the dark plate inside it) goes entirely
    n, lab_, st, _ = cv2.connectedComponentsWithStats(redbox.astype(np.uint8))
    for k in range(1, n):
        x, y, w, h, a = st[k]
        if a > 40 and w > 20:
            m[max(0, y - 8):y + h + 10, max(0, x - 8):x + w + 8] = 1
    # shadow falls a few px down/right of the glyphs
    sh = np.roll(m, 4, axis=0) | np.roll(m, 3, axis=1)
    return ((m | sh) > 0).astype(np.uint8) * 255


def clean_frame(frame):
    band = frame[Y0:Y1].copy()
    m = caption_mask(band)
    if m is None:
        return frame
    out = frame.copy()
    res = np.zeros_like(band)
    cv2.xphoto.inpaint(band, 255 - m, res, cv2.xphoto.INPAINT_FSR_FAST)
    out[Y0:Y1] = res
    return out


def run_part(src, dst, start_frame, n_frames, w=720, h=1280, fps=30):
    """Clean frames [start_frame, start_frame+n_frames) of src into a near-lossless dst clip."""
    import subprocess
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-vf", f"select='gte(n\\,{start_frame})'",
                            "-vsync", "0", "-frames:v", str(n_frames), "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}",
                            "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "8",
                            "-pix_fmt", "yuv444p", dst], stdin=subprocess.PIPE)
    sz = w * h * 3
    k = 0
    while True:
        buf = dec.stdout.read(sz)
        if len(buf) < sz:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(h, w, 3)
        enc.stdin.write(clean_frame(fr).tobytes())
        k += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    return k


if __name__ == "__main__":
    import sys
    print(run_part(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])))
