#!/usr/bin/env python3
"""Recompute and cross-check the committed summary; producer-authored, not PCC."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent

def compare(summary, full, full_bytes):
    rows = full['rows']
    return all([
        summary['source_order'] == full['source']['order'],
        summary['target_order'] == full['target']['order'],
        summary['kernel_size'] == full['kernel_size'],
        summary['image_size'] == full['image_size'],
        summary['generator'] == full['source_generator'],
        summary['homomorphism_pairs'] == full['homomorphism_checks'],
        summary['dual_composition_points'] == full['dual_composition_checks'],
        summary['subgroup_inverse_points'] == full['inverse_subgroup_checks'],
        summary['seed'] == full['seed'],
        summary['samples'] == len(rows),
        summary['correct_logs_direct'] == len(rows),
        summary['correct_logs_transfer'] == len(rows),
        summary['k'] == [r['k'] for r in rows],
        summary['direct_finv'] == [r['source_ops']['finv'] for r in rows],
        summary['transfer_finv'] == [r['transferred_ops']['finv'] for r in rows],
        summary['totals']['direct'] == full['totals']['direct'],
        summary['totals']['transfer'] == full['totals']['transferred'],
        summary['totals']['inverse_optional'] == full['totals']['inverse_optional'],
        summary['script_sha256'] == full['script_sha256'],
        summary['full_local_raw_json_sha256'] == hashlib.sha256(full_bytes).hexdigest(),
        all(r['k'] == r['source_log'] == r['transferred_log'] for r in rows),
    ])

def main():
    s = json.loads((ROOT / 'RESULTS_SUMMARY.json').read_text())
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp) / 'full.json'
        replay = ROOT / 'replay.py'
        subprocess.run([sys.executable, str(replay), '--out', str(out)], check=True)
        raw = out.read_bytes()
        f = json.loads(raw)
        if not compare(s, f, raw): raise SystemExit('FAIL: summary does not match replay')
        subprocess.run([sys.executable, str(replay), '--verify-json', str(out)], check=True)
        bad = dict(s)
        bad['k'] = [((s['k'][0] + 1) % 491)] + s['k'][1:]
        if compare(bad, f, raw): raise SystemExit('FAIL: summary mutation not detected')
        f['rows'][0]['transferred_log'] = (f['rows'][0]['transferred_log']+1)%491
        out.write_text(json.dumps(f))
        p = subprocess.run([sys.executable, str(replay), '--verify-json', str(out)], capture_output=True, text=True)
        if p.returncode == 0: raise SystemExit('FAIL: full-result mutation not detected')
    print('PASS: summary replay and two mutation-rejection controls (producer-local, unsigned)')

if __name__ == '__main__': main()
