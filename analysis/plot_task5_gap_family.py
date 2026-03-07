#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'analysis' / 'figures'
CSV_PATH = ROOT / 'analysis' / 'task5_gap_family_summary.csv'

RUNS = [
    ('adjacent', 'task5_realvideo_long_v2_20260307T014857Z', 'task5_realvideo_long_v2'),
    ('gap4', 'task5_realvideo_gap4_long_v2_20260306T135653Z', 'task5_realvideo_gap4_long_v2'),
    ('gap8', 'task5_realvideo_gap8_long_v1_20260307T023000Z', 'task5_realvideo_gap8_long_v1'),
    ('gap16', 'task5_realvideo_gap16_long_v1_20260307T032500Z', 'task5_realvideo_gap16_long_v1'),
    ('gap24', 'task5_realvideo_gap24_long_v1_20260307T040500Z', 'task5_realvideo_gap24_long'),
    ('gap32', 'task5_realvideo_gap32_long_v1_20260307T040700Z', 'task5_realvideo_gap32_long'),
    ('gap40', 'task5_realvideo_gap40_long_v1_20260307T105308Z', 'task5_realvideo_gap40_long_v1'),
]

W, H = 1180, 680
BG = '#fcfbf7'
TEXT = '#111827'
GRID = '#d1d5db'
AXIS = '#1f2937'
BAR_FG = '#0f766e'
BAR_LOSS = '#1d4ed8'
ACCENT = '#92400e'
PANEL_FILL = '#fffdf8'


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for label, run_dir, key in RUNS:
        path = ROOT / 'artifacts' / run_dir / 'summary_agg.json'
        data = json.loads(path.read_text())
        row = data[key]
        rows.append(
            {
                'label': label,
                'delta_fg': float(row['delta_maskacc_fg_val']),
                'delta_loss_improve': -float(row['delta_last_val_loss']),
                'best_fg_fs0': float(row['best_maskacc_fg_val_fs0']),
                'best_fg_fs1': float(row['best_maskacc_fg_val_fs1']),
            }
        )
    return rows


def write_csv(rows: list[dict]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['label', 'delta_fg', 'delta_loss_improve', 'best_fg_fs0', 'best_fg_fs1'])
        w.writeheader()
        w.writerows(rows)


def x_positions(n: int, left: int, width: int) -> list[float]:
    gap = width / n
    return [left + gap * (i + 0.5) for i in range(n)]


def ymap(y: float, ymin: float, ymax: float, top: int, height: int) -> float:
    return top + (ymax - y) / (ymax - ymin) * height


def draw_panel(draw: ImageDraw.ImageDraw, *, left: int, top: int, width: int, height: int, title: str, ymax: float, rows: list[dict], key: str, color: str, y_ticks: list[float], subtitle: str | None = None) -> None:
    font = ImageFont.load_default()
    draw.rounded_rectangle((left, top, left + width, top + height), radius=12, outline='#d6d3d1', fill=PANEL_FILL, width=2)
    plot_left, plot_top = left + 68, top + 52
    plot_w, plot_h = width - 92, height - 92
    for y in y_ticks:
        yy = ymap(y, 0.0, ymax, plot_top, plot_h)
        draw.line((plot_left, yy, plot_left + plot_w, yy), fill=GRID, width=1)
        draw.text((left + 14, yy - 7), f'{y:.2f}', fill=TEXT, font=font)
    draw.line((plot_left, plot_top, plot_left, plot_top + plot_h), fill=AXIS, width=2)
    draw.line((plot_left, plot_top + plot_h, plot_left + plot_w, plot_top + plot_h), fill=AXIS, width=2)
    xs = x_positions(len(rows), plot_left, plot_w)
    bar_w = plot_w / (len(rows) * 1.8)
    for x, row in zip(xs, rows):
        value = row[key]
        yy = ymap(value, 0.0, ymax, plot_top, plot_h)
        draw.rectangle((x - bar_w / 2, yy, x + bar_w / 2, plot_top + plot_h), fill=color, outline=color)
        draw.text((x - 12, plot_top + plot_h + 10), row['label'], fill=TEXT, font=font)
        draw.text((x - 12, yy - 16), f'{value:.3f}', fill=color, font=font)
    draw.text((left + 18, top + 16), title, fill=TEXT, font=font)
    if subtitle:
        draw.text((left + 18, top + 32), subtitle, fill=ACCENT, font=font)


