#!/usr/bin/env sage -python
"""One exact union-polynomial GCD versus direct N41 target screening."""
import hashlib
import json
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n41_first_product_interpolated_eliminant_20261017'
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009/geometry.json'
FLATS = ROOT / 'n41_valid_affine_flat_target_20261017/result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def horner(coefficients, value, zero):
    out = zero
    for coefficient in reversed(coefficients):
        out = out * value + coefficient
    return out


def main():
    signal.alarm(300)
    protocol_path = HERE / 'union_protocol.json'
    protocol = json.loads(protocol_path.read_text())
    paths = {'union.py': Path(__file__), 'union_protocol.json': protocol_path,
             'geometry.json': GEOMETRY, 'flat_result.json': FLATS,
             'witness_result_v2.json': SOURCE / 'witness_result_v2.json',
             'negative_result_v2.json': SOURCE / 'negative_result_v2.json',
             'sweep_result.json': SOURCE / 'sweep_result.json',
             'sage_runtime_info.json': HERE / 'sage_runtime_info.json'}
    source_sha256 = {name: sha(path) for name, path in paths.items()}
    geo = json.loads(GEOMETRY.read_text())
    legal = sorted(geo['permitted_canonical_a'])
    covered = set(json.loads(FLATS.read_text())['covered_masks'])
    assert len(legal) == 40 and len(covered) == 27
    leftover = sorted(set(legal) - covered)
    assert len(leftover) == 13
    F2 = PolynomialRing(GF(2), 't'); t = F2.gen()
    field = GF(2**41, name='t', modulus=t**41+t**3+1)
    zero = field.zero(); one = field.one()
    poly = PolynomialRing(field, 'R'); R = poly.gen()
    def dec(value):
        return field(F2([(int(value) >> i) & 1 for i in range(41)]))
    def product(slot, mask):
        out = 0
        for i, basis in enumerate(geo['blocks'][slot]['product_basis']):
            if mask >> i & 1:
                out ^= basis
        return dec(out)
    products = [[product(slot, mask) for mask in legal] for slot in range(3)]
    by_mask = {mask: products[2][i] for i, mask in enumerate(legal)}
    start = time.perf_counter_ns()
    vanish = poly(one)
    for mask in sorted(covered):
        vanish *= R-by_mask[mask]
    setup_ns = time.perf_counter_ns()-start
    assert vanish.degree() == 27
    assert {mask for mask in legal if vanish(by_mask[mask]) == 0} == covered
    sweep = json.loads((SOURCE / 'sweep_result.json').read_text())
    panels = []
    for label in protocol['panels']:
        tensor = json.loads((SOURCE / (label+'_result_v2.json')).read_text())
        terms = [(qi,ri,[(pi,dec(c)) for pi,c in coeff])
                 for qi,ri,coeff in tensor['coefficient_terms']]
        phase = {'coefficient':0,'direct':0,'union_gcd_route':0}
        direct_zeros = set(); grouped_zeros = set()
        gcd_count = nonconstant = root_checks = 0
        for ip,pvalue in enumerate(products[0]):
            start=time.perf_counter_ns()
            pp=[pvalue**i for i in range(17)]
            specialized=[(qi,ri,sum((c*pp[pi] for pi,c in coeff),zero))
                         for qi,ri,coeff in terms]
            phase['coefficient']+=time.perf_counter_ns()-start
            for iq,qvalue in enumerate(products[1]):
                start=time.perf_counter_ns()
                qp=[qvalue**i for i in range(17)]
                cp=[zero]*25
                for qi,ri,c in specialized:
                    cp[ri]+=c*qp[qi]
                phase['coefficient']+=time.perf_counter_ns()-start
                pair=(legal[ip],legal[iq])
                def direct():
                    for ir,r in enumerate(products[2]):
                        if horner(cp,r,zero)==0:
                            direct_zeros.add(pair+(legal[ir],))
                def grouped():
                    nonlocal gcd_count,nonconstant,root_checks
                    f=poly(cp)
                    g=f.gcd(vanish)
                    gcd_count+=1
                    if g.degree()>0:
                        nonconstant+=1
                        for mask in covered:
                            root_checks+=1
                            if horner(cp,by_mask[mask],zero)==0:
                                grouped_zeros.add(pair+(mask,))
                    for mask in leftover:
                        if horner(cp,by_mask[mask],zero)==0:
                            grouped_zeros.add(pair+(mask,))
                if (ip+iq)&1:
                    start=time.perf_counter_ns();grouped();phase['union_gcd_route']+=time.perf_counter_ns()-start
                    start=time.perf_counter_ns();direct();phase['direct']+=time.perf_counter_ns()-start
                else:
                    start=time.perf_counter_ns();direct();phase['direct']+=time.perf_counter_ns()-start
                    start=time.perf_counter_ns();grouped();phase['union_gcd_route']+=time.perf_counter_ns()-start
        expected={tuple(row['masks']) for row in next(x for x in sweep['panels'] if x['name']==label)['zero_triples']}
        assert direct_zeros==grouped_zeros==expected
        panels.append({'label':label,'phase_ns':phase,'specialized_pair_count':1600,
                       'direct_horner_evaluations':64000,'gcd_count':gcd_count,
                       'nonconstant_gcds':nonconstant,'post_gcd_root_checks':root_checks,
                       'leftover_horner_evaluations':1600*13,
                       'zero_masks':[list(row) for row in sorted(grouped_zeros)]})
        print(label,panels[-1],flush=True)
    result={'status':'PASS_N41_UNION_VANISHING_GCD_MATCHED_SCAN',
            'candidate_id':None,'source_sha256':source_sha256,
            'union_setup_ns':setup_ns,'union_root_count':27,
            'leftover_masks':leftover,'panels':panels,
            'peak_self_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (HERE/'union_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],flush=True)


if __name__=='__main__':
    main()
