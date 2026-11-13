from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-reference';scratch=Path('/workspace/scratch');base='c0b8c791ec35577bbae4af5cbcbc7ed34d2ee8a7'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
scope=['experiments/chained-transfer-reference','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-12.md','docs/session-logs/2026-11-13.md','.github/workflows/chained-transfer-reference.yml']
def paths():
 a=set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))
 a|=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'));a.discard(b'');return sorted(a)
def owned(p):return p=='.resume/RESUME.md' or any(p==x or p.startswith(x+'/') for x in scope)
o=s/'evidence/prime-norm-governance-01';o.mkdir()
claims=[p for p in paths() if p.startswith(b'pcc/claims/')];subjects=[]
for p in claims:
 cl=json.loads((r/p.decode()).read_text())
 for proof in cl.get('proofs',[]):
  if proof.get('kind')=='attestation':
   x=proof['subject'];f=r/x['path'];assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==x['sha256'],(p,x);subjects.append(x['path'])
(o/'pinned-subjects.json').write_text(json.dumps(dict(new_claims=len(claims),attestation_subjects=len(subjects),present_hash_match=True,paths=sorted(set(subjects))),indent=2)+'\n')
for label,cmd in [('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]),('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode() for p in paths() if p.endswith(b'.md')]]),('working-diff',['git','diff','--check'])]:
 run=subprocess.run(cmd,cwd=r,capture_output=True);(o/(label+'.log')).write_bytes(run.stdout+run.stderr);(o/(label+'.exit')).write_text(str(run.returncode)+'\n');print(label,run.returncode,(run.stdout+run.stderr).decode(errors='replace')[:1000],flush=True);assert run.returncode==0
before=json.loads((scratch/'ct53-prime-tests-01/before.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in before.items())
retention=json.loads((scratch/'ct53-old-inputs-and-jobs.json').read_text());assert retention['old_input_files']==35 and not retention['changed']
old=subprocess.check_output(['git','show',base+':.github/workflows/chained-transfer-reference.yml'],cwd=r);assert (r/'.github/workflows/chained-transfer-reference.yml').read_bytes().startswith(old)
assert not subprocess.check_output(['git','diff','--name-only',base,'--','benchmarks'],cwd=r)
for f in [s/'norm-checker/engine/Cargo.toml',s/'norm-checker/Cargo.toml',s/'norm-checker/Cargo.lock']:assert f.is_file()
def stage():
 ps=paths();assert all(owned(p.decode()) for p in ps);assert not any(b'/target/' in p or p.endswith(b'.olean') for p in ps)
 manifest=scratch/'ct53-prime-stage.bin';manifest.write_bytes(b'\0'.join(ps)+b'\0')
 subprocess.run(['git','add','--pathspec-from-file='+str(manifest),'--pathspec-file-nul'],cwd=r,check=True)
 # First consumer resume is ignored;only this precise owned file is added.
 subprocess.run(['git','add','-f','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)|{b'.resume/RESUME.md'}
 for subject in set(subjects):
  if subprocess.run(['git','cat-file','-e',base+':'+subject],cwd=r,capture_output=True).returncode!=0:assert subject.encode() in selected,subject
 return selected
selected=stage()
run=subprocess.run(['git','diff','--cached','--check'],cwd=r,capture_output=True);(o/'cached-diff.log').write_bytes(run.stdout+run.stderr);(o/'cached-diff.exit').write_text(str(run.returncode)+'\n');assert run.returncode==0,(run.stdout+run.stderr).decode()
tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run=subprocess.run(['python3','tools/artifacts/artifacts.py','check',base,tree],cwd=r,capture_output=True);(o/'artifact.log').write_bytes(run.stdout+run.stderr);(o/'artifact.exit').write_text(str(run.returncode)+'\n');print('artifact',run.returncode,(run.stdout+run.stderr).decode(errors='replace')[:1000],flush=True);assert run.returncode==0
meta=dict(base=base,own_ledger_prefix=True,prose_exit=0,working_cached_whitespace_exit=0,selected_artifact_exit=0,source_inputs_current_unchanged=194,old_inputs_unchanged=35,four_whole_jobs_prefix_unchanged=True,new_fifth_job_additive=True,new_subjects_hash_match=True,benchmark_paths_changed=False,prior_broad_benchrec='ad2383sixteenoldarchivegapsunchanged/NOTgreen;notrerununchanged',unit_native='204440',lean='380d2b11exactboundlocalpasses0trusted',cli='fdd13236boundedfibres+newIDC',report='6c3a4e3pages55807allinspected',pending='strictadmission/full55minreplay/own5jobCI/actual506588rawS3publication',scope='localcorrectnessunitcheckpoint;notfullintegrationacceptance/scientificsignature')
(o/'custody.json').write_text(json.dumps(meta,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Unsigned prime-norm unit checkpointgovernance:ownc0b8ledgerprefix/prose0/workingcachedwhitespace0/selectedartifactcheck0/all194currentinputhashesunchanged/all35oldsourcescheckpins/fourwholeCIjobprefixunchanged/fifthadditive/allnewattestationsubjectshashmatch+stagingcoverage/no benchmarkpaths. Acceptedlocalunits204440/Lean380d2b/CLIfdd132/report6c3a4e all3pagesinspected. Fullreplay/admissioncontrols/own5jobCI/actual506588rawpublicationpendingexplicit;selectedartifactgreen doesNOTassertremoteavailability. Priorad2383sixteenoldarchivegapsunchangedNOTgreen.']
for f in sorted(o.iterdir()):cmd+=['--proof','attestation:'+str(f.relative_to(r))]
cl=subprocess.run(cmd,cwd=r,text=True,capture_output=True,check=True).stdout.strip();(scratch/'ct53-prime-governance.claim').write_text(cl+'\n');print(cl,flush=True)
with (r/'docs/session-logs/2026-11-13.md').open('a') as f:f.write(f'''\n## {datetime.now(timezone.utc).isoformat()} — scoped unit checkpoint governance terminal (Codex)\n\n### What was done (commands, files, features)\n- {cl}:ownc0b8ledgerprefix/prose0/workingcachedwhitespace0/selectedartifact0/all194currentinputhashesunchanged/all35oldinputs/fourwholejobsunchanged/fifthadditive/pinnedsubjecthash+stagecoverage pass. Native204440/Lean380d2b/CLIfdd132/report6c3a4e complete local only. [pcc:unverified]\n\n### Decisions made (and why)\n- Normal scopedcommit now makes newdriverinputsclean;publishreadychildunder1517 andrunadmission/fullreplay next. Selectedartifactcheck doesnotclaimremote506588archiveavailability. Priorad2383sixteenoldgapsunchangedNOTgreen;no benchmarkpaths changed.\n\n### Open threads (unfinished, pick up next time)\n- Exactobjectpublication/readyPR/new5jobCI/currentGitHubqueue/rootCI00:29;admissioncontrols/full55minreplay/rawmigration/replayaddendum/nextfullF101C0↔T20adapter.\n\n### Errors (what went wrong, how it was handled)\n- Firststaticmanifestfail01 retained7f58bd;S3checkpointtransportgapnotwaived. Allnewresults unsigned;no costclaim/historyrewrite/subagent.\n''')
selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True)
subprocess.run(['git','commit','--quiet','-m','research: independently check T20 prime-field norms and completed pullback'],cwd=r,check=True)
print(subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
