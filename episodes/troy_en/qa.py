"""Pre-delivery checks for the Troy short.

usage: python -m episodes.troy_en.qa output/Just_Needy_The_Trojan_Horse_EN.mp4
"""
import json
import re
import subprocess
import sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main(path):
    ok = True
    pr = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path]).stdout)
    v = [s for s in pr["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in pr["streams"] if s["codec_type"] == "audio"][0]
    dur = float(pr["format"]["duration"])
    checks = [
        ("resolution 1080x1920", (v["width"], v["height"]) == (1080, 1920)),
        ("30 fps", v["r_frame_rate"] == "30/1"),
        ("h264 / aac", v["codec_name"] == "h264" and a["codec_name"] == "aac"),
        (f"duration {dur:.1f}s within 55-75s", 55 <= dur <= 75),
        (f"size {int(pr['format']['size']) / 1e6:.1f} MB < 100 MB", int(pr["format"]["size"]) < 100e6),
    ]
    e = run(["ffmpeg", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", e)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", e)[-1])
    checks += [(f"loudness {I:.1f} LUFS (-15..-13)", -15 <= I <= -13), (f"true peak {tp:.1f} dBFS <= -1", tp <= -0.9)]
    bd = run(["ffmpeg", "-i", path, "-vf", "blackdetect=d=0.2:pix_th=0.05", "-an", "-f", "null", "-"]).stderr
    checks.append(("no black gaps", "black_start" not in bd))
    sil = run(["ffmpeg", "-i", path, "-af", "silencedetect=n=-45dB:d=1.2", "-vn", "-f", "null", "-"]).stderr
    checks.append(("no silent gaps > 1.2s", "silence_start" not in sil))
    for name, good in checks:
        print(("PASS " if good else "FAIL ") + name)
        ok &= good
    print("ALL GOOD" if ok else "ISSUES FOUND")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1]) else 1)
