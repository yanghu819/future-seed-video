# Video Tasks Explained

## What the two main video experiments actually are

### 1. `task5_realvideo_gap40_confirm3`

This is **video interpolation / missing-middle-frame recovery**, not square-hole inpainting.

- sequence order: `middle | left | right`
- each frame is quantized grayscale `16x16`
- `SEQ_LEN = 768 = 3 * 16 * 16`
- mask: `prefix:0.333333`
- effect of that mask: the **entire middle frame** is hidden
- the model must reconstruct the whole middle frame from the left and right context frames

Qualitative cases:

- [task5_gap40_cases.png](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/task5_gap40_cases.png)
- [task5_gap40_error_cases.png](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/task5_gap40_error_cases.png)

Why this task matters:

- it is a clean future-dependent video task
- in a plain causal scan, the missing middle frame comes first in the token sequence and cannot see the later context frames within a layer
- Future-Seed is exactly meant to help with that

### 2. `realvideo_square_migration_confirm3`

This is **video inpainting in the middle frame**, closer to what people usually mean by hole filling.

- sequence order: `middle | left | right`
- each frame is quantized grayscale `24x24`
- `SEQ_LEN = 1728 = 3 * 24 * 24`
- mask: `square(frame_side=24, frame_index=0, size=8)`
- effect of that mask: only the **center 8x8 hole inside the middle frame** is hidden
- the model sees the rest of the middle frame plus the left/right context frames, and fills the missing hole

Qualitative cases:

- [square_migration_cases.png](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/square_migration_cases.png)
- [square_migration_error_cases.png](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/square_migration_error_cases.png)

Why this task matters:

- it checks whether the gain transfers from full-frame interpolation into a more classic local inpainting geometry
- this branch now passes 3-seed confirm, so it is no longer just a single coarse positive

## How to read the qualitative panels

Each row is one validation sample.

Columns:

1. `left ctx`: left context frame
2. `masked target`: what the model actually gets as the target frame input
3. `right ctx`: right context frame
4. `GT middle`: the real target frame
5. `FS0 pred`: baseline causal RWKV prediction
6. `FS1 pred`: Future-Seed prediction

`fg_acc` is the foreground masked accuracy on that one sample.

## Bottom line

- if you want the cleanest **video interpolation** case, look at `task5_gap40_cases.png`
- if you want the more intuitive **video inpainting / hole filling** case, look at `square_migration_cases.png`

## What the new error maps clarify

- `task5` is a full-middle-frame interpolation task, so the visual difference is distributed over the whole 16x16 frame and can look modest in plain grayscale panels. The error maps are more honest there than the raw images.
- `square migration` is a local-hole task, so zooming the hole and its error map makes the difference much easier to see. In the strongest cases, `FS0` collapses to a smoother/emptier hole fill while `FS1` restores more of the local structure.
