"""Assemble and render "Just Needy - The Prisoner Who Escaped With Dry Peas" (YouTube Short, 1080x1920).

usage:
  python -m episodes.dry_peas_escape.episode timeline
  python -m episodes.dry_peas_escape.episode stills T1 T2 ...      # PNG previews at global times
  python -m episodes.dry_peas_escape.episode audio                 # soundtrack + SRT
  python -m episodes.dry_peas_escape.episode video [--draft]       # frames -> mp4 (needs audio)
  python -m episodes.dry_peas_escape.episode all
"""
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time

import episodes.dry_peas_escape  # noqa: F401  (vertical canvas)

import cairo
import numpy as np

from cinecode import audio as A
from cinecode import captions, tts
from cinecode.align import trim
from cinecode.core import FPS, H, W, ease_out, prog
from cinecode.timeline import Episode, VoiceDB
from episodes.dry_peas_escape import sound
from episodes.dry_peas_escape.script import LABELS, LINES, TEXT
from episodes.dry_peas_escape.timing import CLIP_POST, CLIP_PRE, LINES_JSON, SCHED, TEMPO, TOTAL, WORDS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "dry_peas_escape")
OUT = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_DRY_PEAS_PRISON_ESCAPE_FINAL"
SRT_NAME = "JUST_NEEDY_DRY_PEAS_PRISON_ESCAPE_ENGLISH.srt"
TITLE = "The Prisoner Who Escaped With Dry Peas"

SUB_SIZE = 70
SUB_Y = 1480
SUB_MAXW = W - 140


# ------------------------------------------------------------------ subtitles
def subtitle_chunks():
    """Short caption segments (1-4 words, <= 22 chars, break after punctuation), timed to words."""
    chunks = []
    for lid, _, _, _ in LINES:
        ws = WORDS[lid]
        cur = []
        for k, (w, a, b) in enumerate(ws):
            cur.append((w, a, b))
            txt = " ".join(x[0] for x in cur)
            nxt = ws[k + 1][0] if k + 1 < len(ws) else ""
            brk = (w[-1] in ",.?!:" or w.endswith('"') or len(cur) >= 4 or
                   len(txt) + 1 + len(nxt) > 22 or not nxt)
            # don't leave a lone short word dangling at a line end
            if brk and nxt and k + 2 == len(ws) and len(nxt) <= 5 and w[-1] not in ",.?!:" and len(cur) < 4:
                brk = False
            if brk:
                chunks.append({"text": txt, "t0": cur[0][1], "t1": cur[-1][2], "lid": lid})
                cur = []
    # hold each chunk until the next one (or a short tail), never overlapping
    for c in chunks:
        c["t0"] = max(0.0, c["t0"] - 0.04)
    for i, c in enumerate(chunks):
        nxt = chunks[i + 1]["t0"] if i + 1 < len(chunks) else TOTAL
        c["t1"] = min(max(c["t1"] + 0.25, c["t0"] + 0.45), nxt - 0.02)
    return chunks


def _wrap(txt, size):
    surf, w, h, pad = captions.render_text(txt, size)
    if w - 2 * pad <= SUB_MAXW:
        return txt
    ws = txt.split()
    best = None
    for k in range(1, len(ws)):
        a, b = " ".join(ws[:k]), " ".join(ws[k:])
        m = max(len(a), len(b))
        if best is None or m < best[0]:
            best = (m, a + "\n" + b)
    return best[1]


def draw_subtitle(cx, gt, chunks):
    for c in chunks:
        if c["t0"] <= gt < c["t1"]:
            txt = _wrap(c["text"], SUB_SIZE)
            surf, w, h, pad = captions.render_text(txt, SUB_SIZE)
            a = ease_out(prog(gt, c["t0"], c["t0"] + 0.06))
            cx.save()
            cx.set_source_surface(surf, W / 2 - w / 2, SUB_Y - h / 2)
            cx.paint_with_alpha(a)
            cx.restore()
            return


def draw_label(cx, gt):
    for t0, t1, head, body in LABELS:
        if t0 <= gt <= t1 + 0.2:
            a = min(ease_out(prog(gt, t0, t0 + 0.15)), 1 - prog(gt, t1, t1 + 0.2))
            y = 300
            if head:
                s, w, h, pad = captions.render_text(head, 44)
                cx.set_source_surface(s, W / 2 - w / 2, y - 60 - h / 2)
                cx.paint_with_alpha(a)
            s, w, h, pad = captions.render_text(body, 64)
            cx.set_source_surface(s, W / 2 - w / 2, y - h / 2)
            cx.paint_with_alpha(a)


