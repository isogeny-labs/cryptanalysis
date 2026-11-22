"""Freeze the independent Sage replay before executing it."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    census = json.loads((HERE / 'census_result.json').read_text())
    assert census['status'] == 'PASS_EXACT_ORBIT_CENSUS'
    assert census['protocol_sha256'] == sha(HERE / 'protocol.json')
    record = {
        'kind': 'n131_d13_adjacent_image_sage_audit_v1',
        'status': 'FROZEN_BEFORE_AUDIT',
        'frozen_utc': datetime.now(timezone.utc).isoformat(),
        'source_receipt': protocol['source_receipt'],
        'source_receipt_sha256': protocol['source_receipt_sha256'],
        'census_result_sha256': sha(HERE / 'census_result.json'),
        'auditor_source_sha256': sha(HERE / 'audit_sage.py'),
        'runtime_info_sha256': protocol['runtime_info_sha256'],
        'subgroup_order': protocol['subgroup_order'],
        'frobenius_eigenvalue': protocol['frobenius_eigenvalue'],
        'wall_cap_seconds': 180,
        'rss_cap_bytes': 4 * 1024**3,
    }
    with (HERE / 'audit_protocol.json').open('x') as stream:
        json.dump(record, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print('FROZEN_AUDIT', record['frozen_utc'])


if __name__ == '__main__':
    main()
