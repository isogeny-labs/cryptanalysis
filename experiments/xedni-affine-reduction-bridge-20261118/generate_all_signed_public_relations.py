#!/usr/bin/env python3
"""Generate the thirteen signed public-point group relations."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'xedni-known-relation-lifts-20261118' / 'run-result.json'
TARGET = HERE / 'AllSignedPublicRelations.lean'


def generate():
    raw = SOURCE.read_bytes()
    digest = sha256(raw).hexdigest()
    assert digest == json.loads((HERE / 'protocol.json').read_text())['source_sha256']
    rows = [r for r in json.loads(raw)['rows'] if r['status'] == 'exact_relation']
    assert len(rows) == 13
    lines = [
        'import SignedPublicRelation', '',
        '/-! Exact signed public-point relations for the thirteen frozen xedni lifts. -/',
        f'-- Source SHA-256: {digest}', '',
        'namespace XedniAllSignedPublicRelations', '',
        'open XedniLocalZModReduction XedniRegularChainReduction',
        'open XedniRegularGroupLaw XedniCurveEquationCertificates',
        'open XedniRecordedRegularSteps XedniExactChainMultipliers',
        'open XedniFiniteGroupChains XedniPublicPointReduction',
        'open XedniSignedPublicRelation', '',
    ]
    for p in sorted({r['hit']['p'] for r in rows}):
        lines.append(f'local instance : Fact (Nat.Prime {p}) := ⟨by norm_num⟩')
    lines.append('')
    seen = set()
    for r in rows:
        i, p, A, B = r['hit_index'], r['hit']['p'], r['model']['A'], r['model']['B']
        if (p,A,B) in seen:
            continue
        seen.add((p,A,B))
        lines.extend([
            'local instance :',
            '    (shortCurve',
            f'      (reduceZMod {p} ((algebraMap ℤ (localIntegers {p})) ({A})))',
            f'      (reduceZMod {p} ((algebraMap ℤ (localIntegers {p})) ({B})))).IsElliptic :=',
            f'  row{i}_reduced_elliptic', '',
        ])
    for r in rows:
        i,h = r['hit_index'],r['hit']
        p,a,b = h['p'],h['a'],h['b']
        assert a > 0 and b != 0
        ma,mb = abs(a),abs(b)
        def group_point(m):
            return f'toGroupPoint (mapPoint (reduceZMod {p}) row{i}_m{m}_localPoint)'
        lines.extend([
            f'/-- Row {i}: the reduced starting point. -/',
            f'private noncomputable def row{i}_R := {group_point(1)}',
            f'private noncomputable def row{i}_U := '+ ('' if b > 0 else '-')+group_point(mb),
            f'private noncomputable def row{i}_V := -{group_point(ma)}', '',
        ])
        for m in sorted({ma,mb}):
            chain = '(.refl _)'
            for k in range(m-1,0,-1):
                chain = f'(.step row{i}_step{k} {chain})'
            lines.extend([
                f'theorem row{i}_m{m}_chainN :',
                f'    RegularChainN row{i}_m1_localPoint {m-1} row{i}_m1_localPoint row{i}_m{m}_localPoint := by',
                f'  exact {chain}', '',
                f'theorem row{i}_m{m}_exact :',
                f'    {group_point(m)} = {m} • row{i}_R := by',
                f'  exact reduced_regularChainN_from_self (reduceZMod {p}) row{i}_m{m}_chainN', '',
            ])
        for name,m,sign,xy in [('U',mb,b,h['U']),('V',ma,-a,h['V'])]:
            c = 'neg_toGroupPoint' if sign < 0 else 'toGroupPoint'
            lines.extend([
                f'theorem row{i}_{name}_coords :',
                f'    pointCoords row{i}_{name} = some (({xy[0]} : ZMod {p}), ({xy[1]} : ZMod {p})) := by',
                f'  simp [row{i}_{name}, pointCoords_{c}, row{i}_m{m}_x_public, row{i}_m{m}_y_public] <;> (norm_num <;> decide)', '',
            ])
        lines.extend([
            f'theorem row{i}_public_relation :',
            f'    ({a} : ℤ) • row{i}_U + ({b} : ℤ) • row{i}_V = 0 := by',
            f'  have hU : row{i}_U = ({b} : ℤ) • row{i}_R := by',
            (f'    simp [row{i}_U, row{i}_R] <;> rfl' if mb == 1 else f'    simp [row{i}_U, row{i}_m{mb}_exact] <;> rfl'),
            f'  have hV : row{i}_V = ({-a} : ℤ) • row{i}_R := by',
            (f'    simp [row{i}_V, row{i}_R] <;> rfl' if ma == 1 else f'    simp [row{i}_V, row{i}_m{ma}_exact] <;> rfl'),
            '  rw [hU, hV]',
            f'  exact signed_multiple_relation row{i}_R {a} ({b})', '',
        ])
        for m in sorted({ma,mb}):
            lines.extend([f'#print axioms row{i}_m{m}_chainN',f'#print axioms row{i}_m{m}_exact'])
        lines.extend([f'#print axioms row{i}_U_coords',f'#print axioms row{i}_V_coords',f'#print axioms row{i}_public_relation',''])
    lines.extend(['end XedniAllSignedPublicRelations', ''])
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    want=generate()
    if args.check:
        assert TARGET.read_text()==want, 'generated module differs'
    else:
        TARGET.write_text(want)
    print(json.dumps({'check':args.check,'rows':13}))

if __name__=='__main__':
    main()
