# future-seed-video backup

Last backup time: 2026-03-06 (local)
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

## Analysis Docs
- [BUDGET_BOUNDARY.md](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/BUDGET_BOUNDARY.md): formal note for the `ratio50` budget threshold claim.
- [ratio50_budget_boundary_summary.csv](/Users/torusmini/Downloads/autodl3-impainting-fs/future-seed-video/analysis/ratio50_budget_boundary_summary.csv): compact numeric table behind that note.

## Content per run
- `summary_rows.csv`
- `summary_agg.json`
- `run_manifest.txt` (if present on remote)
- `logs/*.log`
