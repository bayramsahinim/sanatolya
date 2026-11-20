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
from episodes.stroop_challenge.script import LEVELS

NAME = "Your_Brain_Cant_Stop_Reading_Stroop_Challenge"
OUT_MP4 = f"output/{NAME}.mp4"
OUT_SRT = f"output/{NAME}.en.srt"
MIX = "build/stroop_mix.wav"
FPS = 30
W, H = 1080, 1920
SR = A.SR


# ============================================================ audio
def sfx_buzz():
    d = 0.32
    t = A.t_arr(d)
    x = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in (110, 116.5))
    x = A.lp(x, 1600) * A.env_adsr(len(t), 0.005, 0.05, 0.7, 0.08)
    return A.norm(x, 0.5)


def sfx_tick():
    d = 0.04
    t = A.t_arr(d)
    x = np.sin(2 * np.pi * 1900 * t) * A.exp_env(len(t), 0.006) + A.hp(A.noise(d, 9), 3000) * A.exp_env(len(t), 0.003) * 0.4
    return A.norm(x, 0.35)


def sfx_go():
    d = 0.5
    t = A.t_arr(d)
    x = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((880, 1), (1320, 0.5), (1760, 0.25)))
    return A.norm(x * A.exp_env(len(t), 0.12), 0.45)


def sfx_stamp():
    x = A.sfx_thud(90, 0.4).copy()
    c = A.sfx_click()
    x[:len(c)] += 0.4 * c
    return A.norm(x, 0.8)


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

    sfx = np.zeros(n)
    # scene transitions (soft whoosh), level starts, card pops, timer ticks
    for name, t0, t1 in tl.scenes():
        if name.startswith("play"):
            continue
        if t0 > 0.5:
            A.add(sfx, A.sfx_whoosh(0.35, 400, 2200) * 0.12, t0 - 0.12)
    for li, lv in enumerate(T["levels"]):
        A.add(sfx, sfx_go() * 0.8, lv["start"] - 0.05)
        for k, (a, b) in enumerate(lv["cards"]):
            A.add(sfx, A.sfx_pop() * 0.35, a)
            # clock ticks across each card; faster levels tick faster
            step = [0.4, 0.275, 0.2375][li]
            tt = a + step
            while tt < b - 0.05:
                A.add(sfx, sfx_tick() * 0.5, tt)
                tt += step
        A.add(sfx, A.sfx_ding() * 0.25, lv["end"])
    # demo badges
    wd = L["demo"]["words"]
    A.add(sfx, sfx_buzz() * 0.45, wd[2])
    A.add(sfx, A.sfx_ding() * 0.35, wd[11])
    # 1935 stamp + crosses
    A.add(sfx, sfx_stamp() * 0.7, L["y1935"]["words"][6])
    for j in range(7):
        A.add(sfx, A.sfx_click() * 0.35, L["y1935"]["words"][3] + j * 0.28)
    # recap checkmarks, trap glow, race, kids, stats
    A.add(sfx, A.sfx_ding() * 0.25, L["matched"]["words"][4])
    A.add(sfx, A.sfx_sparkle() * 0.3, L["trap"]["words"][3])
    A.add(sfx, A.sfx_whoosh(0.5, 300, 3000) * 0.25, L["auto"]["start"] + 0.3)
    A.add(sfx, A.sfx_ding() * 0.3, L["kids"]["words"][8])
    A.add(sfx, A.sfx_whoosh(0.6, 200, 1500) * 0.2, L["slow"]["words"][6] - 0.3)
    # ending
    A.add(sfx, sfx_stamp() * 0.9, L["stop"]["start"])
    A.add(sfx, A.sfx_pop() * 0.4, L["howmany"]["start"] + 0.35)
    A.add(sfx, A.sfx_pop() * 0.4, L["comment"]["start"])
    A.add(sfx, sfx_stamp() * 0.8, L["believe"]["start"] + 1.1)

    # music bed: light quirky loop, ducked under narration, quieter during play
    mus = A.track("quirky", dur)[:n]
    mus = mus / max(1e-6, np.abs(mus).max())
    env = A.envelope_follow(voice, 0.03, 0.4)
    env = env / max(1e-6, env.max())
    gain = 0.16 - 0.08 * np.clip(env * 2.5, 0, 1)
    tt = np.arange(n) / SR
    for lv in T["levels"]:
        inside = (tt > lv["start"] - 0.3) & (tt < lv["end"] + 0.3)
        gain[inside] *= 0.7
    fade = np.clip(tt / 0.6, 0, 1) * np.clip((T["end"] - tt) / 1.2, 0, 1)
    mus = mus * gain * fade

    mix = voice + sfx * 0.9 + mus
    peak = np.abs(mix).max()
    mix = mix / peak * 0.89
    os.makedirs("build", exist_ok=True)
    sf.write(MIX, mix.astype(np.float32), SR)
    # loudness: report voice-vs-music level for QA
    vrms = np.sqrt((voice[np.abs(voice) > 0.02] ** 2).mean())
    mrms = np.sqrt((mus ** 2).mean())
    print(f"mix {dur:.2f}s  voice/music RMS ratio {20*np.log10(vrms/mrms):.1f} dB -> {MIX}")


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
                    "-i", MIX, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
                    "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", OUT_MP4], check=True)
    print("video ->", OUT_MP4)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    os.makedirs("output", exist_ok=True)
    if what in ("audio", "all"):
        build_audio()
        build_srt()
    if what in ("video", "all"):
        build_video()
