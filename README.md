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

## Short: "Your Brain Can't Stop Reading" (Stroop Effect Challenge)

Color-reading Short adapted from a Turkish reference. Revision 2: game starts within ~7 s,
19 challenges (5 / 6 / 8 cards at 1.8 s / 1.25 s / 1.0 s), level 3 read aloud as a distraction
after an explicit "ignore my voice" rule, clean `? / 19` + "COMMENT YOUR SCORE!" ending.
Soft UI sound design (no whooshes/ticks/buzzers), steady music bed 17-21 dB under the voice,
static master at about -15.5 LUFS / -1.5 dBTP.

| Deliverable | Path |
|---|---|
| Final video (1080×1920, 30 fps, H.264/AAC, 64.6 s) | `output/Your_Brain_Cant_Stop_Reading_Stroop_Challenge.mp4` |
| English subtitles | `output/Your_Brain_Cant_Stop_Reading_Stroop_Challenge.en.srt` |

```
episodes/stroop_challenge/
  script.py      challenges (word, ink colour), ink palette, narration lines
  make_voice.py  Gemini TTS, one take per line (cached in assets/audio/tts/stroop)
  timeline.py    narration placement, word timings, card schedule, scene ranges
  render.py      scenes, HUD, cards, captions, mascot
  episode.py     voice chain, sound design, music, master, SRT, video
```

```bash
python -m episodes.stroop_challenge.make_voice
python -m episodes.stroop_challenge.timeline        # print the timing plan
python -m episodes.stroop_challenge.episode all
```
