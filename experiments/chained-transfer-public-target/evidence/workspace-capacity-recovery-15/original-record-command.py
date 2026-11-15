"""Checkpoint complete filesystem/partial-clone failure and whole-cache recovery evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';scratch=Path('/workspace/scratch');e=s/'evidence/workspace-capacity-recovery-15';e.mkdir()
roots=[scratch/'ct98-readonly-archive-view-probe-01',scratch/'ct98-immutable-object-pack-consumer01',scratch/'ct98-remote-cache-relocation-01']
all_raw={}
for root in roots:
 for f in root.rglob('*'):
  if not f.is_file():continue
  all_raw[str(f)]=dict(bytes=f.stat().st_size,sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest())
  # Entire package/probe/failure evidence remains raw; retain all small result
  # receipts and lossless whole text sources in this checkpoint too.
  if f.suffix in ['.json','.txt','.stderr','.stdout','.exit','.py']and f.stat().st_size<200000:
   name=root.name+'--'+str(f.relative_to(root)).replace('/','__');body=f.read_bytes()
   if len(body)>60000:(e/(name+'.xz')).write_bytes(lzma.compress(body))
   else:(e/name).write_bytes(body)
for name in ['ct98-immutable-object-pack-consumer01-caller.txt','ct98-immutable-object-pack-consumer01-caller.exit','ct98-remote-cache-relocation-caller01.txt','ct98-remote-cache-relocation-caller01.exit','ct98-direct-object-subject-assessment.json','ct97-root-unheld-registry-cache-readonly-assessment.json','ct98-cross-repository-immutable-object-readonly-assessment.json']:
 f=scratch/name
 if f.is_file():
  body=f.read_bytes();dest=e/name
  if len(body)>60000:dest=dest.with_name(dest.name+'.xz');body=lzma.compress(body)
  dest.write_bytes(body)
recovery=json.loads((scratch/'ct98-remote-cache-relocation-01/outcome.json').read_text());assert recovery['all_original_paths_bytes_modes_preserved']and recovery['all_refs_HEAD_status_unchanged']
assert(scratch/'ct98-immutable-object-pack-consumer01/all-before-refs.txt').read_bytes()==(scratch/'ct98-remote-cache-relocation-01/all-before-refs.txt').read_bytes()
assert not(scratch/'ct98-immutable-object-pack-consumer01/all-selected-object-ids.txt').exists()
(e/'whole-local-raw-inventory.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),whole_files=all_raw,whole_new_remote_cache_pack_bytes_retained_in_RAM_as_original_path_symlink=True,no_actual_existing_object_packing_or_removal_occurred=True,scope='whole filesystem capability/cache failure and recovery evidence; Git objects remain intact, no research result or cost inference'),indent=2)+'\n')
(e/'REPORT.md').write_text('''# Capacity probes and complete reversible cache recovery

The81MB UV Typst cache file is hardlinked to the installed tool, so removing
its cache link would reclaim no data blocks. A read-only filesystem probe
fails with actual fusermount Operation not permitted; no research data is
changed. All guard/PCC direct Git-object-path checks find zero such subjects.
[pcc:unverified]

The proposed bounded object encoding operation stops at history enumeration:
git rev-list triggers partial-clone promisor fetches and ENOSPC128 before any
object selection, packing or original-object removal. Complete source and
error output remain intact. Every ref before/after that failed attempt is
byte-identical. No packing, pruning, branch reset or history rewrite occurs.
[pcc:unverified]

One newly fetched complete180,145,172-byte remote promisor cache pack is
copied to8.8GiB RAM storage, whole-byte/mode compared and retained behind its
original path. All original paths/bytes/modes, refs, HEAD and Git status are
unchanged; available space returns from0 to118,800,384 bytes. This relocates
only a regenerable remote download-cache encoding, with its full bytes still
accessible. Actual research raw/source/executables/prepared libraries and
all local/nonpromisor object encodings remain untouched. Recovery instructions
for a replaced environment are in the complete outcome receipt: never remove
refs or local/nonpromisor data. Use GIT_NO_LAZY_FETCH=1 and avoid whole-history
enumeration. These are unsigned capacity facts, not a scientific negative or
calibrated measurement. [pcc:unverified]
''');shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Capacityrecovery15: UVTypst81MBsharesinstalledinode/noblockgain; readonlymfuseprobeactualEPERM/server1/noresearchdatachange. Wholehistoryinventorytriggeredpartialclonepromisorfetch/ENOSPC128BEFOREanyobjectselection-packing-removal; completeactualsource-errorpreserved/ALLbefore-afterrefsbyteequal/no pruning-reset-historyrewrite. OneNEWcomplete180145172BremotepromisorcachepackcopiedtoRAM/wholeindependentbyte-modecompared/originalpathretainedaslink/allobjectbytes-refHEAD-Gitstatusunchanged/free0to118800384B. Fullcachebytesremainaccessible, onlyregenerableremotefetchencodingrelocated; no existinglocal-nonpromisorobjects/researchsource-raw-executables-preparedlibrariesremoved. All51583guardkeys/everyPCCsubjectdirect-objectpathassessment0, recoveryrecipeforreplacedenvironmentrecorded/GIT_NO_LAZY_FETCH=1/no furtherwholehistoryenumeration. Wholeprobe-package-failure-refs-cachemetadata rawinventory retainedforNEW26; unsignedcapacityonly/no math-cost-standing inference.']
for f in sorted(e.rglob('*')):
 if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct98-capacity-recovery15.claim.txt').write_text(cl+'\n');print(cl,flush=True)
