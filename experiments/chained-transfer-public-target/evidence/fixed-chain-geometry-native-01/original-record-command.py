"""Project literal native observations and custody; no research arithmetic."""
from pathlib import Path
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';raw=Path('/workspace/scratch/ct82-fixed-chain-geometry-native-01')
names=['immediate-original-gate','runtime-custody','initial-prior-inputs','native','final-runtime-bytes','final-prior-inputs','original']
assert all((raw/(name+'.exit')).read_text().strip()=='0'for name in names)
text=(raw/'native.txt').read_text();assert text.count('test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;')==1
rows=[]
for line in text.splitlines():
 if 'N4_' in line:
  kind,body=line[line.index('N4_'):].split(' ',1);rows.append(dict(kind=kind,data=json.loads(body)))
expected=['N4_CHAIN_OLD_LITERAL_PARITY','N4_NONDUAL13_KERNEL_GATE','N4_NEXT13_KERNEL_GATE','N4_TWIST_ORDER_CANDIDATE','N4_TWIST_GENERATOR_ATTEMPTS','N4_FOURTH_KERNEL_GATE','N4_CHAIN_ACTUAL_ELLIPTIC_CERTIFICATES']
expected+=['N4_CHAIN_FIXED_GEOMETRY','N4_CHAIN_ACTUAL_REJECTIONS']*3
assert [x['kind']for x in rows]==expected
(raw/'all-thirteen-whole-records.json').write_text(json.dumps(rows,indent=2)+'\n')
e=s/'evidence/fixed-chain-geometry-native-01';e.mkdir()
for p in sorted(raw.iterdir()):
 if p.is_file()and p.suffix=='.exit':shutil.copyfile(p,e/p.name)
for name in ['runtime-custody.json','start.txt','finish.txt','original-command.sh']:shutil.copyfile(raw/name,e/name)
models=[x['data']for x in rows if x['kind']=='N4_CHAIN_FIXED_GEOMETRY'];rejections=[x['data']for x in rows if x['kind']=='N4_CHAIN_ACTUAL_REJECTIONS']
summary=dict(source='70ec53e5a297a47e8c933dad1b58e870211b16fa',build='ct82-fixed-chain-geometry-build-02',original_checkpoint=dict(run=43663258495,job=132657011870,artifact=14141210588,sha256='08c474581e04a127bdca2e99a0d114729b63b905ec25a4e2bf7bb50d36100830',all28members_and_remote_local_gate=0),all_original_phase_exits={name:int((raw/(name+'.exit')).read_text())for name in names},whole_ordered_record_tags=expected,models=[dict(index=x['index'],source=x['source'],mask=x['mask'],case=x['case'],all224_line_offsets=x['all224_line_offsets'],separate_prime_origin=x['separate_prime_origin'],separate_quadratic_origin=x['separate_quadratic_origin'],quadratic_origin_calls=x['quadratic_origin_calls'],all_point_controls=x['all_point_controls'],all_correction_fibres=x['all_correction_fibres'])for x in models],all_actual_rejections=rejections,old_known_answer_packet_panel=rows[0]['data']['all_actual_packets'],scope='One unfiltered PhaseA test0; actual old literal parity and all three frozen geometry models. The224-line origins are not the PhaseC exceptional-class workload. No complete chained Jacobian evaluation or calibrated cost result yet. Full raw source/binary/stdout/whole13records retained locally forNEW22; unsigned.')
(e/'literal-results-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
members={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in sorted(raw.rglob('*'))if p.is_file()}
(e/'whole-local-raw-inventory.json').write_text(json.dumps(dict(raw_root=str(raw),all_unfiltered_files=members,future_custody='NEW22; no new remote read/publication claimed'),indent=2)+'\n');shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Fixed new-instance geometry native01 on published70ec53e5/build02/exact originalcheckpoint43663258495/job132657011870/art14141210588/all28members plus immediate original localgate0: ONE unfiltered PhaseA test0/allseven phase exits0/full actual compiler-runtime bytes equal/all1060oldsourceguards0. All13 whole ordered records retained: old literal six-model/wholepacket/origin parity and ALLthree fixed C2nu/C3nu/C4nu actual source-certified prime/quadratic models, ALL224lineorigins each/separatequadraticorigins, actual NormPhi2 onallfourE2 and generator controls, actual TWOtwo-point correction-image fibres permodel, actual foreign order/prime/source/frozenmask/zerogenerator rejections. These are line-origin checks, not PhaseC exceptional-class coverage. CompleteJacobian chain/672exceptionals/fullgroup inverses/sourceoperationvectors remain open under5caf67. Unsigned/localrawNEW22/no priced or signed promotion.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(claim,flush=True);Path('/workspace/scratch/ct82-geometry-native.claim.txt').write_text(claim+'\n')
