set -euo pipefail
cd /root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed
/root/miniconda3/bin/python rwkv_diff_future_seed.py </dev/null >/dev/null 2>/dev/null || true
env PYTHONUNBUFFERED=1 TRAIN=1 MODEL=rwkv RWKV7_KERNEL=python DATA_BIN=/root/autodl-tmp/data/video_interp_complex_v1/realvideo_complex_midfirst_train.bin DATA_VAL_BIN=/root/autodl-tmp/data/video_interp_complex_v1/realvideo_complex_midfirst_val.bin VOCAB_SIZE=32 SEQ_LEN=1728 BIN_MASK_MODE=prefix BIN_PREFIX_RATIO=0.5 MASKACC_EVAL=1 MASKACC_FG_EVAL=1 FG_TOKEN_THRESHOLD=2 N_LAYER=3 N_EMBD=192 HEAD_SIZE=32 DEVICE_BSZ=24 BATCH_SIZE=96 MAX_ITERS=180 EVAL_INTERVAL=30 EVAL_ITERS=10 MASKACC_ITERS=20 RANDOM_SEED=20260320 LOG_SAMPLE=0 LOG_OUTPUT=0 FUTURE_SEED=0 WEIGHTS_PATH=weights/rvc1_ratio50_scratch180_seed20260320_fs0_20260306T040234Z.pt /root/miniconda3/bin/python rwkv_diff_future_seed.py | tee exp/realvideo_complex_v1_ratio50_scratch180_seed20260320_20260306T040234Z/logs/fs0.log
env PYTHONUNBUFFERED=1 TRAIN=1 MODEL=rwkv RWKV7_KERNEL=python DATA_BIN=/root/autodl-tmp/data/video_interp_complex_v1/realvideo_complex_midfirst_train.bin DATA_VAL_BIN=/root/autodl-tmp/data/video_interp_complex_v1/realvideo_complex_midfirst_val.bin VOCAB_SIZE=32 SEQ_LEN=1728 BIN_MASK_MODE=prefix BIN_PREFIX_RATIO=0.5 MASKACC_EVAL=1 MASKACC_FG_EVAL=1 FG_TOKEN_THRESHOLD=2 N_LAYER=3 N_EMBD=192 HEAD_SIZE=32 DEVICE_BSZ=24 BATCH_SIZE=96 MAX_ITERS=180 EVAL_INTERVAL=30 EVAL_ITERS=10 MASKACC_ITERS=20 RANDOM_SEED=20260320 LOG_SAMPLE=0 LOG_OUTPUT=0 FUTURE_SEED=1 FUTURE_SEED_ALPHA_INIT=-2 WEIGHTS_PATH=weights/rvc1_ratio50_scratch180_seed20260320_fs1_20260306T040234Z.pt /root/miniconda3/bin/python rwkv_diff_future_seed.py | tee exp/realvideo_complex_v1_ratio50_scratch180_seed20260320_20260306T040234Z/logs/fs1.log
/root/miniconda3/bin/python - <<PY2
import csv, json, re
exp="exp/realvideo_complex_v1_ratio50_scratch180_seed20260320_20260306T040234Z"
pat_step=re.compile(r"^step\s+(\d+):.*val loss\s+([0-9.]+)")
pat_acc=re.compile(r"^maskacc_val\s+([0-9.]+)")
pat_fg=re.compile(r"^maskacc_fg_val\s+([0-9.]+)")
rows=[]
for fs in [0,1]:
    path=f"{exp}/logs/fs{fs}.log"
    best_acc=-1.0; best_fg=-1.0; last_loss=float('nan')
    with open(path) as f:
        lines=f.readlines()
    i=0
    while i < len(lines):
        m=pat_step.match(lines[i].strip())
        if m:
            last_loss=float(m.group(2))
            if i+2 < len(lines):
                m1=pat_acc.match(lines[i+1].strip()); m2=pat_fg.match(lines[i+2].strip())
                if m1 and m2:
                    best_acc=max(best_acc,float(m1.group(1)))
                    best_fg=max(best_fg,float(m2.group(1)))
        i += 1
    rows.append({"seed":20260320,"fs":fs,"max_iters":180,"best_maskacc_val":round(best_acc,4),"best_maskacc_fg_val":round(best_fg,4),"last_val_loss":round(last_loss,4),"exit_code":0,"log_path":path})
rows.sort(key=lambda x:x['fs'])
agg={
  "seed":20260320,
  "best_fg_fs0": rows[0]['best_maskacc_fg_val'],
  "best_fg_fs1": rows[1]['best_maskacc_fg_val'],
  "delta_fg_180": rows[1]['best_maskacc_fg_val']-rows[0]['best_maskacc_fg_val'],
  "ref_best_fg_fs0_150": 0.0548,
  "ref_best_fg_fs1_150": 0.0902,
  "ref_delta_fg_150": 0.0354,
  "delta_vs_ref_delta": (rows[1]['best_maskacc_fg_val']-rows[0]['best_maskacc_fg_val'])-0.0354,
}
with open(f"{exp}/summary_rows.csv","w",newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
with open(f"{exp}/summary_agg.json","w") as f:
    json.dump({"realvideo_complex_v1_ratio50_scratch180_seed20260320":agg},f,indent=2)
print(json.dumps(agg, indent=2))
PY2
