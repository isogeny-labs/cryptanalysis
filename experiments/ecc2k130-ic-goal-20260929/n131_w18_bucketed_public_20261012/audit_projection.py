"""Independent exhaustive cross-class count with incident-edge subtraction."""
import hashlib,json,time
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def c2(n):return n*(n-1)//2
def main():
    p=json.loads((HERE/'projection_audit_protocol.json').read_text())
    paths={'source':HERE/'audit_projection.py',
           'support':HERE.parent/'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv',
           'producer':HERE/'projection_result.json'}
    assert {k:sha(v) for k,v in paths.items()}==p['sha256']
    start=time.monotonic_ns()
    rows=[tuple(map(int,s.split())) for s in paths['support'].read_text().splitlines()]
    assert len(rows)==131307 and len({m for m,_ in rows})==len(rows)
    k=Counter(col for _,col in rows)
    A=[col for mask,col in rows if mask%64==9]
    B=[col for mask,col in rows if mask%64==14]
    assert len(A)==2042 and len(B)==2038
    N=len(rows);valid_pairs=c2(N)-sum(c2(v) for v in k.values())
    first_edges=0;left_entries=0
    for ci in A:
        ki=k[ci]
        for cj in B:
            if ci==cj:continue
            kj=k[cj]
            slot1=valid_pairs-ki*(N-ki)-kj*(N-kj)+ki*kj
            assert slot1>=0
            first_edges+=1
            left_entries+=16*slot1
    result=json.loads(paths['producer'].read_text())
    assert result['first_unordered_admissible_edges']==first_edges
    assert result['literal_left_entries']==left_entries
    assert result['one_bit_per_entry_bytes']==(left_entries+7)//8
    out={'status':'PASS_INDEPENDENT_N131_BUCKET_LITERAL_MEMORY_AUDIT',
         'first_unordered_admissible_edges':first_edges,
         'literal_left_entries':left_entries,
         'one_bit_per_entry_bytes':(left_entries+7)//8,
         'wall_ns':time.monotonic_ns()-start,'sha256':{k:sha(v) for k,v in paths.items()},
         'protocol_sha256':sha(HERE/'projection_audit_protocol.json')}
    (HERE/'projection_audit_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(out['status'],first_edges,left_entries,flush=True)
if __name__=='__main__':main()
