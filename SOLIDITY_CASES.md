# Solidity Cases

## What is solid

- `realvideo_complex_v1 ratio50` is solid on the frozen main line: `120-step` is a strict 3-seed positive boundary and `150-step` is a 5-seed positive aggregate.
- `task5 gap40` is solid on the discovery side: 3-seed confirm passes with all non-negative FG deltas.
- `realvideo_square_migration` is now also solid: the 3-seed square-mask transfer confirm passes with all non-negative FG deltas.

## What is strong but not equally solid

- `task5 adjacent` and `task5 gap24` are large single-run wins, but they are still single-run wins.
- `realvideo_square_migration_coarse120` should now be read as the entry point of a branch that later passed confirm, not as a standalone pending result.

## Visual

- Figure: [solid_case_matrix.svg](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/solid_case_matrix.svg)
- Table: [solid_case_matrix.csv](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/solid_case_matrix.csv)

## Anchor cases

1. Main-line solid case: `realvideo_complex_v1_ratio50_full150_multiseed`
   - `avg_delta_maskacc_fg_val = +0.0389`
   - `n_seeds = 5`
   - all seed deltas non-negative

2. Discovery-family solid case: `task5_realvideo_gap40_confirm3`
   - `avg_delta_maskacc_fg_val = +0.1461`
   - `n_seeds = 3`
   - all seed deltas non-negative

3. Transfer solid case: `realvideo_square_migration_confirm3_20260308T123605Z`
   - `avg_delta_maskacc_fg_val = +0.0891`
   - `n_seeds = 3`
   - all seed deltas non-negative
