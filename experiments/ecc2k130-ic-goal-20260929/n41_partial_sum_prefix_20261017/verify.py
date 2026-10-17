"""Bind the finite negative family, native census, and checked-Sage replay."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'n41_sixpair_shared_target_20261017/join_input.tsv'
ARCHIVE=HERE.parent/'n41_sixpair_shared_target_20261017/join_exact.cpp'
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
half=json.loads((HERE/'half_protocol.json').read_text())
audit_protocol=json.loads((HERE/'audit_protocol.json').read_text())
native=json.loads((HERE/'half_result.json').read_text())
audit=json.loads((HERE/'audit_result.json').read_text())
assert half['source_sha256']==sha(SOURCE)
assert half['archived_join_sha256']==sha(ARCHIVE)
for name,digest in half['sha256'].items():assert sha(HERE/name)==digest,name
assert native['status']=='COMPLETE' and native['worker_exit']==0
assert native['stop_reason'] is None and native['live_monitor_failures']==0
assert native['sampled_peak_combined_rss_bytes']<half['rss_cap_bytes']
assert native['parent_wall_seconds']<half['wall_cap_seconds']
assert native['protocol_sha256']==sha(HERE/'half_protocol.json')
assert native['stdout_sha256']==sha(HERE/'half_stdout.txt')
assert native['stderr_sha256']==sha(HERE/'half_stderr.txt')
assert audit_protocol['sources']=={'source':sha(SOURCE),
                                  'native_result':sha(HERE/'half_result.json'),
                                  'runner':sha(HERE/'audit_sage.py'),
                                  'runtime':sha(HERE/'sage_runtime_info.json')}
assert audit['status']=='COMPLETE'
assert audit['protocol_sha256']==sha(HERE/'audit_protocol.json')
assert audit['native_result_sha256']==sha(HERE/'half_result.json')
worker=native['worker']
assert worker['status']=='COMPLETE' and worker['panel']=='code_ordinal_0_to_19'
assert worker['left_triples']==worker['right_triples']==417024
assert worker['relations']==worker['coordinate_hits']==0
assert audit['triples']==[417024,417024]
assert audit['coordinate_hits']==0 and audit['relations']==[]
assert audit['prefixes']==worker['prefixes']
assert [row['intersection'] for row in worker['prefixes']]==[256,4096,62682,62212,5088,317,17]
assert [12,122,116,47,128,34][1]//4 not in half['code_ordinals_included']
result={'status':'PASS_INDEPENDENT_HALF_CODE_PREFIX_GATE',
        'protocol_sha256':sha(HERE/'half_protocol.json'),
        'native_result_sha256':sha(HERE/'half_result.json'),
        'audit_result_sha256':sha(HERE/'audit_result.json'),
        'source_sha256':sha(SOURCE),'checked_prefix_widths':half['prefix_bits']}
with (HERE/'terminal.json').open('x') as f:
    json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(result['status'])
