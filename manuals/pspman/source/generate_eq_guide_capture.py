#!/usr/bin/env python3
"""Generate the PSPMAN Alpha 6 Equalizer documentation capture."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "screenshots" / "eq-480x272.png"
FONT = ROOT / "assets" / "fonts" / "Inter-Regular.ttf"

img = Image.new("RGB", (480, 272), (0, 0, 0))
d = ImageDraw.Draw(img)
f13 = ImageFont.truetype(str(FONT), 13)
f12 = ImageFont.truetype(str(FONT), 12)
f11 = ImageFont.truetype(str(FONT), 11)
white=(232,232,232); gray=(82,82,82); green=(0,255,0)

d.text((15,9), "-", font=f13, fill=(150,150,150))
d.text((10,34), "PREAMP 0.", font=f13, fill=green)
d.text((395,9), "00:00 / --:--", font=f13, fill=white)
d.text((441,34), "OFF", font=f13, fill=white)

centers=[24,72,120,168,216,264,312,360,408,456]
ys=[62,73,84,95,106,117,128,139,150,161,172,183,194]
for cx in centers:
    for y in ys:
        d.line((cx-12,y,cx+12,y), fill=green if y==128 else gray, width=2 if y==128 else 1)

for i,(cx,label) in enumerate(zip(centers,["31","62","125","250","500","1K","2K","4K","8K","16K"])):
    color=green if i==0 else white
    for y,text in ((211,label),(232,"0.0")):
        box=d.textbbox((0,0),text,font=f12)
        d.text((cx-(box[2]-box[0])/2,y),text,font=f12,fill=color)

d.line((13,224,37,224),fill=white,width=1)
d.text((10,252),"Preset",font=f11,fill=white)
d.text((83,252),"Flat",font=f11,fill=white)
d.text((253,252),"SQUARE ON/OFF · TRIANGLE PRESET",font=f11,fill=white)

OUT.parent.mkdir(parents=True,exist_ok=True)
img.save(OUT,"PNG",optimize=False)
print(OUT)
