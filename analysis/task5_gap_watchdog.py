#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path('/root/autodl-tmp/experiments/future-seed-main/rwkv-diff-future-seed')
EXP_ROOT = ROOT / 'exp'
WEIGHTS_DIR = ROOT / 'weights'
RAW_DIR = Path('/root/autodl-tmp/data/video_interp_smoke/raw')
DATA_DIR = Path('/root/autodl-tmp/data/video_interp_smoke')
BUILDER = EXP_ROOT / 'build_realtriplet_midfirst_bin.py'
STATE_PATH = EXP_ROOT / 'task5_gap_watchdog_state.json'
DECISION_PATH = EXP_ROOT / 'task5_gap_watchdog_decision.json'
LOG_PATH = EXP_ROOT / 'task5_gap_watchdog.log'
DEFAULT_POLL_SECS = 60
GAPS = [24, 32, 40]
SEEDS = {24: 20260310, 32: 20260311, 40: 20260312}
STRONG_DELTA_FG = 0.10
STRONG_DELTA_LOSS = -0.50
WEAK_DELTA_FG = 0.03
FAIL_DELTA_FG = 0.008
MIN_WINDOWS = 400
TAG_PREFIX = 'task5_realvideo_gap'


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Watch and extend the task5 real-video gap queue.')
    p.add_argument('--once', action='store_true', help='Run one reconciliation pass and exit.')
    p.add_argument('--poll-secs', type=int, default=DEFAULT_POLL_SECS, help='Sleep interval between watchdog passes.')
    return p.parse_args()


@dataclass
class GapRecord:
    gap: int
    tag: str | None
    raw_windows: int | None = None
    state: str = 'unknown'
    delta_maskacc_fg_val: float | None = None
    delta_last_val_loss: float | None = None
    decision: str | None = None
    updated_at: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def log(msg: str) -> None:
    line = f'[{utc_now()}] {msg}'
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open('a') as f:
        f.write(line + '\n')


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, shell=True, text=True, capture_output=True, check=check)


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    records = {str(g): asdict(GapRecord(gap=g, tag=find_existing_tag(g))) for g in GAPS}
    return {'created_at': utc_now(), 'stop_reason': None, 'records': records, 'events': []}


def save_state(state: dict[str, Any]) -> None:
    state['updated_at'] = utc_now()
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True))


def record_event(state: dict[str, Any], action: str, **payload: Any) -> None:
    state.setdefault('events', []).append({'time': utc_now(), 'action': action, **payload})


def find_existing_tag(gap: int) -> str | None:
    candidates = sorted(EXP_ROOT.glob(f'{TAG_PREFIX}{gap}_long_v1_*'))
    dirs = [c for c in candidates if c.is_dir()]
    if not dirs:
        return None
    return dirs[-1].name


def read_summary(tag: str) -> tuple[float, float] | None:
    path = EXP_ROOT / tag / 'summary_agg.json'
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    row = next(iter(data.values()))
    return float(row['delta_maskacc_fg_val']), float(row['delta_last_val_loss'])


def classify(delta_fg: float, delta_loss: float) -> str:
    if delta_fg >= STRONG_DELTA_FG and delta_loss <= STRONG_DELTA_LOSS:
        return 'strong_positive'
    if delta_fg >= WEAK_DELTA_FG:
        return 'weak_positive'
    if delta_fg < FAIL_DELTA_FG:
        return 'failed'
    return 'borderline'


def runner_pids(tag: str) -> list[int]:
    out = run(f"pgrep -f '{tag}/runner.sh'", check=False).stdout.strip().splitlines()
    pids = []
    for line in out:
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def training_pids(tag: str) -> list[int]:
    base = tag.split('_2026')[0]
    out = run(f"pgrep -f 'weights/{base}_fs'", check=False).stdout.strip().splitlines()
    pids = []
    for line in out:
        line = line.strip()
        if line.isdigit():
            pids.append(int(line))
    return pids


def kill_tag(tag: str) -> None:
    for pid in training_pids(tag) + runner_pids(tag):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    time.sleep(1)
    for pid in training_pids(tag) + runner_pids(tag):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def count_raw_windows(gap: int) -> int:
    cmd = f"{sys.executable} - <<'PY'\nimport cv2\nfrom pathlib import Path\nraw = Path('{RAW_DIR}')\ngap = {gap}\ncount = 0\nfor video_path in sorted(raw.glob('*.mp4')):\n    cap = cv2.VideoCapture(str(video_path))\n    if not cap.isOpened():\n        raise SystemExit('failed to open ' + str(video_path))\n    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))\n    cap.release()\n    if n >= 2 * gap + 1:\n        count += n - 2 * gap\nprint(count)\nPY"
    return int(run(cmd).stdout.strip())


