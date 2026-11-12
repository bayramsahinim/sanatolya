"""Assemble and render the Just Needy Short "I Complained About Mom's Cooking. Big Mistake."

usage:
  python -m episodes.mom_cooking.episode timeline
  python -m episodes.mom_cooking.episode stills t1 t2 ...       # PNG previews at global times
  python -m episodes.mom_cooking.episode audio                  # mix soundtrack + SRT
  python -m episodes.mom_cooking.episode video [--draft]        # render frames -> mp4 (needs audio)
  python -m episodes.mom_cooking.episode all
"""
import os

os.environ["CINECODE_SIZE"] = "1080x1920"   # vertical 9:16 -- must be set before cinecode is imported

import json  # noqa: E402
import multiprocessing as mp  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import cairo  # noqa: E402
import numpy as np  # noqa: E402

from cinecode import audio as A  # noqa: E402
from cinecode import tts  # noqa: E402
from cinecode.align import trim  # noqa: E402
from cinecode.core import FPS, H, W, ease_out, prog, rrect  # noqa: E402
from cinecode.timeline import Episode, VoiceDB  # noqa: E402
from episodes.mom_cooking import sfx as FX  # noqa: E402
from episodes.mom_cooking.script import DIALOGUE, SLUG, TITLE, all_texts  # noqa: E402

assert (W, H) == (1080, 1920), "cinecode was imported before CINECODE_SIZE was set"

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "mom_cooking")
OUT = os.path.join(ROOT, "output")
LINES = os.path.join(ROOT, "assets", "audio", "tts", "mom_cooking", "lines.json")
CLIP_PRE, CLIP_POST = 0.05, 0.12

# ------------------------------------------------------------------ typography
FONT = "Inter ExtraBold"
INK = (0x1F / 255, 0x1F / 255, 0x24 / 255, 1)     # charcoal
ACCENT = (0x34 / 255, 0x78 / 255, 0xF6 / 255, 1)  # #3478F6, the hoodie blue
IN_T, OUT_T = 0.14, 0.18


def _runs(line):
    out = []
    for part in re.split(r"(\[[^\]]*\])", line):
        if part:
            out.append((part[1:-1], True) if part.startswith("[") else (part, False))
    return out


def draw_text_accent(cx, t, c):
    """Short animated text accent: Inter ExtraBold, charcoal + blue, quick fade/scale, no effects."""
    if t < c["t0"] or t > c["t1"] + OUT_T:
        return
    a_in = ease_out(prog(t, c["t0"], c["t0"] + IN_T))
    a = min(a_in, 1 - prog(t, c["t1"], c["t1"] + OUT_T))
    if a <= 0:
        return
    sc = 0.92 + 0.08 * a_in
    size = c["size"]
    lines = c["text"].split("\n")
    # fit inside the 9:16 safe width (>= 90 px side margins)
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    widest = max(sum(cx.text_extents(s).x_advance for s, _ in _runs(ln)) for ln in lines)
    size = size * min(1.0, (W - 180) / widest)
    lh = size * 1.12
    cx.save()
    cx.translate(W / 2, c["y"] + (1 - a_in) * 10)
    cx.scale(sc, sc)
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(size)
    cap = cx.text_extents("H").height
    y0 = -lh * (len(lines) - 1) / 2 + cap / 2
    for i, ln in enumerate(lines):
        runs = _runs(ln)
        wsum = sum(cx.text_extents(s).x_advance for s, _ in runs)
        x = -wsum / 2
        for s, hi in runs:
            cx.move_to(x, y0 + i * lh)
            col = ACCENT if hi else INK
            cx.set_source_rgba(col[0], col[1], col[2], a)
            cx.show_text(s)
            x += cx.text_extents(s).x_advance
    cx.restore()


DLG_SIZE, LABEL_SIZE, DLG_MAX_W, DLG_IN, DLG_OUT = 66, 32, 760, 0.12, 0.12


