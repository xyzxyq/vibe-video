import base64
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'vibe-video/scripts/deliver_assets.py'
spec = importlib.util.spec_from_file_location('delivery', SCRIPT)
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l9sAAAAASUVORK5CYII=')


class DeliveryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / '01_主角.png'
        self.source.write_bytes(PNG)
        self.manifest = self.root / '素材任务.json'
        self.output = self.root / '上传素材包'
        self.data = {'project': '测试短片', 'review': {'status': 'pending', 'note': ''}, 'assets': [
            {'id': '01', 'name': '主角', 'kind': 'image', 'method': 'builtin-image',
             'qa': 'passed', 'decision': 'accepted', 'notes': '',
             'files': [{'path': self.source.name, 'sha256': hashlib.sha256(PNG).hexdigest()}]},
            {'id': '动01', 'name': '未采用动作', 'kind': 'motion', 'qa': 'failed',
             'decision': 'excluded', 'notes': '用户弃用：方向错误', 'files': []}]}

    def approve(self):
        self.data['review'] = {'status': 'approved', 'note': '测试夹具：接受01，弃用动01',
                               'selection_sha256': delivery.selection_digest(self.data)}

    def run_cli(self, command='pack', output=None, ok=True):
        self.manifest.write_text(json.dumps(self.data, ensure_ascii=False), encoding='utf-8')
        result = subprocess.run([sys.executable, str(SCRIPT), command, str(self.manifest),
                                 str(output or self.output)], capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def test_pack_accepted_only_and_never_overwrite(self):
        (self.root / '._01_主角.png').write_bytes(b'macOS sidecar')
        (self.root / '旧版.png').write_bytes(b'old version')
        self.approve()
        result = json.loads(self.run_cli().stdout)
        self.assertEqual(result['file_count'], 1)
        self.assertEqual(result['accepted_assets']['motion'], 0)
        self.assertEqual((self.output / '图片组件' / self.source.name).read_bytes(), PNG)
        self.assertEqual(self.source.read_bytes(), PNG)
        self.assertEqual(len(list(p for p in self.output.rglob('*') if p.is_file())), 4)
        report = json.loads((self.output / '打包校验.json').read_text())
        self.assertEqual(report['excluded'][0]['id'], '动01')
        with (self.output / '素材清单.csv').open(encoding='utf-8-sig', newline='') as stream:
            self.assertEqual(next(csv.DictReader(stream))['sha256'], hashlib.sha256(PNG).hexdigest())
        self.run_cli(ok=False)
        self.assertEqual((self.output / '图片组件' / self.source.name).read_bytes(), PNG)

    def test_user_approval_required(self):
        self.run_cli(ok=False)
        self.assertFalse(self.output.exists())
        self.approve()
        self.data['review']['note'] = None
        self.run_cli(ok=False)

    def test_pending_decision_or_failed_qa_blocks_pack(self):
        for field, value in [('decision', 'pending'), ('qa', 'failed')]:
            with self.subTest(field=field):
                self.data['assets'][0].update(decision='accepted', qa='passed')
                self.data['assets'][0][field] = value
                self.approve()
                self.run_cli(ok=False)
                self.assertFalse(self.output.exists())

    def test_changed_file_requires_new_review(self):
        self.approve()
        self.source.write_bytes(PNG + b'changed')
        self.run_cli(ok=False)
        self.assertFalse(self.output.exists())

    def test_changed_selection_invalidates_approval(self):
        self.approve()
        self.data['assets'][0]['notes'] = '改变验收版本的限制说明'
        self.run_cli(ok=False)
        self.assertFalse(self.output.exists())

    def test_unsafe_paths_rejected(self):
        (self.root / 'link.png').symlink_to(self.source)
        (self.root / '.hidden.png').write_bytes(PNG)
        for value in ['../outside.png', str(self.source), 'link.png', '.hidden.png', 'x\\01.png']:
            with self.subTest(value=value):
                self.data['assets'][0]['files'][0]['path'] = value
                self.approve()
                self.run_cli(ok=False)
                self.assertFalse(self.output.exists())

    def test_missing_file_or_hash_rejected(self):
        self.data['assets'][0]['files'][0]['path'] = 'missing.png'
        self.approve()
        self.run_cli(ok=False)
        self.data['assets'][0]['files'][0] = {'path': self.source.name, 'sha256': ''}
        self.approve()
        self.run_cli(ok=False)
        self.assertFalse(self.output.exists())

    def test_duplicate_delivery_names_rejected(self):
        (self.root / 'other').mkdir()
        (self.root / 'other' / self.source.name).write_bytes(PNG)
        second = dict(self.data['assets'][0], id='02', files=[{
            'path': 'other/' + self.source.name, 'sha256': hashlib.sha256(PNG).hexdigest()}])
        self.data['assets'].append(second)
        self.approve()
        self.run_cli(ok=False)
        self.assertFalse(self.output.exists())

    def test_preview_escapes_text_and_does_not_approve(self):
        self.data['project'] = '<script>alert(1)</script>'
        self.data['assets'][0]['decision'] = 'pending'
        output = self.root / '素材总览.html'
        result = json.loads(self.run_cli('preview', output).stdout)
        page = output.read_text()
        self.assertIn('&lt;script&gt;', page)
        self.assertNotIn('<script>', page)
        self.assertIn('%E4%B8%BB%E8%A7%92.png', page)
        self.assertEqual(result['selection_sha256'], delivery.selection_digest(self.data))
        self.assertEqual(json.loads(self.manifest.read_text())['review']['status'], 'pending')
        self.run_cli('preview', output)
        output.write_text('a different document')
        self.run_cli('preview', output, ok=False)
        self.assertEqual(output.read_text(), 'a different document')

    def test_unresolved_exclusion_and_duplicate_ids_rejected(self):
        self.data['assets'][1]['notes'] = ''
        self.approve()
        self.run_cli(ok=False)
        self.data['assets'][1].update(notes='用户弃用', id='01')
        self.approve()
        self.run_cli(ok=False)
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    unittest.main()
