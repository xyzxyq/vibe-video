"""Build a local review page or an approved, uncompressed asset delivery folder."""
import argparse
import csv
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import unicodedata
from urllib.parse import quote


KINDS = {
    'image': ('图片组件', {'.png', '.jpg', '.jpeg', '.webp'}),
    'motion': ('动图组件', {'.webm', '.mov', '.mp4', '.gif', '.apng'}),
    'cover': ('封面', {'.png', '.jpg', '.jpeg', '.webp'}),
    'document': ('说明附件', {'.md', '.txt', '.csv', '.json'}),
}
DECISIONS = {'pending', 'accepted', 'excluded', 'deferred'}
MARKER = '<!-- vibe-video asset preview -->'


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def local_file(root, value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise ValueError(f'需要项目内相对路径：{value!r}')
    rel = Path(value)
    if rel.is_absolute() or any(p.startswith('.') for p in value.split('/')):
        raise ValueError(f'拒绝隐藏文件或越界路径：{value}')
    path = root
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f'拒绝符号链接：{value}')
    if not path.is_file():
        raise ValueError(f'文件不存在：{value}')
    return path


def load_manifest(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or not isinstance(data.get('project'), str) or not data['project'].strip():
        raise ValueError('清单需要非空 project 名称')
    if not isinstance(data.get('assets'), list) or not data['assets']:
        raise ValueError('清单需要非空 assets 列表')
    ids = set()
    for asset in data['assets']:
        if not isinstance(asset, dict) or not isinstance(asset.get('id'), str) or not asset['id'].strip():
            raise ValueError('每项需要非空字符串 id')
        if asset['id'] in ids:
            raise ValueError(f'重复编号：{asset["id"]}')
        ids.add(asset['id'])
        if asset.get('kind') not in KINDS or asset.get('decision') not in DECISIONS:
            raise ValueError(f'{asset["id"]} 的 kind / decision 无效')
        if not isinstance(asset.get('files'), list):
            raise ValueError(f'{asset["id"]} 需要 files 列表，未生成时用 []')
        for key in ('name', 'method', 'notes'):
            if not isinstance(asset.get(key, ''), str):
                raise ValueError(f'{asset["id"]}.{key} 必须是字符串')
    return data


def selection_digest(data):
    snapshot = {'project': data['project'], 'assets': data['assets']}
    return hashlib.sha256(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def checked_files(root, asset):
    result = []
    for item in asset['files']:
        if not isinstance(item, dict) or not re.fullmatch('[0-9a-f]{64}', str(item.get('sha256', ''))):
            raise ValueError(f'{asset["id"]} 缺少有效 SHA-256')
        path = local_file(root, item.get('path'))
        if path.suffix.lower() not in KINDS[asset['kind']][1]:
            raise ValueError(f'{asset["id"]} 不支持此交付格式：{path.name}')
        if digest(path) != item['sha256']:
            raise ValueError(f'文件已变更，需重新检查和验收：{item["path"]}')
        result.append((item, path))
    return result


def preview(data, root, output):
    if output.suffix.lower() != '.html' or not output.resolve().is_relative_to(root):
        raise ValueError('预览必须是项目目录内的 .html 文件')
    if output.is_symlink() or (output.exists() and not output.read_text(encoding='utf-8').startswith(MARKER)):
        raise ValueError('拒绝覆盖非本工具生成的预览文件')
    cards = []
    esc = lambda value: html.escape(str(value), quote=True)
    for asset in data['assets']:
        files = checked_files(root, asset)
        display = files[0][1] if files else None
        if asset.get('preview'):
            display = local_file(root, asset['preview'])
            if display.suffix.lower() not in {'.mp4', '.webm', '.mov', '.gif', '.apng'}:
                raise ValueError('preview 必须为项目内视频或动态图')
        def url(path):
            return esc(quote(os.path.relpath(path, output.parent).replace(os.sep, '/'), safe='/'))
        media = '<p>尚无文件</p>'
        if display and display.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.apng'}:
            media = f'<img loading="lazy" src="{url(display)}" alt="{esc(asset.get("name", asset["id"]))}">'
        elif display and display.suffix.lower() in {'.mp4', '.webm', '.mov'}:
            loop = ' loop' if asset.get('loop') is True else ''
            media = f'<video controls muted playsinline preload="metadata"{loop} src="{url(display)}">请下载原文件查看</video>'
        elif display:
            media = '<p>说明附件，见下载链接。</p>'
        links = ' · '.join(f'<a href="{url(p)}" download>{esc(p.name)}</a>' for _, p in files)
        cards.append(f'<article><h2>{esc(asset["id"])} · {esc(asset.get("name", ""))}</h2>'
                     f'<p>方式：{esc(asset.get("method", ""))} · 技术：{esc(asset.get("qa", "pending"))} · 用户：{esc(asset["decision"])}</p>'
                     f'<div class="media">{media}</div><p>{esc(asset.get("notes", ""))}</p><p>{links}</p>'
                     + ('<p>当前播放为预览，交付以下载链接为准。</p>' if asset.get('preview') else '') + '</article>')
    page = MARKER + '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    page += f'<title>{esc(data["project"])} · 素材验收</title>'
    page += '''<style>body{font:16px/1.6 system-ui;margin:24px;background:#f3f4f6;color:#172230}button{font:inherit;padding:8px 16px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(360px,100%),1fr));gap:20px}article{border:1px solid #98a1ac;border-radius:12px;padding:16px;overflow-wrap:anywhere}h2{font-size:20px}.media{background:repeating-conic-gradient(#bbb 0% 25%,#eee 0% 50%) 0/24px 24px;border-radius:8px}img,video{display:block;max-width:100%;height:280px;object-fit:contain;margin:auto}body.dark{background:#18202b;color:#eef3fa}body.dark .media{background:#333}a{color:#145fbb}body.dark a{color:#a5ceff}</style>'''
    page += f'<h1>{esc(data["project"])} · 素材验收</h1><p>查看文件并按编号回复接受、弃用或暂缓；此页面不会自动批准。</p>'
    page += '<button type="button" aria-pressed="false" onclick="document.body.classList.toggle(\'dark\');this.setAttribute(\'aria-pressed\',document.body.classList.contains(\'dark\'))">切换深浅背景</button><main>'
    page += ''.join(cards) + '</main></html>'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding='utf-8')
    return {'preview': str(output), 'assets': len(data['assets']), 'selection_sha256': selection_digest(data)}


def pack(data, root, output):
    review = data.get('review', {})
    if not isinstance(review, dict) or review.get('status') != 'approved' or not isinstance(review.get('note'), str) or not review['note'].strip():
        raise ValueError('需要用户对当前版本的明确验收记录')
    if review.get('selection_sha256') != selection_digest(data):
        raise ValueError('清单快照与验收版本不同，需重新核对用户决定')
    planned, excluded, targets = [], [], set()
    for asset in data['assets']:
        decision = asset['decision']
        if decision == 'pending':
            raise ValueError(f'{asset["id"]} 仍待用户决定')
        if decision != 'accepted':
            if not asset.get('notes', '').strip():
                raise ValueError(f'{asset["id"]} 需要弃用或暂缓理由')
            excluded.append({'id': asset['id'], 'decision': decision, 'notes': asset['notes']})
            continue
        if asset.get('qa') != 'passed' or not asset['files'] or not asset.get('method', '').strip():
            raise ValueError(f'{asset["id"]} 缺少技术检查、文件或制作方式')
        for item, source in checked_files(root, asset):
            target = Path(KINDS[asset['kind']][0]) / source.name
            key = unicodedata.normalize('NFC', str(target)).casefold()
            if key in targets:
                raise ValueError(f'重复交付文件名：{target}')
            targets.add(key)
            planned.append((asset, item, source, target))
    if not planned:
        raise ValueError('没有已接受的文件可打包')
    # mkdir is exclusive; an existing delivery folder is never merged or overwritten.
    output.mkdir(parents=False, exist_ok=False)
    rows = []
    try:
        for asset, item, source, rel in planned:
            target = output / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst)
            if digest(target) != item['sha256']:
                raise ValueError(f'复制内容与验收版本不符：{rel}')
            rows.append({'id': asset['id'], 'name': asset.get('name', ''), 'kind': asset['kind'],
                         'method': asset['method'], 'file': rel.as_posix(), 'sha256': item['sha256'],
                         'bytes': target.stat().st_size, 'native_size': asset.get('native_size'),
                         'delivered_size': asset.get('delivered_size'), 'notes': asset.get('notes', '')})
        with (output / '素材清单.csv').open('x', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            for row in rows:
                writer.writerow({k: "'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@', '\t', '\r')) else v for k, v in row.items()})
        counts = {kind: len({r['id'] for r in rows if r['kind'] == kind}) for kind in KINDS}
        report = {'status': 'PASS', 'project': data['project'], 'accepted_assets': counts,
                  'file_count': len(rows), 'bytes': sum(r['bytes'] for r in rows),
                  'selection_sha256': review['selection_sha256'], 'files': rows, 'excluded': excluded}
        note = f'# {data["project"]} · 上传素材包\n\n普通文件夹，未压缩。共 {len(rows)} 个交付文件；编号数：{counts}。\n\n'
        note += '同一动图的 WebM/MOV 是格式副本；网页可用 WebM，剪辑按目标软件支持选择 MOV。GIF 仅供预览。\n\n'
        note += '只收录用户已接受且通过记录中技术检查的版本，复制前后逐项核对 SHA-256。目录整理不代表已上传或已验证目标软件兼容性。\n\n'
        note += '制作方式、原生/交付尺寸及限制见素材清单；本地二维动画不代表模型图生视频。\n\n'
        note += '## 未纳入\n\n' + ('\n'.join(f'- {a["id"]}（{a["decision"]}）：{a["notes"]}' for a in excluded) or '无。') + '\n'
        (output / '使用说明.md').write_text(note, encoding='utf-8')
        (output / '打包校验.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except Exception:
        (output / '打包未完成.txt').write_text('本目录未完成校验，不是正式交付；请检查错误并使用新目录重试。\n', encoding='utf-8')
        raise
    return {'folder': str(output), 'status': 'PASS', 'file_count': len(rows), 'accepted_assets': counts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['preview', 'pack'])
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        manifest = args.manifest.resolve()
        data = load_manifest(manifest)
        result = (preview if args.command == 'preview' else pack)(data, manifest.parent, args.output.absolute())
    except (OSError, ValueError, TypeError) as error:
        parser.exit(1, f'错误：{error}\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
