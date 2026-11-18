"""Unified export adapter; runs only on actual captured panel files."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from analyze import summarize


def flatten(value, prefix=''):
    result = {}
    if isinstance(value, dict):
        for key, item in value.items():
            result.update(flatten(item, prefix+'.'+key if prefix else key))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            result.update(flatten(item, f'{prefix}.{i}'))
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        result[prefix] = value
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--protocol-tool', type=Path, required=True)
    args = parser.parse_args()
    cells = [(p, json.loads(p.read_text())) for p in sorted((args.directory/'cells').glob('*.json'))]
    flat = []
    sources = []
    for i, (file, cell) in enumerate(cells):
        summary = summarize(cell)
        status = ('succeeded' if cell['status'] == 'self_checked_recovered'
                  else 'timeout' if cell['status'] == 'cell_timeout' else 'failed')
        flat.append({'run_id': file.stem, 'arm': cell['arm'],
                     'instance_id': cell['instance']['fixture_id'],
                     'seed': str(cell['workload']['seed']),
                     'replicate': 0 if cell['workload']['seed'] == 2026111801 else 1,
                     'warmup': False, 'status': status, 'verification': 'no_claim',
                     'usable_relations': summary['usable_relations'],
                     'rank': cell.get('rank', 0),
                     'process_peak_rss': summary['peak_rss_kib'],
                     'wall_seconds': cell.get('collection', {}).get('wall_ns', 0)/1e9,
                     'tier': 'unqualified'})
        sources.append((file, cell, False))
        for control in cell.get('controls', []):
            outcome = control['status']
            control_status = ('succeeded' if outcome == 'self_check_pass' else
                              'timeout' if outcome == 'timeout' else
                              'cancelled' if outcome == 'not_applicable' else 'failed')
            flat.append({'run_id': file.stem+'-'+control['kind'],
                         'arm': control['kind'], 'instance_id': cell['instance']['fixture_id'],
                         'seed': str(cell['workload']['seed']), 'replicate': 0,
                         'warmup': True, 'status': control_status,
                         'verification': 'no_claim', 'tier': 'unqualified'})
            sources.append((file, cell, True))
    raw = args.directory/'runs.jsonl'
    raw.write_text(''.join(json.dumps(row)+'\n' for row in flat))
    out = args.directory/'export.json'
    subprocess.run([sys.executable, str(args.protocol_tool), 'from-rows', str(raw),
                    '--protocol', str(args.protocol), '--out', str(out),
                    '--export-id', 'curve-representation-controlled-20261118'], check=True)
    export = json.loads(out.read_text())
    for row, (file, cell, is_control) in zip(export['runs'], sources):
        usage = {} if is_control else cell.get('os_child_rusage', {})
        row['measurements']['wall_valid'] = False
        row['measurements']['cpu_user_seconds'] = usage.get('ru_utime')
        row['measurements']['cpu_sys_seconds'] = usage.get('ru_stime')
        rss = usage.get('ru_maxrss')
        row['measurements']['max_rss_bytes'] = rss*1024 if rss is not None else None
        row['measurements']['counters'] = {} if is_control else flatten({key: cell[key] for key in [
            'queries', 'collection', 'os_child_rusage', 'rho_reference'] if key in cell})
        row['verification'] = {'status': 'no_claim',
                               'verifier': 'producer point-equation checks only; no signed independent PCC verdict'}
        row['isolation'] = {'tier': 'unqualified', 'contended': None,
                             'blockers': ['No admitted isolation receipt; CPU affinity is placement only.']}
        row['artifacts'] = [{'path': str(file.relative_to(args.directory)),
                             'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                             'bytes': file.stat().st_size, 'kind': 'raw'}]
    out.write_text(json.dumps(export, indent=2)+'\n')
    subprocess.run([sys.executable, str(args.protocol_tool), 'check-export', str(out),
                    '--protocol', str(args.protocol), '--verify-files'], check=True)


if __name__ == '__main__':
    main()
