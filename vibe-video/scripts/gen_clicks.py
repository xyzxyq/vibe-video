#!/usr/bin/env python3
"""按显式秒数生成确定性的咔哒音效；不依赖任何画面源码。"""
import argparse, array, math, random, sys, wave
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('out', type=Path)
p.add_argument('times', nargs='+', type=float)
p.add_argument('--duration', type=float, default=175)
a = p.parse_args()
if not math.isfinite(a.duration) or a.duration <= 0 or any(not math.isfinite(t) or not 0 <= t < a.duration for t in a.times):
    p.error('duration must be positive and every time must be within the duration')
sr = 44100
buf = array.array('h', [0]) * round(sr * a.duration)
rng = random.Random(7)
for t in a.times:
    start = round(t * sr)
    for i in range(min(round(sr * 0.03), len(buf) - start)):
        sample = round(rng.uniform(-1, 1) * math.exp(-i / (sr * 0.006)) * 16000)
        buf[start + i] = max(-32768, min(32767, buf[start + i] + sample))
if sys.byteorder != 'little':
    buf.byteswap()
a.out.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(a.out), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    w.writeframes(buf.tobytes())
print(a.out)