def _wrap(cx, text, maxw):
    words, rows, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if cur and cx.text_extents(trial.replace("[", "").replace("]", "")).x_advance > maxw:
            rows.append(cur)
            cur = w
        else:
            cur = trial
    rows.append(cur)
    # carry [..] highlight across a line break
    out, open_ = [], False
    for r in rows:
        r2 = ("[" if open_ else "") + r
        open_ = r2.count("[") > r2.count("]")
        out.append(r2 + ("]" if open_ else ""))
    return out


def draw_dialogue(cx, t, c, head, other_faces):
    """Speaker caption: white card + charcoal outline, small blue speaker tag, tail to the speaker,
    placed above the speaker's head and never over a face."""
    if head is None or t < c["t0"] or t > c["t1"] + DLG_OUT:
        return
    a_in = ease_out(prog(t, c["t0"], c["t0"] + DLG_IN))
    a = min(a_in, 1 - prog(t, c["t1"], c["t1"] + DLG_OUT))
    if a <= 0:
        return
    text = c["text"]
    if c.get("reveal_dt") and t < c["t0"] + c["reveal_dt"]:
        shown_upto = text.index("[")          # second word lands on its beat
    else:
        shown_upto = None
    cx.save()
    cx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cx.set_font_size(DLG_SIZE)
    rows = _wrap(cx, text, DLG_MAX_W)
    widths = [sum(cx.text_extents(s).x_advance for s, _ in _runs(r)) for r in rows]
    cap = cx.text_extents("H").height
    lh = DLG_SIZE * 1.18
    padx, pady = 34, 22
    lab_h = LABEL_SIZE * 1.15
    bw = max(widths) + 2 * padx
    bh = pady * 2 + lab_h + lh * len(rows) - (lh - cap)
    hx, hy, hr = head
    gap, tail = 22, 30
    bx = min(max(hx - bw / 2, 50), W - 50 - bw)
    by = hy - hr - gap - tail - bh
    # keep clear of any other face
    for (fx, fy, fr) in other_faces:
        if bx < fx + fr and bx + bw > fx - fr and by < fy + fr and by + bh > fy - fr:
            by = fy - fr - gap - bh
    by = max(by, 120)
    sc = 0.9 + 0.1 * a_in if not c.get("dry") else 0.97 + 0.03 * a_in
    ox, oy = min(max(hx, bx + 40), bx + bw - 40), by + bh
    cx.translate(ox, oy)
    cx.scale(sc, sc)
    cx.translate(-ox, -oy)
    cx.push_group()
    rrect(cx, bx, by, bw, bh, 28)
    tx = min(max(hx, bx + 50), bx + bw - 50)
    cx.move_to(tx - 20, by + bh - 2)
    cx.line_to(hx + (tx - hx) * 0.3, hy - hr - gap * 0.6)
    cx.line_to(tx + 20, by + bh - 2)
    cx.close_path()
    cx.set_source_rgba(1, 1, 1, 0.97)
    cx.fill_preserve()
    cx.set_source_rgba(*INK)
    cx.set_line_width(4)
    cx.set_line_join(cairo.LINE_JOIN_ROUND)
    cx.stroke()
    # speaker tag
    cx.set_font_size(LABEL_SIZE)
    cx.move_to(bx + padx, by + pady + LABEL_SIZE * 0.78)
    cx.set_source_rgba(*ACCENT)
    cx.show_text(c["label"])
    # dialogue text
    cx.set_font_size(DLG_SIZE)
    y = by + pady + lab_h + cap
    count = 0
    for r, wr in zip(rows, widths):
        x = bx + padx
        for s, hi in _runs(r):
            if shown_upto is not None and count >= shown_upto:
                break
            seg = s if shown_upto is None else s[: max(0, shown_upto - count)]
            cx.move_to(x, y)
            cx.set_source_rgba(*(ACCENT if hi else INK))
            cx.show_text(seg)
            x += cx.text_extents(s).x_advance
            count += len(s)
        y += lh
    cx.pop_group_to_source()
    cx.paint_with_alpha(a)
    cx.restore()


