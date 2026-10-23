"""Reconstruct the conductor-2 degree-3 Hecke incidence in frozen f=6 walks."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

from sage.all import EllipticCurve_from_j, QQ, matrix

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
INPUTS=json.loads((HERE/'inputs.json').read_text())
sys.path.insert(0,str(ROOT/'experiments/hecke-floor-overlap-holdout-20261023/tools'))
import hecke11 as H


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode(E,text):
    match=re.fullmatch(r'\((\d+) : (\d+) : 1\)',text)
    if not match:raise ValueError(f'unexpected point encoding: {text}')
    return E([int(match.group(1)),int(match.group(2)),1])


def model(n):
    M=matrix(QQ,n,n,0)
    for i in range(n):
        M[i,i]+=1
        M[i,(i-1)%n]+=1
        M[i,(i+1)%n]+=1
    return M


def cycles_from_adjacency(adj):
    unseen=set(adj)
    cycles=[]
    while unseen:
        first=min(unseen)
        cycle=[]
        previous=None
        current=first
        while current not in cycle:
            if current not in unseen:raise ValueError('cycle merges into prior component')
            unseen.remove(current)
            cycle.append(current)
            options=sorted(adj[current]-({previous} if previous is not None else set()))
            if len(options)!=1 and previous is not None:
                raise ValueError('non-two-regular graph')
            if not options:raise ValueError('cycle path stopped')
            previous,current=current,options[0]
        if current!=first:raise ValueError('cycle closes at wrong vertex')
        cycles.append(cycle)
    return cycles


def audit_one(item,funcs,jfun):
    path=ROOT/item['path']
    assert sha(path)==item['sha256']
    data=json.loads(path.read_text())
    assert (data['DK'],data['f'],data['p'],data['u'],data['class_size'],data['relations'])==(
        item['DK'],6,item['p'],item['u'],item['class_size'],item['relations'])
    out={'path':item['path'],'sha256':item['sha256'],'DK':data['DK'],
         'p':data['p'],'class_size':data['class_size'],'saved_rows':data['relations']}
    if data['class_size']==0:
        out.update(status='EMPTY_CLASS',conductor2_points=0,cycle_lengths=[])
        return out
    rd=H.Reduced(data['p'],funcs,jfun,[2,3])
    points=[decode(rd.E,text) for text in data['column_points']]
    if len(set(points))!=len(points) or len(points)!=data['class_size']:
        out.update(status='INVALID_POINT_LIST')
        return out
    index={point:i for i,point in enumerate(points)}
    conductor_by_j={}
    conductors=[]
    for point in points:
        j=rd.j(point)
        if j is None:raise ValueError('j-map undefined on saved class point')
        key=int(j)
        if key not in conductor_by_j:
            E=EllipticCurve_from_j(j)
            assert abs(int(E.trace_of_frobenius()))==data['u']
            conductor_by_j[key]=int(E.endomorphism_order().conductor())
        conductors.append(conductor_by_j[key])
    c2={i for i,c in enumerate(conductors) if c==2}
    floor={i for i,c in enumerate(conductors) if c==6}
    out.update(conductor_counts=dict(sorted(Counter(conductors).items())),
               conductor2_points=len(c2),floor_points=len(floor))
    saved=Counter(tuple(sorted((int(k),int(v)) for k,v in row.items() if v))
                  for row in data['relation_rows'])
    missing=[]
    shape_errors=[]
    adj={}
    projected_rows={}
    for src in sorted(c2):
        point=points[src]
        neighbors=rd.neighbours_all(3,point)
        if neighbors is None or len(neighbors)!=4:
            shape_errors.append({'source':src,'reason':'not_four_rational_neighbors'})
            continue
        if sum(neighbors,rd.E(0))!=rd.a_l[3]*point:
            shape_errors.append({'source':src,'reason':'group_sum_mismatch'})
            continue
        if any(q not in index for q in neighbors):
            shape_errors.append({'source':src,'reason':'neighbor_outside_saved_class'})
            continue
        row=Counter(index[q] for q in neighbors)
        row[src]-=rd.a_l[3]
        row={k:v for k,v in row.items() if v}
        key=tuple(sorted(row.items()))
        if saved[key]:saved[key]-=1
        else:missing.append(src)
        projected={col:value for col,value in row.items() if col not in floor}
        horizontal={col for col in projected if col!=src}
        if (len(projected)!=3 or projected.get(src)!=1 or
            set(projected.values())!={1} or
            len(horizontal)!=2 or not horizontal<=c2 or
            len(row)!=5 or sum(col in floor for col in row)!=2):
            shape_errors.append({'source':src,'reason':'projected_row_not_cycle_form',
                                 'projected':projected})
            continue
        adj[src]=horizontal
        projected_rows[src]=projected
    out.update(reconstructed_sources=len(projected_rows),
               saved_row_missing_sources=missing,
               shape_errors=shape_errors)
    if len(adj)!=len(c2):
        out.update(status='PARTIAL_CYCLE_STRUCTURE',cycle_lengths=[])
        return out
    reciprocal=all(len(ns)==2 and all(src in adj.get(neighbor,set()) for neighbor in ns)
                   for src,ns in adj.items())
    out['reciprocal_horizontal_edges']=reciprocal
    if not reciprocal:
        out.update(status='NONRECIPROCAL_HORIZONTAL_GRAPH',cycle_lengths=[])
        return out
    cycles=cycles_from_adjacency(adj)
    cycle_records=[]
    for cycle in cycles:
        n=len(cycle)
        actual=matrix(QQ,[[projected_rows[src].get(col,0) for col in cycle]
                          for src in cycle])
        if actual!=model(n):raise ValueError('ordered cycle matrix differs from I+S+S^-1')
        rank=int(actual.rank())
        expected=n-(2 if n%3==0 else 0)
        if rank!=expected:raise ValueError('cycle exact rank contradicts theorem')
        cycle_records.append({'length':n,'rank_QQ':rank,
                              'kernel_dimension_QQ':n-rank})
    out.update(cycle_lengths=sorted(len(c) for c in cycles),cycles=cycle_records,
               total_cycle_kernel_QQ=sum(c['kernel_dimension_QQ'] for c in cycle_records),
               status='PASS_SAVED_CYCLE_BRIDGE' if not missing and not shape_errors else
                      'PASS_GEOMETRY_WITH_SAVED_ROW_GAPS')
    return out


def main():
    assert INPUTS['status']=='FROZEN_RETROSPECTIVE_ALL_SAVED_F6_WALKS'
    assert INPUTS['hecke_source_sha256']==sha(ROOT/INPUTS['hecke_source'])
    funcs,jfun=H.build([2,3])
    results=[]
    for item in INPUTS['inputs']:
        try:result=audit_one(item,funcs,jfun)
        except Exception as ex:
            result={'path':item['path'],'sha256':item['sha256'],
                    'status':'AUDIT_ERROR','error_type':type(ex).__name__,
                    'error':str(ex)}
        results.append(result)
        print(json.dumps({k:v for k,v in result.items() if k in
                          ('path','status','class_size','conductor2_points',
                           'cycle_lengths','saved_row_missing_sources','error')},sort_keys=True),flush=True)
    output={'status':'CENSUS_COMPLETE_WITH_ALL_INPUTS_RETAINED',
            'inputs_sha256':sha(HERE/'inputs.json'),
            'script_sha256':sha(HERE/'audit.py'),
            'cases':results,'counts':dict(sorted(Counter(r['status'] for r in results).items())),
            'candidate_id':None,'timing_claim':None}
    (HERE/'audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':output['status'],'counts':output['counts']},sort_keys=True))


if __name__=='__main__':main()
