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

### 4. `task5_realvideo_gap8_long_v1` on `realtriplet_midfirst_gap8`

Why it now ranks fourth:

- it extends the same positive family to a larger temporal gap than `gap4`
- effect size remains large rather than collapsing

Evidence:

- [task5_realvideo_gap8_long_v1_20260307T023000Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_gap8_long_v1_20260307T023000Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.1314`
- `delta_last_val_loss = -0.6836`

Status:

- confirmed positive

### 5. `task5_realvideo_gap4_long_v2` on `realtriplet_midfirst_gap4`

Why it now ranks fifth:

- same structural family as the strong-positive CIFAR `task5_midframe`
- closer to real video interpolation
- the long run is now strongly positive, not just loss-positive

Evidence:

- [task5_realvideo_gap4_long_v2_20260306T135653Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_gap4_long_v2_20260306T135653Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.1305`
- `delta_last_val_loss = -0.6902`

### 6. `task5_realvideo_gap24` on `realtriplet_midfirst_gap24`

Why it now ranks sixth:

- this is the active stronger-gap search branch
- raw window count is still acceptable at `475`, so it is a real task-discovery step rather than a data-starved stunt

Status:

- running as `task5_realvideo_gap24_long_v1_20260307T040500Z`

### 7. `task5_realvideo_gap32` on `realtriplet_midfirst_gap32`

Why it now ranks seventh:

- this is the queued follow-up if `gap24` remains strong
- raw window count is still workable at `443`

Status:

- queued as `task5_realvideo_gap32_long_v1_20260307T040700Z`

### 8. `realvideo_square_migration` on `realvideo_complex_midfirst`

Why it now ranks eighth:

- this is not just a new guess; it composes two existing wins
- on video, `realvideo_complex_v1 ratio50 prefix` is already a confirmed positive line
- on image, `prefix-source -> square` migration was a better ROI move than adding more iters

Why it matters:

- it is the cleanest way to test whether the main video prefix success can transfer into a more classic hole-filling setting
- but it is not `ready-now`: current `BIN_MASK_MODE=square` requires `SEQ_LEN` to be a perfect square, while the current video triplets use `SEQ_LEN=768/1728`
- so this branch needs a small frame-local square-mask patch before it can be run cleanly

Evidence:

- [future-seed-video README.md](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/README.md)
- [fs-impainting CURRENT_STATUS.md](/Users/torusmini/Downloads/autodl3-impainting-fs/fs-impainting/CURRENT_STATUS.md)
- [rwkv_diff_future_seed.py](/Users/torusmini/Downloads/autodl3-impainting-fs/payload/src/future-seed-main/rwkv-diff-future-seed/rwkv_diff_future_seed.py): current `square` branch checks `side * side == SEQ_LEN`

Suggested frozen setup:

- source weights: one of the passed `realvideo_complex_v1_ratio50_full150_*` checkpoints
- target task: `realvideo_complex_midfirst` with `BIN_MASK_MODE=square`
- vary only `BIN_SQUARE_SIZE` first; do not change model scale or alpha on the first coarse run

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

1. `task5` real-video family is now strongly positive across `adjacent`, `gap4`, `gap8`, and `gap16`
2. `task5_realvideo_gap24_long_v1` is running as the next stronger-gap discovery branch
3. `task5_realvideo_gap32_long_v1` is queued behind `gap24`
4. `analysis/task5_gap_watchdog.py` now owns the queue rule: if `gap24` is not strong positive it will cancel `gap32`; if `gap32` is strong positive it will queue `gap40`
5. keep `realvideo_square_migration` on deck, but treat it as a small-code-patch branch rather than an immediate run
6. do not pivot to `moving_mnist`
