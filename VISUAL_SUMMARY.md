# Visual Summary

## 1. Budget Boundary on the Solid Main Line

- Figure: [ratio50_budget_boundary.png](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/ratio50_budget_boundary.png)
- What to look at:
  - `90` steps: essentially no FG gain
  - `120` steps: stable positive FG gain appears
  - `150` steps: gain becomes larger
- Interpretation:
  - this is the cleanest picture for the claim that Future-Seed is budget-triggered on the frozen `realvideo_complex_v1 ratio50` setup

## 2. Strong Positive Real-Video Midframe Family

- Figure: [task5_realvideo_gap4_long_v2_curves.png](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/task5_realvideo_gap4_long_v2_curves.png)
- What to look at:
  - left panel: `maskacc_fg_val` for `FS1` pulls away from `FS0` early and keeps widening
  - right panel: `val_loss` for `FS1` drops much faster and remains much lower
- Final numbers:
  - `best FG: 0.4174 -> 0.5479`
  - `delta FG: +0.1305`
  - `last val loss: 1.9349 -> 1.2447`

## 3. How to Read These Together

- the `ratio50` figure answers: "is the main video result stable and when does it turn on?"
- the `gap4` figure answers: "what does a strong Future-Seed win actually look like over training?"
- together they show two different strengths:
  - one line is **solid and reproducible**
  - one line is **large-effect and highly promising**

## 4. Family-Level Real-Video Gap Ladder

- Figure: [task5_gap_family.png](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/figures/task5_gap_family.png)
- What to look at:
  - left panel: `delta_maskacc_fg_val` stays in the `+0.13` to `+0.15` band from `adjacent` through `gap40`
  - right panel: validation-loss improvement remains large across the same family
- Interpretation:
  - this is the compact view showing the current best claim on the discovery side
  - the `task5` real-video family is not a one-off win; it stays strongly positive across multiple temporal gaps, and `gap40` is now in 3-seed confirm
