"""Read-only terminal binding for panel, full index, independent replays, and Lean."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE/name).read_text())


def check_protocol(name, local, external):
    p=load(name)
    for key,filename in local.items():
        assert p['source_sha256'][key]==sha(HERE/filename),(name,key)
    for key,path in external.items():
        assert p['source_sha256'][key]==sha(path),(name,key)
    return p


source=ROOT/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'
relation=ROOT/'n41_n131_w29_rotation_alignment_20261017/n41_audit_result.json'
sample=ROOT/'n41_n131_fivepair_w9_w29_20261017/sample_result.json'
sample_audit=ROOT/'n41_n131_fivepair_w9_w29_20261017/sample_audit_result.json'
sample_source=ROOT/'n41_n131_fivepair_w9_w29_20261017/sample_w29.cpp'
rank=ROOT/'n41_n131_w29_inverse_output_20261017/projection_result.json'
trace=ROOT/'n41_n131_s3_code_inverse_20261017/trace_result.json'

panel=load('panel.json')
assert panel['status']=='FROZEN_N41_TRIPLE_CODE_BOX_PANEL'
assert panel['source_sha256']=={'states':sha(source),'relation':sha(relation)}
assert len(panel['boxes'])==1025 and panel['draws']==1179
assert panel['boxes'][0]=={'kind':'archived_positive','codes':[61,16,11]}
assert len({tuple(box['codes']) for box in panel['boxes']})==1025
assert panel['fixed_slot_state_ids']=={'0':105,'4':111}

p=check_protocol('protocol.json',
                 {'script':'run_sage.py','runtime':'sage_runtime_info.json',
                  'panel':'panel.json'},
                 {'states':source,'relation':relation})
r=load('result.json')
assert r['status']=='PASS_N41_THREE_FREE_CODE_FAMILY_S3_PANEL'
assert r['protocol_sha256']==sha(HERE/'protocol.json')
assert r['box_count']==1025 and len(r['rows'])==1025
assert r['algebraic_hits']==r['exact_hit_boxes']==1
assert r['unknown_exception_boxes']==0 and r['s3_quadratics']==6150
assert r['rows'][0]['codes']==[61,16,11]
assert r['rows'][0]['exact_state_triples']==[[244,66,47]]
assert all(not row['algebraic_hit'] and not row['exact_state_triples']
           for row in r['rows'][1:])

check_protocol('audit_protocol.json',
               {'script':'audit_sage.py','runtime':'sage_runtime_info.json',
                'panel':'panel.json','producer':'result.json'},
               {'states':source})
ar=load('audit_result.json')
assert ar['status']=='PASS_INDEPENDENT_N41_TRIPLE_BOX_GROUP_REPLAY'
assert ar['protocol_sha256']==sha(HERE/'audit_protocol.json')
assert ar['source_sha256']['producer']==sha(HERE/'result.json')
assert ar['boxes']==1025 and ar['signed_assignment_comparisons']==65600
assert ar['group_chart_exceptions']==0 and ar['exact_hit_boxes']==1

check_protocol('full_protocol.json',
               {'script':'full_index_sage.py','runtime':'full_sage_runtime_info.json',
                'panel':'panel.json'},
               {'states':source,'relation':relation})
full=load('full_result.json')
assert full['status']=='PASS_N41_FULL_THREE_CODE_FAMILY_S3_INDEX'
assert full['protocol_sha256']==sha(HERE/'full_protocol.json')
assert full['source_eligible_pair_families']==4686
assert full['source_eligible_triple_boxes']==313158
assert full['left_coordinate_records']==full['distinct_left_coordinates']==37488
assert full['right_code_families']==69
assert full['exception_pair_count']==full['right_exception_count']==0
expected_boxes=[[61,11,16],[61,16,11]]
expected_witnesses=[[61,11,16,244,47,66],[61,16,11,244,66,47]]
assert full['candidate_code_boxes']==expected_boxes
assert full['exact_state_witnesses']==expected_witnesses

check_protocol('full_audit_protocol.json',
               {'script':'audit_full_sage.py','runtime':'full_audit_runtime_info.json',
                'producer':'full_result.json','producer_protocol':'full_protocol.json'},
               {'states':source})
fa=load('full_audit_result.json')
assert fa['status']=='PASS_INDEPENDENT_N41_FULL_THREE_CODE_GROUP_INDEX'
assert fa['protocol_sha256']==sha(HERE/'full_audit_protocol.json')
assert fa['source_sha256']['producer']==sha(HERE/'full_result.json')
for key in ('source_eligible_pair_families','source_eligible_triple_boxes',
            'left_coordinate_records','right_code_families','left_digest',
            'right_digest','candidate_code_boxes','exact_state_witnesses'):
    assert fa[key]==full[key],key
assert fa['group_chart_exceptions']==0

check_protocol('transfer_protocol.json',
               {'script':'transfer_bound.py','n41_full':'full_result.json',
                'n41_full_audit':'full_audit_result.json'},
               {'sample':sample,'sample_audit':sample_audit,
                'sample_source':sample_source,'product_rank':rank,
                'trace_census':trace})
transfer=load('transfer_result.json')
assert transfer['status']=='PASS_LITERAL_N131_PAIR_INDEX_PAYLOAD_OVER_4G'
assert transfer['protocol_sha256']==sha(HERE/'transfer_protocol.json')
assert transfer['source_sha256']=={
    key:sha(path) for key,path in {
        'sample':sample,'sample_audit':sample_audit,
        'sample_source':sample_source,'product_rank':rank,
        'trace_census':trace,'n41_full':HERE/'full_result.json',
        'n41_full_audit':HERE/'full_audit_result.json'}.items()}
n=json.loads(sample.read_text())['sample']['usable_sample_edges']
assert n==16677
good1=n-4*131
good2=n-6*131-4
assert (good1,good2)==(16153,15887)
assert good1*good2==transfer['nonexceptional_eligible_ordered_pair_families_at_least']==256622711
assert good1*good2*17==transfer['literal_index_payload_bytes_at_least']==4362586087
assert transfer['four_gib_bytes']==1<<32
assert transfer['excess_bytes']==4362586087-(1<<32)==67618791

check_protocol('transfer_audit_protocol.json',
               {'script':'audit_transfer.py','transfer_result':'transfer_result.json',
                'full_result':'full_result.json'},
               {'n41_source':source,'n131_sample_audit':sample_audit})
ta=load('transfer_audit_result.json')
assert ta['status']=='PASS_INDEPENDENT_TRANSFER_INTEGER_AND_N41_INCIDENCE'
assert ta['protocol_sha256']==sha(HERE/'transfer_audit_protocol.json')
assert ta['n41_max_codes_per_column']==2
assert ta['n41_pair_incidence_lower_bound']==3465
assert ta['n41_actual_eligible_pairs']==4686
assert ta['n131_pair_lower_bound']==256622711
assert ta['n131_literal_payload_bytes']==4362586087

lean=(HERE/'TripleBox.lean').read_text()
assert all(token not in lean for token in ('sorry','admit','sorryAx','axiom '))
assert (HERE/'lean-toolchain').read_text().strip()=='leanprover/lean4:v4.34.1'
axioms=(HERE/'lean.stdout').read_text()
for name in ('s3_as_quadratic','quadratic_root_pair','char_two_root_pair'):
    assert f"'TripleBox.{name}' depends on axioms: [propext, Classical.choice, Quot.sound]" in axioms
for name in ('n131_one_coordinate_payload',
             'conditional_payload_over_four_gib'):
    assert f"'TripleBox.{name}' does not depend on any axioms" in axioms
for name in ('freeze.stderr','run.stderr','audit.stderr','full.stderr',
             'full_audit.stderr','transfer.stderr','transfer_audit.stderr',
             'lean.stderr'):
    assert not (HERE/name).read_bytes(),name
for name in ('freeze.stdout','run.stdout','audit.stdout','full.stdout',
             'full_audit.stdout','transfer.stdout','transfer_audit.stdout'):
    assert b'PASS_' in (HERE/name).read_bytes() or name=='freeze.stdout',name

artifacts=['freeze_panel.py','panel.json','protocol.json','result.json','audit_protocol.json',
           'audit_result.json','full_protocol.json','full_result.json',
           'full_audit_protocol.json','full_audit_result.json',
           'transfer_protocol.json','transfer_result.json',
           'transfer_audit_protocol.json','transfer_audit_result.json',
           'TripleBox.lean',
           'lean.stdout','RESULT.md','PROOF_MAP.md']
print(json.dumps({'status':'PASS_N41_TRIPLE_BOX_TERMINAL',
                  'n41_full_eligible_boxes':313158,
                  'n131_literal_payload_lower_bytes':4362586087,
                  'artifact_sha256':{name:sha(HERE/name) for name in artifacts}},
                 sort_keys=True,indent=2))
