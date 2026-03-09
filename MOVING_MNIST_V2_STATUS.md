# Moving MNIST v2 Status

## Final status

This branch is currently **paused / closed**.

Reason:

- baseline whole-middle-frame interpolation: `discard`
- `num_digits=2` harder interpolation: `discard`
- `middle-frame square hole (8x8)`: `discard`

After two consecutive discard results on the new autoresearch-style loop, there is no evidence that Future-Seed is helping this Moving MNIST v2 setup under the current fixed budget and evaluator.

## Completed runs

1. `moving_mnist_v2_smoke_20260309a`
- task: full middle-frame reconstruction from left/right frames
- result: `delta_iou = 0.0000`, `delta_l1 = 0.0000`
- status: `discard`

2. `moving_mnist_v2_nd2_20260309T065421Z`
- mutation: `num_digits=2`
- result: `delta_iou = 0.0000`, `delta_l1 = 0.0000`
- status: `discard`

3. `moving_mnist_v2_masksquare_sq8_sfs24_sfi0_20260309T084833Z`
- mutation: `mask_mode=square,square_size=8`
- result: `delta_iou = 0.0000`, `delta_l1 = 0.0000`
- status: `discard`

## Interpretation

The task itself is learnable: training loss falls substantially for both FS0 and FS1.

But under the fixed evaluator, both models collapse to the same degenerate prediction on the masked region:

- IoU = 0
- F1 = 0
- FG accuracy = 0
- identical L1 for FS0 and FS1

So the current conclusion is not "Future-Seed hurts".
It is narrower:

**Under this Moving MNIST v2 formulation and budget, we do not observe any measurable benefit from Future-Seed.**

## Why we stop here

This branch already applied the main process fix:

- fixed builder
- fixed evaluator
- fixed launcher
- one mutable surface (`spec.json`)
- append-only results table

So continuing to mutate more specs right now is low ROI.

## Recommended next step

Do not continue this exact Moving MNIST v2 branch immediately.

Prefer one of these:

1. a stronger positive control with obvious future dependence, such as bouncing shapes / grid sprites
2. return to the already-solid real-video lines for final write-up
3. redesign the Moving MNIST evaluator around a different reconstruction target before reopening the branch
