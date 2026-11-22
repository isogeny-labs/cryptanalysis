"""Freeze the exact factor-base expansion census before running it."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GOAL = HERE.parent
SOURCE = Path('/Volumes/SSD990-2/ecc2k130-ic-runstore/d13-m12-20261115/IC1N131Ckb1fb1083108PDP12satRCdirectLAgaussTDdirectISO0h195ae7ea5e75W3c1992b7c92fR1/factor_base_receipt.json')
EIGEN = GOAL / 'n131_w18_linked_tenpair_public_20261017/lambda_sage_result.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    source = json.loads(SOURCE.read_text())
    eigen = json.loads(EIGEN.read_text())
    assert source['curve_id'] == 'EC1N131Ckb1heb5f1998f20b'
    assert eigen['status'] == 'PASS_ACTUAL_N131_FROBENIUS_EIGENVALUE'
    record = {
        'kind': 'n131_d13_adjacent_endomorphism_base_screen_v1',
        'status': 'FROZEN_BEFORE_CENSUS',
        'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'proposal_id': 'Q20261115082001',
        'candidate_id': None,
        'curve_id': source['curve_id'],
        'subgroup_order': '680564733841876926932320129493409985129',
        'frobenius_eigenvalue': eigen['lambda'],
        'source_receipt': str(SOURCE),
        'source_receipt_sha256': sha(SOURCE),
        'eigen_receipt_sha256': sha(EIGEN),
        'runtime_info_sha256': sha(HERE / 'sage_runtime_info.json'),
        'census_source_sha256': sha(HERE / 'census.py'),
        'codegen_source_sha256': {
            name: sha(ROOT / 'ecc2k130/codegen' / name)
            for name in ('field.py', 'curves.py', 'indexcalc_e2e.py')},
        'wall_cap_seconds': 180,
        'rss_cap_bytes': 4 * 1024**3,
        'source_point_count': 1083108,
        'source_folded_columns': 4134,
        'screen_hypothesis': 'The signed Frobenius closure of P+tau(P) is disjoint from the original d13 base, doubles actual B, and introduces no new independent log unknowns.',
        'decision_gate': 'Promote only if exact set census, subgroup scalar mapping, source-bound N41 unpinned relation and N131 formula cost all pass; an enlarged B or model-count heuristic alone is insufficient.',
    }
    with (HERE / 'protocol.json').open('x') as stream:
        json.dump(record, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print('FROZEN', record['frozen_utc'])


if __name__ == '__main__':
    main()