def draw_png(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGBA', (W, H), BG)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((64, 24), 'Task5 real-video family: Future-Seed stays strong from adjacent to gap40', fill=TEXT, font=font)
    draw.text((64, 44), 'The signal is not isolated to one temporal geometry; gain remains large across the discovered gap ladder through gap40.', fill=ACCENT, font=font)
    draw_panel(draw, left=56, top=82, width=520, height=520, title='Delta maskacc_fg_val', ymax=0.18, rows=rows, key='delta_fg', color=BAR_FG, y_ticks=[0.00, 0.06, 0.12, 0.18], subtitle='Primary metric')
    draw_panel(draw, left=606, top=82, width=520, height=520, title='Validation-loss improvement (-delta_last_val_loss)', ymax=0.80, rows=rows, key='delta_loss_improve', color=BAR_LOSS, y_ticks=[0.00, 0.20, 0.40, 0.60, 0.80], subtitle='Supporting evidence')
    best = max(rows, key=lambda r: r['delta_fg'])
    weakest = min(rows, key=lambda r: r['delta_fg'])
    draw.rounded_rectangle((640, 614, 460 + 640, 662), radius=12, outline='#d6d3d1', fill='#fffdf8', width=2)
    draw.text((660, 630), f"Best FG gain: {best['label']} = +{best['delta_fg']:.4f}; weakest confirmed still = {weakest['label']} = +{weakest['delta_fg']:.4f}", fill=TEXT, font=font)
    img.save(OUT_DIR / 'task5_gap_family.png')


def svg_bar(x: float, y: float, w: float, h: float, fill: str) -> str:
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{fill}" />'


def draw_svg(rows: list[dict]) -> None:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{BG}" />',
        f'<text x="64" y="24" font-size="18" fill="{TEXT}">Task5 real-video family: Future-Seed stays strong from adjacent to gap40</text>',
        f'<text x="64" y="44" font-size="12" fill="{ACCENT}">The signal is not isolated to one temporal geometry; gain remains large across the discovered gap ladder through gap40.</text>',
    ]

    def panel(left: int, top: int, width: int, height: int, title: str, ymax: float, key: str, color: str, ticks: list[float], subtitle: str) -> None:
        parts.append(f'<rect x="{left}" y="{top}" width="{width}" height="{height}" rx="12" ry="12" fill="{PANEL_FILL}" stroke="#d6d3d1" stroke-width="2" />')
        plot_left, plot_top = left + 68, top + 52
        plot_w, plot_h = width - 92, height - 92
        parts.append(f'<text x="{left+18}" y="{top+16}" font-size="12" fill="{TEXT}">{escape(title)}</text>')
        parts.append(f'<text x="{left+18}" y="{top+32}" font-size="11" fill="{ACCENT}">{escape(subtitle)}</text>')
        for y in ticks:
            yy = ymap(y, 0.0, ymax, plot_top, plot_h)
            parts.append(f'<line x1="{plot_left}" y1="{yy:.1f}" x2="{plot_left+plot_w}" y2="{yy:.1f}" stroke="{GRID}" stroke-width="1" />')
            parts.append(f'<text x="{left+14}" y="{yy+4:.1f}" font-size="11" fill="{TEXT}">{y:.2f}</text>')
        parts.append(f'<line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_top+plot_h}" stroke="{AXIS}" stroke-width="2" />')
        parts.append(f'<line x1="{plot_left}" y1="{plot_top+plot_h}" x2="{plot_left+plot_w}" y2="{plot_top+plot_h}" stroke="{AXIS}" stroke-width="2" />')
        xs = x_positions(len(rows), plot_left, plot_w)
        bar_w = plot_w / (len(rows) * 1.8)
        for x, row in zip(xs, rows):
            value = row[key]
            yy = ymap(value, 0.0, ymax, plot_top, plot_h)
            parts.append(svg_bar(x - bar_w / 2, yy, bar_w, plot_top + plot_h - yy, color))
            parts.append(f'<text x="{x-12:.1f}" y="{plot_top+plot_h+22:.1f}" font-size="11" fill="{TEXT}">{escape(row["label"])}</text>')
            parts.append(f'<text x="{x-12:.1f}" y="{yy-6:.1f}" font-size="11" fill="{color}">{value:.3f}</text>')

    panel(56, 82, 520, 520, 'Delta maskacc_fg_val', 0.18, 'delta_fg', BAR_FG, [0.00, 0.06, 0.12, 0.18], 'Primary metric')
    panel(606, 82, 520, 520, 'Validation-loss improvement (-delta_last_val_loss)', 0.80, 'delta_loss_improve', BAR_LOSS, [0.00, 0.20, 0.40, 0.60, 0.80], 'Supporting evidence')
    best = max(rows, key=lambda r: r['delta_fg'])
    weakest = min(rows, key=lambda r: r['delta_fg'])
    parts.append('<rect x="640" y="614" width="460" height="48" rx="12" ry="12" fill="#fffdf8" stroke="#d6d3d1" stroke-width="2" />')
    parts.append(f'<text x="660" y="642" font-size="12" fill="{TEXT}">Best FG gain: {escape(best["label"])} = +{best["delta_fg"]:.4f}; weakest confirmed still = {escape(weakest["label"])} = +{weakest["delta_fg"]:.4f}</text>')
    parts.append('</svg>')
    (OUT_DIR / 'task5_gap_family.svg').write_text('\n'.join(parts))


def main() -> None:
    rows = load_rows()
    write_csv(rows)
    draw_png(rows)
    draw_svg(rows)


if __name__ == '__main__':
    main()
