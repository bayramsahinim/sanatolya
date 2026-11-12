"""Assemble and render Just Needy — Zombie Apocalypse, Episode 1 (vertical Short, 1080x1920).

usage:
  python -m episodes.zombie_ep01.episode timeline             # shot list + total duration
  python -m episodes.zombie_ep01.episode stills t1 t2 ...     # PNG previews at global times
  python -m episodes.zombie_ep01.episode sheet [n]            # contact sheet of n frames
  python -m episodes.zombie_ep01.episode audio                # mix soundtrack + write SRT
  python -m episodes.zombie_ep01.episode video [--draft]      # render frames -> mp4 (needs audio)
  python -m episodes.zombie_ep01.episode all
"""
import episodes.zombie_ep01  # noqa: F401  (sets the vertical frame size before cinecode loads)

import json
import multiprocessing as mp
import os
import subprocess
import sys
import time

import cairo
import numpy as np

from cinecode import audio as A
from cinecode import tts
from cinecode.align import trim
from cinecode.core import FPS, H, W
from cinecode.timeline import Episode, VoiceDB
from episodes.zombie_ep01.script import LINES, SLUG, TEXT, TITLE
from episodes.zombie_series import sound as Z

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "zombie_ep01")
OUT = os.path.join(ROOT, "output", "zombie_ep01")
LINES_JSON = os.path.join(ROOT, "assets", "audio", "tts", "zombie_ep01", "lines.json")
CLIP_PRE, CLIP_POST = 0.05, 0.12
VIDEO = os.path.join(OUT, SLUG + ".mp4")
SRT = os.path.join(OUT, SLUG + ".en.srt")
MIX = os.path.join(BUILD, "mix.wav")


def load_voice():
    durs = {}
    for lid, v in json.load(open(LINES_JSON)).items():
        durs[lid] = v["end"] - v["start"] + CLIP_PRE + CLIP_POST
    return VoiceDB(durs, TEXT, 1.0)


def build_episode():
    from episodes.zombie_ep01 import shots_a as SA
    from episodes.zombie_ep01 import shots_b as SB
    shots = [SA.S1Window(), SA.S1FaceCU(),
             SA.S2Bed(), SA.S2Chase(), SA.S2Crawl(), SA.S2Curtains(), SA.S2Lock(), SA.S2Breakfast(),
             SA.S3Montage(), SA.S3Smug(),
             SA.S4Faucet(), SA.S4Pump(), SA.S4Diagram(), SA.S4Bottle(),
             SB.S5Tiptoe(), SB.S5Rooster(), SB.S5Stop(), SB.S5Turn(), SB.S5Feathers(),
             SB.S6Window(), SB.S6Creak(), SB.S6Hallway(),
             SB.S7Door(), SB.S7Face(), SB.S7Black()]
    return Episode(shots, load_voice())


# ------------------------------------------------------------------ stills
def stills(times, prefix="still"):
    ep = build_episode()
    os.makedirs(BUILD, exist_ok=True)
    paths = []
    for gt in times:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        cx = cairo.Context(s)
        cx.set_source_rgb(0, 0, 0)
        cx.paint()
        ep.render(cx, gt)
        p = os.path.join(BUILD, f"{prefix}_{gt:06.2f}.png")
        s.write_to_png(p)
        paths.append(p)
    return paths


