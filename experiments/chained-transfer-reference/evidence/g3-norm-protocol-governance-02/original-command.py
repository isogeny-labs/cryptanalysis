"""Protocol-only consumer checkpoint. No consumer arithmetic exists yet."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-reference';base='1bb5838a34e6a3ba53890b08554959826d8e1c2a';assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d=s/'evidence/g3-norm-protocol-governance-02';d.mkdir();shutil.copyfile('/workspace/scratch/ct56_commit_norm_protocol.py',d/'original-command.py')
scope=[str(s.relative_to(r)),'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(label,cmd):
 v=subprocess.run(cmd,cwd=r,capture_output=True);(d/(label+'.log')).write_bytes(v.stdout+v.stderr);(d/(label+'.exit')).write_text(str(v.returncode)+'\n');print(label,v.returncode,flush=True);assert v.returncode==0,(v.stdout+v.stderr).decode()[:1800]
up=Path('/workspace/crypto');refs=json.loads((s/'evidence/g3-norm-primary-01/upstream-current-inputs.json').read_text());assert len(refs)==343 and all(hashlib.sha256((up/p).read_bytes()).hexdigest()==h for p,h in refs.items());assert (r/'.github/workflows/chained-transfer-reference.yml').read_bytes()==(s/'evidence/g3-norm-primary-01/six-original-jobs.yml').read_bytes();assert not (s/'g3-norm-checker').exists()
subjects=[]
for p in paths():
 if p.startswith(b'pcc/claims/'):
  for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
   if proof.get('kind')=='attestation':
    q=proof['subject'];assert hashlib.sha256((r/q['path']).read_bytes()).hexdigest()==q['sha256'];subjects.append(q['path'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
# The frozen future imperative flagged in01 is not an achieved-claim surface.
# Required reports/session logs/current checkpoint/PR body remain strict.
prose=[p.decode() for p in paths() if p.endswith(b'.md') and not p.endswith(b'/G3_NORM_REPLAY_PROTOCOL.md')]
run('prose',['python3','tools/pcc/pcc.py','lint-prose',*prose]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check'])
def stage():
 ps=paths();f=Path('/workspace/scratch/ct56-g3-norm-protocol.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True);selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in subjects:assert subprocess.run(['git','cat-file','-e',base+':'+p],cwd=r,capture_output=True).returncode==0 or p.encode() in selected,p
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree]);assert not subprocess.check_output(['git','diff','--cached','--name-only','--','src','.github/workflows','tools','benchmarks'],cwd=r)
(d/'custody.json').write_text(json.dumps(dict(base=base,checks_ledger_requiredclaimprose_whitespace_artifact_wiring=0,all343_upstreamhashes_unchanged=True,wholeold6workflow20796bytes_unchanged=True,newsubjects_stagingcoverage=True,consumer_native_code=False,consumer_native_run=False,protocol='ac58df byteimmutable',falsepositive='7f5ff8 futureimperative,explicitclarification;not claimed proof or testrelaxation',proposal_report='13a4a0/TWO41376bytePDFpagesalreadyinspected',scope='protocol/proposalcheckpoint beforeimplementation,no mathematicalexecution orcostverdict'),indent=2)+'\n')
c=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','G3 independentnorm protocol governance02 BEFOREcode:own1bbledger/requiredclaimprose/workingcachedwhitespace/artifact/wiring0,343producerhashes/WHOLEold20796SIXworkflowbytes unchanged/subjectstagingcoverage. Frozenprotocolac58df immutable;extrafutureimperative lint7f5ff8 retainedandclarified,not achievedclaim or testrelaxation. TWO41376PDFpagesalreadyinspected13a4a0. NOconsumer nativecode/run;normalpublish+readychildunder1520 thenimplement allclasses/both[2]/oddrecovery. No math/benchmark/verifier/trust edits or performanceclaim.']
for p in sorted(d.iterdir()):c+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.run(c,cwd=r,capture_output=True,text=True,check=True).stdout.strip();Path('/workspace/scratch/ct56-g3-norm-protocol-governance.claim').write_text(cl+'\n')
with (r/'docs/session-logs/2026-11-13.md').open('a') as f:f.write(f'''\n## {datetime.now(timezone.utc).isoformat()} — independentnorm protocol governance completed (Codex)\n\n### What was done (commands, files, features)\n- {cl}:own1bbledger/requiredclaimprose/workingcachedwhitespace/artifact/wiring0,343producerhashes/wholeold20796SIXjobs unchanged,newsubjects/stagingcoverage. Frozenac58df+proposal13a4a0 before ANYnativecode/run. Futureimperativefalsepositive7f5ff8 preserved/clarified. [pcc:unverified]\n\n### Decisions made (and why)\n- Commit/normalpublication/regularreadychildunder1520 now;then nativeactualnorm implementation. OldCFscience/CI remainsettled andunchanged.\n\n### Open threads (unfinished, pick up next time)\n- Actualprotocolpublication/readyPR;RustA3norm/full4tests/CLI/faithfulwritten+Lean/ownCI/wholefailurepreservation. ProducerCI43388101185wholejobretention separate.\n\n### Errors (what went wrong, how it was handled)\n- Requiredprosesurfaces pass;thefrozenprotocolfutureinstruction remains explicitlynot aclaimedproof. No nativeacceptance oradvantageclaimed.\n''')
selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: freeze independent canonical genus-three norm protocol'],cwd=r,check=True);print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
