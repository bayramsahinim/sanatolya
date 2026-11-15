# Just Needy — Cinecode episodes

**Cinecode** is the code-driven 2D animation pipeline used to produce Just Needy episodes:
vector characters and sets drawn with Cairo, procedural sound design and music, Gemini TTS
narration, and ffmpeg assembly. Every frame and sound is reproducible from this repository.

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

## Episode: "Japan's Vanishing People" (vertical short)

English adaptation of a Turkish short about jōhatsu and *yonige-ya* (night movers): same hook, beats and ending,
with original art, voice and score.

| Deliverable | Path |
|---|---|
| Final video (1080×1920, 30 fps, 68 s, H.264/AAC, −14 LUFS) | `output/JUST_NEEDY_JAPAN_DISAPPEARANCE_ENGLISH.mp4` |
| English subtitles | `output/JUST_NEEDY_JAPAN_DISAPPEARANCE_ENGLISH.srt` |
| Revised-hook final (new 0:00–0:03.34, rest unchanged) | `output/JUST_NEEDY_JAPAN_DISAPPEARANCE_HOOK_FINAL.mp4` |

```
episodes/japan_johatsu/
  script.py     Turkish source transcript, English lines, factual notes
  make_voice.py one-take Gemini TTS narration (cached in assets/audio/tts/johatsu)
  timing.py     pause-cut pieces -> word timings -> 1-3 word caption groups
  art.py        2.5D kit: shaded round-head rig, glows, contact shadows, camera, grain/vignette
  sets.py       apartment, alley, street, van, phone, Japan map ...
  shots.py      26 shots keyed to the narration
  render.py     frames + bloom + captions -> silent video
  mix.py        procedural score, ambience, SFX, voice mix; SRT
  hook.py       revised opening: counting yen -> gloved hand takes it -> he leaves, door shuts -> empty room
  hook_splice.py splices the new opening into the approved export (video frames 0-100, audio delta only)
```

```bash
python -m episodes.japan_johatsu.render video build/johatsu_silent.mp4
python -m episodes.japan_johatsu.mix build/johatsu_mix.wav output/JUST_NEEDY_JAPAN_DISAPPEARANCE_ENGLISH.srt
ffmpeg -i build/johatsu_silent.mp4 -i build/johatsu_mix.wav -map 0:v -map 1:a -c:v libx264 -preset slow \
  -crf 23 -tune film -pix_fmt yuv420p -af "loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 192k \
  -movflags +faststart -shortest output/JUST_NEEDY_JAPAN_DISAPPEARANCE_ENGLISH.mp4
```
