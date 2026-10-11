# usage: python3 sheet.py <dir> <cols> [out]  -> labelled contact sheet of every t*.jpg
import sys,glob,os
from PIL import Image,ImageDraw
d=sys.argv[1]; cols=int(sys.argv[2]); out=sys.argv[3] if len(sys.argv)>3 else d+'_sheet.jpg'
fs=sorted(glob.glob(d+'/t*.jpg'),key=lambda f: float(os.path.basename(f)[1:-4]))
W,H=640,360
rows=(len(fs)+cols-1)//cols
S=Image.new('RGB',(cols*W,rows*H),'black')
for k,f in enumerate(fs):
    im=Image.open(f).resize((W,H))
    ImageDraw.Draw(im).text((6,4),os.path.basename(f)[1:-4],fill=(255,255,0))
    S.paste(im,((k%cols)*W,(k//cols)*H))
S.save(out,quality=85); print(out,len(fs))
