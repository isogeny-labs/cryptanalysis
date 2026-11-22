"""Freeze Q1358 pair-index and N41 public-hit inputs before measured runs."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GOAL = HERE.parent
PAIR = GOAL / 'n131_phi_pair_occupancy_20261018'
N41 = GOAL / 'n41_target_conditioned_2p1_join_20261018'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    pair_cfg = json.loads((PAIR / 'protocol.json').read_text())
    pair_result = json.loads((PAIR / 'result.json').read_text())
    pair_audit = json.loads((PAIR / 'audit_result.json').read_text())
    n41_cfg = json.loads((N41 / 'protocol.json').read_text())
    n41_audit = json.loads((N41 / 'audit_result.json').read_text())
    assert pair_cfg['curve_id'] == 'EC1N131Ckb1heb5f1998f20b'
    assert pair_result['distinct_partial_sums'] == 1132096
    assert pair_audit['status'] == 'PASS_INDEPENDENT_DIRECT_PAIR_ENUMERATION'
    assert n41_audit['status'] == 'PASS_INDEPENDENT_N41_2P1_PUBLIC_RELATION'
    assert sha(N41 / 'join_input.tsv') == n41_cfg['source_sha256'][
        str((N41 / 'join_input.tsv').relative_to(ROOT))]
    sources = {
        'geometry': Path(pair_cfg['sources']['geometry']['path']),
        'field.py': ROOT / 'ecc2k130/codegen/field.py',
        'curves.py': ROOT / 'ecc2k130/codegen/curves.py',
        'pair_protocol': PAIR / 'protocol.json',
        'pair_result': PAIR / 'result.json',
        'pair_audit': PAIR / 'audit_result.json',
        'n41_join_input': N41 / 'join_input.tsv',
        'n41_join_protocol': N41 / 'protocol.json',
        'n41_join_audit': N41 / 'audit_result.json',
        'run_sage.py': HERE / 'run_sage.py',
        'audit_sage.py': HERE / 'audit_sage.py',
        'n41_control_sage.py': HERE / 'n41_control_sage.py',
        'freeze.py': HERE / 'freeze.py',
        'verify.py': HERE / 'verify.py',
        'XPairLookup.lean': HERE / 'XPairLookup.lean',
        'lean-toolchain': HERE / 'lean-toolchain',
        'lean_check.log': HERE / 'lean_check.log',
        'sage_runtime_info': HERE / 'sage_runtime_info.json',
    }
    frozen = {name: {'path': str(path), 'sha256': sha(path)}
              for name, path in sources.items()}
    cfg = {'status': 'FROZEN_BEFORE_INDEX', 'candidate_id': None,
           'curve_id': pair_cfg['curve_id'], 'workload_id': '3c1992b7c92f',
           'source_pair_domain': {'slot_positions': [0, 1],
                                  'valid_codes': 532, 'signed_options': 1064,
                                  'signed_pairs': 1132096},
           'positive_seed': 2026101819, 'positive_query_count': 256,
           'ordinary_query_seed': 2026101820,
           'ordinary_right_family_count': 256,
           'n41_control_seed': 2026101821,
           'n41_family_queries': 1024,
           'build_wall_cap_seconds': 600,
           'rss_cap_bytes': 4294967296,
           'worker_count': 1, 'sources': frozen}
    with (HERE / 'protocol.json').open('x') as out:
        json.dump(cfg, out, sort_keys=True, indent=2)
        out.write('\n')
    print(json.dumps({'status': cfg['status'],
                      'protocol_sha256': sha(HERE / 'protocol.json')}, sort_keys=True))


if __name__ == '__main__':
    main()
