"""Exact Sage replay of the frozen D1295 two-sheet norm-three test."""
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys

from sage.all import EllipticCurve_from_j,PolynomialRing,QQ,classical_modular_polynomial,matrix

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'tools'))
import hecke11 as H


def read(name):
    return json.loads((HERE/name).read_text())


def sha(name):
    return hashlib.sha256((HERE/name).read_bytes()).hexdigest()


def decode(E,text):
    match=re.fullmatch(r'\((\d+) : (\d+) : 1\)',text)
    assert match,text
    return E([int(match.group(1)),int(match.group(2)),1])


def rank(rows,columns,keep=None):
    return int(matrix(QQ,[[int(row.get(str(j),0)) if keep is None or j in keep else 0
                           for j in range(columns)] for row in rows]).rank())


def cycles(adj):
    unseen=set(adj)
    output=[]
    while unseen:
        first=min(unseen)
        order=[]
        previous=None
        current=first
        while current not in order:
            assert current in unseen
            unseen.remove(current)
            order.append(current)
            options=sorted(adj[current]-({previous} if previous is not None else set()))
            assert options
            previous,current=current,options[0]
        assert current==first
        output.append(order)
    return output


def main():
    protocol=read('producer_protocol.json')
    selection=read('selection.json')
    gate=read('fiber_gate_result.json')
    assert protocol['status']=='FROZEN_BEFORE_GATE_AND_PRODUCER'
    assert protocol['selection_sha256']==sha('selection.json')
    assert selection['protocol_sha256']==sha('selection_protocol.json')
    for name,digest in protocol['source_sha256'].items():assert sha(name)==digest
    assert gate['status']=='PASS_UNIFORM_TWO_SHEET_GATE'
    data=read('data/exp11_class_walk_D1295_f6.json')
    assert (data['DK'],data['f'],data['p'],data['u'],data['hecke_primes'])==(-1295,6,11719,16,[2,3])
    funcs,jfun=H.build([2,3])
    rd=H.Reduced(11719,funcs,jfun,[2,3])
    assert rd.a_l[3]==-1
    points=[decode(rd.E,text) for text in data['column_points']]
    index={q:i for i,q in enumerate(points)}
    assert len(points)==len(index)==protocol['predictions']['class_points']==432
    phi={l:classical_modular_polynomial(l) for l in (2,3)}
    ring=PolynomialRing(rd.Fp,'J')
    J=ring.gen()
    conductor_by_j={}
    records=[]
    strata=Counter()
    root_counts={2:Counter(),3:Counter()}
    row_records=[]
    row_index=0
    for i,q in enumerate(points):
        j=rd.j(q)
        assert j is not None
        key=int(j)
        if key not in conductor_by_j:
            model=EllipticCurve_from_j(j)
            assert abs(int(model.trace_of_frobenius()))==16
            conductor_by_j[key]=int(model.endomorphism_order().conductor())
        c=conductor_by_j[key]
        assert 6%c==0
        strata[c]+=1
        records.append({'column':i,'j':key,'conductor':c})
        for l in (2,3):
            expected=l+1 if (6//c)%l==0 else 1
            got_x=sum(int(m) for _,m in rd.neighbour_x(l,q).roots())
            got_j=sum(int(m) for _,m in ring(phi[l](j,J)).roots())
            assert got_x==got_j==expected,(i,l,c,got_x,got_j)
            root_counts[l][expected]+=1
            if expected!=l+1:continue
            neighbors=rd.neighbours_all(l,q)
            assert neighbors is not None and len(neighbors)==l+1
            assert sum(neighbors,rd.E(0))==rd.a_l[l]*q
            assert all(other in index for other in neighbors)
            row=Counter(index[other] for other in neighbors)
            row[i]-=rd.a_l[l]
            generated={str(col):int(value) for col,value in row.items() if value}
            saved={col:int(value) for col,value in data['relation_rows'][row_index].items() if value}
            assert generated==saved,(i,l,row_index)
            row_records.append({'row':row_index,'source':i,'conductor':c,'degree':l})
            row_index+=1
    assert row_index==data['relations']==360
    assert dict(strata)=={1:72,2:72,3:144,6:144}
    assert Counter(r['degree'] for r in row_records)=={2:216,3:144}
    c2={r['column'] for r in records if r['conductor']==2}
    floor={r['column'] for r in records if r['conductor']==6}
    assert len(c2)==72 and len(floor)==144
    j_by_col={r['column']:r['j'] for r in records}
    fiber=Counter(j_by_col[col] for col in c2)
    assert len(fiber)==36 and set(fiber.values())=={2}
    adj={}
    source_row={}
    for meta in row_records:
        if meta['degree']!=3 or meta['conductor']!=2:continue
        src=meta['source']
        row=data['relation_rows'][meta['row']]
        projected={int(col):int(value) for col,value in row.items()
                   if int(col) not in floor and value}
        assert len(projected)==3 and projected.get(src)==1
        assert set(projected.values())=={1} and set(projected)<=c2
        adj[src]=set(projected)-{src}
        source_row[src]=meta['row']
    assert set(adj)==c2
    assert all(len(ns)==2 and all(src in adj[other] for other in ns)
               for src,ns in adj.items())
    components=cycles(adj)
    cycle_records=[]
    for component in components:
        n=len(component)
        actual=matrix(QQ,[[int(data['relation_rows'][source_row[src]].get(str(col),0))
                           for col in component] for src in component])
        model=matrix(QQ,n,n,0)
        for i in range(n):
            for j in (i,(i-1)%n,(i+1)%n):model[i,j]+=1
        assert actual==model
        js=Counter(j_by_col[col] for col in component)
        cycle_records.append({'vertices':component,'length':n,
                              'distinct_j':len(js),'j_multiplicities':dict(sorted(js.items())),
                              'projected_rank_QQ':int(actual.rank()),
                              'projected_kernel_QQ':n-int(actual.rank())})
    lengths=sorted(c['length'] for c in cycle_records)
    predicted=protocol['predictions']
    separate=lengths==[predicted['separate_sheet_cycle_length']]*predicted['separate_sheet_cycle_count']
    swapped=lengths==[predicted['sheet_swap_cycle_length']]*predicted['sheet_swap_cycle_count']
    verdict='SEPARATE_SHEET_CYCLES' if separate else 'SHEET_SWAP_CYCLES' if swapped else 'NEITHER_FROZEN_PATTERN'
    if separate:
        assert all(c['distinct_j']==c['length'] and set(c['j_multiplicities'].values())=={1}
                   for c in cycle_records)
    if swapped:
        assert all(c['distinct_j']*2==c['length'] and set(c['j_multiplicities'].values())=={2}
                   for c in cycle_records)
    nonfloor={i for i in range(len(points)) if i not in floor}
    d3=[row for row,meta in zip(data['relation_rows'],row_records) if meta['degree']==3]
    ranks={'degree3_full_QQ':rank(d3,len(points)),
           'degree3_nonfloor_QQ':rank(d3,len(points),nonfloor),
           'combined_full_QQ':rank(data['relation_rows'],len(points)),
           'combined_nonfloor_QQ':rank(data['relation_rows'],len(points),nonfloor)}
    result={'status':'VERIFIED_D1295_SHEET_ACTION','verdict':verdict,
            'selection_sha256':sha('selection.json'),
            'protocol_sha256':sha('producer_protocol.json'),
            'data_sha256':sha('data/exp11_class_walk_D1295_f6.json'),
            'script_sha256':sha('audit.py'),
            'class_points':len(points),'rows':row_index,
            'conductor_counts':dict(sorted(strata.items())),
            'root_counts':{str(l):dict(sorted(root_counts[l].items())) for l in (2,3)},
            'c2_j_fibers':dict(sorted(fiber.items())),
            'point_records':records,'row_records':row_records,
            'degree3_source_rows':{str(k):v for k,v in sorted(source_row.items())},
            'cycle_lengths':lengths,'cycles':cycle_records,
            'ranks':ranks,'candidate_id':None,'timing_claim':None}
    (HERE/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in
                      ('point_records','row_records','degree3_source_rows','cycles','c2_j_fibers')},sort_keys=True))


if __name__=='__main__':main()
