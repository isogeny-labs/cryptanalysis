"""Original process/JSON custody and unchanged original PCC digest bookkeeping."""
from pathlib import Path
from datetime import datetime,timezone
import json,re,hashlib,shutil,lzma,subprocess,importlib.util,sys
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';ci=s/'ci_v2';full=Path('/workspace/scratch/ct58-V2-full-01');o=Path('/workspace/scratch/ct58-V2-own-CI-raw-01');source='093134ba9fbdaa4fdb50fe4bc53cd29d809500d0'
assert all((full/(x+'.exit')).read_text().strip()=='0' for x in ['native','guard'])
driver=full/'driver';assert all((driver/(x+'.exit')).read_text().strip()=='0' for x in ['original','guard','cleanliness'])
phases=[x.split() for x in(driver/'phase-index.txt').read_text().splitlines()];assert [[x[0],int(x[1])]for x in phases]==json.loads((ci/'phase-policy.json').read_text()) and len(phases)==17
for label,expected,actual in phases:assert expected==actual and (driver/(label+'.pipe-exits')).read_text().split()==[actual,'0']
assert json.loads((full/'guards.json').read_text())==dict(count=469,changed=[])
d=s/'evidence/V2-independent-full-01';d.mkdir()
for name in ['before.json','guards.json','start.txt','finish.txt','native.exit','guard.exit','original-command.sh']:shutil.copyfile(full/name,d/name)
for name in ['phase-index.txt','original.exit','guard.exit','cleanliness.exit']:shutil.copyfile(driver/name,d/('driver-'+name))
raw=(full/'native.log').read_bytes();z=lzma.compress(raw);assert lzma.decompress(z)==raw;(d/'whole-native.log.xz').write_bytes(z)
summary=dict(source=source,producer='3d49af7f3d0a28e76b79e4825c9d2324e85853d2',source_guards=469,portable_inputs=468,all_source_HEAD_cleanliness_original_process_guards=0,ordered_phase_pairs=17,positive_0_0=15,intentional_2_0=2,all_seven_V2_and_five_rho_native_records_equal_originals=True,actual_rho_five_CLI_answers_and_two_rejections=True,both_original3theorem_gates=True,all_three_exact_local_bindings='pass/unsigned',four_admission_controls='all2/nooutput/restored',scope='independent correctness only;not fullformalgeometry,costadvantage orsignedexecution')
(d/'acceptance.json').write_text(json.dumps(summary,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','V2independentfull01 exact093/producer3d ORIGINALexit0/all469guards0/driverHEADcleanliness0/all17orderedpairs15positive0/0+2intentional2/0. All7V203+5rho nativeJSON equalfrozenoriginals/actualfiveCLIanswers+two2controls/bothoriginal3theorem gates/3exactlocalbindingspass. Fouractualadmission2/nooutput/restored. Finalbytes include frozenEOF-only3202e2 correction. Wholeclosedcapture retained;unsignedcorrectness,notfullformalgeometry/cost/signedexecution.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
print('full',subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
def records(log,prefix):
    rows=[]
    for line in log.splitlines():
        m=re.search(r'\b('+prefix+r'[A-Z_]+) (\{.*\})$',line)
        if m:rows.append(dict(kind=m[1],data=json.loads(m[2])))
    return rows
canonical=lambda rows:sorted(json.dumps(x,sort_keys=True,separators=(',',':'))for x in rows)
allverdicts=[];native={};jobrows=[]
for label,run,job,marker in [('V2',43440225770,131935606787,'Completed V2/rho replay complete:'),('P1',43440225517,131935606265,'Public-target N4 replay complete:')]:
    jobs=json.loads((o/(label+'-jobs-api.json')).read_text())['structuredContent']['jobs'];assert len(jobs)==1 and(jobs[0]['id'],jobs[0]['run_id'],jobs[0]['status'],jobs[0]['conclusion'])==(job,run,'completed','success')
    log=json.loads((o/(label+'-log-api.json')).read_text())['structuredContent']['content'];assert source in log and marker in log
    (o/(label+'-whole-job.log')).write_text(log);jobrows.append(dict(run=run,job=job,status='completed',conclusion='success'))
    for line in log.splitlines():
        if '{"claim_id":' in line:allverdicts.append(json.loads(line[line.index('{"claim_id":'):]))
    native[label]=records(log,'N4_')
assert len(allverdicts)==17 and len(native['V2'])==12 and len(native['P1'])==13
assert canonical([x for x in native['V2']if x['kind'].startswith('N4_V2_')])==canonical(json.loads((ci/'expected-native-v2.json').read_text()))
assert canonical([x for x in native['V2']if x['kind'].startswith('N4_RHO_')])==canonical(json.loads((ci/'expected-native-rho.json').read_text()))
def omit_only_timing(rows):
    rows=json.loads(json.dumps(rows))
    for row in rows:
        if row['kind']=='N4_PUBLIC_ATTEMPT':
            for p in row['data']['public']['phases']:del p['wall']
            row['data']['public']['stats']=[x for x in row['data']['public']['stats']if x[0]!='wall_total']
    return rows
assert canonical(omit_only_timing(native['P1']))==canonical(omit_only_timing(json.loads((s/'evidence/unit-acceptance-01/all-native-records.json').read_text())))
spec=importlib.util.spec_from_file_location('original_pcc',r/'tools/pcc/pcc.py');pcc=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pcc;spec.loader.exec_module(pcc)
expected={}
for folder in ['lean-bindings-01','origin-lean-bindings-01','prime-field-bindings-02']:
    for b in json.loads((s/'evidence'/folder/'claims.json').read_text()):
        claim=json.loads((r/b['claim_path']).read_text());expected[claim['id']]=pcc.claim_digest(claim)
assert len(expected)==17 and set(expected)=={v['claim_id']for v in allverdicts}
for v in allverdicts:assert v['verdict']=='pass' and not v['reasons'] and v['commit']==source and v['claim_sha256']==expected[v['claim_id']]
shutil.copytree(driver/'source',o/'source');p=o/'source/cryptanalysis/experiments/chained-transfer-public-target/ci_v2/reference-01.sha256';shutil.copyfile(full/'original-reference.sha256',p);assert len([p for p in(o/'source').rglob('*')if p.is_file()])==469
for name,value in [('all-native-records.json',native),('all17-exact-verdicts.json',allverdicts),('original-PCC-canonical-digests.json',expected)]: (o/name).write_text(json.dumps(value,indent=2)+'\n')
shutil.copyfile(__file__,o/'original-collector.py')
meta=dict(at=datetime.now(timezone.utc).isoformat(),source=source,jobs=jobrows,all17_canonical_original_PCC_digests_match=True,all17_verdicts='pass/unsigned',native_records=25,V2_rho_all12_records_equal_native_originals=True,P1_all13_records_equal_originals_except_ONLY_recorded_wall_walltotal=True,whole_logs_API_and469_source_snapshots_retained=True,artifact_ZIP_downloaded=False,CI_guard_scope='original complete driver marker plus successful step;standalone CIexitfiles notdownloaded;localfull hasall469actualguards',scope='fullcorrectness observations;no fullformalgeometry/cost/signedexecution')
(o/'plan.json').write_text(json.dumps(meta,indent=2)+'\n');dest=s/'evidence/V2-own-CI-01';dest.mkdir();(dest/'observation.json').write_text(json.dumps(meta,indent=2)+'\n')
for name in ['all-native-records.json','all17-exact-verdicts.json','original-PCC-canonical-digests.json']:shutil.copyfile(o/name,dest/name)
for label in ['V2','P1']:
    raw=(o/(label+'-whole-job.log')).read_bytes();z=lzma.compress(raw);assert lzma.decompress(z)==raw;(dest/(label+'-whole-job.log.xz')).write_bytes(z)
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Exact093 independentCI BOTH V2run43440225770/job131935606787 andP1run43440225517/job131935606265 SUCCESS;all25nativeJSON matchoriginals V2rho12whole/P113ONLYrecordedwallwalltotalexcluded/rawintact. ALL17exactPCCverdictsPASS/source093/originalcanonicaldigests match. Whole2UTF8logs/API/469sources retained,CIguardinferenceoriginaldriver markers+successfulstep;no downloadedstandaloneexitfiles/ZIP. Localfull469guards0 separatelyretained. Notfullformalgeometry/costadvantage/signedexecution.']
for p in sorted(dest.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
print('CI',subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
