#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path

import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Evaluate Moving MNIST v2 checkpoints with fixed metrics.')
    p.add_argument('--trainer', type=Path, required=True)
    p.add_argument('--data-bin', type=Path, required=True)
    p.add_argument('--weights', type=Path, required=True)
    p.add_argument('--out-json', type=Path, required=True)
    p.add_argument('--voc', type=int, required=True)
    p.add_argument('--seq-len', type=int, required=True)
    p.add_argument('--frame-side', type=int, required=True)
    p.add_argument('--frame-count', type=int, default=3)
    p.add_argument('--n-layer', type=int, required=True)
    p.add_argument('--n-embd', type=int, required=True)
    p.add_argument('--head-size', type=int, required=True)
    p.add_argument('--prefix-ratio', type=float, default=0.333333)
    p.add_argument('--eval-samples', type=int, default=256)
    p.add_argument('--seed', type=int, default=20260309)
    p.add_argument('--device', type=str, default='cuda' if torch.cuda.is_available() else 'cpu')
    return p.parse_args()


def load_rows(path: Path, seq_len: int) -> np.ndarray:
    with path.open('rb') as f:
        f.read(256 * 4)
        arr = np.frombuffer(f.read(), dtype=np.uint16)
    if arr.size % seq_len != 0:
        raise RuntimeError(f'bad bin size: {arr.size} not divisible by {seq_len}')
    return arr.reshape(-1, seq_len)


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
    spec = importlib.util.spec_from_file_location('rwkv_mm_eval', str(args.trainer))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_model(module, args: argparse.Namespace):
    cfg = module.GPTConfig(vocab_size=args.voc + 1, n_layer=args.n_layer, n_embd=args.n_embd)
    future_seed = 'fs1' in args.weights.name.lower() or 'future_seed=1' in args.weights.name.lower()
    model = module.GPT(cfg, future_seed=future_seed).to(args.device)
    model.load_state_dict(torch.load(args.weights, map_location=args.device))
    model.eval()
    return model


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


def main() -> None:
    args = parse_args()
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    rows = load_rows(args.data_bin, args.seq_len)
    module = import_trainer(args)
    model = load_model(module, args)

    frame_tokens = args.frame_side * args.frame_side
    prefix_len = frame_tokens
    mask = np.zeros(args.seq_len, dtype=bool)
    mask[:prefix_len] = True

    tp = fp = fn = tn = 0
    l1_sum = 0.0
    fg_acc_sum = 0.0
    fg_acc_used = 0
    for i in range(min(args.eval_samples, len(rows))):
        y = rows[i].astype(np.int64)
        out = infer(model, y, mask, args.voc, args.device)
        gt = y[:frame_tokens]
        pr = out[:frame_tokens]
        gt_fg = gt > 0
        pr_fg = pr > 0
        tp += int(np.logical_and(gt_fg, pr_fg).sum())
        fp += int(np.logical_and(~gt_fg, pr_fg).sum())
        fn += int(np.logical_and(gt_fg, ~pr_fg).sum())
        tn += int(np.logical_and(~gt_fg, ~pr_fg).sum())
        l1_sum += float(np.abs(pr - gt).mean())
        if gt_fg.any():
            fg_acc_sum += float((pr[gt_fg] == gt[gt_fg]).mean())
            fg_acc_used += 1

    iou = tp / max(tp + fp + fn, 1)
    f1 = 2 * tp / max(2 * tp + fp + fn, 1)
    l1 = l1_sum / min(args.eval_samples, len(rows))
    fg_acc = fg_acc_sum / max(fg_acc_used, 1)
    out = {
        'weights': str(args.weights),
        'eval_samples': int(min(args.eval_samples, len(rows))),
        'val_middle_iou': float(iou),
        'val_middle_f1': float(f1),
        'val_middle_l1': float(l1),
        'val_middle_fg_acc': float(fg_acc),
        'tp': int(tp),
        'fp': int(fp),
        'fn': int(fn),
        'tn': int(tn),
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
