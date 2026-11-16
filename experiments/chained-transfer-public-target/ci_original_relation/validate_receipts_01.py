"""Operational process/file/proof-log custody only; Rust/Lean check all mathematics."""
from pathlib import Path
import hashlib,json,re,sys
repo,out=map(Path,sys.argv[1:3]);study=repo/'experiments/chained-transfer-public-target';ci=study/'ci_original_relation'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
expected=[line.split()for line in(ci/'phase-plan-01.txt').read_text().splitlines()]
assert expected[-2:]==[['complete-operational-receipt-validation','0'],['final-published-source-guards','0']]
actual=[line.split()for line in(out/'phases.txt').read_text().splitlines()]
assert len(actual)in[len(expected)-2,len(expected)-1,len(expected)]
assert actual==[[name,want,want]for name,want in expected[:len(actual)]]
assert len({row[0]for row in expected})==len(expected)
for name,want in expected[:len(actual)]:assert(out/(name+'.pipe-exits')).read_text().split()==[want,'0']
checkpoint=out/'original-pre-native-checkpoint'
assert(checkpoint/'source-head.txt').read_bytes()==(out/'consumer-head.txt').read_bytes()
for label in ['original-gate','readback-pack','readback-resume','readback-meta']:assert(checkpoint/(label+'.exit')).read_text().strip()=='0'
assert(checkpoint/'original-RESUME.md').read_bytes()==(checkpoint/'remote-RESUME.md').read_bytes()==(checkpoint/'pack-RESUME.md').read_bytes()==(repo/'.resume/RESUME.md').read_bytes()
meta=read(checkpoint/'remote-meta.json');assert meta['head']==(out/'consumer-head.txt').read_text().strip()and meta['repo']=='cryptanalysis'
assert(checkpoint/'remote-meta.json').read_bytes()==(checkpoint/'pack-meta.json').read_bytes()
legacy=out/'inherited-original-fixed-ic'
assert(legacy/'original.exit').read_text().strip()=='0'and(legacy/'final-source-guards.exit').read_text().strip()=='0'
old_plan=read(study/'ci_original_fixed_ic/phases-01.json')['ordered_phases']
assert[ln.split()for ln in(legacy/'phases.txt').read_text().splitlines()]==[[row['name'],str(row['expected_exit']),str(row['expected_exit'])]for row in old_plan]
for row in old_plan:assert(legacy/(row['name']+'.pipe-exits')).read_text().split()==[str(row['expected_exit']),'0']
# Preserve exact original setup copies and references to their complete bytes.
prepared=read(out/'engine-prepared.json');assert prepared==read(legacy/'engine-prepared.json')
assert len(prepared['files'])==2
for row in prepared['files']:
    original=Path(row['copy']);assert original.is_relative_to(legacy)
    assert original.stat().st_size==row['bytes']and sha(original)==row['sha256']
    assert Path(row['actual_path']).read_bytes()==original.read_bytes()
assert{Path(row['actual_path']).suffix for row in prepared['files']}=={'.rlib','.rmeta'}
for label in ['passive','character-producer','character-auditor','character-mutation']:
    v=read(out/('engine-reused-'+label+'.json'))
    assert v['actual_reuse']is True and v['actual_prepared_bytes_unchanged']is True and v['Cargo_artifact']['fresh']is True
    assert len(v['actual_aliases'])==2
    for row in v['actual_aliases']:
        assert row['whole_before_and_after_bytes_equal']is True
        assert sha(Path(row['dependency_path']))==row['sha256']and Path(row['dependency_path']).stat().st_size==row['bytes']
for label in ['passive','character']:
    assert read(out/('engine-closure-'+label+'.json'))['exact_complete_closure']is not None
for name in ['rank','comparator']:
    v=read(out/(name+'-no-field-engine/engine-closure-original-kernel.json'))
    assert v['exact_complete_closure']is None and v['field_engine']=='none'
compiled=read(out/'passive-compiled-binary.json');runtime=read(out/'passive-runtime-binary.json')
assert compiled['actual_Cargo_artifact']==runtime['actual_Cargo_artifact']and compiled['actual_path']==runtime['actual_path']and runtime['compiled_runtime_equal']is True
assert(out/'passive-original-compiled-test.bin').read_bytes()==(out/'passive-actual-runtime-test.bin').read_bytes()
assert sha(out/'passive-original-compiled-test.bin')==compiled['sha256']==runtime['sha256']
labels=['passive-auditor','passive-native-auditor','rank-producer','rank-replay','rank-controls','character-producer','character-auditor','character-mutation','comparator']
for label in labels:
    a=read(out/(label+'-compiled-custody.json'));b=read(out/(label+'-runtime-custody.json'))
    assert a['actual_Cargo_artifact']==b['actual_Cargo_artifact']and a['actual_path']==b['actual_path']and b['whole_compiled_runtime_equal']is True
    assert(out/('actual-compiled-'+label+'.bin')).read_bytes()==(out/('actual-runtime-'+label+'.bin')).read_bytes()
    assert sha(out/('actual-compiled-'+label+'.bin'))==a['sha256']==b['sha256']
