#!/usr/bin/env python3
"""为视频混入默认 BGM 和可选音效时间表，不依赖预先存在的笑声文件。"""
import argparse, json, math, subprocess
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('video', type=Path)
p.add_argument('out', type=Path)
p.add_argument('--bgm', type=Path, default=Path('public/bgm.mp3'))
p.add_argument('--effects', type=Path, help='JSON 数组：每项包含 file、start 和可选 volume')
a = p.parse_args()
events = json.loads(a.effects.read_text()) if a.effects else []
if not isinstance(events, list):
    p.error('effects must be a JSON array')
if not a.video.is_file() or not a.bgm.is_file():
    p.error('video or BGM file does not exist; run in the copied project or specify --bgm')
if a.video.resolve() == a.out.resolve() or a.bgm.resolve() == a.out.resolve():
    p.error('output must differ from inputs')
duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(a.video)]))
if not math.isfinite(duration) or duration <= 0:
    p.error('video duration must be positive')
fade = min(3.5, duration)
fc = [f'[1:a]apad,atrim=0:{duration},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.3,afade=t=out:st={duration-fade}:d={fade},aresample=48000[bgm]']
cmd = ['ffmpeg', '-n', '-v', 'error', '-i', str(a.video), '-i', str(a.bgm)]
labels = ['[bgm]']
for i, e in enumerate(events):
    if not isinstance(e, dict) or not isinstance(e.get('file'), str):
        p.error('each effect needs a file string')
    start, volume = e.get('start'), e.get('volume', 0.25)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in (start, volume)) or not 0 <= start < duration or volume < 0:
        p.error('effect start must be within video duration and volume must be nonnegative')
    if not Path(e['file']).is_file() or Path(e['file']).resolve() == a.out.resolve():
        p.error('effect file is missing or equals output')
    cmd += ['-i', e['file']]
    fc.append(f'[{i+2}:a]aresample=48000,asetpts=PTS-STARTPTS,volume={volume},adelay={round(start*1000)}:all=1[e{i}]')
    labels.append(f'[e{i}]')
fc.append(''.join(labels) + f'amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.95:latency=1,atrim=0:{duration}[a]')
a.out.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(cmd + ['-filter_complex', ';'.join(fc), '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-movflags', '+faststart', str(a.out)], check=True)
print(a.out)
