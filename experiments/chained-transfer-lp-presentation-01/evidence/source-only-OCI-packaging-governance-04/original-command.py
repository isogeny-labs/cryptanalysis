from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, lzma, os, re, shutil, subprocess

r=Path('/workspace/cryptanalysis')
base='6ad0826722e91097cbb6feafcd99d3f625e08304'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
idx=Path('/dev/shm/ct345-Consumer-OCI-recipe-source-index');idx.mkdir()
shutil.copyfile(r/'.git/index',idx/'entire-before')
shutil.copyfile(r/'.git/index',idx/'actual-current')
os.environ.update(GIT_INDEX_FILE=str(idx/'actual-current'),GIT_OPTIONAL_LOCKS='0')
p=r/'experiments/chained-transfer-lp-presentation-01'
g=p/'evidence/source-only-OCI-packaging-governance-04';g.mkdir()
shutil.copyfile(__file__,g/'original-command.py')
scope=[str(p.relative_to(r)),'pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-16.md','.resume/RESUME.md','.github/workflows/chained-transfer-lp-historical-development-01.yml','.github/workflows/pcc-gate.yml','.gitattributes']
def names():
    return sorted(set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''})
def run(label,cmd,expected=0):
    q=subprocess.run(cmd,cwd=r,capture_output=True)
    (g/(label+'.txt.xz')).write_bytes(lzma.compress(q.stdout+q.stderr))
    (g/(label+'.exit')).write_text(str(q.returncode)+'\n')
    print(label,q.returncode,flush=True)
    assert q.returncode==expected
protected=subprocess.check_output(['git','diff','--name-only',base,'--','tools','scripts','suite','.github/workflows','.artifacts/config.json',str(p.relative_to(r))+'/native',str(p.relative_to(r))+'/matrix-01',str(p.relative_to(r))+'/lean',str(p.relative_to(r))+'/historical-01',str(p.relative_to(r))+'/post-character-01'],cwd=r)
assert set(protected.decode().splitlines())=={'.github/workflows/chained-transfer-lp-historical-development-01.yml',str(p.relative_to(r))+'/historical-01/source-01.sha256'}
run('original-ledger-prefix',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
run('authored-prose',['python3','tools/pcc/pcc.py','lint-prose',*[n.decode() for n in names() if n.endswith(b'.md')]])
run('all1605-original-source-pins',['sha256sum','--check','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256'])
run('all50-current-native-probe-proof-source-pins',['sha256sum','--check',str(p.relative_to(r))+'/historical-01/source-01.sha256'])
run('benchrec',['python3','tools/benchrec.py','gate'])
run('wiring',['python3','tools/artifacts/wire_workflows.py','--check'])
run('report-Python',['python3','tools/ci/check_report_graph_python.py'])
run('workflow-actionlint',['/workspace/scratch/actionlint-bin/actionlint','-oneline','.github/workflows/chained-transfer-lp-historical-development-01.yml'])
run('all12-population-runtime-source-guards',['sha256sum','--check',str(p.relative_to(r))+'/population-01/source-01.sha256'])
run('all8-OCI-recipe-source-guards',['sha256sum','--check',str(p.relative_to(r))+'/runtime-01/oci-01/source-01.sha256'])
run('runtime-assembler-shell-syntax',['bash','-n',str(p.relative_to(r))+'/runtime-01/assemble-01.sh',str(p.relative_to(r))+'/runtime-01/export-guarded-bytes-01.sh',str(p.relative_to(r))+'/runtime-01/oci-01/assemble-context-01.sh'])
def stage():
    ns=[n for n in names() if n]
    paths=idx/'selected-paths0';paths.write_bytes(b'\0'.join(n for n in ns if n!=b'.resume/RESUME.md')+b'\0')
    subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(paths),'--pathspec-file-nul'],cwd=r,check=True)
    subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True)
    selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''}
    assert selected==set(ns)
    for n in selected:
        if n.startswith(b'pcc/claims/'):
            for proof in json.loads((r/n.decode()).read_text()).get('proofs',[]):
                if proof.get('kind')=='attestation':
                    s=proof['subject'];assert hashlib.sha256((r/s['path']).read_bytes()).hexdigest()==s['sha256']
                    assert s['path'].encode() in selected or subprocess.run(['git','cat-file','-e',base+':'+s['path']],cwd=r,capture_output=True).returncode==0
