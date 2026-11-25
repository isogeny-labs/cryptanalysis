"""Owned source/result checkpoint through the original repository gates."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,shutil,lzma
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='f888bd5fe50262d0d74d85ff4caaf4e4af96c81d'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
g=s/'evidence/native-governance-03';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=['.github/workflows/pcc-gate.yml',str(s.relative_to(r)),'problems/chained-transfer-public-target-destination-bridge.md','problems/README.md','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
lock=str((s/'native/Cargo.lock').relative_to(r));subprocess.run(['git','add','--sparse','-f','--',lock],cwd=r,check=True)
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
    v=subprocess.run(cmd,cwd=r,capture_output=True);raw=v.stdout+v.stderr
    if len(raw)>60000:z=lzma.compress(raw,format=lzma.FORMAT_XZ);assert lzma.decompress(z)==raw;(g/(name+'.txt.xz')).write_bytes(z)
    else:(g/(name+'.txt')).write_bytes(raw)
    (g/(name+'.exit')).write_text(str(v.returncode)+'\n');print(name,v.returncode,flush=True);assert v.returncode==0,raw.decode()[:1800]
run('parent437',['sha256sum','--check','experiments/chained-transfer-reference/g3-norm-reference-01.sha256'])
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows/chained-transfer-reference.yml','experiments/chained-transfer-reference'],cwd=r)
subjects=[]
for p in paths():
    if p.startswith(b'pcc/claims/'):
        for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
            if proof.get('kind')=='attestation':
                x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path'];subjects.append(x['path'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode() for p in paths() if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate']);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/pcc-gate.yml']);before_workflow=(s/'evidence/diagnostic-data-read-plan-01/before-workflow.yml').read_text();after_workflow=(r/'.github/workflows/pcc-gate.yml').read_text();restore_block='      - name: Restore frozen public-target diagnostic data\n        run: |\n          set -euo pipefail\n          xz --decompress --stdout experiments/chained-transfer-public-target/evidence/native-diff-encoding-correction-01/cached-whitespace.txt.xz > experiments/chained-transfer-public-target/evidence/native-diff-encoding-correction-01/cached-whitespace.txt\n';assert after_workflow.count(restore_block)==2 and after_workflow.replace(restore_block,'')==before_workflow
def stage():
    ps=paths();f=Path('/workspace/scratch/ct57-native-03.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True);selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    for p in subjects:assert subprocess.run(['git','cat-file','-e',base+':'+p],cwd=r,capture_output=True).returncode==0 or p.encode() in selected,p
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(base=base,all437_parent_native_inputs_unchanged=True,whole_parent7workflow_and_verifier_trust_unchanged=True,ONLYPCCworkflowdelta="onefixedfrozen0da3f3datarestoreinBOTHexistingjobs;wholeinversecheck",new_native_source='publicQONLY4literalbodychanges/4originalfilesbyteexact',own_ledger_prose_whitespace_wiring_benchrec_artifact=0,all_new_subject_hashes_and_staging_covered=True,unit='e08eac',actualCLI='9e522f',formal='f68241/9exactlocalbindings/originalgates9/0trusted',actualraw='f32a84/30806e',report='19f350/TWO50557bytePDFpagesALLinspected',independent_full_CI_and_rhoanswer_P2_geometry='pending',benchmark_admission=False),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','PublicN4 nativecheckpoint governance ownf888ledger/prose/workingcachedwhitespace/wiring/benchrec/artifact0/all437parentinputs/whole7workflow unchanged/newsubjecthashstaging;ONLYPCCdeltaonefixedfrozen0da3f3datarestoreinBOTHexistingjobs/wholeinversecheck/actionlint0,originalverifiertrustunchanged. Actualunit e08eac FIVEIC/CLI9e522f FIVEpublicQ+14controls;9originalgates/bindings f68241 partial;allTHREEwholearchives actuallypublishedf32a84/genuine30806e. TWOfinal50557PDFpages19f350ALLinspected. Independentfull/ownCI/rhoanswer/P2concretegeometry/costadmission pending;no sourceverifier/trust/policy change ormergedclaim.']
for p in sorted(g.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct57-native-governance.claim').write_text(cl+'\n');selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: implement and check public-target N4 with explicit model proofs'],cwd=r,check=True);print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
