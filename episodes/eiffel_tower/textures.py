"""Procedural PIL textures (facades, paper, newspaper, letters, banknotes...) for the 3D sets."""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEX = os.path.join(ROOT, "build", "tex")
FONT_BOLD = os.path.join(ROOT, "assets", "fonts", "Montserrat-ExtraBold.ttf")
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_R = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_I = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"


def _font(path, size):
    for p in (path, SERIF, FONT_BOLD):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _save(img, name):
    os.makedirs(TEX, exist_ok=True)
    p = os.path.join(TEX, name)
    img.save(p)
    return p


def _grain(img, amt=10, seed=0):
    rng = np.random.default_rng(seed)
    a = np.asarray(img).astype(np.int16)
    n = rng.integers(-amt, amt + 1, size=a.shape[:2])[..., None]
    a[..., :3] = np.clip(a[..., :3] + n, 0, 255)
    return Image.fromarray(a.astype(np.uint8), img.mode)


def facade(name="facade_a", floors=6, bays=5, seed=1, stone=(222, 205, 172), lit=0.0):
    """Haussmann facade: 1 tile = one building face (floors x bays), ground floor shops."""
    rng = random.Random(seed)
    bw, fh = 180, 200
    W, H = bays * bw, floors * fh
    img = Image.new("RGB", (W, H), stone)
    d = ImageDraw.Draw(img)
    # stone courses
    for y in range(0, H, 34):
        c = tuple(max(0, v - 18) for v in stone)
        d.line([(0, y), (W, y)], fill=c, width=2)
    for f in range(floors):
        y0 = H - (f + 1) * fh
        if f == 0:
            # shopfronts
            for b in range(bays):
                x0 = b * bw + 14
                col = rng.choice([(70, 40, 30), (40, 55, 70), (90, 30, 30), (30, 60, 45)])
                d.rectangle([x0, y0 + 30, x0 + bw - 28, H], fill=col)
                glass = (255, 205, 130) if rng.random() < lit else (55, 62, 70)
                d.rectangle([x0 + 12, y0 + 70, x0 + bw - 40, H - 16], fill=glass)
                d.rectangle([x0, y0 + 30, x0 + bw - 28, y0 + 60], fill=tuple(int(v * 0.7) for v in col))
            d.rectangle([0, y0, W, y0 + 14], fill=tuple(max(0, v - 30) for v in stone))
            continue
        if f == floors - 1:
            # cornice
            d.rectangle([0, y0 + fh - 24, W, y0 + fh - 4], fill=tuple(min(255, v + 15) for v in stone))
        for b in range(bays):
            x0 = b * bw + 50
            wx, wy = x0, y0 + 40
            ww, wh = bw - 100, fh - 70
            # window surround
            d.rectangle([wx - 10, wy - 12, wx + ww + 10, wy + wh + 6], fill=tuple(min(255, v + 12) for v in stone))
            on = rng.random() < lit
            glass = (255, 196, 110) if on else (58, 66, 78)
            d.rectangle([wx, wy, wx + ww, wy + wh], fill=glass)
            # glazing bars
            bar = (235, 228, 210)
            d.line([(wx + ww // 2, wy), (wx + ww // 2, wy + wh)], fill=bar, width=4)
            for k in (1, 2):
                d.line([(wx, wy + wh * k // 3), (wx + ww, wy + wh * k // 3)], fill=bar, width=3)
            # reflections
            if not on:
                d.polygon([(wx + 4, wy + wh - 10), (wx + ww * 0.6, wy + 6), (wx + ww * 0.8, wy + 6), (wx + 10, wy + wh - 4)],
                          fill=(88, 98, 112))
            # shutters
            sc = rng.choice([(70, 78, 70), (88, 94, 100), (110, 98, 80)])
            d.rectangle([wx - 34, wy, wx - 12, wy + wh], fill=sc)
            d.rectangle([wx + ww + 12, wy, wx + ww + 34, wy + wh], fill=sc)
            # balcony rail (2nd and 5th floor continuous; others small)
            if f in (2, floors - 2):
                pass
            else:
                d.rectangle([wx - 6, wy + wh - 30, wx + ww + 6, wy + wh - 2], outline=(30, 30, 32), width=3)
                for k in range(wx, wx + ww, 9):
                    d.line([(k, wy + wh - 30), (k, wy + wh)], fill=(30, 30, 32), width=2)
        if f in (2, floors - 2):
            y = y0 + fh - 38
            d.rectangle([0, y, W, y + 8], fill=(40, 38, 40))
            d.rectangle([0, y + 34, W, y + 40], fill=tuple(max(0, v - 50) for v in stone))
            for k in range(0, W, 10):
                d.line([(k, y), (k, y + 34)], fill=(35, 33, 36), width=2)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    return _save(_grain(img, 6, seed), name + ".png")


def slate(name="slate"):
    W, H = 512, 512
    img = Image.new("RGB", (W, H), (92, 104, 120))
    d = ImageDraw.Draw(img)
    rng = random.Random(3)
    for y in range(0, H, 24):
        off = (y // 24) % 2 * 20
        for x in range(-40 + off, W, 40):
            c = 86 + rng.randint(-10, 12)
            d.rectangle([x + 1, y + 1, x + 38, y + 22], fill=(c, c + 10, c + 26))
    return _save(_grain(img, 6), name + ".png")


def dormer_roof(name="roof"):
    """Mansard roof face with dormer windows & chimneys hint."""
    W, H = 900, 400
    img = Image.new("RGB", (W, H), (88, 100, 116))
    d = ImageDraw.Draw(img)
    rng = random.Random(4)
    for y in range(0, H, 18):
        off = (y // 18) % 2 * 15
        for x in range(-30 + off, W, 30):
            c = 84 + rng.randint(-8, 10)
            d.rectangle([x + 1, y + 1, x + 28, y + 16], fill=(c, c + 10, c + 24))
    for b in range(5):
        x0 = b * 180 + 60
        d.rectangle([x0 - 6, 140, x0 + 66, 330], fill=(226, 214, 190))
        d.polygon([(x0 - 14, 140), (x0 + 30, 96), (x0 + 74, 140)], fill=(70, 80, 94))
        d.rectangle([x0 + 8, 170, x0 + 52, 320], fill=(55, 62, 74))
        d.line([(x0 + 30, 170), (x0 + 30, 320)], fill=(225, 220, 205), width=3)
    d.rectangle([0, 0, W, 12], fill=(60, 66, 76))
    return _save(_grain(img, 5), name + ".png")


def cobble(name="cobble"):
    W, H = 512, 512
    img = Image.new("RGB", (W, H), (74, 70, 66))
    d = ImageDraw.Draw(img)
    rng = random.Random(5)
    for y in range(0, H, 22):
        off = rng.randint(0, 20)
        for x in range(-30 + off, W, 30):
            c = 110 + rng.randint(-22, 22)
            d.rounded_rectangle([x + 2, y + 2, x + 28, y + 20], 5, fill=(c, c - 6, c - 14))
    return _save(_grain(img.filter(ImageFilter.GaussianBlur(0.7)), 8), name + ".png")


def pavement(name="pavement"):
    W, H = 512, 512
    img = Image.new("RGB", (W, H), (176, 166, 150))
    d = ImageDraw.Draw(img)
    rng = random.Random(6)
    for y in range(0, H, 64):
        for x in range(0, W, 128):
            c = 170 + rng.randint(-12, 12)
            d.rectangle([x + 2, y + 2, x + 126, y + 62], fill=(c, c - 8, c - 20))
    return _save(_grain(img, 6), name + ".png")


def awning(name="awning", c1=(150, 32, 36), c2=(236, 222, 196)):
    W, H = 512, 256
    img = Image.new("RGB", (W, H), c2)
    d = ImageDraw.Draw(img)
    for x in range(0, W, 64):
        d.rectangle([x, 0, x + 31, H], fill=c1)
    for x in range(0, W, 32):
        d.pieslice([x - 2, H - 40, x + 34, H - 4], 0, 180, fill=c1 if (x // 32) % 2 == 0 else c2)
    return _save(_grain(img, 6), name + ".png")


def sign(name, text, w=1024, h=180, bg=(26, 40, 32), fg=(222, 186, 108), size=110, font=SERIF):
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    f = _font(font, size)
    tw = d.textlength(text, font=f)
    d.rectangle([8, 8, w - 9, h - 9], outline=fg, width=5)
    d.text(((w - tw) / 2, (h - size) / 2 - size * 0.1), text, font=f, fill=fg)
    return _save(_grain(img, 4), name + ".png")


def paper_tex(name="paper", w=1024, h=1400, tint=(240, 232, 212), seed=1):
    img = Image.new("RGB", (w, h), tint)
    img = _grain(img, 7, seed)
    return img


def newspaper(name="newspaper"):
    w, h = 1400, 1900
    img = paper_tex(w=w, h=h, tint=(228, 218, 196), seed=2)
    d = ImageDraw.Draw(img)
    ink = (34, 30, 28)
    d.text((w / 2 - d.textlength("LE JOURNAL DE PARIS", font=_font(SERIF, 104)) / 2, 40), "LE JOURNAL DE PARIS",
           font=_font(SERIF, 104), fill=ink)
    d.line([(50, 175), (w - 50, 175)], fill=ink, width=6)
    sm = _font(SERIF_R, 30)
    d.text((60, 186), "PARIS  —  1925", font=sm, fill=ink)
    d.text((w - 60 - d.textlength("25 CENTIMES", font=sm), 186), "25 CENTIMES", font=sm, fill=ink)
    d.line([(50, 232), (w - 50, 232)], fill=ink, width=3)
    big = _font(SERIF, 118)
    for i, ln in enumerate(["LA TOUR EIFFEL", "COÛTE TROP CHER"]):
        tw = d.textlength(ln, font=big)
        d.text(((w - tw) / 2, 262 + i * 136), ln, font=big, fill=ink)
    sub = _font(SERIF_I, 44)
    ln = "Costly repairs: who will pay for the old tower?"
    tw = d.textlength(ln, font=sub)
    d.text(((w - tw) / 2, 552), ln, font=sub, fill=ink)
    d.line([(50, 630), (w - 50, 630)], fill=ink, width=3)
    # engraving-style tower illustration
    cx0, top, bot = 380, 680, 1350
    for k in range(-1, 2, 2):
        pts = []
        for i in range(40):
            z = i / 39
            hw = 230 * (1 - z) ** 2.2 + 12
            pts.append((cx0 + k * hw, bot - z * (bot - top)))
        d.line(pts, fill=ink, width=7)
    for i in range(1, 30):
        z = i / 30
        hw = 230 * (1 - z) ** 2.2 + 12
        y = bot - z * (bot - top)
        d.line([(cx0 - hw, y), (cx0 + hw, y)], fill=ink, width=2)
        if i % 2 == 0:
            z2 = (i + 2) / 30
            hw2 = 230 * (1 - z2) ** 2.2 + 12
            y2 = bot - z2 * (bot - top)
            d.line([(cx0 - hw, y), (cx0 + hw2, y2)], fill=ink, width=1)
            d.line([(cx0 + hw, y), (cx0 - hw2, y2)], fill=ink, width=1)
    d.arc([cx0 - 160, bot - 160, cx0 + 160, bot + 120], 180, 360, fill=ink, width=5)
    d.rectangle([cx0 - 170, bot - 240, cx0 + 170, bot - 222], fill=ink)
    d.rectangle([cx0 - 90, bot - 470, cx0 + 90, bot - 456], fill=ink)
    # columns of text (greeked)
    rng = random.Random(7)
    for col in range(2):
        x0 = 700 + col * 340
        for y in range(670, 1820, 26):
            ww = rng.randint(240, 310)
            if rng.random() < 0.08:
                continue
            d.line([(x0, y), (x0 + ww, y)], fill=(80, 74, 66), width=9)
    for y in range(1400, 1820, 26):
        d.line([(60, y), (60 + rng.randint(500, 590), y)], fill=(80, 74, 66), width=9)
    d.rectangle([20, 20, w - 20, h - 20], outline=(190, 178, 152), width=4)
    return _save(img.filter(ImageFilter.GaussianBlur(0.8)), name + ".png")


def letterhead(name="letter", signed=False, stamped=False):
    w, h = 1100, 1500
    img = paper_tex(w=w, h=h, tint=(244, 238, 222), seed=3)
    d = ImageDraw.Draw(img)
    ink = (28, 30, 52)
    # republic emblem (laurel circle) + header
    cx0 = w / 2
    d.ellipse([cx0 - 70, 50, cx0 + 70, 190], outline=ink, width=5)
    d.text((cx0 - d.textlength("RF", font=_font(SERIF, 70)) / 2, 78), "RF", font=_font(SERIF, 70), fill=ink)
    f1 = _font(SERIF, 46)
    f2 = _font(SERIF_R, 32)
    for i, (ln, f) in enumerate([("RÉPUBLIQUE FRANÇAISE", f1), ("Ministère des Postes et Télégraphes", f2)]):
        d.text((cx0 - d.textlength(ln, font=f) / 2, 214 + i * 62), ln, font=f, fill=ink)
    d.line([(120, 320), (w - 120, 320)], fill=ink, width=3)
    d.text((120, 350), "CONFIDENTIEL", font=_font(SERIF, 40), fill=(140, 24, 24))
    rng = random.Random(9)
    for y in range(440, 1080, 38):
        ww = rng.randint(620, 860)
        d.line([(120, y), (120 + ww, y)], fill=(70, 72, 92), width=10)
    if signed:
        pts = []
        for i in range(120):
            u = i / 119
            pts.append((620 + u * 330, 1220 - 40 * math.sin(u * 14) * (1 - u * 0.5) - u * 30))
        d.line(pts, fill=(20, 24, 70), width=7)
    d.line([(600, 1260), (1000, 1260)], fill=ink, width=2)
    d.text((640, 1275), "Le Directeur général adjoint", font=_font(SERIF_I, 28), fill=ink)
    if stamped:
        stamp_mark(d, 330, 1220, 140)
    return _save(img.filter(ImageFilter.GaussianBlur(0.7)), name + ".png")


def stamp_mark(d, x, y, r, col=(150, 30, 40)):
    d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=9)
    d.ellipse([x - r + 22, y - r + 22, x + r - 22, y + r - 22], outline=col, width=4)
    f = _font(SERIF, 34)
    for i, ln in enumerate(["MINISTÈRE", "PARIS"]):
        d.text((x - d.textlength(ln, font=f) / 2, y - 40 + i * 44), ln, font=f, fill=col)


def stamp_seal(name="stamp_mark"):
    img = Image.new("RGBA", (400, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    stamp_mark(d, 200, 200, 170)
    return _save(img.filter(ImageFilter.GaussianBlur(1.0)), name + ".png")


def envelope_tex(name="envelope", addressed=True):
    w, h = 1200, 700
    img = paper_tex(w=w, h=h, tint=(232, 220, 190), seed=4)
    d = ImageDraw.Draw(img)
    if addressed:
        f = _font(SERIF_I, 46)
        for i, ln in enumerate(["Monsieur A. Poisson", "Fers & Métaux", "Paris"]):
            d.text((520, 330 + i * 64), ln, font=f, fill=(30, 30, 60))
        d.rectangle([1000, 50, 1130, 200], fill=(150, 60, 50))
        d.rectangle([1012, 62, 1118, 188], outline=(240, 220, 200), width=3)
    return _save(img.filter(ImageFilter.GaussianBlur(0.6)), name + ".png")


def banknote(name="banknote"):
    w, h = 900, 480
    img = Image.new("RGB", (w, h), (196, 186, 150))
    d = ImageDraw.Draw(img)
    d.rectangle([14, 14, w - 15, h - 15], outline=(80, 70, 110), width=10)
    d.rectangle([40, 40, w - 41, h - 41], outline=(110, 96, 130), width=3)
    d.ellipse([w / 2 - 120, h / 2 - 140, w / 2 + 120, h / 2 + 140], fill=(176, 160, 150), outline=(80, 70, 110), width=5)
    f = _font(SERIF, 90)
    d.text((70, 100), "1000", font=f, fill=(80, 60, 100))
    d.text((w - 70 - d.textlength("1000", font=f), h - 160), "1000", font=f, fill=(80, 60, 100))
    f2 = _font(SERIF, 34)
    t = "BANQUE DE FRANCE"
    d.text((w / 2 - d.textlength(t, font=f2) / 2, 50), t, font=f2, fill=(70, 50, 90))
    for i in range(0, w, 7):
        d.line([(i, 30), (i + 40, h - 30)], fill=(186, 176, 146), width=1)
    return _save(_grain(img.filter(ImageFilter.GaussianBlur(0.8)), 6), name + ".png")


def contract(name="contract", fake=False):
    """The 'agreement' Poisson re-reads."""
    w, h = 1100, 1500
    img = paper_tex(w=w, h=h, tint=(242, 234, 214), seed=8)
    d = ImageDraw.Draw(img)
    ink = (28, 30, 52)
    f1 = _font(SERIF, 54)
    t = "CONTRAT DE VENTE"
    d.text((w / 2 - d.textlength(t, font=f1) / 2, 90), t, font=f1, fill=ink)
    f2 = _font(SERIF_I, 36)
    t = "Tour Eiffel — 7 000 tonnes de fer"
    d.text((w / 2 - d.textlength(t, font=f2) / 2, 170), t, font=f2, fill=ink)
    d.line([(120, 240), (w - 120, 240)], fill=ink, width=3)
    rng = random.Random(11)
    for y in range(290, 1100, 38):
        d.line([(120, y), (120 + rng.randint(600, 860), y)], fill=(70, 72, 92), width=10)
    pts = []
    for i in range(120):
        u = i / 119
        pts.append((620 + u * 330, 1240 - 40 * math.sin(u * 14) * (1 - u * 0.5) - u * 30))
    d.line(pts, fill=(20, 24, 70), width=7)
    stamp_mark(d, 330, 1240, 130)
    return _save(img.filter(ImageFilter.GaussianBlur(0.7)), name + ".png")


def blueprint(name="blueprint"):
    w, h = 2048, 2048
    img = Image.new("RGB", (w, h), (226, 214, 186))
    d = ImageDraw.Draw(img)
    for i in range(0, w, 64):
        d.line([(i, 0), (i, h)], fill=(196, 182, 150), width=2)
        d.line([(0, i), (w, i)], fill=(196, 182, 150), width=2)
    for i in range(0, w, 256):
        d.line([(i, 0), (i, h)], fill=(170, 150, 118), width=4)
        d.line([(0, i), (w, i)], fill=(170, 150, 118), width=4)
    return _save(_grain(img, 6), name + ".png")


def wallpaper(name="wallpaper", base=(96, 30, 34), fg=(126, 52, 48)):
    w, h = 512, 512
    img = Image.new("RGB", (w, h), base)
    d = ImageDraw.Draw(img)
    for y in range(0, h, 128):
        for x in range(0, w, 128):
            ox = 64 if (y // 128) % 2 else 0
            cx0, cy0 = x + ox, y + 64
            d.ellipse([cx0 - 26, cy0 - 40, cx0 + 26, cy0 + 40], outline=fg, width=6)
            d.line([(cx0, cy0 - 56), (cx0, cy0 + 56)], fill=fg, width=4)
    for x in range(0, w, 32):
        d.line([(x, 0), (x, h)], fill=tuple(max(0, v - 8) for v in base), width=2)
    return _save(_grain(img, 5), name + ".png")


def parquet(name="parquet"):
    w, h = 1024, 1024
    img = Image.new("RGB", (w, h), (110, 64, 36))
    d = ImageDraw.Draw(img)
    rng = random.Random(12)
    for y in range(0, h, 64):
        for x in range(0, w, 256):
            c = rng.randint(-20, 20)
            ox = 128 if (y // 64) % 2 else 0
            d.rectangle([x + ox - 256, y, x + ox - 2, y + 62], fill=(118 + c, 68 + c // 2, 36 + c // 3))
            d.rectangle([x + ox, y, x + ox + 254, y + 62], fill=(112 + c, 64 + c // 2, 34 + c // 3))
            for k in range(6):
                yy = y + rng.randint(4, 58)
                d.line([(x + ox, yy), (x + ox + 254, yy + rng.randint(-3, 3))], fill=(96 + c, 54, 28), width=1)
    return _save(_grain(img.filter(ImageFilter.GaussianBlur(0.5)), 6), name + ".png")


def marble(name="marble"):
    w, h = 1024, 1024
    rng = np.random.default_rng(13)
    yy, xx = np.mgrid[0:h, 0:w] / w
    v = np.zeros((h, w))
    for k in range(5):
        f = 2 ** k
        ph = rng.random(2) * 10
        v += np.sin((xx * 3 + yy * 2) * f * 2.5 + np.sin(yy * f * 6 + ph[0]) * 1.4 + ph[1]) / f
    vein = np.exp(-np.abs(v) * 7)
    base = np.array([236, 228, 214]) - vein[..., None] * np.array([70, 70, 64])
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for i in range(0, w, 256):
        d.line([(i, 0), (i, h)], fill=(196, 186, 170), width=3)
        d.line([(0, i), (w, i)], fill=(196, 186, 170), width=3)
    return _save(img, name + ".png")


def tag(name="tag_7000"):
    w, h = 700, 380
    img = Image.new("RGB", (w, h), (232, 214, 170))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 10, w - 11, h - 11], outline=(120, 80, 40), width=8)
    f = _font(SERIF, 120)
    t = "7 000 t"
    d.text((w / 2 - d.textlength(t, font=f) / 2, 40), t, font=f, fill=(40, 30, 24))
    f2 = _font(SERIF, 52)
    t = "FER • À VENDRE"
    d.text((w / 2 - d.textlength(t, font=f2) / 2, 220), t, font=f2, fill=(140, 30, 30))
    d.ellipse([40, h / 2 - 25, 90, h / 2 + 25], fill=(30, 26, 24))
    return _save(_grain(img, 5), name + ".png")


def station_sign(name="station_sign"):
    return sign(name, "PARIS — GARE DE L'EST", w=1400, h=200, bg=(30, 44, 70), fg=(236, 226, 200), size=96)


def office_sign(name="office_sign"):
    return sign(name, "A. POISSON — FERS & MÉTAUX", w=1400, h=200, bg=(48, 30, 20), fg=(222, 186, 108), size=86)


def hotel_sign(name="hotel_sign"):
    return sign(name, "GRAND HÔTEL", w=1200, h=220, bg=(20, 30, 26), fg=(230, 192, 110), size=130)


def cafe_sign(name="cafe_sign"):
    return sign(name, "CAFÉ DE LA TOUR", w=1200, h=200, bg=(110, 24, 28), fg=(240, 220, 170), size=110)


def all_textures():
    out = {}
    for k in range(4):
        stones = [(224, 208, 176), (230, 216, 186), (216, 200, 168), (234, 222, 196)]
        out[f"facade_{k}"] = facade(f"facade_{k}", seed=k + 1, stone=stones[k], floors=6 + (k % 2))
        out[f"facade_lit_{k}"] = facade(f"facade_lit_{k}", seed=k + 1, stone=stones[k], floors=6 + (k % 2), lit=0.35)
    out["roof"] = dormer_roof()
    out["slate"] = slate()
    out["cobble"] = cobble()
    out["pavement"] = pavement()
    out["awning"] = awning()
    out["awning_green"] = awning("awning_green", (36, 80, 56), (232, 222, 196))
    out["newspaper"] = newspaper()
    out["letter"] = letterhead("letter")
    out["letter_signed"] = letterhead("letter_signed", signed=True)
    out["letter_stamped"] = letterhead("letter_stamped", signed=True, stamped=True)
    out["stamp_mark"] = stamp_seal()
    out["envelope"] = envelope_tex()
    out["envelope_plain"] = envelope_tex("envelope_plain", addressed=False)
    out["banknote"] = banknote()
    out["contract"] = contract()
    out["blueprint"] = blueprint()
    out["wallpaper"] = wallpaper()
    out["wallpaper_green"] = wallpaper("wallpaper_green", (34, 58, 48), (60, 86, 70))
    out["parquet"] = parquet()
    out["marble"] = marble()
    out["tag"] = tag()
    out["station_sign"] = station_sign()
    out["office_sign"] = office_sign()
    out["hotel_sign"] = hotel_sign()
    out["cafe_sign"] = cafe_sign()
    return out


if __name__ == "__main__":
    for k, v in all_textures().items():
        print(k, v)