class Short(Episode):
    def render(self, cx, gt):
        super().render(cx, gt)
        sh = self.shots[self.shot_at(gt)]
        for c in self.cues:
            if c["type"] == "jn_accent":
                draw_text_accent(cx, gt, c)
            elif c["type"] == "jn_dlg":
                head = sh.heads.get(c["who"])
                others = [h for k, h in sh.heads.items() if k != c["who"]]
                draw_dialogue(cx, gt, c, head, others)


# ------------------------------------------------------------------ build
def load_voice():
    durs = {}
    for lid, v in json.load(open(LINES)).items():
        durs[lid] = v["end"] - v["start"] + CLIP_PRE + CLIP_POST
    return VoiceDB(durs, all_texts(), 1.0)


def build_episode():
    from episodes.mom_cooking.shots import scenes
    return Short(scenes(), load_voice())


def stills(times, prefix="still", scale=0.5):
    ep = build_episode()
    os.makedirs(BUILD, exist_ok=True)
    paths = []
    for gt in times:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(W * scale), int(H * scale))
        cx = cairo.Context(s)
        cx.scale(scale, scale)
        ep.render(cx, gt)
        p = os.path.join(BUILD, f"{prefix}_{gt:06.2f}.png")
        s.write_to_png(p)
        paths.append(p)
    return paths


# ------------------------------------------------------------------ video
_EP = None


def _worker(args):
    a, b, path, scale = args
    global _EP
    if _EP is None:
        _EP = build_episode()
    w, h = int(W * scale), int(H * scale)
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium" if scale == 1 else "veryfast",
           "-crf", "17" if scale == 1 else "26", "-tune", "animation", "-pix_fmt", "yuv420p", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    for i in range(a, b):
        cx = cairo.Context(s)
        cx.set_source_rgb(1, 1, 1)
        cx.paint()
        if scale != 1:
            cx.scale(scale, scale)
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
    mix = os.path.join(BUILD, "mix.wav")
    final = os.path.join(OUT, f"{SLUG}_draft.mp4" if draft else f"{SLUG}.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", mix, "-c:v", "copy", "-c:a", "aac", "-ac", "2",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                    "-metadata", f"title={TITLE}", final], check=True)
    print("wrote", final, f"{time.time() - t:.0f}s")
    return final


# ------------------------------------------------------------------ audio
def voice_clips():
    meta = json.load(open(LINES))
    takes, clips = {}, {}
    for lid, v in meta.items():
        f = os.path.join(ROOT, v["file"])
        if f not in takes:
            takes[f] = tts.read_wav(f)
        raw = trim(takes[f], v["start"], v["end"], CLIP_PRE, CLIP_POST)
        clips[lid] = A.resample(raw, tts.SR, A.SR).astype(np.float32)
    return clips


def level_voice(x, target=0.16):
    v = x[np.abs(x) > 0.02]
    if len(v) == 0:
        return x
    return x * (target / (np.sqrt((v ** 2).mean()) + 1e-9))


def compressor(x, thr=0.3, ratio=2.5):
    env = A.envelope_follow(x, 0.005, 0.12)
    g = np.ones_like(env)
    o = env > thr
    g[o] = (thr + (env[o] - thr) / ratio) / env[o]
    return x * g


