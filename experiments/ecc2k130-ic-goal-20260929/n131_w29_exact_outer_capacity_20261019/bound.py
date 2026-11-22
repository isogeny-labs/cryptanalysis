"""Instantiate the fixed-outer coverage theorem with the complete W29 census."""
import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def ceildiv(a,b):return (a+b-1)//b

def threshold(r,m,k):
    values=ceildiv(r,2*k*m)
    bits=(values-1).bit_length()
    assert 2*(1<<(bits-1))*k*m<r<=2*(1<<bits)*k*m
    return {'fixed_outer_proposals_per_advice':k,
            'minimum_advice_values_for_half_bound':values,
            'minimum_advice_bits_for_half_bound':bits,
            'below_threshold_numerator':(1<<(bits-1))*k*m,
            'at_threshold_numerator':(1<<bits)*k*m,
            'probability_denominator':r}

def main():
    cfg=json.loads((HERE/'protocol.json').read_text())
    assert cfg['status']=='FROZEN_BEFORE_EXACT_W29_OUTER_CAPACITY'
    assert cfg['script_sha256']==sha(__file__)
    for rec in cfg['sources'].values():assert sha(rec['path'])==rec['sha256']
    read=lambda label:json.loads(Path(cfg['sources'][label]['path']).read_text())
    count=read('independent_count')
    stream=read('full_stream')
    old=read('prior_bound')
    assert count['status']=='PASS_INDEPENDENT_W29_SOURCE_COUNT'
    assert stream['status']=='PASS_FULL_STREAM_TERMINAL_REPLAY'
    assert old['status']=='PASS_W29_FIXED_OUTER_COVERAGE_BOUND'
    assert count['codes_checked']==1<<28
    B=count['valid_codes']
    assert B==count['producer_valid_codes']==stream['source_valid_codes']==67109836
    assert stream['source_outputs']==2*B and stream['stream_bytes']==17*2*B
    assert all(row['roots']==4*B for row in stream['queries'].values())
    r=old['n131']['subgroup_order']
    assert r==680564733841876926932320129493409985129
    S=4*B;M=S*S
    assert S==268439344 and M==72059681407150336
    assert M<old['n131']['ordered_right_pair_sum_ceiling']
    getcontext().prec=60
    panels=[threshold(r,M,k) for k in cfg['proposal_budgets']]
    assert [row['minimum_advice_bits_for_half_bound'] for row in panels]==[72,70,69,48]
    native=stream['queries']
    constructed_budget=600//native['linear']['parent_wall_seconds']
    public_budget=600//native['public_linear']['parent_wall_seconds']
    assert int(constructed_budget)==8 and int(public_budget)==6
    result={'status':'PASS_EXACT_W29_OUTER_CAPACITY','candidate_id':None,
            'curve_id':'EC1N131Ckb1heb5f1998f20b',
            'subgroup_order':r,'complete_valid_codes':B,
            'signed_pair_states_per_slot_upper':S,
            'ordered_right_pair_sum_upper':M,
            'upper_reduction_from_old_capacity':{'numerator':old['n131']['ordered_right_pair_sum_ceiling'],
                                                 'denominator':M},
            'thresholds':panels,
            'uniform_subgroup_success_upper':[
                {'proposals':k,'numerator':k*M,'denominator':r,
                 'decimal':str(Decimal(k*M)/Decimal(r))} for k in (1,6,8)],
            'observed_sequential_query_projection':{
                'six_hundred_second_cap':600,
                'constructed_residuals_at_observed_rate':int(constructed_budget),
                'public_residuals_at_observed_rate':int(public_budget),
                'constructed_query_wall_seconds':native['linear']['parent_wall_seconds'],
                'public_query_wall_seconds':native['public_linear']['parent_wall_seconds']},
            'protocol_sha256':sha(HERE/'protocol.json'),
            'script_sha256':sha(__file__)}
    (HERE/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'signed_states':S,'pair_upper':M,
                      'advice_bits':[x['minimum_advice_bits_for_half_bound'] for x in panels]},sort_keys=True))

if __name__=='__main__':main()
