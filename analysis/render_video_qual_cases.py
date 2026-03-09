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
    p = argparse.ArgumentParser(description='Render qualitative video cases for FS0 vs FS1.')
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
    if arr.size % seq_len != 0:
        raise RuntimeError(f'bad bin size for {path}: {arr.size} not divisible by {seq_len}')
    return arr.reshape(-1, seq_len)


def build_mask(args: argparse.Namespace) -> np.ndarray:
    mask = np.zeros(args.seq_len, dtype=bool)
    if args.mask_mode == 'prefix':
        prefix_len = max(1, min(args.seq_len, int(args.seq_len * args.prefix_ratio)))
        mask[:prefix_len] = True
    elif args.mask_mode == 'square':
        side = args.frame_side
        frame_tokens = side * side
        sq = max(1, min(side, args.square_size))
        r0 = (side - sq) // 2
        c0 = (side - sq) // 2
        frame_mask = np.zeros((side, side), dtype=bool)
        frame_mask[r0:r0+sq, c0:c0+sq] = True
        start = args.square_frame_index * frame_tokens
        mask[start:start+frame_tokens] = frame_mask.reshape(-1)
    else:
        raise ValueError(args.mask_mode)
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
    spec = importlib.util.spec_from_file_location('rwkv_qual_module', str(args.trainer))
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


def run_case(model, row: np.ndarray, mask: np.ndarray, mask_token_id: int, device: str):
    x = row.copy()
    x[mask] = mask_token_id
    x_t = torch.tensor(x, dtype=torch.long, device=device).unsqueeze(0)
    with torch.no_grad():
        logits, _ = model(x_t)
    pred = logits.argmax(dim=-1)[0].detach().cpu().numpy().astype(np.int64)
    out = x.copy().astype(np.int64)
    out[mask] = pred[mask]
    return out, pred


def fg_acc(out: np.ndarray, y: np.ndarray, mask: np.ndarray, thr: int) -> float:
    fg = mask & (y > thr)
    if fg.sum() == 0:
        return float('nan')
    return float((out[fg] == y[fg]).mean())


def to_img(tokens: np.ndarray, side: int, voc: int, scale: int = 8) -> np.ndarray:
    arr = tokens.reshape(side, side).astype(np.float32)
    if voc > 1:
        arr = arr * (255.0 / (voc - 1))
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    arr = cv2.resize(arr, (side * scale, side * scale), interpolation=cv2.INTER_NEAREST)
    return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)


