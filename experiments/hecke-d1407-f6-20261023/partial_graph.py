"""Exact component ranks for the D1407 floor after the missing fiber cut."""
from collections import defaultdict, deque
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json

P=Path(__file__).resolve().parent

def rank(vectors):
    pivots={}
    for source in vectors:
        row={int(k):Fraction(v) for k,v in source.items() if v}
        while row:
            col=min(row)
            if col not in pivots:
                inv=1/row[col];pivots[col]={k:v*inv for k,v in row.items()}
                break
            a=row[col]
            for k,v in pivots[col].items():
                new=row.get(k,0)-a*v
                if new:row[k]=new
                else:row.pop(k,None)
    return len(pivots)

def main():
    source=P/'floor_exception.json';d=json.loads(source.read_text())
    cycles=[{int(k):int(v) for k,v in c['signed_floor_columns'].items()} for c in d['cycles']]
    pairs=[{int(k):int(v) for k,v in p['signed_columns'].items()} for p in d['pairs']]
    adj=defaultdict(set);edges=[]
    for i,c in enumerate(cycles):
        for j,p in enumerate(pairs):
            shared=set(c)&set(p)
            if not shared:continue
            adj[('c',i)].add(('p',j));adj[('p',j)].add(('c',i))
            edges.append({'cycle':i,'pair':j,'overlap_size':len(shared),
                          'ratios':sorted({c[k]*p[k] for k in shared})})
    assert set(adj)=={('c',i) for i in range(len(cycles))}|{('p',j) for j in range(len(pairs))}
    seen=set();components=[]
    for root in sorted(adj):
        if root in seen:continue
        queue=deque([root]);seen.add(root);nodes=[]
        while queue:
            node=queue.popleft();nodes.append(node)
            for nxt in adj[node]:
                if nxt not in seen:seen.add(nxt);queue.append(nxt)
        ci=sorted(i for kind,i in nodes if kind=='c')
        pi=sorted(i for kind,i in nodes if kind=='p')
        local=rank([cycles[i] for i in ci]+[pairs[i] for i in pi])
        components.append({'cycles':ci,'pairs':pi,'rank':local,
                           'intersection_dimension':len(ci)+len(pi)-local,
                           'covered_columns':len(set().union(*(set(cycles[i]) for i in ci),*(set(pairs[i]) for i in pi)))})
    assert sorted((len(c['cycles']),len(c['pairs']),c['intersection_dimension']) for c in components)==[(5,11,0),(6,12,1)]
    assert sum(c['rank'] for c in components)==d['cycle_pair_span_rank']==33
    result={'status':'EXACT_D1407_ONE_SURVIVING_CROSS_DEGREE_IDENTITY',
            'floor_sha256':sha256(source.read_bytes()).hexdigest(),
            'script_sha256':sha256((P/'partial_graph.py').read_bytes()).hexdigest(),
            'edge_count':len(edges),'edges':edges,'components':components,
            'rank':33,'candidate_id':None,'timing_claim':None}
    (P/'partial_graph.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'components':components,'rank':33}))

if __name__=='__main__':main()