def ensure_bins(gap: int) -> int:
    train_out = DATA_DIR / f'realtriplet_midfirst_gap{gap}_train.bin'
    val_out = DATA_DIR / f'realtriplet_midfirst_gap{gap}_val.bin'
    windows = count_raw_windows(gap)
    if windows < MIN_WINDOWS:
        raise RuntimeError(f'gap{gap} has only {windows} raw windows < {MIN_WINDOWS}')
    if train_out.exists() and val_out.exists():
        return windows
    cmd = (
        f"{sys.executable} {BUILDER} "
        f"--raw-dir {RAW_DIR} "
        f"--train-out {train_out} "
        f"--val-out {val_out} "
        f"--gap {gap} --img-size 16 --vocab-size 16 "
        f"--train-samples 4000 --val-samples 800 --seed {SEEDS[gap]}"
    )
    result = run(cmd)
    log(f'built gap{gap} bins: {result.stdout.strip()}')
    return windows


def make_tag(gap: int) -> str:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return f'{TAG_PREFIX}{gap}_long_v1_{stamp}'


def make_manifest(gap: int, windows: int, depends_on_tag: str | None) -> str:
    wait_text = depends_on_tag or 'none'
    return '\n'.join([
        f'goal=P_task5_realvideo_gap{gap}_long_v1',
        'metric_primary=maskacc_fg_val',
        'threshold_coarse=+0.008',
        f'priority_reason=task5 real-video family remains strong; test stronger temporal gap={gap} with continuous queue and raw_windows={windows}',
        f'hard_constraints=single_gpu_only; wait_for={wait_text}; frozen recipe copied from task5 real-video family except dataset path and gap',
        f'fixed=data=realtriplet_midfirst_gap{gap},vocab=16,seq_len=768,mask=prefix:0.333333,n_layer=2,n_embd=128,head=32,device_bsz=64,batch=128,max_iters=400,eval_interval=50,maskacc_iters=100,fg_threshold=0,random_seed={SEEDS[gap]}',
        'change=FUTURE_SEED(0|1),ALPHA(fs1=-2)',
        'failure=oom_or_nan_or_missing_metric',
        '',
    ])


