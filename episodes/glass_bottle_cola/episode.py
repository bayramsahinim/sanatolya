"""Build "Why Does Coke Taste Better From a Glass Bottle?" (Just Needy Short, 1080x1920, 30 fps).

usage:
  python -m episodes.glass_bottle_cola.episode audio     # narration placement + music + SFX mix, SRT
  python -m episodes.glass_bottle_cola.episode video     # native 1080x1920 render, muxed with the mix
  python -m episodes.glass_bottle_cola.episode stills t1 t2 ...
  python -m episodes.glass_bottle_cola.episode all
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
from episodes.glass_bottle_cola import scenes as SC
from episodes.glass_bottle_cola.art import H, W
from episodes.glass_bottle_cola.script import END, TITLE
from episodes.glass_bottle_cola.timing import POST, PRE, TAKE, TL

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "cola")
OUT = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_GLASS_BOTTLE_COLA_FINAL.mp4"
SRT = "JUST_NEEDY_GLASS_BOTTLE_COLA_ENGLISH.srt"
FPS = 30
NFRAMES = int(round(END * FPS))


# ------------------------------------------------------------------ audio
def _db(take, t, win=0.02):
    s = take[max(0, int(t * tts.SR)):max(1, int((t + win) * tts.SR))]
    return 20 * np.log10(np.sqrt((s ** 2).mean()) + 1e-9) if len(s) else -120


def _silence_before(take, t, lo, thr=-58, need=0.06):
    """walk back from t until `need` s of silence (word timestamps can sit after the consonant burst)."""
    quiet = 0.0
    x = t
    while x > lo:
        x -= 0.01
        quiet = quiet + 0.01 if _db(take, x, 0.01) < thr else 0.0
        if quiet >= need:
            return x + need - 0.02
    return lo


def _silence_after(take, t, hi, thr=-58, need=0.06):
    quiet = 0.0
    x = t
    while x < hi:
        quiet = quiet + 0.01 if _db(take, x, 0.01) < thr else 0.0
        x += 0.01
        if quiet >= need:
            return x - need + 0.03
    return hi


def voice_track(n):
    take = tts.read_wav(TAKE)
    out = np.zeros(n)
    for i, l in enumerate(TL):
        lo = (TL[i - 1]["take_e"] + l["take_s"]) / 2 if i > 0 else 0.0
        hi = (l["take_e"] + TL[i + 1]["take_s"]) / 2 if i + 1 < len(TL) else len(take) / tts.SR
        lo, hi = max(lo, l["take_s"] - 0.3), min(hi, l["take_e"] + 0.35)
        a = max(lo, min(l["take_s"] - PRE, _silence_before(take, l["take_s"], lo)))
        b = min(hi, max(l["take_e"] + POST, _silence_after(take, l["take_e"], hi)))
        clip = take[int(a * tts.SR):int(b * tts.SR)].astype(np.float64)
        f = int(0.012 * tts.SR)
        clip[:f] *= np.linspace(0, 1, f)
        clip[-f:] *= np.linspace(1, 0, f)
        clip = A.resample(clip, tts.SR, A.SR)
        A.add(out, clip, a + l["off"])
    return out


def sfx_fizz(d=1.6, density=900, seed=0, decay=0.8):
    rng = np.random.default_rng(seed)
    n = int(d * A.SR)
    x = np.zeros(n)
    k = int(density * d)
    pos = rng.integers(0, n - 200, k)
    amp = rng.uniform(0.2, 1.0, k)
    for p, a in zip(pos, amp):
        L = rng.integers(20, 90)
        x[p:p + L] += a * rng.standard_normal(L) * np.exp(-np.arange(L) / (L / 4))
    x = A.hp(x, 2500)
    hiss = A.bp(rng.standard_normal(n), 4000, 11000) * 0.25
    env = np.exp(-np.arange(n) / (decay * A.SR))
    env[: int(0.02 * A.SR)] *= np.linspace(0, 1, int(0.02 * A.SR))
    return A.norm((x + hiss) * env, 0.6)


def sfx_events():
    from episodes.glass_bottle_cola import scenes as S
    ev = [("pop", 0.32, 0.9), (sfx_fizz(2.2, 1200, 1, 1.0), 0.33, 0.55),
          ("swish", S.T2 - 0.15, 0.45), ("swish", S.T2E - 0.05, 0.4)]
    ev += [("pop", S.T3 + 0.05 + i * 0.12, 0.28) for i in range(4)]
    ev += [("suck", S.SQUEEZE - 0.1, 0.35), ("swish", S.A_END, 0.45), ("click", S.SOLID, 0.5),
           (sfx_fizz(1.4, 500, 2, 0.9), S.T5 + 0.05, 0.4), ("whoosh", S.B_ZOOM0, 0.35),
           (sfx_fizz(3.0, 260, 3, 2.5), S.B_ZOOM1, 0.22), ("pop", S.TWO_PCT - 0.05, 0.4)]
    # week counter flips
    n = len(S.WEEKS)
    step = ((S.FLAT - 0.2) - (S.T8 + 0.1)) / (n - 1)
    ev += [("click", S.T8 + 0.1 + i * step, 0.45) for i in range(1, n)]
    ev += [("thud", S.FLAT, 0.7)]
    # tongue: gas lands -> acid tingle
    ev += [("sparkle", t0 + 0.55, 0.16) for _, t0, _ in S.DROPS[::3]]
    ev += [(sfx_fizz(2.0, 700, 4, 1.4), S.T10, 0.35), ("swish", S.E_END, 0.35)]
    ev += [("sparkle", S.LINED, 0.25), ("whoosh", S.F_ZOOM0, 0.35), ("pop", S.TWO_WK - 0.05, 0.4),
           ("swish", S.G_END, 0.3), ("whoosh", S.H_END, 0.3)]
    ev += [("clank", S.FACTORY + 0.05, 0.45), ("click", S.FACTORY + 0.06, 0.6), ("sparkle", S.FACTORY + 0.35, 0.3)]
    return ev


def mix_audio():
    import soundfile as sf
    n = int(END * A.SR)
    voice = voice_track(n)
    fx = np.zeros(n)
    for name, t, vol in sfx_events():
        x = A.get_sfx(name) if isinstance(name, str) else name
        A.add(fx, x * vol, t)
    rng = np.random.default_rng(77)
    loop = A._quirky(rng, root=55, bpm=112, scale="major", bars=8, soft=True, bright=0.55)
    music = np.tile(loop, n // len(loop) + 2)[:n]
    fo = int(1.2 * A.SR)
    music[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    music[: int(0.3 * A.SR)] *= np.linspace(0, 1, int(0.3 * A.SR))
    env = A.envelope_follow(voice, 0.03, 0.4)
    duck = 1.0 - 0.55 * np.clip(env / 0.08, 0, 1)
    # gentle voice levelling
    v = voice[np.abs(voice) > 0.02]
    voice *= 0.2 / (np.sqrt((v ** 2).mean()) + 1e-9)
    total = voice + music * 10 ** (-19 / 20) * duck + fx * 10 ** (-10 / 20) * (1 - 0.3 * np.clip(env / 0.08, 0, 1))
    total = np.tanh(total * 0.95) / 0.95
    os.makedirs(BUILD, exist_ok=True)
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, total.astype(np.float32), A.SR, subtype="FLOAT")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    out = os.path.join(BUILD, "mix.wav")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", raw, "-af", af, "-ar", "48000", out], check=True)
    sf.write(os.path.join(BUILD, "voice_only.wav"), (voice / max(1e-9, np.abs(voice).max()) * 0.9).astype(np.float32), A.SR)
    return out


# ------------------------------------------------------------------ SRT (same cues as burned-in captions)
def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(path):
    rows = []
    for i, c in enumerate(SC.CUES):
        t1 = c["t1"] if c["cut_out"] else c["t1"] + 0.1
        rows.append(f"{i + 1}\n{fmt(max(0, c['t0']))} --> {fmt(t1)}\n{c['text']}\n")
    with open(path, "w") as f:
        f.write("\n".join(rows))
    return path


# ------------------------------------------------------------------ video
def _worker(args):
    a, b, path = args
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-tune", "animation",
           "-pix_fmt", "yuv420p", "-profile:v", "high", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for i in range(a, b):
        cx = cairo.Context(s)
        cx.set_source_rgb(0, 0, 0)
        cx.paint()
        SC.render(cx, i / FPS)
        s.flush()
        pr.stdin.write(bytes(s.get_data()))
    pr.stdin.close()
    pr.wait()
    return path


def render_video(workers=4):
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    chunks = 16
    step = (NFRAMES + chunks - 1) // chunks
    jobs = [(k * step, min(NFRAMES, (k + 1) * step), os.path.join(BUILD, f"part_{k:02d}.mp4"))
            for k in range(chunks) if k * step < NFRAMES]
    t = time.time()
    with mp.Pool(workers) as pool:
        for i, _ in enumerate(pool.imap(_worker, jobs)):
            print(f"  chunk {i + 1}/{len(jobs)}  {time.time() - t:.0f}s", flush=True)
    lst = os.path.join(BUILD, "parts.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for _, _, p in jobs)
    silent = os.path.join(BUILD, "video_silent.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent],
                   check=True)
    final = os.path.join(OUT, NAME)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", os.path.join(BUILD, "mix.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{NFRAMES / FPS:.3f}",
                    "-movflags", "+faststart", "-metadata", f"title={TITLE}", final], check=True)
    print("wrote", final, f"{time.time() - t:.0f}s")
    return final


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("audio", "all"):
        print(mix_audio())
        os.makedirs(OUT, exist_ok=True)
        print(write_srt(os.path.join(OUT, SRT)))
    if cmd in ("video", "all"):
        render_video()
    if cmd == "stills":
        os.makedirs(BUILD, exist_ok=True)
        for a in sys.argv[2:]:
            s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
            SC.render(cairo.Context(s), float(a))
            p = os.path.join(BUILD, f"still_{float(a):05.2f}.png")
            s.write_to_png(p)
            print(p)


if __name__ == "__main__":
    main()
