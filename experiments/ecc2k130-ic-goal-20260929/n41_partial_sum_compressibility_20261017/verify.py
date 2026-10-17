"""Verify source binding, exact census, and archived same-point replay."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
OLD=D.parent/'n41_sixpair_shared_target_20261017'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(path.read_text())


def main():
    p=read(D/'protocol.json');r=read(D/'run_result.json')
    audit=read(OLD/'join_audit_result.json')
    old=read(OLD/'join_result.json')
    assert sha(D/'sorted_join.cpp')==p['source_sha256']
    assert sha(D/'run.py')==p['runner_sha256']==r['runner_sha256']
    assert sha(OLD/'join_exact.cpp')==p['included_source_sha256']
    assert sha(Path(p['input_path']))==p['input_sha256']
    assert sha(D/'protocol.json')==r['protocol_sha256']
    assert sha(D/'sorted_join')==r['binary_sha256']
    for ext in ('stdout','stderr'):
        assert sha(D/('compile.'+ext))==r['compile_'+ext+'_sha256']
        assert sha(D/('run.'+ext))==r[ext+'_sha256']
    assert r['status']=='HIT_PENDING_INDEPENDENT_REPLAY'
    assert r['exit_code']==0 and r['stop_reason'] is None and not r['monitor_degraded']
    assert r['sampled_peak_combined_rss_bytes']<p['rss_cap_bytes']
    lines=(D/'run.stdout').read_text().splitlines()
    census=next(line.split() for line in lines if line.startswith('CENSUS '))
    hit=next(line.split() for line in lines if line.startswith('HIT '))
    assert len(r['hit_lines'])==1 and r['hit_lines'][0]==' '.join(hit)
    left=int(next(line.split()[1] for line in lines if line.startswith('LEFT_ENUM ')))
    unique_points,unique_x,collision_rows,both_y=map(int,census[1:5])
    assert left==3750144 and unique_points==3750136
    assert collision_rows==left-unique_points==8
    assert unique_points==2*unique_x and both_y==unique_x==1875068
    assert list(map(int,census[5:10]))==[256,65536,1774282,1874644,1875068]
    ids=list(map(int,hit[1:7]))
    assert ids==[row['state_id'] for row in audit['pair_rows']]
    assert p['public_raw_target']==audit['raw_target']
    assert audit['status']=='PASS_INDEPENDENT_N41_SIXPAIR_PUBLIC_RELATION'
    assert old['status']=='HIT_PENDING_SAGE_REPLAY'
    states=read(D/'state_audit.json')
    assert states['status']=='PASS' and states['source_input_sha256']==p['input_sha256']
    assert states['signed_states_checked']==960 and states['involution_pairs']==480
    assert (D/'lean_build.exit').read_text().strip()=='0'
    lean=(D/'lean_build.stdout').read_text()
    assert 'NegationQuotient.tripleNegation' in lean
    assert 'NegationQuotient.lookupEitherSign' in lean
    assert (D/'run_attempt1.exit').read_text().strip()=='1'
    assert 'ModuleNotFoundError' in (D/'run_attempt1.stderr').read_text()
    result={'status':'PASS','relation_replay':'ARCHIVED_INDEPENDENT_SAGE',
            'left_rows':left,'unique_points':unique_points,'unique_x':unique_x,
            'negation_complete_x':both_y,'duplicate_point_rows':collision_rows,
            'hit_ids':ids,'query_wall_s':r['wall_s'],
            'sampled_peak_combined_rss_bytes':r['sampled_peak_combined_rss_bytes'],
            'old_wall_s':old['wall_ns']/1e9,
            'old_peak_bytes':old['sampled_peak_combined_rss_bytes']}
    (D/'verification.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
