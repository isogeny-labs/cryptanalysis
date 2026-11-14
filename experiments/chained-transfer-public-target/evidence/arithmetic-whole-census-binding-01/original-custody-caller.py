from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,io,lzma,os,shutil,subprocess,tarfile
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';raw=Path('/workspace/scratch/ct72-census-binding-process-controls-01');d=s/'evidence/arithmetic-whole-census-binding-01';d.mkdir()
assert(raw/'build.exit').read_text().strip()=='0'and(raw/'controls.exit').read_text().strip()=='0'
for name,expected in [('positive',0),('count-plus-one',101),('metadata-changed',101)]:assert(raw/'actual-processes'/(name+'.exit')).read_text().strip()==str(expected)
# Whole output/source/control-input tree, with actual binaries separately retained.
cap=Path('/workspace/scratch/ct72-census-binding-output-01');cap.mkdir();shutil.copytree(raw/'actual-processes',cap/'actual-processes')
for name in ['controls.rs','build.txt','build.exit','controls.txt','controls.exit','whole-golden.json']:shutil.copyfile(raw/name,cap/name)
shutil.copyfile(s/'arithmetic-audit/taps/src/bin/census.rs',cap/'actual-census.rs');shutil.copyfile(s/'ARITHMETIC_REPLAY_COUNTER_BINDING_01.md',cap/'prospective-protocol.md');shutil.copyfile('/workspace/scratch/ct72-whole-census-golden-custody-01.json',cap/'golden-custody.json')
cache=Path(str(raw)+'-build-cache');src=cache/'release/census';dest=raw/'actual-census-executable.bin';dest.write_bytes(src.read_bytes())
(cap/'actual-command-and-binaries.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),command='controls actual-census-executable native04/native.txt fullgolden.json fresh-actual-processes',rust='1.99.1/release/offline/locked',actual_census_binary=dict(path=str(dest),bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()),actual_driver=dict(path=str(raw/'controls'),sha256=hashlib.sha256((raw/'controls').read_bytes()).hexdigest()),source_manifest='reference-02/21runtime+self22',whole_original_native_log_genuine='92a00d/420904/71856B XZ',scope='ALL control source/input/output bytes inonewholearchive; actualbinaries separatelyretained/pinned, not a performancecomparison'),indent=2)+'\n')
b=io.BytesIO();members={}
with tarfile.open(fileobj=b,mode='w',format=tarfile.PAX_FORMAT)as tf:
 for p in sorted(cap.rglob('*')):
  if p.is_file():
   data=p.read_bytes();name=str(p.relative_to(cap));members[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest());tf.add(p,arcname=name,recursive=False)
tar=b.getvalue();z=lzma.compress(tar);(d/'whole-raw.tar.xz').write_bytes(z);assert len(z)<=65536,len(z)
with tarfile.open(fileobj=io.BytesIO(lzma.decompress(z)))as tf:
 assert set(tf.getnames())==set(members)
 for p in tf.getmembers():assert hashlib.sha256(tf.extractfile(p).read()).hexdigest()==members[p.name]['sha256']
(d/'members.json').write_text(json.dumps(members,indent=2)+'\n');(d/'observed.json').write_text(json.dumps(dict(actual_processes=[dict(control=n,expected=e,actual=int((raw/'actual-processes'/(n+'.exit')).read_text()))for n,e in [('positive',0),('count-plus-one',101),('metadata-changed',101)]],complete_original_census_rows=7113,whole_archive_bytes=len(z),whole_archive_sha256=hashlib.sha256(z).hexdigest(),golden_whole_XZ_bytes=29960,whole_native_log_retained_genuine=True,any_masks=False,no_original_or_tap_arithmetic_changes=True,scope='unsigned/no executionproof/no price/wholelogstillgenuine; new21source+self22/freshfull18CIpending'),indent=2)+'\n')
c=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Whole-census binding nativeprocesscontrols underprospectiveprotocol: actualbuild0/actualdriver0; acceptedWHOLE7113rowcensus+ALLmetadata exact0; copiedfirstcount+1 rejects101 andcopiedschema metadatachange rejects101; NOMASKS. Allsource/inputs/stdout/stderr/exits retainedONEwholearchive+completeindex/everymemberroundtrip; actualdriver/censusbinaries separatelykept/pinned. DerivedgoldenONEcompleteJSON29960BXZ; WHOLE71856BnativeXZ remainsgenuine92a00d/420904/no splitpruneforpolicy. Currentnewsource21+self22/replayreference02, historical19input01keptunchanged; no arithmetic/solver/tapexpression/old17workflow/original785/verifierchange. Freshfull/exact18CIpending;allunsigned/no calibratedcost/stagewin/advantage.']
for p in sorted(d.iterdir()):c+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(c,cwd=r,text=True).strip();Path('/workspace/scratch/ct72-census-binding-controls.claim').write_text(cl+'\n');print(cl,'wholeoutputarchive',len(z),flush=True)
files=[p for p in cache.rglob('*')if p.is_file()];receipt=dict(at=datetime.now(timezone.utc).isoformat(),removed_only_closed_derived_cache=str(cache),files=len(files),bytes=sum(p.stat().st_size for p in files),all_actual_sources_inputs_outputs_and_binaries_kept=True);shutil.rmtree(cache);Path('/workspace/scratch/ct72-census-derived-cache-cleanup-01.json').write_text(json.dumps(receipt,indent=2)+'\n')
