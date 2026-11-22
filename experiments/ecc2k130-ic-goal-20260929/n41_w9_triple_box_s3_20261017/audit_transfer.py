"""Independent integer replay and N41 incidence control for transfer bound."""
import collections
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/'n41_n131_w29_rotation_alignment_20261017/aligned_states.json'
SAMPLE=ROOT/'n41_n131_fivepair_w9_w29_20261017/sample_audit_result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protocol=json.loads((HERE/'transfer_audit_protocol.json').read_text())
for key,path in {'script':Path(__file__),'n41_source':SOURCE,
                 'n131_sample_audit':SAMPLE,
                 'transfer_result':HERE/'transfer_result.json',
                 'full_result':HERE/'full_result.json'}.items():
    assert sha(path)==protocol['source_sha256'][key],key
assert not (HERE/'transfer_audit_result.json').exists()
source=json.loads(SOURCE.read_text())
sample=json.loads(SAMPLE.read_text())
transfer=json.loads((HERE/'transfer_result.json').read_text())
full=json.loads((HERE/'full_result.json').read_text())

incidence=collections.Counter()
for code in range(source['usable_edges']):
    columns=source['states'][0][4*code]['columns']
    assert len(columns)==len(set(columns))==2
    incidence.update(columns)
maximum=max(incidence.values())
assert maximum==2
n41=source['usable_edges']
n41_bound=max(0,n41-4*maximum)*max(0,n41-6*maximum-4)
assert n41_bound==3465
assert n41_bound<=full['source_eligible_pair_families']==4686

n=sample['counts']['usable_sample_edges']
assert n==16677
first=n-4*131
second=n-6*131-4
minimal_pairs=first*second
minimal_bytes=minimal_pairs*((131+7)//8)
assert minimal_pairs==transfer['nonexceptional_eligible_ordered_pair_families_at_least']
assert minimal_bytes==transfer['literal_index_payload_bytes_at_least']
assert minimal_bytes-(1<<32)==transfer['excess_bytes']

result={
    'status':'PASS_INDEPENDENT_TRANSFER_INTEGER_AND_N41_INCIDENCE',
    'n41_distinct_folded_columns':len(incidence),
    'n41_max_codes_per_column':maximum,
    'n41_pair_incidence_lower_bound':n41_bound,
    'n41_actual_eligible_pairs':full['source_eligible_pair_families'],
    'n131_sample_codes':n,
    'n131_pair_lower_bound':minimal_pairs,
    'n131_literal_payload_bytes':minimal_bytes,
    'protocol_sha256':sha(HERE/'transfer_audit_protocol.json'),
    'source_sha256':{'transfer_result':sha(HERE/'transfer_result.json'),
                     'full_result':sha(HERE/'full_result.json'),
                     'n41_source':sha(SOURCE)},
}
(HERE/'transfer_audit_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:result[k] for k in
                  ('status','n41_max_codes_per_column',
                   'n41_pair_incidence_lower_bound',
                   'n131_pair_lower_bound','n131_literal_payload_bytes')}))
