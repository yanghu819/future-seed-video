#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "analysis" / "ratio50_budget_boundary_summary.csv"
OUT_DIR = ROOT / "analysis" / "figures"

W, H = 980, 560
ML, MR, MT, MB = 90, 40, 55, 80
PLOT_W = W - ML - MR
PLOT_H = H - MT - MB
X_MIN, X_MAX = 55, 155
Y_MIN, Y_MAX = -0.002, 0.045
THRESHOLD = 0.015

COLORS = {
    "bg": "#fcfbf7",
    "axis": "#1f2937",
    "grid": "#d1d5db",
    "strict": "#0f766e",
    "supporting": "#6b7280",
    "threshold": "#b91c1c",
    "highlight": "#f59e0b",
    "text": "#111827",
}


def load_rows() -> list[dict]:
    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["budget"] = int(row["budget"])
        row["n_seeds"] = int(row["n_seeds"])
        row["avg"] = float(row["avg_delta_maskacc_fg_val"])
        row["min"] = float(row["min_delta_maskacc_fg_val"])
        row["max"] = float(row["max_delta_maskacc_fg_val"])
    return rows


def xmap(x: float) -> float:
    return ML + (x - X_MIN) / (X_MAX - X_MIN) * PLOT_W


def ymap(y: float) -> float:
    return MT + (Y_MAX - y) / (Y_MAX - Y_MIN) * PLOT_H


def hex_rgba(hex_color: str, alpha: int) -> tuple[int, int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4)) + (alpha,)