stage()
run('cached-whitespace',['git','diff','--cached','--check'])
tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip()
run('immediate-artifact-policy',['python3','tools/artifacts/artifacts.py','check',base,tree])
run('frozen826-artifact-policy',['python3','tools/artifacts/artifacts.py','check','82617f14fb48843585137f0310f7d1fa9a5d8ea6',tree],1)
raw=lzma.decompress((g/'frozen826-artifact-policy.txt.xz').read_bytes())
found={(m.group(2).decode(),int(m.group(1).replace(b',',b''))) for m in re.finditer(rb'^ +([0-9,]+)  (.+)$',raw,re.M)}
expected={(str(p.relative_to(r))+'/evidence/historical-native-CI-success-01/entire-original-checkpoint-metadata/remote-RESUME.md.xz',109392)}
expected.update(('experiments/chained-transfer-relation-diagnostics-02/evidence/entire-CI02-source-guard-failure-01/entire-original-checkpoint-metadata/'+n+'-RESUME.md.xz',101396) for n in ['original','pack','remote'])
expected.update((str(p.relative_to(r))+'/evidence/whole-guarded-byte-snapshot-01/'+n,b) for n,b in [('all-materialized-whole-files.sha256.xz',65844),('entire-unique-source-plan.tsv.xz',70088),('entire-unsorted-source-plan.tsv.xz',70840)])
assert found==expected and b'7 data file(s)' in raw
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Source-only whole LP runtime packaging and context custody: official immutable Debian amd64 base metadata3a72e2, exact old340729140B/pure53419171B CI archives/39331840B source tar/native/compiler/engine/fixtures complete in successive held contexts b75dd8/4ba9e2 and final own8-source-guarded309-file/19-byte-phase metadata context, no Docker/AWS/compiler/science invocation. Recipe explicitly sets UID1000 ownership and refuses dirty/unbound recipe-source builds; first source review/manifest refresh errors and all whole context files preserved. Original immediate prefix/prose/all1605/all50/all12/all8/benchrec/wiring/reportPython/actionlint/shell/cached/immediate artifact0; broader frozen826 artifact1 remains exact7 older whole objects (3 snapshot XZ plus4 RESUME), not prior5-JSON prediction. Original ConsumerPCC workflow1605 pin stays unchanged after retained7f4d7d; no policy/source guard waiver or merge before genuine store/hydration/all-rawNEW28/current applicable checks/review. CI only adds shell/source/capture for actual recipe, with workflow→pure50→population12 hash metadata refresh. Native math/Lean/controls/protocol/limits/tools/verifiers/keyring unchanged. Entire original Consumer index/config/shared metadata5bad90 retained inRAM; equivalent split index restores16MiB and source6ad/staged tree unchanged, no raw/object deletion. Root47b94f publishes final raw coefficient word bridge2aa7f3 dual27/0/10bindings/reporte1998c/current8880-key FF59199b with76dd39; separate currentCI pending. Actual2c native/compiler/proof941dbe remains native provenance; current recipe and oldbaselineb7/upstream3d/Rootsnapshot44 separate. All paid builds/jobs stop e42949; clean runtimeGit/bootstrap/checkpoint/OCI/ABI/actualJob/Pod/admission/full historical LP population remain open.']
for f in sorted(g.iterdir()):cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True)
subprocess.run(['git','commit','--quiet','-m','research: package whole LP runtime inputs with pinned source-only image recipe'],cwd=r,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
shutil.copyfile(idx/'actual-current',r/'.git/index')
assert hashlib.sha256((r/'.git/index').read_bytes()).digest()==hashlib.sha256((idx/'actual-current').read_bytes()).digest()
print(claim,head,flush=True)
out=Path('/workspace/scratch/ct345-Consumer-OCI-source-normal-publication')
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-lp-presentation-20261115',str(out)],cwd=r,capture_output=True)
(idx/'whole-publication-caller.txt').write_bytes(q.stdout+q.stderr)
print('normal-publication',q.returncode,flush=True);assert q.returncode==0
print(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source=head,governance=claim,publication=str(out))))
