#!/usr/bin/env python3
"""Versioned correction of three notation-only Lean simplification targets."""
import hashlib
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
V1_SHA = 'd544d25b023d94cdb6afd3fe951343112395a6a196eb4b595eb961d72da3404d'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    original = P / 'FloorSix.lean'
    assert sha(original) == V1_SHA
    source = original.read_text()
    replacements = {
        'have h3 : -a1 - b0 = 0': 'have h3 : -a1 + -b0 = 0',
        'have h5 : a1 - b0 = 0': 'have h5 : a1 + -b0 = 0',
        'have h33 : a2 - b1 = 0': 'have h33 : a2 + -b1 = 0',
    }
    for before, after in replacements.items():
        assert source.count(before) == 1
        source = source.replace(before, after)
    output = P / 'FloorSixV2.lean'
    if '--check' in sys.argv:
        assert output.read_text() == source
        status = 'LEAN_V2_SOURCE_MATCH'
    else:
        assert not output.exists()
        output.write_text(source)
        status = 'LEAN_V2_SOURCE_GENERATED'
    print(json.dumps({'status': status, 'source_sha256': sha(output)}, sort_keys=True))

if __name__ == '__main__':
    main()
