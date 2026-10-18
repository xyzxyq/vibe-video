# AI 动图入库：解码透明 WebM/MOV（或抠纯绿幕 MP4），补透明小洞、柔化边缘、可按静图调色，
# 裁到所有帧的并集范围后打包成帧图集 public/anim/名称_N.png，并把元数据合并进 src/clips.json
# 用法：python3 prep_clip.py 动图文件 名称 工程目录 [--cell-h 600] [--match 静图.png] [--green] [--hole 900]
# 需要系统 FFmpeg/ffprobe、numpy、opencv-python-headless、Pillow。
import argparse, glob, json, os, re, subprocess, sys, tempfile
import numpy as np
import cv2
from PIL import Image

MAX_SHEET = 4096

def probe_fps(src):
    if not os.path.isfile(src):
        sys.exit(f'找不到文件：{src}')
    try:
        out = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=codec_name,avg_frame_rate,r_frame_rate', '-of', 'json', src], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        sys.exit(f'读不出视频：{src}')
    streams = json.loads(out).get('streams') or []
    if not streams:
        sys.exit(f'没有视频流：{src}')
    s = streams[0]
    num, den = (s.get('avg_frame_rate') or s['r_frame_rate']).split('/')
    if float(den) == 0 or float(num) == 0:
        num, den = s['r_frame_rate'].split('/')
    return s['codec_name'], float(num) / float(den)

def decode(src, codec, tmp):
    cmd = ['ffmpeg', '-v', 'error']
    # FFmpeg 自带的 vp8/vp9 解码器会丢掉 alpha，必须用 libvpx
    if codec == 'vp9':
        cmd += ['-c:v', 'libvpx-vp9']
    elif codec == 'vp8':
        cmd += ['-c:v', 'libvpx']
    cmd += ['-i', src, '-pix_fmt', 'rgba', os.path.join(tmp, '%05d.png')]
    subprocess.run(cmd, check=True)
    return [np.array(Image.open(f).convert('RGBA')) for f in sorted(glob.glob(os.path.join(tmp, '*.png')))]

def key_green(f):
    rgb = f[..., :3].astype(np.float32) / 255
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    d = g - np.maximum(r, b)
    a = np.clip(1 - (d - 0.06) / 0.22, 0, 1)
    g2 = np.minimum(g, np.maximum(r, b) + 0.02)  # 去绿溢色
    rgb = np.dstack([r, g2, b])
    return np.dstack([(rgb * 255).round(), (a * 255).round()]).astype(np.uint8)

