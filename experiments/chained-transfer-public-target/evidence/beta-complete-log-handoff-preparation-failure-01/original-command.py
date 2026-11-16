"""Whole storage custody and fresh publication hold; no scientific computation."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,io,json,lzma,os,shutil,subprocess,tarfile
r=Path('/workspace/crypto');s=r/'research/chained_jacobian_transfers_20261110';c=Path('/workspace/cryptanalysis');cs=c/'experiments/chained-transfer-public-target'
base='e149ba385fd3539a58fada68f279e9f1b30f898e';consumer='b691714c8c6f7b157f9ec832ccc91413c624c541'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=c,text=True).strip()==consumer
o=Path('/workspace/scratch/ct73-PCC-log-handoff-01');o.mkdir()
d=s/'evidence/public-n4-complete-PCC-log-handoff-01';d.mkdir();g=s/'evidence/public-n4-complete-beta-current-guard-13';g.mkdir()
at=datetime.now(timezone.utc).isoformat()
state=f'''# Complete replay and blocking whole-log publication — {at}

Complete b691 physical replay666cb7 passes20expectedphases/threeactual101controls/882unchangedguards/whole3nativeJSONNOmasks/bothoriginal44+1proofgates/sevenbindings. Automatic b691CI has19success+onePCCmissingPNGfailure423f66; newcomplete43585724236 succeeded. No all20greenclaim. Data routing8397ab preserves allreport subjects/workflows/881scienceinputs using canonicaldocsPNG+seventhrelativeGitlink. Originalartifactgate1 nowrequires genuinepublication ofwhole68044Bfailurelog (7b651f); no policy exception. All unsigned. [pcc:unverified]

NEWguard13 publication covers unchangedwholePCCfailurelog, completependingconsumer/baseb691/patch/ledger/resume plusWHOLE freshCfull/driver/own20CIcaptures(all20logs/fourwholeZIPs/everymember) checkpoint, andwholecurrentinputmap. HOLD allcurrent scientificpaths/actualproofsources andbothrepoownedbytes until original remote-byte replays/exactpublisherFF/terminalguards. Prior6210guard12 scope retained withONLYtwo removedreportmetadata files relocated to exactpreservedfailure copies afterrelease12; everyoldbyte accounted. Existingsevenlinktypes pinned. No scienceedit duringhold. [pcc:unverified]

Afterrelease projectlogentryinto canonicaldocs plusrelative evidence link, preserve alloldclaims, completeconsumer datafixcommit andownautomatic20CI/audit419native/73canonical75actualverdicts/whole7113census/allphaseguards. Freshb691full remainsvalid forbyte-identical881inputs. Remainingwholeca9/398/A-B/C77largecaptures (includingsealedBfullcache) move toNEWguard14; do notdrop them. Then prospectiveprimary/KB-reviewed directNormhalving vsstrongnorm-assistedbaseline, no newcodeorperformanceclaimyet. Rootclock124/101/mainledger/reviews/signing/conflict/fullformalgeometry/globalclosedcoords/calibratedcost/livebudgetcapacity/vaultKB remainopen. Continueunblockedwork/no paidlaunch/nowaiver. [pcc:unverified]
'''
for p in [cs/'RESEARCH_QUEUE.md',cs/'CHECKPOINT.md',c/'.resume/RESUME.md']:p.write_text(state+'\n---\n\n'+p.read_text())
with(c/'docs/session-logs/2026-11-14.md').open('a')as f:f.write('\n'+state)
scopes=['experiments/chained-transfer-public-target','docs/research-artifacts/chained-transfer/beta-complete-rational-01','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-14.md','.resume/RESUME.md','.gitattributes','.github/workflows','problems/chained-transfer-odd-product-kernel-and-odd-factor.md']
names=sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scopes],cwd=c).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--no-renames','--name-only','-z'],cwd=c).split(b'\0')))-{b''})
files=[];deleted=[]
for name in names:
 p=c/name.decode()
 if p.exists()or p.is_symlink():files.append((p,'consumer/'+name.decode()))
 else:deleted.append(name.decode())
rawdirs=[Path('/workspace/scratch')/n for n in ['ct73-complete-full-01','ct73-complete-driver-01','ct73-complete-own-CI-01','ct73-complete-PNG-routing-01']]
for directory in rawdirs:
 assert directory.is_dir();files.extend((p,'runs/'+directory.name+'/'+p.relative_to(directory).as_posix())for p in sorted(directory.rglob('*'))if p.is_file()or p.is_symlink())
for pattern in ['ct73*complete*PNG*routing*caller*.txt','ct73*complete*png*routing*.py','ct73*complete*checkpoint_0[345].py','ct73*complete*full*.py']:
 files.extend((p,'commands/'+p.name)for p in sorted(Path('/workspace/scratch').glob(pattern))if p.is_file())
files=list({name:(p,name)for p,name in files}.values());assert len({name for _,name in files})==len(files)
controls={'control/base.txt':(consumer+'\n').encode(),'control/pending-full.patch':subprocess.check_output(['git','diff',consumer,'--binary','--full-index','--',*scopes],cwd=c),'control/deleted-paths.json':(json.dumps(deleted,indent=2)+'\n').encode(),'control/snapshot.json':(json.dumps(dict(at=at,root_base=base,consumer_base=consumer,all_pending_owned_paths=len(names),whole_raw_roots=[str(p)for p in rawdirs],all20logs_fourZIPs_all_members=True,build_cache_outside_captured_roots=True,remaining_bulk_batch='NEWguard14'),indent=2)+'\n').encode()}
archive=o/'pending-source-complete-full-and-CI.tar.xz';members=[]
with tarfile.open(archive,'w:xz',dereference=False)as t:
 for p,name in sorted(files,key=lambda x:x[1]):
  b=p.read_bytes();row=dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
  if p.is_symlink():row['symlink_target']=os.readlink(p)
  members.append(row);info=t.gettarinfo(str(p),arcname=name);info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  if p.is_symlink():t.addfile(info)
  else:t.addfile(info,io.BytesIO(b))
 for name,b in sorted(controls.items()):
  info=tarfile.TarInfo(name);info.size=len(b);info.mode=0o644;t.addfile(info,io.BytesIO(b));members.append(dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
with tarfile.open(archive,'r:xz')as t:
 assert len(t.getmembers())==len(members)
 for row in members:
  member=t.getmember(row['path'])
  if 'symlink_target'in row:assert member.issym()and member.linkname==row['symlink_target'];continue
  b=t.extractfile(member).read();assert len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']
(d/'checkpoint-members.json').write_text(json.dumps(dict(members=members,all_pending_owned_paths=len(names),deleted_paths=deleted,whole_raw_roots=[str(p)for p in rawdirs],symlinks_preserved=True,no_pruning_or_splitting=True),indent=2)+'\n')
old=json.loads(Path('/workspace/scratch/ct73-png-handoff-02/current-inputs.json').read_text());assert len(old)==6210
current={};relocations=[]
for name,h in old.items():
 p=Path(name)
 if not p.exists():
  assert p.parent==cs/'reports/beta-complete-rational-01'and p.name in {'.artifacts.json','.gitignore'}
  new=cs/'evidence/beta-complete-PCC-hydration-failure-01'/('prior-report'+p.name)
  assert hashlib.sha256(new.read_bytes()).hexdigest()==h;relocations.append(dict(old=name,current=str(new),sha256=h,reason='after released12: canonical docs routing, exact old report metadata retained'));p=new
 assert hashlib.sha256(p.read_bytes()).hexdigest()==h,name;current[str(p)]=h
assert len(relocations)==2
for name,h in json.loads(Path('/workspace/scratch/ct73-complete-full-01/before.json').read_text()).items():
 assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==h;current[name]=h
for path in [cs/'ci_beta_complete/reference-01.sha256',c/'docs/research-artifacts/chained-transfer/beta-complete-rational-01/complete-diagram.png']:
 current[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
links={p:os.readlink(p)for p in current if Path(p).is_symlink()};assert len(links)==7
raw=(json.dumps(current,indent=2)+'\n').encode();(o/'current-inputs.json').write_bytes(raw);(o/'whole-current-inputs.json.xz').write_bytes(lzma.compress(raw))
(g/'symlink-targets.json').write_text(json.dumps(links,indent=2)+'\n');(g/'released12-metadata-relocations.json').write_text(json.dumps(relocations,indent=2)+'\n')
(g/'custody.json').write_text(json.dumps(dict(at=at,guard13=len(current),prior6210_bytes_all_accounted=True,exact_two_non_science_metadata_relocations=relocations,all_current881_science_plus_self_and_fresh882=True,links=links,hold='no held scientific or owned byte edits until genuine remote replay and exactFF terminal checks',whole_map=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())),indent=2)+'\n')
log=cs/'evidence/beta-complete-PCC-hydration-failure-01/PCC-whole-failure.log.xz';assert log.stat().st_size==68044
objects=[]
for src in [log,archive,o/'whole-current-inputs.json.xz']:
 dest=d/src.name;shutil.copyfile(src,dest);b=dest.read_bytes();objects.append(dict(path=str(dest.relative_to(r)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),local_original=str(src)))
(d/'objects.json').write_text(json.dumps(objects,indent=2)+'\n');shutil.copyfile(__file__,d/'original-command.py')
(d/'scope.json').write_text(json.dumps(dict(at=at,root_base=base,consumer_base=consumer,objects=objects,checkpoint_members=len(members),whole_raw_roots=[str(p)for p in rawdirs],guard13=len(current),symlink_types=7,remaining_bulk_capture_batch='NEWguard14',remote_availability='pending genuine publisher replay before bot',scope='unsigned whole custody; no science, verifier, workflow or policy edits'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Blocking complete-PCC log handoff: THREEwholeobjects include unchanged68044B failurelogXZ, completependingconsumer/baseb691/patch/ledger/resume plusWHOLEfreshCfull/driver/own20CI(all20logs/fourZIPs/everymember) checkpoint, andwholecurrent-inputmap. Every regular archive member roundtripped/hashchecked andeverylink target retained, no prune/split/policy change. NEWguard13 retainsallprior6210bytes withEXACTtwo released12 non-science reportmetadata relocations, plusfresh882sources/current881self/sevenlinktypes; holduntilgenuine3remotereplays/exactbotFF/allguards+ownedbytes. Remainingca9/398/A-B/C77bulkbatch NEWguard14. Allunsigned; correctedconsumerCI stillpending.']
for p in [d/'objects.json',d/'scope.json',d/'checkpoint-members.json',g/'custody.json',g/'symlink-targets.json',g/'released12-metadata-relocations.json']:cmd+=['--proof','attestation:'+str(p.relative_to(r))]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();(o/'handoff.claim').write_text(claim+'\n');(o/'expected-migration-paths.json').write_text(json.dumps([x['path']for x in objects],indent=2)+'\n')
for p in [s/'QUEUE.md',s/'PUBLIC_TARGET_CHECKPOINT.md',r/'.resume/RESUME.md']:p.write_text(state+'\nHandoff '+claim+'; actualpublisherpending/guard13HOLD. [pcc:unverified]\n\n---\n\n'+p.read_text())
with(r/'docs/session-logs/2026-11-14.md').open('a')as f:f.write('\n'+state+'\nHandoff '+claim+' retains whole blockinglog/source/fullC/CI capture. [pcc:unverified]\n')
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in current.items())
print(claim);print(json.dumps(dict(guards=len(current),links=len(links),members=len(members),objects=[dict(path=x['path'],bytes=x['bytes'])for x in objects])))
