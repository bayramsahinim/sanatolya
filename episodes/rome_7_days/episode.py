"""Assemble and render "I Got Stuck in Ancient Rome for 7 Days".

usage:
  python -m episodes.rome_7_days.episode stills [t1 t2 ...]     # PNG previews at global times
  python -m episodes.rome_7_days.episode timeline               # print shot list
  python -m episodes.rome_7_days.episode audio                  # mix soundtrack + SRT
  python -m episodes.rome_7_days.episode video [--draft]        # render frames -> mp4 (needs audio)
  python -m episodes.rome_7_days.episode all
"""
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
from episodes.rome_7_days.script import DIALOGUE, NARRATION

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "rome_7_days")
OUT = os.path.join(ROOT, "output")
LINES = os.path.join(ROOT, "assets", "audio", "tts", "lines.json")
TEMPO = json.load(open(os.path.join(ROOT, "config", "narrator_voice.json"))).get("playback_tempo", 1.0)
CLIP_PRE, CLIP_POST = 0.05, 0.12
GAP_SCALE = 1.0         # tune pauses between lines so the cut lands at 8-9 minutes
TITLE = "I Got Stuck in Ancient Rome for 7 Days"


def all_texts():
    d = {lid: t for s in NARRATION.values() for lid, t in s}
    d.update({lid: t for lid, _, t in DIALOGUE})
    return d


def load_voice():
    durs = {}
    if os.path.exists(LINES):
        for lid, v in json.load(open(LINES)).items():
            durs[lid] = (v["end"] - v["start"] + CLIP_PRE + CLIP_POST) / TEMPO
    v = VoiceDB(durs, all_texts(), TEMPO)
    v.gap_scale = GAP_SCALE
    return v


def build_episode():
    from episodes.rome_7_days import scenes_1_2
    shots = scenes_1_2.scenes()
    for mod in ("scenes_3_4", "scenes_5_7", "scenes_8_10"):
        try:
            m = __import__(f"episodes.rome_7_days.{mod}", fromlist=["scenes"])
            shots += m.scenes()
        except ModuleNotFoundError as e:
            if mod not in str(e):
                raise
    return Episode(shots, load_voice())


# ------------------------------------------------------------------ stills
def stills(times, prefix="still"):
    ep = build_episode()
    os.makedirs(BUILD, exist_ok=True)
    paths = []
    for gt in times:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        cx = cairo.Context(s)
        ep.render(cx, gt)
        p = os.path.join(BUILD, f"{prefix}_{gt:07.2f}.png")
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
    chunks = workers * 6
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
    name = "rome_7_days_draft.mp4" if draft else "I_Got_Stuck_in_Ancient_Rome_for_7_Days.mp4"
    final = os.path.join(OUT, name)
    aud = ["-ss", str(t0), "-t", str(n / FPS), "-i", mix] if (t0 or t1) else ["-i", mix]
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, *aud, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                    "-metadata", f"title={TITLE}", final], check=True)
    print("wrote", final, f"{time.time() - t:.0f}s")
    return final


# ------------------------------------------------------------------ audio
def narration_clips(ep):
    """lid -> float32 @48k, slowed by TEMPO, cached."""
    cache = os.path.join(BUILD, "clips")
    os.makedirs(cache, exist_ok=True)
    meta = json.load(open(LINES)) if os.path.exists(LINES) else {}
    takes = {}
    clips = {}
    for lid, v in meta.items():
        p = os.path.join(cache, f"{lid}_{TEMPO}_{v['start']}_{v['end']}.npy")
        if os.path.exists(p):
            clips[lid] = np.load(p)
            continue
        f = os.path.join(ROOT, v["file"])
        if f not in takes:
            takes[f] = tts.read_wav(f)
        raw = trim(takes[f], v["start"], v["end"], CLIP_PRE, CLIP_POST)
        y, sr = A.stretch(raw, tts.SR, TEMPO, cache)
        y = A.resample(y, sr, A.SR).astype(np.float32)
        np.save(p, y)
        clips[lid] = y
    return clips


def loudness_norm_voice(x):
    """Gentle per-clip levelling (RMS of voiced part -> target)."""
    v = x[np.abs(x) > 0.02]
    if len(v) == 0:
        return x
    rms = np.sqrt((v ** 2).mean())
    return x * (0.16 / (rms + 1e-9))


def compressor(x, thr=0.35, ratio=3.0):
    env = A.envelope_follow(x, 0.005, 0.12)
    gain = np.ones_like(env)
    over = env > thr
    gain[over] = (thr + (env[over] - thr) / ratio) / env[over]
    return x * gain


