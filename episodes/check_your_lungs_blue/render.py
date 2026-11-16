"""Blue-theme rebrand of JUST_NEEDY_CHECK_YOUR_LUNGS_FINAL.mp4.

Recolours the orange background to navy, keeps lungs/text/captions untouched,
redraws the progress bar (white track, blue progress) and replaces the emoji
marker with a miniature Just Needy blue-hoodie character on the exact same path.
"""
import json, math, subprocess, sys
import numpy as np
import cairo
from scipy.ndimage import gaussian_filter, median_filter

SRC = sys.argv[1]
OUT = sys.argv[2]
PROBE = sys.argv[3]
LIMIT = int(sys.argv[4]) if len(sys.argv) > 4 else None
W, H, FPS = 1080, 1920, 30

# ---------------------------------------------------------------- geometry
TX = 469.5                     # track centre x
TRACK_HW = 28.5                # track half width (441..498)
TRACK_TOP = 325.0
CPS = [470.0, 809.5, 1149.5, 1489.5]
CP_R = 47.5
BX0, BX1, BY0, BY1 = 395, 546, 290, 1580   # band that is redrawn
BW, BH = BX1 - BX0, BY1 - BY0

# ---------------------------------------------------------------- timing
p = json.load(open(PROBE))
N = len(p)
g = np.array([o['gmax'] or 446 for o in p], float)
center = median_filter(g - 60.0, size=7, mode='nearest')
center = np.convolve(np.pad(center, 2, mode='edge'), np.ones(5) / 5, 'valid')
blue_cnt = np.array([o['blue'] for o in p])
BLUE = (blue_cnt > 5)
BLUE = median_filter(BLUE.astype(int), size=5).astype(bool)
GOLD_START = 282
fill_end = center.copy()

def crossing(y):
    for i in range(GOLD_START, N):
        if center[i] >= y - 2:
            return i
    return N - 1

CP_FR = [crossing(y) for y in CPS]

# ---------------------------------------------------------------- colour
def hexc(h):
    h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)

STOPS = [(0.00, '#050D1A'), (0.10, '#09182C'), (0.30, '#0F2847'), (0.45, '#133461'),
         (0.60, '#1B55A0'), (0.80, '#45B9FF'), (1.00, '#D0EEFF')]
xs = np.linspace(0, 1, 1024)
LUT = np.stack([np.interp(xs, [s[0] for s in STOPS], [hexc(s[1])[k] for s in STOPS]) for k in range(3)], 1)

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)

PROTECT = [(736, 598, 766, 645)]   # cigarette filter (orange, belongs to the lung art)

def recolor(fr):
    f = fr.astype(np.float32) / 255.0
    r, gg, b = f[..., 0], f[..., 1], f[..., 2]
    mx = f.max(2); mn = f.min(2); d = mx - mn + 1e-6
    s = d / (mx + 1e-6)
    # hue only needed for r-max pixels (orange); others -> 0 weight
    hue = np.where(mx == r, 60 * ((gg - b) / d), np.where(mx == gg, 120 + 60 * (b - r) / d, 999))
    wh = smooth(4, 13, hue) * (1 - smooth(42, 54, hue))
    w = wh * smooth(0.32, 0.6, s)
    for x0, y0, x1, y1 in PROTECT:
        w[y0:y1, x0:x1] = 0
    L = 0.299 * r + 0.587 * gg + 0.114 * b
    Lb = gaussian_filter(L, 5)
    L2 = np.clip(Lb + 0.55 * (L - Lb), 0, 1)
    navy = LUT[(L2 * 1023).astype(np.int32)]
    out = w[..., None] * navy + (1 - w[..., None]) * fr.astype(np.float32)
    return out

