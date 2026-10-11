import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'vibe-video' / 'scripts'

class ToolsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def run_script(self, name, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPTS / name), *map(str, args)], cwd=self.dir, capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_install_archive_matches_skill(self):
        root = SCRIPTS.parents[1]
        skill = root / 'vibe-video'
        expected = {str(p.relative_to(root)): p.read_bytes() for p in skill.rglob('*') if p.is_file() and not p.name.startswith('._') and '__pycache__' not in p.parts}
        with zipfile.ZipFile(root / 'skill.zip') as archive:
            actual = {i.filename: archive.read(i) for i in archive.infolist() if not i.is_dir()}
            self.assertEqual(actual.keys(), expected.keys())
            self.assertTrue(all(actual[name] == data for name, data in expected.items()))
            self.assertTrue((archive.getinfo('vibe-video/assets/starter/render.sh').external_attr >> 16) & 0o111)

    def test_click_timing_and_invalid_input(self):
        out = self.dir / 'clicks.wav'
        self.run_script('gen_clicks.py', out, 0.1, '--duration', 0.5)
        with wave.open(str(out)) as w:
            self.assertEqual(w.getnframes(), 22050)
            self.assertEqual(w.getframerate(), 44100)
            data = w.readframes(w.getnframes())
        self.assertEqual(data[:int(0.1*44100)*2], bytes(int(0.1*44100)*2))
        self.assertNotEqual(data[int(0.1*44100)*2:int(0.13*44100)*2], bytes(int(0.03*44100)*2))
        self.assertEqual(data[int(0.13*44100)*2:], bytes(len(data)-int(0.13*44100)*2))
        bad = self.dir / 'bad.wav'
        for value in ('-1', 'nan', '0.5'):
            self.run_script('gen_clicks.py', bad, value, '--duration', 0.5, ok=False)
            self.assertFalse(bad.exists())

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'system FFmpeg/ffprobe required')
    def test_mix_and_frame_splice(self):
        def video(name, color, duration):
            file = self.dir / name
            subprocess.run(['ffmpeg', '-n', '-v', 'error', '-f', 'lavfi', '-i', f'color=c={color}:s=64x64:r=30:d={duration}', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(file)], check=True)
            return file
        def probe(file):
            return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-show_entries', 'format=duration:stream=codec_type,nb_read_frames', '-of', 'json', str(file)]))
        base = video('base.mp4', 'red', 1)
        patch = video('seg_10-19.mp4', 'blue', 1/3)
        spliced = self.dir / 'spliced.mp4'
        self.run_script('splice2.py', base, spliced, patch)
        self.assertEqual(int(probe(spliced)['streams'][0]['nb_read_frames']), 30)
        pixels = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(spliced), '-vf', "select='eq(n,0)+eq(n,10)+eq(n,20)',scale=1:1", '-vsync', '0', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
        self.assertEqual(len(pixels), 9)
        self.assertGreater(pixels[0], pixels[2])
        self.assertGreater(pixels[5], pixels[3])
        self.assertGreater(pixels[6], pixels[8])
        bgm = self.dir / 'public' / 'bgm.mp3'
        self.run_script('gen_clicks.py', bgm, 0.1, '--duration', 0.5)
        # WAV bytes with a .mp3 name exercise FFmpeg's content-based probing.
        events = self.dir / 'effects.json'
        events.write_text(json.dumps([{'file': str(bgm), 'start': 0.2}]))
        bgm_only = self.dir / 'bgm-only.mp4'
        self.run_script('mix.py', spliced, bgm_only)
        self.assertEqual({s['codec_type'] for s in probe(bgm_only)['streams']}, {'video', 'audio'})
        mixed = self.dir / 'mixed.mp4'
        self.run_script('mix.py', spliced, mixed, '--effects', events)
        info = probe(mixed)
        self.assertEqual({s['codec_type'] for s in info['streams']}, {'video', 'audio'})
        self.assertAlmostEqual(float(info['format']['duration']), 1, delta=0.05)
        self.run_script('mix.py', mixed, mixed, ok=False)
        events.write_text('[{"file":"missing.wav","start":-1}]')
        self.run_script('mix.py', spliced, self.dir/'bad.mp4', '--effects', events, ok=False)
        self.assertFalse((self.dir/'bad.mp4').exists())
        wrong = video('seg_10-30.mp4', 'blue', 1/3)
        self.run_script('splice2.py', base, self.dir/'bad-splice.mp4', wrong, ok=False)
        self.assertFalse((self.dir/'bad-splice.mp4').exists())

if __name__ == '__main__':
    unittest.main()