def mix_audio(ep):
    n = int(ep.duration * A.SR) + A.SR
    voice = np.zeros(n)
    music = np.zeros(n)
    amb = np.zeros(n)
    fx = np.zeros(n)
    clips = narration_clips(ep)
    missing = []
    for c in ep.cues:
        if c["type"] in ("narr", "dlg"):
            if c["id"] in clips:
                x = loudness_norm_voice(clips[c["id"]])
                if c["type"] == "dlg":
                    x = x * 1.05
                A.add(voice, x, c["t0"])
            else:
                missing.append(c["id"])
        elif c["type"] == "sfx" and c["vol"] > 0:
            A.add(fx, A.get_sfx(c["name"]) * c["vol"], c["t0"])
    # music + ambience beds, per contiguous run of shots
    def beds(attr, gain_attr, render, xf):
        runs = []
        for sh, st in zip(ep.shots, ep.starts):
            name = getattr(sh, attr)
            g = getattr(sh, gain_attr)
            if runs and runs[-1][0] == name:
                runs[-1][2] = st + sh.dur
            else:
                runs.append([name, st, st + sh.dur, g])
        out = np.zeros(n)
        for name, a, b, g in runs:
            if not name:
                continue
            a2, b2 = max(0, a - xf / 2), b + xf / 2
            x = render(name, b2 - a2) * g
            k = int(xf * A.SR)
            k = min(k, len(x) // 2)
            x[:k] *= np.linspace(0, 1, k)
            x[-k:] *= np.linspace(1, 0, k)
            A.add(out, x, a2)
        return out

    music = beds("music", "music_gain", A.track, 1.2)
    amb = beds("amb", "amb_gain", lambda nm, d: np.tile(A.amb_loop(nm), int(d / 12) + 2)[: int(d * A.SR)], 1.0)
    # ducking: music + ambience drop under the voice
    env = A.envelope_follow(voice, 0.03, 0.45)
    duck = 1.0 - 0.62 * np.clip(env / 0.08, 0, 1)
    music_gain = 10 ** (-17 / 20)
    amb_gain = 10 ** (-27 / 20)
    fx_gain = 10 ** (-9 / 20)
    voice = compressor(voice, 0.3, 2.5)
    fx_duck = 1.0 - 0.3 * np.clip(env / 0.08, 0, 1)
    total = voice + music * music_gain * duck + amb * amb_gain * duck + fx * fx_gain * fx_duck
    total = np.tanh(total * 0.95) / 0.95
    os.makedirs(BUILD, exist_ok=True)
    raw = os.path.join(BUILD, "mix_raw.wav")
    import soundfile as sf
    sf.write(raw, total[: int(ep.duration * A.SR)].astype(np.float32), A.SR, subtype="FLOAT")
    # two-pass loudness normalisation to -14 LUFS / -1.5 dBTP (YouTube)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af",
                        "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    m = json.loads(js)
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true")
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    if missing:
        print("WARNING: no audio yet for", len(missing), "lines:", missing[:6], "...")
    return out


# ------------------------------------------------------------------ SRT
def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(ep, path):
    texts = all_texts()
    speaker = {lid: who for lid, who, _ in DIALOGUE}
    cues = sorted([c for c in ep.cues if c["type"] in ("narr", "dlg")], key=lambda c: c["t0"])
    lines = []
    for i, c in enumerate(cues):
        t0 = c["t0"] + 0.03
        t1 = c["t0"] + c["dur"] - 0.05
        if i + 1 < len(cues):
            t1 = min(t1 + 0.25, cues[i + 1]["t0"] - 0.02)
        txt = texts[c["id"]]
        if c["type"] == "dlg":
            txt = f"{speaker[c['id']].upper()}: {txt}"
        # wrap at ~42 chars, max 2 lines
        words, rows, cur = txt.split(), [], ""
        for w in words:
            if len(cur) + len(w) + 1 > 42 and cur:
                rows.append(cur)
                cur = w
            else:
                cur = (cur + " " + w).strip()
        rows.append(cur)
        if len(rows) > 2:
            half = len(words) // 2
            rows = [" ".join(words[:half]), " ".join(words[half:])]
        lines.append(f"{i + 1}\n{fmt(t0)} --> {fmt(t1)}\n" + "\n".join(rows) + "\n")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    args = sys.argv[2:]
    if cmd == "timeline":
        ep = build_episode()
        print(ep.summary())
        print(f"TOTAL {ep.duration:.1f}s = {ep.duration / 60:.2f} min; estimated lines: {len(ep.voice.estimated)}")
    elif cmd == "stills":
        for p in stills([float(a) for a in args]):
            print(p)
    elif cmd == "audio":
        ep = build_episode()
        print(mix_audio(ep))
        os.makedirs(OUT, exist_ok=True)
        print(write_srt(ep, os.path.join(OUT, "I_Got_Stuck_in_Ancient_Rome_for_7_Days.en.srt")))
    elif cmd == "video":
        draft = "--draft" in args
        rng = [float(a) for a in args if not a.startswith("--")]
        render_video(draft, t0=rng[0] if rng else 0.0, t1=rng[1] if len(rng) > 1 else None)
    elif cmd == "all":
        ep = build_episode()
        mix_audio(ep)
        os.makedirs(OUT, exist_ok=True)
        write_srt(ep, os.path.join(OUT, "I_Got_Stuck_in_Ancient_Rome_for_7_Days.en.srt"))
        render_video("--draft" in args)


if __name__ == "__main__":
    main()