# ---------------------------------------------------------------- expressions
# head units; origin = head centre, y down
EXPR = {
    'calm':      dict(bl=[-.31, -.43, -.10, -.60, .04, -.52], br=[.39, -.42, .60, -.44, .68, -.29],
                      eo=1.0, lid=0.0, hap=0.0, look=0.0, m=[-.23, .23, -.12, .37, .10, .44, .31, .41], tilt=0.0),
    'curious':   dict(bl=[-.31, -.55, -.12, -.74, .04, -.66], br=[.39, -.56, .53, -.66, .68, -.52],
                      eo=1.12, lid=0.0, hap=0.0, look=.035, m=[-.06, .31, .02, .37, .14, .37, .22, .31], tilt=6.0),
    'uncertain': dict(bl=[-.31, -.39, -.12, -.43, .04, -.53], br=[.39, -.53, .53, -.48, .68, -.38],
                      eo=.95, lid=.08, hap=0.0, look=-.04, m=[-.15, .34, -.02, .27, .12, .39, .25, .31], tilt=-3.0),
    'tired':     dict(bl=[-.31, -.35, -.12, -.39, .05, -.39], br=[.39, -.38, .53, -.39, .68, -.33],
                      eo=.92, lid=.48, hap=0.0, look=0.0, m=[-.10, .35, .00, .32, .12, .32, .22, .34], tilt=-5.0),
    'relieved':  dict(bl=[-.31, -.46, -.12, -.60, .05, -.54], br=[.39, -.50, .53, -.56, .68, -.43],
                      eo=1.0, lid=0.0, hap=1.0, look=0.0, m=[-.25, .22, -.10, .45, .18, .47, .33, .30], tilt=2.0),
}
SEQ = ['calm', 'curious', 'uncertain', 'tired', 'relieved']

def lerp_expr(a, b, t):
    out = {}
    for k in a:
        if isinstance(a[k], list):
            out[k] = [x + (y - x) * t for x, y in zip(a[k], b[k])]
        else:
            out[k] = a[k] + (b[k] - a[k]) * t
    return out

def expr_at(i):
    stage = 0
    for k, fr in enumerate(CP_FR):
        if i >= fr:
            stage = k + 1
    if stage == 0:
        return dict(EXPR['calm'])
    # ease from previous expression over 0.5 s
    t = min(1.0, (i - CP_FR[stage - 1]) / (0.5 * FPS))
    t = t * t * (3 - 2 * t)
    return lerp_expr(EXPR[SEQ[stage - 1]], EXPR[SEQ[stage]], t)

def blink(i):
    # quick blink roughly every 3.7 s (offset so it never sits on a checkpoint change)
    ph = (i + 40) % 111
    if ph < 5:
        return [1, .55, .12, .55, 1][ph]
    return 1.0

# ---------------------------------------------------------------- drawing
BLACK = (0.04, 0.04, 0.06)
HOOD = (0.035, 0.40, 0.98)      # royal blue
HOOD_D = (0.02, 0.28, 0.78)
HEAD = (0.985, 0.985, 1.0)
SHADE = (0.86, 0.85, 0.95)

def rgb(h):
    c = hexc(h) / 255; return tuple(c)

def capsule(cx, x0, x1, y0, y1):
    r = (x1 - x0) / 2
    cx.new_path()
    cx.arc(x0 + r, y0 + r, r, math.pi, 2 * math.pi)
    cx.line_to(x1, y1 - r)
    cx.arc(x0 + r, y1 - r, r, 0, math.pi)
    cx.close_path()

