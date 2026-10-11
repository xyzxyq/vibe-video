# synthesise the geiger clicks from the same level curve and per-frame dice as the on-screen trace (src/hud.tsx)
# 第 8 支的样板：从 src/hud.tsx 里读 KEYS 曲线和 FINAL_CLICK，用和画面同一个 hash 生成咔哒，保证声画同源。换片改读取的常量名和 FORCED 时间点。
import re, math, wave, struct, random
src = open('src/hud.tsx').read()
keys = [(float(a), float(b)) for a, b in re.findall(r'\[([\d.]+), ([\d.]+)\]', src.split('const KEYS')[1].split('];')[0])]
FINAL = float(re.search(r'FINAL_CLICK = ([\d.]+)', src).group(1))
FORCED = [3.2, 3.55, 4.25, FINAL]
def easeIO(x):
    v = min(1, max(0, x))
    return 4 * v ** 3 if v < 0.5 else 1 - (-2 * v + 2) ** 3 / 2
def level(t):
    if t <= keys[0][0]: return 0
    for (a, va), (b, vb) in zip(keys, keys[1:]):
        if t <= b: return va + (vb - va) * easeIO((t - a) / (b - a))
    return 0
def h(n):
    s = math.sin(n * 127.1 + 311.7) * 43758.5453
    return s - math.floor(s)
SR = 44100; N = SR * 175
buf = [0.0] * N
rnd = random.Random(7)
def click(t0, amp, big=False):
    i0 = int(t0 * SR)
    L = int(SR * (0.03 if big else 0.006))
    prev = 0
    for i in range(L):
        if i0 + i >= N: break
        env = math.exp(-i / (SR * (0.006 if big else 0.0012)))
        x = rnd.uniform(-1, 1)
        y = x - prev * 0.6  # a little brighter than white noise
        prev = x
        buf[i0 + i] += amp * env * y
for bf in range(175 * 30):
    bt = bf / 30
    lv = level(bt)
    forced = any(abs(bt - f) < 0.02 for f in FORCED)
    if forced or (lv > 0.01 and h(bf * 1.37) < 0.02 + lv * 0.55):
        amp = 1 if forced else 0.35 + 0.65 * h(bf * 2.11)
        click(bt + h(bf * 5.3) / 30, 0.32 * amp, big=abs(bt - FINAL) < 0.02)
peak = max(abs(v) for v in buf) or 1
with wave.open('public/clicks.wav', 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b''.join(struct.pack('<h', int(max(-1, min(1, v / peak * 0.5)) * 32767)) for v in buf))
print('clicks ok', len(keys), 'keys')
