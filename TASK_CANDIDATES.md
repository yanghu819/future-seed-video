# Task Candidates

## Goal

Prioritize new tasks that are most likely to show a real Future-Seed advantage, based on:

1. alignment with Future-Seed's future-dependence mechanism
2. existing empirical hints in our archive
3. implementation cost on the current single-5090 setup

## Ranked Candidates

### 1. `task5_midframe` on `cifar16_triplet_midfirst`

Why it ranks first:

- already strongly positive in the archive
- same "recover the missing middle frame from context" structure that Future-Seed should help
- clean, cheap, and highly reproducible

Evidence:

- [task5_long_20260302T050853Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_long_20260302T050853Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.2186`

Role:

- strongest visual positive control outside the main `realvideo_complex_v1` line

### 2. `task5_realvideo_gap4_long_v2` on `realtriplet_midfirst_gap4`

Why it ranks second:

- same structural family as the strong-positive CIFAR `task5_midframe`
- closer to real video interpolation
- earlier short-budget run showed a large loss advantage for FS1 even though accuracy stayed flat

Evidence:

- [task5_realvideo_gap4_20260302T100014Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_gap4_20260302T100014Z/summary_agg.json)
- short run: `delta_maskacc_fg_val = 0.0000`, but `delta_last_val_loss = -0.1611`

Status:

- queued and running after `fullcfg180`

### 3. `task5_realvideo_long` on `realtriplet_midfirst`

Why it ranks third:

- same real-video family as candidate 2
- earlier short-budget run also showed a material FS1 loss advantage
- likely cheaper to validate than inventing a new dataset

Evidence:

- [task5_realvideo_20260302T091839Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_20260302T091839Z/summary_agg.json)
- short run: `delta_maskacc_fg_val = 0.0000`, but `delta_last_val_loss = -0.1535`

### 4. `task2_square_hole` on `cifar16_gray_row`

Why it ranks fourth:

- this is the cleanest spatial inpainting-style task in the archive
- already showed a weak positive signal under longer budget
- useful if we want a more classic "hole filling" visual task

Evidence:

- [task2_long_20260302T044214Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task2_long_20260302T044214Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.0081`

### 5. `task1_left_half` on `cifar16_gray_col`

Why it ranks lower:

- theoretically future-dependent
- empirically flat in the archive
- weaker than the midframe task family

Evidence:

- [coarse_15_20260302T033458Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/coarse_15_20260302T033458Z/summary_agg.json)
- `delta_maskacc_fg_val = 0.0000`

### 6. `moving_mnist_*`

Why it ranks last:

- early runs show degenerate FG behavior (`0.0` or `1.0`)
- metric is not trustworthy enough yet for efficient FS evaluation
- fixing that metric path is extra work before we can trust any result

Evidence:

- [moving_mnist_coarse120_20260302T110339Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/moving_mnist_coarse120_20260302T110339Z/summary_agg.json)
- [moving_mnist_bin2_coarse120_20260302T114400Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/moving_mnist_bin2_coarse120_20260302T114400Z/summary_agg.json)
- [moving_mnist_bin2_fgW8_coarse120_20260302T122607Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/moving_mnist_bin2_fgW8_coarse120_20260302T122607Z/summary_agg.json)

## Current Recommendation

1. finish `task5_realvideo_gap4_long_v2`
2. if positive, run `task5_realvideo_long`
3. if negative, do not pivot to `moving_mnist`; use `task2_square_hole` as the next cheaper fallback