def fill_holes(rgb, a, max_area):
    solid = (a > 128).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(1 - solid, connectivity=4)
    h, w = a.shape
    bad = np.zeros_like(solid)
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        touches = x == 0 or y == 0 or x + bw == w or y + bh == h
        if not touches and area < max_area:
            bad[lab == i] = 1
    if bad.any():
        bad = cv2.dilate(bad, np.ones((3, 3), np.uint8))
        rgb = cv2.inpaint(np.ascontiguousarray(rgb), bad, 4, cv2.INPAINT_TELEA)
        a = np.where(bad > 0, 255, a).astype(np.uint8)
    return rgb, a, int(bad.sum())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('name')
    ap.add_argument('project')
    ap.add_argument('--cell-h', type=int, default=600, help='图集里每帧的高度（像素）')
    ap.add_argument('--match', help='对应静图：按它的色相和饱和度校正动图偏色')
    ap.add_argument('--green', action='store_true', help='源文件是纯绿幕（#00FF00）视频，先抠像')
    ap.add_argument('--hole', type=int, default=900, help='小于此面积（像素）的内部透明洞会被补上')
    a = ap.parse_args()
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', a.name):
        sys.exit('名称只能用字母、数字和下划线')

    codec, fps = probe_fps(a.src)
    with tempfile.TemporaryDirectory() as tmp:
        frames = decode(a.src, codec, tmp)
    if not frames:
        sys.exit('没有解出帧')
    if a.green:
        frames = [key_green(f) for f in frames]
    elif all(f[..., 3].min() == 255 for f in frames[:3]):
        sys.exit('前几帧完全不透明：源文件没有 alpha。绿幕素材请加 --green')

    H, W = frames[0].shape[:2]
    union = np.zeros((H, W), bool)
    for f in frames:
        union |= f[..., 3] > 10
    if not union.any():
        sys.exit('所有帧都是透明的')
    ys, xs = np.where(union)
    pad = 8
    x0, x1 = max(0, xs.min() - pad), min(W, xs.max() + 1 + pad)
    y0, y1 = max(0, ys.min() - pad), min(H, ys.max() + 1 + pad)

    tgt = None
    if a.match:
        m = np.array(Image.open(a.match).convert('RGBA'))
        sel = m[..., 3] > 200
        tgt = np.median(cv2.cvtColor(np.ascontiguousarray(m[..., :3]), cv2.COLOR_RGB2HSV)[sel], axis=0)

    fixed, out = 0, []
    for f in frames:
        rgb, al = f[..., :3].copy(), f[..., 3].copy()
        rgb, al, k = fill_holes(rgb, al, a.hole)
        fixed += k
        al = cv2.GaussianBlur(al, (3, 3), 0.7)  # 柔化锯齿边
        if tgt is not None and (al > 200).any():
            hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
            cur = np.median(hsv[al > 200], axis=0)
            hsv[..., 0] = (hsv[..., 0] + (tgt[0] - cur[0])) % 180
            hsv[..., 1] = np.clip(hsv[..., 1] * (tgt[1] / max(cur[1], 1)), 0, 255)
            rgb = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        out.append(np.dstack([rgb, al])[y0:y1, x0:x1])

    ch = min(a.cell_h, MAX_SHEET)
    cw = max(1, round((x1 - x0) / (y1 - y0) * ch))
    if cw > MAX_SHEET:
        sys.exit('单帧太宽，调小 --cell-h')
    n = len(out)
    cols = max(1, min(n, MAX_SHEET // cw))
    per = cols * max(1, MAX_SHEET // ch)
    anim = os.path.join(a.project, 'public', 'anim')
    os.makedirs(anim, exist_ok=True)
    for old in glob.glob(os.path.join(anim, f'{a.name}_*.png')):
        if re.fullmatch(re.escape(a.name) + r'_\d+\.png', os.path.basename(old)):
            os.remove(old)
    files, rows = [], []
    for s in range(0, n, per):
        chunk = out[s:s + per]
        r = (len(chunk) + cols - 1) // cols
        sheet = Image.new('RGBA', (cols * cw, r * ch), (0, 0, 0, 0))
        for i, im in enumerate(chunk):
            sheet.paste(Image.fromarray(im).resize((cw, ch), Image.LANCZOS), ((i % cols) * cw, (i // cols) * ch))
        fn = f'{a.name}_{len(files)}.png'
        sheet.save(os.path.join(anim, fn))
        files.append(fn)
        rows.append(r)

    # 首尾帧差异：大于约 3% 说明不能无缝循环
    def small(im):
        return np.asarray(Image.fromarray(im).resize((64, max(1, round(64 * ch / cw)))), np.float32) / 255
    loop_err = float(np.sqrt(np.mean((small(out[0]) - small(out[-1])) ** 2)))

    meta_path = os.path.join(a.project, 'src', 'clips.json')
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, encoding='utf-8') as fh:
            meta = json.load(fh)
    meta[a.name] = {'n': n, 'fps': round(fps, 3), 'cols': cols, 'per': per, 'aspect': round(cw / ch, 4), 'files': files, 'rows': rows}
    with open(meta_path, 'w', encoding='utf-8') as fh:
        json.dump(dict(sorted(meta.items())), fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    print(json.dumps({'name': a.name, 'frames': n, 'fps': round(fps, 3), 'cell': [cw, ch], 'atlases': files, 'filled_px': fixed, 'loop_rms': round(loop_err, 4)}, ensure_ascii=False))
    if loop_err > 0.03:
        print(f'注意：首尾帧差异 {loop_err:.3f}，循环会跳；改成单次播放或在代码里交叉淡化', file=sys.stderr)

if __name__ == '__main__':
    main()
