"""Troy 3D orchestrator.

python -m episodes.troy3d.render3d preview          # 1 low-res frame per shot -> build/troy3d/preview_sheet.png
python -m episodes.troy3d.render3d blender          # all Blender frames (resumable)
python -m episodes.troy3d.render3d comp             # composite + captions -> build/troy3d/video_silent.mp4
python -m episodes.troy3d.render3d final            # mux with the episode mix -> output/
"""
import json
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import cairo
import cv2
import numpy as np

from cinecode.core import back_out, ease_out, hexc, lerp, prog, smooth, src
from episodes.troy3d import comp3d
from episodes.troy3d.shots3d import SHOTS3, Split26, shot_at
from episodes.troy_en import gfx
from episodes.troy_en.render import draw_caption, draw_tag
from episodes.troy_en.shots import DUR, label

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "troy3d")
BLENDER = "/opt/blender/blender-4.2.3-linux-x64/blender"
FPS = 30
NFR = int(math.ceil(DUR * FPS))
W, H = 1080, 1920


def frames_of(sh):
    return [f for f in range(NFR) if sh.t0 <= f / FPS < sh.t1 or (sh is SHOTS3[-1] and f / FPS >= sh.t0)]


def sub_renders(sh, f):
    """[(subshot, local_t, key)] Blender renders needed for global frame f."""
    t = f / FPS - sh.t0
    if isinstance(sh, Split26):
        out = [(sh.top, t, "top")]
        if t >= sh.b0():
            out.append((sh.bottom, t - sh.b0(), "bot"))
        return out
    return [(sh, t, "main")]


def frame_dir(i, key, set_name):
    return os.path.join(BUILD, "frames", f"{i:02d}_{key}_{set_name}")


def make_jobs(res=(720, 1280), samples=12, only=None, preview=False):
    jobs = {}
    spr_dir = os.path.join(BUILD, "spr")
    os.makedirs(spr_dir, exist_ok=True)
    for i, sh in enumerate(SHOTS3):
        frs = frames_of(sh)
        if preview:
            frs = [frs[len(frs) // 2]]
        if only is not None and i not in only:
            continue
        for f in frs:
            for sub, t, key in sub_renders(sh, f):
                st = sub.set_at(t)
                d = frame_dir(i, key, st) + ("_prev" if preview else "")
                jf = sub.job_frame(t, f)
                if preview:
                    c = sub.cam(t, (360, 640))
                    jf.update(c.job())
                cards = []
                for k, act in enumerate(sub.actors(t)):
                    cards.append(comp3d.write_sprite(act, os.path.join(spr_dir, f"{i:02d}{key}_{f:05d}_{k}.png")))
                jf["actors"] = cards
                j = jobs.setdefault(d, {"set": st, "out": d, "res": list(res), "samples": samples, "horse": sub.horse,
                                        "frames": []})
                j["frames"].append(jf)
    paths = []
    for d, j in jobs.items():
        os.makedirs(d, exist_ok=True)
        p = d + ".json"
        json.dump(j, open(p, "w"))
        paths.append(p)
    return paths


def run_blender(paths, log=None):
    for p in paths:
        j = json.load(open(p))
        todo = [f for f in j["frames"] if not os.path.exists(os.path.join(j["out"], f"color_{f['index']:04d}.png"))]
        if not todo:
            continue
        print(f"[blender] {os.path.basename(p)}: {len(todo)} frames", flush=True)
        subprocess.run([BLENDER, "-b", "--factory-startup", "--python",
                        os.path.join(ROOT, "episodes", "troy3d", "bl_build.py"), "--", p],
                       stdout=log or subprocess.DEVNULL, stderr=subprocess.STDOUT)


# ------------------------------------------------------------------ compositing
def motion_blur(img, c0, c1):
    """2D camera blur from two consecutive 3D cameras."""
    p = c1.project(c0.loc + c0.f * 12)
    if p is None:
        return img
    vx, vy = (W / 2 - p[0]), (H / 2 - p[1])
    d0 = np.linalg.norm(c0.target - c0.loc)
    d1 = np.linalg.norm(c1.target - c1.loc)
    zr = (c1.lens / c0.lens) * (d0 / max(1e-3, d1)) - 1
    sp = math.hypot(vx, vy)
    if sp < 18 and abs(zr) < 0.03:
        return img
    a = img.astype(np.float32)
    if sp >= 18:
        L = int(min(300, sp * 1.4)) | 1
        k = np.zeros((L, L), np.float32)
        c = L // 2
        ang = math.atan2(vy, vx)
        cv2.line(k, (int(c - math.cos(ang) * c), int(c - math.sin(ang) * c)),
                 (int(c + math.cos(ang) * c), int(c + math.sin(ang) * c)), 1.0, 1)
        k /= k.sum()
        a = cv2.filter2D(a, -1, k, borderType=cv2.BORDER_REFLECT)
    if abs(zr) >= 0.03:
        n = int(min(36, 8 + abs(zr) * 140))
        acc = np.zeros_like(a)
        for i in range(n):
            M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + zr * i / (n - 1))
            acc += cv2.warpAffine(a, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        a = acc / n
    return np.clip(a, 0, 255).astype(np.uint8)


def comp_sub(i, sub, t, key, f, preview=False):
    st = sub.set_at(t)
    d = frame_dir(i, key, st) + ("_prev" if preview else "")
    bg, z = comp3d.load_bg(os.path.join(d, f"color_{f:04d}.png"), os.path.join(d, f"depth_{f:04d}.exr"))
    cam = sub.cam(t)
    joints = {}

    def extra(cx, J):
        joints.update(J)
        sub.overlay(cx, t, cam, J)
    surf = comp3d.composite(bg, z, cam, sub.actors(t), tint=comp3d_tint(sub.light), draw_extra=extra,
                            fog_args=comp3d_fog(sub.light))
    arr = gfx.to_np(surf).copy()
    if not preview:
        arr = motion_blur(arr, sub.cam(max(0.0, t - 1 / FPS)), cam)
    return gfx.from_np(arr)


def comp3d_tint(light):
    from episodes.troy3d.shots3d import TINT
    return TINT[light]


def comp3d_fog(light):
    from episodes.troy3d.shots3d import FOG
    return FOG[light]


def render_frame(f, preview=False):
    T = f / FPS
    sh = shot_at(T)
    i = SHOTS3.index(sh)
    t = T - sh.t0
    if isinstance(sh, Split26):
        s = gfx.surface()
        cx = cairo.Context(s)
        top = comp_sub(i, sh.top, t, "top", f, preview)
        split = ease_out(prog(t, sh.b0(), sh.b0() + 0.35))
        top_h = lerp(H, H / 2, split)
        cx.save()
        cx.rectangle(0, 0, W, top_h)
        cx.clip()
        cx.set_source_surface(top, 0, -(H - top_h) / 2 + 160 * split)
        cx.paint()
        cx.restore()
        label(cx, "10 YEARS", W / 2, 150, 92, hexc("#FFFFFF"), alpha=smooth(prog(t, 0.2, 0.5)))
        if t >= sh.b0():
            bot = comp_sub(i, sh.bottom, t - sh.b0(), "bot", f, preview)
            cx.save()
            cx.rectangle(0, top_h, W, H - top_h)
            cx.clip()
            cx.set_source_surface(bot, 0, top_h - 560 + (1 - split) * 200)
            cx.paint()
            cx.restore()
            from cinecode.core import line
            line(cx, [(0, top_h), (W, top_h)], (1, 1, 1, 1), 12)
            line(cx, [(0, top_h), (W, top_h)], hexc("#14141A"), 4)
            k = back_out(prog(t, sh.b0() + 0.9, sh.b0() + 1.25))
            if k > 0:
                cx.save()
                cx.translate(W / 2, top_h + 110)
                cx.scale(k, k)
                label(cx, "1 AFTERNOON", 0, 0, 92, hexc("#FFD60A"))
                cx.restore()
    else:
        s = comp_sub(i, sh, t, "main", f, preview)
        cx = cairo.Context(s)
    tags = sh.tags(t)
    if tags:
        name, txt = tags[0]
        t_on = t
        while t_on - 1 / FPS >= 0 and sh.tags(t_on - 1 / FPS):
            t_on -= 1 / FPS
        draw_tag(cx, name, txt, back_out(prog(t - t_on, 0, 0.2)) if t - t_on < 0.2 else 1.0)
    draw_caption(cx, T)
    return s


def _chunk(args):
    k, f0, f1 = args
    out = os.path.join(BUILD, f"part_{k:02d}.mp4")
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}", "-r",
                          str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt",
                          "yuv420p", out], stdin=subprocess.PIPE)
    for f in range(f0, f1):
        s = render_frame(f)
        s.flush()
        p.stdin.write(bytes(s.get_data()))
    p.stdin.close()
    p.wait()
    return out


