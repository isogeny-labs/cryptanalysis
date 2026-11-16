"""Checkpoint the accepted source through unchanged repository governance."""
from pathlib import Path
import subprocess,json,hashlib,lzma,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='5b459ecae1fc469bf9c3bd5fdfe26a0ac0a09d86'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d=s/'evidence/gluing-source-governance-01';d.mkdir();shutil.copyfile(__file__,d/'original-command.py')
scope=[str(s.relative_to(r)),'.github/workflows/chained-transfer-gluing.yml','pcc/claims','pcc/ledger.jsonl','problems/chained-transfer-public-target-destination-bridge.md','problems/chained-transfer-geometric-two-torsion.md','problems/chained-transfer-primefield-polarized-two-kernel.md','problems/README.md','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
 p=subprocess.run(cmd,cwd=r,capture_output=True);raw=p.stdout+p.stderr
 (d/(name+'.txt.xz'if len(raw)>60000 else name+'.txt')).write_bytes(lzma.compress(raw)if len(raw)>60000 else raw)
 (d/(name+'.exit')).write_text(str(p.returncode)+'\n');print(name,p.returncode,flush=True);assert p.returncode==0,raw.decode(errors='replace')[:2000]
guard=json.loads(Path('/workspace/scratch/ct60-gluing-maps-native-03/before.json').read_text());assert len(guard)==2401 and all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in guard.items())
protected=['tools','suite','.github/workflows','experiments/chained-transfer-reference']+[str((s/name).relative_to(r))for name in ['native','v2','rho-accessor','prime-field','completed-descent','ci_v2','ci_completed','ci_two_primary','two-primary','ci_bitangents','bitangents','kernel-census','kernel-replay','ci_kernels','PROTOCOL-01.md','COMPLETED_DESCENT_PROTOCOL_02.md','V2_MAPS_01.md','DERIVATION.md','PROOF_MAP.md','README.md','KERNEL_CENSUS_PROTOCOL_01.md','KERNEL_REPLAY_PROTOCOL_01.md','KERNEL_OBSTRUCTION_DERIVATION_01.md','GLUING_CHAIN_PROPOSAL_01.md']]
assert not subprocess.check_output(['git','diff','--name-only',base,'--',*protected],cwd=r)
for name,ref in [('parent437','experiments/chained-transfer-reference/g3-norm-reference-01.sha256'),('P1434',str((s/'reference-02.sha256').relative_to(r))),('V2468',str((s/'ci_v2/reference-01.sha256').relative_to(r))),('completed483',str((s/'ci_completed/reference-01.sha256').relative_to(r))),('two502',str((s/'ci_two_primary/reference-01.sha256').relative_to(r))),('bit522',str((s/'ci_bitangents/reference-01.sha256').relative_to(r))),('kernels554',str((s/'ci_kernels/reference-01.sha256').relative_to(r))),('gluing596',str((s/'ci_gluing/reference-01.sha256').relative_to(r)))]:run(name,['sha256sum','--check',ref])
run('shell',['bash','-n',str(s/'ci_gluing/check.sh')]);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/chained-transfer-gluing.yml'])
run('format',['/home/agent/.cargo/bin/rustfmt','--edition','2021','--config','skip_children=true','--check',*[str(s/p)for p in ['gluing-models/src/lib.rs','gluing-models/src/even.rs','gluing-maps/src/lib.rs','gluing-maps/src/adapter.rs','gluing-maps/src/norm.rs','gluing-maps/src/tests.rs']]])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode()for p in paths()if p.endswith(b'.md')]])
run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
for name in ['gluing-models','gluing-maps']:subprocess.run(['git','add','--sparse','-f','--',str((s/name/'Cargo.lock').relative_to(r))],cwd=r,check=True)
def stage():
 ps=paths();f=Path('/workspace/scratch/ct60-gluing-source.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0')
 subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
 selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in ps:
  if p.startswith(b'pcc/claims/'):
   for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
    if proof.get('kind')=='attestation':
     x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
     assert x['path'].encode()in selected or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode==0,x['path']
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
meta=dict(base=base,all2401_native_inputs_unchanged=True,all_original_reference_manifests_pass=True,new_reference=596,new_outer_self=597,old_workflows_native_sources_verifiers_frozen_protocols_unchanged=True,ledger_prose_whitespace_cached_whitespace_wiring_benchrec_artifact_format_shell_actionlint=0,all_new_subject_hashes_and_staging=True,native='f33c42/7c9bf4',written='5f7e4c',formal='11newnamedbothoriginalgates/zero trusted/41accumulatedlocalbindings;geometrypartial',report='a96d2b;THREE63028finalpagesALLinspected',previous_kernel_full_CI='b9cd55/48edee;58native30digests',preserved_failures='1e3436/ec6f14/8e56fa+originalkernelprose01/e2da08',next='normalpublishsource;597cleanfull/fouractualadmission/eightworkflows/76native41digests;wholedatahandoff;chainkernelstructure;collapseawarefurtherwalks;costadmissionopen')
(d/'custody.json').write_text(json.dumps(meta,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Alternativegluing source+ownCIintegration own5b:ALL2401nativeinputs/allold437434468483502522554/new596referencesunchanged;originalengines/verifiers/previousworkflows/frozenprotocols unchanged. Originalledger/allchangedMDprose/workingcachedwhitespace/wiring/benchrec/artifact/format/actionlint/shell0/newsubjecthashstagingcoverage. Nativef33c42all6models+7c9bf4all4completePhiNorm/both2+both4/public5/exceptionalcontrols, written5f7e4cthreeF223targetsnonisomorphictoold,11newfaithfulpartialbindingsbothgates/41total. FinalTHREE63028PDFpagesALLinspecteda96d2b. Firstcompile/field failures andintermediate02 retained. Parentkernelfullb9cd55/CI48edee58native30digestssettled. Own596publishedsourcefull/CIpending;unsigned/actualgeometrypartial/no costadvantage/securityclaim.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: construct alternative prime-field gluings and complete chained Jacobian maps'],cwd=r,check=True)
print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
