"""Mux picture + soundtrack -> final deliverables in output/.

usage: python -m episodes.zombie_day_1.finalize
"""
import os
import shutil
import subprocess

from .render import BUILD, ROOT

NAME = "JUST_NEEDY_ZOMBIE_DAY_1_REMASTERED"


def main():
    out = os.path.join(ROOT, "output", NAME + ".mp4")
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-i", os.path.join(BUILD, "video_silent.mp4"),
        "-i", os.path.join(BUILD, "mix.wav"),
        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "9M", "-bufsize", "18M", "-tune", "grain",
        "-pix_fmt", "yuv420p", "-r", "30",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    shutil.copy(os.path.join(BUILD, "day1.srt"), os.path.join(ROOT, "output", NAME + ".srt"))
    print(out)


if __name__ == "__main__":
    main()
