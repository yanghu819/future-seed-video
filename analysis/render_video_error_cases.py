#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import math
import os
from pathlib import Path

import cv2
import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Render focused target/error cases for video experiments.')
    p.add_argument('--trainer', type=Path, required=True)
    p.add_argument('--data-bin', type=Path, required=True)
    p.add_argument('--fs0-weights', type=Path, required=True)
    p.add_argument('--fs1-weights', type=Path, required=True)
    p.add_argument('--out-png', type=Path, required=True)
    p.add_argument('--title', type=str, required=True)
    p.add_argument('--voc', type=int, required=True)
    p.add_argument('--seq-len', type=int, required=True)
    p.add_argument('--frame-side', type=int, required=True)
    p.add_argument('--frame-count', type=int, default=3)
    p.add_argument('--n-layer', type=int, required=True)
    p.add_argument('--n-embd', type=int, required=True)
    p.add_argument('--head-size', type=int, required=True)
    p.add_argument('--mask-mode', choices=['prefix', 'square'], required=True)
    p.add_argument('--prefix-ratio', type=float, default=0.0)
    p.add_argument('--square-size', type=int, default=0)
    p.add_argument('--square-frame-index', type=int, default=0)
    p.add_argument('--fg-threshold', type=int, default=0)
    p.add_argument('--scan-samples', type=int, default=96)
    p.add_argument('--top-k', type=int, default=4)
    p.add_argument('--seed', type=int, default=0)
    p.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu')
    return p.parse_args()


def load_rows(path: Path, seq_len: int) -> np.ndarray:
    with path.open('rb') as f:
        f.read(256 * 4)
        arr = np.frombuffer(f.read(), dtype=np.uint16)
    return arr.reshape(-1, seq_len)


def build_mask(args: argparse.Namespace) -> np.ndarray:
    mask = np.zeros(args.seq_len, dtype=bool)
    if args.mask_mode == 'prefix':
        prefix_len = max(1, min(args.seq_len, int(args.seq_len * args.prefix_ratio)))
        mask[:prefix_len] = True
    else:
        side = args.frame_side
        sq = max(1, min(side, args.square_size))
        r0 = (side - sq) // 2
        c0 = (side - sq) // 2
        frame_mask = np.zeros((side, side), dtype=bool)
        frame_mask[r0:r0+sq, c0:c0+sq] = True
        start = args.square_frame_index * side * side
        mask[start:start + side * side] = frame_mask.reshape(-1)
    return mask


def import_trainer(args: argparse.Namespace):
    os.environ['MODEL'] = 'rwkv'
    os.environ['RWKV7_KERNEL'] = 'python'
    os.environ['HEAD_SIZE'] = str(args.head_size)
    os.environ['SEQ_LEN'] = str(args.seq_len)
    os.environ['VOCAB_SIZE'] = str(args.voc)
    os.environ['N_LAYER'] = str(args.n_layer)
    os.environ['N_EMBD'] = str(args.n_embd)
    os.environ['DATA_BIN'] = str(args.data_bin)
    os.environ['DATA_VAL_BIN'] = str(args.data_bin)
    os.environ['DEVICE_BSZ'] = '1'
    os.environ['BATCH_SIZE'] = '1'
    os.environ['TRAIN'] = '0'
    os.environ['FUTURE_SEED_ALPHA_INIT'] = '-2'
    spec = importlib.util.spec_from_file_location('rwkv_case_module', str(args.trainer))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_models(module, args: argparse.Namespace, device: str):
    cfg = module.GPTConfig(vocab_size=args.voc + 1, n_layer=args.n_layer, n_embd=args.n_embd)
    fs0 = module.GPT(cfg, future_seed=False).to(device)
    fs1 = module.GPT(cfg, future_seed=True).to(device)
    fs0.load_state_dict(torch.load(args.fs0_weights, map_location=device))
    fs1.load_state_dict(torch.load(args.fs1_weights, map_location=device))
    fs0.eval(); fs1.eval()
    return fs0, fs1


