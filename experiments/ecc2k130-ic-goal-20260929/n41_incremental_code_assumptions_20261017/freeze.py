"""Freeze the incremental binary, exact public formula, and code order."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
CUBES=D.parent/'n41_public_code_cube_20261017'
OLD=D.parent/'n41_sixpair_shared_target_20261017'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


old=json.loads((CUBES/'protocol.json').read_text())
wires=json.loads((CUBES/'wires.json').read_text())
assert wires['allowed_codes']==old['allowed_codes'] and len(old['allowed_codes'])==40
assert sha(OLD/'public.xcnf')==old['archived_formula_sha256']
text='W 7 '+' '.join(map(str,wires['code_wires']))+'\n'
text+=''.join(f'C {code}\n' for code in old['allowed_codes'])
(D/'codes.tsv').write_text(text)
lib=Path('/opt/homebrew/lib/libcryptominisat5.dylib')
record={'schema':1,'candidate_id':None,
        'curve_id':old['curve_id'],'public_raw_point':old['public_raw_point'],
        'source_sha256':sha(D/'incremental.cpp'),
        'binary_sha256':sha(D/'incremental'),
        'lib_sha256':sha(lib),'lib_path':str(lib),
        'header_sha256':sha(Path('/opt/homebrew/include/cryptominisat5/cryptominisat_c.h')),
        'formula_sha256':sha(OLD/'public.xcnf'),'formula_path':str(OLD/'public.xcnf'),
        'codes_sha256':sha(D/'codes.tsv'),
        'prior_cube_protocol_sha256':sha(CUBES/'protocol.json'),
        'prior_cube_result_sha256':sha(CUBES/'campaign_result.json'),
        'allowed_codes':old['allowed_codes'],
        'per_call_cpu_cap_s':10,'parent_cap_s':550,
        'rss_cap_bytes':4*1024**3,'worker_count':1,
        'compile_command':['/usr/bin/clang++','-O2','-std=c++17',
                           '-I/opt/homebrew/include','incremental.cpp',
                           '-L/opt/homebrew/lib','-lcryptominisat5',
                           '-Wl,-rpath,/opt/homebrew/lib','-o','incremental'],
        'producer_sha256':sha(Path(__file__))}
(D/'protocol.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'FROZEN','protocol_sha256':sha(D/'protocol.json')}))
