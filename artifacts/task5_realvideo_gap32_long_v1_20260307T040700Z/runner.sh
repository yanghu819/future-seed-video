set -euo pipefail
cd /root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed
if [ "task5_realvideo_gap24_long_v1_20260307T040500Z" != "none" ]; then
  while pgrep -f "task5_realvideo_gap24_long_v1_20260307T040500Z/runner.sh" >/dev/null || pgrep -f "weights/task5_realvideo_gap32_long_v1_fs" >/dev/null; do
    sleep 60
  done
fi
env PYTHONUNBUFFERED=1 TRAIN=1 MODEL=rwkv RWKV7_KERNEL=python DATA_BIN=/root/autodl-tmp/data/video_interp_smoke/realtriplet_midfirst_gap32_train.bin DATA_VAL_BIN=/root/autodl-tmp/data/video_interp_smoke/realtriplet_midfirst_gap32_val.bin VOCAB_SIZE=16 SEQ_LEN=768 BIN_MASK_MODE=prefix BIN_PREFIX_RATIO=0.333333 MASKACC_EVAL=1 MASKACC_FG_EVAL=1 FG_TOKEN_THRESHOLD=0 MASKACC_ITERS=100 N_LAYER=2 N_EMBD=128 HEAD_SIZE=32 DEVICE_BSZ=64 BATCH_SIZE=128 MAX_ITERS=400 EVAL_INTERVAL=50 RANDOM_SEED=20260311 LOG_SAMPLE=0 LOG_OUTPUT=0 FUTURE_SEED=0 WEIGHTS_PATH=weights/task5_realvideo_gap32_long_v1_fs0_20260307T040700Z.pt /root/miniconda3/bin/python rwkv_diff_future_seed.py | tee exp/task5_realvideo_gap32_long_v1_20260307T040700Z/logs/fs0.log
env PYTHONUNBUFFERED=1 TRAIN=1 MODEL=rwkv RWKV7_KERNEL=python DATA_BIN=/root/autodl-tmp/data/video_interp_smoke/realtriplet_midfirst_gap32_train.bin DATA_VAL_BIN=/root/autodl-tmp/data/video_interp_smoke/realtriplet_midfirst_gap32_val.bin VOCAB_SIZE=16 SEQ_LEN=768 BIN_MASK_MODE=prefix BIN_PREFIX_RATIO=0.333333 MASKACC_EVAL=1 MASKACC_FG_EVAL=1 FG_TOKEN_THRESHOLD=0 MASKACC_ITERS=100 N_LAYER=2 N_EMBD=128 HEAD_SIZE=32 DEVICE_BSZ=64 BATCH_SIZE=128 MAX_ITERS=400 EVAL_INTERVAL=50 RANDOM_SEED=20260311 LOG_SAMPLE=0 LOG_OUTPUT=0 FUTURE_SEED=1 FUTURE_SEED_ALPHA_INIT=-2 WEIGHTS_PATH=weights/task5_realvideo_gap32_long_v1_fs1_20260307T040700Z.pt /root/miniconda3/bin/python rwkv_diff_future_seed.py | tee exp/task5_realvideo_gap32_long_v1_20260307T040700Z/logs/fs1.log
/root/miniconda3/bin/python - <<PY2
import csv, json, re
exp="exp/task5_realvideo_gap32_long_v1_20260307T040700Z"
name="task5_realvideo_gap32_long_v1_20260307T040700Z".split("_")[:-2]
name="_".join(name)
pat_step=re.compile(r"^step\s+(\d+):.*val loss\s+([0-9.]+)")
pat_acc=re.compile(r"^maskacc_val\s+([0-9.]+)")
pat_fg=re.compile(r"^maskacc_fg_val\s+([0-9.]+)")
rows=[]
for fs in [0,1]:
    path=f"{exp}/logs/fs{fs}.log"
    best_acc=-1.0; best_fg=-1.0; last_loss=float("nan")
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
    rows.append({"task":name,"fs":fs,"alpha":-2 if fs==1 else 0,"max_iters":400,"eval_interval":50,"maskacc_iters":100,"best_maskacc_val":round(best_acc,4),"best_maskacc_fg_val":round(best_fg,4),"last_val_loss":round(last_loss,4),"exit_code":0,"log_path":path})
rows.sort(key=lambda x:x["fs"])
agg={name:{
    "best_maskacc_val_fs0": rows[0]["best_maskacc_val"],
    "best_maskacc_val_fs1": rows[1]["best_maskacc_val"],
    "delta_maskacc_val": rows[1]["best_maskacc_val"]-rows[0]["best_maskacc_val"],
    "best_maskacc_fg_val_fs0": rows[0]["best_maskacc_fg_val"],
    "best_maskacc_fg_val_fs1": rows[1]["best_maskacc_fg_val"],
    "delta_maskacc_fg_val": rows[1]["best_maskacc_fg_val"]-rows[0]["best_maskacc_fg_val"],
    "last_val_loss_fs0": rows[0]["last_val_loss"],
    "last_val_loss_fs1": rows[1]["last_val_loss"],
    "delta_last_val_loss": rows[1]["last_val_loss"]-rows[0]["last_val_loss"]
}}
with open(f"{exp}/summary_rows.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(f"{exp}/summary_agg.json","w") as f:
    json.dump(agg,f,indent=2)
print(json.dumps(agg,indent=2))
PY2
