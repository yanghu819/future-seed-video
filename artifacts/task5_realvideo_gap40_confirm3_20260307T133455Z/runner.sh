set -euo pipefail
cd /root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed
while pgrep -f "task5_realvideo_gap40_confirm_seed20260314_20260307T133455Z/runner.sh" >/dev/null || pgrep -f "weights/task5_realvideo_gap40_confirm_seed20260314_fs" >/dev/null; do
  sleep 60
done
/root/miniconda3/bin/python - <<PY3
import csv, json
from pathlib import Path
exp_root = Path("/root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed/exp")
agg_dir = exp_root / "task5_realvideo_gap40_confirm3_20260307T133455Z"
agg_dir.mkdir(parents=True, exist_ok=True)
items = [
    (20260312, "task5_realvideo_gap40_long_v1_20260307T105308Z"),
    (20260313, "task5_realvideo_gap40_confirm_seed20260313_20260307T133455Z"),
    (20260314, "task5_realvideo_gap40_confirm_seed20260314_20260307T133455Z"),
]
rows = []
for seed, tag in items:
    data = json.loads((exp_root / tag / "summary_agg.json").read_text())
    row = next(iter(data.values()))
    rows.append({
        "seed": seed,
        "tag": tag,
        "best_maskacc_fg_val_fs0": row["best_maskacc_fg_val_fs0"],
        "best_maskacc_fg_val_fs1": row["best_maskacc_fg_val_fs1"],
        "delta_maskacc_fg_val": row["delta_maskacc_fg_val"],
        "last_val_loss_fs0": row["last_val_loss_fs0"],
        "last_val_loss_fs1": row["last_val_loss_fs1"],
        "delta_last_val_loss": row["delta_last_val_loss"],
    })
with (agg_dir / "summary_rows.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
deltas = [r["delta_maskacc_fg_val"] for r in rows]
loss_deltas = [r["delta_last_val_loss"] for r in rows]
agg = {
    "task5_realvideo_gap40_confirm3": {
        "n_seeds": len(rows),
        "seeds": [r["seed"] for r in rows],
        "avg_delta_maskacc_fg_val": round(sum(deltas) / len(deltas), 4),
        "min_delta_maskacc_fg_val": round(min(deltas), 4),
        "max_delta_maskacc_fg_val": round(max(deltas), 4),
        "avg_delta_last_val_loss": round(sum(loss_deltas) / len(loss_deltas), 4),
        "all_non_negative_fg": all(d >= 0 for d in deltas),
        "pass_rule": all(d >= 0 for d in deltas) and (sum(deltas) / len(deltas) >= 0.10),
    }
}
(agg_dir / "summary_agg.json").write_text(json.dumps(agg, indent=2))
print(json.dumps(agg, indent=2))
PY3
