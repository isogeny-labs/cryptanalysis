"""Hash-bound audit of exact inverse-trace slice ANFs and valid-code ranks."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=json.loads((H/'terminal_protocol.json').read_text())
assert cfg['status']=='FROZEN_BEFORE_INVERSE_TRACE_TERMINAL'
for label,s in cfg['sources'].items():assert sha(s['path'])==s['sha256'],label
for name in ('protocol_v3.json','rank_protocol_v2.json','audit_protocol.json'):
    p=json.loads((H/name).read_text())
    for label,s in p['sources'].items():assert sha(s['path'])==s['sha256'],(name,label)
truth=json.loads((H/'result_v3.json').read_text())
rank=json.loads((H/'rank_result_v2.json').read_text())
audit=json.loads((H/'audit_result.json').read_text())
assert truth['status']=='COMPLETE_INVERSE_TRACE_ANF'
assert truth['families']['n41']['full_valid_count']==281
assert truth['wall_seconds']<120 and truth['peak_rss_raw']<4294967296
assert truth['rlimit_status']=='UNAVAILABLE_OS_AFTER_V1_VALUEERROR'
assert all(v==[0,0,0] for f in truth['families'].values()
           for v in f['known_code_checks'].values())
n131=truth['families']['n131']['slices'];assert len(n131)==3
assert [x['valid_codes'] for x in n131]==[1016,1013,998]
assert [x['trace_inv_a']['degree'] for x in n131]==[12,12,12]
assert [x['trace_inv_b']['degree'] for x in n131]==[12,12,11]
assert all(x['trace_a']['degree']==-1 for x in n131)
assert rank['status']=='COMPLETE_VALID_CODE_ANNIHILATOR_RANK'
assert len(rank['rows'])==4 and rank['wall_seconds']<120
for row in rank['rows']:
    d=4 if row['family']=='n131' else 3
    selected=next(x for x in row['ranks'] if x['degree_cap']==d)
    expected=794 if d==4 else 130
    assert selected['monomials']==selected['rank_on_valid_codes']==expected
    assert selected['annihilator_dimension']==0 and len(selected['pivot_codes'])==expected
    if row['family']=='n131':
        assert all(x['annihilator_dimension']==0 for x in row['ranks'])
assert audit['status']=='PASS_INDEPENDENT_VALID_PIVOT_AUDIT'
assert audit['valid_pivots_checked']==2512 and audit['wall_seconds']<120
assert audit['peak_rss_raw']<4294967296
for row in audit['rows']:
    assert row['valid_pivots_checked']==row['independent_rank']
for name in ('first_attempt.json','second_attempt.json'):
    assert json.loads((H/'scratch'/name).read_text())['status']=='PRODUCER_FAILURE'
lean=(H/'NoAnnihilator.lean').read_text();output=(H/'lean.stdout').read_text()
assert all(bad not in lean for bad in ('sorry','admit','axiom '))
assert (H/'lean.stderr').read_bytes()==b'' and 'sorryAx' not in output
assert "'InverseTraceANF.no_nonzero_annihilator_of_injective_eval' does not depend on any axioms" in output
field_lean=(H/'FieldIdentities.lean').read_text()
field_output=(H/'field_lean.stdout').read_text()
assert all(bad not in field_lean for bad in ('sorry','admit','axiom '))
assert (H/'field_lean.stderr').read_bytes()==b'' and 'sorryAx' not in field_output
for declaration in ('first_source_inverse_identity','second_source_inverse_identity',
                    'source_trace_conditions_iff'):
    assert "'InverseTraceANF."+declaration+"' depends on axioms: [propext, Classical.choice, Quot.sound]" in field_output
result={'status':'PASS_W33_INVERSE_TRACE_LOW_DEGREE_FALSIFIER','candidate_id':None,
        'n41_exact_valid_codes':281,'n131_slices':3,'n131_degree_four_full_rank_slices':3,
        'independent_valid_pivots_checked':2512,
        'protocol_sha256':sha(H/'terminal_protocol.json'),
        'verifier_sha256':sha(Path(__file__))}
(H/'terminal_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps(result,sort_keys=True))
