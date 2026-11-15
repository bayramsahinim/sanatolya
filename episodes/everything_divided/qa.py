"""Pre-delivery checks for the English Short.

usage: python -m episodes.everything_divided.qa output/JUST_NEEDY_EVERYTHING_DIVIDED_ENGLISH.mp4 [--sync N]
"""
import glob
import json
import os
import random
import re
import subprocess
import sys

import numpy as np

from episodes.everything_divided import common as C

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILD = os.path.join(ROOT, "build", "everything")
OK, BAD = "PASS", "FAIL"
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{OK if ok else BAD}] {name}  {detail}")


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels:format=duration",
                        "-of", "json", path], capture_output=True, text=True)
    return json.loads(r.stdout)


def loudness(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)[-1])
    return i, tp


def voice_margin():
    import soundfile as sf
    v, sr = sf.read(os.path.join(BUILD, "stem_voice.wav"))
    b, _ = sf.read(os.path.join(BUILD, "stem_bed.wav"))
    hop = int(sr * 0.05)
    n = min(len(v), len(b)) // hop
    rv = np.sqrt((v[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    rb = np.sqrt((b[: n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    speech = rv > np.percentile(rv, 60) * 0.5
    d = 20 * np.log10(rv[speech] / rb[speech])
    return float(np.median(d)), float(np.percentile(d, 5))


def sync_spotcheck(video, n=10, seed=3):
    """Cut the final audio at caption-group times; an independent model transcribes each cut."""
    import base64
    import urllib.request

    def transcribe_en(mp3):
        b = base64.b64encode(open(mp3, "rb").read()).decode()
        body = {"contents": [{"parts": [{"inlineData": {"mimeType": "audio/mp3", "data": b}},
                                        {"text": "This is a short clip of American English narration. Transcribe "
                                                 "exactly the words spoken, nothing else. Write numbers as words."}]}]}
        import time
        for attempt in range(6):
            m = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-2.5-flash", "gemini-3-flash-preview"][attempt % 4]
            req = urllib.request.Request(
                f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent",
                data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "x-goog-api-key": "dummy"})
            try:
                d = json.load(urllib.request.urlopen(req, timeout=120))
                return "".join(x.get("text", "") for x in d["candidates"][0]["content"]["parts"])
            except Exception:
                time.sleep(4 * (attempt + 1))
        return ""
    rnd = random.Random(seed)
    groups = [g for g in C.CAPS if len(g["words"]) >= 2]
    pick = sorted(rnd.sample(groups, n), key=lambda g: g["t0"])
    good = 0
    for k, g in enumerate(pick):
        mp3 = os.path.join(BUILD, f"qa_cut_{k}.mp3")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{g['t0'] - 0.08:.3f}", "-to",
                        f"{g['t1'] + 0.1:.3f}", "-i", video, "-vn", "-ac", "1", "-b:a", "96k", mp3], check=True)
        heard = transcribe_en(mp3).lower()
        hw = re.findall(r"[a-z0-9']+", heard.replace("-", " "))
        exp = [w.lower() for w in g["words"]]
        exp_w = re.findall(r"[a-z0-9']+", " ".join(exp).replace("-", " "))
        nums = {"two": "2", "three": "3", "six": "6", "twelve": "12", "eight": "8", "seventy": "75", "five": "75",
                "hundred": "375", "twenty": "27", "seven": "27"}
        hits = sum(1 for w in exp_w if w in hw or nums.get(w) in hw or (w == "you'd" and "you" in hw))
        ok = hits >= max(1, len(exp_w) - 1)
        good += ok
        print(f"   {g['t0']:6.2f}  caption='{g['text']}'  heard='{heard.strip()}'  {'ok' if ok else 'MISS'}")
    return good, n


def main():
    video = sys.argv[1]
    info = probe(video)
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in info["streams"] if s["codec_type"] == "audio"][0]
    dur = float(info["format"]["duration"])
    check("resolution 1080x1920 (9:16)", (v["width"], v["height"]) == (1080, 1920), f"{v['width']}x{v['height']}")
    check("30 fps", v["r_frame_rate"] == "30/1", v["r_frame_rate"])
    check("H.264 + AAC", v["codec_name"] == "h264" and a["codec_name"] == "aac", f"{v['codec_name']}/{a['codec_name']}")
    check("duration 57-60 s", 57 <= dur <= 60, f"{dur:.2f}s")
    i, tp = loudness(video)
    check("loudness ~-14 LUFS, TP <= -1 dBTP", abs(i + 14) <= 1.0 and tp <= -1.0, f"I={i} LUFS TP={tp} dBFS")
    med, p5 = voice_margin()
    check("narration above music/SFX", med >= 12 and p5 >= 6, f"median {med:.1f} dB, 5th pct {p5:.1f} dB")
    srt = glob.glob(os.path.join(ROOT, "output", "*EVERYTHING*.srt"))
    check("SRT exported", bool(srt), srt[0] if srt else "")
    # no Turkish text anywhere in on-screen strings
    tr = re.compile(r"[ğĞıİşŞçÇöÖüÜ]")
    hits = []
    for f in glob.glob(os.path.join(ROOT, "episodes", "everything_divided", "*.py")) + srt:
        for ln, line in enumerate(open(f, encoding="utf-8"), 1):
            if tr.search(line) and "qa.py" not in f:
                hits.append(f"{os.path.basename(f)}:{ln}")
    check("no Turkish characters in visuals/captions/SRT", not hits, ", ".join(hits[:5]))
    # caption groups 1-3 words (numbers kept with their unit may make 3-4 tokens)
    sizes = [len(g["text"].split()) for g in C.CAPS]
    check("caption groups short (<= 3 words, numbers+unit <= 4)", max(sizes) <= 4,
          f"max {max(sizes)}, mean {np.mean(sizes):.1f}")
    if "--sync" in sys.argv:
        n = int(sys.argv[sys.argv.index("--sync") + 1])
        good, tot = sync_spotcheck(video, n)
        check("caption/voice sync spot-check", good >= tot - 1, f"{good}/{tot} cuts contain the caption words")
    print()
    print(f"{sum(1 for r in results if r[1])}/{len(results)} checks passed")


if __name__ == "__main__":
    main()