def sheet(n=24, times=None, path=None):
    from PIL import Image, ImageDraw
    ep = build_episode()
    times = times or [ep.duration * (k + 0.5) / n for k in range(n)]
    cols = 6
    tw, th = 216, 384
    rows = (len(times) + cols - 1) // cols
    out = Image.new("RGB", (cols * tw, rows * (th + 22)), (20, 20, 20))
    d = ImageDraw.Draw(out)
    for k, gt in enumerate(times):
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        cx = cairo.Context(s)
        cx.set_source_rgb(0, 0, 0)
        cx.paint()
        ep.render(cx, gt)
        im = Image.frombuffer("RGBA", (W, H), bytes(s.get_data()), "raw", "BGRA", 0, 1).convert("RGB")
        im = im.resize((tw, th))
        x, y = (k % cols) * tw, (k // cols) * (th + 22)
        out.paste(im, (x, y))
        i = ep.shot_at(gt)
        d.text((x + 4, y + th + 4), f"{gt:5.2f} {type(ep.shots[i]).__name__}", fill=(230, 230, 230))
    path = path or os.path.join(BUILD, "sheet.png")
    out.save(path)
    return path


# ------------------------------------------------------------------ video
_EP = None


def _worker(args):
    a, b, path, scale = args
    global _EP
    if _EP is None:
        _EP = build_episode()
    w, h = int(W * scale) // 2 * 2, int(H * scale) // 2 * 2
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium" if scale == 1 else "veryfast",
           "-crf", "18" if scale == 1 else "26", "-tune", "animation", "-pix_fmt", "yuv420p", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    for i in range(a, b):
        cx = cairo.Context(s)
        cx.set_source_rgb(0, 0, 0)
        cx.paint()
        if scale != 1:
            cx.scale(w / W, h / H)
        _EP.render(cx, i / FPS)
        s.flush()
        pr.stdin.write(bytes(s.get_data()))
    pr.stdin.close()
    pr.wait()
    return path


def render_video(draft=False, workers=4):
    ep = build_episode()
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    n = ep.nframes
    chunks = workers * 4
    step = (n + chunks - 1) // chunks
    jobs = []
    for k in range(chunks):
        a, b = k * step, min(n, (k + 1) * step)
        if a < b:
            jobs.append((a, b, os.path.join(BUILD, f"part_{k:03d}.mp4"), 0.5 if draft else 1.0))
    t = time.time()
    with mp.Pool(workers) as pool:
        for i, _ in enumerate(pool.imap(_worker, jobs)):
            print(f"  chunk {i + 1}/{len(jobs)}  {time.time() - t:.0f}s", flush=True)
    lst = os.path.join(BUILD, "parts.txt")
    with open(lst, "w") as f:
        for _, _, p, _ in jobs:
            f.write(f"file '{p}'\n")
    silent = os.path.join(BUILD, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    silent], check=True)
    final = os.path.join(BUILD, "draft.mp4") if draft else VIDEO
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", MIX, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
                    "-metadata", f"title={TITLE}", final], check=True)
    print("wrote", final, f"{time.time() - t:.0f}s")
    return final


# ------------------------------------------------------------------ audio
def narration_clips():
    takes, clips = {}, {}
    for lid, v in json.load(open(LINES_JSON)).items():
        f = os.path.join(ROOT, v["file"])
        if f not in takes:
            takes[f] = tts.read_wav(f)
        raw = trim(takes[f], v["start"], v["end"], CLIP_PRE, CLIP_POST)
        clips[lid] = A.resample(raw.astype(np.float64), tts.SR, A.SR)
    return clips


def level_voice(x, target=0.16):
    v = x[np.abs(x) > 0.02]
    if len(v) == 0:
        return x
    return x * (target / (np.sqrt((v ** 2).mean()) + 1e-9))


# Per-line delivery level (the ending gets quieter, as directed; the rest sits level).
LINE_GAIN = {"l18": 0.92, "l19": 0.9, "l20": 0.9}


