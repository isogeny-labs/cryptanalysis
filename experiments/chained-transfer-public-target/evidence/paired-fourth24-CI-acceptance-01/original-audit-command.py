"""Whole artifact byte checks and execution of its original published Rust auditor."""
from pathlib import Path
import hashlib,json,lzma,os,subprocess,zipfile
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';out=Path('/workspace/scratch/ct82-fourth24-CI-acceptance-01');a=out/'audit-input';a.mkdir()
inventory=json.loads((out/'whole-members.json').read_text());jobs=json.loads((out/'jobs-api.json').read_text())['structuredContent']['jobs'];assert len(jobs)==1 and jobs[0]['id']==132657012367 and jobs[0]['conclusion']=='success'
assert(out/'whole-run-logs-cli.exit').read_text().strip()=='0'and(out/'whole-job-from-run-zip.log').stat().st_size==8972686
with zipfile.ZipFile(out/'whole-original-artifact.zip')as z:
 def data(name):
  b=z.read(name);assert len(b)==inventory[name]['bytes']and hashlib.sha256(b).hexdigest()==inventory[name]['sha256'];return b
 assert data('original.exit')==b'0\n'and data('final-source-guards.exit')==b'0\n'
 phases=[line.split()for line in data('phases.txt').decode().splitlines()];assert len(phases)==37 and all(expected==actual for _,expected,actual in phases)
 assert data('original-reference.sha256')==(s/'ci_paired_fourth/reference-01.sha256').read_bytes()
 for line in data('original-reference.sha256').decode().splitlines():
  h,p=line.split('  ',1);assert hashlib.sha256((r/p).read_bytes()).hexdigest()==h
 for prefix,compiled,runtime in [('paired-fourth','paired-fourth-original-compiled-test.bin','paired-fourth-actual-runtime-test.bin'),('auditor','actual-compiled-auditor.bin','actual-runtime-auditor.bin'),('control','actual-compiled-old-dual-control.bin','actual-runtime-old-dual-control.bin')]:
  assert inventory[compiled]==inventory[runtime]and data(compiled)==data(runtime)
  cm=json.loads(data(prefix+'-compiled-binary.json'if prefix=='paired-fourth'else prefix+'-compiled-custody.json'));rm=json.loads(data(prefix+'-runtime-binary.json'if prefix=='paired-fourth'else prefix+'-runtime-custody.json'))
  assert cm['bytes']==inventory[compiled]['bytes']and cm['sha256']==inventory[compiled]['sha256']and rm['sha256']==cm['sha256']
 prepared=json.loads(data('engine-prepared.json'));reused=json.loads(data('engine-reused.json'));assert reused['actual_reuse']and reused['Cargo_artifact']['fresh']
 for item in prepared['files']:
  name='actual-prepared-original-engine/'+Path(item['copy']).name;assert inventory[name]==dict(bytes=item['bytes'],sha256=item['sha256'])
  assert hashlib.sha256(data(name)).hexdigest()==item['sha256']
 for side in ['consumer','producer']:
  statuses=[name for name in inventory if name.startswith(side+'-proofs/')and name.endswith('/status')];assert len(statuses)==5
  for name in statuses:assert data(name).decode().split()[0]=='PASS'
 for name,existing in [('old-nine-expected.json',Path('/workspace/scratch/ct81-paired-fourth-native-01/old-nine.json')),('all-sixteen-expected.json',Path('/workspace/scratch/ct81-paired-fourth-native-01/all-sixteen-expected.json'))]:
  b=data(name);assert b==existing.read_bytes();os.link(existing,a/name)
 assert data('all-sixteen-expected.json')==lzma.decompress((s/'paired-fourth-preflight/expected-native-01.json.xz').read_bytes())
 assert data('whole-five-original-control.json')==lzma.decompress((s/'paired-fourth-preflight/expected-old-dual-control-01.json.xz').read_bytes())
 names=['actual-compiled-auditor.bin','paired-fourth-native.txt','N4_FOURTH_PUBLIC-entire-actual-record-omitted.txt','N4_FOURTH_MATCHED_ENDPOINTS-entire-actual-record-omitted.txt','actual-old-third-dual.txt','whole-five-original-control.json']
 for name in names:(a/name).write_bytes(data(name))
 (out/'all-original-phase-exits.json').write_text(json.dumps(phases,indent=2)+'\n')
auditor=a/'actual-compiled-auditor.bin';os.chmod(auditor,0o755)
def run(label,wanted,args):
 q=subprocess.run(['timeout','120',str(auditor),*map(str,args)],cwd=r,capture_output=True);(out/(label+'.txt')).write_bytes(q.stdout+q.stderr);(out/(label+'.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==wanted;print(label,q.returncode,flush=True)
run('actual-CI-auditor-positive',0,['--compare',a/'old-nine-expected.json',a/'all-sixteen-expected.json',a/'paired-fourth-native.txt',a/'whole-positive-accepted.json'])
accepted=a/'whole-positive-accepted.json';expected=a/'all-sixteen-expected.json';assert accepted.read_bytes()==expected.read_bytes();temp=a/'exact-accepted-link.tmp';os.link(expected,temp);os.replace(temp,accepted)
for tag in ['N4_FOURTH_PUBLIC','N4_FOURTH_MATCHED_ENDPOINTS']:
 destination=a/(tag+'-must-not-accept.json');run('actual-CI-auditor-'+tag+'-omission',101,['--compare',a/'old-nine-expected.json',expected,a/(tag+'-entire-actual-record-omitted.txt'),destination]);assert not destination.exists()
run('actual-CI-auditor-whole-five-control',0,['--control',a/'old-nine-expected.json',a/'actual-old-third-dual.txt',a/'whole-five-control-accepted.json'])
assert(a/'whole-five-control-accepted.json').read_bytes()==(a/'whole-five-original-control.json').read_bytes()
(out/'audit-observation.json').write_text(json.dumps(dict(source='70ec53e5a297a47e8c933dad1b58e870211b16fa',run=43663258742,job=132657012367,artifact=14141755094,bytes=35654567,sha256='48ff0906f647f8b853fbf2670b0aee949a162ac8ebf91c083e5cd13abbcb1809',all182members_read_and_hashed=True,all37phases_expected=True,all1077original_guards=True,both_original_proof_gates_and20bindings=0,all_actual_test_auditor_control_compiler_runtime_bytes_equal=True,whole_prepared_original_library_copies_equal=True,actual_original_CI_Rust_auditor_positive=0,both_entire_record_omissions=101,no_accepted_negative_outputs=True,actual_original_CI_Rust_auditor_whole_five_control=0,whole_full_job_log_bytes=8972686,whole_run_log_ZIP_and_all_members_preserved=True,original_connector_transport_and_job_download_failures_preserved_safely=True,scope='Unsigned exact24th workflow science/byte audit; no all24-current workflows or signed/execution/performance promotion. Full ZIP/source/logs retained locally forNEW22.'),indent=2)+'\n')
