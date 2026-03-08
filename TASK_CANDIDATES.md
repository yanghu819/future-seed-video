# Task Candidates

## Goal

Prioritize new tasks that are most likely to show a real Future-Seed advantage, based on:

1. alignment with Future-Seed's future-dependence mechanism
2. existing empirical hints in our archive
3. implementation cost on the current single-5090 setup

## Evidence Table

- Structured scoreboard: [task_candidate_scoreboard.csv](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/task_candidate_scoreboard.csv)

Interpretation rule:

1. prefer tasks with a real `delta_maskacc_fg_val` advantage
2. if FG delta is still flat, a material `delta_last_val_loss < 0` can justify one longer recheck
3. derived tasks are only worth running if they combine already-validated signals with low implementation cost

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

### 2. `task5_realvideo_gap16_long_v1` on `realtriplet_midfirst_gap16`

Why it now ranks second:

- among the confirmed real-video runs, this currently has the largest FG gain
- it shows the effect survives even when the temporal gap is much larger

Evidence:

- [task5_realvideo_gap16_long_v1_20260307T032500Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_gap16_long_v1_20260307T032500Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.1529`
- `delta_last_val_loss = -0.6820`

Status:

- confirmed positive

### 3. `task5_realvideo_long_v2` on `realtriplet_midfirst`

Why it now ranks third:

- this is the strongest adjacent-context real-video result
- it proves the effect is not limited to only large-gap interpolation

Evidence:

- [task5_realvideo_long_v2_20260307T014857Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_long_v2_20260307T014857Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.1495`
- `delta_last_val_loss = -0.7089`

Status:

- confirmed positive

### 4. `realvideo_square_migration` on `realvideo_complex_midfirst`

Why it now ranks fourth:

- the gap ladder is now strong enough through `gap40`, so the highest-ROI next question is whether that success transfers into a more classic hole-filling geometry
- this branch is no longer blocked: the training script now supports frame-local square masking for non-square triplet sequences
- the first coarse run is already queued and then started under the frozen migrated recipe

Status:

- running as `realvideo_square_migration_coarse120_seed20260318_20260308T031506Z`
- source init: `rvc1_ratio50_full150_seed20260318_{fs0,fs1}`
- target mask: `square(frame_side=24, frame_index=0, size=8)`

### 5. `task5_realvideo_gap40_confirm3` on `realtriplet_midfirst_gap40`

Why it now ranks fifth:

- this is now confirm-grade evidence, not just a single-seed positive
- it shows the strongest reachable-gap line remains stable across three seeds

Evidence:

- [task5_realvideo_gap40_confirm3_20260307T133455Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_gap40_confirm3_20260307T133455Z/summary_agg.json)
- avg `delta_maskacc_fg_val = +0.1461`
- min/max `delta_maskacc_fg_val = +0.1334 / +0.1577`
- avg `delta_last_val_loss = -0.6455`

Status:

- confirm pass

### 6. `task5_realvideo_gap40_long_v1` on `realtriplet_midfirst_gap40`

Why it now ranks sixth:

- this is the strongest-gap single-seed positive we currently have
- even at `gap40`, the gain remains in the same `+0.13` to `+0.15` band rather than collapsing

Evidence:

- [task5_realvideo_gap40_long_v1_20260307T105308Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_gap40_long_v1_20260307T105308Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.1471`
- `delta_last_val_loss = -0.6291`

Status:

- confirmed positive

### 7. `task5_realvideo_gap32_long_v1` on `realtriplet_midfirst_gap32`

Why it now ranks seventh:

- this is no longer speculative; it finished strong positive and unlocked `gap40`
- it shows the family remains healthy beyond `gap24`

Evidence:

- [task5_realvideo_gap32_long_v1_20260307T040700Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_gap32_long_v1_20260307T040700Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.1359`
- `delta_last_val_loss = -0.6407`

Status:

- confirmed positive

### 8. `task5_realvideo_gap24_long_v1` on `realtriplet_midfirst_gap24`

Why it now ranks eighth:

- this was the rung that proved the larger-gap ladder would keep working on real video
- it remains a strong positive and a clean midpoint in the discovered gap ladder

Evidence:

- [task5_realvideo_gap24_long_v1_20260307T040500Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_gap24_long_v1_20260307T040500Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.1358`
- `delta_last_val_loss = -0.6559`

Status:

- confirmed positive

### 9. `task2_square_hole` on `cifar16_gray_row`

Why it now ranks ninth:

- this is the cleanest spatial inpainting-style task in the archive
- already showed a weak positive signal under longer budget
- useful if we want a more classic "hole filling" visual task

Evidence:

- [task2_long_20260302T044214Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task2_long_20260302T044214Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.0081`

### 10. `realvideo_left=right` positive control

Why it now ranks tenth:

- not a natural task, but a high-value mechanism check
- we already know from MNIST `left=right` and upstream `rightcopy/constr` that copy-style future-dependent tasks expose Future-Seed cleanly

Why it matters:

- if a real-video line becomes ambiguous, this task can tell us whether the issue is the mechanism or the dataset/task geometry
- this needs a small data-generation pass, so it stays below the ready-now candidates

### 11. `task1_left_half` on `cifar16_gray_col`

Why it ranks lower:

- theoretically future-dependent
- empirically flat in the archive
- weaker than the midframe task family

Evidence:

- [coarse_15_20260302T033458Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/coarse_15_20260302T033458Z/summary_agg.json)
- `delta_maskacc_fg_val = 0.0000`

### 12. `moving_mnist_*`

Why it ranks last:

- early runs show degenerate FG behavior (`0.0` or `1.0`)
- metric is not trustworthy enough yet for efficient FS evaluation
- fixing that metric path is extra work before we can trust any result

Evidence:

- [moving_mnist_coarse120_20260302T110339Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/moving_mnist_coarse120_20260302T110339Z/summary_agg.json)
- [moving_mnist_bin2_coarse120_20260302T114400Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/moving_mnist_bin2_coarse120_20260302T114400Z/summary_agg.json)
- [moving_mnist_bin2_fgW8_coarse120_20260302T122607Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/moving_mnist_bin2_fgW8_coarse120_20260302T122607Z/summary_agg.json)

## Current Recommendation

1. `task5` real-video family is now strongly positive across `adjacent`, `gap4`, `gap8`, `gap16`, `gap24`, `gap32`, and `gap40`, and `gap40` has already passed 3-seed confirm
2. the highest-ROI active branch is now `realvideo_square_migration_coarse120_seed20260318_20260308T031506Z`
3. the automatic `gap24 -> gap32 -> gap40` ladder completed cleanly; every rung passed the strong-positive gate
4. do not pivot to `moving_mnist`
