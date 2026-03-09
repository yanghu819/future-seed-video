#!/usr/bin/env python3
from __future__ import annotations

import csv
import fcntl
import json
import re
import subprocess
import sys
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path('/Users/torusmini/Downloads/autodl3-impainting-fs')
DOCS = ROOT / 'future-seed-video'
ANALYSIS = DOCS / 'analysis'
BASE_SPEC_PATH = ANALYSIS / 'moving_mnist_v2_base_spec.json'
QUEUE_PATH = ANALYSIS / 'moving_mnist_v2_mutation_queue.tsv'
RESULTS_PATH = ANALYSIS / 'moving_mnist_v2_results.tsv'
LAUNCHER = ANALYSIS / 'launch_moving_mnist_v2_smoke.py'
GENERATED_SPECS = ANALYSIS / 'moving_mnist_v2_specs'
LOG_DIR = ANALYSIS / 'moving_mnist_v2_loop_logs'
LOOP_STATE = ANALYSIS / 'moving_mnist_v2_loop_state.json'
LOCK_PATH = ANALYSIS / 'moving_mnist_v2_loop.lock'
SSH = ['ssh', '-i', str(Path.home() / '.ssh' / 'autodl_ed25519'), '-o', 'IdentitiesOnly=yes', '-o', 'StrictHostKeyChecking=no', '-p', '19708', 'root@connect.bjb2.seetacloud.com']

STANDARD_QUEUE_FIELDS = [
    'priority', 'status', 'mutation', 'goal', 'note', 'run_tag', 'result_status', 'delta_iou', 'delta_l1',
    'launched_at', 'finished_at', 'spec_path', 'description'
]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + '\n')


def load_results() -> list[dict]:
    with RESULTS_PATH.open() as f:
        return list(csv.DictReader(f, delimiter='\t'))


def next_confirm_seed(rows: list[dict], base_seed: int) -> int:
    seeds = [base_seed]
    for row in rows:
        try:
            seeds.append(int(row['seed']))
        except Exception:
            pass
    return max(seeds) + 1


def load_queue() -> tuple[list[str], list[dict]]:
    with QUEUE_PATH.open() as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
        fields = reader.fieldnames or STANDARD_QUEUE_FIELDS
    merged = []
    for field in STANDARD_QUEUE_FIELDS:
        if field not in fields:
            merged.append(field)
    fields = list(fields) + merged
    for row in rows:
        for field in fields:
            row.setdefault(field, '')
    return fields, rows


def save_queue(fields: list[str], rows: list[dict]) -> None:
    for idx, row in enumerate(rows, start=1):
        row['priority'] = str(idx)
    with QUEUE_PATH.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)


def reset_stale_running(rows: list[dict]) -> None:
    for row in rows:
        if row.get('status') == 'running':
            row['status'] = 'queued'
            row['run_tag'] = ''
            row['launched_at'] = ''
            row['spec_path'] = ''
            row['description'] = row.get('description') or ''


def parse_scalar(raw: str):
    text = raw.strip()
    if text.lower() in {'true', 'false'}:
        return text.lower() == 'true'
    if re.fullmatch(r'-?\d+', text):
        return int(text)
    if re.fullmatch(r'-?\d+\.\d*', text):
        return float(text)
    return text


def parse_mutation(mutation: str) -> dict:
    out = {}
    for part in mutation.split(','):
        part = part.strip()
        if not part:
            continue
        key, value = part.split('=', 1)
        out[key.strip()] = parse_scalar(value)
    return out


