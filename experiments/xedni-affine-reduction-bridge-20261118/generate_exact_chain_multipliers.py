#!/usr/bin/env python3
"""Generate exact-length endpoint certificates from frozen recorded paths."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'xedni-known-relation-lifts-20261118' / 'run-result.json'
TARGET = HERE / 'ExactChainMultipliers.lean'
START = '-- BEGIN GENERATED ROWS\n'
END = '-- END GENERATED ROWS\n'


def generated_rows():
    source_bytes = SOURCE.read_bytes()
    expected = json.loads((HERE / 'protocol.json').read_text())['source_sha256']
    assert sha256(source_bytes).hexdigest() == expected
    rows = [r for r in json.loads(source_bytes)['rows'] if r['status'] == 'exact_relation']
    assert len(rows) == 13
    lines = [f'-- Source SHA-256: {expected}', '']
    seen = {(313, -1, 15961)}
    for r in rows:
        p, A, B = r['hit']['p'], r['model']['A'], r['model']['B']
        if p != 313 and p not in {x[0] for x in seen}:
            lines.append(f'local instance : Fact (Nat.Prime {p}) := ⟨by norm_num⟩')
        if (p, A, B) not in seen:
            lines.extend([
                'local instance :',
                '    (shortCurve',
                f'      (reduceZMod {p} ((algebraMap ℤ (localIntegers {p})) ({A})))',
                f'      (reduceZMod {p} ((algebraMap ℤ (localIntegers {p})) ({B})))).IsElliptic :=',
                f'  row{r["hit_index"]}_reduced_elliptic',
                '',
            ])
        seen.add((p, A, B))
    for r in rows:
        i = r['hit_index']
        p = r['hit']['p']
        last = max(abs(r['hit']['a']), abs(r['hit']['b']))
        assert last >= 2
        chain = '(.refl _)'
        for k in range(last-1, 0, -1):
            chain = f'(.step row{i}_step{k} {chain})'
        lines.extend([
            f'/-- Row {i}: the recorded path has exactly {last-1} additions. -/',
            f'theorem row{i}_chainN :',
            f'    RegularChainN row{i}_m1_localPoint {last-1} row{i}_m1_localPoint row{i}_m{last}_localPoint := by',
            f'  exact {chain}',
            '',
            f'theorem row{i}_exact :',
            f'    toGroupPoint (mapPoint (reduceZMod {p}) row{i}_m{last}_localPoint) =',
            f'      {last} • toGroupPoint (mapPoint (reduceZMod {p}) row{i}_m1_localPoint) := by',
            f'  exact reduced_regularChainN_from_self (reduceZMod {p}) row{i}_chainN',
            '',
            f'#print axioms row{i}_chainN',
            f'#print axioms row{i}_exact',
            '',
        ])
    return '\n'.join(lines).rstrip()+'\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    current = TARGET.read_text()
    prefix, rest = current.split(START, 1)
    _, suffix = rest.split(END, 1)
    want = prefix + START + generated_rows() + END + suffix
    if args.check:
        assert current == want, 'ExactChainMultipliers.lean differs from generated rows'
    else:
        TARGET.write_text(want)
    print(json.dumps({'check': args.check, 'rows': 13}))


if __name__ == '__main__':
    main()
