"""File custody only: whole bytes at already hydrated original docs addresses."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, importlib.util, json, os, shutil, subprocess, sys
r=Path('/workspace/cryptanalysis')
g=r/'experiments/chained-transfer-lp-presentation-01/evidence/whole-payload-original-docs-hydration-layout-07'
g.mkdir()
shutil.copyfile(__file__,g/'entire-original-byte-layout-command.py')
docs=r/'docs/chained-transfer-byte-custody-20261116'
(docs/'payloads').mkdir(parents=True)
sp=importlib.util.spec_from_file_location('original_artifact_policy',r/'tools/artifacts/artifacts.py')
m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m)
policy=m.Config.load(r).policy
names=set(subprocess.check_output(['git','diff','--name-only','82617f14fb48843585137f0310f7d1fa9a5d8ea6','HEAD'],cwd=r,text=True).splitlines())|set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard'],cwd=r,text=True).splitlines())
selected=[]
for name in sorted(names):
    p=r/name
    if p.is_file() and not p.is_symlink() and m.belongs_in_store(name,p.stat().st_size,policy):
        assert name.startswith(('experiments/chained-transfer-lp-presentation-01/evidence/','experiments/chained-transfer-relation-diagnostics-02/evidence/'))
        selected.append(name)
assert len(selected)==12
workflow=r/'.github/workflows/pcc-gate.yml'
workflow_before=workflow.read_bytes()
assert workflow_before==subprocess.check_output(['git','show','HEAD:.github/workflows/pcc-gate.yml'],cwd=r)
assert workflow_before.count(b'artifacts.py pull --jobs 16 docs ')==2
before=[]
for name in selected:
    p=r/name;b=p.read_bytes();sha=hashlib.sha256(b).hexdigest()
    assert p.suffix=='.xz'
    target=docs/'payloads'/(sha+'.xz')
    if target.exists():assert target.is_file() and not target.is_symlink() and target.read_bytes()==b
    else:os.link(p,target)
    relative=os.path.relpath(target,p.parent)
    before.append({'original_path':name,'original_bytes':len(b),'sha256':sha,'original_mode':p.stat().st_mode&0o777,'entire_regular_payload':target.relative_to(r).as_posix(),'original_address_relative_symlink':relative})
manifest={'schema':'chained-transfer.whole-byte-address-custody/v1','time':datetime.now(timezone.utc).isoformat(),'addresses':before,'distinct_complete_encoded_payloads':len({x['sha256']for x in before}),'coverage':'both original frozen PCC jobs hydrate docs before original verify-all','scope':'whole encoded files preserved; original store upload/full replay/current CI still required; no scientific execution or policy exception'}
(docs/'EXACT_ADDRESSES_01.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copyfile(docs/'EXACT_ADDRESSES_01.json',g/'immutable-entire-exact-addresses-01.json')
for x in before:
    p=r/x['original_path'];q=p.with_name(p.name+'.whole-docs-byte-address')
    assert not q.exists() and not q.is_symlink()
    q.symlink_to(x['original_address_relative_symlink']);q.replace(p)
    assert p.is_file() and p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'] and p.stat().st_size==x['original_bytes']

def run(name,args):
    q=subprocess.run(args,cwd=r,capture_output=True,timeout=120)
    (g/(name+'.stdout')).write_bytes(q.stdout);(g/(name+'.stderr')).write_bytes(q.stderr);(g/(name+'.exit')).write_text(str(q.returncode)+'\n')
    print(name,q.returncode,flush=True);assert q.returncode==0
for label,path in [('original1605','experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256'),('pure50','experiments/chained-transfer-lp-presentation-01/historical-01/source-01.sha256'),('population12','experiments/chained-transfer-lp-presentation-01/population-01/source-01.sha256'),('own9','experiments/chained-transfer-lp-presentation-01/runtime-01/oci-01/source-01.sha256')]:
    run('all-'+label+'-original-source-pins',['sha256sum','--check',path])
assert workflow.read_bytes()==workflow_before
sp=importlib.util.spec_from_file_location('original_pcc',r/'tools/pcc/pcc.py');pcc=importlib.util.module_from_spec(sp);sys.modules[sp.name]=pcc;sp.loader.exec_module(pcc)
keyring=pcc.load_keyring(r/'pcc/keyring.json');subjects=[]
for claim_path in sorted((r/'pcc/claims').glob('*.json')):
    claim=json.loads(claim_path.read_text())
    for index,proof in enumerate(claim.get('proofs',[])):
        if proof.get('kind')=='attestation' and proof.get('subject',{}).get('path') in selected:
            reasons=[];notes=[]
            verdict=pcc.verify_attestation(proof,r,keyring,reasons,notes)
            assert verdict=='not_covered' and not reasons
            subjects.append({'claim':claim['id'],'proof_index':index,'path':proof['subject']['path'],'sha256':proof['subject']['sha256'],'original_verifier':verdict,'reasons':reasons,'notes':notes})
assert subjects
(g/'all-affected-original-attestation-subject-results.json').write_text(json.dumps(subjects,indent=2)+'\n')
protected=set()
for name in ['experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256','experiments/chained-transfer-lp-presentation-01/historical-01/source-01.sha256','experiments/chained-transfer-lp-presentation-01/population-01/source-01.sha256']:
    protected.update(line.split('  ',1)[1] for line in (r/name).read_text().splitlines())
intersections=sorted(set(selected)&protected)
(g/'actual-whole-address-layout.json').write_text(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'whole_original_addresses':len(before),'distinct_complete_payloads':manifest['distinct_complete_encoded_payloads'],'all_original_sizes_and_sha256_unchanged':True,'affected_original_attestations_unsigned_no_failures':len(subjects),'original_source_guard_paths_intersecting_moved_evidence':intersections,'frozen_original_PCC_workflow_unchanged':True,'original_policy_verifier_keyring_unchanged':True,'genuine_remote_migration':'pending; local full-data layout only'},indent=2)+'\n')
print('whole_addresses',len(before),'whole_payloads',manifest['distinct_complete_encoded_payloads'],'original_attestation_subjects',len(subjects),'guard_intersection',intersections,flush=True)
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Whole-data layout under the already existing original Consumer docs hydration preserves12 complete encoded evidence addresses as explicit relative symlinks to whole regular SHA-addressed docs payloads. All actual original byte counts/digests remain exact, complete immutable address map and original command retained; all original1605/pure50/pop12/current own9 source guards0 and every affected original attestation subject returns unsigned not_covered with no failed subjects. Frozen original PCC gate/sign bytes unchanged and already pull docs, original policy/verifier/keyring/native/protocol/limits unchanged. This addresses local coverage design for the prior seven objects plus new source-custody whole data; it does not establish actual remote upload/hydration/CI, require genuine original migration/full remote replay before bot/merge. No missing-file shortcut, payload sharding/truncation/extension exception, claim/path-hash mutation, ledger rewrite, paid/scientific/native/image or signed standing.']
for f in sorted(g.iterdir()):cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim,flush=True)
entry='\n---\n\n'+datetime.now(timezone.utc).isoformat()+'\n# Original docs hydration covers complete scientific-source custody payloads locally\n\n## What was done\n'+claim+':12 original whole encoded addresses retain exact sizes/SHA through explicit relative links to full regular docs payloads; complete address map/command retained. Original1605/50/12/own9 guards0; every affected original attestation subject unsigned/not_covered without failures. Frozen PCC workflow remains byte-exact and both jobs already pull docs. [pcc:unverified]\n\n## Decisions made\nPublish complete original-policy payloads and original address links, then require genuine upload/full remote replay/bot plus own current CI before claiming remote closure or merge. Preserve all original data/claims/tools/policy/workflow. [pcc:unverified]\n\n## Open threads\nSource governor/publication/current CI/whole remote migration, full scientificNEW28 and combined fresh runtime/checkpoint/ABI/EKS/full LP remain separate. [pcc:unverified]\n\n## Errors\nNo observed source/payload/subject hash failure; no missing-file waiver/sharding/policy exception or science/paid run. [pcc:unverified]\n'
for name in ['docs/session-logs/2026-11-16.md','.resume/RESUME.md']:
    with(r/name).open('a')as f:f.write(entry)
