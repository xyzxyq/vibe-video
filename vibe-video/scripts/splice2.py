#!/usr/bin/env python3
"""用 seg_起帧-止帧.mp4 按帧覆盖原视频；参数顺序靠后的片段优先。"""
import argparse, json, re, subprocess
from fractions import Fraction
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('video', type=Path)
p.add_argument('out', type=Path)
p.add_argument('segments', nargs='+', type=Path)
a = p.parse_args()
def info(file):
    if not file.is_file() or file.resolve() == a.out.resolve():
        p.error('input is missing or equals output')
    data = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames,avg_frame_rate,width,height', '-of', 'json', str(file)]))
    if not data['streams']:
        p.error('input has no video stream')
    return data['streams'][0]
base = info(a.video)
n = int(base['nb_read_frames'])
layers = [(a.video, 0, n-1)]
for file in a.segments:
    match = re.fullmatch(r'seg_(\d+)-(\d+)', file.stem)
    if not match:
        p.error('segment filenames must be seg_start-end.mp4')
    start, end = map(int, match.groups())
    if not 0 <= start <= end < n:
        p.error('segment range must be within original video')
    meta = info(file)
    if int(meta['nb_read_frames']) != end-start+1 or any(meta[k] != base[k] for k in ('width', 'height')) or Fraction(meta['avg_frame_rate']) != Fraction(base['avg_frame_rate']):
        p.error('segment frame count, dimensions or FPS do not match')
    layers.append((file, start, end))
owner = [0] * n
for i, (_, start, end) in enumerate(layers):
    owner[start:end+1] = [i] * (end-start+1)
runs = []
for frame, layer in enumerate(owner):
    if runs and runs[-1][0] == layer:
        runs[-1][2] = frame
    else:
        runs.append([layer, frame, frame])
cmd = ['ffmpeg', '-n', '-v', 'error']
for file, _, _ in layers:
    cmd += ['-i', str(file)]
fc, labels = [], []
for i, (layer, start, end) in enumerate(runs):
    origin = layers[layer][1]
    fc.append(f'[{layer}:v]trim=start_frame={start-origin}:end_frame={end-origin+1},setpts=PTS-STARTPTS[v{i}]')
    labels.append(f'[v{i}]')
fc.append(''.join(labels) + f'concat=n={len(labels)}:v=1:a=0[v]')
a.out.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(cmd + ['-filter_complex', ';'.join(fc), '-map', '[v]', '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', base['avg_frame_rate'], str(a.out)], check=True)
print(a.out, '(silent; mix audio after splicing)')