def make_runner(tag: str, gap: int, depends_on_tag: str | None) -> str:
    wait_block = 'if [ "none" != "none" ]; then\n  while pgrep -f "none/runner.sh" >/dev/null || pgrep -f "weights/none_fs" >/dev/null; do\n    sleep 60\n  done\nfi'
    if depends_on_tag:
        base = depends_on_tag.split('_2026')[0]
        wait_block = (
            f'while pgrep -f "{depends_on_tag}/runner.sh" >/dev/null || '
            f'pgrep -f "weights/{base}_fs" >/dev/null; do\n'
            '  sleep 60\n'
            'done'
        )
    task_base = tag.split('_2026')[0]
    exp_rel = f'exp/{tag}'
    data_train = f'{DATA_DIR}/realtriplet_midfirst_gap{gap}_train.bin'
    data_val = f'{DATA_DIR}/realtriplet_midfirst_gap{gap}_val.bin'
    summary_py = f'''/root/miniconda3/bin/python - <<PY2
import csv, json, re
exp="{exp_rel}"
name="{task_base}"
pat_step=re.compile(r"^step\\s+(\\d+):.*val loss\\s+([0-9.]+)")
pat_acc=re.compile(r"^maskacc_val\\s+([0-9.]+)")
pat_fg=re.compile(r"^maskacc_fg_val\\s+([0-9.]+)")
rows=[]
for fs in [0,1]:
    path=f"{{exp}}/logs/fs{{fs}}.log"
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
    rows.append({{"task":name,"fs":fs,"alpha":-2 if fs==1 else 0,"max_iters":400,"eval_interval":50,"maskacc_iters":100,"best_maskacc_val":round(best_acc,4),"best_maskacc_fg_val":round(best_fg,4),"last_val_loss":round(last_loss,4),"exit_code":0,"log_path":path}})
rows.sort(key=lambda x:x["fs"])
agg={{name:{{
    "best_maskacc_val_fs0": rows[0]["best_maskacc_val"],
    "best_maskacc_val_fs1": rows[1]["best_maskacc_val"],
    "delta_maskacc_val": rows[1]["best_maskacc_val"]-rows[0]["best_maskacc_val"],
    "best_maskacc_fg_val_fs0": rows[0]["best_maskacc_fg_val"],
    "best_maskacc_fg_val_fs1": rows[1]["best_maskacc_fg_val"],
    "delta_maskacc_fg_val": rows[1]["best_maskacc_fg_val"]-rows[0]["best_maskacc_fg_val"],
    "last_val_loss_fs0": rows[0]["last_val_loss"],
    "last_val_loss_fs1": rows[1]["last_val_loss"],
    "delta_last_val_loss": rows[1]["last_val_loss"]-rows[0]["last_val_loss"]
}}}}
with open(f"{{exp}}/summary_rows.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(f"{{exp}}/summary_agg.json","w") as f:
    json.dump(agg,f,indent=2)
print(json.dumps(agg,indent=2))
PY2'''
    lines = [
        'set -euo pipefail',
        f'cd {ROOT}',
        wait_block,
        f'mkdir -p {exp_rel}/logs {WEIGHTS_DIR}',
        f'env PYTHONUNBUFFERED=1 TRAIN=1 MODEL=rwkv RWKV7_KERNEL=python DATA_BIN={data_train} DATA_VAL_BIN={data_val} VOCAB_SIZE=16 SEQ_LEN=768 BIN_MASK_MODE=prefix BIN_PREFIX_RATIO=0.333333 MASKACC_EVAL=1 MASKACC_FG_EVAL=1 FG_TOKEN_THRESHOLD=0 MASKACC_ITERS=100 N_LAYER=2 N_EMBD=128 HEAD_SIZE=32 DEVICE_BSZ=64 BATCH_SIZE=128 MAX_ITERS=400 EVAL_INTERVAL=50 RANDOM_SEED={SEEDS[gap]} LOG_SAMPLE=0 LOG_OUTPUT=0 FUTURE_SEED=0 WEIGHTS_PATH={WEIGHTS_DIR}/{task_base}_fs0_{tag.split("_")[-1]}.pt /root/miniconda3/bin/python rwkv_diff_future_seed.py | tee {exp_rel}/logs/fs0.log',
        f'env PYTHONUNBUFFERED=1 TRAIN=1 MODEL=rwkv RWKV7_KERNEL=python DATA_BIN={data_train} DATA_VAL_BIN={data_val} VOCAB_SIZE=16 SEQ_LEN=768 BIN_MASK_MODE=prefix BIN_PREFIX_RATIO=0.333333 MASKACC_EVAL=1 MASKACC_FG_EVAL=1 FG_TOKEN_THRESHOLD=0 MASKACC_ITERS=100 N_LAYER=2 N_EMBD=128 HEAD_SIZE=32 DEVICE_BSZ=64 BATCH_SIZE=128 MAX_ITERS=400 EVAL_INTERVAL=50 RANDOM_SEED={SEEDS[gap]} LOG_SAMPLE=0 LOG_OUTPUT=0 FUTURE_SEED=1 FUTURE_SEED_ALPHA_INIT=-2 WEIGHTS_PATH={WEIGHTS_DIR}/{task_base}_fs1_{tag.split("_")[-1]}.pt /root/miniconda3/bin/python rwkv_diff_future_seed.py | tee {exp_rel}/logs/fs1.log',
        summary_py,
        '',
    ]
    return '\n'.join(lines)


def queue_gap(gap: int, depends_on_tag: str | None, state: dict[str, Any]) -> str:
    windows = ensure_bins(gap)
    tag = find_existing_tag(gap)
    if tag:
        rec = state['records'].setdefault(str(gap), asdict(GapRecord(gap=gap, tag=tag)))
        rec['tag'] = tag
        rec['raw_windows'] = windows
        rec['state'] = 'existing'
        rec['updated_at'] = utc_now()
        log(f'gap{gap} already exists as {tag}; reusing')
        return tag
    tag = make_tag(gap)
    exp_dir = EXP_ROOT / tag
    exp_dir.mkdir(parents=True, exist_ok=True)
    (exp_dir / 'logs').mkdir(parents=True, exist_ok=True)
    (exp_dir / 'run_manifest.txt').write_text(make_manifest(gap, windows, depends_on_tag))
    runner_path = exp_dir / 'runner.sh'
    runner_path.write_text(make_runner(tag, gap, depends_on_tag))
    runner_path.chmod(0o755)
    launch = run(f'cd {ROOT} && nohup bash {exp_dir}/runner.sh > {exp_dir}/launch.log 2>&1 &')
    rec = state['records'].setdefault(str(gap), asdict(GapRecord(gap=gap, tag=tag)))
    rec['tag'] = tag
    rec['raw_windows'] = windows
    rec['state'] = 'queued'
    rec['updated_at'] = utc_now()
    record_event(state, 'queued_gap', gap=gap, tag=tag, depends_on=depends_on_tag, raw_windows=windows)
    log(f'queued gap{gap} as {tag} (depends_on={depends_on_tag}, raw_windows={windows})')
    return tag


