# AI 生成的静图入库：按透明区域裁边、改英文名、缩到上限，写 public/cut/*.png 和 src/imgs.ts 宽高比表
# 用法：python3 prep_images.py 素材目录 工程目录 [--map 对照.csv] [--max 1920] [--pad 6] [--sheet 联系表.jpg]
# 对照.csv 两列：编号,英文名（如 01,poop_gold）。不给时按文件名前的编号命名为 i01、i28a。
# 需要 Pillow。
import argparse, csv, os, re, sys
from PIL import Image, ImageDraw

EXTS = ('.png', '.jpg', '.jpeg', '.webp')

def key_of(fname):
    m = re.match(r'^([0-9]+[a-z]?)[_\-\s]', fname, re.I)
    return m.group(1).lower() if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('project')
    ap.add_argument('--map', help='两列 CSV：编号,英文名')
    ap.add_argument('--max', type=int, default=1920, help='长边上限（像素）')
    ap.add_argument('--pad', type=int, default=6, help='裁边后保留的透明边（像素）')
    ap.add_argument('--sheet', help='把全部入库图片拼成联系表（中灰底，方便看白边和画风是否统一）')
    a = ap.parse_args()

    names = {}
    if a.map:
        with open(a.map, newline='', encoding='utf-8-sig') as fh:
            for row in csv.reader(fh):
                if len(row) >= 2 and row[0].strip() and not row[0].startswith('#'):
                    names[row[0].strip().lower()] = row[1].strip()
    for n in names.values():
        if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', n):
            sys.exit(f'英文名只能用字母、数字和下划线：{n}')

    files = sorted(f for f in os.listdir(a.src) if f.lower().endswith(EXTS) and not f.startswith('.'))
    if not files:
        sys.exit(f'{a.src} 里没有图片')
    out_dir = os.path.join(a.project, 'public', 'cut')
    os.makedirs(out_dir, exist_ok=True)
    seen, asp, warn, thumbs = {}, {}, [], []
    for f in files:
        k = key_of(f)
        if k is None:
            warn.append(f'跳过（文件名不以编号开头）：{f}')
            continue
        name = names.get(k, f'i{k}')
        if name in seen:
            sys.exit(f'编号重复：{seen[name]} 和 {f} 都会写成 {name}.png')
        seen[name] = f
        im = Image.open(os.path.join(a.src, f)).convert('RGBA')
        alpha = im.getchannel('A')
        lo, _ = alpha.getextrema()
        if lo == 255:
            warn.append(f'{f}：没有透明区域，按完整背景处理')
        else:
            bb = alpha.point(lambda v: 255 if v > 8 else 0).getbbox()
            if bb is None:
                sys.exit(f'{f}：整张都是透明的')
            if bb[0] == 0 or bb[1] == 0 or bb[2] == im.width or bb[3] == im.height:
                warn.append(f'{f}：主体贴到画布边缘，可能被裁掉了，检查原图')
            p = a.pad
            im = im.crop((max(0, bb[0] - p), max(0, bb[1] - p), min(im.width, bb[2] + p), min(im.height, bb[3] + p)))
        if max(im.size) > a.max:
            s = a.max / max(im.size)
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        im.save(os.path.join(out_dir, name + '.png'))
        asp[name] = im.width / im.height
        if a.sheet:
            th = im.copy()
            th.thumbnail((300, 260))
            thumbs.append((name, th))
        print(f'{f} -> cut/{name}.png {im.width}x{im.height}')

    os.makedirs(os.path.join(a.project, 'src'), exist_ok=True)
    ts = os.path.join(a.project, 'src', 'imgs.ts')
    with open(ts, 'w', encoding='utf-8') as fh:
        fh.write('// 由 prep_images.py 生成：public/cut 里每张图的宽高比（宽/高），已按透明区域裁边\n')
        fh.write('export const ASPECT = {\n')
        for k, v in asp.items():
            fh.write(f'  {k}: {v:.4f},\n')
        fh.write('} as const;\nexport type ImgName = keyof typeof ASPECT;\n')
    print(f'写入 {ts}，共 {len(asp)} 张')
    if a.sheet and thumbs:
        cols = 6
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * 320, rows * 300), (128, 128, 128))
        draw = ImageDraw.Draw(sheet)
        for i, (name, th) in enumerate(thumbs):
            x, y = (i % cols) * 320, (i // cols) * 300
            sheet.paste(th, (x + (320 - th.width) // 2, y + 10 + (260 - th.height) // 2), th)
            draw.text((x + 8, y + 278), name, fill=(255, 255, 0))
        os.makedirs(os.path.dirname(os.path.abspath(a.sheet)), exist_ok=True)
        sheet.save(a.sheet, quality=88)
        print(f'联系表 {a.sheet}')
    for w in warn:
        print('注意：' + w, file=sys.stderr)

if __name__ == '__main__':
    main()
