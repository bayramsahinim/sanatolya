"""Ask Gemini to blind-describe audio files (QA for procedural SFX). usage: python -m tools.judge_audio f.wav ..."""
import base64, subprocess, time, sys
from cinecode.transcribe import _call
Q="This is a sound effect for a cartoon. In one short blunt sentence, what does it sound like? If it is a voice, say whether it is clearly a human voice or convincingly an animal/creature."
for f in sys.argv[1:]:
    subprocess.run(["ffmpeg","-loglevel","error","-y","-i",f,"-t","8","-b:a","96k","/tmp/s.mp3"],check=True)
    b=base64.b64encode(open("/tmp/s.mp3","rb").read()).decode()
    out=None
    for attempt in range(5):
        for m in ["gemini-3.1-flash-lite","gemini-3.5-flash-lite"]:
            try: out=_call(m,b,Q).strip(); break
            except Exception: pass
        if out: break
        time.sleep(4)
    print(f.split('/')[-1], "|", out, flush=True)