def update_records(state: dict[str, Any]) -> None:
    for gap in GAPS:
        rec = state['records'].setdefault(str(gap), asdict(GapRecord(gap=gap, tag=find_existing_tag(gap))))
        tag = rec.get('tag') or find_existing_tag(gap)
        rec['tag'] = tag
        if tag is None:
            rec['state'] = 'absent'
            rec['updated_at'] = utc_now()
            continue
        summary = read_summary(tag)
        if summary is not None:
            delta_fg, delta_loss = summary
            rec['delta_maskacc_fg_val'] = delta_fg
            rec['delta_last_val_loss'] = delta_loss
            rec['decision'] = classify(delta_fg, delta_loss)
            rec['state'] = 'finished'
        else:
            pids = runner_pids(tag)
            rec['state'] = 'running_or_waiting' if pids else 'stalled'
        if rec.get('raw_windows') is None:
            try:
                rec['raw_windows'] = count_raw_windows(gap)
            except Exception as exc:
                log(f'count_raw_windows failed for gap{gap}: {exc}')
        rec['updated_at'] = utc_now()


def write_decision_snapshot(state: dict[str, Any]) -> None:
    DECISION_PATH.write_text(json.dumps({
        'time': utc_now(),
        'stop_reason': state.get('stop_reason'),
        'records': state.get('records', {}),
        'events': state.get('events', [])[-20:],
    }, indent=2, sort_keys=True))


def maybe_cancel_due_to_previous(state: dict[str, Any], gap: int) -> None:
    idx = GAPS.index(gap)
    if idx == 0:
        return
    prev_gap = GAPS[idx - 1]
    prev = state['records'][str(prev_gap)]
    rec = state['records'][str(gap)]
    tag = rec.get('tag')
    if not tag or rec.get('state') == 'cancelled':
        return
    if prev.get('state') != 'finished':
        return
    if prev.get('decision') == 'strong_positive':
        return
    kill_tag(tag)
    rec['state'] = 'cancelled'
    rec['decision'] = 'cancelled_by_watchdog'
    rec['updated_at'] = utc_now()
    state['stop_reason'] = f'gap{prev_gap} was {prev.get("decision")}; cancelled downstream gap{gap} and stopped expansion'
    record_event(state, 'cancelled_gap', gap=gap, tag=tag, reason=state['stop_reason'])
    log(state['stop_reason'])


def maybe_queue_next(state: dict[str, Any], gap: int) -> None:
    idx = GAPS.index(gap)
    if idx >= len(GAPS) - 1:
        return
    rec = state['records'][str(gap)]
    if rec.get('state') != 'finished' or rec.get('decision') != 'strong_positive':
        return
    next_gap = GAPS[idx + 1]
    next_rec = state['records'].setdefault(str(next_gap), asdict(GapRecord(gap=next_gap, tag=find_existing_tag(next_gap))))
    if next_rec.get('tag'):
        return
    queue_gap(next_gap, depends_on_tag=rec['tag'], state=state)


def main() -> None:
    args = parse_args()
    log('starting task5 gap watchdog')
    state = load_state()
    save_state(state)
    while True:
        update_records(state)
        for gap in GAPS[1:]:
            maybe_cancel_due_to_previous(state, gap)
        if state.get('stop_reason') is None:
            for gap in GAPS[:-1]:
                maybe_queue_next(state, gap)
        if all(state['records'][str(g)].get('state') in {'finished', 'cancelled', 'absent', 'stalled'} for g in GAPS):
            if state.get('stop_reason') is None:
                state['stop_reason'] = 'gap plan exhausted or completed without further expansion'
                record_event(state, 'watchdog_complete', reason=state['stop_reason'])
                log(state['stop_reason'])
            save_state(state)
            write_decision_snapshot(state)
            break
        save_state(state)
        write_decision_snapshot(state)
        if args.once:
            break
        time.sleep(args.poll_secs)


if __name__ == '__main__':
    main()
