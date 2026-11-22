"""Source-bound payload check for the literal N131 full-coordinate index."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCES={
    'sample':ROOT/'n41_n131_fivepair_w9_w29_20261017/sample_result.json',
    'sample_audit':ROOT/'n41_n131_fivepair_w9_w29_20261017/sample_audit_result.json',
    'sample_source':ROOT/'n41_n131_fivepair_w9_w29_20261017/sample_w29.cpp',
    'product_rank':ROOT/'n41_n131_w29_inverse_output_20261017/projection_result.json',
    'trace_census':ROOT/'n41_n131_s3_code_inverse_20261017/trace_result.json',
    'n41_full':HERE/'full_result.json',
    'n41_full_audit':HERE/'full_audit_result.json',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((HERE/'transfer_protocol.json').read_text())
assert sha(Path(__file__))==protocol['source_sha256']['script']
for key,path in SOURCES.items():
    assert sha(path)==protocol['source_sha256'][key],key
assert not (HERE/'transfer_result.json').exists()
sample=json.loads(SOURCES['sample'].read_text())
sample_audit=json.loads(SOURCES['sample_audit'].read_text())
rank=json.loads(SOURCES['product_rank'].read_text())
trace=json.loads(SOURCES['trace_census'].read_text())
full=json.loads(SOURCES['n41_full'].read_text())
full_audit=json.loads(SOURCES['n41_full_audit'].read_text())

N=sample['sample']['usable_sample_edges']
assert N==sample_audit['counts']['usable_sample_edges']==16677
assert sample['sample']['same_column']==0
assert sample_audit['status']=='PASS_INDEPENDENT_SAGE_W29_SAMPLE_REPLAY'
assert rank['status']=='PASS_EXACT_PRODUCT_MAP_RANK_AND_BASIS_INVERSE'
assert any(row['field']=='n131' and row['canonical_source_bits']==28 and
           row['product_map_rank']==28 for row in rank['rows'])
assert trace['n131']['nonzero_trace_count']==0
assert full['status']=='PASS_N41_FULL_THREE_CODE_FAMILY_S3_INDEX'
assert full_audit['status']=='PASS_INDEPENDENT_N41_FULL_THREE_CODE_GROUP_INDEX'
assert full['candidate_code_boxes']==full_audit['candidate_code_boxes']

orbit_max=131
first_forbidden_columns=4
second_forbidden_columns=6
extra_exception_codes=4
first_good=N-first_forbidden_columns*orbit_max
second_good=N-second_forbidden_columns*orbit_max-extra_exception_codes
pair_families=first_good*second_good
raw_coordinate_bytes=(131+7)//8
payload=pair_families*raw_coordinate_bytes
limit=1<<32
assert first_good==16153 and second_good==15887
assert pair_families==256622711
assert raw_coordinate_bytes==17
assert payload==4362586087 and payload>limit

result={
    'status':'PASS_LITERAL_N131_PAIR_INDEX_PAYLOAD_OVER_4G',
    'model':'one full 131-bit coordinate stored per nonexceptional eligible ordered code pair; no code IDs, hash overhead, or extra roots charged',
    'sample_valid_distinct_codes':N,
    'max_orbit_size':orbit_max,
    'first_slot_fixed_column_exclusions_at_most':4*orbit_max,
    'second_slot_fixed_and_first_column_exclusions_at_most':6*orbit_max,
    'second_slot_s3_exception_code_exclusions_at_most':extra_exception_codes,
    'first_slot_remaining_codes_at_least':first_good,
    'second_slot_remaining_codes_per_first_at_least':second_good,
    'nonexceptional_eligible_ordered_pair_families_at_least':pair_families,
    'one_raw_coordinate_bytes':raw_coordinate_bytes,
    'literal_index_payload_bytes_at_least':payload,
    'four_gib_bytes':limit,
    'excess_bytes':payload-limit,
    'n41_index_control':{'pair_families':full['source_eligible_pair_families'],
                         'coordinate_records':full['left_coordinate_records'],
                         'eligible_triple_boxes':full['source_eligible_triple_boxes']},
    'protocol_sha256':sha(HERE/'transfer_protocol.json'),
    'source_sha256':{key:sha(path) for key,path in SOURCES.items()},
}
(HERE/'transfer_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({key:result[key] for key in
                  ('status','sample_valid_distinct_codes',
                   'nonexceptional_eligible_ordered_pair_families_at_least',
                   'literal_index_payload_bytes_at_least','excess_bytes')}))
