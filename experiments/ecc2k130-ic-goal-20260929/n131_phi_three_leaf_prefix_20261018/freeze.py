"""Freeze ordinary three-leaf prefixes against the archived Q1358 d10 formula."""
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'experiments/ecc2k130-ic-goal-20260929/n131_phi_torsion_frobenius_domains_20261005'
sys.path.insert(0, str(ROOT / 'ecc2k130/codegen'))
import curves
import field


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    geometry_path = SOURCE / 'm15_d10_static/d10_exact_geometry_v1.json'
    formula_path = SOURCE / 'm15_d10_static/official_q_phi_fiber_d10_m15_v1.xcnf'
    receipt_path = SOURCE / 'm15_d10_static/d10_m15_formula_and_planted_control_v1.json'
    workload_path = ROOT / 'experiments/ecc2k130-ic-goal-20260929/n131_w2_m15_official_single_target_4g_r3_20261004/workload.json'
    solver_path = Path('/opt/homebrew/bin/cryptominisat5')
    receipt = json.loads(receipt_path.read_text())
    geometry = json.loads(geometry_path.read_text())
    workload = json.loads(workload_path.read_text())
    assert receipt['formula_file']['sha256'] == sha(formula_path)
    assert receipt['curve_id'] == geometry['curve_id'] == 'EC1N131Ckb1heb5f1998f20b'
    assert workload['target_count'] == 1 and workload['workload_id'] == '3c1992b7c92f'
    onb = field.Onb(131)
    curve = curves.Curve(onb)
    basis = [int(v, 16) for v in geometry['domain']['basis_coordinate_masks_hex']]
    valid = []
    for code in range(1 << len(basis)):
        mask = 0
        for bit, b in enumerate(basis):
            if code >> bit & 1:
                mask ^= b
        if mask:
            phi = onb.fromCoords(mask)
            point = curve.pointFromX(onb.add(onb.inv(phi), onb.one()))
            if point is not None:
                valid.append(code)
    assert len(valid) == 532
    rng = random.Random(2026101814)
    prefixes = []
    while len(prefixes) < 16:
        triple = [rng.choice(valid) for _ in range(3)]
        if triple not in prefixes:
            prefixes.append(triple)
    sources = {name: {'path': str(path), 'sha256': sha(path)} for name, path in {
        'geometry': geometry_path, 'formula': formula_path,
        'formula_receipt': receipt_path, 'workload': workload_path,
        'solver': solver_path, 'field.py': ROOT / 'ecc2k130/codegen/field.py',
        'curves.py': ROOT / 'ecc2k130/codegen/curves.py',
        'freeze.py': HERE / 'freeze.py', 'run.py': HERE / 'run.py',
        'sage_runtime_info': HERE / 'sage_runtime_info.json'}.items()}
    protocol = {'status': 'FROZEN_BEFORE_SOLVER', 'candidate_id': None,
                'curve_id': geometry['curve_id'], 'workload_id': workload['workload_id'],
                'target_count': 1, 'public_point': workload['targets'][0],
                'valid_codes_sha256': hashlib.sha256(json.dumps(valid, separators=(',', ':')).encode()).hexdigest(),
                'sample_seed': 2026101814, 'ordinary_prefixes': prefixes,
                'invalid_domain_control': [0, valid[0], valid[1]],
                'baseline_control': True,
                'leaf_variable_rule': 'leaf i bit j is XCNF variable 2+10*i+j, for i=0..14 and j=0..9',
                'solver_flags': ['--threads=1', '--maxtime=20', '--printsol=1', '--verb=1',
                                 '--xor=0', '--maxmatrixrows=10000', '--maxmatrixcols=15000',
                                 '--maxnummatrices=10', '--random=2026101814'],
                'per_arm_parent_wall_cap_seconds': 25,
                'campaign_parent_wall_cap_seconds': 550,
                'rss_cap_bytes': 4294967296, 'sources': sources}
    with (HERE / 'protocol.json').open('x') as handle:
        json.dump(protocol, handle, sort_keys=True, indent=2)
        handle.write('\n')
    print(json.dumps({'status': protocol['status'], 'ordinary_prefixes': len(prefixes),
                      'formula_sha256': sources['formula']['sha256']}, sort_keys=True))


if __name__ == '__main__':
    main()
