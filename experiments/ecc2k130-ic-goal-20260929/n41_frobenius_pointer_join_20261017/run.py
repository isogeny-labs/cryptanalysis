import hashlib
import json
from pathlib import Path
import subprocess

D=Path(__file__).resolve().parent
R=D.parent
SRC={'direct':R/'n41_sixpair_shared_target_20261017'/'join_exact.cpp',
     'vector':R/'n41_frobenius_folded_join_20261016'/'folded.cpp',
     'pointer':D/'pointer.cpp'}
INPUT=R/'n41_sixpair_shared_target_20261017'/'join_input.tsv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
for arm,source in SRC.items():
    subprocess.run(['clang++','-O3','-std=c++17','-o',str(D/arm),str(source)],check=True)
order=['direct','pointer','vector','vector','pointer','direct']
protocol={'order':order,'input_sha256':sha(INPUT),'source_sha256':{a:sha(s) for a,s in SRC.items()},
          'binary_sha256':{a:sha(D/a) for a in SRC},'one_source_sha256':sha(D/'one.py'),
          'compiler':subprocess.check_output(['clang++','--version'],text=True).splitlines()[0],
          'compile_flags':['-O3','-std=c++17'],'per_run_cap_s':180,'rss_boundary_bytes':4294967296,
          'one_worker':True,'target':[2026560328086,1928332930914]}
write(D/'protocol.json',protocol)
records=[]
for i,arm in enumerate(order):
    stem=D/f'run_{i}_{arm}'
    p=subprocess.run(['python3',str(D/'one.py'),str(D/arm),str(INPUT),str(stem)],capture_output=True,text=True,timeout=190)
    assert p.returncode==0,p.stderr
    r=json.loads(p.stdout);lines=r.pop('lines')
    assert r['exit_code']==0 and len(lines)==3 and lines[0].startswith('CHECK_PASS ') and lines[1].startswith('LEFT_DONE ') and lines[2].startswith('HIT '),lines
    rec={'arm':arm,'order':i,'hit':lines[2],**r,'stdout_sha256':sha(Path(str(stem)+'.stdout')),
         'stderr_sha256':sha(Path(str(stem)+'.stderr'))}
    records.append(rec)
    write(D/'result.json',{'protocol_sha256':sha(D/'protocol.json'),'runs':records})
    print(json.dumps(rec),flush=True)
assert len({tuple(r['hit'].split()[1:9]) for r in records})==1
assert all(r['peak_child_rss_bytes']<4294967296 for r in records)
print('PASS matched exact hit, counts and resource boundary',flush=True)
