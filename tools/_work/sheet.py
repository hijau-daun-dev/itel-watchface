import sys,json,os
from PIL import Image
d=sys.argv[1]; out=sys.argv[2]; extra=sys.argv[3] if len(sys.argv)>3 else None
lay=json.load(open(os.path.join(d,'layout.json')))
ims=[]
for e in lay['elements']:
    for r in e['images']:
        im=Image.open(os.path.join(d,r)).convert('RGBA'); ims.append(im)
W=1400; x=y=0; rowh=0; pos=[]
for im in ims:
    w,h=im.size
    if w>300: im=im.resize((w//2,h//2)); w,h=im.size
    if x+w>W: x=0; y+=rowh+6; rowh=0
    pos.append((im,x,y)); x+=w+6; rowh=max(rowh,h)
sheet=Image.new('RGBA',(W,y+rowh),(255,0,255,255))
# checker-ish magenta backdrop shows transparency
for im,x,y in pos: sheet.alpha_composite(im,(x,y))
if extra:
    ex=Image.open(extra).convert('RGBA'); s2=Image.new('RGBA',(W,sheet.height+ex.height+6),(40,40,40,255)); s2.paste(ex,(0,0)); s2.alpha_composite(sheet,(0,ex.height+6)); sheet=s2
sheet.convert('RGB').save(out)
