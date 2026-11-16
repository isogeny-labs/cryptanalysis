"""Version strict Rust CI audit; preserve every prior comparison and mask."""
from pathlib import Path
import json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';old=Path('/workspace/scratch/ct73-cc69-CI-audit-01');o=Path('/workspace/scratch/ct74-norm-halving-CI-audit-01');o.mkdir();ci=Path('/workspace/scratch/ct74-norm-halving-own-CI-01');source='5ac59843a0cc6546b0f007c0bd2f79212d169c43'
for name in ['canonical-digests73.json','all-original-goldens-plus-complete.json']:shutil.copyfile(old/name,o/name)
for p in old.glob('*-reference.sha256'):shutil.copyfile(p,o/p.name)
for p in old.glob('*-original-proof-source'):shutil.copytree(p,o/p.name)
canonical=json.loads((o/'canonical-digests73.json').read_text());verdicts=json.loads((s/'evidence/norm-halving-bindings-01/local-verdicts.json').read_text());assert len(verdicts)==9
for v in verdicts:assert v['claim_id']not in canonical;canonical[v['claim_id']]=v['claim_sha256']
assert len(canonical)==82;(o/'canonical-digests82.json').write_text(json.dumps(canonical,indent=2)+'\n')
shutil.copyfile(s/'ci_norm_halving/reference-01.sha256',o/'norm-reference.sha256');shutil.copyfile(s/'norm-halving-evaluator/lean/NormHalving.lean',o/'NormHalving.lean');shutil.copyfile(s/'norm-halving-evaluator/halving-identities.certificate.json',o/'halving-identities.certificate.json')
# Whole map is the actual Rust-frozen fixture; Python only copies bytes.
shutil.copyfile('/workspace/scratch/ct74-norm-halving-audit-02/expected-native-05.json',o/'norm-whole-golden.json')
source_dir=o/'checkpoint-source-inputs';source_dir.mkdir()
for line in(ci/'checkpoint-artifact-members/source-inputs.sha256').read_text().splitlines():
 h,p=line.split('  ',1);dst=source_dir/p;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(subprocess.check_output(['git','show',source+':'+p],cwd=r))
