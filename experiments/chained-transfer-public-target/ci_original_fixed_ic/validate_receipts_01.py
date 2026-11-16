"""Check complete literal evidence receipts; Rust and Lean perform all mathematics."""
from pathlib import Path
import hashlib,json,re,sys
repo,out=map(Path,sys.argv[1:3]);study=repo/'experiments/chained-transfer-public-target';ci=study/'ci_original_fixed_ic'
def read(p):return json.loads(p.read_text())
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
expected=read(ci/'phases-01.json')['ordered_phases']
actual=[line.split()for line in(out/'phases.txt').read_text().splitlines()]
# This validator is itself the penultimate phase. A replay of the completed
# output may include its own recorded exit and the final source-guard phase.
prefix=expected[:-2]
assert len(actual)in[len(prefix),len(expected)-1,len(expected)]
assert actual==[[v['name'],str(v['expected_exit']),str(v['expected_exit'])]for v in expected[:len(actual)]]
for row in expected[:len(actual)]:
    assert(out/(row['name']+'.pipe-exits')).read_text().split()==[str(row['expected_exit']),'0']
prepared=read(out/'engine-prepared.json');assert len(prepared['files'])==2
prepared_by_suffix={}
for row in prepared['files']:
    p=out/'actual-prepared-original-engine'/Path(row['copy']).name
    assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']
    suffix=Path(row['actual_path']).suffix;assert suffix not in prepared_by_suffix;prepared_by_suffix[suffix]=row
assert set(prepared_by_suffix)=={'.rlib','.rmeta'}
whole=[]
for label,package,count,tags in [('original-ic','original-fixed-model-ic-01',100,7),('original-sampler','original-fixed-model-sampler-01',101,8)]:
    compiled=read(out/(label+'-compiled-binary.json'));runtime=read(out/(label+'-runtime-binary.json'))
    a=out/(label+'-original-compiled-test.bin');b=out/(label+'-actual-runtime-test.bin')
    assert a.read_bytes()==b.read_bytes()and sha(a)==compiled['sha256']==runtime['sha256']
    assert compiled['actual_path']==runtime['actual_path']and runtime['compiled_runtime_equal']is True
    assert runtime['actual_Cargo_artifact']==compiled['actual_Cargo_artifact']
    a=out/('actual-compiled-'+label+'-auditor.bin');b=out/('actual-runtime-'+label+'-auditor.bin')
    compiled_auditor=read(out/(label+'-auditor-compiled-custody.json'));runtime_auditor=read(out/(label+'-auditor-runtime-custody.json'))
    assert a.read_bytes()==b.read_bytes()and sha(a)==compiled_auditor['sha256']==runtime_auditor['sha256']
    assert compiled_auditor['actual_path']==runtime_auditor['actual_path']and runtime_auditor['whole_compiled_runtime_equal']is True
    assert(out/(label+'-whole-frozen.json')).read_bytes()==(out/(label+'-all-whole-records.json')).read_bytes()
    historical=read(out/(label+'-historical-equality.json'))
    assert historical['all_non_time_values_equal']is True and historical['all_counters_and_non_time_statistics_compared_exactly']is True
    assert historical['historical_whole_sha256']==sha(out/(label+'-expected.json'))and historical['fresh_whole_sha256']==sha(out/(label+'-whole-frozen.json'))
    for control in ['missing-record-class','changed-scalar','changed-counter','unexpected-report-field']:
        assert(out/(label+'-historical-controls')/(control+'.json')).is_file()
        assert not(out/(label+'-'+control+'-historical-accepted.json')).exists()
    assert(out/(label+'-timing-only-historical-accepted.json')).is_file()
    before=read(out/('engine-reused-'+label+'-before-native.json'));after=read(out/('engine-reused-'+label+'.json'))
    assert before==after and after['actual_reuse']is True and after['actual_prepared_bytes_unchanged']is True
    assert len(after['actual_aliases'])==2
    for row in after['actual_aliases']:
        ref=prepared_by_suffix[Path(row['dependency_path']).suffix]
        assert row['sha256']==ref['sha256']and row['bytes']==ref['bytes']and row['whole_before_and_after_bytes_equal']is True
    closure=read(out/('engine-closure-'+label+'.json'));assert closure['exact_complete_closure']is not None
    omissions=read(out/(label+'-whole-omission-custody.json'));assert len(omissions['whole_controls'])==tags
    for row in omissions['whole_controls']:
        assert row['every_retained_line_byte_equal']is True
        assert not(out/(label+'-'+row['tag']+'-must-not-accept.json')).exists()
    source=study/package;snapshot=out/'actual-compiled-source'/package
    selected=[source/'Cargo.toml',source/'Cargo.lock']+sorted((source/'src').rglob('*.rs'))+sorted((source/'derived').rglob('*.rs'))
    for p in selected:assert p.read_bytes()==(snapshot/p.relative_to(source)).read_bytes()
    # Full record populations and their mathematics were accepted by the actual
    # unchanged Rust --compare process; this receipt checks its complete bytes.
    whole.append(dict(label=label,historical_whole_records=count,whole_compared_sha256=sha(out/(label+'-all-whole-records.json')),test_sha256=runtime['sha256'],auditor_sha256=runtime_auditor['sha256'],whole_class_omissions=tags))
