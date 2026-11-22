import hashlib
import json
import pathlib
import re
import subprocess
import time

D = pathlib.Path(__file__).resolve().parent
BASE = D.parent / 'n41_sixpair_shared_target_20261017'
INPUT = BASE / 'join_input.tsv'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')

for arm, source in [('baseline', BASE / 'join_exact.cpp'), ('folded', D / 'folded.cpp')]:
    subprocess.run(['clang++', '-O3', '-std=c++17', '-o', str(D / arm), str(source)], check=True)
protocol = {
    'input': str(INPUT), 'input_sha256': sha(INPUT),
    'source_sha256': {arm: sha(source) for arm, source in [('baseline', BASE/'join_exact.cpp'), ('folded', D/'folded.cpp')]},
    'binary_sha256': {arm: sha(D/arm) for arm in ('baseline', 'folded')},
    'compiler': subprocess.check_output(['clang++','--version'], text=True).splitlines()[0],
    'compile_args': ['-O3','-std=c++17'], 'order': ['baseline','folded','folded','baseline'],
    'cap_s_per_run': 180, 'rss_cap_bytes': 4294967296,
    'target': [2026560328086,1928332930914],
}
write(D/'protocol.json', protocol)
records=[]
for i,arm in enumerate(protocol['order']):
    start=time.monotonic()
    p=subprocess.run(['/usr/bin/time','-l',str(D/arm),str(INPUT)],capture_output=True,text=True,timeout=180)
    wall=time.monotonic()-start
    (D/f'run_{i}_{arm}.stdout').write_text(p.stdout)
    (D/f'run_{i}_{arm}.stderr').write_text(p.stderr)
    hit=re.search(r'^HIT (.+)$',p.stdout,re.M)
    rss=re.search(r'(\d+)\s+maximum resident set size',p.stderr)
    rec={'arm':arm,'exit_code':p.returncode,'parent_wall_s':wall,'worker_hit_line':hit.group(0) if hit else None,
         'peak_rss_bytes':int(rss.group(1)) if rss else None,'stdout_sha256':sha(D/f'run_{i}_{arm}.stdout'),
         'stderr_sha256':sha(D/f'run_{i}_{arm}.stderr')}
    records.append(rec)
    write(D/'result.json', {'protocol_sha256':sha(D/'protocol.json'),'runs':records})
    print(json.dumps(rec),flush=True)
assert all(r['exit_code']==0 and r['worker_hit_line'] for r in records)
assert len({tuple(r['worker_hit_line'].split()[1:7]) for r in records})==1
assert len({tuple(r['worker_hit_line'].split()[7:9]) for r in records})==1
print('PASS exact witness and probe counts',flush=True)
