import hashlib
import json
from pathlib import Path
D=Path(__file__).resolve().parent
R=D.parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((D/'protocol.json').read_text());r=json.loads((D/'result.json').read_text());a=json.loads((D/'audit_result.json').read_text())
assert r['protocol_sha256']==sha(D/'protocol.json')
assert p['input_sha256']==sha(R/'n41_sixpair_shared_target_20261017'/'join_input.tsv')
sources={'direct':R/'n41_sixpair_shared_target_20261017'/'join_exact.cpp',
         'vector':R/'n41_frobenius_folded_join_20261016'/'folded.cpp','pointer':D/'pointer.cpp'}
assert p['one_source_sha256']==sha(D/'one.py')
for arm,source in sources.items():
    assert p['source_sha256'][arm]==sha(source)
    assert p['binary_sha256'][arm]==sha(D/arm)
assert [v['arm'] for v in r['runs']]==p['order']
assert len(r['runs'])==6 and a['matched_runs']==6 and a['status']=='PASS'
for i,v in enumerate(r['runs']):
    assert v['exit_code']==0 and v['peak_child_rss_bytes']<p['rss_boundary_bytes']
    stem=D/f"run_{i}_{v['arm']}"
    assert v['stdout_sha256']==sha(Path(str(stem)+'.stdout'))
    assert v['stderr_sha256']==sha(Path(str(stem)+'.stderr'))
    lines=Path(str(stem)+'.stdout').read_text().splitlines()
    assert lines[1].split()[1]=='3750144'
    assert lines[2]==v['hit']
    assert tuple(map(int,lines[2].split()[1:9]))==(12,122,116,47,128,34,1100323,3)
assert a['target']==p['target'] and a['distinct_columns']==12
out={'status':'PASS','protocol_sha256':sha(D/'protocol.json'),'result_sha256':sha(D/'result.json'),
     'audit_sha256':sha(D/'audit_result.json'),'matched_runs':6,'hit_ids':[12,122,116,47,128,34]}
(D/'terminal.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out))
