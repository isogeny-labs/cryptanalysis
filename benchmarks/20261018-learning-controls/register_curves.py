import copy, hashlib, json, re
from pathlib import Path
import yaml
from tools.curve_identity import curve_identity
root=Path('/workspace/cryptanalysis')
registry=root/'experiments/ic-candidate-catalog/curves.yaml'
source=root/'experiments/ideas_learning_20261018/curve-records.json'
raw=registry.read_bytes(); old=yaml.safe_load(raw); records=json.loads(source.read_text())
assert set(old)=={'schema_version','identity_rule','curves'}
assert len(records)==10
additions={}; receipt=[]; seen=set()
for row in records:
    match=re.fullmatch(r'EC1N[0-9]+C([a-z][a-z0-9]*)h[a-f0-9]{12}',row['curve_id']); assert match
    identity=curve_identity(row['field'],row['curve'],match[1])
    assert all(identity[k]==row[k] for k in identity), (identity,row)
    assert identity['curve_uid'] not in seen; seen.add(identity['curve_uid'])
    for alias, existing in old['curves'].items():
        assert existing.get('curve_id')!=row['curve_id'], 'existing ID requires explicit identity reuse review'
    alias=f"ideas20261018_n{row['field']['degree']}_b{row['curve']['a6']}_h{row['curve_sha256'][:12]}"
    assert alias not in old['curves']
    entry={'label':f"2026-10-18 learning-control exact binary curve n={row['field']['degree']}, b={row['curve']['a6']}",
           'curve_tag':match[1], 'curve_ref':f"ideas_learning_20261018/{alias}", **identity,
           'field':copy.deepcopy(row['field']), 'curve':copy.deepcopy(row['curve']),
           'endomorphism':{'endomorphism_order_conductor':None,'frobenius_order_conductor':None,'volcano_levels':{},'status':'not_computed'},
           'isogeny_routes':{'incoming':[],'outgoing':[]},
           'evidence_ref':'experiments/ideas_learning_20261018/curve-records.json',
           'provenance':{'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'validation_ref':'experiments/ideas_learning_20261018/verify.json','scope':'Exact representation identity only; finite subgroup admission and group-law controls remain source evidence; no isogeny or performance promotion.'}}
    additions[alias]=entry; receipt.append({'alias':alias,**identity,'exact_metadata_hashes_match':True})
text='\n# Exact local records from the 2026-10-18 bounded learning controls.\n'
text+=''.join('  '+line+'\n' for line in yaml.safe_dump(additions,sort_keys=False,allow_unicode=True).splitlines())
registry.write_bytes(raw+text.encode())
new=yaml.safe_load(registry.read_bytes()); assert all(new['curves'][k]==v for k,v in old['curves'].items())
for alias,entry in additions.items():
    assert new['curves'][alias]==entry
    assert curve_identity(entry['field'],entry['curve'],entry['curve_tag'])['curve_uid']==entry['curve_uid']
output={'schema':'campaign-curve-registry-verification/v1','records_added':len(additions),'old_records_unchanged':True,'source':'experiments/ideas_learning_20261018/curve-records.json','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'registry_before_sha256':hashlib.sha256(raw).hexdigest(),'registry_after_sha256':hashlib.sha256(registry.read_bytes()).hexdigest(),'verification':'Metadata canonical SHA256 and UID recomputation using tools/curve_identity.py; not independent mathematical certification.','records':receipt}
(root/'benchmarks/20261018-learning-controls/registry-verification.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'added':len(additions),'old_unchanged':True}))
