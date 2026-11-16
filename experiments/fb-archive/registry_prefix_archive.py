"""Rebuild declared registry-curve prefix bases independently of the Rust suite."""
import hashlib
import json
from pathlib import Path
import yaml
from purepy import PyField
from external import _smul

ROOT=Path(__file__).resolve().parents[2]


def canonical(v):
    return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False)


def digest(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()


def integer(v):
    return int(v,0) if isinstance(v,str) and v.startswith('0x') else int(v)


def build(n,l,seed,points,extra):
    if seed!=0 or set(extra)!={'registry_alias'} or not points:
        raise ValueError('registry-prefix requires seed0, points, and registry_alias')
    entry=yaml.safe_load((ROOT/'experiments/ic-candidate-catalog/curves.yaml').read_text())['curves'][extra['registry_alias']]
    field,curve=entry['field'],entry['curve']
    if field.get('degree')!=n or field.get('characteristic')!=2 or not 1<=l<=min(n,12):
        raise ValueError('unsupported registry-prefix field/dimension')
    identity={'field':field,'curve':curve}
    if digest(identity)!=entry['curve_uid'].rsplit(':',1)[1]:
        raise ValueError('registry identity mismatch')
    modulus=sum(1<<e for e in field['modulus_exponents'])
    K=PyField(n,modulus)
    a,b=map(integer,(curve['coefficients'][1],curve['coefficients'][4]))
    r,h=map(integer,(curve['subgroup_order'],curve['cofactor']))
    G=tuple(map(integer,curve['generator']))
    if _smul(K,a,G,r) is not None or _smul(K,a,G,1)!=G:
        raise ValueError('generator membership mismatch')
    if r<2 or any(r%d==0 for d in range(2,int(r**.5)+1)):
        raise ValueError('nonprime declared subgroup')
    # Solve u^2+u=c by elimination, independently of native field arithmetic.
    pivots={}
    for i in range(n):
        v=(1<<i); image=K.sqr(v)^v
        while image:
            lead=image.bit_length()-1
            if lead not in pivots:
                pivots[lead]=(image,v);break
            row,pre=pivots[lead];image^=row;v^=pre
    def solve(c):
        u=0
        while c:
            lead=c.bit_length()-1
            if lead not in pivots:return None
            row,pre=pivots[lead];c^=row;u^=pre
        return u
    base=[];labels=[];representatives=[];strict=0;torsion=0
    for x in range(1,1<<l):
        u=solve(x^a^K.mul(b,K.sqr(K.inv(x))))
        if u is None:continue
        y=K.mul(x,u);col=len(representatives);representatives.append([x,y])
        for yy,coefficient in [(y,1),(y^x,r-1)]:
            P=(x,yy)
            if K.sqr(yy)^K.mul(x,yy)^K.mul(K.sqr(x),x)^K.mul(a,K.sqr(x))^b:
                raise ValueError('point fails curve equation')
            strict+=_smul(K,a,P,r) is None
            torsion+=_smul(K,a,P,h) is None
            base.append([x,yy]);labels.append([col,coefficient])
    if torsion:
        raise ValueError('prefix contains pure torsion; usable-point policy unresolved')
    ordered=sorted(zip(base,labels))
    base=[p for p,_ in ordered];labels=[label for _,label in ordered]
    rec={'curve_id':entry['curve_id'],'construction':{'family':'registry-prefix','basis':[1<<i for i in range(l)],
         'params':{'registry_alias':extra['registry_alias'],'exclude_x_zero':True},'polynomial_constraint':'none','shifted_bases':'none'},
         'subgroup_policy':'full curve lifts, relations reduced in the prime-order cofactor quotient; no pure torsion',
         'enumerated_set_sha256':digest(base),'nominal_dimension':l,'geometric_point_count':len(base),
         'actual_usable_point_count':len(base),'strict_subgroup_point_count':strict,
         'quotient_rule':'sign, with prime-order cofactor quotient logarithms','effective_columns':len(representatives)}
    return {'field':field,'curve':dict(curve,curve_id=entry['curve_id']), 'factor_base':rec,
            'points':base,'point_columns':labels,'column_representatives':representatives,
            'builder':'experiments/fb-archive/registry_prefix_archive.py; pure Python field and group arithmetic',
            'source_registry_alias':extra['registry_alias']}
