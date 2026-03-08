set -euo pipefail
cd /root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed
while pgrep -f "task5_realvideo_gap40_confirm_seed20260314_20260307T133455Z/runner.sh" >/dev/null || pgrep -f "weights/task5_realvideo_gap40_confirm_seed20260314_fs" >/dev/null; do
  sleep 60
done
mkdir -p exp/realvideo_square_migration_coarse120_seed20260318_20260308T031506Z/logs /root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed/weights
cp "/root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed/weights/rvc1_ratio50_full150_seed20260318_fs0_20260304T122457Z.pt" "/root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed/weights/realvideo_square_migration_coarse120_seed20260318_fs0_20260308T031506Z.pt"
env PYTHONUNBUFFERED=1 TRAIN=1 MODEL=rwkv RWKV7_KERNEL=python DATA_BIN=/root/autodl-tmp/data/video_interp_complex_v1/realvideo_complex_midfirst_train.bin DATA_VAL_BIN=/root/autodl-tmp/data/video_interp_complex_v1/realvideo_complex_midfirst_val.bin VOCAB_SIZE=32 SEQ_LEN=1728 BIN_MASK_MODE=square BIN_SQUARE_FRAME_SIDE=24 BIN_SQUARE_FRAME_INDEX=0 BIN_SQUARE_SIZE=8 BIN_SQUARE_TOP=-1 BIN_SQUARE_LEFT=-1 MASKACC_EVAL=1 MASKACC_FG_EVAL=1 FG_TOKEN_THRESHOLD=2 N_LAYER=3 N_EMBD=192 HEAD_SIZE=32 DEVICE_BSZ=24 BATCH_SIZE=96 MAX_ITERS=120 EVAL_INTERVAL=30 MASKACC_ITERS=50 RANDOM_SEED=20260318 LOG_SAMPLE=0 LOG_OUTPUT=0 FUTURE_SEED=0 WEIGHTS_PATH="/root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed/weights/realvideo_square_migration_coarse120_seed20260318_fs0_20260308T031506Z.pt" /root/miniconda3/bin/python rwkv_diff_future_seed.py | tee exp/realvideo_square_migration_coarse120_seed20260318_20260308T031506Z/logs/fs0.log
cp "/root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed/weights/rvc1_ratio50_full150_seed20260318_fs1_20260304T122457Z.pt" "/root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed/weights/realvideo_square_migration_coarse120_seed20260318_fs1_20260308T031506Z.pt"
env PYTHONUNBUFFERED=1 TRAIN=1 MODEL=rwkv RWKV7_KERNEL=python DATA_BIN=/root/autodl-tmp/data/video_interp_complex_v1/realvideo_complex_midfirst_train.bin DATA_VAL_BIN=/root/autodl-tmp/data/video_interp_complex_v1/realvideo_complex_midfirst_val.bin VOCAB_SIZE=32 SEQ_LEN=1728 BIN_MASK_MODE=square BIN_SQUARE_FRAME_SIDE=24 BIN_SQUARE_FRAME_INDEX=0 BIN_SQUARE_SIZE=8 BIN_SQUARE_TOP=-1 BIN_SQUARE_LEFT=-1 MASKACC_EVAL=1 MASKACC_FG_EVAL=1 FG_TOKEN_THRESHOLD=2 N_LAYER=3 N_EMBD=192 HEAD_SIZE=32 DEVICE_BSZ=24 BATCH_SIZE=96 MAX_ITERS=120 EVAL_INTERVAL=30 MASKACC_ITERS=50 RANDOM_SEED=20260318 LOG_SAMPLE=0 LOG_OUTPUT=0 FUTURE_SEED=1 FUTURE_SEED_ALPHA_INIT=-2 WEIGHTS_PATH="/root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed/weights/realvideo_square_migration_coarse120_seed20260318_fs1_20260308T031506Z.pt" /root/miniconda3/bin/python rwkv_diff_future_seed.py | tee exp/realvideo_square_migration_coarse120_seed20260318_20260308T031506Z/logs/fs1.log
/root/miniconda3/bin/python - <<PY2
import csv, json, re
exp="exp/realvideo_square_migration_coarse120_seed20260318_20260308T031506Z"
name="realvideo_square_migration_coarse120"
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
    rows.append({"task":name,"fs":fs,"alpha":-2 if fs==1 else 0,"init":"ratio50_full150_seed20260318","max_iters":120,"eval_interval":30,"maskacc_iters":50,"best_maskacc_val":round(best_acc,4),"best_maskacc_fg_val":round(best_fg,4),"last_val_loss":round(last_loss,4),"exit_code":0,"log_path":path})
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
