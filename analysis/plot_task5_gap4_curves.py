#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / 'artifacts' / 'task5_realvideo_gap4_long_v2_20260306T135653Z'
FS0_LOG = EXP_DIR / 'logs' / 'fs0.log'
FS1_LOG = EXP_DIR / 'logs' / 'fs1.log'
OUT_DIR = ROOT / 'analysis' / 'figures'

W, H = 1180, 620
BG = '#fcfbf7'
TEXT = '#111827'
GRID = '#d1d5db'
AXIS = '#1f2937'
FS0 = '#6b7280'
FS1 = '#0f766e'
ACC = '#9a3412'
LOSS = '#1d4ed8'

STEP_RE = re.compile(r'^step\s+(\d+):\s+train loss\s+([0-9.]+),\s+val loss\s+([0-9.]+),')
ACC_RE = re.compile(r'^maskacc_val\s+([0-9.]+)$')
FG_RE = re.compile(r'^maskacc_fg_val\s+([0-9.]+)$')


def parse_log(path: Path):
    rows = []
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        m = STEP_RE.match(lines[i].strip())
        if m and i + 2 < len(lines):
            m_acc = ACC_RE.match(lines[i + 1].strip())
            m_fg = FG_RE.match(lines[i + 2].strip())
            if m_acc and m_fg:
                rows.append(
                    {
                        'step': int(m.group(1)),
                        'train_loss': float(m.group(2)),
                        'val_loss': float(m.group(3)),
                        'maskacc_val': float(m_acc.group(1)),
                        'maskacc_fg_val': float(m_fg.group(1)),
                    }
                )
        i += 1
    return rows


def xmap(x, x0, x1, left, width):
    return left + (x - x0) / (x1 - x0) * width


def ymap(y, y0, y1, top, height):
    return top + (y1 - y) / (y1 - y0) * height


def draw_line(draw, pts, color, width=3):
    if len(pts) >= 2:
        draw.line(pts, fill=color, width=width)
    for x, y in pts:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=color, outline=color)


