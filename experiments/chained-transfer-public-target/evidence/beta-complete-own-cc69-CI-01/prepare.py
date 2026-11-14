"""Copy unchanged references and adapt strict Rust audit to corrected own-head CI."""
from pathlib import Path
import json,shutil,subprocess
old=Path('/workspace/scratch/ct73-b691-CI-audit-02');o=Path('/workspace/scratch/ct73-cc69-CI-audit-01');o.mkdir();ci=Path('/workspace/scratch/ct73-cc69-own-CI-01');r=Path('/workspace/cryptanalysis')
for p in old.glob('*.json'):
 if p.name not in {'audit-result.json','all75-current-verdicts.json','correction.json'}:shutil.copyfile(p,o/p.name)
for p in old.glob('*-reference.sha256'):shutil.copyfile(p,o/p.name)
for p in old.glob('*-original-proof-source'):shutil.copytree(p,o/p.name)
crate=o/'audit-cli';(crate/'src').mkdir(parents=True)
for n in ['Cargo.toml','Cargo.lock']:shutil.copyfile(old/'audit-cli'/n,crate/n)
shutil.copyfile(old/'audit-cli/src/original_sha256.rs',crate/'src/original_sha256.rs')
source=o/'checkpoint-source-inputs';source.mkdir()
for line in(ci/'checkpoint-artifact-members/source-inputs.sha256').read_text().splitlines():
 h,p=line.split('  ',1);dest=source/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(subprocess.check_output(['git','show','cc69f16d083cdce88813a7c3379e839e8454e063:'+p],cwd=r))
code=(old/'audit-cli/src/main.rs').read_text().replace('b691714c8c6f7b157f9ec832ccc91413c624c541','cc69f16d083cdce88813a7c3379e839e8454e063')
changes=[('let mut expected_failure=0;','let mut pcc_gates=0;'),('assert_eq!(item["run"]["conclusion"],if item["run"]["name"]=="pcc-gate"{"failure"}else{"success"});','assert_eq!(item["run"]["conclusion"],"success");'),('let is_expected_failure=job["name"]=="gate";assert_eq!(job["conclusion"],if is_expected_failure{"failure"}else{"success"});','let is_PCC=job["name"]=="gate";assert_eq!(job["conclusion"],"success");'),('assert_eq!(success,19)','assert_eq!(success,21)'),('assert_eq!(skipped,1)','assert_eq!(skipped,2)'),('assert_eq!(expected_failure,1)','assert_eq!(pcc_gates,2)')]
for a,b in changes:assert a in code,a;code=code.replace(a,b)
start=code.index('if is_expected_failure {');end=code.index('success+=1;',start)
code=code[:start]+'''if is_PCC {let failures:Vec<_>=log.lines().filter_map(|line|line.split_once(' ').map(|x|x.1)).filter(|line|line.starts_with("PCC-")&&line.ends_with(": fail")).collect();assert!(failures.is_empty());for claim in["f4a048","423f66","8397ab"]{assert_eq!(log.matches(&format!("PCC-20261114-{claim}: not_covered")).count(),1);}pcc_gates+=1;}'''+code[end:]
code=code.replace('"successful_runs":19,"failed_PCC_runs":1,"PCC_sign_jobs_skipped":1','"successful_runs":21,"failed_PCC_runs":0,"PCC_sign_jobs_skipped":2')
code=code.replace('"expected_failure_exact":"f4a048 missing original report PNG in original docs-only hydration; preserved without suppression"','"PCC_repair":"both automatic synchronize and body-edited gates success; f4a048/423f66/8397ab allnotcovered without failure; original b691 negative remains separate"')
code=code.replace('"scope":"unsigned data audit; overall CI failed as recorded; no signed execution or performance standing"','"scope":"unsigned data audit;20distinctworkflows/21automaticruns successful; no signed execution or performance standing"')
code=code.replace('20workflows19success+EXACToneexpectedPCCfailure','20distinctworkflows21automaticSUCCESSruns/twoPCCsignskips')
(crate/'src/main.rs').write_text(code);shutil.copyfile(__file__,o/'prepare.py');print('strict corrected-head Rust audit prepared')
