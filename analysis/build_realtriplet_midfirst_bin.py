#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build real-video triplet-midfirst bins from mp4 files.")
    p.add_argument("--raw-dir", type=Path, required=True)
    p.add_argument("--train-out", type=Path, required=True)
    p.add_argument("--val-out", type=Path, required=True)
    p.add_argument("--gap", type=int, required=True, help="Temporal gap between frames in a triplet window.")
    p.add_argument("--img-size", type=int, default=16)
    p.add_argument("--vocab-size", type=int, default=16)
    p.add_argument("--train-samples", type=int, default=4000)
    p.add_argument("--val-samples", type=int, default=800)
    p.add_argument("--seed", type=int, default=20260307)
    return p.parse_args()


def load_video_tokens(video_path: Path, img_size: int, vocab_size: int) -> np.ndarray:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"failed to open video: {video_path}")

    frames: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (img_size, img_size), interpolation=cv2.INTER_AREA)
        q = np.clip((small.astype(np.uint16) * vocab_size) // 256, 0, vocab_size - 1)
        frames.append(q.astype(np.uint16))
    cap.release()

    if not frames:
        raise RuntimeError(f"no frames decoded from {video_path}")
    return np.stack(frames, axis=0)


def build_windows(videos: list[np.ndarray], gap: int) -> np.ndarray:
    windows: list[np.ndarray] = []
    for frames in videos:
        if len(frames) < 2 * gap + 1:
            continue
        for start in range(0, len(frames) - 2 * gap):
            left = frames[start]
            mid = frames[start + gap]
            right = frames[start + 2 * gap]
            triplet = np.concatenate([mid.reshape(-1), left.reshape(-1), right.reshape(-1)], axis=0)
            windows.append(triplet.astype(np.uint16))
    if not windows:
        raise RuntimeError(f"no valid windows for gap={gap}")
    return np.stack(windows, axis=0)


def sample_rows(windows: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    idx = rng.integers(0, len(windows), size=n, endpoint=False)
    return windows[idx]


def write_bin(path: Path, rows: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = np.zeros(256, dtype=np.int32)
    with path.open("wb") as f:
        f.write(header.tobytes())
        f.write(rows.astype(np.uint16).reshape(-1).tobytes())


def main() -> None:
    args = parse_args()
    videos = []
    for video_path in sorted(args.raw_dir.glob("*.mp4")):
        videos.append(load_video_tokens(video_path, args.img_size, args.vocab_size))
    if not videos:
        raise RuntimeError(f"no mp4 files under {args.raw_dir}")

    windows = build_windows(videos, args.gap)
    rng = np.random.default_rng(args.seed)
    train_rows = sample_rows(windows, args.train_samples, rng)
    val_rows = sample_rows(windows, args.val_samples, rng)
    write_bin(args.train_out, train_rows)
    write_bin(args.val_out, val_rows)

    print(
        {
            "raw_dir": str(args.raw_dir),
            "n_videos": len(videos),
            "n_windows": int(len(windows)),
            "gap": int(args.gap),
            "img_size": int(args.img_size),
            "vocab_size": int(args.vocab_size),
            "train_samples": int(args.train_samples),
            "val_samples": int(args.val_samples),
            "train_out": str(args.train_out),
            "val_out": str(args.val_out),
        }
    )


if __name__ == "__main__":
    main()
