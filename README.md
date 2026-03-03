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

## Candidate / needs re-check

1. `realvideo_complex_v1_ratio67_coarse150_20260303T132507Z`
- coarse showed `delta_maskacc_fg_val = +0.0263` (early stop)
- but follow-up `confirmlite2` did not reproduce gain

## Pruned / negative lines

1. `realvideo_cross_v1_coarse120_20260303T082857Z`
- cross-scene generalization line
- avg `delta_maskacc_fg_val = 0.0000` (pruned)

2. `realvideo_complex_v1_ratio67_confirmlite2_20260303T165146Z`
- seeds `20260313/20260314`
- avg `delta_maskacc_fg_val = 0.0000` (failed confirm-like rule)

3. `realvideo_complex_v1_scaleM_L4E256_ratio50_coarse120_20260303T160109Z`
- medium scale (`L4/E256`), compared at step40 for FS0/FS1
- `delta_maskacc_fg_val = 0.0000` (pruned)

4. `realvideo_complex_v1_scaleL6E384_ratio50_coarse150_fit_20260303T154725Z`
- large scale (`L6/E384`) too slow under `RWKV7_KERNEL=python`
- hard-stop (`exit_code=143`)

## Content per run
- `summary_rows.csv`
- `summary_agg.json`
- `run_manifest.txt` (if present on remote)
- `logs/*.log`
