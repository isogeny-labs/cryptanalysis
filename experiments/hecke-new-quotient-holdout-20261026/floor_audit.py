"""Exact signed-cycle and degree-3 pair certificates for the frozen matrix."""
import hashlib
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

from sage.all import QQ, matrix

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def components(rows, nonfloor):
    owners = defaultdict(list)
    parent = {i:i for i in rows}
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i,row in rows.items():
        for col in row:
            if col in nonfloor:
                owners[col].append(i)
    for incident in owners.values():
        for i in incident[1:]:
            parent[root(i)] = root(incident[0])
    grouped = defaultdict(list)
    for i in rows:
        grouped[root(i)].append(i)
    return list(grouped.values()),owners


def signed_component(indices, rows, owners, floor):
    lower = {c for i in indices for c in rows[i] if c not in floor}
    if len(lower) != len(indices) or any(sum(c in floor for c in rows[i]) != 1 for i in indices):
        return None,'floor/lower incidence mismatch'
    adjacency = defaultdict(list)
    for col in lower:
        incident = [(i,rows[i][col]) for i in owners[col]]
        if sorted(value for _,value in incident) != [1,1,2]:
            return None,'lower incidence is not [1,1,2]'
        heavy = next(i for i,value in incident if value == 2)
        for light,value in incident:
            if value == 1:
                adjacency[heavy].append(light)
                adjacency[light].append(heavy)
    signs = {indices[0]:1}
    queue = deque([indices[0]])
    while queue:
        i = queue.popleft()
        for other in adjacency[i]:
            needed = -signs[i]
            if other in signs:
                if signs[other] != needed:
                    return None,'inconsistent alternating cycle'
            else:
                signs[other] = needed
                queue.append(other)
    if len(signs) != len(indices):
        return None,'signed incidence disconnected'
    result = Counter()
    for i,sign in signs.items():
        for col,value in rows[i].items():
            result[col] += sign*value
    result = {col:value for col,value in result.items() if value}
    if set(result)-floor or set(result.values())-{-1,1} or len(result)!=len(indices):
        return None,'integer cancellation failed'
    return {'signed_rows':{str(i):sign for i,sign in sorted(signs.items())},
            'signed_floor_columns':{str(col):value for col,value in sorted(result.items())}},None


def main():
    source_path = HERE/'data'/'exp11_class_walk_D2631_f6.json'
    audit_path = HERE/'audit.json'
    data = json.loads(source_path.read_text())
    audit = json.loads(audit_path.read_text())
    assert audit['source_sha256']==digest(source_path) and audit['status']=='VERIFIED_FORECAST_MATCH'
    rows = [{int(k):int(v) for k,v in row.items() if v} for row in data['relation_rows']]
    metadata = audit['row_records']
    floor = {record['column'] for record in audit['point_records'] if record['endomorphism_conductor']==6}
    nonfloor = set(range(len(audit['point_records'])))-floor
    c3_degree2 = {i:row for i,row in enumerate(rows)
                  if metadata[i]['degree']==2 and metadata[i]['source_conductor']==3}
    groups,owners = components(c3_degree2,nonfloor)
    cycles,rejected = [],[]
    for group in groups:
        certificate,reason = signed_component(group,c3_degree2,owners,floor)
        if certificate:
            cycles.append(certificate)
        else:
            rejected.append({'rows':group,'reason':reason})
    cycle_vectors = [{int(k):int(v) for k,v in c['signed_floor_columns'].items()} for c in cycles]
    c2_degree3 = {i:row for i,row in enumerate(rows)
                  if metadata[i]['degree']==3 and metadata[i]['source_conductor']==2}
    by_lower = defaultdict(list)
    for i,row in c2_degree3.items():
        signature = tuple(sorted((col,value) for col,value in row.items() if col in nonfloor))
        by_lower[signature].append(i)
    pairs,rejected_pairs = [],[]
    for indices in sorted(by_lower.values()):
        if len(indices)!=2:
            rejected_pairs.append({'rows':indices,'reason':'not a pair'})
            continue
        a,b = indices
        diff = {col:rows[a].get(col,0)-rows[b].get(col,0) for col in rows[a].keys()|rows[b].keys()}
        diff = {col:value for col,value in diff.items() if value}
        if set(diff)-floor:
            rejected_pairs.append({'rows':indices,'reason':'nonfloor remainder'})
            continue
        pairs.append({'rows':indices,'signed_floor_columns':{str(k):v for k,v in sorted(diff.items())}})
    pair_vectors = [{int(k):int(v) for k,v in p['signed_floor_columns'].items()} for p in pairs]
    cycle_use = Counter(col for vector in cycle_vectors for col in vector)
    pair_use = Counter(col for vector in pair_vectors for col in vector)
    edges = []
    for ci,cycle in enumerate(cycle_vectors):
        for pi,pair in enumerate(pair_vectors):
            common = sorted(set(cycle)&set(pair))
            if common:
                ratios = sorted({cycle[col]*pair[col] for col in common})
                edges.append({'cycle':ci,'pair':pi,'overlap':len(common),'ratios':ratios,
                              'locally_uniform':len(ratios)==1})
    incidence = defaultdict(set)
    for edge in edges:
        a,b = ('c',edge['cycle']),('p',edge['pair'])
        incidence[a].add(b)
        incidence[b].add(a)
    seen,graph_components = set(),[]
    for node in incidence:
        if node in seen: continue
        pending=[node]
        part=set()
        while pending:
            current=pending.pop()
            if current in part: continue
            part.add(current)
            pending.extend(incidence[current]-part)
        seen |= part
        graph_components.append({'cycles':sorted(i for kind,i in part if kind=='c'),
                                 'pairs':sorted(i for kind,i in part if kind=='p'),
                                 'mixed_edges':sum(1 for e in edges if ('c',e['cycle']) in part and not e['locally_uniform'])})
    all_vectors = cycle_vectors+pair_vectors
    span_rank = int(matrix(QQ,[[vector.get(col,0) for col in range(len(audit['point_records']))]
                              for vector in all_vectors]).rank())
    expected_floor_rank = audit['ranks']['QQ']['2+3'][0]-audit['ranks']['QQ']['2+3'][1]
    match = (len(cycles)==6 and not rejected and [len(c['signed_rows']) for c in cycles]==[48]*6
             and len(pairs)==48 and not rejected_pairs
             and cycle_use==Counter({col:1 for col in floor})
             and pair_use==Counter({col:1 for col in floor})
             and len(graph_components)==6 and all(c['mixed_edges']>0 for c in graph_components)
             and span_rank==expected_floor_rank==54)
    result = {'status':'VERIFIED_SIX_MIXED_COMPONENTS' if match else 'FORECAST_MISMATCH',
              'prediction_match':match,'source_sha256':digest(source_path),'audit_sha256':digest(audit_path),
              'floor_columns':len(floor),'degree2_source_rows':len(c3_degree2),
              'degree3_source_rows':len(c2_degree3),'cycle_count':len(cycles),
              'cycle_sizes':[len(c['signed_rows']) for c in cycles],
              'pair_count':len(pairs),'pair_sizes':[len(p['signed_floor_columns']) for p in pairs],
              'graph_components':graph_components,'edges':edges,
              'floor_vector_rank_QQ':span_rank,'whole_matrix_floor_rank_QQ':expected_floor_rank,
              'rejected_cycles':rejected,'rejected_pairs':rejected_pairs,
              'cycles':cycles,'pairs':pairs}
    (HERE/'floor_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('cycles','pairs','edges')},sort_keys=True))


if __name__=='__main__':main()