class ShortEpisode(Episode):
    def __init__(self, shots, voice):
        super().__init__(shots, voice)
        self.chunks = subtitle_chunks()

    def render(self, cx, gt):
        from episodes.dry_peas_escape import shots
        shots.BASE[0] = cx.get_matrix()
        super().render(cx, gt)
        cx.set_matrix(shots.BASE[0])
        draw_label(cx, gt)
        draw_subtitle(cx, gt, self.chunks)


def load_voice():
    meta = json.load(open(LINES_JSON))
    durs = {lid: (v["end"] - v["start"] + CLIP_PRE + CLIP_POST) / TEMPO for lid, v in meta.items()}
    return VoiceDB(durs, TEXT, TEMPO)


def build_episode():
    from episodes.dry_peas_escape import shots
    return ShortEpisode(shots.scenes(), load_voice())


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
           "-crf", "18" if scale == 1 else "26", "-tune", "animation", "-pix_fmt", "yuv420p", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    for i in range(a, b):
        cx = cairo.Context(s)
        cx.set_source_rgb(0, 0, 0)
        cx.paint()
        if scale != 1:
            cx.scale(scale, scale)
        _EP.render(cx, i / FPS)
        s.flush()
        pr.stdin.write(bytes(s.get_data()))
    pr.stdin.close()
    pr.wait()
    return path


def render_video(draft=False, workers=4, t0=0.0, t1=None):
    ep = build_episode()
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    f0 = int(t0 * FPS)
    f1 = ep.nframes if t1 is None else min(ep.nframes, int(t1 * FPS))
    n = f1 - f0
    chunks = workers * 4
    step = (n + chunks - 1) // chunks
    jobs = []
    for k in range(chunks):
        a, b = f0 + k * step, min(f1, f0 + (k + 1) * step)
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
    final = os.path.join(OUT if not draft else BUILD, (NAME if not draft else "draft") + ".mp4")
    aud = ["-ss", str(t0), "-t", str(n / FPS), "-i", mix] if (t0 or t1) else ["-i", mix]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, *aud, "-c:v", "copy", "-c:a", "aac", "-ac", "2",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                    "-metadata", f"title={TITLE}", final], check=True)
    print("wrote", final, f"{time.time() - t:.0f}s")
    return final


# ------------------------------------------------------------------ audio
def narration_clips():
    cache = os.path.join(BUILD, "clips")
    os.makedirs(cache, exist_ok=True)
    meta = json.load(open(LINES_JSON))
    takes, clips = {}, {}
    for lid, v in meta.items():
        p = os.path.join(cache, f"{lid}_{TEMPO}_{v['start']}_{v['end']}.npy")
        if os.path.exists(p):
            clips[lid] = np.load(p)
            continue
        f = os.path.join(ROOT, v["file"])
        if f not in takes:
            takes[f] = tts.read_wav(f)
        raw = trim(takes[f], v["start"], v["end"], CLIP_PRE, CLIP_POST)
        a, b = os.path.join(cache, "in.wav"), os.path.join(cache, "out.wav")
        tts.write_wav(a, raw)
        # formant-preserving time stretch (ffmpeg's librubberband), then 48 kHz
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a, "-af",
                        f"rubberband=tempo={TEMPO}:formant=preserved:pitchq=quality,aresample=48000", "-ac", "1",
                        b], check=True)
        import soundfile as sf
        y, sr = sf.read(b)
        assert sr == A.SR
        y = y.astype(np.float32)
        np.save(p, y)
        clips[lid] = y
    return clips


def voice_level(x):
    v = x[np.abs(x) > 0.02]
    if len(v) == 0:
        return x
    return x * (0.16 / (np.sqrt((v ** 2).mean()) + 1e-9))


def compressor(x, thr=0.3, ratio=2.5):
    env = A.envelope_follow(x, 0.005, 0.12)
    gain = np.ones_like(env)
    over = env > thr
    gain[over] = (thr + (env[over] - thr) / ratio) / env[over]
    return x * gain


