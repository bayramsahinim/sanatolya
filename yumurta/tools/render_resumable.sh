#!/bin/bash
# Resumable full render of a story: 2 workers write PNG frames (frames already on disk are skipped), then encode + mux.
# After a container restart just run it again; it continues where it stopped.
#   usage (repo root): nohup setsid yumurta/tools/render_resumable.sh <story> > build/<story>_driver.log 2>&1 < /dev/null &
#   progress: tail build/<story>.log  (ends with "DONE hh:mm:ss")   output: yumurta/stories/<story>/out/<story>.mp4
set -u
STORY=$1; ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT/yumurta/engine"
[ -d node_modules ] || npm install --silent
export CHROME_PATH=${CHROME_PATH:-/opt/pw-browsers/chromium-1243/chrome-linux64/chrome} SWGL=${SWGL:-1}
SD=../stories/$STORY; FR=$SD/out/frames; mkdir -p "$ROOT/build"; LOG=$ROOT/build/$STORY.log
echo "start $(date +%T) have $(ls $FR/*.png 2>/dev/null | wc -l)" >> $LOG
rm -f $FR/*.tmp
node render_frames.mjs $STORY --worker=0 --workers=2 >> $LOG 2>&1 &
node render_frames.mjs $STORY --worker=1 --workers=2 >> $LOG 2>&1 &
wait
N=$(python3 -c "import json;print(json.load(open('$FR/meta.json'))['N'])")
HAVE=$(ls $FR/f*.png | wc -l)
[ "$HAVE" -lt "$N" ] && { echo "INCOMPLETE $HAVE/$N" >> $LOG; exit 1; }
ffmpeg -y -loglevel error -framerate 30 -i $FR/f%05d.png -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart $SD/out/${STORY}_video.mp4
if [ -f $SD/audio/mix.wav ]; then
  ffmpeg -y -loglevel error -i $SD/out/${STORY}_video.mp4 -i $SD/audio/mix.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 256k -shortest $SD/out/$STORY.mp4
else mv $SD/out/${STORY}_video.mp4 $SD/out/$STORY.mp4; fi
echo "DONE $(date +%T)" >> $LOG
