# Just Needy — Cinecode episodes

**Cinecode** is the code-driven 2D animation pipeline used to produce Just Needy episodes:
vector characters and sets drawn with Cairo, procedural sound design and music, Gemini TTS
narration, and ffmpeg assembly. Every frame and sound is reproducible from this repository.

## Episode: "The Number Above Their Head" (vertical short)

Just Needy adaptation of a reference short: same story, scene order and message (numbers above
people's heads = how many more times you'll see them), retold with the blue-hoodie hero in a
monochrome "glow-line" look with blue accents.

| Deliverable | Path |
|---|---|
| Final video (1080×1920, 30 fps, 2:58.6, H.264/AAC) | `output/The_Number_Above_Their_Head.mp4` |
| English subtitles (burned in + SRT) | `output/The_Number_Above_Their_Head.en.srt` |
| Landscape YouTube version (1920×1080, 30 fps, same film reframed for 16:9) | `output/The_Number_Above_Their_Head_16x9.mp4` |

Code: `episodes/numbers_above/` (`script.py` narration, `look.py` palette/bloom/numbers, `cast.py`
characters, `sets.py` line-art sets + phone UI, `shots_a.py`/`shots_b.py` 25 shots, `frame.py`
timeline + subtitles, `mixdown.py` score/SFX/mix, `episode.py` driver).

```bash
python -m episodes.numbers_above.make_voice          # TTS takes (cached in assets/audio/tts_numbers)
python -m episodes.numbers_above.make_voice split    # split takes into per-line clips
python -m episodes.numbers_above.episode audio       # soundtrack + SRT
python -m episodes.numbers_above.episode video       # render (then 2-pass re-encode to <100 MB, see below)
```
Landscape: `python -m episodes.numbers_above.episode video --land` renders the same shots through per-shot
16:9 views (`landscape.py`), with widened sets and a few side-by-side recompositions; audio and subtitles are shared.

Final file was re-encoded with `ffmpeg -c:v libx264 -preset slow -b:v 3900k` (2-pass) to stay under GitHub's 100 MB limit.

## Episode: "I Got Stuck in Ancient Rome for 7 Days"

| Deliverable | Path |
|---|---|
| Final video (1920×1080, 30 fps, H.264/AAC) | `output/I_Got_Stuck_in_Ancient_Rome_for_7_Days.mp4` |
| English subtitles (YouTube CC) | `output/I_Got_Stuck_in_Ancient_Rome_for_7_Days.en.srt` |
| Thumbnail | `output/thumbnail_1280x720.jpg`, `output/thumbnail_1920x1080.png` |

### Layout

```
cinecode/            engine
  core.py            canvas helpers, easing, keyframes, camera
  characters.py      stick-figure rig + cast (hero, Maximus, Lucia, the boy, Romans)
  props.py, sets.py  props and environments (room, Roman street, forum, bakery, square, desert)
  captions.py        on-screen text, implemented to the channel caption spec
  timeline.py        shot planning (animation timed to the real voice clips) + episode assembly
  audio.py           procedural SFX, music, ambience, mixing helpers
  tts.py / align.py  Gemini TTS client, take-to-line alignment
config/narrator_voice.json   the channel narrator voice (reuse for every episode)
episodes/rome_7_days/
  script.py          narration + dialogue
  scenes_*.py        shots for scenes 1-10
  episode.py         assemble / render / mix / SRT
  qa.py              pre-delivery checks
assets/              font (Montserrat ExtraBold, OFL) and cached TTS takes
```

### Rebuild

```bash
pip install pycairo numpy scipy soundfile pillow librosa fonttools
apt-get install -y ffmpeg rubberband-cli espeak-ng
mkdir -p ~/.fonts && cp assets/fonts/Montserrat-ExtraBold.ttf ~/.fonts && fc-cache -f

python -m episodes.rome_7_days.make_voice           # TTS (cached in assets/audio/tts)
python -m episodes.rome_7_days.align_voice          # split takes into lines
python -m episodes.rome_7_days.episode audio        # soundtrack + SRT
python -m episodes.rome_7_days.episode video        # final 1080p render
python -m episodes.rome_7_days.thumbnail
python -m episodes.rome_7_days.qa output/I_Got_Stuck_in_Ancient_Rome_for_7_Days.mp4
```
