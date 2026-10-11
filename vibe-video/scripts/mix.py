#!/usr/bin/env python3
# Mix BGM + the laugh track at the five laugh moments. usage: python3 mix.py video.mp4 out.mp4
# L 是每一路笑声（起点秒、变速、音量、截止秒），DUCK 是 BGM 压低的时间窗；换片只改这两张表和输入音频文件名。
import subprocess, sys

video, out = sys.argv[1], sys.argv[2]

# (start, rate, volume, cut_at) ; rate != 1 shifts pitch+speed for the crowd voices
L = [
    (6.0, 1.0, 1.5, 10.1),
    (30.0, 1.0, 1.5, 31.6),
    # 卷三 chorus: a crowd of voices
    (84.0, 1.0, 1.4, 89.2),
    (84.18, 1.12, 0.7, 89.2),
    (84.4, 0.9, 0.7, 89.2),
    (84.65, 1.25, 0.5, 89.2),
    (84.9, 0.82, 0.5, 89.2),
    # 卷六: one laugh, then more and more screens join; everything stops dead at 146
    (138.0, 1.0, 1.4, 146.0),
    (139.4, 1.1, 0.6, 146.0),
    (140.8, 0.92, 0.45, 146.0),
    (140.9, 1.2, 0.45, 146.0),
    (142.4, 0.85, 0.35, 146.0),
    (142.5, 1.3, 0.35, 146.0),
    (142.6, 1.05, 0.35, 146.0),
    (143.3, 1.0, 0.6, 146.0),  # second full pass keeps the wall loud to the end
    # ending
    (170.0, 1.0, 1.5, 175.0),
]
# BGM ducking windows (start, end)
DUCK = [(5.95, 10.15), (29.95, 31.7), (83.9, 89.4), (137.9, 146.3), (169.9, 175.2)]

def duck_expr():
    terms = []
    for a, b in DUCK:
        # trapezoid: 0.15 s ramps
        terms.append(f"min(max((t-{a})/0.15,0),1)*min(max(({b}-t)/0.3,0),1)")
    m = terms[0]
    for x in terms[1:]:
        m = f"max({m},{x})"
    return f"1-0.93*({m})"

fc = [f"[1:a]volume='{duck_expr()}':eval=frame,aresample=48000[bgm]"]
labels = ["[bgm]"]
for i, (s, r, v, cut) in enumerate(L):
    dur = cut - s
    chain = f"[2:a]"
    filt = []
    if r != 1.0:
        filt.append(f"asetrate={int(48000*r)},aresample=48000")
    filt.append(f"atrim=0:{dur:.3f}")
    fade = 0.06 if cut in (146.0,) else 0.25
    filt.append(f"afade=t=out:st={max(0, dur-fade):.3f}:d={fade}")
    filt.append(f"volume={v}")
    ms = int(round(s * 1000))
    filt.append(f"adelay={ms}|{ms}")
    fc.append(chain + ",".join(filt) + f"[l{i}]")
    labels.append(f"[l{i}]")
fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.95,atrim=0:175[a]")
cmd = ["ffmpeg", "-y", "-i", video, "-i", "public/bgm.mp3", "-i", "public/laugh.wav", "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", out]
print(" ".join(cmd[:8]), "...")
subprocess.run(cmd, check=True)