def comp_video(workers=4):
    k = math.ceil(NFR / (workers * 3))
    jobs = [(i, f0, min(NFR, f0 + k)) for i, f0 in enumerate(range(0, NFR, k))]
    with Pool(workers) as pool:
        parts = pool.map(_chunk, jobs, chunksize=1)
    lst = os.path.join(BUILD, "parts.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    out = os.path.join(BUILD, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    print("wrote", out)


def final():
    out = os.path.join(ROOT, "output", "Just_Needy_The_Trojan_Horse_3D_EN.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(BUILD, "video_silent.mp4"), "-i",
                    os.path.join(ROOT, "build", "troy_en", "mix.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    print("final", out)


if __name__ == "__main__":
    cmd = sys.argv[1]
    only = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else None
    if cmd == "preview":
        paths = make_jobs((360, 640), 8, only, preview=True)
        run_blender(paths)
        outs = []
        for i, sh in enumerate(SHOTS3):
            if only is not None and i not in only:
                continue
            frs = frames_of(sh)
            f = frs[len(frs) // 2]
            p = os.path.join(BUILD, f"prev_{i:02d}.png")
            render_frame(f, preview=True).write_to_png(p)
            outs.append(p)
        cols = 7
        args, fc = [], ""
        for j, p in enumerate(outs):
            args += ["-i", p]
            fc += f"[{j}]scale=270:480[v{j}];"
        rows = math.ceil(len(outs) / cols)
        for j in range(len(outs), rows * cols):
            args += ["-f", "lavfi", "-i", "color=c=black:s=270x480"]
            fc += f"[{j}]null[v{j}];"
        fc += "".join(f"[v{j}]" for j in range(rows * cols)) + f"xstack=inputs={rows * cols}:layout=" + "|".join(
            f"{(j % cols) * 270}_{(j // cols) * 480}" for j in range(rows * cols))
        subprocess.run(["ffmpeg", "-v", "error", "-y"] + args + ["-filter_complex", fc, "-frames:v", "1",
                                                                  os.path.join(BUILD, "preview_sheet.png")])
        print("sheet", os.path.join(BUILD, "preview_sheet.png"))
    elif cmd == "blender":
        paths = make_jobs(only=only)
        with open(os.path.join(BUILD, "blender.log"), "a") as log:
            run_blender(paths, log)
        print("blender done")
    elif cmd == "comp":
        comp_video()
    elif cmd == "final":
        final()
