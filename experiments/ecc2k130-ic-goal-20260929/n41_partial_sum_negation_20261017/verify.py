"""Check the frozen quotient, ordinary hit, and forced-sign control."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
OLD=D.parent/'n41_sixpair_shared_target_20261017'
SORTED=D.parent/'n41_partial_sum_compressibility_20261017'


def read(path):return json.loads(path.read_text())


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def main():
    p=read(D/'protocol.json');r=read(D/'run_result.json')
    flip=read(D/'flip_control_result.json')
    audit=read(OLD/'join_audit_result.json')
    old=read(OLD/'join_result.json')
    sorted_run=read(SORTED/'run_result.json')
    assert sha(D/'negation_join.cpp')==p['source_sha256']
    assert sha(D/'run.py')==p['runner_sha256']==r['runner_sha256']
    assert sha(OLD/'join_exact.cpp')==p['included_source_sha256']
    assert sha(Path(p['input_path']))==p['input_sha256']
    assert sha(D/'protocol.json')==r['protocol_sha256']
    assert sha(D/'negation_join')==r['binary_sha256']
    for ext in ('stdout','stderr'):
        assert sha(D/('compile.'+ext))==r['compile_'+ext+'_sha256']
        assert sha(D/('run.'+ext))==r[ext+'_sha256']
    assert r['status']=='HIT_PENDING_INDEPENDENT_REPLAY'
    assert r['exit_code']==0 and r['stop_reason'] is None and not r['monitor_degraded']
    assert r['sampled_peak_combined_rss_bytes']<p['rss_cap_bytes']
    lines=(D/'run.stdout').read_text().splitlines()
    left=int(next(line.split()[1] for line in lines if line.startswith('LEFT_ENUM ')))
    census=next(line.split() for line in lines if line.startswith('CENSUS '))
    hit=next(line.split() for line in lines if line.startswith('HIT '))
    assert left==1875072
    assert list(map(int,census[1:5]))==[1875072,1875068,0,4]
    assert list(map(int,census[5:10]))==[256,65536,1774282,1874644,1875068]
    assert r['hit_lines']==[' '.join(hit)]
    ids=list(map(int,hit[1:7]))
    assert ids==[row['state_id'] for row in audit['pair_rows']]
    assert int(hit[9])==0 and int(hit[7])==1100323
    assert p['public_raw_target']==audit['raw_target']
    assert audit['status']=='PASS_INDEPENDENT_N41_SIXPAIR_PUBLIC_RELATION'
    assert old['status']=='HIT_PENDING_SAGE_REPLAY'
    assert flip['status']=='PASS_FLIPPED_LOOKUP'
    assert flip['binary_sha256']==r['binary_sha256']
    assert flip['source_input_sha256']==p['input_sha256']
    assert sha(D/'flip_control.tsv')==flip['control_input_sha256']
    for ext in ('stdout','stderr'):
        assert sha(D/('flip_control.'+ext))==flip[ext+'_sha256']
    flip_hit=flip['hit_line'].split()
    assert list(map(int,flip_hit[1:7]))==flip['flipped_left_ids']+flip['right_ids']
    assert int(flip_hit[7])==1 and int(flip_hit[9])==1
    assert flip['hit_line'] in (D/'flip_control.stdout').read_text()
    source_state=read(SORTED/'state_audit.json')
    assert source_state['status']=='PASS' and source_state['signed_states_checked']==960
    assert (SORTED/'lean_build.exit').read_text().strip()=='0'
    result={'status':'PASS','ordinary_hit_ids':ids,
            'ordinary_replay':'ARCHIVED_INDEPENDENT_SAGE',
            'flip_control':'PASS_FIRST_PROBE',
            'left_rows':left,'unique_x':1875068,
            'query_wall_s':r['wall_s'],
            'sampled_peak_combined_rss_bytes':r['sampled_peak_combined_rss_bytes'],
            'sorted_wall_s':sorted_run['wall_s'],
            'sorted_peak_bytes':sorted_run['sampled_peak_combined_rss_bytes'],
            'hash_wall_s':old['wall_ns']/1e9,
            'hash_peak_bytes':old['sampled_peak_combined_rss_bytes'],
            'flip_control_source_sha256':sha(D/'flip_control.py')}
    (D/'verification.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