def draw_bar(cx, i):
    gold = i >= GOLD_START
    blue = bool(BLUE[i]) and not gold
    fe = fill_end[i]
    active = gold or blue
    x0, x1 = TX - TRACK_HW, TX + TRACK_HW
    # restrained glow along the filled part
    if gold and fe > TRACK_TOP + 10:
        for wdt, a in ((70, .07), (50, .10), (34, .14)):
            cx.set_line_cap(cairo.LINE_CAP_ROUND)
            cx.set_line_width(wdt)
            cx.set_source_rgba(0.27, 0.72, 1.0, a)
            cx.move_to(TX, TRACK_TOP + 20); cx.line_to(TX, fe); cx.stroke()
    # track body: white with thin navy edge
    capsule(cx, x0, x1, TRACK_TOP, CPS[-1])
    cx.set_source_rgb(*rgb('#FFFFFF')); cx.fill_preserve()
    cx.set_source_rgba(0.03, 0.08, 0.16, 0.9); cx.set_line_width(2.5); cx.stroke()
    # inner channel
    ci = 9.0
    capsule(cx, x0 + ci, x1 - ci, TRACK_TOP + ci, CPS[-1] - ci + 0)
    cx.set_source_rgb(*rgb('#E3ECF7')); cx.fill()
    # active progress
    if active and fe > TRACK_TOP + ci + 4:
        end = min(fe, CPS[-1])
        capsule(cx, x0 + ci, x1 - ci, TRACK_TOP + ci, max(end, TRACK_TOP + ci + 2 * (TRACK_HW - ci)))
        grad = cairo.LinearGradient(x0, 0, x1, 0)
        if gold:
            grad.add_color_stop_rgb(0, *rgb('#1976FF')); grad.add_color_stop_rgb(.5, *rgb('#45B9FF'))
            grad.add_color_stop_rgb(1, *rgb('#1976FF'))
        else:
            grad.add_color_stop_rgb(0, *rgb('#7FD0FF')); grad.add_color_stop_rgb(.5, *rgb('#B8E6FF'))
            grad.add_color_stop_rgb(1, *rgb('#7FD0FF'))
        cx.set_source(grad); cx.fill()
    # checkpoints
    for y in CPS:
        reached = active and fe >= y - 3
        if reached and gold:
            rg = cairo.RadialGradient(TX, y, CP_R * .6, TX, y, CP_R * 1.7)
            rg.add_color_stop_rgba(0, 0.27, 0.72, 1.0, 0.45); rg.add_color_stop_rgba(1, 0.27, 0.72, 1.0, 0)
            cx.set_source(rg); cx.arc(TX, y, CP_R * 1.7, 0, 2 * math.pi); cx.fill()
        cx.arc(TX, y, CP_R, 0, 2 * math.pi)
        cx.set_source_rgb(1, 1, 1); cx.fill_preserve()
        cx.set_source_rgba(0.03, 0.08, 0.16, 0.9); cx.set_line_width(2.5); cx.stroke()
        cx.arc(TX, y, 31, 0, 2 * math.pi)
        if reached:
            rg = cairo.RadialGradient(TX - 6, y - 8, 2, TX, y, 31)
            if gold:
                rg.add_color_stop_rgb(0, *rgb('#9BDCFF')); rg.add_color_stop_rgb(.55, *rgb('#45B9FF')); rg.add_color_stop_rgb(1, *rgb('#1976FF'))
            else:
                rg.add_color_stop_rgb(0, *rgb('#E2F5FF')); rg.add_color_stop_rgb(1, *rgb('#7FD0FF'))
            cx.set_source(rg)
        else:
            cx.set_source_rgb(*rgb('#0B1E38'))
        cx.fill()

