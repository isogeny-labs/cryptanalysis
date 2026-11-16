"""Retain literal full-census outputs and actual execution custody."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
raw=Path('/workspace/scratch/ct87-original-kernel-native-01');e=s/'evidence/original-kernel-census-native-01';e.mkdir()
assert(raw/'original.exit').read_text().strip()=='0'
supervisor=Path('/workspace/scratch/ct87-original-kernel-native01-supervisor-01')
assert Path(str(supervisor)+'.exit').read_text().strip()=='0'
phases=[]
for line in(raw/'phases.txt').read_text().splitlines():
 name,want,actual=line.split();assert want==actual;phases.append(dict(name=name,expected_exit=int(want),actual_exit=int(actual)))
assert len(phases)==13
for tag in ['TRANSPORT','VERTEX','PAIR','TRIPLE']:assert not(raw/('N4_ORIGINAL_KERNEL_'+tag+'-must-not-accept.json')).exists()
rows=json.loads((raw/'all311-compared.json').read_text());assert len(rows)==311
assert(raw/'all311-compared.json').read_bytes()==(raw/'all311-expected.json').read_bytes()
summary=rows[-1]['data'];assert rows[-1]['kind']=='N4_ORIGINAL_KERNEL_SUMMARY'
controls=rows[-2]['data'];assert rows[-2]['kind']=='N4_ORIGINAL_KERNEL_REJECTIONS'
accepted=[x for x in rows if x['kind']=='N4_ORIGINAL_KERNEL_TRIPLE' and x['data']['supported_compatible_chain']]
assert len(accepted)==1 and accepted[0]['data']['indices']==[4,1,4]
vertices=[next(x for x in rows if x['kind']=='N4_ORIGINAL_KERNEL_VERTEX' and x['data']['domain']==d and x['data']['index']==i)for d,i in enumerate([4,1,4])]
pairs=[x for x in rows if x['kind']=='N4_ORIGINAL_KERNEL_PAIR' and x['data']['supported_compatible']]
(e/'literal-whole-selected-vertices.json').write_text(json.dumps(vertices,indent=2)+'\n')
(e/'literal-supported-pairs-and-triple.json').write_text(json.dumps(dict(whole_pairs=pairs,whole_accepted_triples=accepted),indent=2)+'\n')
(e/'literal-full-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(e/'literal-rejection-controls.json').write_text(json.dumps(controls,indent=2)+'\n')
for p in sorted(raw.iterdir()):
 if p.is_file()and p.suffix not in ['.bin','.json']and p.name!='native.txt'and'entire-actual-records-omitted'not in p.name:
  b=p.read_bytes();name=p.name+'.xz'if len(b)>60000 else p.name;value=lzma.compress(b)if len(b)>60000 else b
  if len(value)<65536:(e/name).write_bytes(value)
shutil.copyfile(raw/'runtime-custody.json',e/'runtime-custody.json')
for suffix in ['start','finish','exit','txt']:shutil.copyfile(str(supervisor)+'.'+suffix,e/('supervisor.'+suffix))
inventory={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest())for p in sorted(raw.rglob('*'))if p.is_file()}
(e/'whole-unfiltered-raw-inventory.json').write_text(json.dumps(dict(root=str(raw),all_members=inventory,future_custody='NEW24; every complete input/output/omission/source/binary retained'),indent=2)+'\n')
shutil.copyfile('/workspace/scratch/ct87-current-original-checkpoint-16/observation.json',e/'exact-original-checkpoint16.json')
shutil.copyfile(__file__,e/'original-record-command.py')
(e/'outcome.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),prospective='0158c5 publishedc1cbc188 before implementation',source='811395139bbd33b75fd5697973202cd1dcc13bba',compiled_claim='4fde50',exact_original_checkpoint=dict(run=43686905905,job=132729176127,artifact=14150917768,all28_members=True,immediate_gate=0),unfiltered_native_exit=0,worker_exit=0,supervisor_exit=0,all13phases=phases,whole_ordered_records=311,whole_freeze_compare_bytes_equal=True,four_actual_whole_class_omissions='101/no accepted output',all1172_prior_hashes=0,actual_compiler_runtime_test_auditor_bytes_equal=True,literal_summary=summary,literal_rejections=controls,formal='actual-data independent Lean verdict pending',scope='unsigned finite family compatibility and supplied-source eligibility only; no full-group Jacobian evaluator or cost result'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Prospective0158c5/c1cbc188 original kernelcensus fullnative atpublished8113951/build01/exact originalcheckpoint16 run43686905905/job132729176127/artifact14150917768/all28matching/immediategate0: oneUNFILTEREDtest0/worker0/supervisor0/all13phases expected. ALL311orderedwhole records agree withpinned-input basis-span auditor reconstruction; fouractual entiretransport-vertex-pair-triple classomissions reject101/nooutput. All1172oldhashes andactual compiler/runtime test-auditorbytes exact. Entire18original modelrows/two64-coordinate4096-pair135-mask certificates andall72pairs216triples retained; sixactualmalformedinputs reject. Finite result: eligiblevertices4/2/2, kernelcompatiblepairs6/6, supportedcompatiblepairs1/1, exactlyONEsupportedcompatibletriple indices[4,1,4], cases[(2,0),(0,1),(2,0)], originalD116/39/36. Every othertriple andfailedcondition retained; no oldfixednegative orprime-onlycase changed. Independent actual-data Lean verdict pending; no full-group Jacobian evaluator, universal classification orcost conclusion. Whole raw/source/binaries retained forNEW24. Unsigned finite result.']
for p in sorted(e.iterdir()):
 assert p.stat().st_size<262144
 cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct87-kernel-native.claim.txt').write_text(claim+'\n');print(claim)
state='# Full original kernel census: one supported compatible triple\n\n'+claim+': published8113951/build01/exact originalcheckpoint16/all28/immediategate0. One unfilterednative0/worker0/supervisor0/all13phases expected; all311whole ordered records pass basis-span reconstruction, fouractual whole-class omissions101/nooutput, all1172hashes andactual binaries exact. [pcc:unverified]\n\n## What was done\nExhausted all18original vertices/72pairs/216triples withcomplete oldrows/two64-4096-135certificates andevery failedreason. Eligiblevertices4/2/2; compatiblepairs6/6; supplied-source eligible compatiblepairs1/1; exactlyone supportedcompatibletriple [4,1,4], cases(2,0)/(0,1)/(2,0), D116/39/36. Sixactualmalformedinput controls reject. All oldfixed D12/D24/D67 negatives andprime-only976f50 choices remain unchanged. [pcc:unverified]\n\n## Decisions made\nFirst independently encode actualfinite masks/transports inLean, runbothoriginal proofgates andlocalbindings, produce inspected resultvisual andpublish. Then freeze unique full-group original-source triple in a separate implementation protocol before porting thecomplete evaluator; no full-group map is claimed constructed yet. [pcc:unverified]\n\n## Open threads\nIndependent actual-data Lean coverage/verdict, visualreport, normalpublication; nextprospective full-group evaluator for originalell2773073/order11092292 withallfullcofactor/halves-corrections/population criteria, strongestknown-point andcompleteprimitive comparison retained. FuturewholecustodyNEW24. [pcc:unverified]\n\n## Errors\nNo censusnativefailure. KB theorem andformal-source queries exit127; originalhelpers arebyteexact. Metadata inspection syntaxerror was corrected beforeI/O. All historical failednative/source/format/infrastructure andmathematical negatives retained. Unsignedfinite scope; actualgeometry/program bridges andcost obligations remain. [pcc:unverified]\n\n---\n\n'
for p in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:p.write_text(state+p.read_text())
p=r/'docs/session-logs/2026-11-15.md';p.write_text(p.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