def infer(model, row: np.ndarray, mask: np.ndarray, mask_token_id: int, device: str) -> np.ndarray:
    x = row.copy()
    x[mask] = mask_token_id
    x_t = torch.tensor(x, dtype=torch.long, device=device).unsqueeze(0)
    with torch.no_grad():
        logits, _ = model(x_t)
    pred = logits.argmax(dim=-1)[0].detach().cpu().numpy().astype(np.int64)
    out = x.copy().astype(np.int64)
    out[mask] = pred[mask]
    return out


def fg_acc(out: np.ndarray, y: np.ndarray, mask: np.ndarray, thr: int) -> float:
    fg = mask & (y > thr)
    if fg.sum() == 0:
        return float('nan')
    return float((out[fg] == y[fg]).mean())


def mae(out: np.ndarray, y: np.ndarray, mask: np.ndarray) -> float:
    return float(np.abs(out[mask].astype(np.int64) - y[mask].astype(np.int64)).mean())


def frame_to_gray(frame_tokens: np.ndarray, side: int, voc: int, scale: int = 12) -> np.ndarray:
    arr = frame_tokens.reshape(side, side).astype(np.float32)
    arr = arr * (255.0 / max(voc - 1, 1))
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return cv2.resize(arr, (side * scale, side * scale), interpolation=cv2.INTER_NEAREST)


def error_to_rgb(pred_tokens: np.ndarray, gt_tokens: np.ndarray, side: int, voc: int, scale: int = 12) -> np.ndarray:
    err = np.abs(pred_tokens.reshape(side, side).astype(np.float32) - gt_tokens.reshape(side, side).astype(np.float32))
    err = err / max(voc - 1, 1)
    err = np.clip(err * 255.0, 0, 255).astype(np.uint8)
    err = cv2.resize(err, (side * scale, side * scale), interpolation=cv2.INTER_NEAREST)
    return cv2.applyColorMap(err, cv2.COLORMAP_TURBO)


def overlay_square(img_gray: np.ndarray, side: int, sq: int, color=(0,0,255)) -> np.ndarray:
    rgb = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
    scale = img_gray.shape[0] // side
    r0 = (side - sq) // 2
    c0 = (side - sq) // 2
    x0, y0 = c0 * scale, r0 * scale
    x1, y1 = (c0 + sq) * scale, (r0 + sq) * scale
    cv2.rectangle(rgb, (x0, y0), (x1-1, y1-1), color, 2)
    return rgb


