"""Read-only archive check for W29 prefix, full census, and count replay."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())


def check_run(label,supervisor,expected_status):
    cfg=load(HERE/f'query_protocol_{label}.json')
    receipt=load(HERE/f'{label}.receipt.json')
    assert cfg['status']==expected_status and cfg['candidate_id'] is None
    assert cfg['worker_count']==1 and cfg['rss_cap_bytes']==4294967296
    assert cfg['supervisor_sha256']==sha(HERE/supervisor)
    for rec in [cfg['binary'],cfg['input'],*cfg['dependencies'].values()]:
        assert sha(rec['path'])==rec['sha256']
    assert receipt['status']=='COMPLETE' and receipt['exit_code']==0
    assert receipt['protocol_sha256']==sha(HERE/f'query_protocol_{label}.json')
    assert receipt['stdout_sha256']==sha(HERE/f'{label}.stdout')
    assert receipt['stderr_sha256']==sha(HERE/f'{label}.stderr')
    assert receipt['sampled_peak_combined_rss_bytes']<4294967296
    assert receipt['wall_seconds']<cfg['wall_cap_seconds']
    return receipt


def main():
    prep=load(HERE/'prepare_result.json')
    assert prep['status']=='PASS_NATIVE_PAIR_SOURCE_PREPARATION'
    assert prep['protocol_sha256']==sha(HERE/'prepare_protocol.json')
    assert prep['script_sha256']==sha(HERE/'prepare_sage.py')
    for rec in prep['cases']:assert sha(rec['path'])==rec['sha256']
    build=load(HERE/'build_result.json')
    assert build['status']=='PASS_NATIVE_SOURCE_BUILDS'
    for binary,rec in build['entries'].items():
        assert sha(HERE/binary)==rec['binary_sha256']
        assert sha(HERE/(binary+'.cpp'))==rec['source_sha256']
    for label,n in [('n41',41),('n131',131)]:
        check_run(label,'supervise.py',f'FROZEN_BEFORE_NATIVE_PAIR_SOURCE_{label.upper()}')
        audit=load(HERE/f'audit_result_{label}.json')
        assert audit['status']==f'PASS_NATIVE_PAIR_SOURCE_AUDIT_{label.upper()}'
        assert audit['field_degree']==n
        assert audit['stdout_sha256']==sha(HERE/f'{label}.stdout')
    full=check_run('n131_full','supervise_full.py',
                   'FROZEN_BEFORE_NATIVE_PAIR_SOURCE_N131_FULL')
    count=check_run('n131_count','supervise_count.py',
                    'FROZEN_BEFORE_INDEPENDENT_W29_SOURCE_COUNT')
    audit_full=load(HERE/'full_audit_result.json')
    audit_count=load(HERE/'count_audit_result.json')
    assert audit_full['status']=='PASS_FULL_W29_SOURCE_CENSUS_ARCHIVE'
    assert audit_count['status']=='PASS_INDEPENDENT_W29_SOURCE_COUNT'
    assert audit_full['valid_codes_reported']==audit_count['valid_codes']==67109836
    assert audit_full['outputs_reported']==134219672
    assert audit_full['sage_prefix_outputs_replayed']==2128
    assert audit_count['codes_checked']==1<<28
    assert audit_full['stdout_sha256']==sha(HERE/'n131_full.stdout')
    assert audit_count['stdout_sha256']==sha(HERE/'n131_count.stdout')
    result={'status':'PASS_W29_FULL_SOURCE_ARCHIVE','candidate_id':None,
            'curve_id':'EC1N131Ckb1heb5f1998f20b','codes_checked':1<<28,
            'valid_codes':67109836,'output_roots':134219672,
            'full_parent_wall_seconds':full['wall_seconds'],
            'count_parent_wall_seconds':count['wall_seconds'],
            'script_sha256':sha(__file__)}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
