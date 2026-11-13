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

## Short: "He Survived 60 Hours Underwater" (Harrison Okene, Jascon-4, 2013)

| Deliverable | Path |
|---|---|
| Final vertical video (1080×1920, 30 fps, H.264/AAC, 59.3 s, ~-14 LUFS) | `output/HE_SURVIVED_60_HOURS_UNDERWATER_FINAL.mp4` |
| English subtitles (word-aligned) | `output/HE_SURVIVED_60_HOURS_UNDERWATER_FINAL.srt` |

`episodes/okene_60h/`: script + director's notes (`script.py`), one continuous Gemini TTS take
(Fenrir, chosen by A/B against the reference narrator) force-aligned word by word with pocketsphinx
(`cinecode/wordalign.py`) and re-timed into beats (`voice.py`); a lit, graded vertical look with
spot/point light maps, volumetric beams, fog, bloom, grain (`look.py`); textured steel sets
(`sets.py`); cast (`cast.py`); 28 shots timed to the spoken words (`shots_a.py`, `shots_b.py`);
procedural SFX, score and side-chain-ducked mix (`sound.py`).

```bash
pip install pocketsphinx   # plus the deps above
python -m episodes.okene_60h.voice          # narration stem + word timings (from cached take)
python -m episodes.okene_60h.episode video  # render picture (4 processes)
python -m episodes.okene_60h.sound          # SFX + score + mix
python -m episodes.okene_60h.episode final  # mux + SRT -> output/
```
The canvas size is set per episode through `CINECODE_SIZE` (default 1920x1080).
