"""Assemble the Short: soundtrack, SRT, video.

usage:
  python -m episodes.stroop_challenge.episode audio   # build/stroop_mix.wav + output SRT
  python -m episodes.stroop_challenge.episode video   # final MP4 (needs audio first)
  python -m episodes.stroop_challenge.episode all
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
import soundfile as sf

from cinecode import audio as A
from cinecode import tts
from episodes.stroop_challenge import timeline as tl

NAME = "Your_Brain_Cant_Stop_Reading_Stroop_Challenge"
OUT_MP4 = f"output/{NAME}.mp4"
OUT_SRT = f"output/{NAME}.en.srt"
MIX = "build/stroop_mix.wav"
MASTER = "build/stroop_master.wav"
FPS = 30
W, H = 1080, 1920
SR = A.SR


# ============================================================ audio
# Revision 2 sound design: no whooshes, ticks, buzzers or stamps. Every effect is a
# short, low-passed, softly enveloped tone, levelled against the narration.
def _env(n, att, tau):
    e = np.exp(-np.arange(n) / (tau * SR))
    na = max(1, int(att * SR))
    e[:na] *= np.linspace(0, 1, na)
    e[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    return e


def soft_tap():
    """Muted wooden UI tap for card changes."""
    d = 0.09
    t = A.t_arr(d)
    x = np.sin(2 * np.pi * 520 * t) + 0.35 * np.sin(2 * np.pi * 1040 * t)
    return A.lp(x * _env(len(t), 0.004, 0.022), 2400)


def soft_chime(notes=(784.0, 1174.7), gap=0.07):
    """Gentle two-note marimba-like chime (level start / correct)."""
    d = 0.55 + gap * (len(notes) - 1)
    out = np.zeros(int(d * SR))
    for i, f in enumerate(notes):
        t = A.t_arr(0.55)
        x = (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t)) * _env(len(t), 0.008, 0.16)
        s0 = int(i * gap * SR)
        out[s0:s0 + len(x)] += x
    return A.lp(out, 3500)


def soft_thump():
    """Soft low 'nope' for the wrong example and STOP."""
    d = 0.22
    t = A.t_arr(d)
    f = 150 * np.exp(-t * 2.0)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return A.lp(x * _env(len(t), 0.008, 0.07), 900)


def level_to(x, ref_rms, db_below):
    """Scale an effect so its RMS (over its audible part) sits `db_below` the narration RMS."""
    act = x[np.abs(x) > np.abs(x).max() * 0.05]
    r = np.sqrt((act ** 2).mean())
    return x / max(r, 1e-9) * ref_rms * 10 ** (-db_below / 20)


SFX_DB = {"tap": 22, "chime": 15, "thump": 15}


def process_voice(v):
    """Broadcast-style voice chain on the narration stem only: gentle compression + peak control."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        sf.write(f"{d}/in.wav", v.astype(np.float32), SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{d}/in.wav", "-af",
                        "acompressor=threshold=-22dB:ratio=3:attack=5:release=120:knee=6:makeup=3,"
                        "alimiter=limit=0.8:attack=2:release=50:level=disabled",
                        "-ar", str(SR), f"{d}/out.wav"], check=True)
        out, _ = sf.read(f"{d}/out.wav")
    return out[:len(v)] if len(out) >= len(v) else np.pad(out, (0, len(v) - len(out)))