def draw_png(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    # Highlight region 90->120
    draw.rectangle(
        [(xmap(90), ymap(Y_MAX)), (xmap(120), ymap(Y_MIN))],
        fill=hex_rgba(COLORS["highlight"], 28),
    )

    # Grid / axes
    y_ticks = [0.0, THRESHOLD, 0.03, 0.045]
    x_ticks = [60, 90, 120, 150]
    for y in y_ticks:
        yy = ymap(y)
        draw.line([(ML, yy), (W - MR, yy)], fill=COLORS["grid"], width=1)
        draw.text((18, yy - 7), f"{y:+.3f}".replace("+", ""), fill=COLORS["text"], font=font)
    for x in x_ticks:
        xx = xmap(x)
        draw.line([(xx, MT), (xx, H - MB)], fill=COLORS["grid"], width=1)
        draw.text((xx - 10, H - MB + 12), str(x), fill=COLORS["text"], font=font)

    draw.line([(ML, MT), (ML, H - MB)], fill=COLORS["axis"], width=2)
    draw.line([(ML, H - MB), (W - MR, H - MB)], fill=COLORS["axis"], width=2)

    # Threshold line
    draw.line(
        [(ML, ymap(THRESHOLD)), (W - MR, ymap(THRESHOLD))],
        fill=COLORS["threshold"],
        width=2,
    )

    # Points and error bars
    for row in rows:
        color = COLORS[row["evidence_tier"]]
        xx = xmap(row["budget"])
        yy = ymap(row["avg"])
        ymin = ymap(row["min"])
        ymax = ymap(row["max"])
        r = 4 + row["n_seeds"]
        draw.line([(xx, ymin), (xx, ymax)], fill=color, width=2)
        draw.line([(xx - 5, ymin), (xx + 5, ymin)], fill=color, width=2)
        draw.line([(xx - 5, ymax), (xx + 5, ymax)], fill=color, width=2)
        if row["evidence_tier"] == "strict":
            draw.ellipse([(xx - r, yy - r), (xx + r, yy + r)], fill=color, outline=color, width=2)
        else:
            draw.ellipse([(xx - r, yy - r), (xx + r, yy + r)], fill=COLORS["bg"], outline=color, width=2)
        draw.text((xx - 10, yy - 22), f"n={row['n_seeds']}", fill=color, font=font)

    # Titles / labels / legend
    draw.text((300, 18), "Future-Seed gain vs training budget on ratio50", fill=COLORS["text"], font=font)
    draw.text((ML, H - 34), "Max training steps", fill=COLORS["text"], font=font)
    draw.text((18, 34), "Delta maskacc_fg_val", fill=COLORS["text"], font=font)
    draw.text((xmap(122), ymap(0.032)), "Boundary turns on here", fill="#92400e", font=font)
    draw.line([(xmap(121), ymap(0.0315)), (xmap(120), ymap(0.0249))], fill="#92400e", width=2)

    legend_x = W - 245
    legend_y = 24
    draw.text((legend_x, legend_y), "Evidence", fill=COLORS["text"], font=font)
    for i, (label, color, filled) in enumerate(
        [("Strict comparable", COLORS["strict"], True), ("Supporting", COLORS["supporting"], False)]
    ):
        y = legend_y + 20 + i * 18
        if filled:
            draw.ellipse([(legend_x, y), (legend_x + 10, y + 10)], fill=color, outline=color)
        else:
            draw.ellipse([(legend_x, y), (legend_x + 10, y + 10)], fill=COLORS["bg"], outline=color, width=2)
        draw.text((legend_x + 16, y - 1), label, fill=COLORS["text"], font=font)
    y = legend_y + 56
    draw.line([(legend_x, y + 5), (legend_x + 12, y + 5)], fill=COLORS["threshold"], width=2)
    draw.text((legend_x + 16, y), "Pass threshold (+0.015)", fill=COLORS["text"], font=font)

    img.save(OUT_DIR / "ratio50_budget_boundary.png")


def svg_circle(cx: float, cy: float, r: float, stroke: str, fill: str, stroke_width: int = 2) -> str:
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" stroke="{stroke}" fill="{fill}" stroke-width="{stroke_width}" />'


def draw_svg(rows: list[dict]) -> None:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{COLORS["bg"]}" />',
        f'<rect x="{xmap(90):.1f}" y="{ymap(Y_MAX):.1f}" width="{xmap(120)-xmap(90):.1f}" height="{ymap(Y_MIN)-ymap(Y_MAX):.1f}" fill="{COLORS["highlight"]}" opacity="0.10" />',
    ]

    y_ticks = [0.0, THRESHOLD, 0.03, 0.045]
    x_ticks = [60, 90, 120, 150]
    for y in y_ticks:
        yy = ymap(y)
        parts.append(f'<line x1="{ML}" y1="{yy:.1f}" x2="{W-MR}" y2="{yy:.1f}" stroke="{COLORS["grid"]}" stroke-width="1" />')
        parts.append(
            f'<text x="18" y="{yy+4:.1f}" font-size="11" fill="{COLORS["text"]}">{escape(f"{y:+.3f}".replace("+", ""))}</text>'
        )
    for x in x_ticks:
        xx = xmap(x)
        parts.append(f'<line x1="{xx:.1f}" y1="{MT}" x2="{xx:.1f}" y2="{H-MB}" stroke="{COLORS["grid"]}" stroke-width="1" />')
        parts.append(f'<text x="{xx-10:.1f}" y="{H-MB+24}" font-size="11" fill="{COLORS["text"]}">{x}</text>')

    parts.append(f'<line x1="{ML}" y1="{MT}" x2="{ML}" y2="{H-MB}" stroke="{COLORS["axis"]}" stroke-width="2" />')
    parts.append(f'<line x1="{ML}" y1="{H-MB}" x2="{W-MR}" y2="{H-MB}" stroke="{COLORS["axis"]}" stroke-width="2" />')
    parts.append(
        f'<line x1="{ML}" y1="{ymap(THRESHOLD):.1f}" x2="{W-MR}" y2="{ymap(THRESHOLD):.1f}" stroke="{COLORS["threshold"]}" stroke-width="2" />'
    )

    for row in rows:
        color = COLORS[row["evidence_tier"]]
        xx = xmap(row["budget"])
        yy = ymap(row["avg"])
        ymin = ymap(row["min"])
        ymax = ymap(row["max"])
        r = 4 + row["n_seeds"]
        parts.append(f'<line x1="{xx:.1f}" y1="{ymin:.1f}" x2="{xx:.1f}" y2="{ymax:.1f}" stroke="{color}" stroke-width="2" />')
        parts.append(f'<line x1="{xx-5:.1f}" y1="{ymin:.1f}" x2="{xx+5:.1f}" y2="{ymin:.1f}" stroke="{color}" stroke-width="2" />')
        parts.append(f'<line x1="{xx-5:.1f}" y1="{ymax:.1f}" x2="{xx+5:.1f}" y2="{ymax:.1f}" stroke="{color}" stroke-width="2" />')
        fill = color if row["evidence_tier"] == "strict" else COLORS["bg"]
        parts.append(svg_circle(xx, yy, r, color, fill))
        parts.append(f'<text x="{xx-10:.1f}" y="{yy-14:.1f}" font-size="11" fill="{color}">n={row["n_seeds"]}</text>')

    parts.append(f'<text x="300" y="26" font-size="18" fill="{COLORS["text"]}">Future-Seed gain vs training budget on ratio50</text>')
    parts.append(f'<text x="{ML}" y="{H-24}" font-size="13" fill="{COLORS["text"]}">Max training steps</text>')
    parts.append(f'<text x="18" y="42" font-size="13" fill="{COLORS["text"]}">Delta maskacc_fg_val</text>')
    parts.append(f'<text x="{xmap(122):.1f}" y="{ymap(0.032):.1f}" font-size="12" fill="#92400e">Boundary turns on here</text>')
    parts.append(
        f'<line x1="{xmap(121):.1f}" y1="{ymap(0.0315):.1f}" x2="{xmap(120):.1f}" y2="{ymap(0.0249):.1f}" stroke="#92400e" stroke-width="2" />'
    )

    legend_x = W - 245
    legend_y = 24
    parts.append(f'<text x="{legend_x}" y="{legend_y}" font-size="12" fill="{COLORS["text"]}">Evidence</text>')
    parts.append(svg_circle(legend_x + 5, legend_y + 18, 5, COLORS["strict"], COLORS["strict"]))
    parts.append(f'<text x="{legend_x+16}" y="{legend_y+22}" font-size="11" fill="{COLORS["text"]}">Strict comparable</text>')
    parts.append(svg_circle(legend_x + 5, legend_y + 36, 5, COLORS["supporting"], COLORS["bg"]))
    parts.append(f'<text x="{legend_x+16}" y="{legend_y+40}" font-size="11" fill="{COLORS["text"]}">Supporting</text>')
    parts.append(f'<line x1="{legend_x}" y1="{legend_y+54}" x2="{legend_x+12}" y2="{legend_y+54}" stroke="{COLORS["threshold"]}" stroke-width="2" />')
    parts.append(f'<text x="{legend_x+16}" y="{legend_y+58}" font-size="11" fill="{COLORS["text"]}">Pass threshold (+0.015)</text>')

    parts.append("</svg>")
    (OUT_DIR / "ratio50_budget_boundary.svg").write_text("\n".join(parts))


def main() -> None:
    rows = load_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    draw_png(rows)
    draw_svg(rows)


if __name__ == "__main__":
    main()
