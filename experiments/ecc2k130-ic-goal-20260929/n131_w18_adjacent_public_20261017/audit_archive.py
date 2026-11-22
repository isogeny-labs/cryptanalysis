#!/usr/bin/env python3
"""Terminal replay using byte-exact compressed XCNF archives."""
import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, indent=2, sort_keys=True)
        file.write('\n')


def paths():
    return {'script': HERE / 'audit_archive.py',
            'control_archive': HERE / 'control.xcnf.gz',
            'ordinary_archive': HERE / 'ordinary.xcnf.gz',
            'first_audit_protocol': HERE / 'audit_protocol.json',
            'first_audit_result': HERE / 'audit_result.json',
            'control_result': HERE / 'control_result.json',
            'query_result': HERE / 'query_result.json'}


def freeze():
    save('archive_protocol.json', {'status': 'FROZEN_ADJACENT_N131_ARCHIVE_REPLAY',
         'source_sha256': {name: sha(path) for name, path in paths().items()}})


def inspect_archive(path):
    digest = hashlib.sha256()
    size = 0
    variables = total = None
    cnf = xor = 0
    with gzip.open(path, 'rb') as file:
        for line in file:
            digest.update(line)
            size += len(line)
            if variables is None:
                words = line.split()
                assert words[:2] == [b'p', b'cnf']
                variables, total = map(int, words[2:4])
            elif line.startswith(b'x '):
                xor += 1
            else:
                cnf += 1
    assert total == cnf + xor
    return {'sha256': digest.hexdigest(), 'bytes': size,
            'variables': variables, 'cnf': cnf, 'xor': xor}


def run():
    protocol = load('archive_protocol.json')
    assert protocol['status'] == 'FROZEN_ADJACENT_N131_ARCHIVE_REPLAY'
    assert protocol['source_sha256'] == {name: sha(path) for name, path in paths().items()}
    first_protocol = load('audit_protocol.json')
    first_result = load('audit_result.json')
    assert first_result['status'] == 'PASS_ADJACENT_N131_QUERY_AUDIT'
    assert first_result['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    control, query = load('control_result.json'), load('query_result.json')
    rows = {}
    for name, profile in (('control', control['formula']), ('ordinary', query['formula'])):
        archive = HERE / f'{name}.xcnf.gz'
        actual = inspect_archive(archive)
        assert actual == {'sha256': profile['xcnf_sha256'],
                          'bytes': profile['xcnf_bytes'],
                          'variables': profile['variables'],
                          'cnf': profile['clauses'],
                          'xor': profile['native_xor_rows']}
        assert first_protocol['source_sha256'][f'{name}_xcnf'] == actual['sha256']
        rows[name] = {'archive_sha256': sha(archive), **actual}
    save('archive_result.json', {'status': 'PASS_ADJACENT_N131_ARCHIVE_REPLAY',
         'protocol_sha256': sha(HERE / 'archive_protocol.json'),
         'source_sha256': protocol['source_sha256'], 'formulas': rows,
         'query_status': first_result['query_status']})
    print('PASS_ADJACENT_N131_ARCHIVE_REPLAY')


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