def _beds(ep, n, attr, gain_attr, render, fade_in=0.6, fade_out=0.6):
    """Contiguous runs of the same bed across shots. A shot may end its bed early with
    `music_until` (shot-local seconds): that makes a hard stop (power cut, silence before a scare)."""
    runs = []
    for sh, st in zip(ep.shots, ep.starts):
        name = getattr(sh, attr)
        g = getattr(sh, gain_attr)
        until = getattr(sh, "music_until", None) if attr == "music" else None
        end = st + (until if until is not None else sh.dur)
        hard = until is not None
        if runs and runs[-1][0] == name and not runs[-1][4] and abs(runs[-1][2] - st) < 1e-6:
            runs[-1][2] = end
            runs[-1][4] = hard
        else:
            runs.append([name, st, end, g, hard])
    out = np.zeros(n)
    for name, a, b, g, hard in runs:
        if not name:
            continue
        a2 = max(0.0, a - fade_in / 2)
        b2 = b + (0.06 if hard else fade_out / 2)
        x = render(name, b2 - a2) * g
        ki = min(int(fade_in * A.SR), len(x) // 2)
        ko = min(int((0.08 if hard else fade_out) * A.SR), len(x) // 2)
        if a > 0:
            x[:ki] *= np.linspace(0, 1, ki)
        x[-ko:] *= np.linspace(1, 0, ko)
        A.add(out, x, a2)
    return out


def mix_audio(ep):
    n = int(ep.duration * A.SR) + A.SR
    voice, fx = np.zeros(n), np.zeros(n)
    clips = narration_clips()
    missing = []
    for c in ep.cues:
        if c["type"] == "narr":
            if c["id"] in clips:
                A.add(voice, level_voice(clips[c["id"]]) * LINE_GAIN.get(c["id"], 1.0), c["t0"])
            else:
                missing.append(c["id"])
        elif c["type"] == "sfx" and c["vol"] > 0:
            A.add(fx, Z.get_sfx(c["name"]) * c["vol"], c["t0"])
    music = _beds(ep, n, "music", "music_gain", Z.track)
    amb = _beds(ep, n, "amb", "amb_gain",
                lambda nm, d: np.tile(Z.amb_loop(nm), int(d / 16) + 2)[: int(d * A.SR)], 0.4, 0.4)
    # ducking: beds drop well under the voice, SFX dip a little
    env = A.envelope_follow(voice, 0.02, 0.4)
    k = np.clip(env / 0.06, 0, 1)
    music_g, amb_g, fx_g = 10 ** (-16 / 20), 10 ** (-23 / 20), 10 ** (-7 / 20)
    voice = np.tanh(voice * 1.6) / 1.6          # gentle limiting of voice peaks
    total = voice + music * music_g * (1 - 0.72 * k) + amb * amb_g * (1 - 0.55 * k) + fx * fx_g * (1 - 0.45 * k)
    total = np.tanh(total * 0.95) / 0.95
    os.makedirs(BUILD, exist_ok=True)
    import soundfile as sf
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, total[: int(ep.duration * A.SR)].astype(np.float32), A.SR, subtype="FLOAT")
    for name, sig in (("stem_voice", voice), ("stem_bg", total - voice)):
        sf.write(os.path.join(BUILD, name + ".wav"), sig[: int(ep.duration * A.SR)].astype(np.float32), A.SR,
                 subtype="FLOAT")
    # two-pass loudness normalisation to -14 LUFS / -1.5 dBTP (YouTube)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", MIX], check=True)
    if missing:
        print("WARNING: no audio for", missing)
    return MIX


# ------------------------------------------------------------------ SRT
def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def _wrap(txt, width=40):
    words, rows, cur = txt.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            rows.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    rows.append(cur)
    if len(rows) > 2:
        half = len(words) // 2
        rows = [" ".join(words[:half]), " ".join(words[half:])]
    return rows


def write_srt(ep, path=SRT):
    """One cue per narration line, timed to the speech inside each clip (not the clip padding)."""
    cues = sorted([c for c in ep.cues if c["type"] == "narr"], key=lambda c: c["t0"])
    out = []
    for i, c in enumerate(cues):
        t0 = c["t0"] + CLIP_PRE - 0.02
        t1 = c["t0"] + c["dur"] - CLIP_POST + 0.25
        if i + 1 < len(cues):
            t1 = min(t1, cues[i + 1]["t0"] + CLIP_PRE - 0.06)
        out.append(f"{i + 1}\n{fmt(max(0, t0))} --> {fmt(t1)}\n" + "\n".join(_wrap(TEXT[c['id']])) + "\n")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return path


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    args = sys.argv[2:]
    if cmd == "timeline":
        ep = build_episode()
        print(ep.summary())
        print(f"TOTAL {ep.duration:.2f}s; estimated lines: {sorted(ep.voice.estimated)}")
    elif cmd == "stills":
        for p in stills([float(a) for a in args]):
            print(p)
    elif cmd == "sheet":
        print(sheet(int(args[0]) if args else 24))
    elif cmd == "audio":
        ep = build_episode()
        print(mix_audio(ep))
        print(write_srt(ep))
    elif cmd == "video":
        render_video("--draft" in args)
    elif cmd == "all":
        ep = build_episode()
        mix_audio(ep)
        write_srt(ep)
        render_video("--draft" in args)


if __name__ == "__main__":
    main()
