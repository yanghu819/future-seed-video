# future-seed-video backup

Last backup time: 2026-03-04 (local)
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
- `ratio50` is strongly budget-sensitive: 60-step runs show no gain, while full 150-step runs repeatedly show clear positive delta.

## Content per run
- `summary_rows.csv`
- `summary_agg.json`
- `run_manifest.txt` (if present on remote)
- `logs/*.log`
