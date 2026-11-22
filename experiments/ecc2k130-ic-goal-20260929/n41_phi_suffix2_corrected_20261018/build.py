"""Freeze corrected suffix-pair support on partial8 of the unpinned N41 chain."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'n41_phi_second_link_control_20261009'
OLD = HERE.parent / 'n41_phi_suffix2_guided_20261009'
N, DIM, M = 41, 6, 12
PARTIAL8 = 2 + M * DIM + 8 * N


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, obj):
    with path.open('x') as out:
        json.dump(obj, out, sort_keys=True, indent=2)
        out.write('\n')


def main():
    previous = json.loads((BASE / 'protocol.json').read_text())
    suffix = json.loads((OLD / 'suffix_masks.json').read_text())
    old_protocol = json.loads((OLD / 'protocol.json').read_text())
    assert previous['target_count'] == old_protocol['target_count'] == 1
    assert suffix['status'] == 'FROZEN_ENUMERATION'
    assert suffix['enumerated_signed_pairs'] == 3600
    assert suffix['nonfinite_residual_cases'] == 0
    assert len(suffix['masks']) == 3577
    assert old_protocol['source_sha256']['suffix'] == sha(OLD / 'suffix_masks.json')
    assert previous['source_sha256']['source'] == sha(BASE / 'source.xcnf')
    assert previous['source_sha256']['solver'] == sha(previous['solver'])
    original = BASE / 'source.xcnf'
    destination = HERE / 'guided_partial8.xcnf'
    masks = suffix['masks']
    with original.open('rt', encoding='ascii') as src, destination.open('x', encoding='ascii') as out:
        header = src.readline().split()
        assert header == ['p', 'cnf', '34334', '52397']
        old_vars, old_records = int(header[2]), int(header[3])
        out.write('p cnf %d %d\n' % (old_vars + len(masks),
                                      old_records + len(masks) * N + 1))
        for line in src:
            out.write(line)
        for index, mask in enumerate(masks):
            selector = old_vars + index + 1
            for bit in range(N):
                variable = PARTIAL8 + bit
                literal = variable if mask >> bit & 1 else -variable
                out.write('%d %d 0\n' % (-selector, literal))
        out.write(' '.join(str(old_vars + index + 1) for index in range(len(masks))) + ' 0\n')
    source_paths = {'source_formula': original,
                    'old_suffix': OLD / 'suffix_masks.json',
                    'old_protocol': OLD / 'protocol.json',
                    'old_preflight': OLD / 'preflight.json',
                    'base_protocol': BASE / 'protocol.json',
                    'base_table': BASE / 'table.json',
                    'solver': Path(previous['solver']),
                    'build.py': HERE / 'build.py',
                    'audit_sage.py': HERE / 'audit_sage.py',
                    'run.py': HERE / 'run.py',
                    'verify.py': HERE / 'verify.py',
                    'sage_runtime_info': HERE / 'sage_runtime_info.json',
                    'guided_formula': destination}
    sources = {name: {'path': str(path), 'sha256': sha(path)}
               for name, path in source_paths.items()}
    protocol = {'status': 'FROZEN_BEFORE_SOLVER', 'candidate_id': None,
                'curve_id': previous['curve_id'], 'workload_id': previous['workload_id'],
                'target_count': 1, 'target_coordinates': previous['target_coordinates'],
                'endpoint_coordinates': previous['endpoint_coordinates'],
                'summand_count': M, 'domain_dimension': DIM,
                'source_header': header,
                'guided_header': ['p', 'cnf', str(old_vars + len(masks)),
                                  str(old_records + len(masks) * N + 1)],
                'partial_index': 8, 'partial_variables': list(range(PARTIAL8, PARTIAL8 + N)),
                'suffix_positions': [10, 11],
                'signed_suffix_pairs': 3600, 'finite_mask_count': len(masks),
                'solver_flags': previous['solver_flags'],
                'per_arm_parent_wall_cap_seconds': 240,
                'campaign_parent_wall_cap_seconds': 550,
                'rss_cap_bytes': 4294967296,
                'arms': ['source_unpinned', 'guided_partial8_unpinned'],
                'sources': sources}
    dump(HERE / 'protocol.json', protocol)
    print(json.dumps({'status': protocol['status'], 'partial_index': 8,
                      'masks': len(masks), 'guided_sha256': sha(destination),
                      'protocol_sha256': sha(HERE / 'protocol.json')}, sort_keys=True))


if __name__ == '__main__':
    main()
