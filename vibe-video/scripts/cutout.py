# 用户给的图抠背景（rembg isnet-general-use），抠完的 PNG 再拿去逐像素取色做粒子或直接贴图
# 用法：python3 cutout.py 输出目录 图1.jpg 图2.png ...   （先 pip install rembg onnxruntime）
import os, sys
from rembg import remove, new_session
from PIL import Image
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
s = new_session("isnet-general-use")
for f in sys.argv[2:]:
    o = remove(Image.open(f).convert("RGB"), session=s)
    name = os.path.splitext(os.path.basename(f))[0] + ".png"
    o.save(os.path.join(out, name))
    print("ok", name)
