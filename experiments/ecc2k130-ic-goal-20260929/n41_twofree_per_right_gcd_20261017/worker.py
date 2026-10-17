#!/usr/bin/env sage -python
"""Test two free product spans one right product at a time at degree <=16."""
import hashlib,json,resource,signal,time
from pathlib import Path
from sage.all import GF,PolynomialRing

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
OLD=ROOT/'n41_twofree_symbolic_resultant_replay_20261016'
GEO=ROOT/'n41_w8_fixed_sum_table_20261009/geometry.json'
FILES={'worker':HERE/'worker.py','geometry':GEO,'witness':OLD/'result.json',
       'negative':OLD/'control_result.json','joint':OLD/'joint_result.json',
       'negative_joint':OLD/'control_joint_result.json','runtime':HERE/'sage_runtime_info.json'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def independent(values):
    pivots={};out=[]
    for original in values:
        v=original
        while v:
            k=v.bit_length()-1
            if k in pivots:v^=pivots[k]
            else:pivots[k]=v;out.append(original);break
    return out
def span(basis):
    out=[0]
    for b in basis:out += [x^b for x in out]
    return out
def annihilator(field,basis):
    coeffs=[field.one()]
    for v in basis:
        alpha=sum((c*v**(1<<i) for i,c in enumerate(coeffs)),field.zero())
        assert alpha
        nxt=[field.zero()]*(len(coeffs)+1)
        for i,c in enumerate(coeffs):nxt[i]+=alpha*c;nxt[i+1]+=c**2
        coeffs=nxt
    return coeffs
def main():
    signal.alarm(120)
    proto=json.loads((HERE/'protocol.json').read_text())
    assert proto['source_sha256']=={k:sha(v) for k,v in FILES.items()}
    poly=PolynomialRing(GF(2),'t');t=poly.gen()
    field=GF(2**41,name='t',modulus=t**41+t**3+1)
    def dec(v):return field(poly([(v>>i)&1 for i in range(41)]))
    def enc(v):return sum(int(b)<<i for i,b in enumerate(v.polynomial().list()))
    ring=PolynomialRing(field,'q');q=ring.gen()
    geometry=json.loads(GEO.read_text());blocks=geometry['blocks']
    qb=independent(blocks[1]['product_basis']);rb=independent(blocks[2]['product_basis'])
    assert len(qb)==len(rb)==7
    qspan=sorted(span(qb));rspan=sorted(span(rb))
    L=sum((c*q**(1<<i) for i,c in enumerate(annihilator(field,[dec(v) for v in qb]))),ring.zero())
    assert L.degree()==128
    assert all(L(dec(v))==0 for v in qspan)
    def product(block,mask):
        out=0
        for i,v in enumerate(blocks[block]['product_basis']):
            if mask>>i&1:out^=v
        return out
    valid_masks=geometry['permitted_canonical_a']
    qvalid=set(product(1,m) for m in valid_masks)
    rvalid=set(product(2,m) for m in valid_masks)
    assert len(qvalid)==len(rvalid)==40
    out=[]
    for name,symbolic_path,joint_path in [('witness',FILES['witness'],FILES['joint']),
                                          ('negative',FILES['negative'],FILES['negative_joint'])]:
        symbolic=json.loads(symbolic_path.read_text())
        terms=[(powers[0],powers[1],dec(value)) for powers,value in symbolic['terms']]
        assert max(i for i,_,_ in terms)==16 and max(j for _,j,_ in terms)==24
        panel_start=time.monotonic_ns();gcd_ns=0;specialize_ns=0;direct_ns=0
        matches=[];valid_matches=[];degree_hist={};zero_polynomials=0
        checkpoints=[]
        for index,rv in enumerate(rspan,1):
            begin=time.monotonic_ns();rvalue=dec(rv)
            powers={j:rvalue**j for _,j,_ in terms}
            coeffs=[field.zero()]*17
            for i,j,c in terms:coeffs[i]+=c*powers[j]
            f=ring(coeffs)
            specialize_ns+=time.monotonic_ns()-begin
            degree=int(f.degree()) if f else -1
            degree_hist[str(degree)]=degree_hist.get(str(degree),0)+1
            begin=time.monotonic_ns()
            if f==0:
                zero_polynomials+=1;roots=qspan
            elif degree==0:roots=[]
            else:
                rem=L%f
                g=f.gcd(rem).monic()
                roots=sorted(enc(v) for v,_ in g.roots())
            gcd_ns+=time.monotonic_ns()-begin
            begin=time.monotonic_ns()
            direct=[v for v in qspan if f(dec(v))==0]
            direct_ns+=time.monotonic_ns()-begin
            assert roots==direct,(name,rv,roots,direct)
            matches.extend((v,rv) for v in roots)
            if rv in rvalid:valid_matches.extend((v,rv) for v in roots if v in qvalid)
            if index in (8,32,128):checkpoints.append({'processed':index,
                   'elapsed_ns':time.monotonic_ns()-panel_start})
        archived=json.loads(joint_path.read_text())
        assert sorted(set(rv for _,rv in matches))==archived['panels'][0]['span_roots']
        assert sorted(valid_matches)==archived['panels'][1]['usable_r_matches']
        out.append({'name':name,'right_products':len(rspan),'valid_right_products':len(rvalid),
                    'left_span_size':len(qspan),'max_specialized_degree':max(int(k) for k in degree_hist),
                    'degree_histogram':degree_hist,'identically_zero_specializations':zero_polynomials,
                    'matches':matches,'valid_matches':valid_matches,
                    'specialize_ns':specialize_ns,'gcd_ns':gcd_ns,'direct_replay_ns':direct_ns,
                    'panel_ns':time.monotonic_ns()-panel_start,'checkpoints':checkpoints})
    result={'status':'PASS_PER_RIGHT_LOW_DEGREE_GCD','candidate_id':None,
            'curve_id':'EC1N41Ckb1h7d5e80d3c4d0','protocol_sha256':sha(HERE/'protocol.json'),
            'source_sha256':proto['source_sha256'],'panels':out,
            'peak_self_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    with (HERE/'result.json').open('x') as output:json.dump(result,output,sort_keys=True,indent=2);output.write('\n')
    print(json.dumps({'status':result['status'],'panels':[(x['name'],len(x['matches']),x['panel_ns']) for x in out]}))
if __name__=='__main__':main()
