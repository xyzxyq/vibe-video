#!/usr/bin/env python3
# Build the final cut from film_v1 plus re-rendered segments; later layers override earlier ones.
# 用法：整片放 out/film_v1.mp4，重渲的段命名 seg_起帧-止帧.mp4 放进下面 d 列表的目录，跑完出 out/film_v3.mp4，再重新混音。路径按需改。
import subprocess, glob, re
N = 5250
layers = [('out/film_v1.mp4', 0, N - 1)]
for d in ['out', 'out/s2', 'out/s3']:
    for f in sorted(glob.glob(f'{d}/seg_*.mp4')):
        a, b = map(int, re.findall(r'seg_(\d+)-(\d+)', f)[0])
        layers.append((f, a, b))
owner = [0] * N
for li, (_, a, b) in enumerate(layers):
    for k in range(a, b + 1):
        owner[k] = li
runs = []
for k in range(N):
    if runs and runs[-1][0] == owner[k]:
        runs[-1][2] = k
    else:
        runs.append([owner[k], k, k])
inputs, fc, labels = [], [], []
for i, (li, a, b) in enumerate(runs):
    f, s0, _ = layers[li]
    if f not in inputs:
        inputs.append(f)
    ii = inputs.index(f)
    fc.append(f'[{ii}:v]trim=start_frame={a - s0}:end_frame={b - s0 + 1},setpts=PTS-STARTPTS[v{i}]')
    labels.append(f'[v{i}]')
    print(f, a, b)
fc.append(''.join(labels) + f'concat=n={len(labels)}:v=1:a=0[v]')
cmd = ['ffmpeg', '-y', '-v', 'error']
for f in inputs:
    cmd += ['-i', f]
cmd += ['-filter_complex', ';'.join(fc), '-map', '[v]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', 'out/film_v3.mp4']
subprocess.run(cmd, check=True)
