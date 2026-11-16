"""Record whole original CI artifact, log and actual Rust-auditor observations."""
from pathlib import Path
import hashlib,json,shutil,subprocess,zipfile
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';raw=Path('/workspace/scratch/ct82-fourth24-CI-acceptance-01');e=s/'evidence/paired-fourth24-CI-acceptance-01';e.mkdir()
observation=json.loads((raw/'audit-observation.json').read_text());assert observation['all37phases_expected']and observation['all182members_read_and_hashed']
names=['jobs-api.json','artifacts-api.json','whole-members.json','whole-run-log-members.json','log-retrieval-diagnosis.json','all-original-phase-exits.json','audit-observation.json','whole-log-cli.exit','whole-run-logs-cli.exit','connector-whole-log-failure.json','connector-whole-log-retry-failure.json']
names+=[p.name for p in raw.iterdir()if p.is_file()and p.name.startswith('actual-CI-auditor-')]
for name in names:shutil.copyfile(raw/name,e/name)
bindings=[]
with zipfile.ZipFile(raw/'whole-original-artifact.zip')as z:
 for name in z.namelist():
  if name.startswith('binding-')and name.endswith('.txt'):
   b=z.read(name);v=json.loads(b);assert v['verdict']=='pass';bindings.append(dict(original_member=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),verdict=v['verdict']))
 for name in ['consumer-proof.txt','producer-proof.txt','engine-prepared.json','engine-reused.json','paired-fourth-compiled-binary.json','paired-fourth-runtime-binary.json','auditor-compiled-custody.json','auditor-runtime-custody.json','control-compiled-custody.json','control-runtime-custody.json']:(e/name).write_bytes(z.read(name))
assert len(bindings)==20;(e/'all20-exact-binding-verdicts.json').write_text(json.dumps(bindings,indent=2)+'\n')
members={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(raw.rglob('*'))if p.is_file()}
(e/'whole-local-raw-inventory.json').write_text(json.dumps(dict(raw_root=str(raw),all_unfiltered_files=members,scope='Whole original182-member ZIP, complete run-log ZIP/all15logmembers/full8972686-byte joblog and actual original CI auditor inputs/outputs retained locally forNEW22; temporary signed URLs excluded.'),indent=2)+'\n')
shutil.copyfile(__file__,e/'original-record-command.py');shutil.copyfile('/workspace/scratch/ct82_audit_fourth24_CI_01.py',e/'original-audit-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Own70ec53e5 additive24th CI43663258742/job132657012367SUCCESS: exact artifact14141755094/35654567bytes/SHA48ff0906f647f8b853fbf2670b0aee949a162ac8ebf91c083e5cd13abbcb1809/all182members read+hashed; ALL37actualphases expected and1077originalsourceguards exact; full16wholeorderedrecords/firstnineexact/twoentireomissions101/realolddual101/allfiveexact. Both original proof gates20namedroots0trusted and ALL20exactbindingverdicts pass. Full actual test/auditor/control compiler-runtime bytes and original prepared full-library copies match. Actual downloaded CI Rustauditor onourhost wholepositive0/bothwholeomissions101/noacceptedoutputs/wholefivecontrol0. ConnectorTransportClosed twice and single-job redirected403 retained safely; materially different run-logZIP endpoint0 supplies whole8972686-byte joblog/all15logmembers. All raw/archive/source/binaries/logs retained locally forNEW22. Unsigned exact24th-only scope, no all24-current-CI/signed/execution/price promotion.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim,flush=True);Path('/workspace/scratch/ct82-fourth24-CI.claim.txt').write_text(claim+'\n')
