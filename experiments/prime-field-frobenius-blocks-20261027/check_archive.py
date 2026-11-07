"""Read-only integrity and summary-consistency checks for a historical import."""
from hashlib import sha256
from pathlib import Path
import json
import math


def main():
    root = Path(__file__).resolve().parent
    archive = root / 'archive'
    manifest = json.loads((archive / 'manifest.json').read_text())
    provenance = json.loads((root / 'PROVENANCE.json').read_text())
    assert sha256((archive / 'manifest.json').read_bytes()).hexdigest() == provenance['archive_manifest_sha256']
    for path, expected in manifest['files'].items():
        assert sha256((archive / path).read_bytes()).hexdigest() == expected, path
    raw = json.loads((archive / 'experiments/ideas/block_benchmark.json').read_text())
    summary = json.loads((archive / 'results.json').read_text())
    audits = json.loads((archive / 'experiments/ideas/audit.json').read_text())
    assert audits['errors'] == 0
    assert audits['known_labels_verified'] == 1664
    assert audits['principal_divisors_verified'] == 78
    assert audits['progression_indices_replayed'] == 1163264
    for name, totals in summary['complete_labeled_domain_construction'].items():
        rows = [r for r in raw['complete_constructions'] if r['algorithm'] == name]
        assert len(rows) == totals['trials'] == 8
        for key in ['construction_group_ops', 'blocks', 'failed_blocks', 'verified_hit_indices']:
            assert sum(r[key] for r in rows) == totals[key], (name, key)
        assert math.isclose(sum(r['complete_cpu_s'] for r in rows), totals['complete_cpu_s'], rel_tol=1e-12)
        assert all(r['final_known_coordinates'] == 33 for r in rows)
    report = root / 'REPORT.pdf'
    if report.exists():
        assert report.read_bytes().startswith(b'%PDF-')
        assert report.stat().st_size <= 65536, 'Report exceeds data-store threshold'
    print(json.dumps({'archive_files_hash_verified': len(manifest['files']) + 1,
                      'recorded_audit_errors': audits['errors'],
                      'complete_construction_rows_consistent': len(raw['complete_constructions']),
                      'status': 'historical archive integrity checked; no new experiment'}, indent=2))


if __name__ == '__main__':
    main()
