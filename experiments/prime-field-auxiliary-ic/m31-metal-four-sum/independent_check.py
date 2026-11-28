#!/usr/bin/env python3
"""Independent affine check of the public scalar answers in a raw panel."""
import json
import sys

P=2_147_483_647
G=(1,814455902)

def add(a,b):
    if a is None: return b
    if b is None: return a
    x,y=a; u,v=b
    if x==u and (y+v)%P==0: return None
    if x==u:
        slope=((3*x*x+2)*pow(2*y,-1,P))%P
    else:
        slope=((v-y)*pow((u-x)%P,-1,P))%P
    nx=(slope*slope-x-u)%P
    return nx,(slope*(x-nx)-y)%P

def mul(n,a):
    result=None
    while n:
        if n&1: result=add(result,a)
        a=add(a,a); n>>=1
    return result

def main(path):
    rows=[json.loads(line) for line in open(path)]
    assert len(rows)==30
    pairs={}
    for row in rows:
        assert row['returncode']==0 and not row['timeout']
        out=json.loads(row['stdout'])
        assert out['status']=='solved' and out['Q']==row['Q'] and out['seed']==row['seed']
        q=tuple(row['Q']); scalar=out['scalar']
        assert mul(scalar,G)==q,(q,scalar)
        key=(row['target'],row['seed'])
        pairs.setdefault(key,{})[row['mode']]=out
    assert len(pairs)==15
    for key,pair in pairs.items():
        assert set(pair)=={'cpu','metal'}
        for field in ['scalar','certificate_digest','queries','relations','rank']:
            assert pair['cpu'][field]==pair['metal'][field],(key,field)
    schemas={json.loads(row['stdout'])['schema'] for row in rows}
    assert len(schemas)==1
    digest_scope='complete_fields' if schemas=={'m31-metal-full-rust/v2'} else 'relations_only'
    print(json.dumps({'arms':len(rows),'pairs':len(pairs),'independent_public_group_checks':len(rows),
                      'cross_arm_digest_checks':len(pairs),'digest_scope':digest_scope,'status':'pass'}))

if __name__=='__main__': main(sys.argv[1])
