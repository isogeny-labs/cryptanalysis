"""Record actual sidecar release, preserve bytes and exact canonical alias."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,os,shutil,subprocess
r=Path('/workspace/crypto');c=Path('/workspace/cryptanalysis');scratch=Path('/workspace/scratch')
s=r/'research/chained_jacobian_transfers_20261110';cs=c/'experiments/chained-transfer-public-target'
source='00be7d5432324d2686686fbb57498f3c968fa07a';bot='67353d444b4266b6815e6c6d8a5db85218561ea4'
ff=scratch/'ct109-index-sidecar-artifact-ff-01'
assert(scratch/'ct109-index-sidecar-FF-caller01.exit').read_text().strip()=='0'
receipt=json.loads((ff/'terminal-release.json').read_text());assert receipt['sidecar_hold'].startswith('RELEASED')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==bot
payload=s/'evidence/public-n4-comparator-index-sidecar-01';manifest=json.loads((payload/'.artifacts.json').read_text());objects=json.loads((payload/'objects.json').read_text());assert len(objects)==len(manifest['files'])==2
# Populate only the two exact genuinely published canonical cache paths. All
# originals remain intact; no new consumer remote read is asserted.
for row in objects:
 target=r/row['path'];original=Path(row['local_original']);assert not target.exists()and not target.is_symlink()
 shutil.copyfile(original,target);assert target.read_bytes()==original.read_bytes()and hashlib.sha256(target.read_bytes()).hexdigest()==row['sha256']
 assert subprocess.run(['git','check-ignore','-q',row['path']],cwd=r).returncode==0
e=s/'evidence/public-n4-comparator-index-publication-01';e.mkdir()
for p in sorted(ff.iterdir()):
 if p.is_file():shutil.copyfile(p,e/p.name)
for p in sorted((scratch/'ct109-index-sidecar-RAM-bot-fetch-01').iterdir()):
 if p.is_file():shutil.copyfile(p,e/('fetch-'+p.name))
for p,name in [(scratch/'ct109-index-sidecar-original-jobs-final-api.json','original-jobs-api.json'),(scratch/'ct109-index-sidecar-actual-original-publication-01/whole-job.log.xz','whole-original-job.log.xz'),(scratch/'ct108-index-sidecar-normal-publication-01/receipt.json','original-normal-push-receipt.json')]:shutil.copyfile(p,e/name)
for p,name in [(scratch/'ct109-index-sidecar-FF-caller01.txt','whole-FF-caller.txt.xz'),(scratch/'ct108-index-sidecar-normal-publication-01/push.log','whole-original-push.log.xz')]:
 body=p.read_bytes();packed=lzma.compress(body);assert lzma.decompress(packed)==body;(e/name).write_bytes(packed)
(e/'original-record-command.py').write_bytes(Path(__file__).read_bytes())
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Actual original immutable metadata sidecar publication: run43750430453/job132922943345, two remote objects replayed BEFORE actual bot67353d444b/direct00be7d54/exact4paths. Both full source Gitblobs equal unchanged original2140576B index/a879984e98342913e4614533083ca6a25aa51c0963cfab03faadea222e5426c7 and851696B completecurrentguard; fullXZintegrity/decompressedguard/indexencoding checked. All66706content keys185literal links538consumerownedpaths/consumerHEAD-status-exactledger/Rootledgerprefix and allprior65886keys179links preserved, normalFF/originalartifact/wiring0; temporary sidecar HOLD RELEASED. Exact2canonical entries are actual original publisher output; only those genuinely published ignored Root cache files restored byte-exact from retained originals for PCC subject reads, no new remote read claimed. Firstgovernor parsing failure5dca3c and comparator build/governance failures32398d/4a8f8f/cdcaa2 preserved. This is complete metadata custody, distinct from pending whole scientific custodyNEW28 and unexecuted comparator controls; unsigned.' ]
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
rootclaim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(rootclaim,flush=True)
name='whole-failed-staged-index.xz';entry=manifest['files'][name]
old=cs/'evidence/whole-relation-comparator-source-governance-failure-01'/name
assert old.is_file()and not old.is_symlink()and old.stat().st_size==entry['bytes']and hashlib.sha256(old.read_bytes()).hexdigest()==entry['sha256']
docs=c/'docs/research-artifacts/chained-transfer/comparator-index-sidecar-01';docs.mkdir()
projection=dict(manifest);projection['files']={name:entry}
(docs/'.artifacts.json').write_text(json.dumps(projection,indent=2)+'\n');(docs/'.gitignore').write_text(name+'\n')
os.rename(old,docs/name);old.symlink_to(os.path.relpath(docs/name,old.parent))
assert old.read_bytes()==(docs/name).read_bytes()==(payload/name).read_bytes()
assert hashlib.sha256(old.read_bytes()).hexdigest()==entry['sha256']and len(os.readlink(old))<500
ce=cs/'evidence/genuine-comparator-index-sidecar-publication-01';ce.mkdir()
for p,name2 in [(payload/'.artifacts.json','actual-original-root-manifest.json'),(docs/'.artifacts.json','exact-consumer-projection-manifest.json'),(ff/'terminal-release.json','actual-original-terminal-release.json')]:shutil.copyfile(p,ce/name2)
(ce/'original-command.py').write_bytes(Path(__file__).read_bytes())
(ce/'projection.json').write_text(json.dumps(dict(root_publication_claim=rootclaim,source=source,actual_bot=bot,run=43750430453,job=132922943345,original_replays_before_bot=2,exact_original_manifest_entry=entry,canonical_docs=docs.relative_to(c).as_posix(),same_pinned_subject_path=old.relative_to(c).as_posix(),transparent_relative_literal_target=os.readlink(old),all_original_full_bytes_SHA_unchanged=True,original_pinned_claim='4a8f8f',new_consumer_remote_read_claimed=False,full_scientific_custody='NEW28 remains pending',scope='unsigned original canonical byte projection only'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Consumer immutable metadata sidecar projection: actual original43750430453/job132922943345 two remote replays BEFORE actual bot67353d444b/direct00be7d54/exact4paths, full66706content185links538owned consumerHEAD-status-ledger/Rootprefix terminal guards and normalFF-artifact-wiring0 release temporaryhold. Exact original canonical entry for the complete2140576Bfailedindex/SHAa879984e98342913e4614533083ca6a25aa51c0963cfab03faadea222e5426c7 copied unchanged; all original full bytes moved intact into canonical docs and the SAME4a8f8f pinnedsubject path is a transparent relative alias with identical bytes. No syntheticmanifest/policy exemption or newconsumer remote read claimed. Fullguard original2entryRootpublication remains complete and separate from future fullscientificcustodyNEW28. All firstsourcegovernance/build/parser failures preserved; comparator174696 stillcompiled but wholecontrols/nativeCI UNEXECUTED pending clean sourcepublication/exactoriginalcheckpoint25. Unsigned bytecustody only.' ]
for p in sorted(ce.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(c).as_posix()]
cmd+=['--proof','attestation:'+old.relative_to(c).as_posix()]
consumerclaim=subprocess.check_output(cmd,cwd=c,text=True).strip();print(consumerclaim,flush=True)
(scratch/'ct110-index-sidecar-publication-claims.json').write_text(json.dumps(dict(root=rootclaim,consumer=consumerclaim),indent=2)+'\n')
state='''# Complete metadata sidecar genuinely published; hold released

## What was done
'''+rootclaim+' / '+consumerclaim+''': original43750430453/job132922943345 two actual remote replays BEFORE bot67353d444b/direct00be7d54/exact4paths. All66706content185literal links538consumerowned/HEAD-status-ledger/Rootprefix terminal checks, full sourceblobs/XZintegrity/guarddecodedbytes/indexencoding and normalFF/originalartifact/wiring0 pass. Temporary sidecar HOLD RELEASED. Complete2,140,576-byte failedindex subject4a8f8f retains exact bytes via one exact original canonical entry and a transparent relative alias at the same path. Root two genuine ignored cache objects are restored from full retained originals; no new remote read claimed. [pcc:unverified]

## Decisions made
Finish comparator compiled-source governor03 with exact canonical artifact verification, source/byte/ledger/prose gates, then normalpublication and original exactsource checkpoint25 before whole controls. Preserve every failed build/source-governance/parser attempt and all pinned bytes. Full scientific custody NEW28 remains separate and pending. [pcc:unverified]

## Open threads
Comparator compiled-source checkpoint and originalreceipt25; run fullpositive/eightnegative/elapsed-only controls with whole archives and runtime/sourceguards; implement whole diagnosticCI under prospectively published9aad0c/5f23dd29; review/freeze unassisted relation-completion successor. Existing global/model/numericLean/calibrated/admission/reference/merge requirements persist. [pcc:unverified]

## Errors
Firstbuild missinghex testdependency32398d, immutable testlog whitespace4a8f8f, full index originalartifact selectioncdcaa2 and sidecar governor stdout-stderr parser5dca3c all retained. No source, mathematical gate, originalpolicy, pinned byte or historical failure changed. [pcc:unverified]

---

'''
for repo,study,ck,queue in [(r,s,'PUBLIC_TARGET_CHECKPOINT.md','QUEUE.md'),(c,cs,'CHECKPOINT.md','RESEARCH_QUEUE.md')]:
 for p in [repo/'.resume/RESUME.md',study/ck,study/queue]:p.write_text(state+p.read_text())
 p=repo/'docs/session-logs/2026-11-15.md';p.write_text(p.read_text().rstrip()+'\n\n'+datetime.now(timezone.utc).isoformat()+'\n\n'+state.rstrip()+'\n')
print('actual publication/projection recorded; settlement and source governor03 next',flush=True)