def face(cx, e, bl_f):
    lw = 0.052
    cx.set_line_cap(cairo.LINE_CAP_ROUND); cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.set_source_rgb(*BLACK)
    # brows
    for b in (e['bl'], e['br']):
        cx.move_to(b[0], b[1]); cx.curve_to(b[2], b[3], b[2], b[3], b[4], b[5])
        cx.set_line_width(lw * 1.05); cx.stroke()
    # eyes
    lk = e['look']
    for ex, ey in ((-0.01 + lk, -0.13), (0.51 + lk, -0.11)):
        rx, ry = 0.068, 0.185 * e['eo']
        open_a = 1 - e['hap']
        if open_a > 0.01:
            sq = max(0.10, bl_f)
            ry2 = ry * sq
            cx.save()
            top = ey - ry2 + 2 * ry2 * e['lid'] * (1 if sq > 0.5 else 0)
            cx.rectangle(ex - 0.2, top, 0.4, 1.0); cx.clip()
            cx.save(); cx.translate(ex, ey); cx.scale(rx, ry2); cx.arc(0, 0, 1, 0, 2 * math.pi); cx.restore()
            cx.set_source_rgba(*BLACK, open_a); cx.fill()
            cx.restore()
            if e['lid'] > 0.05 and sq > 0.5:
                cx.move_to(ex - rx * 1.5, top + 0.005); cx.line_to(ex + rx * 1.5, top - 0.01)
                cx.set_source_rgba(*BLACK, open_a); cx.set_line_width(lw * 0.9); cx.stroke()
        if e['hap'] > 0.01:
            cx.move_to(ex - 0.085, ey + 0.02); cx.curve_to(ex - 0.06, ey - 0.09, ex + 0.06, ey - 0.09, ex + 0.085, ey + 0.02)
            cx.set_source_rgba(*BLACK, e['hap']); cx.set_line_width(lw * 1.1); cx.stroke()
    # mouth
    m = e['m']
    cx.move_to(m[0], m[1]); cx.curve_to(m[2], m[3], m[4], m[5], m[6], m[7])
    cx.set_source_rgb(*BLACK); cx.set_line_width(lw * 1.05); cx.stroke()

def character(cx, x, y, e, bl_f):
    R = 50.0
    cx.save()
    cx.translate(x, y - 14)
    cx.scale(R, R)
    OL = 0.095
    cx.set_line_join(cairo.LINE_JOIN_ROUND); cx.set_line_cap(cairo.LINE_CAP_ROUND)
    # soft contact shadow
    rg = cairo.RadialGradient(0, 1.85, 0.1, 0, 1.85, 1.5)
    rg.add_color_stop_rgba(0, 0, 0.02, 0.06, 0.45); rg.add_color_stop_rgba(1, 0, 0.02, 0.06, 0)
    cx.set_source(rg); cx.save(); cx.scale(1, 0.35); cx.arc(0, 1.85 / 0.35, 1.5, 0, 2 * math.pi); cx.restore(); cx.fill()
    # hood (collar puff behind neck)
    cx.save(); cx.translate(-0.04, 1.02); cx.scale(1.0, 0.36); cx.arc(0, 0, 1, 0, 2 * math.pi); cx.restore()
    cx.set_source_rgb(*HOOD); cx.fill_preserve(); cx.set_source_rgb(*BLACK); cx.set_line_width(OL); cx.stroke()
    # torso
    cx.move_to(-1.36, 1.92)
    cx.curve_to(-1.38, 1.48, -1.18, 1.16, -0.72, 1.12)
    cx.line_to(0.72, 1.12)
    cx.curve_to(1.18, 1.16, 1.38, 1.48, 1.36, 1.92)
    cx.curve_to(0.9, 2.04, -0.9, 2.04, -1.36, 1.92)
    cx.close_path()
    cx.set_source_rgb(*HOOD); cx.fill_preserve(); cx.set_source_rgb(*BLACK); cx.set_line_width(OL); cx.stroke()
    # hood rim over shoulders (front of collar)
    cx.move_to(-0.98, 1.08); cx.curve_to(-0.86, 1.30, -0.45, 1.28, -0.22, 1.18)
    cx.move_to(0.98, 1.08); cx.curve_to(0.86, 1.30, 0.45, 1.28, 0.22, 1.18)
    cx.set_source_rgb(*BLACK); cx.set_line_width(OL * 0.8); cx.stroke()
    # fabric shading
    for (a, b, c, d) in ((-0.8, 0.95, -0.5, 0.88), (0.55, 0.9, 0.82, 0.97)):
        cx.move_to(a, b); cx.line_to(c, d)
    cx.set_source_rgb(*HOOD_D); cx.set_line_width(0.07); cx.stroke()
    cx.move_to(-0.98, 1.92); cx.curve_to(-0.95, 1.65, -0.85, 1.5, -0.72, 1.42)
    cx.move_to(0.98, 1.92); cx.curve_to(0.95, 1.65, 0.85, 1.5, 0.72, 1.42)
    cx.set_source_rgb(*HOOD_D); cx.set_line_width(0.06); cx.stroke()
    # V neck with white neck showing
    cx.move_to(-0.30, 1.02); cx.line_to(0.0, 1.40); cx.line_to(0.30, 1.02); cx.close_path()
    cx.set_source_rgb(*HEAD); cx.fill()
    cx.move_to(-0.34, 1.0); cx.line_to(0.0, 1.42); cx.line_to(0.34, 1.0)
    cx.set_source_rgb(*BLACK); cx.set_line_width(OL * 0.85); cx.stroke()
    # drawstrings
    for sx in (-0.21, 0.21):
        cx.move_to(sx, 1.30); cx.line_to(sx + (0.01 if sx > 0 else -0.01), 1.74)
        cx.set_source_rgb(*BLACK); cx.set_line_width(0.13); cx.stroke()
        cx.move_to(sx, 1.30); cx.line_to(sx + (0.01 if sx > 0 else -0.01), 1.74)
        cx.set_source_rgb(*HOOD); cx.set_line_width(0.05); cx.stroke()
        cx.arc(sx + (0.01 if sx > 0 else -0.01), 1.78, 0.06, 0, 2 * math.pi)
        cx.set_source_rgb(*HOOD); cx.fill_preserve(); cx.set_source_rgb(*BLACK); cx.set_line_width(0.04); cx.stroke()
    # head (tilts around the neck)
    cx.translate(0, 0.95); cx.rotate(math.radians(e['tilt'])); cx.translate(0, -0.95)
    cx.arc(0, 0, 1, 0, 2 * math.pi)
    cx.set_source_rgb(*SHADE); cx.fill()
    cx.save(); cx.arc(0, 0, 1, 0, 2 * math.pi); cx.clip()
    cx.arc(0.2, -0.04, 0.93, 0, 2 * math.pi); cx.set_source_rgb(*HEAD); cx.fill()
    cx.restore()
    cx.arc(0, 0, 1, 0, 2 * math.pi)
    cx.set_source_rgb(*BLACK); cx.set_line_width(OL); cx.stroke()
    face(cx, e, bl_f)
    cx.restore()

