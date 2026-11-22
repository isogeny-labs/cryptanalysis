#!/usr/bin/env python3
"""Read-only byte and status replay for the sealed D39/f6 holdout."""
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
    assert manifest['status'] == 'SEALED_D39_F6_SIX_FLOOR_DIRECTIONS'
    actual = {
        str(p.relative_to(P)): sha(str(p.relative_to(P)))
        for p in P.rglob('*') if p.is_file() and '.lake' not in p.parts
        and p.name != 'manifest.json' and '__pycache__' not in p.parts
    }
    assert actual == manifest['files'], 'file set or bytes changed'
    for name in ('protocol.json', 'audit_protocol.json',
                 'validation_protocol.json', 'formal_protocol.json',
                 'formal_protocol_v2.json'):
        d = record(name)
        for path, digest in d.get('input_sha256', {}).items():
            assert sha(path) == digest, (name, path)
        for path, digest in d.get('files', {}).items():
            assert sha(path) == digest, (name, path)
    protocol = record('protocol.json')
    launch = record('launch.json')
    audit = record('audit.json')
    floor = record('floor.json')
    validation = record('validation.json')
    assert protocol['status'] == 'FROZEN_BEFORE_D39_F6_PRODUCER'
    assert protocol['subset_rank_predicted']['2+3'] == [40, 36]
    assert launch['status'] == 'PROCESS_COMPLETE' and launch['exit_code'] == 0
    assert launch['result_sha256'] == sha('data/exp11_class_walk_D39_f6.json')
    assert audit['status'] == 'VERIFIED_D39_F6_MATRIX'
    assert audit['point_count'] == 64 and audit['matched_rows'] == 48
    assert floor['status'] == 'VERIFIED_D39_F6_FLOOR_MISMATCH'
    assert floor['graph_match'] and floor['pair_match']
    assert not floor['span_match'] and not floor['rank_match']
    assert validation['status'] == 'EXACT_D39_F6_SIX_FLOOR_DIRECTIONS'
    assert validation['ranks']['QQ']['2+3'] == [40, 34]
    assert validation['independent_floor_directions'] == 6
    assert 'sorryAx' in (P / 'lean-check.txt').read_text()
    for name in ('lean-check-v2.txt', 'lean-build-v2.txt'):
        output = (P / name).read_text()
        assert 'D39Floor.six_floor_vectors_independent' in output
        assert '[propext, Classical.choice, Quot.sound]' in output
        assert 'sorryAx' not in output and 'error:' not in output
    print(json.dumps({
        'status': manifest['status'],
        'files': len(actual),
        'manifest_sha256': sha('manifest.json'),
        'full_rank': 40,
        'nonfloor_rank': 34,
        'floor_directions': 6,
        'lean_axioms': ['propext', 'Classical.choice', 'Quot.sound'],
    }, sort_keys=True))

if __name__ == '__main__':
    main()