def apply_mutation(spec: dict, mutation: str) -> dict:
    out = deepcopy(spec)
    for key, value in parse_mutation(mutation).items():
        out[key] = value
    if out.get('mask_mode') == 'square':
        out.setdefault('square_frame_side', out['img_size'])
        out.setdefault('square_frame_index', 0)
        out.setdefault('square_size', max(4, out['img_size'] // 3))
    out['seq_len'] = int(out['img_size']) * int(out['img_size']) * int(out.get('frame_count', 3))
    return out


def slugify(mutation: str) -> str:
    text = mutation.lower()
    replacements = {
        'num_digits': 'nd',
        'digit_size_min': 'dmin',
        'digit_size_max': 'dmax',
        'speed_min': 'smin',
        'speed_max': 'smax',
        'mask_mode': 'mask',
        'square_size': 'sq',
        'square_frame_side': 'sfs',
        'square_frame_index': 'sfi',
        'img_size': 'img',
        'max_iters': 'it',
        'random_seed': 'seed',
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    text = text.replace('=', '').replace(',', '_').replace('.', 'p')
    text = re.sub(r'[^a-z0-9_]+', '', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text[:80]


def build_run_tag(spec: dict, mutation: str) -> str:
    return f"moving_mnist_v2_{slugify(mutation)}_{now_utc()}"


def status_from_metrics(delta_iou: float, delta_l1: float) -> str:
    if delta_iou > 0.02 and delta_l1 < 0:
        return 'keep'
    if delta_iou <= 0:
        return 'discard'
    return 'ambiguous'


def wait_for_remote_idle(timeout_hours: float = 0.5) -> None:
    deadline = time.time() + timeout_hours * 3600
    cmd = SSH + ["ps -eo pid,cmd | grep -E 'moving_mnist_v2_.*\\.sh|eval_moving_mnist_v2|rwkv_diff_future_seed.py' | grep -v grep || true"]
    while time.time() < deadline:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        out = proc.stdout.strip()
        if not out:
            return
        time.sleep(20)
    raise RuntimeError(f'remote did not become idle in time:\n{out}')


def run_one(spec_path: Path, description: str, log_path: Path) -> None:
    cmd = ['python3', str(LAUNCHER), '--spec', str(spec_path), '--results', str(RESULTS_PATH), '--description', description]
    with log_path.open('w') as logf:
        proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, text=True)
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f'launcher failed: {spec_path} -> exit {rc}')


def enqueue_confirm(rows: list[dict], fields: list[str], finished_row: dict, seed: int) -> None:
    family_mutation = finished_row['mutation']
    for row in rows:
        if row.get('mutation') == family_mutation and 'confirm_seed' in row.get('note', '') and row.get('status') in {'queued', 'running'}:
            return
    new_row = {field: '' for field in fields}
    new_row.update({
        'status': 'queued',
        'mutation': f'{family_mutation},random_seed={seed}',
        'goal': 'confirm repeat of keep candidate',
        'note': f"confirm_seed from {finished_row.get('run_tag', '')}",
        'description': f"confirm repeat for {family_mutation}",
    })
    insert_at = rows.index(finished_row) + 1
    rows.insert(insert_at, new_row)


def main() -> None:
    hours = float(sys.argv[1]) if len(sys.argv) > 1 else 8.0
    end_time = datetime.now(timezone.utc) + timedelta(hours=hours)
    GENERATED_SPECS.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    lock_file = LOCK_PATH.open('w')
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise RuntimeError(f'loop already running: {LOCK_PATH}')

    base_spec = load_json(BASE_SPEC_PATH)
    fields, rows = load_queue()
    reset_stale_running(rows)
    save_queue(fields, rows)
    save_json(LOOP_STATE, {
        'started_at': now_utc(),
        'deadline_at': end_time.strftime('%Y%m%dT%H%M%SZ'),
        'mode': 'moving_mnist_v2_autoresearch_loop'
    })

    while datetime.now(timezone.utc) < end_time:
        fields, rows = load_queue()
        queued_idx = next((i for i, row in enumerate(rows) if row.get('status') == 'queued'), None)
        if queued_idx is None:
            break
        row = rows[queued_idx]
        mutation = row['mutation']
        spec = apply_mutation(base_spec, mutation)
        if 'random_seed' not in parse_mutation(mutation):
            spec['random_seed'] = base_spec['random_seed']
        run_tag = build_run_tag(spec, mutation)
        spec['run_tag'] = run_tag
        spec_path = GENERATED_SPECS / f'{run_tag}.json'
        spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=True) + '\n')
        log_path = LOG_DIR / f'{run_tag}.log'
        description = row.get('description') or f'autoresearch mutation: {mutation}'

        row['status'] = 'running'
        row['run_tag'] = run_tag
        row['spec_path'] = str(spec_path)
        row['launched_at'] = now_utc()
        row['description'] = description
        save_queue(fields, rows)

        wait_for_remote_idle(timeout_hours=0.2)
        run_one(spec_path, description, log_path)

        agg = load_json(DOCS / 'artifacts' / run_tag / 'summary_agg.json')[run_tag]
        delta_iou = float(agg['delta_iou'])
        delta_l1 = float(agg['delta_l1'])
        result_status = status_from_metrics(delta_iou, delta_l1)

        fields, rows = load_queue()
        target = next(r for r in rows if r.get('run_tag') == run_tag)
        target['status'] = result_status
        target['result_status'] = result_status
        target['delta_iou'] = f'{delta_iou:.6f}'
        target['delta_l1'] = f'{delta_l1:.6f}'
        target['finished_at'] = now_utc()
        save_queue(fields, rows)

        if result_status == 'keep':
            next_seed = next_confirm_seed(load_results(), int(base_spec['random_seed']))
            fields, rows = load_queue()
            target = next(r for r in rows if r.get('run_tag') == run_tag)
            enqueue_confirm(rows, fields, target, next_seed)
            save_queue(fields, rows)

        save_json(LOOP_STATE, {
            'started_at': load_json(LOOP_STATE)['started_at'],
            'last_finished_at': now_utc(),
            'deadline_at': end_time.strftime('%Y%m%dT%H%M%SZ'),
            'last_run_tag': run_tag,
            'last_status': result_status,
            'last_delta_iou': delta_iou,
            'last_delta_l1': delta_l1,
        })

    save_json(LOOP_STATE, {
        **load_json(LOOP_STATE),
        'ended_at': now_utc(),
        'finished': True,
    })
    lock_file.close()


if __name__ == '__main__':
    main()