compiled=read(out/'historical-auditor-compiled-custody.json');runtime=read(out/'historical-auditor-runtime-custody.json')
assert(out/'actual-compiled-historical-auditor.bin').read_bytes()==(out/'actual-runtime-historical-auditor.bin').read_bytes()
assert sha(out/'actual-compiled-historical-auditor.bin')==compiled['sha256']==runtime['sha256']and runtime['whole_compiled_runtime_equal']is True
assert compiled['actual_path']==runtime['actual_path']
for p in (ci/'audit').rglob('*'):
    if p.is_file():assert p.read_bytes()==(out/'actual-compiled-source/historical-auditor'/p.relative_to(ci/'audit')).read_bytes()
claims=(ci/'statement-bindings-01.txt').read_text().splitlines();assert len(claims)==len(set(claims))==5
theorems=[];bindings=[]
for name in claims:
    claim=read(repo/'pcc/claims'/(name+'.json'));verdict=read(out/('binding-'+name+'.txt'))
    canonical=json.dumps({k:v for k,v in claim.items()if k!='standing'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    assert verdict['claim_sha256']==hashlib.sha256(canonical).hexdigest()and verdict['verdict']=='pass'
    assert verdict['commit']==(out/'consumer-head.txt').read_text().strip()and all(v['verdict']=='pass'for v in verdict['proofs'])
    roots=[p['theorem']for p in claim['proofs']if p.get('kind')=='lean'];assert len(roots)==1;theorems+=roots;bindings.append(name)
for side in ['consumer','producer']:
    logs=list((out/(side+'-proofs')).rglob('audit.log'));statuses=list((out/(side+'-proofs')).rglob('status'));assert len(logs)==len(statuses)==2
    assert all(p.read_text().strip()=='PASS'for p in statuses)
    declarations=[]
    for p in logs:
        text=p.read_text();assert re.search(r'audited [23] theorems in .*; 0 failing, 0 trusted \(native_decide\)',text)
        declarations+=re.findall(r'^ok\s+(\S+)',text,re.M)
    assert len(declarations)==len(set(declarations))==5 and set(declarations)==set(theorems)
for module in ['NewTargetIC','NormAssistedSampling']:
    package='new-target-ic'if module=='NewTargetIC'else'norm-assisted-ic'
    assert(study/package/'lean'/(module+'.lean')).read_bytes()==(out/'actual-proof-stage'/(module+'.lean')).read_bytes()
induced=out/'induced-full-transfer-proof';assert(induced/'original.exit').read_text().strip()=='0'
coverage=read(induced/'whole-proof-coverage-and-bindings.json');assert len(coverage['gates'])==2 and len(coverage['all_nine_exact_bindings'])==9
for gate in coverage['gates']:assert len(gate['actual_declarations'])==21 and gate['failing']==gate['trusted']==0
(out/'complete-whole-population-and-custody.json').write_text(json.dumps(dict(whole_populations=whole,exact_old_five_theorem_bindings=bindings,induced_declarations_per_original_gate=21,induced_named_bindings=9,total_declarations_per_original_gate=26,required_scientific_prefix_phases=len(prefix),complete_driver_phases=len(expected),completion_requirement='The caller must separately require original.exit0, final-source-guards.exit0 and the entire ordered phase list; this validator runs before its own exit is recorded.',scope='unsigned exact correctness/proof/byte replay; timings and partial counters are retained unpriced; original actual-model/program and complete-cost bridges unchanged'),indent=2)+'\n')
