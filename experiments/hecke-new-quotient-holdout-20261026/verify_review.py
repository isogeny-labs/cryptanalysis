#!/usr/bin/env python3
"""Check the historical bundle and its explicit current-source review version.

This leaves SEAL.json and seal.py unchanged. Hydrate producer.stdout first.
"""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SEAL_SHA = '2a8b4c5974aa939e968c08bc64df65e4e46aa28bce7a8799328ed395d6ef4df5'
OLD_SHA = '710bbf06230e206b433fd856d2d996a0951494389b58f9448322d9fd7f7a1442'
CURRENT_SHA = '217d9a05ff5483fc27115d583a4a0d26539f5583a003c184fe126368a7a3290a'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def statement_and_body(text):
    return '\n'.join(line.replace('public theorem ', 'theorem ')
                     for line in text.splitlines() if line.strip() and not line.startswith('#print axioms '))


def verify(root):
    require(digest(root/'SEAL.json') == SEAL_SHA, 'original seal changed')
    seal = json.loads((root/'SEAL.json').read_text())
    provenance = json.loads((root/'review-20261030/provenance.json').read_text())
    require(provenance['original_seal_sha256'] == SEAL_SHA, 'wrong historical seal binding')
    require(provenance['sealed_source_sha256'] == OLD_SHA, 'wrong historical source binding')
    require(provenance['current_source_sha256'] == CURRENT_SHA, 'wrong current source binding')
    old = root/'review-20261030/MixedSix.sealed.lean.txt'
    current = root/'formal/MixedSix.lean'
    require(digest(old) == OLD_SHA, 'historical proof source changed')
    require(digest(current) == CURRENT_SHA, 'current proof source changed')
    require(statement_and_body(old.read_text()) == statement_and_body(current.read_text()),
            'theorem statements, hypotheses or proof bodies changed')
    for path, expected in seal['files'].items():
        source = old if path == 'formal/MixedSix.lean' else root/path
        require(digest(source) == expected, f'historical sealed file changed: {path}')
    manifest = json.loads((root/'review-20261030/visuals-manifest.json').read_text())
    for path, record in manifest['files'].items():
        require(digest(root/path) == record['sha256'], f'review file changed: {path}')
        require((root/path).stat().st_size == record['bytes'], f'review file size changed: {path}')
    return len(seal['files']), len(manifest['files'])


def self_test():
    mutations = ['RESULT.md', 'formal/MixedSix.lean',
                 'review-20261030/MixedSix.sealed.lean.txt', 'RESULT_REVIEWED.md']
    for path in mutations:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp)/'study'
            shutil.copytree(HERE, copy)
            changed = copy/path
            changed.write_bytes(changed.read_bytes()+b'\ncorrupted-byte-control\n')
            try:
                verify(copy)
            except ValueError:
                continue
            raise AssertionError(f'accepted corruption: {path}')
    print('PASS: historical result, current proof, archived proof and reviewed-report corruptions rejected')


if __name__ == '__main__':
    historical, reviewed = verify(HERE)
    print(f'PASS: {historical} original sealed files, explicit source transition, {reviewed} review files')
    if '--self-test' in sys.argv:
        self_test()