def overlay(i):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, BW, BH)
    cx = cairo.Context(surf)
    cx.translate(-BX0, -BY0)
    cx.set_antialias(cairo.ANTIALIAS_BEST)
    draw_bar(cx, i)
    e = expr_at(i)
    character(cx, TX, center[i], e, blink(i))
    a = np.ndarray((BH, BW, 4), np.uint8, surf.get_data()).astype(np.float32) / 255.0
    # cairo: BGRA premultiplied
    return a[..., [2, 1, 0]], a[..., 3:4]

# ---------------------------------------------------------------- plate
PLATE = None   # dict: B (orig-colour clean bg), Bn (navy clean bg), wB (bg weight of plate)

def read_frames(n_at):
    cmd = ['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    pr = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    want = set(n_at); got = {}
    for k in range(max(n_at) + 1):
        buf = pr.stdout.read(W * H * 3)
        if k in want:
            got[k] = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
    pr.kill()
    return got

def bg_weight(fr):
    f = fr.astype(np.float32) / 255.0
    r, gg, b = f[..., 0], f[..., 1], f[..., 2]
    mx = f.max(2); mn = f.min(2); d = mx - mn + 1e-6
    s = d / (mx + 1e-6)
    hue = np.where(mx == r, 60 * ((gg - b) / d), 999)
    return smooth(4, 13, hue) * (1 - smooth(42, 54, hue)) * smooth(0.32, 0.6, s)

def build_plate():
    ids = list(range(5, 1560, 26))
    fr = read_frames(ids + [60, 200])
    med = np.median(np.stack([fr[i] for i in ids]), 0).astype(np.float32)
    comp = fr[60].astype(np.float32)
    comp[BY0:480] = fr[200][BY0:480]
    xa, xb = 399, 541
    wl = bg_weight(comp[:, xa - 1:xa].astype(np.uint8))[:, 0]
    t = ((np.arange(xa, xb) - xa) / (xb - xa))[None, :, None]
    left = np.where(wl[:, None] > 0.6, comp[:, xa - 1], comp[:, xb])[:, None, :]
    comp[:, xa:xb] = left * (1 - t) + comp[:, xb:xb + 1] * t
    B = med.copy()
    B[BY0 - 20:BY1 + 20, xa:xb] = comp[BY0 - 20:BY1 + 20, xa:xb]
    B8 = B.astype(np.uint8)
    return dict(B=B, Bn=recolor(B8), wB=bg_weight(B8))

def unmix(fr):
    P = fr.astype(np.float32); B = PLATE['B']; Bn = PLATE['Bn']
    D = P - B
    a = 255.0 - B; b = -B
    aa = (a * a).sum(2); bb = (b * b).sum(2); ab = (a * b).sum(2)
    da = (D * a).sum(2); db = (D * b).sum(2)
    det = aa * bb - ab * ab + 1e-3
    aw = np.clip((da * bb - db * ab) / det, 0, 1)
    ak = np.clip((db * aa - da * ab) / det, 0, 1)
    sc = np.maximum(1.0, aw + ak); aw /= sc; ak /= sc
    res = np.sqrt(((D - aw[..., None] * a - ak[..., None] * b) ** 2).sum(2))
    out = aw[..., None] * 255.0 + (1 - aw - ak)[..., None] * Bn
    k = PLATE['wB'] * (1 - smooth(18, 45, res))
    for x0, y0, x1, y1 in PROTECT:
        k[y0:y1, x0:x1] = 0
    return out, k

def init():
    global PLATE
    PLATE = dict(np.load(PLATE_PATH))

YY, XX = np.mgrid[BY0:BY1, BX0:BX1].astype(np.float32)
TRACKMASK = smooth(56, 50, np.abs(XX - TX))   # original track + checkpoint rings (r 47.5)

def process(args):
    i, buf = args
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    hue_out = recolor(fr)
    um, k = unmix(fr)
    out = k[..., None] * um + (1 - k[..., None]) * hue_out
    # under the original bar + emoji: clean navy plate
    em = smooth(78, 70, np.hypot(XX - TX, YY - center[i]))
    m = np.maximum(TRACKMASK * (YY < CPS[-1] + 60), em)[..., None]
    band = out[BY0:BY1, BX0:BX1]
    band = m * PLATE['Bn'][BY0:BY1, BX0:BX1] + (1 - m) * band
    col, al = overlay(i)
    band = band * (1 - al) + col * 255.0
    out[BY0:BY1, BX0:BX1] = band
    return np.clip(out + 0.5, 0, 255).astype(np.uint8).tobytes()

PLATE_PATH = OUT + '.plate.npz'

if __name__ == '__main__':
    from multiprocessing import Pool
    np.savez(PLATE_PATH, **build_plate())
    print('checkpoint frames', CP_FR, [round(f / FPS, 2) for f in CP_FR], flush=True)
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', SRC, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                            '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-i', SRC,
                            '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17',
                            '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-r', str(FPS),
                            '-c:a', 'copy', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)

    def gen():
        k = 0
        while True:
            if LIMIT is not None and k >= LIMIT:
                return
            buf = dec.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                return
            yield (min(k, N - 1), buf)
            k += 1

    with Pool(4, initializer=init) as pool:
        for n, data in enumerate(pool.imap(process, gen(), chunksize=2)):
            enc.stdin.write(data)
            if n % 150 == 0:
                print('frame', n, flush=True)
    enc.stdin.close(); enc.wait(); dec.kill()
    print('done')
