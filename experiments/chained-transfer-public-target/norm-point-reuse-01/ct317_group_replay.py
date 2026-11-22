#!/usr/bin/env python3
"""CT317 independently replays a source-curve ECDLP group equation from raw solver bytes.

This is an offline prime-field, <=31-bit, short-Weierstrass grader; it does not
establish that the producing executable ran, or certify a transfer speedup.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile

SCHEMA = 'ct317-group-replay/v1'
HEX = re.compile(r'[0-9a-f]{64}\Z')
RUN_ID = re.compile(r'[A-Za-z0-9_-]{1,80}\Z')


def refuse(message):
    raise ValueError('CT317: ' + message)


def num(x, name, least=0):
    if type(x) is not int or x < least:
        refuse('invalid integer '+name)
    return x


def strict(raw):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                refuse('duplicate JSON key '+k)
            out[k] = v
        return out
    def no_const(x):
        refuse('non-JSON constant '+x)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=no_const)


def prime(n):
    if type(n) is not int or n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    k = 3
    while k*k <= n:
        if n % k == 0:
            return False
        k += 2
    return True


def point(x, p, a, b):
    if type(x) is not list or len(x) != 2:
        refuse('affine point required')
    xx, yy = x
    num(xx, 'x'); num(yy, 'y')
    if xx >= p or yy >= p or (yy*yy-xx*xx*xx-a*xx-b) % p:
        refuse('point off curve or noncanonical coordinate')
    return (xx, yy)


def add(P, Q, p, a):
    if P is None:
        return Q
    if Q is None:
        return P
    x,y=P; u,v=Q
    if x == u and (y+v) % p == 0:
        return None
    if P == Q:
        if y == 0:
            return None
        slope = ((3*x*x+a)*pow((2*y) % p,-1,p)) % p
    else:
        if x == u:
            refuse('inconsistent affine addition')
        slope = ((v-y)*pow((u-x) % p,-1,p)) % p
    xx = (slope*slope-x-u) % p
    return (xx, (slope*(x-xx)-y) % p)


def mul(k, P, p, a):
    R = None
    while k:
        if k & 1:
            R = add(R, P, p, a)
        P = add(P, P, p, a)
        k >>= 1
    return R


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(panel, witness, root):
    # This is an additional gate, not a substitute for the CT315 cost gate.
    if type(panel) is not dict or panel.get('schema') != 'ct315-complete-cold-panel/v1':
        refuse('missing CT315 raw panel')
    rows = panel.get('runs')
    if type(rows) is not list or len(rows) < 28 or len(rows) % 7:
        refuse('incomplete CT315 population')
    if type(witness) is not dict or set(witness) != {
        'schema','curve_id','p','a','b','generator','subgroup_prime','targets'
    } or witness['schema'] != SCHEMA:
        refuse('incorrect witness schema')
    cid = witness['curve_id']
    if type(cid) is not str or not cid:
        refuse('missing curve ID')
    p = num(witness['p'], 'p', 5)
    n = num(witness['subgroup_prime'], 'subgroup_prime', 3)
    if p > 2**31-1 or n > 2**32-1 or not prime(p) or not prime(n):
        refuse('only independently trial-divided <=31-bit primes supported')
    a=num(witness['a'],'a'); b=num(witness['b'],'b')
    if a >= p or b >= p or (4*a*a*a+27*b*b)%p==0:
        refuse('nonsingular canonical short-Weierstrass curve required')
    P=point(witness['generator'],p,a,b)
    if mul(n,P,p,a) is not None:
        refuse('subgroup order does not annihilate generator')
    targets=witness['targets']
    if type(targets) is not list or not targets:
        refuse('no public targets')
    indexed={}
    for t in targets:
        if type(t) is not dict or set(t) != {'target_id','Q'}:
            refuse('malformed target')
        name=t['target_id']
        if type(name) is not str or not name or name in indexed:
            refuse('duplicate/missing target id')
        Q=point(t['Q'],p,a,b)
        if mul(n,Q,p,a) is not None:
            refuse('Q not in claimed source prime subgroup')
        indexed[name]=Q
    used=set(); ids=set()
    for i,row in enumerate(rows):
        if type(row) is not dict or row.get('curve_id') != cid or row.get('subgroup_order') != n:
            refuse('source curve/subgroup mismatch at run '+str(i))
        name=row.get('target_id')
        if name not in indexed:
            refuse('unknown public target')
        used.add(name)
        k=num(row.get('result_scalar'),'result scalar')
        if k>=n or row.get('expected_scalar') != k:
            refuse('scalar or claim mismatch')
        if mul(k,P,p,a) != indexed[name]:
            refuse('recovered scalar fails independent Q=[k]P')
        ident=row.get('run_id')
        if type(ident) is not str or RUN_ID.fullmatch(ident) is None or ident in ids:
            refuse('unsafe or repeated run ID')
        ids.add(ident)
        stdout_hash=row.get('stdout_sha256')
        receipt_hash=row.get('receipt_sha256')
        if any(type(h) is not str or HEX.fullmatch(h) is None for h in (stdout_hash,receipt_hash)):
            refuse('invalid raw evidence SHA')
        # Read-only, exact raw files, no canonicalized stdout or self-generated receipt.
        stdout=(root / (ident+'.stdout')).read_bytes()
        receipt=(root / (ident+'.receipt.json')).read_bytes()
        if digest(stdout) != stdout_hash or digest(receipt) != receipt_hash:
            refuse('unaligned raw stdout/receipt SHA at '+ident)
        record=strict(stdout)
        if type(record) is not dict or set(record) != {'schema','scalar'} or record['schema'] != 'ct317-solver-scalar/v1' or record['scalar'] != k or type(record['scalar']) is not int:
            refuse('noncanonical/mismatched raw solver scalar')
    if used != set(indexed):
        refuse('omitted declared public target')
    return {'schema':'ct317-conditional-group-replay-result/v1',
            'source_curve_prime':p,'subgroup_prime':n,
            'raw_stdout_and_receipt_hashes_rechecked':len(rows),
            'target_group_equations_replayed':len(rows),
            'unique_public_targets':len(used),'actual_native_jacobian_executions':0,
            'execution_authenticity_verified':False,'pcc':'unverified'}


def self_test():
    # p=97, y²=x³+2x+3, P=(3,6) has prime order five.
    w={'schema':SCHEMA,'curve_id':'synthetic-prime97','p':97,'a':2,'b':3,
       'generator':[3,6],'subgroup_prime':5,
       'targets':[{'target_id':'toy-Q','Q':[80,10]}]}
    p={'schema':'ct315-complete-cold-panel/v1','runs':[]}
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp)
        for i in range(28):
            name='toy-%02d'%i
            stdout=b'{"schema":"ct317-solver-scalar/v1","scalar":2}\n'
            receipt=('{"toyReceipt":%d}\n'%i).encode()
            (root/(name+'.stdout')).write_bytes(stdout)
            (root/(name+'.receipt.json')).write_bytes(receipt)
            p['runs'].append({'run_id':name,'curve_id':w['curve_id'],
                'subgroup_order':5,'target_id':'toy-Q','expected_scalar':2,
                'result_scalar':2,'stdout_sha256':digest(stdout),'receipt_sha256':digest(receipt)})
        if audit(p,w,root)['target_group_equations_replayed']!=28:
            raise AssertionError('toy group proof failed')
        mutations=[
            lambda a,b: a['runs'][0].update(result_scalar=3,expected_scalar=3),
            lambda a,b: b['targets'][0].update(Q=[3,6]),
            lambda a,b: b.update(generator=[3,91]),
            lambda a,b: b.update(p=95),
            lambda a,b: b.update(subgroup_prime=6),
            lambda a,b: b.update(b=0),
            lambda a,b: a['runs'][0].update(stdout_sha256='0'*64),
            lambda a,b: a['runs'][0].update(receipt_sha256='0'*64),
            lambda a,b: a['runs'][1].update(run_id='toy-00'),
            lambda a,b: a['runs'][1].update(run_id='../escape'),
            lambda a,b: a['runs'][0].update(expected_scalar=3),
            lambda a,b: a['runs'].pop(),
        ]
        refused=0
        for mut in mutations:
            q=copy.deepcopy(p); v=copy.deepcopy(w)
            mut(q,v)
            try:
                audit(q,v,root)
            except (ValueError,OSError):
                refused+=1
            else:
                raise AssertionError('accepted synthetic corruption #'+str(refused))
        if refused!=len(mutations):
            raise AssertionError('mutation count mismatch')
    return {'schema':'ct317-source-only-selftest/v1',
            'positive_toy_replays':28,'synthetic_mutations_refused':refused,
            'native_models_executed':0,'pcc':'unverified'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--self-test',action='store_true')
    g.add_argument('--panel',type=Path)
    parser.add_argument('--witness',type=Path)
    parser.add_argument('--raw-root',type=Path)
    args=parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(),sort_keys=True))
    else:
        if args.witness is None or args.raw_root is None:
            refuse('--witness and --raw-root are mandatory')
        print(json.dumps(audit(strict(args.panel.read_bytes()),
            strict(args.witness.read_bytes()),args.raw_root),sort_keys=True))


if __name__=='__main__':
    main()
