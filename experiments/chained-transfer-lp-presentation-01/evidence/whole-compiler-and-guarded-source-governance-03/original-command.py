from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, lzma, os, re, shutil, subprocess

r=Path('/workspace/cryptanalysis')
base='2c44ee2ebb0be9b5fc0375818cc18924cef82c41'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
idx=Path('/dev/shm/ct318-consumer-compiler-snapshot-corrected-whole-index');idx.mkdir()
shutil.copyfile(r/'.git/index',idx/'entire-before')
shutil.copyfile(r/'.git/index',idx/'actual-current')
os.environ.update(GIT_INDEX_FILE=str(idx/'actual-current'),GIT_OPTIONAL_LOCKS='0')
p=r/'experiments/chained-transfer-lp-presentation-01'
g=p/'evidence/whole-compiler-and-guarded-source-governance-03';g.mkdir()
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
assert set(protected.decode().splitlines())==set()
run('original-ledger-prefix',['python3','tools/pcc/pcc.py','ledger','verify','--base',base])
run('authored-prose',['python3','tools/pcc/pcc.py','lint-prose',*[n.decode() for n in names() if n.endswith(b'.md')]])
run('all1605-original-source-pins',['sha256sum','--check','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256'])
run('all50-current-native-probe-proof-source-pins',['sha256sum','--check',str(p.relative_to(r))+'/historical-01/source-01.sha256'])
run('benchrec',['python3','tools/benchrec.py','gate'])
run('wiring',['python3','tools/artifacts/wire_workflows.py','--check'])
run('report-Python',['python3','tools/ci/check_report_graph_python.py'])
run('workflow-actionlint',['/workspace/scratch/actionlint-bin/actionlint','-oneline','.github/workflows/chained-transfer-lp-historical-development-01.yml'])
run('all12-population-runtime-source-guards',['sha256sum','--check',str(p.relative_to(r))+'/population-01/source-01.sha256'])
run('runtime-assembler-shell-syntax',['bash','-n',str(p.relative_to(r))+'/runtime-01/assemble-01.sh',str(p.relative_to(r))+'/runtime-01/export-guarded-bytes-01.sh'])
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
run('immediate-artifact-policy',['python3','tools/artifacts/artifacts.py','check',base,tree],1)
raw_now=lzma.decompress((g/'immediate-artifact-policy.txt.xz').read_bytes());assert b'1 data file(s)' in raw_now and b'full-runtime-source-closure-metadata-01/entire-1661-file-closure.json' in raw_now
run('frozen826-artifact-policy',['python3','tools/artifacts/artifacts.py','check','82617f14fb48843585137f0310f7d1fa9a5d8ea6',tree],1)
raw=lzma.decompress((g/'frozen826-artifact-policy.txt.xz').read_bytes())
found={(m.group(2).decode(),int(m.group(1).replace(b',',b''))) for m in re.finditer(rb'^ +([0-9,]+)  (.+)$',raw,re.M)}
expected={(str(p.relative_to(r))+'/evidence/historical-native-CI-success-01/entire-original-checkpoint-metadata/remote-RESUME.md.xz',109392)}
expected.update(('experiments/chained-transfer-relation-diagnostics-02/evidence/entire-CI02-source-guard-failure-01/entire-original-checkpoint-metadata/'+n+'-RESUME.md.xz',101396) for n in ['original','pack','remote'])
expected.add((str(p.relative_to(r))+'/evidence/full-runtime-source-closure-metadata-01/entire-1661-file-closure.json',543821))
assert found==expected and b'5 data file(s)' in raw
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Publish completed actual2c native/cold-compiler/proof whole-CI custody941dbe,1661-file full source closureee0ca3 and complete1663-member guarded byte snapshot10ced7. New exporter is file I/O only; all14 actual byte phases0, no local math/paid build/job or runtimeGit/OCI/ABI/admission qualification. Original immediate-parent prefix/prose/all1605/all50/all12/benchrec/wiring/reportPython/actionlint/runtime-shell/cached checks0; mathematical/native/Lean/controls/protocol/limits/tools/keyring/verifiers unchanged. Rejected hydration proposal/frozen-workflow guard1 retained; exact original workflow restored. All five genuine store/hydration prerequisites stay open and must respect original1605 source closure. Immediate artifact1 is exactly the whole543821B directly pinned closure JSON; broad826 artifact1 is exactly that JSON plus4 older whole RESUME archives (109392 and3x101396B). No renaming/sharding/policy waiver or merge before genuine all-raw scientific store/current checks/review requirements. Current full53419171B740-member CI archive/full log/source/compiler/profiles/nativebytes and earlier04031MB502-member failure remain whole; actual2c fresh pure14/15 package release compilation succeeds, existing native14/5/15/2 and both original graph10/0 gates pass, compiler-only outputs unexecuted. Norm Root4413 actually mergedaa1e8236 after exact current original15/0 gates/full8723-key guard, separate source scope. All LP60/240/62/original360/witness/7 controls/feedback/post executions remain prospective under exhausted budgete42949; next runtime context/source work proceeds without paid builds/jobs.']
for f in sorted(g.iterdir()):cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True)
subprocess.run(['git','commit','--quiet','-m','research: retain successful pure builds and whole guarded source snapshot'],cwd=r,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()
shutil.copyfile(idx/'actual-current',r/'.git/index')
assert hashlib.sha256((r/'.git/index').read_bytes()).digest()==hashlib.sha256((idx/'actual-current').read_bytes()).digest()
print(claim,head,flush=True)
out=Path('/workspace/scratch/ct318-consumer-normal-source-publication-01')
q=subprocess.run(['python3','/workspace/scratch/publish_normal_git_checkpoint.py','isogeny-labs/cryptanalysis',base,head,'research/chained-transfer-lp-presentation-20261115',str(out)],cwd=r,capture_output=True)
(idx/'whole-publication-caller.txt').write_bytes(q.stdout+q.stderr)
print('normal-publication',q.returncode,flush=True);assert q.returncode==0
print(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),source=head,governance=claim,publication=str(out))))
