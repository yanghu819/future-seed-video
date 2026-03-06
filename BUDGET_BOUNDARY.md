# Ratio50 Budget Boundary

## Scope

This note isolates the strongest conclusion currently supported by the `future-seed-video` archive:

- task line: `realvideo_complex_v1`
- data: `realvideo_complex_midfirst`
- mask: `prefix:0.5`
- model: `L3/E192/H32`
- vocab: `32`
- seq_len: `1728`
- batch: `device_bsz=24`, `batch=96`
- comparison: `FS0` vs `FS1(alpha=-2)`
- primary metric: `maskacc_fg_val`

The question is not whether Future-Seed helps "video" in general.
The question is narrower:

Can Future-Seed produce a stable foreground recovery gain on this frozen `ratio50` line, and if so, at what training budget does that gain first appear?

## Strict Comparable Evidence

The cleanest evidence comes from budgets `90` and `120`, where the runs share the same task, model, mask, and eval cadence (`eval_interval=30`, `eval_iters=10`, `maskacc_iters=20`).

| Budget | Seeds | Avg delta FG | Range | Result |
|---|---:|---:|---:|---|
| 90 | 3 | +0.0000 | 0.0000 to 0.0000 | no gain |
| 120 | 3 | +0.0249 | +0.0241 to +0.0254 | stable gain |

Sources:

- [budgetcurve seed20260320](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/realvideo_complex_v1_ratio50_budgetcurve_seed20260320_20260305T061022Z/summary_agg.json)
- [boundaryconfirm2](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/realvideo_complex_v1_ratio50_boundaryconfirm2_20260305T112958Z/summary_agg.json)

This is the main boundary claim:

- `90` steps: no measurable Future-Seed gain across 3 seeds.
- `120` steps: Future-Seed gain appears and is stable across 3 seeds.

## Supporting Evidence

Two additional budgets strengthen the interpretation, but they are not as cleanly matched as the `90/120` subset.

| Budget | Seeds | Avg delta FG | Evidence tier | Caveat |
|---|---:|---:|---|---|
| 60 | 4 | +0.0000 | supporting | lite runs use `eval_interval=20` in one group and `30` in another |
| 150 | 5 | +0.0389 | supporting | full-budget aggregate uses `maskacc_iters=50` |

Sources:

- [confirmlite3](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/realvideo_complex_v1_ratio50_confirmlite3_20260303T234917Z/summary_agg.json)
- [full150 multiseed aggregate](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/artifacts/realvideo_complex_v1_ratio50_full150_multiseed_agg_20260305T030102Z/summary_agg.json)

These runs support the same shape:

- `60` steps: still no gain.
- `150` steps: larger and highly repeatable gain.

## Interpretation

The current evidence supports a budget-triggered effect:

1. Future-Seed does not help at very short budgets on this line.
2. The gain turns on between `90` and `120` steps.
3. The gain grows further by `150` steps.

This is more precise than saying "FS works" or "FS does not work."
The supported statement is:

Future-Seed yields a stable positive `maskacc_fg_val` delta on the frozen `ratio50` video line, but only after the training budget crosses a threshold near `120` steps.

## Claims We Can Defend

1. `ratio50` under low budget (`60/90`) is effectively a no-gain regime.
2. `ratio50` at `120+` is a positive-gain regime.
3. `150` has the strongest current evidence base.

## Claims We Should Not Make

1. Do not generalize this to all video tasks.
2. Do not generalize this to `ratio67`; that line did not hold frozen rechecks.
3. Do not claim cross-scene generalization; the current cross-scene run is negative.

## Recommended Next Step

If the goal is publication-quality evidence, the next high-value step is not another broad sweep.
It is a compact figure/table package built around this boundary:

1. `budget -> delta_maskacc_fg_val`
2. `budget -> delta_maskacc_val`
3. one qualitative FS0/FS1 reconstruction pair from `90` and `120`

The numeric summary used in this note is also exported as:

- [ratio50_budget_boundary_summary.csv](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/ratio50_budget_boundary_summary.csv)
