#!/usr/bin/env bash
# Mux rendered frames + soundtrack into the deliverables (1080x1920, 30 fps, H.264 2-pass ~11.5 Mb/s, AAC).
#   assemble.sh            -> output/JUST_NEEDY_ZOMBIE_PART_3_FINAL.mp4      (no burned captions)
#   assemble.sh captioned  -> output/JUST_NEEDY_ZOMBIE_PART_3_CAPTIONED.mp4  (word-group captions burned in)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; B="$ROOT/build/p3"
VF="null"; OUT="$ROOT/output/JUST_NEEDY_ZOMBIE_PART_3_FINAL.mp4"
if [ "${1:-}" = "captioned" ]; then
  VF="subtitles=$B/captions.ass:fontsdir=$B/fonts"; OUT="$ROOT/output/JUST_NEEDY_ZOMBIE_PART_3_CAPTIONED.mp4"
  mkdir -p "$B/fonts"; cp "$ROOT/assets/fonts/Montserrat-ExtraBold.ttf" "$B/fonts/"
fi
V="-c:v libx264 -preset slow -b:v 11500k -maxrate 16000k -bufsize 24000k -pix_fmt yuv420p -profile:v high -level 4.2 -r 30"
cd "$B"
ffmpeg -y -hide_banner -loglevel error -thread_queue_size 512 -framerate 30 -i frames/f%05d.jpg -vf "$VF" $V -pass 1 -passlogfile "$B/x264" -an -f mp4 /dev/null
ffmpeg -y -hide_banner -loglevel error -thread_queue_size 512 -framerate 30 -i frames/f%05d.jpg -i soundtrack_raw.wav -map 0:v -map 1:a \
  -vf "$VF" $V -pass 2 -passlogfile "$B/x264" \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000" -c:a aac -b:a 256k -ar 48000 -t 60.5 -movflags +faststart \
  -metadata title="Just Needy - Zombie Apocalypse Part 3: Don't Let It Out" "$OUT"
ls -la "$OUT"
