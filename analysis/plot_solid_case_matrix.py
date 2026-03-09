from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

cases = [
    {'label':'ratio50 120-step','kind':'solid-main','n_seeds':3,'delta_fg':0.0249,'delta_loss':0.0,'note':'strict multiseed boundary confirm'},
    {'label':'ratio50 150-step','kind':'solid-main','n_seeds':5,'delta_fg':0.0389,'delta_loss':0.37518,'note':'5-seed aggregate, all non-negative'},
    {'label':'task5 gap40','kind':'solid-discovery','n_seeds':3,'delta_fg':0.1461,'delta_loss':0.6455,'note':'3-seed confirm, all non-negative'},
    {'label':'task5 adjacent','kind':'strong-single','n_seeds':1,'delta_fg':0.1495,'delta_loss':0.7089,'note':'single-run strong positive'},
    {'label':'task5 gap24','kind':'strong-single','n_seeds':1,'delta_fg':0.1358,'delta_loss':0.6559,'note':'single-run strong positive'},
    {'label':'square migration coarse','kind':'promising-not-solid','n_seeds':1,'delta_fg':0.0633,'delta_loss':0.4270,'note':'coarse positive; confirm now passed'},
    {'label':'square migration confirm3','kind':'solid-discovery','n_seeds':3,'delta_fg':0.0891,'delta_loss':0.4154,'note':'3-seed confirm, all non-negative'},
]
COLORS = {
    'solid-main':'#0b6e4f',
    'solid-discovery':'#1f78b4',
    'strong-single':'#e07a00',
    'promising-not-solid':'#b23a48',
}
BG = '#f7f4ed'
GRID = '#d8d2c6'
TEXT = '#192126'
SUB = '#6a727a'

root = Path(__file__).resolve().parents[1]
out = root/'analysis'/'figures'/'solid_case_matrix.png'
out.parent.mkdir(parents=True, exist_ok=True)

W,H = 1300,650
img = Image.new('RGB',(W,H),BG)
d = ImageDraw.Draw(img)
font = ImageFont.load_default()
font_big = font
font_title = font

try:
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 16)
    font_big = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 20)
    font_title = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 28)
except Exception:
    pass

def text(x,y,s,f=font,fill=TEXT,anchor=None):
    d.text((x,y), s, font=f, fill=fill, anchor=anchor)

text(40,24,'Future-Seed positive cases: solidity by evidence tier',font_title)
text(40,58,'Left: FG gain in percentage points. Right: validation-loss improvement (FS0 - FS1). Circle size ~= seed count.',font, SUB)

margin_top=110
label_x=40
left_x0=290
left_w=400
gap=70
right_x0=left_x0+left_w+gap
right_w=400
row_h=68
max_fg_pp=16.0
max_loss=0.8

for t in range(0,17,2):
    x=left_x0+left_w*t/max_fg_pp
    d.line((x,margin_top,x,margin_top+row_h*len(cases)), fill=GRID, width=1)
    text(x, margin_top-20, str(t), font, SUB, 'mm')
text(left_x0+left_w/2, margin_top-42, 'FG gain (pp)', font_big, TEXT, 'mm')
xt = left_x0+left_w*1.5/max_fg_pp
for yy in (margin_top, margin_top+row_h*len(cases)):
    pass
for off in range(0,row_h*len(cases),8):
    y1 = margin_top+off
    y2 = min(y1+4, margin_top+row_h*len(cases))
    d.line((xt,y1,xt,y2), fill='#7c7c7c', width=2)
text(xt+4, margin_top+row_h*len(cases)+8, 'main-line threshold 1.5pp', font, '#666666')

for t in range(0,9):
    v=t/10
    x=right_x0+right_w*v/max_loss
    d.line((x,margin_top,x,margin_top+row_h*len(cases)), fill=GRID, width=1)
    text(x, margin_top-20, f'{v:.1f}', font, SUB, 'mm')
text(right_x0+right_w/2, margin_top-42, 'Validation loss improvement', font_big, TEXT, 'mm')

for i,c in enumerate(cases):
    y=margin_top+i*row_h+26
    text(label_x, y-8, c['label'], font_big)
    text(label_x, y+14, c['note'], font, SUB)
    col=COLORS[c['kind']]
    fg_pp=c['delta_fg']*100
    cx=left_x0+left_w*fg_pp/max_fg_pp
    r=int(10+c['n_seeds']*3)
    d.ellipse((cx-r,y-r,cx+r,y+r), fill=col, outline='black', width=1)
    text(cx+r+10,y-8,f'{fg_pp:.1f}pp',font_big)
    bar_x1=right_x0+right_w*c['delta_loss']/max_loss
    d.rounded_rectangle((right_x0,y-10,bar_x1,y+10), radius=4, fill=col)
    text(bar_x1+10,y-8,f"{c['delta_loss']:.3f}",font_big)

legend = [
    ('solid-main','solid main line'),
    ('solid-discovery','solid discovery family'),
    ('strong-single','strong single run'),
    ('promising-not-solid','promising, not solid yet'),
]
x=40
y=H-36
for key,label in legend:
    col=COLORS[key]
    d.ellipse((x-7,y-7,x+7,y+7), fill=col, outline='black', width=1)
    text(x+16,y-8,label,font)
    x += 290

img.save(out)
print(out)
