"""Mux picture + soundtrack -> final deliverables in output/.

usage: python -m episodes.zombie_day_1.finalize
"""
import os
import shutil
import subprocess

from .render import BUILD, ROOT

NAME = "JUST_NEEDY_ZOMBIE_DAY_1_REMASTERED"


def main():
    # Ending revision: final_audio.wav = v1 delivered soundtrack (already loudness-normalised) with the
    # new ending spliced in -> mux as-is. Fresh builds without it normalise mix.wav instead.
    spliced = os.path.join(BUILD, "final_audio.wav")
    global AUDIO, AF
    if os.path.exists(spliced):
        AUDIO, AF = spliced, []
    else:
        AUDIO, AF = os.path.join(BUILD, "mix.wav"), ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
    out = os.path.join(ROOT, "output", NAME + ".mp4")
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-i", os.path.join(BUILD, "video_silent.mp4"),
        "-i", AUDIO,
        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-maxrate", "9M", "-bufsize", "18M", "-tune", "grain",
        "-pix_fmt", "yuv420p", "-r", "30",
        *AF, "-ar", "48000",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    shutil.copy(os.path.join(BUILD, "day1.srt"), os.path.join(ROOT, "output", NAME + ".srt"))
    print(out)


if __name__ == "__main__":
    main()
