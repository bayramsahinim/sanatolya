#!/usr/bin/env bash
# Mux rendered frames + soundtrack into the final H.264/AAC MP4 (1080x1920, 30 fps).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; B="$ROOT/build/p3"; OUT="$ROOT/output/JUST_NEEDY_ZOMBIE_PART_3_FINAL.mp4"
n=$(ls "$B/frames" | grep -c '\.jpg$'); echo "frames: $n"
ffmpeg -y -hide_banner -loglevel warning -framerate 30 -i "$B/frames/f%05d.jpg" -i "$B/soundtrack_raw.wav" \
  -map 0:v -map 1:a -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -profile:v high -level 4.2 \
  -movflags +faststart -r 30 \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 256k -ar 48000 \
  -t 60.5 -metadata title="Just Needy — Zombie Apocalypse Part 3: Don't Let It Out" "$OUT"
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of compact "$OUT"
