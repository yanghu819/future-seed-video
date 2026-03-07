# future-seed-video backup

Last backup time: 2026-03-07 (local)
Source host: `connect.bjb2.seetacloud.com:19708`

## Confirmed positive runs

1. `realvideo_complex_v1_confirm2_20260302T182340Z`
- 2 seeds pass
- avg `delta_maskacc_fg_val = +0.0292`

2. `realvideo_complex_v1_ratio50_confirm_20260303T043332Z`
- 2 seeds pass
- avg `delta_maskacc_fg_val = +0.0408`

3. `realvideo_complex_v1_ratio50_full150_seed20260317_20260304T092527Z`
- full-budget single-seed recheck (new seed)
- `delta_maskacc_fg_val = +0.0332` (pass)

4. `realvideo_complex_v1_ratio50_full150_seed20260318_20260304T122457Z`
- full-budget single-seed recheck (new seed)
- `delta_maskacc_fg_val = +0.0405` (pass)

5. `realvideo_complex_v1_ratio50_full150_seed20260319_20260305T000359Z`
- full-budget single-seed recheck (new seed)
- `delta_maskacc_fg_val = +0.0392` (pass)

6. `realvideo_complex_v1_ratio50_full150_multiseed_agg_20260305T030102Z`
- aggregated comparable full150 seeds: `20260306/20260307/20260317/20260318/20260319`
- avg `delta_maskacc_fg_val = +0.0389`
- all seed deltas non-negative

7. `realvideo_complex_v1_ratio50_budgetcurve_seed20260320_20260305T061022Z`
- budget boundary curve on one new seed (`60/90/120/150`)
- first budget passing `delta_fg>=0.015` is **120**
- deltas: `60:+0.0000, 90:+0.0000, 120:+0.0241, 150:+0.0354`

8. `realvideo_complex_v1_ratio50_boundaryconfirm2_20260305T112958Z`
- multi-seed boundary confirmation on new seeds `20260321/20260322`
- budget `90`: avg `delta_maskacc_fg_val = +0.0000`
- budget `120`: avg `delta_maskacc_fg_val = +0.02525`
- confirms the gain transition happens between **90** and **120**

9. `task5_realvideo_gap4_long_v2_20260306T135653Z`
- strong positive on the real-video midframe family
- `best_maskacc_fg_val`: FS0 `0.4174` -> FS1 `0.5479`
- `delta_maskacc_fg_val = +0.1305`
- `delta_last_val_loss = -0.6902`

10. `task5_realvideo_long_v2_20260307T014857Z`
- strong positive on the adjacent-context real-video midframe family
- `best_maskacc_fg_val`: FS0 `0.4010` -> FS1 `0.5505`
- `delta_maskacc_fg_val = +0.1495`
- `delta_last_val_loss = -0.7089`

11. `task5_realvideo_gap8_long_v1_20260307T023000Z`
- strong positive on the larger-gap real-video midframe family
- `best_maskacc_fg_val`: FS0 `0.4518` -> FS1 `0.5832`
- `delta_maskacc_fg_val = +0.1314`
- `delta_last_val_loss = -0.6836`

12. `task5_realvideo_gap16_long_v1_20260307T032500Z`
- strong positive on the much-larger-gap real-video midframe family
- `best_maskacc_fg_val`: FS0 `0.4100` -> FS1 `0.5629`
- `delta_maskacc_fg_val = +0.1529`
- `delta_last_val_loss = -0.6820`

13. `task5_realvideo_gap24_long_v1_20260307T040500Z`
- strong positive on the still-larger-gap real-video midframe family
- `best_maskacc_fg_val`: FS0 `0.4327` -> FS1 `0.5685`
- `delta_maskacc_fg_val = +0.1358`
- `delta_last_val_loss = -0.6559`

## Step-Extension Probes

1. `realvideo_complex_v1_ratio50_scratch180_seed20260320_20260306T040234Z`
- exploratory longer-budget scratch rerun on the `budgetcurve` line (`maskacc_iters=20`)
- `best_fg_fs0 = 0.0548`, `best_fg_fs1 = 0.0980`
- `delta_fg_180 = +0.0432`
- compared to the same-seed `150-step` reference (`+0.0354`), this is `+0.0078` higher
- treat this as supportive, not final: step-extension still needs a more directly comparable rerun on the full150 setting

2. `realvideo_complex_v1_ratio50_fullcfg180_seed20260318_20260306T061017Z`
- directly comparable extension of `full150 seed20260318` to `180` steps
- `best_fg_fs0 = 0.0538`, `best_fg_fs1 = 0.0964`
- `delta_fg_180 = +0.0426`
- compared to the `150-step` reference (`+0.0405`), this is only `+0.0021` higher
- current interpretation: `180` is at most a small marginal gain over `150`, not a new regime change

## Pruned / negative lines

1. `realvideo_cross_v1_coarse120_20260303T082857Z`
- cross-scene generalization line
- avg `delta_maskacc_fg_val = 0.0000` (pruned)

2. `realvideo_complex_v1_ratio67_confirmlite2_20260303T165146Z`
- seeds `20260313/20260314`
- avg `delta_maskacc_fg_val = 0.0000` (failed confirm-like rule)

