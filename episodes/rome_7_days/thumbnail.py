"""YouTube thumbnail (same caption typography as the episode)."""
import os

import cairo

from cinecode import captions
from cinecode import props as P
from cinecode import sets as S
from cinecode.characters import HERO, hero_pose, max_pose, run, soldier
from cinecode.core import H, W, Cam
from episodes.rome_7_days.common import GY, WET_MAX, vignette
from episodes.rome_7_days.episode import OUT


def render(path):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cx = cairo.Context(s)
    cam = Cam(1180, 640, 1.55)
    S.rome_street(cx, cam, 1.0, x0=-1500, x1=6000)
    cx.save()
    cam.apply(cx)
    for i in range(2):
        soldier(i).draw(cx, run(max_pose(1820 + i * 170, GY - 10, 0.3 + i * 0.3, f=-1, s=1.12, mouth="yell",
                                         brows="angry"), 0.3 + i * 0.3, 2.1))
    mp = run(max_pose(1480, GY, 0.55, f=-1, mouth="yell", eyes="angry", brows="angry"), 0.55, 2.0)
    mp = mp.but(arm_b=95, elb_b=-8, lean=mp.lean + 10)
    J = WET_MAX.draw(cx, mp)
    P.drips(cx, 1480, J["head"][1] + 40, 120, 0.4, 6, 0.9)
    hp = run(hero_pose(1080, GY, 0.2, f=-1, eyes="wide", mouth="scream", brows="worried", sweat=1.0,
                       look=(1, 0)), 0.2, 2.4, 1.0, flail=True)
    HJ = HERO.draw(cx, hp.but(s=1.08))
    P.watch(cx, HJ["hand_a"][0] - 10, HJ["hand_a"][1] - 20, 0.55, 0.3, display="0:03", lcd_glow=1, label=False)
    cx.restore()
    vignette(cx, 0.35)
    captions.draw_accent(cx, 10.0, {"text": "STUCK IN [ROME]\nFOR 7 DAYS", "t0": 0.0, "t1": 20.0,
                                    "size": 118, "pos": (600, 230)})
    s.write_to_png(path)
    return path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    full = render(os.path.join(OUT, "thumbnail_1920x1080.png"))
    from PIL import Image
    Image.open(full).convert("RGB").resize((1280, 720), Image.LANCZOS).save(
        os.path.join(OUT, "thumbnail_1280x720.jpg"), quality=92)
    print(full)
