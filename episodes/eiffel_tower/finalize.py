"""Mux video + mix, export final MP4 and SRT into output/."""
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V = os.path.join(ROOT, "build", "video_noaudio.mp4")
A = os.path.join(ROOT, "build", "mix_ln.wav")
OUT = os.path.join(ROOT, "output", "JUST_NEEDY_EIFFEL_TOWER_FINAL.mp4")

if __name__ == "__main__":
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", V, "-i", A, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-maxrate", "11M", "-bufsize", "22M", "-pix_fmt", "yuv420p", "-r", "30",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", OUT], check=True)
    print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height,r_frame_rate,codec_name",
                          "-of", "compact", OUT], capture_output=True, text=True).stdout)
