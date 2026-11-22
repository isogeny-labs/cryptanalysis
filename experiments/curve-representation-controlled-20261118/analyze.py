"""Frozen descriptive analysis. No winner or qualified speedup inference."""
import argparse
from collections import Counter
import json
from pathlib import Path


def summarize(record):
    queries = record.get('queries', [])
    counts = Counter(q['status'] for q in queries)
    usable = sum(q.get('usable_relations', 0) for q in queries)
    candidates = sum(q.get('solver', {}).get('candidate_coordinate_tuples', 0)
                     for q in queries)
    rejects = sum(q.get('solver', {}).get('rejected_coordinate_tuples', 0)
                  for q in queries)
    pdp_wall = sum(q.get('pdp', {}).get('wall_ns', 0) for q in queries)
    return {'instance_id': record['instance']['fixture_id'],
            'source_field': record['instance']['source_field'],
            'field': record['instance']['p'], 'subgroup_order': record['instance']['r'],
            'control_kind': record['instance']['kind'], 'arm': record['arm'],
            'same_point_rho_reference': record.get('rho_reference'),
            'seed': record['workload']['seed'], 'status': record['status'],
            'standing': 'unverified', 'attempted_queries': len(queries),
            'status_counts': dict(counts), 'usable_relations': usable,
            'rank': record.get('rank'), 'unknowns': record.get('unknowns'),
            'pdp_wall_ns_including_failed_attempts': pdp_wall,
            'pdp_ns_per_usable_relation': pdp_wall/usable if usable else None,
            'candidate_rejection_rate': rejects/candidates if candidates else None,
            'query_timeout_rate': counts['timeout']/len(queries) if queries else None,
            'peak_rss_kib': record.get('os_child_rusage', {}).get('ru_maxrss',
                           record.get('worker_peak_rss_kib')),
            'observed_collection_wall_ns': record.get('collection', {}).get('wall_ns'),
            'complete_collection_wall_ns': record.get('complete_collection_wall_ns'),
            'timing_qualification': 'exploratory_only_unless_independent_admission_supplied'}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('directory', type=Path)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    records = [json.loads(f.read_text()) for f in sorted(args.directory.glob('*.json'))]
    rows = [summarize(record) for record in records]
    args.out.write_text(json.dumps({'standing': 'unverified', 'rows': rows,
        'limitations': ['No qualified timing ratio or cryptographic-size extrapolation.',
                        'Null per-relation cost when no accepted relations.',
                        'Null full-collection cost when rank/recovery was not reached.',
                        'Controls with different field/order do not isolate torsion.']}, indent=2)+'\n')


if __name__ == '__main__':
    main()