def crop_square(img: np.ndarray, side: int, sq: int, pad: int = 4) -> np.ndarray:
    scale = img.shape[0] // side
    r0 = max(0, (side - sq) // 2 - pad)
    c0 = max(0, (side - sq) // 2 - pad)
    r1 = min(side, (side - sq) // 2 + sq + pad)
    c1 = min(side, (side - sq) // 2 + sq + pad)
    return img[r0*scale:r1*scale, c0*scale:c1*scale]


def label_cell(img: np.ndarray, title: str, subtitle: str = '') -> np.ndarray:
    h, w = img.shape[:2]
    top = 44 if subtitle else 28
    out = np.full((h + top, w, 3), 245, np.uint8)
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    out[top:, :] = img
    cv2.putText(out, title, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (18,18,18), 1, cv2.LINE_AA)
    if subtitle:
        cv2.putText(out, subtitle, (6, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (70,70,70), 1, cv2.LINE_AA)
    return out


def stack_grid(rows: list[list[np.ndarray]], header: str) -> np.ndarray:
    gap = 10
    row_gap = 18
    widths = [sum(im.shape[1] for im in row) + gap*(len(row)-1) for row in rows]
    heights = [max(im.shape[0] for im in row) for row in rows]
    W = max(widths) + 40
    H = sum(heights) + row_gap*(len(rows)-1) + 86
    canvas = np.full((H, W, 3), 247, np.uint8)
    cv2.putText(canvas, header, (20, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (22,22,22), 2, cv2.LINE_AA)
    cv2.putText(canvas, 'GT / FS0 / FS1 plus absolute error maps. Hotter colors mean larger token error.', (20, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (80,80,80), 1, cv2.LINE_AA)
    y = 76
    for row, rh in zip(rows, heights):
        x = 20
        for im in row:
            h, w = im.shape[:2]
            canvas[y:y+h, x:x+w] = im
            x += w + gap
        y += rh + row_gap
    return canvas


def main() -> None:
    args = parse_args()
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    rows = load_rows(args.data_bin, args.seq_len)
    mask = build_mask(args)
    module = import_trainer(args)
    fs0, fs1 = load_models(module, args, args.device)
    frame_tokens = args.frame_side * args.frame_side
    target_frame = args.square_frame_index if args.mask_mode == 'square' else 0

    scored = []
    for idx in range(min(len(rows), args.scan_samples)):
        y = rows[idx].astype(np.int64)
        out0 = infer(fs0, y, mask, args.voc, args.device)
        out1 = infer(fs1, y, mask, args.voc, args.device)
        a0 = fg_acc(out0, y, mask, args.fg_threshold)
        a1 = fg_acc(out1, y, mask, args.fg_threshold)
        m0 = mae(out0, y, mask)
        m1 = mae(out1, y, mask)
        delta = (-999.0 if math.isnan(a1) else a1) - (-999.0 if math.isnan(a0) else a0)
        scored.append((delta, m0 - m1, idx, y, out0, out1, a0, a1, m0, m1))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    picked = scored[:args.top_k]

    vis_rows = []
    for rank, (delta_fg, delta_mae, idx, y, out0, out1, a0, a1, m0, m1) in enumerate(picked, start=1):
        gt = y[target_frame*frame_tokens:(target_frame+1)*frame_tokens]
        pr0 = out0[target_frame*frame_tokens:(target_frame+1)*frame_tokens]
        pr1 = out1[target_frame*frame_tokens:(target_frame+1)*frame_tokens]
        gimg = frame_to_gray(gt, args.frame_side, args.voc)
        p0 = frame_to_gray(pr0, args.frame_side, args.voc)
        p1 = frame_to_gray(pr1, args.frame_side, args.voc)
        e0 = error_to_rgb(pr0, gt, args.frame_side, args.voc)
        e1 = error_to_rgb(pr1, gt, args.frame_side, args.voc)
        if args.mask_mode == 'square':
            gimg = overlay_square(gimg, args.frame_side, args.square_size)
            p0 = overlay_square(p0, args.frame_side, args.square_size)
            p1 = overlay_square(p1, args.frame_side, args.square_size)
            e0 = overlay_square(cv2.cvtColor(e0, cv2.COLOR_BGR2GRAY), args.frame_side, args.square_size)
            e1 = overlay_square(cv2.cvtColor(e1, cv2.COLOR_BGR2GRAY), args.frame_side, args.square_size)
            gimg = crop_square(cv2.cvtColor(gimg, cv2.COLOR_BGR2GRAY), args.frame_side, args.square_size)
            p0 = crop_square(cv2.cvtColor(p0, cv2.COLOR_BGR2GRAY), args.frame_side, args.square_size)
            p1 = crop_square(cv2.cvtColor(p1, cv2.COLOR_BGR2GRAY), args.frame_side, args.square_size)
            e0 = crop_square(e0, args.frame_side, args.square_size)
            e1 = crop_square(e1, args.frame_side, args.square_size)
        row_title = np.full((gimg.shape[0] + 44, 210, 3), 247, np.uint8)
        cv2.putText(row_title, f'case {rank}', (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (22,22,22), 2, cv2.LINE_AA)
        cv2.putText(row_title, f'sample {idx}', (8, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (70,70,70), 1, cv2.LINE_AA)
        cv2.putText(row_title, f'FG +{delta_fg:.3f}', (8, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (70,70,70), 1, cv2.LINE_AA)
        cv2.putText(row_title, f'MAE {m0:.2f}->{m1:.2f}', (8, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (70,70,70), 1, cv2.LINE_AA)
        row = [
            row_title,
            label_cell(gimg, 'GT target'),
            label_cell(p0, 'FS0 pred', f'fg_acc={a0:.3f}'),
            label_cell(p1, 'FS1 pred', f'fg_acc={a1:.3f}'),
            label_cell(e0, 'FS0 abs error'),
            label_cell(e1, 'FS1 abs error'),
        ]
        vis_rows.append(row)

    header = args.title
    canvas = stack_grid(vis_rows, header)
    args.out_png.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.out_png), canvas)
    print({'out_png': str(args.out_png), 'picked': [x[2] for x in picked]})


if __name__ == '__main__':
    main()