for package in ['original-relation-kernel-01','original-relation-rank-01','original-relation-character-01','ci_original_relation/audit-03']:
    source=study/package;snapshot=out/'actual-compiled-source'/package
    for p in source.rglob('*'):
        if p.is_file():assert p.read_bytes()==(snapshot/p.relative_to(source)).read_bytes(),str(p)
for stage in ['available','selected','candidate','descent']:
    assert(out/('passive-'+stage+'-entire-stage-omitted.json.xz')).is_file()
    assert not(out/('passive-'+stage+'-must-not-accept.json')).exists()
for name in ['matrix-coefficient','constrained-kernel']:
    assert(out/('whole-'+name+'-modified.jsonl')).is_file()
    assert not(out/(name+'-must-not-accept.json')).exists()
assert not(out/'character-scalar-must-not-accept.json').exists()
names=['timing-only','missing-record-class','changed-counter','changed-relation','changed-kernel','missing-rank-call','changed-character-scalar','unexpected-verdict-field','unbound-linked-hash']
controls=read(out/'whole-historical-controls/whole-control-bundles.json')['complete_controls']
assert[row['name']for row in controls]==names
for control in controls:
    assert control['expected_exit']==(0 if control['name']=='timing-only'else 1)
    assert len(control['all_whole_files'])==10
    for row in control['all_whole_files']:
        p=Path(row['path']);assert p.is_relative_to(out/'whole-historical-controls')
        assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
    accepted=out/(control['name']+'-historical-accepted.json')
    assert accepted.is_file()if control['name']=='timing-only'else not accepted.exists()
assert re.search(r'^test result: ok\. 13 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;', (out/'comparator-original-hash-library-tests.txt').read_text(),re.M)
# These are exact log/declaration bindings, not a new numerical proof.
claims=(ci/'kernel-statement-bindings-01.txt').read_text().splitlines();assert len(claims)==len(set(claims))==9
roots=[]
for name in claims:
    claim=read(repo/'pcc/claims'/(name+'.json'));verdict=read(out/('kernel-binding-'+name+'.txt'))
    canonical=json.dumps({k:v for k,v in claim.items()if k!='standing'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    assert verdict['claim_sha256']==hashlib.sha256(canonical).hexdigest()and verdict['verdict']=='pass'
    assert verdict['commit']==(out/'consumer-head.txt').read_text().strip()and all(p['verdict']=='pass'for p in verdict['proofs'])
    found=[p['theorem']for p in claim['proofs']if p.get('kind')=='lean'];assert len(found)==1;roots+=found
assert len(set(roots))==9
want=(ci/'kernel-declarations-01.txt').read_text().splitlines();assert len(want)==len(set(want))==27 and set(roots)<=set(want)
for side in ['consumer','producer']:
    logs=list((out/(side+'-kernel-proofs')).rglob('audit.log'));statuses=list((out/(side+'-kernel-proofs')).rglob('status'))
    assert len(logs)==len(statuses)==1 and statuses[0].read_text().strip()=='PASS'
    text=logs[0].read_text();assert re.search(r'audited 27 theorems in .*; 0 failing, 0 trusted \(native_decide\)',text)
    actual_names=re.findall(r'^ok\s+(\S+)',text,re.M);assert len(actual_names)==len(set(actual_names))==27 and set(actual_names)==set(want)
assert(study/'original-relation-rank-01/lean/RelationKernel.lean').read_bytes()==(out/'actual-kernel-proof-stage/RelationKernel.lean').read_bytes()
bundle=out/'whole-fresh-bundle'
files=[bundle/n for n in ['passive-whole100-native.json','passive-whole60-trace.json','relation-whole60-certificates.jsonl','relation-whole60-verdict.json','source-character-whole60-witnesses.jsonl','source-character-whole60-verdict.json','passive-acceptance.json','original-baseline.json','native.txt','journal.jsonl']]
assert(out/'passive-whole100-same-run-compared.json').read_bytes()==(bundle/'passive-whole100-native.json').read_bytes()
# This receipt deliberately does not synthesize mathematical result numbers.
receipt=dict(completed_prefix_phase_process_exits_and_tee_exits_match_frozen_plan=True,all_captured_compiled_runtime_source_and_original_prepared_file_bytes_equal=True,entire_fresh_input_files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))for p in files],exact_nine_local_statement_bindings=claims,actual27_declaration_names_per_original_gate=want,whole_controls_actual_files_and_no_negative_outputs_checked=True,remaining_caller_obligations=['this validator process exit0 recorded in phases and pipe-exits','final-published-source-guards phase0','finish final-source-guards.exit0','original.exit0','entire ordered phase-plan equality'],scope='unsigned operational process/file/proof-log custody only; all mathematics is checked by unchanged native Rust and original Lean gates, and a complete run still needs the listed future caller exits')
(out/'whole-operational-custody-before-final-exits.json').write_text(json.dumps(receipt,indent=2)+'\n')
