"""Pre-delivery checks for Part 3."""
import json, subprocess, sys, re
mp4 = sys.argv[1] if len(sys.argv) > 1 else "output/JUST_NEEDY_ZOMBIE_PART_3_FINAL.mp4"
srt = mp4.replace(".mp4", ".srt")
info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", mp4], capture_output=True, text=True).stdout)
v = [s for s in info["streams"] if s["codec_type"] == "video"][0]; a = [s for s in info["streams"] if s["codec_type"] == "audio"][0]
dur = float(info["format"]["duration"])
checks = {
    "H.264": v["codec_name"] == "h264", "1080x1920": (v["width"], v["height"]) == (1080, 1920),
    "30 fps": v["r_frame_rate"] == "30/1", "58-62 s": 58 <= dur <= 62, "AAC audio": a["codec_name"] == "aac",
}
lo = subprocess.run(["ffmpeg", "-hide_banner", "-i", mp4, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", lo)[-1]); P = float(re.findall(r"Peak:\s+(-?[\d.]+) dBFS", lo)[-1])
checks["loudness -14 +/-1 LUFS"] = abs(I + 14) <= 1; checks["true peak <= -1 dBTP"] = P <= -1.0
cues = re.findall(r"(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)", open(srt).read())
ts = [(int(h)*3600+int(m)*60+int(s)+int(ms)/1000) for h, m, s, ms, *_ in cues]
checks[f"SRT {len(cues)} cues, monotonic, inside runtime"] = ts == sorted(ts) and ts[-1] < dur
for k, ok in checks.items(): print(("PASS " if ok else "FAIL ") + k)
print(f"duration {dur:.2f}s  loudness {I} LUFS  peak {P} dBTP")
sys.exit(0 if all(checks.values()) else 1)
