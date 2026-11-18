#!/usr/bin/env python3
"""Check prospective design, routing and rejection of corrupted admission controls."""
import ast,copy,json
from pathlib import Path
from setup_fresh_common import MODES,ACTUAL,STRATEGIES,INDEXED,CONTRASTS,FIXTURES,ORDERS
from setup_checks import check_setup
P=Path(__file__).resolve().parent
assert len(MODES)==8 and len(CONTRASTS)==9 and len(FIXTURES)==40
assert len(set(MODES))==8 and len({n for n,_,_ in CONTRASTS})==9
assert set(STRATEGIES.values())=={3,5,6,7,8}
assert len(FIXTURES)*5*len(MODES)==1600 and len(FIXTURES)*5*2==400
assert 9*3*5+3*5+5*5+5==180
checked=rejected=0
for i in range(5):
 for mode in MODES[4:]:
  raw=json.loads((P/'setup-cell-smoke-001'/f'{i}-{ACTUAL[mode]}.stdout').read_text())
  check_setup(raw,mode);checked+=1
  mutants=[]
  bad=copy.deepcopy(raw);bad['mode']='wrong-public-mode';mutants.append(bad)
  bad=copy.deepcopy(raw);bad['report']['Ok']['spec']['oracle_params']['vector_prepare']='9';mutants.append(bad)
  bad=copy.deepcopy(raw);bad['report']['Ok']['decomposition']['setup']['native'].pop('mitm_indexed_prepare_pairs');mutants.append(bad)
  bad=copy.deepcopy(raw);bad['report']['Ok']['decomposition']['cost']['native']['walk_batch_inverse_vector_elements']=0;mutants.append(bad)
  for bad in mutants:
   try:check_setup(bad,mode)
   except (AssertionError,KeyError):rejected+=1
   else:raise AssertionError('Corrupted native control admitted')
for name in ['run_setup_fresh.py','analyze_setup_fresh.py','freeze_setup_inputs.py','seal_setup_provenance.py','record_setup_metrics.py','replay_setup_fresh_answers.py','replay_setup_fresh_states.py']:
 ast.parse((P/name).read_text())
plan=json.loads((P/'setup-raw-reference-plan.json').read_text())
assert plan['expected_references']==len(set(plan['paths']))==25 and plan['expected_metrics']==180
out=dict(status='pass',recorded_native_controls_accepted=checked,corrupted_controls_rejected=rejected,design=dict(methods=8,fixtures_per_field=40,blocks=200,ic_answers=1600,rho_answers=400,aa_answers=400,metrics=180,raw_references=25),scope='Offline packet guards only; no fresh timing or generated identity result')
target=P/'local-tmp/setup-packet-check.json';assert not target.exists();target.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