3. `realvideo_complex_v1_ratio67_seed20260310_recheck_20260303T182041Z`
- same seed used in earlier coarse-positive report (`20260310`) but with frozen recheck config
- `delta_maskacc_fg_val = 0.0000` (non-reproducible)

4. `realvideo_complex_v1_ratio50_confirmlite3_20260303T234917Z`
- calibration seed + two new seeds: `20260306/20260315/20260316`
- avg `delta_maskacc_fg_val = 0.0000` (failed under 60-step lite budget)

5. `realvideo_complex_v1_scaleM_L4E256_ratio50_coarse120_20260303T160109Z`
- medium scale (`L4/E256`), compared at step40 for FS0/FS1
- `delta_maskacc_fg_val = 0.0000` (pruned)

6. `realvideo_complex_v1_scaleL6E384_ratio50_coarse150_fit_20260303T154725Z`
- large scale (`L6/E384`) too slow under `RWKV7_KERNEL=python`
- hard-stop (`exit_code=143`)

## Notes
- `realvideo_complex_v1_ratio67_coarse150_20260303T132507Z` showed one-off coarse positive (`+0.0263`), but follow-up frozen rechecks did not hold.
- `ratio50` is budget-sensitive: 60/90-step runs show no gain, while 120/150-step runs show clear positive delta.
- The 90->120 transition is now supported by both single-seed and multi-seed evidence.
- Checkpoint continuation is not a valid proxy for longer budgets on this line; a `120->150` resume probe underestimates FS1 versus scratch.
- Extending from `150` to `180` looks like, at best, a small marginal gain. This is not currently a high-ROI direction compared with new task discovery.

## Analysis Docs
- [BUDGET_BOUNDARY.md](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/BUDGET_BOUNDARY.md): formal note for the `ratio50` budget threshold claim.
- [VISUAL_SUMMARY.md](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/VISUAL_SUMMARY.md): quick figure guide for the main solid line and the strong `gap4` positive line.
- [TASK_CANDIDATES.md](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/TASK_CANDIDATES.md): ranked list of likely next effective tasks.
- [task_candidate_scoreboard.csv](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/task_candidate_scoreboard.csv): sortable evidence table for ready-now and derived candidate tasks.
- [ratio50_budget_boundary_summary.csv](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/ratio50_budget_boundary_summary.csv): compact numeric table behind that note.
- [ratio50_budget_boundary_caption.md](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/ratio50_budget_boundary_caption.md): paper-style caption text for the budget figure.
- [ratio50_budget_boundary.png](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/ratio50_budget_boundary.png): raster figure for slides/docs.
- [ratio50_budget_boundary.svg](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/ratio50_budget_boundary.svg): vector figure for paper/export.
- [task5_realvideo_gap4_long_v2_curves.png](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/task5_realvideo_gap4_long_v2_curves.png): training-curve comparison of `FS0` vs `FS1` on the strong `gap4` real-video task.
- [task5_realvideo_gap4_long_v2_curves.svg](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/task5_realvideo_gap4_long_v2_curves.svg): vector version of that curve figure.
- [task5_gap_family_summary.csv](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/task5_gap_family_summary.csv): compact numeric table for the confirmed real-video `task5` family through `gap24`.
- [task5_gap_family_caption.md](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/task5_gap_family_caption.md): paper-style caption text for the family-level figure.
- [task5_gap_family.png](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/task5_gap_family.png): family-level bar figure for `adjacent/gap4/gap8/gap16/gap24`.
- [task5_gap_family.svg](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/task5_gap_family.svg): vector version of that family-level figure.
- [plot_ratio50_budget_boundary.py](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/plot_ratio50_budget_boundary.py): no-dependency plot generator using `Pillow`.
- [plot_task5_gap4_curves.py](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/plot_task5_gap4_curves.py): no-dependency curve plot generator for the strong `gap4` task.
- [plot_task5_gap_family.py](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/plot_task5_gap_family.py): no-dependency figure generator for the confirmed real-video `task5` gap ladder.
- [task5_gap_watchdog.py](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/task5_gap_watchdog.py): remote watchdog that enforces the `gap24 -> gap32 -> gap40` queue rule and cancels downstream gaps if the previous one fails the strong-positive gate.

## Content per run
- `summary_rows.csv`
- `summary_agg.json`
- `run_manifest.txt` (if present on remote)
- `logs/*.log`

## Current Search Focus
- keep extending the already-strong `task5_midframe` family into more realistic real-video variants
- `task5_realvideo_gap4_long_v2`, `task5_realvideo_long_v2`, `task5_realvideo_gap8_long_v1`, `task5_realvideo_gap16_long_v1`, and `task5_realvideo_gap24_long_v1` are all now confirmed positives
- `task5_realvideo_gap32_long_v1_20260307T040700Z` is now the active stronger-gap branch; current `fs0` has already reached `step 150` with `maskacc_fg_val = 0.3865`
- `analysis/task5_gap_watchdog.py` is now used to keep the queue honest: `gap24` already passed, so `gap32` stays live; if `gap32` is strong positive, the watchdog will queue `gap40`
- treat `realvideo_square_migration` as a high-ROI derived branch that needs a small frame-local square-mask patch before it is runnable
