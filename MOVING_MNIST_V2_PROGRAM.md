# Moving MNIST v2 Program

This line adopts the useful parts of `karpathy/autoresearch` and drops the parts that do not fit our goal.

## Goal

Find out whether Future-Seed helps on a video task that is visually intuitive enough to demo, while keeping the research loop tight and auditable.

## The adaptation

`autoresearch` is built around three ideas:

1. fixed budget
2. fixed evaluator
3. one small mutable surface

We keep all three, but map them onto the Future-Seed task-discovery problem.

## In-scope files

Read-only / fixed:

- `analysis/build_moving_mnist_v2_bin.py`
- `analysis/eval_moving_mnist_v2.py`
- `analysis/launch_moving_mnist_v2_smoke.py`
- `payload/src/future-seed-main/rwkv-diff-future-seed/rwkv_diff_future_seed.py`

Mutable:

- `analysis/moving_mnist_v2_spec.json`

The rule is simple: if we want to iterate on this line, we change the spec first, not the evaluator and not the trainer.

## Baseline task definition

- dataset: synthetic `Moving MNIST v2`
- frame layout: `middle | left | right`
- frame size: `24 x 24`
- tokenization: binary (`VOCAB_SIZE=2`)
- task: reconstruct the whole missing middle frame from the visible left/right frames
- mask: `prefix: 1/3`
- main metric: `val_middle_iou`
- supporting metrics: `val_middle_f1`, `val_middle_l1`, `val_middle_fg_acc`

## Why this is different from the old Moving MNIST line

The old line relied on the trainer's generic `maskacc_fg` and produced degenerate values (`0.0` or `1.0`).
That line is not trustworthy as evidence.

This v2 line fixes the process problem by freezing a task-specific external evaluator.

It also freezes the execution shape:

- build `.bin` locally
- upload `.bin` to the remote box
- train remotely
- score with the fixed external evaluator

The trainer's in-loop metrics are treated as diagnostics only. Keep / discard decisions come only from the external evaluator.

## Budget

- smoke budget: `MAX_ITERS=120`
- light in-loop eval: `EVAL_ITERS=10`
- coarse budget: `MAX_ITERS=400`
- one GPU only
- one seed for smoke, then expand only if the line looks real

The comparison is always FS0 vs FS1 under the exact same spec.

## Results file

Append one row per completed comparison to:

- `analysis/moving_mnist_v2_results.tsv`

Columns:

- `run_tag`
- `split`
- `seed`
- `metric_iou_fs0`
- `metric_iou_fs1`
- `delta_iou`
- `metric_f1_fs0`
- `metric_f1_fs1`
- `delta_f1`
- `metric_l1_fs0`
- `metric_l1_fs1`
- `delta_l1`
- `status`
- `description`

## Keep / discard rule

- keep if `delta_iou > 0.02` and `delta_l1 < 0`
- discard if `delta_iou <= 0`
- ambiguous if `0 < delta_iou <= 0.02`

## Loop

1. establish the baseline spec and run it once
2. log the results
3. if the line is dead, do not keep mutating the trainer
4. instead, only change one thing in the spec:
   - frame size
   - number of digits
   - motion speed
   - mask geometry
5. rerun under the same evaluator

## Immediate next step

Run the baseline smoke spec in `analysis/moving_mnist_v2_spec.json` and see whether the new evaluator produces a sane signal.
