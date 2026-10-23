"""Exact signed floor geometry after the D1407 exceptional-fiber break."""
from collections import Counter, defaultdict
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import sys

P=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'tools'))
from degree2_graph_audit import components, signed_component

def rank(vectors):
    pivots={}
    for source in vectors:
        row={int(k):Fraction(v) for k,v in source.items() if v}
        while row:
            col=min(row)
            if col not in pivots:
                scale=1/row[col]
                pivots[col]={k:v*scale for k,v in row.items()}
                break
            scale=row[col]
            for k,v in pivots[col].items():
                new=row.get(k,0)-scale*v
                if new:row[k]=new
                else:row.pop(k,None)
    return len(pivots)

def main():
    source=P/'data/exp11_class_walk_D1407_f6.json'
    audit_path=P/'audit_exception.json'
    data=json.loads(source.read_text());audit=json.loads(audit_path.read_text())
    rows=[{int(k):int(v) for k,v in r.items() if v} for r in data['relation_rows']]
    metadata=audit['row_records']
    floor=set(audit['floor_column_indices'])
    nonfloor=set(range(data['class_size']))-floor
    degree2={i:row for i,row in enumerate(rows) if metadata[i]['degree']==2}
    c3_degree2={i:row for i,row in degree2.items() if metadata[i]['source_conductor']==3}
    groups,owners=components(c3_degree2,nonfloor)
    cycles=[];rejected=[]
    for group in groups:
        cert,reason=signed_component(group,c3_degree2,owners,floor)
        if cert is None:rejected.append({'rows':sorted(group),'reason':reason})
        else:cycles.append(cert)
    c2_degree3={i:row for i,row in enumerate(rows)
                if metadata[i]['degree']==3 and metadata[i]['source_conductor']==2}
    by_lower=defaultdict(list)
    for i,row in c2_degree3.items():
        by_lower[tuple(sorted((k,v) for k,v in row.items() if k in nonfloor))].append(i)
    pairs=[];singletons=[]
    for indices in sorted(by_lower.values()):
        if len(indices)!=2:
            singletons.append(indices)
            continue
        a,b=indices
        diff={k:rows[a].get(k,0)-rows[b].get(k,0) for k in rows[a].keys()|rows[b].keys()}
        diff={k:v for k,v in diff.items() if v}
        assert set(diff)<=floor and len(diff)==6 and set(diff.values())<={-1,1}
        pairs.append({'rows':indices,'signed_columns':{str(k):v for k,v in sorted(diff.items())}})
    cycle_vecs=[{int(k):int(v) for k,v in c['signed_floor_columns'].items()} for c in cycles]
    pair_vecs=[{int(k):int(v) for k,v in p['signed_columns'].items()} for p in pairs]
    cycle_use=Counter(k for row in cycle_vecs for k in row)
    pair_use=Counter(k for row in pair_vecs for k in row)
    rank_floor=rank(cycle_vecs+pair_vecs)
    result={'status':'EXACT_D1407_PARTIAL_FLOOR_GEOMETRY',
            'source_sha256':sha256(source.read_bytes()).hexdigest(),
            'audit_sha256':sha256(audit_path.read_bytes()).hexdigest(),
            'script_sha256':sha256((P/'floor_exception.py').read_bytes()).hexdigest(),
            'degree2_component_count':len(groups),'signed_cycle_count':len(cycles),
            'signed_cycle_sizes':sorted(len(c['signed_rows']) for c in cycles),
            'rejected_degree2_components':rejected,
            'pair_count':len(pairs),'unpaired_degree3_groups':singletons,
            'cycle_covered_floor_columns':len(cycle_use),
            'pair_covered_floor_columns':len(pair_use),
            'floor_columns':len(floor),'cycle_pair_span_rank':rank_floor,
            'full_minus_projected_rank':audit['ranks']['QQ']['2+3'][0]-audit['ranks']['QQ']['2+3'][1],
            'cycles':cycles,'pairs':pairs,
            'candidate_id':None,'timing_claim':None}
    (P/'floor_exception.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','degree2_component_count','signed_cycle_count',
            'signed_cycle_sizes','pair_count','unpaired_degree3_groups',
            'cycle_covered_floor_columns','pair_covered_floor_columns',
            'floor_columns','cycle_pair_span_rank','full_minus_projected_rank']}))

if __name__=='__main__':main()
