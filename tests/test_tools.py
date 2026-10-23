import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import wave
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
        pixels = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(spliced), '-vf', "select='eq(n,0)+eq(n,10)+eq(n,20)',scale=1:1", '-fps_mode', 'passthrough', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
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

    @unittest.skipUnless(importlib.util.find_spec('PIL'), 'Pillow required')
    def test_prep_images(self):
        from PIL import Image
        src = self.dir / 'in'
        src.mkdir()
        cut = Image.new('RGBA', (400, 200), (0, 0, 0, 0))
        cut.paste((200, 120, 40, 255), (100, 50, 300, 150))
        cut.save(src / '01_展品.png')
        Image.new('RGB', (320, 180), (90, 90, 120)).save(src / '06_背景.png')
        edge = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
        edge.paste((10, 200, 10, 255), (0, 20, 60, 80))
        edge.save(src / '28a_杆菌.png')
        (src / '说明.txt').write_text('not an image')
        (self.dir / 'map.csv').write_text('01,poop_gold\n', encoding='utf-8')
        (self.dir / 'src').mkdir()
        r = self.run_script('prep_images.py', src, self.dir, '--map', self.dir / 'map.csv', '--pad', 4, '--sheet', self.dir / 'sheet.jpg')
        for path, size in [('sheet.jpg', (1920, 300)), ('public/cut/poop_gold.png', (208, 108)), ('public/cut/i06.png', (320, 180))]:
            with Image.open(self.dir / path) as image:
                self.assertEqual(image.size, size)
        self.assertTrue((self.dir / 'public/cut/i28a.png').exists())
        ts = (self.dir / 'src/imgs.ts').read_text(encoding='utf-8')
        self.assertIn('poop_gold: 1.9259', ts)
        self.assertIn('i06: 1.7778', ts)
        self.assertIn('export type ImgName', ts)
        self.assertIn('06_背景.png', r.stderr)
        self.assertIn('28a_杆菌.png', r.stderr)
        Image.new('RGB', (10, 10)).save(src / '01_重复.png')
        self.run_script('prep_images.py', src, self.dir, ok=False)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe') and importlib.util.find_spec('cv2') and importlib.util.find_spec('numpy') and importlib.util.find_spec('PIL'), 'FFmpeg, opencv-python-headless, numpy and Pillow required')
    def test_prep_clip(self):
        import numpy as np
        from PIL import Image
        (self.dir / 'src').mkdir()
        green = self.dir / 'green.mp4'
        # a red square bobbing on pure green, 24 fps, 1 second; its last frame repeats the first so the loop closes
        subprocess.run(['ffmpeg', '-n', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=0x00FF00:s=160x120:r=24:d=1', '-f', 'lavfi', '-i', 'color=c=red:s=40x40:r=24:d=1',
                        '-filter_complex', "[0][1]overlay=60:40+10*sin(2*PI*t*24/23)", '-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-qp', '0', str(green)], check=True)
        r = self.run_script('prep_clip.py', green, 'box', self.dir, '--green', '--cell-h', 60)
        info = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(info['frames'], 24)
        self.assertLess(info['loop_rms'], 0.03)
        meta = json.loads((self.dir / 'src/clips.json').read_text())['box']
        self.assertEqual((meta['n'], meta['fps'], meta['files']), (24, 24.0, ['box_0.png']))
        sheet = np.array(Image.open(self.dir / 'public/anim/box_0.png'))
        cw = round(meta['aspect'] * 60)
        self.assertEqual(sheet.shape[:2], (60 * meta['rows'][0], cw * meta['cols']))
        cell = sheet[:60, :cw]
        self.assertEqual(cell[0, 0, 3], 0)
        self.assertGreater(cell[30, cw // 2, 3], 200)
        self.assertGreater(int(cell[30, cw // 2, 0]), int(cell[30, cw // 2, 1]) + 100)
        # a non-alpha source without --green is refused, and so is a bad name
        self.run_script('prep_clip.py', green, 'box2', self.dir, ok=False)
        self.run_script('prep_clip.py', green, 'bad-name', self.dir, '--green', ok=False)
        if 'libvpx-vp9' in subprocess.run(['ffmpeg', '-v', 'error', '-encoders'], capture_output=True, text=True).stdout:
            frames = self.dir / 'frames'
            frames.mkdir()
            for i in range(12):
                im = Image.new('RGBA', (80, 80), (0, 0, 0, 0))
                im.paste((40, 90, 220, 255), (20, 20 + i % 3, 60, 60 + i % 3))
                im.save(frames / f'{i:03d}.png')
            webm = self.dir / 'alpha.webm'
            subprocess.run(['ffmpeg', '-n', '-v', 'error', '-framerate', '12', '-i', str(frames / '%03d.png'), '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-auto-alt-ref', '0', str(webm)], check=True)
            r = self.run_script('prep_clip.py', webm, 'blue', self.dir, '--cell-h', 40)
            meta = json.loads((self.dir / 'src/clips.json').read_text())
            self.assertEqual(set(meta), {'box', 'blue'})
            self.assertEqual((meta['blue']['n'], meta['blue']['fps']), (12, 12.0))
            cell = np.array(Image.open(self.dir / 'public/anim/blue_0.png'))
            self.assertEqual(cell[0, 0, 3], 0)

if __name__ == '__main__':
    unittest.main()
