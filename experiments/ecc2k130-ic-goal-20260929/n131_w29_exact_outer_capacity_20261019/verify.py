"""Recompute the exact W29 bound and audit its source and Lean receipts."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    cfg=json.loads((HERE/'protocol.json').read_text())
    result=json.loads((HERE/'result.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_EXACT_W29_OUTER_CAPACITY'
    assert result['status']=='PASS_EXACT_W29_OUTER_CAPACITY'
    assert result['protocol_sha256']==sha(HERE/'protocol.json')
    assert result['script_sha256']==sha(HERE/'bound.py')==cfg['script_sha256']
    for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
    count=json.loads(Path(cfg['sources']['independent_count']['path']).read_text())
    stream=json.loads(Path(cfg['sources']['full_stream']['path']).read_text())
    old=json.loads(Path(cfg['sources']['prior_bound']['path']).read_text())
    B=count['valid_codes']
    assert count['status']=='PASS_INDEPENDENT_W29_SOURCE_COUNT'
    assert stream['status']=='PASS_FULL_STREAM_TERMINAL_REPLAY'
    assert B==count['producer_valid_codes']==stream['source_valid_codes']==result['complete_valid_codes']
    S=4*B;M=S*S;r=old['n131']['subgroup_order']
    assert (S,M,r)==(result['signed_pair_states_per_slot_upper'],
                      result['ordered_right_pair_sum_upper'],result['subgroup_order'])
    assert M<old['n131']['ordered_right_pair_sum_ceiling']
    assert [row['fixed_outer_proposals_per_advice'] for row in result['thresholds']]==cfg['proposal_budgets']
    assert [row['minimum_advice_bits_for_half_bound'] for row in result['thresholds']]==[72,70,69,48]
    for row in result['thresholds']:
        k=row['fixed_outer_proposals_per_advice'];b=row['minimum_advice_bits_for_half_bound']
        assert row['minimum_advice_values_for_half_bound']==(r+2*k*M-1)//(2*k*M)
        assert 2*(1<<(b-1))*k*M<r<=2*(1<<b)*k*M
    lean=(HERE/'lean.stdout').read_text()
    assert lean.count('depends on axioms:')+lean.count('does not depend on any axioms')==12
    assert 'sorryAx' not in lean and not (HERE/'lean.stderr').read_text()
    assert 'sorry' not in (HERE/'ExactCapacity.lean').read_text()
    audit={'status':'PASS_EXACT_W29_CAPACITY_AUDIT','candidate_id':None,
           'complete_codes':B,'ordered_pair_upper':M,
           'threshold_bits':[row['minimum_advice_bits_for_half_bound'] for row in result['thresholds']],
           'result_sha256':sha(HERE/'result.json'),
           'lean_stdout_sha256':sha(HERE/'lean.stdout')}
    (HERE/'verification_result.json').write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
    print(json.dumps(audit,sort_keys=True))

if __name__=='__main__':main()
