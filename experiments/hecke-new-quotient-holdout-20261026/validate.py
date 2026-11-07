"""Independent integer replay of the signed floor certificates and ranks."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sparse_rank(rows, modulus=None):
    pivots = {}
    for source in rows:
        current = {int(k):(Fraction(v) if modulus is None else int(v)%modulus)
                   for k,v in source.items() if v}
        while current:
            first = min(current)
            if first not in pivots:
                inverse = 1/current[first] if modulus is None else pow(current[first],-1,modulus)
                pivots[first] = {k:(v*inverse if modulus is None else v*inverse%modulus)
                                 for k,v in current.items()}
                break
            multiplier = current[first]
            for k,v in pivots[first].items():
                value = current.get(k,0)-multiplier*v
                if modulus is not None: value %= modulus
                if value: current[k] = value
                else: current.pop(k,None)
    return len(pivots)


def main():
    source_path = HERE/'data'/'exp11_class_walk_D2631_f6.json'
    audit_path = HERE/'audit.json'
    floor_path = HERE/'floor_audit.json'
    data = json.loads(source_path.read_text())
    audit = json.loads(audit_path.read_text())
    floor = json.loads(floor_path.read_text())
    assert audit['source_sha256']==floor['source_sha256']==digest(source_path)
    assert floor['audit_sha256']==digest(audit_path)
    rows = [{int(k):int(v) for k,v in row.items() if v} for row in data['relation_rows']]
    floor_columns = {item['column'] for item in audit['point_records'] if item['endomorphism_conductor']==6}
    nonfloor = set(range(data['class_size']))-floor_columns
    cycles,pairs = [],[]
    for certificate in floor['cycles']:
        replay = Counter()
        for i,sign in certificate['signed_rows'].items():
            for col,value in rows[int(i)].items():
                replay[col] += int(sign)*value
        replay = {col:value for col,value in replay.items() if value}
        claimed = {int(k):int(v) for k,v in certificate['signed_floor_columns'].items()}
        assert replay==claimed and set(replay)<=floor_columns
        assert len(certificate['signed_rows'])==len(replay)==48
        cycles.append(replay)
    for certificate in floor['pairs']:
        a,b = certificate['rows']
        replay = {col:rows[a].get(col,0)-rows[b].get(col,0)
                  for col in rows[a].keys()|rows[b].keys()}
        replay = {col:value for col,value in replay.items() if value}
        claimed = {int(k):int(v) for k,v in certificate['signed_floor_columns'].items()}
        assert replay==claimed and set(replay)<=floor_columns
        assert len(replay)==6 and set(replay.values())<= {-1,1}
        pairs.append(replay)
    assert len(cycles)==6 and len(pairs)==48
    assert Counter(col for vector in cycles for col in vector)==Counter({col:1 for col in floor_columns})
    assert Counter(col for vector in pairs for col in vector)==Counter({col:1 for col in floor_columns})
    touches = []
    for pair in pairs:
        touched=[]
        for i,cycle in enumerate(cycles):
            common=set(pair)&set(cycle)
            if common:
                touched.append(i)
                assert {pair[col]*cycle[col] for col in common}=={-1,1}
        assert len(touched)==1
        touches.append(touched[0])
    assert Counter(touches)==Counter({i:8 for i in range(6)})
    ranks={}
    for name,modulus in [('QQ',None),('23',23),('1000000007',1000000007)]:
        witness = sparse_rank(cycles+pairs,modulus)
        full = sparse_rank(rows,modulus)
        projected = sparse_rank([{col:v for col,v in row.items() if col in nonfloor}
                                 for row in rows],modulus)
        assert (witness,full,projected)==(54,480,426)
        ranks[name]={'witness':witness,'full':full,'nonfloor':projected}
    result={'status':'VERIFIED_EXACT_FLOOR_BASIS','source_sha256':digest(source_path),
            'audit_sha256':digest(audit_path),'floor_audit_sha256':digest(floor_path),
            'cycles':len(cycles),'pairs':len(pairs),'pair_touches_per_cycle':dict(sorted(Counter(touches).items())),
            'ranks':ranks}
    (HERE/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