crate=o/'audit-cli';(crate/'src').mkdir(parents=True)
for name in ['Cargo.toml','Cargo.lock']:shutil.copyfile(old/'audit-cli'/name,crate/name)
shutil.copyfile(old/'audit-cli/src/original_sha256.rs',crate/'src/original_sha256.rs')
code=(old/'audit-cli/src/main.rs').read_text().replace('cc69f16d083cdce88813a7c3379e839e8454e063',source).replace('canonical-digests73.json','canonical-digests82.json')
changes=[('digests.as_object().unwrap().len(),73','digests.as_object().unwrap().len(),82'),('("beta-complete","complete")','("beta-complete","complete"),("norm-halving","norm-halving")'),('distinct.len(),20','distinct.len(),21'),('success,21','success,22'),('sum::<usize>(),419','sum::<usize>(),423'),('verdicts.len(),75','verdicts.len(),84'),('reuse.len(),73','reuse.len(),82')]
for a,b in changes:assert a in code,a;code=code.replace(a,b)
needle='assert_eq!(canonical(rows.clone()),canonical(golden[*label].as_array().unwrap().clone()),"whole native JSON mismatch {label}");'
assert needle in code
code=code.replace(needle,'''let expected=if *label=="norm-halving"{load(a.join("norm-whole-golden.json")).as_object().unwrap().iter().map(|(kind,data)|json!({"kind":kind,"data":data})).collect::<Vec<_>>()}else{golden[*label].as_array().unwrap().clone()};assert_eq!(canonical(rows.clone()),canonical(expected),"whole native JSON mismatch {label}");''')
insert=code.index('let out=json!(')
extra=r'''
let n=p.join("norm-halving-artifact-members");
assert_eq!(fs::read_to_string(n.join("consumer-head.txt")).unwrap(),"5ac59843a0cc6546b0f007c0bd2f79212d169c43\n");
assert_eq!(fs::read_to_string(n.join("producer-head.txt")).unwrap(),"3d49af7f3d0a28e76b79e4825c9d2324e85853d2\n");
let mut phases:Vec<(String,i32)>=[("fetch",0),("compile",0),("native",0),("bins",0),("compare",0),("compare-negative",101),("identity-issue",0),("identity-replay",0),("identity-negative",101),("consumer-proof",0),("producer-proof",0)].iter().map(|(s,n)|(s.to_string(),*n)).collect();
for claim in["7cfb9f","0e81c2","03c69b","4127df","3aea5b","e582c4","442f34","22b021","508ce1"]{phases.push((format!("binding-PCC-20261114-{claim}"),0));}phases.push(("final-guards".into(),0));assert_eq!(phases.len(),21);
assert_eq!(fs::read_to_string(n.join("phases.txt")).unwrap(),phases.iter().map(|(name,e)|format!("{name} {e} {e}\n")).collect::<String>());
for(name,e)in &phases{assert_eq!(fs::read_to_string(n.join(format!("{name}.pipe-exits"))).unwrap(),format!("{e} 0\n"));}
for name in["original","phase-caller","final-source-guards"]{assert_eq!(fs::read_to_string(n.join(format!("{name}.exit"))).unwrap(),"0\n");}
assert!(fs::read_to_string(n.join("native.txt")).unwrap().contains("test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;"));
for side in["consumer","producer"]{let log=fs::read_to_string(n.join(format!("{side}-proof.txt"))).unwrap();assert!(log.contains("10 thm   0 trusted"));assert!(!log.contains("sorryAx"));}
let guard=fs::read_to_string(n.join("final-source-guards.txt")).unwrap();assert_eq!(guard.lines().count(),929);assert!(guard.lines().all(|x|x.ends_with(": OK")));
assert_eq!(fs::read(n.join("original-reference.sha256")).unwrap(),fs::read(a.join("norm-reference.sha256")).unwrap());
assert_eq!(fs::read(n.join("producer-staged-source/NormHalving.lean")).unwrap(),fs::read(a.join("NormHalving.lean")).unwrap());
assert_eq!(load(n.join("all-native-records.json")),load(a.join("norm-whole-golden.json")));
assert_eq!(fs::read(n.join("identity.json")).unwrap(),fs::read(a.join("halving-identities.certificate.json")).unwrap());
assert!(fs::read_to_string(n.join("identity-negative.txt")).unwrap().contains("False(Counterexample"));
assert!(fs::read_to_string(n.join("compare-negative.txt")).unwrap().contains("whole native kind set mismatch"));assert!(!n.join("omitted-record-must-not-accept.json").exists());
let binaries=load(n.join("actual-binaries.json"));assert_eq!(binaries.as_object().unwrap().len(),3);
for name in["native-test","audit-native","halving-identity"]{let m=&binaries[name];let raw=fs::read(n.join(format!("{name}.bin"))).unwrap();assert_eq!(m["sha256"],hex(&raw));assert_eq!(m["bytes"].as_u64().unwrap(),raw.len()as u64);assert_eq!(m["built_path"],m["executed_path"]);}
assert_eq!(binaries["native-test"]["Cargo_compile_runtime_paths_equal"],true);
let extract_path=|text:&str,needle:&str|{let line=text.lines().find(|l|l.contains(needle)).unwrap();let start=line.find(needle).unwrap()+needle.len();line[start..].strip_suffix(')').unwrap().to_string()};
let compiled=extract_path(&fs::read_to_string(n.join("compile.txt")).unwrap(),"Executable unittests src/lib.rs (");let executed=extract_path(&fs::read_to_string(n.join("native.txt")).unwrap(),"Running unittests src/lib.rs (");assert_eq!(compiled,executed);assert_eq!(binaries["native-test"]["built_path"],compiled);
'''
code=code[:insert]+extra+code[insert:]
# Correct only the versioned output inventory; all old native and census comparisons remain.
for a,b in [('"distinct_workflows":20','"distinct_workflows":21'),('"successful_runs":21','"successful_runs":22'),('"whole_native_records":419','"whole_native_records":423'),('"canonical_original_PCC_digests":73','"canonical_original_PCC_digests":82'),('"actual_pass_verdicts":75','"actual_pass_verdicts":84'),('all75-current-verdicts.json','all84-current-verdicts.json'),('20distinctworkflows/21automaticruns','21distinctworkflows/22automaticruns'),('ALL419 native','ALL423 native'),('73canonical/75passverdicts','82canonical/84passverdicts'),('20distinctworkflows21automaticSUCCESSruns','21distinctworkflows22automaticSUCCESSruns')]:code=code.replace(a,b)
code=code.replace('"all_final_guards_and_source_manifests_exact":true','"norm21phases_four_unfiltered_four_wholeJSON_without_masks_two10gates9bindings_twoactual101_all929guards_three_actual_binaries_exact":true,"all_final_guards_and_source_manifests_exact":true')
(crate/'src/main.rs').write_text(code);shutil.copyfile(__file__,o/'prepare.py');print('strict additive audit prepared:423whole plus7113census/82canonical84verdicts/22runs/5wholeZIPs')
