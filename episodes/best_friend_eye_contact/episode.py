"""Render, mix and export the Short.

usage:
  python -m episodes.best_friend_eye_contact.episode stills 1.0 8.6 ...
  python -m episodes.best_friend_eye_contact.episode audio
  python -m episodes.best_friend_eye_contact.episode video [--draft]
  python -m episodes.best_friend_eye_contact.episode all
"""
import json
import multiprocessing as mp
import os
import subprocess
import sys

import numpy as np

from cinecode import audio as A
from cinecode import tts
from episodes.best_friend_eye_contact import voice as V

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "best_friend_eye_contact")
OUT = os.path.join(ROOT, "output")
NAME = "JUST_NEEDY_BEST_FRIEND_EYE_CONTACT"
FINAL = os.path.join(OUT, f"{NAME}_FINAL.mp4")
SRT = os.path.join(OUT, f"{NAME}_ENGLISH.srt")
W, H, FPS, DUR = 1080, 1920, 30, 36.0


# ------------------------------------------------------------------ SFX
def sfx_zipper(d=0.6):
    n = int(d * A.SR)
    x = np.zeros(n)
    rng = np.random.default_rng(7)
    t = 0.0
    while t < d - 0.01:
        k = int(t * A.SR)
        click = A.hp(A.noise(0.006, int(t * 1000)), 2500) * np.exp(-np.arange(int(0.006 * A.SR)) / 60)
        x[k:k + len(click)] += click[: n - k] * (0.6 + 0.4 * rng.random())
        t += 0.012 + 0.006 * (t / d)
    return A.norm(A.fade(x, 0.01, 0.05), 0.7)


def sfx_list():
    from episodes.best_friend_eye_contact.scenes import word_t, line_t
    return [
        ("pop", word_t("L03", "Someone"), 0.22),
        ("pop", word_t("L06", "one") - 0.15, 0.18),
        ("pop", word_t("L06", "everything") - 0.12, 0.2),
        ("zap", line_t("L07") - 0.1, 0.07),
        ("pop", line_t("L08") + 0.02, 0.18),
        ("pop", line_t("L08") + 0.14, 0.15),
        ("pop", word_t("L09", "laughed") + 0.05, 0.22),
        ("pop", word_t("L10", "annoyed"), 0.22),
        ("thud", word_t("L11", "built"), 0.25),
        ("swish", word_t("L11", "archive") - 0.1, 0.18),
        ("zipper", word_t("L13", "ZIP") - 0.05, 0.3),
        ("sparkle", word_t("L13", "ZIP") + 0.5, 0.22),
    ]


def mix_audio():
    os.makedirs(BUILD, exist_ok=True)
    n = int(DUR * A.SR)
    voice = A.resample(V.narration_track(DUR), tts.SR, A.SR)[:n]
    voice = np.pad(voice, (0, max(0, n - len(voice))))
    v = voice[np.abs(voice) > 0.02]
    voice = voice * (0.17 / (np.sqrt((v ** 2).mean()) + 1e-9))
    fx = np.zeros(n)
    for name, t, vol in sfx_list():
        x = sfx_zipper() if name == "zipper" else A.get_sfx(name)
        A.add(fx, x * vol, t)
    music = A.track("room", DUR)[:n]
    k = int(0.6 * A.SR)
    music[:k] *= np.linspace(0, 1, k)
    k = int(1.5 * A.SR)
    music[-k:] *= np.linspace(1, 0, k)
    env = A.envelope_follow(voice, 0.03, 0.45)
    duck = 1.0 - 0.55 * np.clip(env / 0.08, 0, 1)
    total = voice + music * 10 ** (-19 / 20) * duck + fx * 10 ** (-8 / 20)
    total = np.tanh(total * 0.95) / 0.95
    import soundfile as sf
    raw = os.path.join(BUILD, "mix_raw.wav")
    sf.write(raw, total.astype(np.float32), A.SR, subtype="FLOAT")
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


def write_srt():
    from episodes.best_friend_eye_contact.scenes import PHRASES
    os.makedirs(OUT, exist_ok=True)
    rows = []
    prev_end = 0.0
    for i, p in enumerate(PHRASES):
        nxt = PHRASES[i + 1]["t0"] if i + 1 < len(PHRASES) else DUR
        end = min(nxt - 0.02, p["t1"] + (0.55 if p["last_in_line"] else 0.15))
        text = " ".join(w for w, _, _ in p["words"])
        start = max(0.0, p["t0"] - 0.05, prev_end + 0.001)
        rows.append(f"{i + 1}\n{fmt(start)} --> {fmt(end)}\n{text}\n")
        prev_end = end
    open(SRT, "w").write("\n".join(rows))
    return SRT


# ------------------------------------------------------------------ video
def _worker(args):
    idx, f0, f1, path, draft = args
    from episodes.best_friend_eye_contact import scenes
    crf = "28" if draft else "16"
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast" if draft else "slow",
           "-crf", crf, "-pix_fmt", "yuv420p", path]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import cairo
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for f in range(f0, f1):
        scenes.render(f / FPS, surf)
        surf.flush()
        pr.stdin.write(bytes(surf.get_data()))
    pr.stdin.close()
    pr.wait()
    return path


def render_video(draft=False, workers=4):
    os.makedirs(BUILD, exist_ok=True)
    total = int(round(DUR * FPS))
    nseg = workers * 3
    bounds = [round(total * i / nseg) for i in range(nseg + 1)]
    jobs = [(i, bounds[i], bounds[i + 1], os.path.join(BUILD, f"seg_{i:02d}.mp4"), draft) for i in range(nseg)]
    with mp.Pool(workers) as pool:
        segs = pool.map(_worker, jobs)
    lst = os.path.join(BUILD, "segs.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in segs))
    silent = os.path.join(BUILD, "silent.mp4")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                    silent], check=True)
    return silent


def mux(silent, mix, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", silent, "-i", mix, "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-movflags", "+faststart", "-shortest", out], check=True)
    return out


def stills(times):
    from episodes.best_friend_eye_contact import scenes
    d = os.path.join(BUILD, "stills")
    os.makedirs(d, exist_ok=True)
    for t in times:
        scenes.render(t).write_to_png(os.path.join(d, f"t_{t:06.2f}.png"))


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "all"
    if cmd == "stills":
        stills([float(x) for x in a[1:]])
    elif cmd == "audio":
        print(mix_audio(), write_srt())
    elif cmd in ("video", "all"):
        draft = "--draft" in a
        mix = mix_audio()
        write_srt()
        silent = render_video(draft)
        out = os.path.join(BUILD, f"{NAME}_draft.mp4") if draft else FINAL
        print(mux(silent, mix, out))


if __name__ == "__main__":
    main()