def overlay_mask(img: np.ndarray, mask_tokens: np.ndarray, side: int, color=(40, 40, 220), alpha=0.28) -> np.ndarray:
    mask2d = mask_tokens.reshape(side, side).astype(np.uint8)
    mask2d = cv2.resize(mask2d, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
    out = img.copy()
    color_arr = np.zeros_like(out)
    color_arr[:, :] = color
    sel = mask2d.astype(bool)
    out[sel] = (out[sel] * (1.0 - alpha) + color_arr[sel] * alpha).astype(np.uint8)
    return out


def draw_cell(img: np.ndarray, title: str, subtitle: str = '') -> np.ndarray:
    h, w = img.shape[:2]
    pad_top = 44 if subtitle else 28
    canvas = np.full((h + pad_top, w, 3), 245, np.uint8)
    canvas[pad_top:, :] = img
    cv2.putText(canvas, title, (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (20, 20, 20), 1, cv2.LINE_AA)
    if subtitle:
        cv2.putText(canvas, subtitle, (6, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.46, (70, 70, 70), 1, cv2.LINE_AA)
    return canvas


def make_grid(rows_img: list[list[np.ndarray]], header: str) -> np.ndarray:
    gap = 10
    row_gap = 18
    widths = [sum(img.shape[1] for img in row) + gap * (len(row) - 1) for row in rows_img]
    heights = [max(img.shape[0] for img in row) for row in rows_img]
    W = max(widths) + 40
    H = sum(heights) + row_gap * (len(rows_img) - 1) + 80
    canvas = np.full((H, W, 3), 247, np.uint8)
    cv2.putText(canvas, header, (20, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.82, (24, 24, 24), 2, cv2.LINE_AA)
    y = 60
    for row, rh in zip(rows_img, heights):
        x = 20
        for img in row:
            h, w = img.shape[:2]
            canvas[y:y+h, x:x+w] = img
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
    device = args.device
    fs0, fs1 = load_models(module, args, device)
    mask_token_id = args.voc
    frame_tokens = args.frame_side * args.frame_side

    scored = []
    limit = min(len(rows), args.scan_samples)
    for idx in range(limit):
        y = rows[idx].astype(np.int64)
        out0, _ = run_case(fs0, y, mask, mask_token_id, device)
        out1, _ = run_case(fs1, y, mask, mask_token_id, device)
        a0 = fg_acc(out0, y, mask, args.fg_threshold)
        a1 = fg_acc(out1, y, mask, args.fg_threshold)
        delta = (-999.0 if math.isnan(a1) else a1) - (-999.0 if math.isnan(a0) else a0)
        scored.append((delta, a1, a0, idx, y, out0, out1))

    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    picked = scored[: args.top_k]

    vis_rows = []
    for rank, (delta, a1, a0, idx, y, out0, out1) in enumerate(picked, start=1):
        frames_y = [y[i*frame_tokens:(i+1)*frame_tokens] for i in range(args.frame_count)]
        frames_0 = [out0[i*frame_tokens:(i+1)*frame_tokens] for i in range(args.frame_count)]
        frames_1 = [out1[i*frame_tokens:(i+1)*frame_tokens] for i in range(args.frame_count)]
        frame_mask = [mask[i*frame_tokens:(i+1)*frame_tokens] for i in range(args.frame_count)]
        mid = args.square_frame_index if args.mask_mode == 'square' else 0
        left = 1 if args.frame_count > 1 else 0
        right = 2 if args.frame_count > 2 else min(args.frame_count - 1, 1)

        mid_masked = frames_y[mid].copy()
        mid_masked[frame_mask[mid]] = 0
        imgs = [
            draw_cell(to_img(frames_y[left], args.frame_side, args.voc), 'left ctx'),
            draw_cell(overlay_mask(to_img(mid_masked, args.frame_side, args.voc), frame_mask[mid], args.frame_side), 'masked target'),
            draw_cell(to_img(frames_y[right], args.frame_side, args.voc), 'right ctx'),
            draw_cell(to_img(frames_y[mid], args.frame_side, args.voc), 'GT middle'),
            draw_cell(to_img(frames_0[mid], args.frame_side, args.voc), 'FS0 pred', f'fg_acc={a0:.3f}' if not math.isnan(a0) else 'fg_acc=nan'),
            draw_cell(to_img(frames_1[mid], args.frame_side, args.voc), 'FS1 pred', f'fg_acc={a1:.3f}' if not math.isnan(a1) else 'fg_acc=nan'),
        ]
        title = f'case {rank} | sample {idx} | delta_fg={delta:.3f}'
        row = [draw_cell(np.full((1,1,3),245,np.uint8), title)]
        row = imgs
        # prepend row title as text-only block
        text_block = np.full((imgs[0].shape[0], 220, 3), 247, np.uint8)
        cv2.putText(text_block, f'case {rank}', (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.68, (20,20,20), 2, cv2.LINE_AA)
        cv2.putText(text_block, f'sample {idx}', (8, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (60,60,60), 1, cv2.LINE_AA)
        cv2.putText(text_block, f'FS1-FS0 fg +{delta:.3f}', (8, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (60,60,60), 1, cv2.LINE_AA)
        vis_rows.append([text_block] + imgs)

    header = f'{args.title} | sequence = [middle | left | right] | showing top {len(picked)} validation cases by per-sample FG gain'
    grid = make_grid(vis_rows, header)
    args.out_png.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(args.out_png), grid)
    print({'out_png': str(args.out_png), 'picked_indices': [p[3] for p in picked]})


if __name__ == '__main__':
    main()