def draw_png(fs0_rows, fs1_rows):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGBA', (W, H), BG)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    left1, top1, plot_w, plot_h = 80, 90, 470, 390
    left2, top2 = 630, 90
    x0, x1 = 0, 400
    y0_acc, y1_acc = 0.0, 0.60
    y0_loss, y1_loss = 1.15, 2.90

    for left, top, y0, y1, ylabel in [
        (left1, top1, y0_acc, y1_acc, 'maskacc_fg_val'),
        (left2, top2, y0_loss, y1_loss, 'val_loss'),
    ]:
        for x in [0, 50, 100, 150, 200, 250, 300, 350, 399]:
            xx = xmap(x, x0, x1, left, plot_w)
            draw.line((xx, top, xx, top + plot_h), fill=GRID, width=1)
            draw.text((xx - 10, top + plot_h + 10), str(x), fill=TEXT, font=font)
        yticks = [0.0, 0.15, 0.30, 0.45, 0.60] if ylabel == 'maskacc_fg_val' else [1.2, 1.6, 2.0, 2.4, 2.8]
        for y in yticks:
            yy = ymap(y, y0, y1, top, plot_h)
            draw.line((left, yy, left + plot_w, yy), fill=GRID, width=1)
            draw.text((left - 48, yy - 7), f'{y:.2f}', fill=TEXT, font=font)
        draw.line((left, top, left, top + plot_h), fill=AXIS, width=2)
        draw.line((left, top + plot_h, left + plot_w, top + plot_h), fill=AXIS, width=2)
        draw.text((left, top - 24), ylabel, fill=TEXT, font=font)
        draw.text((left + plot_w - 50, top + plot_h + 10), 'step', fill=TEXT, font=font)

    fs0_acc_pts = [(xmap(r['step'], x0, x1, left1, plot_w), ymap(r['maskacc_fg_val'], y0_acc, y1_acc, top1, plot_h)) for r in fs0_rows]
    fs1_acc_pts = [(xmap(r['step'], x0, x1, left1, plot_w), ymap(r['maskacc_fg_val'], y0_acc, y1_acc, top1, plot_h)) for r in fs1_rows]
    fs0_loss_pts = [(xmap(r['step'], x0, x1, left2, plot_w), ymap(r['val_loss'], y0_loss, y1_loss, top2, plot_h)) for r in fs0_rows]
    fs1_loss_pts = [(xmap(r['step'], x0, x1, left2, plot_w), ymap(r['val_loss'], y0_loss, y1_loss, top2, plot_h)) for r in fs1_rows]

    draw_line(draw, fs0_acc_pts, FS0)
    draw_line(draw, fs1_acc_pts, FS1)
    draw_line(draw, fs0_loss_pts, FS0)
    draw_line(draw, fs1_loss_pts, FS1)

    draw.text((80, 24), 'Strong positive real-video task: gap4 midframe recovery', fill=TEXT, font=font)
    draw.text((80, 46), 'FS1 pulls away early and keeps widening the gap through step 399', fill='#92400e', font=font)

    legend_x, legend_y = 920, 26
    draw.text((legend_x, legend_y), 'Legend', fill=TEXT, font=font)
    draw.line((legend_x, legend_y + 20, legend_x + 22, legend_y + 20), fill=FS0, width=3)
    draw.ellipse((legend_x + 8, legend_y + 16, legend_x + 16, legend_y + 24), fill=FS0, outline=FS0)
    draw.text((legend_x + 30, legend_y + 15), 'FS0 baseline', fill=TEXT, font=font)
    draw.line((legend_x, legend_y + 40, legend_x + 22, legend_y + 40), fill=FS1, width=3)
    draw.ellipse((legend_x + 8, legend_y + 36, legend_x + 16, legend_y + 44), fill=FS1, outline=FS1)
    draw.text((legend_x + 30, legend_y + 35), 'FS1 future-seed', fill=TEXT, font=font)

    best0 = max(r['maskacc_fg_val'] for r in fs0_rows)
    best1 = max(r['maskacc_fg_val'] for r in fs1_rows)
    delta = best1 - best0
    loss0 = fs0_rows[-1]['val_loss']
    loss1 = fs1_rows[-1]['val_loss']
    draw.rounded_rectangle((820, 470, 1120, 575), radius=12, outline='#d6d3d1', fill='#fffdf8', width=2)
    draw.text((840, 490), f'best FG: FS0 {best0:.4f} -> FS1 {best1:.4f}', fill=TEXT, font=font)
    draw.text((840, 515), f'delta FG: +{delta:.4f}', fill='#065f46', font=font)
    draw.text((840, 540), f'last val loss: {loss0:.4f} -> {loss1:.4f}', fill=TEXT, font=font)
    draw.text((840, 565), f'delta loss: {loss1 - loss0:+.4f}', fill='#1d4ed8', font=font)

    img.save(OUT_DIR / 'task5_realvideo_gap4_long_v2_curves.png')


