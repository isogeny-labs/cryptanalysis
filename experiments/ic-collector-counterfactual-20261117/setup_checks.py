"""Preserve raw public modes; reuse admitted native semantic checks."""
from counterfactual_checks import check,equal
from setup_fresh_common import MODES,ACTUAL,STRATEGIES

def check_setup(raw,mode):
    assert mode in MODES[3:] and raw['mode']==ACTUAL[mode]
    cell='sp' if mode==MODES[3] else 'ip'
    check(dict(raw,mode='mitm-counterfactual-'+cell),cell)
    params=raw['report']['Ok']['spec']['oracle_params']
    assert int(params['vector_prepare'])==STRATEGIES[mode]
    assert int(params.get('suppress_indexed_counter','0'))==0
    return raw
