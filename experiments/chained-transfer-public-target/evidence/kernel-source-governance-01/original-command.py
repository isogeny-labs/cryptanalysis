"""Owned checkpoint using unchanged repository governance tools."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib,lzma,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='85b799ec5d7f3a8e81168af11fbf4ba36007be28'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d=s/'evidence/kernel-source-governance-01';d.mkdir();shutil.copyfile(__file__,d/'original-command.py')
scope=[str(s.relative_to(r)),'.github/workflows/chained-transfer-kernels.yml','pcc/claims','pcc/ledger.jsonl','problems/chained-transfer-public-target-destination-bridge.md','problems/chained-transfer-geometric-two-torsion.md','problems/chained-transfer-primefield-polarized-two-kernel.md','problems/README.md','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
 p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr
 if len(raw)>60000:(d/(name+'.txt.xz')).write_bytes(lzma.compress(raw))
 else:(d/(name+'.txt')).write_bytes(raw)
 (d/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw.decode(errors='replace')[:1800]
guard=json.loads(Path('/workspace/scratch/ct59-kernel-replay-native-01/before.json').read_text());assert len(guard)==2366 and all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guard.items())
protected=['tools','suite','.github/workflows','experiments/chained-transfer-reference']+[str((s/name).relative_to(r)) for name in ['native','v2','rho-accessor','prime-field','completed-descent','ci_v2','ci_completed','ci_two_primary','two-primary','ci_bitangents','bitangents','PROTOCOL-01.md','COMPLETED_DESCENT_PROTOCOL_02.md','V2_MAPS_01.md','DERIVATION.md','PROOF_MAP.md','README.md']]
assert not subprocess.check_output(['git','diff','--name-only',base,'--',*protected],cwd=r)
for label,path in [('parent437','experiments/chained-transfer-reference/g3-norm-reference-01.sha256'),('P1434',str((s/'reference-02.sha256').relative_to(r))),('V2468',str((s/'ci_v2/reference-01.sha256').relative_to(r))),('completed483',str((s/'ci_completed/reference-01.sha256').relative_to(r)))]:run(label,['sha256sum','--check',path])
run('old502',['sha256sum','--check',str((s/'ci_two_primary/reference-01.sha256').relative_to(r))]);run('new522',['sha256sum','--check',str((s/'ci_bitangents/reference-01.sha256').relative_to(r))]);run('parent522',['sha256sum','--check',str((s/'ci_bitangents/reference-01.sha256').relative_to(r))]);run('new554',['sha256sum','--check',str((s/'ci_kernels/reference-01.sha256').relative_to(r))]);run('kernel-shell',['bash','-n',str(s/'ci_kernels/check.sh')]);run('kernel-actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-kernels.yml'])
run('shell',['bash','-n',str(s/'ci_bitangents/check.sh')]);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-bitangents.yml'])
run('format',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',str(s/'kernel-census/src/lib.rs'),str(s/'kernel-census/engine/src/lib.rs'),str(s/'kernel-replay/src/lib.rs')])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode() for p in paths() if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
subprocess.run(['git','add','--sparse','-f','--',str((s/'kernel-census/Cargo.lock').relative_to(r))],cwd=r,check=True)
subprocess.run(['git','add','--sparse','-f','--',str((s/'kernel-replay/Cargo.lock').relative_to(r))],cwd=r,check=True)
def stage():
 ps=paths();f=Path('/workspace/scratch/ct59-kernel-source.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0')
 subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in ps:
  if p.startswith(b'pcc/claims/'):
   for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256']
     assert x['path'].encode() in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(d/'custody.json').write_text(json.dumps(dict(base=base,all2318_native_selected_inputs_unchanged=True,all_old_reference_manifests_pass=True,original_engines_verifiers_workflows_protocols_unchanged=True,ledger_prose_whitespace_wiring_benchrec_artifact_format=0,subjects_hash_and_staging=True,native='c88589/907dfc',written_partial_formal='c2270b/5named8audited/30totallocalbindings;geometryopen',report='9ba899;three59824pages inspected',current_completed_full_CI='af9044/f9535f;50native25digests',next='ownkernelfull/CI;f1d44f differentResEgluing actualmodels/maps;newwholedatahandoff;noadvantage'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Kernel census/replay source+integration own85b:all2366runtime/inputbinaryhashes andold437/434/468/483/502/522/new554referencesunchanged;originalengines/verifiers/previousworkflows/frozenprotocols unchanged. Originalledger/prose/workingcachedwhitespace/wiring/benchrec/artifact/format/actionlint/shell0/newsubjecthashstagingcoverage. Nativec88589/907dfc ALL1451520matrices/compatible120960/commutant12/kernel1;writtenfixeddegreepolarizationobstructionc2270b/5faithfulpartialbindings8audited,bothgates;THREE59824PDFpagesALLinspected9ba899. Newgluingf1d44fPROPOSALONLY. Parentfullaf9044/CIf9535f50native25digestssettled. Own554full/CIpending, no newmap/fullformal/signedexecution/cost/generalimpossibility.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: classify actual q223 polarized two-kernels and preserve the chain obstruction'],cwd=r,check=True)
print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