def draw_svg(fs0_rows, fs1_rows):
    left1, top1, plot_w, plot_h = 80, 90, 470, 390
    left2, top2 = 630, 90
    x0, x1 = 0, 400
    y0_acc, y1_acc = 0.0, 0.60
    y0_loss, y1_loss = 1.15, 2.90

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{BG}" />',
        f'<text x="80" y="24" font-size="18" fill="{TEXT}">Strong positive real-video task: gap4 midframe recovery</text>',
        f'<text x="80" y="46" font-size="12" fill="#92400e">FS1 pulls away early and keeps widening the gap through step 399</text>',
    ]

    def panel(left, top, y0, y1, ylabel, yticks):
        out = []
        for x in [0, 50, 100, 150, 200, 250, 300, 350, 399]:
            xx = xmap(x, x0, x1, left, plot_w)
            out.append(f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{top+plot_h}" stroke="{GRID}" stroke-width="1" />')
            out.append(f'<text x="{xx-10:.1f}" y="{top+plot_h+22}" font-size="11" fill="{TEXT}">{x}</text>')
        for y in yticks:
            yy = ymap(y, y0, y1, top, plot_h)
            out.append(f'<line x1="{left}" y1="{yy:.1f}" x2="{left+plot_w}" y2="{yy:.1f}" stroke="{GRID}" stroke-width="1" />')
            out.append(f'<text x="{left-48}" y="{yy+4:.1f}" font-size="11" fill="{TEXT}">{y:.2f}</text>')
        out.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="{AXIS}" stroke-width="2" />')
        out.append(f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="{AXIS}" stroke-width="2" />')
        out.append(f'<text x="{left}" y="{top-14}" font-size="12" fill="{TEXT}">{escape(ylabel)}</text>')
        out.append(f'<text x="{left+plot_w-50}" y="{top+plot_h+22}" font-size="11" fill="{TEXT}">step</text>')
        return out

    parts += panel(left1, top1, y0_acc, y1_acc, 'maskacc_fg_val', [0.0, 0.15, 0.30, 0.45, 0.60])
    parts += panel(left2, top2, y0_loss, y1_loss, 'val_loss', [1.2, 1.6, 2.0, 2.4, 2.8])

    def poly(rows, left, top, y0, y1, key, color):
        pts = [(xmap(r['step'], x0, x1, left, plot_w), ymap(r[key], y0, y1, top, plot_h)) for r in rows]
        parts = [f'<polyline fill="none" stroke="{color}" stroke-width="3" points="' + ' '.join(f'{x:.1f},{y:.1f}' for x,y in pts) + '" />']
        for x, y in pts:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}" />')
        return parts

    parts += poly(fs0_rows, left1, top1, y0_acc, y1_acc, 'maskacc_fg_val', FS0)
    parts += poly(fs1_rows, left1, top1, y0_acc, y1_acc, 'maskacc_fg_val', FS1)
    parts += poly(fs0_rows, left2, top2, y0_loss, y1_loss, 'val_loss', FS0)
    parts += poly(fs1_rows, left2, top2, y0_loss, y1_loss, 'val_loss', FS1)

    legend_x, legend_y = 920, 26
    parts += [
        f'<text x="{legend_x}" y="{legend_y}" font-size="12" fill="{TEXT}">Legend</text>',
        f'<line x1="{legend_x}" y1="{legend_y+20}" x2="{legend_x+22}" y2="{legend_y+20}" stroke="{FS0}" stroke-width="3" />',
        f'<circle cx="{legend_x+12}" cy="{legend_y+20}" r="4" fill="{FS0}" />',
        f'<text x="{legend_x+30}" y="{legend_y+24}" font-size="11" fill="{TEXT}">FS0 baseline</text>',
        f'<line x1="{legend_x}" y1="{legend_y+40}" x2="{legend_x+22}" y2="{legend_y+40}" stroke="{FS1}" stroke-width="3" />',
        f'<circle cx="{legend_x+12}" cy="{legend_y+40}" r="4" fill="{FS1}" />',
        f'<text x="{legend_x+30}" y="{legend_y+44}" font-size="11" fill="{TEXT}">FS1 future-seed</text>',
    ]

    best0 = max(r['maskacc_fg_val'] for r in fs0_rows)
    best1 = max(r['maskacc_fg_val'] for r in fs1_rows)
    delta = best1 - best0
    loss0 = fs0_rows[-1]['val_loss']
    loss1 = fs1_rows[-1]['val_loss']
    parts += [
        '<rect x="820" y="470" width="300" height="105" rx="12" ry="12" fill="#fffdf8" stroke="#d6d3d1" stroke-width="2" />',
        f'<text x="840" y="492" font-size="12" fill="{TEXT}">best FG: FS0 {best0:.4f} -&gt; FS1 {best1:.4f}</text>',
        f'<text x="840" y="517" font-size="12" fill="#065f46">delta FG: +{delta:.4f}</text>',
        f'<text x="840" y="542" font-size="12" fill="{TEXT}">last val loss: {loss0:.4f} -&gt; {loss1:.4f}</text>',
        f'<text x="840" y="567" font-size="12" fill="#1d4ed8">delta loss: {loss1-loss0:+.4f}</text>',
    ]

    parts.append('</svg>')
    (OUT_DIR / 'task5_realvideo_gap4_long_v2_curves.svg').write_text('\n'.join(parts))


def main():
    fs0_rows = parse_log(FS0_LOG)
    fs1_rows = parse_log(FS1_LOG)
    draw_png(fs0_rows, fs1_rows)
    draw_svg(fs0_rows, fs1_rows)


if __name__ == '__main__':
    main()
