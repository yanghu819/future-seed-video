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

### 3. `realvideo_square_migration` on `realvideo_complex_midfirst`

Why it now ranks third:

- this is not just a new guess; it composes two existing wins
- on video, `realvideo_complex_v1 ratio50 prefix` is already a confirmed positive line
- on image, `prefix-source -> square` migration was a better ROI move than adding more iters

Why it matters:

- it is the cleanest way to test whether the main video prefix success can transfer into a more classic hole-filling setting
- implementation cost is low because `BIN_MASK_MODE=square` already exists and the trainer already auto-loads `WEIGHTS_PATH` if present

Evidence:

- [future-seed-video README.md](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/README.md)
- [fs-impainting CURRENT_STATUS.md](/Users/torusmini/Downloads/autodl3-impainting-fs/fs-impainting/CURRENT_STATUS.md)

Suggested frozen setup:

- source weights: one of the passed `realvideo_complex_v1_ratio50_full150_*` checkpoints
- target task: `realvideo_complex_midfirst` with `BIN_MASK_MODE=square`
- vary only `BIN_SQUARE_SIZE` first; do not change model scale or alpha on the first coarse run

### 4. `task5_realvideo_long` on `realtriplet_midfirst`

Why it ranks fourth:

- same real-video family as candidate 2
- earlier short-budget run also showed a material FS1 loss advantage
- likely cheaper to validate than inventing a new dataset

Evidence:

- [task5_realvideo_20260302T091839Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task5_realvideo_20260302T091839Z/summary_agg.json)
- short run: `delta_maskacc_fg_val = 0.0000`, but `delta_last_val_loss = -0.1535`

### 5. `task5_realvideo_gap8` on `realtriplet_midfirst_gap8`

Why it ranks fifth:

- same task family as the current `gap4` long recheck
- larger temporal gap should make the middle-frame prediction rely more on future context, which is exactly where Future-Seed should help
- this is only medium priority because it requires a small data build from the existing raw video source

Why it matters:

- if `gap4` is weak but not dead, `gap8` is the natural way to amplify future dependence without changing the model

### 6. `task2_square_hole` on `cifar16_gray_row`

Why it ranks sixth:

- this is the cleanest spatial inpainting-style task in the archive
- already showed a weak positive signal under longer budget
- useful if we want a more classic "hole filling" visual task

Evidence:

- [task2_long_20260302T044214Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/task2_long_20260302T044214Z/summary_agg.json)
- `delta_maskacc_fg_val = +0.0081`

### 7. `realvideo_left=right` positive control

Why it ranks seventh:

- not a natural task, but a high-value mechanism check
- we already know from MNIST `left=right` and upstream `rightcopy/constr` that copy-style future-dependent tasks expose Future-Seed cleanly

Why it matters:

- if a real-video line becomes ambiguous, this task can tell us whether the issue is the mechanism or the dataset/task geometry
- this needs a small data-generation pass, so it stays below the ready-now candidates

### 8. `task1_left_half` on `cifar16_gray_col`

Why it ranks lower:

- theoretically future-dependent
- empirically flat in the archive
- weaker than the midframe task family

Evidence:

- [coarse_15_20260302T033458Z summary_agg.json](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/coarse_15_20260302T033458Z/summary_agg.json)
- `delta_maskacc_fg_val = 0.0000`

### 9. `moving_mnist_*`

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
2. if it shows either real FG gain or a persistent loss lead, run `task5_realvideo_long`
3. in parallel planning, prepare `realvideo_square_migration` as the next high-ROI branch because it reuses a confirmed video prefix line and a confirmed `prefix->square` transfer pattern
4. do not pivot to `moving_mnist`; if the real-video midframe family disappoints, use `task2_square_hole` as the cheaper fallback
