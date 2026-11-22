#!/usr/bin/env python3
"""Generate checked reductions of selected rational multiples to public points."""
import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from run import add_rat, reduce_point

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'xedni-known-relation-lifts-20261118' / 'run-result.json'
TARGET = HERE / 'PublicPointReduction.lean'
START = '-- BEGIN GENERATED ROWS\n'
END = '-- END GENERATED ROWS\n'


def rows_text():
    raw = SOURCE.read_bytes()
    digest = sha256(raw).hexdigest()
    assert digest == json.loads((HERE / 'protocol.json').read_text())['source_sha256']
    rows = [r for r in json.loads(raw)['rows'] if r['status'] == 'exact_relation']
    assert len(rows) == 13
    lines = [f'-- Frozen source SHA-256: {digest}', '']
    for p in sorted({r['hit']['p'] for r in rows}):
        lines.append(f'local instance : Fact (Nat.Prime {p}) := ⟨by norm_num⟩')
    lines.append('')
    for r in rows:
        i, h = r['hit_index'], r['hit']
        p, a, b = h['p'], h['a'], h['b']
        A, B = r['model']['A'], r['model']['B']
        T = tuple(Fraction(z) for z in r['model']['T'])
        selected = {1, abs(a), abs(b)}
        P = T
        for m in range(1, max(selected)+1):
            if m > 1:
                P, _, _ = add_rat(P, T, A)
            if m not in selected:
                continue
            xred, yred = reduce_point(P, p)
            if m == 1:
                assert [xred, yred] == r['R']
            if m == abs(b):
                assert xred == h['U'][0] and (yred if b > 0 else (-yred)%p) == h['U'][1]
            if m == abs(a):
                assert xred == h['V'][0] and (yred if a < 0 else (-yred)%p) == h['V'][1]
            for coord, value, residue in zip(('x','y'), P, (xred,yred)):
                stem = f'row{i}_m{m}_{coord}_public'
                q = f'(({value.numerator} : ℚ) / ({value.denominator} : ℚ))'
                lines.extend([
                    f'/-- Row {i}, {m}T: reduced {coord} coordinate. -/',
                    f'theorem {stem} :',
                    f'    (mapPoint (reduceZMod {p}) row{i}_m{m}_localPoint).{coord} = ({residue} : ZMod {p}) := by',
                    f'  change reduceZMod {p} (toLocal {p} {q} row{i}_m{m}_{coord}) = {residue}',
                    '  rw [reduce_rational]',
                    '  norm_num <;> (first | decide | (apply (div_eq_iff (by norm_num <;> decide)).2; norm_num <;> decide))',
                    '',
                    f'#print axioms {stem}',
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
    want = prefix + START + rows_text() + END + suffix
    if args.check:
        assert current == want, 'PublicPointReduction.lean differs from generated rows'
    else:
        TARGET.write_text(want)
    print(json.dumps({'check':args.check,'rows':13,'selected_points':sum(len({1,abs(r['hit']['a']),abs(r['hit']['b'])}) for r in json.loads(SOURCE.read_text())['rows'] if r['status']=='exact_relation')}))


if __name__ == '__main__':
    main()