def deess_brighten(x):
    """gentle clarity: trim mud below 90 Hz, tiny presence lift."""
    return A.hp(x, 90) + A.bp(x, 2500, 5000) * 0.12


def mix_audio(ep):
    n = int(ep.duration * A.SR) + A.SR
    voice, fx = np.zeros(n), np.zeros(n)
    clips = narration_clips()
    for c in ep.cues:
        if c["type"] == "narr":
            A.add(voice, voice_level(clips[c["id"]]), c["t0"])
        elif c["type"] == "sfx" and c["vol"] > 0:
            A.add(fx, A.get_sfx(c["name"]) * c["vol"], c["t0"])

    def beds(attr, render, xf):
        runs = []
        for sh, st in zip(ep.shots, ep.starts):
            name = getattr(sh, attr)
            if runs and runs[-1][0] == name:
                runs[-1][2] = st + sh.dur
            else:
                runs.append([name, st, st + sh.dur])
        out = np.zeros(n)
        for name, a, b in runs:
            if not name:
                continue
            a2, b2 = max(0, a - xf / 2), b + xf / 2
            x = render(name, b2 - a2).astype(np.float64)
            k = min(int(xf * A.SR), len(x) // 2)
            x[:k] *= np.linspace(0, 1, k)
            x[-k:] *= np.linspace(1, 0, k)
            A.add(out, x, a2)
        return out

    music = beds("music", sound.music_bed, 1.0)
    amb = beds("amb", sound.amb_bed, 1.0)
    # music fades out with the final hold
    e = np.ones(n)
    k0, k1 = int((ep.duration - 1.2) * A.SR), int(ep.duration * A.SR)
    e[k0:k1] = np.linspace(1, 0, k1 - k0)
    e[k1:] = 0
    music *= e
    env = A.envelope_follow(voice, 0.03, 0.45)
    duck = 1.0 - 0.55 * np.clip(env / 0.08, 0, 1)
    voice = compressor(deess_brighten(voice))
    total = (voice + music * 10 ** (-14 / 20) * duck + amb * 10 ** (-27 / 20) * duck
             + fx * 10 ** (-11 / 20) * (1.0 - 0.35 * np.clip(env / 0.08, 0, 1)))
    total = np.tanh(total * 0.95) / 0.95
    os.makedirs(BUILD, exist_ok=True)
    import soundfile as sf
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, total[: int(ep.duration * A.SR)].astype(np.float32), A.SR, subtype="FLOAT")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    # stems for QA (voice vs. bed levels)
    sf.write(os.path.join(BUILD, "stem_voice.wav"), voice[: int(ep.duration * A.SR)].astype(np.float32), A.SR)
    bed = music * 10 ** (-14 / 20) * duck + amb * 10 ** (-27 / 20) * duck
    sf.write(os.path.join(BUILD, "stem_bed.wav"), bed[: int(ep.duration * A.SR)].astype(np.float32), A.SR)
    return out


# ------------------------------------------------------------------ SRT
def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(ep, path):
    out = []
    for i, c in enumerate(ep.chunks):
        txt = _wrap(c["text"], SUB_SIZE)
        out.append(f"{i + 1}\n{fmt(c['t0'])} --> {fmt(c['t1'])}\n{txt}\n")
    with open(path, "w") as f:
        f.write("\n".join(out))
    return path


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    args = sys.argv[2:]
    if cmd == "timeline":
        ep = build_episode()
        print(ep.summary())
        print(f"TOTAL {ep.duration:.2f}s")
    elif cmd == "stills":
        for p in stills([float(a) for a in args]):
            print(p)
    elif cmd == "audio":
        ep = build_episode()
        print(mix_audio(ep))
        os.makedirs(OUT, exist_ok=True)
        print(write_srt(ep, os.path.join(OUT, SRT_NAME)))
    elif cmd == "video":
        draft = "--draft" in args
        rng = [float(a) for a in args if not a.startswith("--")]
        render_video(draft, t0=rng[0] if rng else 0.0, t1=rng[1] if len(rng) > 1 else None)
    elif cmd == "all":
        ep = build_episode()
        mix_audio(ep)
        os.makedirs(OUT, exist_ok=True)
        write_srt(ep, os.path.join(OUT, SRT_NAME))
        render_video("--draft" in args)


if __name__ == "__main__":
    main()
