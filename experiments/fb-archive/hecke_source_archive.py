"""Rebuild small projected Hecke bases from immutable, independently replayed receipts.

This is a source-snapshot rebuild, not a new CM class enumeration.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
STUDY=ROOT/'experiments/hecke-sparse-target-20261030'
CASES={11587:'f6-small-01',163567:'f6-medium-01',1032607:'f6-large-01',231559:'f30-01'}


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'))
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()


def build(n,l,seed,points):
    if n!=1 or seed not in CASES:raise ValueError('unsupported frozen Hecke source recipe')
    path=STUDY/'runs'/CASES[seed]/'receipt.json'
    raw=path.read_bytes();source=json.loads(raw)
    if source['p']!=seed or source['f']!=l or source['status']!='verified_finite_diagnostic':
        raise ValueError('Hecke recipe/source mismatch')
    replay=json.loads((STUDY/'runs/independent-01/receipt.json').read_text())
    matches=[r for r in replay['results'] if r['p']==seed]
    if len(matches)!=1 or matches[0]['receipt_sha256']!=hashlib.sha256(raw).hexdigest():
        raise ValueError('Hecke source lacks matching independent replay')
    p=source['p'];base=set()
    for x,y in source['normalized_base']:
        if (y*y+y-x*x*x+x*x+10*x+20)%p:raise ValueError('invalid archived curve point')
        base.add((x,y));base.add((x,(-y-1)%p))
    usable=[list(P) for P in sorted(base)]
    rec=dict(curve_id=source['identity']['curve_id'],
             construction=dict(family='heckecm',basis=None,params=dict(DK=-39,conductor=l,projection=source['h']),
                               polynomial_constraint='projected rational X0(11) lifts of the saved CM class',
                               shifted_bases='none'),
             subgroup_policy='cofactor projection to the declared prime-order subgroup',
             enumerated_set_sha256=digest(usable) if points else None,nominal_dimension=None,
             geometric_point_count=source['C'] if points else None,
             actual_usable_point_count=len(usable) if points else None,
             strict_subgroup_point_count=len(usable) if points else None,
             quotient_rule='negation',effective_columns=len(source['normalized_base']) if points else None)
    return dict(field=source['field'],curve=dict(source['curve'],curve_id=source['identity']['curve_id']),
                factor_base=rec,points=usable if points else None,point_columns=None,
                column_representatives=source['normalized_base'] if points else None,
                builder='fb-archive/hecke_source_archive.py: immutable source snapshot',
                source_receipt=str(path.relative_to(ROOT)),source_receipt_sha256=hashlib.sha256(raw).hexdigest())
