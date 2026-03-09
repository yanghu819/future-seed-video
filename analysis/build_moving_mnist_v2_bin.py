#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Build Moving MNIST v2 middle-frame triplets.')
    p.add_argument('--out-dir', type=Path, required=True)
    p.add_argument('--mnist-root', type=Path, default=Path('~/.cache/moving_mnist_v2').expanduser())
    p.add_argument('--img-size', type=int, default=24)
    p.add_argument('--num-digits', type=int, default=1)
    p.add_argument('--digit-size-min', type=int, default=10)
    p.add_argument('--digit-size-max', type=int, default=14)
    p.add_argument('--speed-min', type=float, default=1.25)
    p.add_argument('--speed-max', type=float, default=2.75)
    p.add_argument('--train-samples', type=int, default=4000)
    p.add_argument('--val-samples', type=int, default=800)
    p.add_argument('--seed', type=int, default=20260309)
    return p.parse_args()


MNIST_TRAIN_IMAGES_URL = 'https://ossci-datasets.s3.amazonaws.com/mnist/train-images-idx3-ubyte.gz'


def ensure_train_images(root: Path) -> Path:
    raw = root / 'MNIST' / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    gz_path = raw / 'train-images-idx3-ubyte.gz'
    if not gz_path.exists():
        urllib.request.urlretrieve(MNIST_TRAIN_IMAGES_URL, gz_path)
    return gz_path


def load_digits(root: Path) -> list[np.ndarray]:
    gz_path = ensure_train_images(root)
    with gzip.open(gz_path, 'rb') as f:
        blob = f.read()
    magic = int.from_bytes(blob[0:4], 'big')
    if magic != 2051:
        raise RuntimeError(f'unexpected MNIST magic: {magic}')
    count = int.from_bytes(blob[4:8], 'big')
    rows = int.from_bytes(blob[8:12], 'big')
    cols = int.from_bytes(blob[12:16], 'big')
    arr = np.frombuffer(blob, dtype=np.uint8, offset=16).reshape(count, rows, cols)
    return [img.copy() for img in arr]


def resize_digit(arr: np.ndarray, size: int) -> np.ndarray:
    pil = Image.fromarray(arr)
    small = pil.resize((size, size), Image.Resampling.BILINEAR)
    out = np.array(small, dtype=np.uint8)
    return (out > 20).astype(np.uint8)


def bounce(pos: float, vel: float, limit: int) -> tuple[float, float]:
    new = pos + vel
    if new < 0:
        new = -new
        vel = -vel
    if new > limit:
        new = 2 * limit - new
        vel = -vel
    return new, vel


def render_triplet(rng: np.random.Generator, digits: list[np.ndarray], side: int, num_digits: int, dmin: int, dmax: int, smin: float, smax: float) -> np.ndarray:
    objs = []
    for _ in range(num_digits):
        size = int(rng.integers(dmin, dmax + 1))
        digit = resize_digit(digits[int(rng.integers(0, len(digits)))], size)
        x = float(rng.uniform(0, side - size))
        y = float(rng.uniform(0, side - size))
        vx = float(rng.choice([-1, 1]) * rng.uniform(smin, smax))
        vy = float(rng.choice([-1, 1]) * rng.uniform(smin, smax))
        objs.append([digit, x, y, vx, vy, size])

    frames = []
    for _t in range(3):
        canvas = np.zeros((side, side), dtype=np.uint8)
        for digit, x, y, vx, vy, size in objs:
            xi = int(round(x))
            yi = int(round(y))
            canvas[yi:yi+size, xi:xi+size] = np.maximum(canvas[yi:yi+size, xi:xi+size], digit)
        frames.append(canvas)
        for obj in objs:
            digit, x, y, vx, vy, size = obj
            x, vx = bounce(x, vx, side - size)
            y, vy = bounce(y, vy, side - size)
            obj[1], obj[2], obj[3], obj[4] = x, y, vx, vy

    left, mid, right = frames[0], frames[1], frames[2]
    triplet = np.concatenate([mid.reshape(-1), left.reshape(-1), right.reshape(-1)], axis=0)
    return triplet.astype(np.uint16)


def write_bin(path: Path, rows: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = np.zeros(256, dtype=np.int32)
    with path.open('wb') as f:
        f.write(header.tobytes())
        f.write(rows.astype(np.uint16).reshape(-1).tobytes())


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    digits = load_digits(args.mnist_root)
    train = np.stack([
        render_triplet(rng, digits, args.img_size, args.num_digits, args.digit_size_min, args.digit_size_max, args.speed_min, args.speed_max)
        for _ in range(args.train_samples)
    ])
    val = np.stack([
        render_triplet(rng, digits, args.img_size, args.num_digits, args.digit_size_min, args.digit_size_max, args.speed_min, args.speed_max)
        for _ in range(args.val_samples)
    ])
    write_bin(args.out_dir / 'moving_mnist_v2_train.bin', train)
    write_bin(args.out_dir / 'moving_mnist_v2_val.bin', val)
    print(json.dumps({
        'out_dir': str(args.out_dir),
        'img_size': args.img_size,
        'num_digits': args.num_digits,
        'train_samples': args.train_samples,
        'val_samples': args.val_samples,
        'seq_len': int(train.shape[1]),
        'seed': args.seed,
    }, indent=2))


if __name__ == '__main__':
    main()
