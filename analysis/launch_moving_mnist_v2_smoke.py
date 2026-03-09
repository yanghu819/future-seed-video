#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import shlex
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('/Users/torusmini/Downloads/autodl3-impainting-fs')
DOCS = ROOT / 'future-seed-video'
SPEC = DOCS / 'analysis' / 'moving_mnist_v2_spec.json'
RESULTS = DOCS / 'analysis' / 'moving_mnist_v2_results.tsv'
REMOTE = 'root@connect.bjb2.seetacloud.com'
SSH_PORT = '19708'
SSH_KEY = str(Path.home() / '.ssh' / 'autodl_ed25519')
SSH_BASE = ['ssh', '-i', SSH_KEY, '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=no', '-p', SSH_PORT]
SCP_BASE = ['scp', '-P', SSH_PORT, '-i', SSH_KEY, '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=no']
REMOTE_EXP_ROOT = '/root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed'
REMOTE_DATA_DIR = '/root/autodl-tmp/data/moving_mnist_v2'
REMOTE_EVAL = '/root/eval_moving_mnist_v2.py'
REMOTE_TRAINER = f'{REMOTE_EXP_ROOT}/rwkv_diff_future_seed.py'


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def qq(s: str) -> str:
    return shlex.quote(str(s))


def append_results(run_tag: str, seed: int, agg: dict) -> None:
    row = {
        'run_tag': run_tag,
        'split': 'val',
        'seed': str(seed),
        'metric_iou_fs0': f"{agg['metric_iou_fs0']:.6f}",
        'metric_iou_fs1': f"{agg['metric_iou_fs1']:.6f}",
        'delta_iou': f"{agg['delta_iou']:.6f}",
        'metric_f1_fs0': f"{agg['metric_f1_fs0']:.6f}",
        'metric_f1_fs1': f"{agg['metric_f1_fs1']:.6f}",
        'delta_f1': f"{agg['delta_f1']:.6f}",
        'metric_l1_fs0': f"{agg['metric_l1_fs0']:.6f}",
        'metric_l1_fs1': f"{agg['metric_l1_fs1']:.6f}",
        'delta_l1': f"{agg['delta_l1']:.6f}",
        'status': 'keep' if agg['delta_iou'] > 0.02 and agg['delta_l1'] < 0 else ('discard' if agg['delta_iou'] <= 0 else 'ambiguous'),
        'description': 'autoresearch-style moving_mnist_v2 smoke',
    }
    with RESULTS.open() as f:
        reader = csv.DictReader(f, delimiter='\t')
        fields = reader.fieldnames
        rows = list(reader)
    rows = [r for r in rows if r['run_tag'] != run_tag]
    rows.append(row)
    with RESULTS.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    spec = json.loads(SPEC.read_text())
    run_tag = spec['run_tag']
    remote_run = f'/root/{run_tag}.sh'
    local_art = DOCS / 'artifacts' / run_tag
    local_data = local_art / 'data_local'
    local_art.mkdir(parents=True, exist_ok=True)

    mask_mode = spec['mask_mode']
    if mask_mode == 'prefix':
        mask_fixed = 'mask:prefix:$PREFIX_RATIO'
        mask_train_env = 'BIN_MASK_MODE=prefix BIN_PREFIX_RATIO="$PREFIX_RATIO"'
        extra_mask_lines: list[str] = [f'PREFIX_RATIO={float(spec["prefix_ratio"])}']
    elif mask_mode == 'square':
        mask_fixed = 'mask:square:frame$SQUARE_FRAME_INDEX:side$SQUARE_SIZE'
        mask_train_env = (
            'BIN_MASK_MODE=square BIN_SQUARE_SIZE="$SQUARE_SIZE" '
            'BIN_SQUARE_FRAME_SIDE="$SQUARE_FRAME_SIDE" BIN_SQUARE_FRAME_INDEX="$SQUARE_FRAME_INDEX"'
        )
        extra_mask_lines = [
            f'SQUARE_SIZE={int(spec["square_size"])}',
            f'SQUARE_FRAME_SIDE={int(spec["square_frame_side"])}',
            f'SQUARE_FRAME_INDEX={int(spec.get("square_frame_index", 0))}',
        ]
    else:
        raise ValueError(f'unsupported mask_mode: {mask_mode}')

    run([
        'python3',
        str(DOCS / 'analysis' / 'build_moving_mnist_v2_bin.py'),
        '--out-dir', str(local_data),
        '--img-size', str(int(spec['img_size'])),
        '--num-digits', str(int(spec['num_digits'])),
        '--digit-size-min', str(int(spec['digit_size_min'])),
        '--digit-size-max', str(int(spec['digit_size_max'])),
        '--speed-min', str(float(spec['speed_min'])),
        '--speed-max', str(float(spec['speed_max'])),
        '--train-samples', str(int(spec['train_samples'])),
        '--val-samples', str(int(spec['val_samples'])),
        '--seed', str(int(spec['random_seed'])),
    ])
    run(SSH_BASE + [REMOTE, f'mkdir -p {qq(REMOTE_DATA_DIR)}'])
    run(SCP_BASE + [str(local_data / 'moving_mnist_v2_train.bin'), f'{REMOTE}:{REMOTE_DATA_DIR}/moving_mnist_v2_train.bin'])
    run(SCP_BASE + [str(local_data / 'moving_mnist_v2_val.bin'), f'{REMOTE}:{REMOTE_DATA_DIR}/moving_mnist_v2_val.bin'])
    run(SCP_BASE + [str(DOCS / 'analysis' / 'eval_moving_mnist_v2.py'), f'{REMOTE}:{REMOTE_EVAL}'])

    lines = [
        '#!/usr/bin/env bash',
        'set -euo pipefail',
        f'RUN_TAG={qq(run_tag)}',
        'export RUN_TAG',
        f'REMOTE_DATA_DIR={qq(REMOTE_DATA_DIR)}',
        f'REMOTE_EXP_ROOT={qq(REMOTE_EXP_ROOT)}',
        f'REMOTE_EVAL={qq(REMOTE_EVAL)}',
        f'REMOTE_TRAINER={qq(REMOTE_TRAINER)}',
        f'IMG_SIZE={int(spec["img_size"])}',
        f'VOC={int(spec["vocab_size"])}',
        f'TRAIN_SAMPLES={int(spec["train_samples"])}',
        f'VAL_SAMPLES={int(spec["val_samples"])}',
        f'SEED={int(spec["random_seed"])}',
        f'NUM_DIGITS={int(spec["num_digits"])}',
        f'DIGIT_SIZE_MIN={int(spec["digit_size_min"])}',
        f'DIGIT_SIZE_MAX={int(spec["digit_size_max"])}',
        f'SPEED_MIN={float(spec["speed_min"])}',
        f'SPEED_MAX={float(spec["speed_max"])}',
        f'SEQ_LEN={int(spec["seq_len"])}',
        f'N_LAYER={int(spec["n_layer"])}',
        f'N_EMBD={int(spec["n_embd"])}',
        f'HEAD_SIZE={int(spec["head_size"])}',
        f'DEVICE_BSZ={int(spec["device_bsz"])}',
        f'BATCH_SIZE={int(spec["batch_size"])}',
        f'MAX_ITERS={int(spec["max_iters"])}',
        f'EVAL_INTERVAL={int(spec["eval_interval"])}',
        f'EVAL_ITERS={int(spec["eval_iters"])}',
        f'MASKACC_ITERS={int(spec["maskacc_iters"])}',
        f'EVAL_SAMPLES={int(spec["eval_samples"])}',
        f'ALPHA={float(spec["future_seed_alpha_init"])}',
        *extra_mask_lines,
        'mkdir -p "$REMOTE_DATA_DIR" "$REMOTE_EXP_ROOT/exp/$RUN_TAG/logs"',
        'cat > "$REMOTE_EXP_ROOT/exp/$RUN_TAG/run_manifest.txt" <<MANIFEST',
        'objective=autoresearch_moving_mnist_v2_smoke',
        'metric=val_middle_iou',
        'threshold_keep=delta_iou_gt_0.02_and_delta_l1_lt_0',
        f'fixed=img_size:$IMG_SIZE,vocab:2,seq_len:$SEQ_LEN,{mask_fixed},n_layer:$N_LAYER,n_embd:$N_EMBD,head:$HEAD_SIZE,device_bsz:$DEVICE_BSZ,batch:$BATCH_SIZE,max_iters:$MAX_ITERS,eval_interval:$EVAL_INTERVAL,eval_iters:$EVAL_ITERS,train_maskacc:off,seed:$SEED',
        'mutable=analysis/moving_mnist_v2_spec.json',
        'MANIFEST',
        'cd "$REMOTE_EXP_ROOT"',
        'mkdir -p weights',
        'for FS in 0 1; do',
        '  WT="weights/${RUN_TAG}_fs${FS}.pt"',
        '  LOG="exp/${RUN_TAG}/logs/fs${FS}.log"',
        '  EXTRA=()',
        '  if [ "$FS" = "1" ]; then EXTRA=("FUTURE_SEED_ALPHA_INIT=$ALPHA"); fi',
        '  env PYTHONUNBUFFERED=1 TRAIN=1 MODEL=rwkv RWKV7_KERNEL=python \\',
        '    DATA_BIN="$REMOTE_DATA_DIR/moving_mnist_v2_train.bin" \\',
        '    DATA_VAL_BIN="$REMOTE_DATA_DIR/moving_mnist_v2_val.bin" \\',
        f'    VOCAB_SIZE="$VOC" SEQ_LEN="$SEQ_LEN" {mask_train_env} \\',
        '    EVAL_ITERS="$EVAL_ITERS" MASKACC_EVAL=0 MASKACC_FG_EVAL=0 FG_TOKEN_THRESHOLD=0 MASKACC_ITERS="$MASKACC_ITERS" \\',
        '    N_LAYER="$N_LAYER" N_EMBD="$N_EMBD" HEAD_SIZE="$HEAD_SIZE" \\',
        '    DEVICE_BSZ="$DEVICE_BSZ" BATCH_SIZE="$BATCH_SIZE" MAX_ITERS="$MAX_ITERS" EVAL_INTERVAL="$EVAL_INTERVAL" \\',
        '    RANDOM_SEED="$SEED" LOG_SAMPLE=0 LOG_OUTPUT=0 FUTURE_SEED="$FS" "${EXTRA[@]}" \\',
        '    WEIGHTS_PATH="$WT" /root/miniconda3/bin/python "$REMOTE_TRAINER" | tee "$LOG"',
        '  /root/miniconda3/bin/python "$REMOTE_EVAL" \\',
        '    --trainer "$REMOTE_TRAINER" \\',
        '    --data-bin "$REMOTE_DATA_DIR/moving_mnist_v2_val.bin" \\',
        '    --weights "$WT" \\',
        '    --out-json "exp/${RUN_TAG}/eval_fs${FS}.json" \\',
        '    --voc "$VOC" --seq-len "$SEQ_LEN" --frame-side "$IMG_SIZE" --frame-count 3 \\',
        '    --n-layer "$N_LAYER" --n-embd "$N_EMBD" --head-size "$HEAD_SIZE" \\',
        '    --prefix-ratio "$PREFIX_RATIO" --eval-samples "$EVAL_SAMPLES" --seed "$SEED"',
        'done',
        "/root/miniconda3/bin/python - <<'PY'",
        'import json, pathlib, os',
        "run_tag = os.environ['RUN_TAG']",
        "exp = pathlib.Path('exp') / run_tag",
        "fs0 = json.loads((exp/'eval_fs0.json').read_text())",
        "fs1 = json.loads((exp/'eval_fs1.json').read_text())",
        'agg = {',
        '  run_tag: {',
        "    'metric_iou_fs0': fs0['val_middle_iou'],",
        "    'metric_iou_fs1': fs1['val_middle_iou'],",
        "    'delta_iou': fs1['val_middle_iou'] - fs0['val_middle_iou'],",
        "    'metric_f1_fs0': fs0['val_middle_f1'],",
        "    'metric_f1_fs1': fs1['val_middle_f1'],",
        "    'delta_f1': fs1['val_middle_f1'] - fs0['val_middle_f1'],",
        "    'metric_l1_fs0': fs0['val_middle_l1'],",
        "    'metric_l1_fs1': fs1['val_middle_l1'],",
        "    'delta_l1': fs1['val_middle_l1'] - fs0['val_middle_l1'],",
        "    'metric_fg_acc_fs0': fs0['val_middle_fg_acc'],",
        "    'metric_fg_acc_fs1': fs1['val_middle_fg_acc'],",
        "    'delta_fg_acc': fs1['val_middle_fg_acc'] - fs0['val_middle_fg_acc'],",
        '  }',
        '}',
        "(exp/'summary_agg.json').write_text(json.dumps(agg, indent=2))",
        'print(json.dumps(agg, indent=2))',
        'PY',
    ]
    remote_script = '\n'.join(lines) + '\n'

    with tempfile.NamedTemporaryFile('w', delete=False) as f:
        f.write(remote_script)
        local_tmp = Path(f.name)
    try:
        run(SCP_BASE + [str(local_tmp), f'{REMOTE}:{remote_run}'])
        run(SSH_BASE + [REMOTE, f'bash {shlex.quote(remote_run)}'])
        run(SCP_BASE + ['-r', f'{REMOTE}:{REMOTE_EXP_ROOT}/exp/{run_tag}/.', str(local_art)])
    finally:
        local_tmp.unlink(missing_ok=True)

    agg = json.loads((DOCS / 'artifacts' / run_tag / 'summary_agg.json').read_text())[run_tag]
    append_results(run_tag, int(spec['random_seed']), agg)
    print(json.dumps({'run_tag': run_tag, **agg}, indent=2))


if __name__ == '__main__':
    main()