def music_bed(ep, n):
    """Music sections from 'music' cues: each runs until the next cue (None = silence)."""
    cues = sorted([c for c in ep.cues if c["type"] == "music"], key=lambda c: c["t0"])
    out = np.zeros(n)
    for i, c in enumerate(cues):
        if not c["name"]:
            continue
        t0 = c["t0"]
        t1 = cues[i + 1]["t0"] if i + 1 < len(cues) else ep.duration
        fo = cues[i + 1]["fade"] if i + 1 < len(cues) else 0.4
        d = t1 - t0 + fo
        loop = FX.music_loop(c["name"])
        x = np.tile(loop, int(d * A.SR) // len(loop) + 1)[: int(d * A.SR)].astype(np.float64) * c["gain"]
        fi = int(c["fade"] * A.SR)
        if fi:
            x[:fi] *= np.linspace(0, 1, fi)
        k = int(fo * A.SR)
        if k:
            x[-k:] *= np.linspace(1, 0, k)
        A.add(out, x, t0)
    return out


def mix_audio(ep):
    n = int(ep.duration * A.SR) + A.SR
    voice = np.zeros(n)
    fx = np.zeros(n)
    clips = voice_clips()
    for c in ep.cues:
        if c["type"] in ("narr", "dlg"):
            x = level_voice(clips[c["id"]])
            A.add(voice, x, c["t0"])
        elif c["type"] == "sfx" and c["vol"] > 0:
            A.add(fx, FX.get(c["name"], c.get("seed", 0)) * c["vol"], c["t0"])
    music = music_bed(ep, n)
    # speech is king: music ducks ~13 dB and effects ~11 dB whenever anyone talks
    env = A.envelope_follow(voice, 0.02, 0.35)
    act = np.clip(env / 0.05, 0, 1)
    music_g = 10 ** (-5 / 20) * (1 - 0.78 * act)
    fx_g = 10 ** (-11 / 20) * (1 - 0.72 * act)
    voice = compressor(voice, 0.3, 2.5)
    total = voice + music * music_g + fx * fx_g
    total = np.tanh(total * 0.95) / 0.95
    os.makedirs(BUILD, exist_ok=True)
    import soundfile as sf
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, total[: int(ep.duration * A.SR)].astype(np.float32), A.SR, subtype="FLOAT")
    # stems for QA
    for nm, x in (("voice", voice), ("music", music * music_g), ("fx", fx * fx_g)):
        sf.write(os.path.join(BUILD, f"stem_{nm}.wav"), x[: int(ep.duration * A.SR)].astype(np.float32), A.SR,
                 subtype="FLOAT")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true")
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    return out


# ------------------------------------------------------------------ SRT
def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(ep, path):
    texts = all_texts()
    speaker = {lid: who for lid, who, _ in DIALOGUE}
    cues = sorted([c for c in ep.cues if c["type"] in ("narr", "dlg")], key=lambda c: c["t0"])
    out = []
    for i, c in enumerate(cues):
        t0 = c["t0"] + CLIP_PRE - 0.02
        t1 = c["t0"] + c["dur"] - 0.04
        if i + 1 < len(cues):
            t1 = min(t1 + 0.3, cues[i + 1]["t0"] + CLIP_PRE - 0.06)
        txt = texts[c["id"]]
        if speaker.get(c["id"]) == "Mom":
            txt = "MOM: " + txt
        elif speaker.get(c["id"]) == "Me":
            txt = "ME: " + txt
        words, rows, cur = txt.split(), [], ""
        for w in words:
            if len(cur) + len(w) + 1 > 32 and cur:
                rows.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        rows.append(cur)
        out.append(f"{i + 1}\n{fmt(t0)} --> {fmt(t1)}\n" + "\n".join(rows[:2]) + "\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    return path


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    args = sys.argv[2:]
    if cmd == "timeline":
        ep = build_episode()
        print(ep.summary())
        for c in sorted([c for c in ep.cues if c["type"] in ("narr", "dlg", "jn_accent", "music")],
                        key=lambda c: c["t0"]):
            print(f"  {c['t0']:6.2f}  {c['type']:9s} {c.get('id') or c.get('text') or c.get('name')}")
        print(f"TOTAL {ep.duration:.2f}s  ({ep.nframes} frames); estimated lines: {ep.voice.estimated}")
    elif cmd == "stills":
        for p in stills([float(a) for a in args]):
            print(p)
    elif cmd == "audio":
        ep = build_episode()
        print(mix_audio(ep))
        os.makedirs(OUT, exist_ok=True)
        print(write_srt(ep, os.path.join(OUT, f"{SLUG}.en.srt")))
    elif cmd == "video":
        render_video("--draft" in args)
    elif cmd == "all":
        ep = build_episode()
        mix_audio(ep)
        os.makedirs(OUT, exist_ok=True)
        write_srt(ep, os.path.join(OUT, f"{SLUG}.en.srt"))
        render_video("--draft" in args)


if __name__ == "__main__":
    main()