def build_audio():
    T = tl.build()
    L = T["lines"]
    dur = T["end"] + 0.2
    n = int(dur * SR)
    voice = np.zeros(n)
    for lid, l in L.items():
        a = A.resample(tl.take(lid), tts.SR, SR)
        A.add(voice, A.fade(a, 0.004, 0.03), l["start"])
    # level-3 distractor words
    w = tl.take("l3read")
    for item in T["l3words"]:
        s0, s1 = item["src"]
        seg = w[int(s0 * tts.SR): int(s1 * tts.SR)]
        A.add(voice, A.fade(A.resample(seg, tts.SR, SR), 0.004, 0.04), item["at"])
    voice = voice / max(1e-6, np.abs(voice).max()) * 0.85
    voice = process_voice(voice)
    vrms = np.sqrt((voice[np.abs(voice) > 0.02] ** 2).mean())

    tap = level_to(soft_tap(), vrms, SFX_DB["tap"])
    chime = level_to(soft_chime(), vrms, SFX_DB["chime"])
    chime1 = level_to(soft_chime((1046.5,)), vrms, SFX_DB["chime"] + 3)
    thump = level_to(soft_thump(), vrms, SFX_DB["thump"])

    sfx = np.zeros(n)
    events = []
    rw = L["rule"]["words"]
    events += [(thump, rw[3]), (chime, rw[6])]                      # RED x, GREEN check
    for li, lv in enumerate(T["levels"]):
        events.append((chime, lv["start"]))                          # level starts
        for k, (a, b) in enumerate(lv["cards"][1:], 1):
            events.append((tap, a))                                  # quiet card change
        events.append((chime1, lv["end"]))                           # level done
    events.append((chime1, L["matched"]["words"][4]))                # "two of them matched"
    events.append((thump, L["stop"]["start"]))
    events.append((chime, L["stop"]["end"] + 0.4))                   # score screen
    for x, t0 in events:
        A.add(sfx, x, t0)

    # music bed: subtle and steady, softened top end, gentle slow ducking under the voice
    mus = A.lp(A.track("warm", dur)[:n], 5000)   # steady pad bed (4-5 dB short-term spread)
    # level the bed itself: constant short-term loudness (the composition has loud/quiet passages)
    k = int(1.2 * SR)
    ms = np.convolve(mus ** 2, np.ones(k) / k, mode="same")
    ms_floor = np.percentile(ms, 20)
    mus = mus / np.sqrt(np.maximum(ms, ms_floor))
    # mild, slow duck: -17 dB in gaps, -20 dB under narration
    env = A.envelope_follow(voice, 0.3, 1.0)
    env = np.clip(env / max(1e-6, np.percentile(env[env > 0], 90)), 0, 1)
    k2 = int(0.5 * SR)
    env = np.convolve(env, np.ones(k2) / k2, mode="same")
    db = -17 - 3 * env
    tt = np.arange(n) / SR
    fade = np.clip(tt / 0.8, 0, 1) * np.clip((T["end"] - tt) / 1.2, 0, 1)
    mus = mus * vrms * 10 ** (db / 20) * fade

    mix = voice + sfx + mus
    for nm, x in (("voice", voice), ("sfx", sfx), ("music", mus)):
        sf.write(f"build/stroop_stem_{nm}.wav", x.astype(np.float32), SR)
    mix = mix / np.abs(mix).max() * 0.89
    os.makedirs("build", exist_ok=True)
    sf.write(MIX, mix.astype(np.float32), SR)
    mrms = np.sqrt((mus[(env > 0.5)] ** 2).mean())
    print(f"mix {dur:.2f}s -> {MIX}")
    print(f"  music under narration: {20*np.log10(vrms/mrms):.1f} dB below voice")
    for name, x in (("tap", tap), ("chime", chime), ("thump", thump)):
        act = x[np.abs(x) > np.abs(x).max() * 0.05]
        print(f"  {name:6} {20*np.log10(vrms/np.sqrt((act**2).mean())):.1f} dB below voice, "
              f"peak {20*np.log10(vrms/np.abs(x).max()):.1f} dB below voice RMS")


def _lufs(path, af=None):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", path]
    if af:
        cmd += ["-af", af + ",ebur128"]
    else:
        cmd += ["-af", "ebur128"]
    r = subprocess.run(cmd + ["-f", "null", "-"], capture_output=True, text=True).stderr
    return float(r[r.rindex("I:"):].split()[1])


def master(target=-14.5):
    """Static master: ONE fixed gain + safety peak limiter (the voice stem is already compressed).
    (No dynamic loudness normalisation - it would pump the music up in the gaps.)"""
    gain = target - _lufs(MIX)
    chain = f"volume={gain:.2f}dB,alimiter=limit=0.74:attack=1:release=60:level=disabled"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", MIX, "-af", chain, "-ar", str(SR), MASTER], check=True)
    print(f"master -> {MASTER}  (static gain {gain:+.1f} dB, {_lufs(MASTER):.1f} LUFS)")


# ============================================================ SRT
def fmt(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt():
    T = tl.build()
    cues = []
    for lid in T["order"]:
        l = T["lines"][lid]
        cues.append((l["start"], l["end"] + 0.25, l["text"]))
        if lid == "readyou":
            ws = T["l3words"]
            cues.append((ws[0]["at"], ws[-1]["at"] + 0.8,
                         " ".join(w["word"].capitalize() + "." for w in ws)))
    cues.sort()
    for i in range(len(cues) - 1):          # no overlaps
        if cues[i][1] > cues[i + 1][0]:
            cues[i] = (cues[i][0], cues[i + 1][0] - 0.02, cues[i][2])
    with open(OUT_SRT, "w") as f:
        for i, (a, b, s) in enumerate(cues, 1):
            f.write(f"{i}\n{fmt(a)} --> {fmt(b)}\n{s}\n\n")
    print("srt ->", OUT_SRT, len(cues), "cues")


# ============================================================ video
def _render_chunk(args):
    idx, f0, f1 = args
    import cairo
    from episodes.stroop_challenge import render
    path = f"build/stroop_chunks/c{idx:03d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "16", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    for fi in range(f0, f1):
        cx = cairo.Context(s)
        render.frame(cx, fi / FPS)
        s.flush()
        p.stdin.write(bytes(s.get_data()))
    p.stdin.close()
    p.wait()
    return path


def build_video(draft=False):
    T = tl.build()
    nfr = int(round(T["end"] * FPS))
    os.makedirs("build/stroop_chunks", exist_ok=True)
    step = 90
    jobs = [(i, a, min(nfr, a + step)) for i, a in enumerate(range(0, nfr, step))]
    with Pool(os.cpu_count()) as pool:
        paths = []
        for k, pth in enumerate(pool.imap(_render_chunk, jobs)):
            paths.append(pth)
            print(f"\r  chunks {k + 1}/{len(jobs)}", end="", flush=True)
    print()
    with open("build/stroop_chunks/list.txt", "w") as f:
        for pth in paths:
            f.write(f"file '{os.path.abspath(pth)}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "build/stroop_chunks/list.txt",
                    "-i", MASTER, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", OUT_MP4], check=True)
    print("video ->", OUT_MP4)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs("output", exist_ok=True)
    if what in ("audio", "all"):
        build_audio()
        master()
        build_srt()
    if what in ("video", "all"):
        build_video()
