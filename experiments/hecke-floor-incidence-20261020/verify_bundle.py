#!/usr/bin/env python3
"""Read-only seal and outcome replay for the two-cell signed-incidence bundle."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent

def sha(name):
    return hashlib.sha256((P / name).read_bytes()).hexdigest()

def record(name):
    return json.loads((P / name).read_text())

def main():
    manifest = record('manifest.json')
    assert manifest['status'] == 'SEALED_D15_GATE_D183_TEN_FLOOR_DIRECTIONS'
    actual = {
        str(p.relative_to(P)): sha(str(p.relative_to(P)))
        for p in P.rglob('*') if p.is_file() and '.lake' not in p.parts
        and '__pycache__' not in p.parts and p.name != 'manifest.json'
    }
    assert actual == manifest['files'], 'file set or bytes changed'
    for name in ('protocol.json', 'protocol_D183.json',
                 'audit_D15_gate_protocol.json', 'audit_protocol_D183.json',
                 'validation_protocol_D183.json', 'formal_protocol_D183.json',
                 'formal_protocol_local.json', 'floor_dependency_amendment.json'):
        d = record(name)
        for path, digest in d.get('input_sha256', {}).items():
            assert sha(path) == digest, (name, path)
        for path, digest in d.get('files', {}).items():
            assert sha(path) == digest, (name, path)
    for name, protocol, source in (
        ('launch.json', 'protocol.json', 'data/exp11_class_walk_D15_f6.json'),
        ('launch_D183.json', 'protocol_D183.json', 'data/exp11_class_walk_D183_f6.json')):
        receipt = record(name)
        assert receipt['status'] == 'PROCESS_COMPLETE' and receipt['exit_code'] == 0
        assert receipt['protocol_sha256'] == sha(protocol)
        assert receipt['result_sha256'] == sha(source)
    gate = record('audit_D15_gate.json')
    assert gate['status'] == 'D15_F6_RATIONAL_X0_11_GATE_FAILED'
    assert gate['matrix_rank'] is None and gate['quadratic_character_at_11'] == -1
    assert len(gate['cm_j_records']) == 2
    assert all(not row['rational_modular_neighbours'] for row in gate['cm_j_records'])
    audit = record('audit_D183.json')
    floor = record('floor_D183.json')
    validation = record('validation_D183.json')
    assert audit['status'] == 'VERIFIED_D183_F6_MATRIX'
    assert audit['point_count'] == 128 and audit['matched_rows'] == 96
    assert floor['status'] == 'VERIFIED_D183_F6_FLOOR_PREDICTION'
    assert all(floor[k] for k in ('graph_match', 'pair_match', 'span_match', 'rank_match'))
    assert validation['status'] == 'EXACT_D183_F6_TEN_FLOOR_DIRECTIONS'
    assert validation['ranks']['QQ']['2+3'] == [80, 70]
    assert validation['independent_floor_directions'] == 10
    for name, theorem in (
        ('lean-check.txt', 'D183Floor.ten_floor_vectors_independent'),
        ('local-span-check.txt', 'FloorIncidence.disjoint_pair_span_iff')):
        output = (P / name).read_text()
        assert theorem in output
        assert '[propext, Classical.choice, Quot.sound]' in output
        assert 'sorryAx' not in output and 'error:' not in output
    print(json.dumps({'status': manifest['status'], 'files': len(actual),
                      'manifest_sha256': sha('manifest.json'),
                      'D15': 'rational_X0_11_gate_failed',
                      'D183_full_rank': 80, 'D183_nonfloor_rank': 70,
                      'D183_floor_directions': 10}, sort_keys=True))

if __name__ == '__main__':
    main()
