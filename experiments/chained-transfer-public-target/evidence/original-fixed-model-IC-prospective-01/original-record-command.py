"""Register full proof-CI acceptance and prospective fixed-model IC before any new Rust."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
assert subprocess.check_output(['git','branch','--show-current'],cwd=r,text=True).strip()=='research/chained-transfer-public-target-20261113'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()=='41e35d8c701484a6ca5406ecbf7bb83278be6073'
assert not(s/'original-fixed-model-ic-01').exists(),'protocol must precede new source'
def claim(statement,files):
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for f in sorted(files):
  if f.is_file():cmd+=['--proof','attestation:'+f.relative_to(r).as_posix()]
 value=subprocess.check_output(cmd,cwd=r,text=True).strip();print(value,flush=True);return value
raw=Path('/workspace/scratch/ct95-induced-proof-CI-acceptance-01');a=json.loads((raw/'acceptance.json').read_text());assert a['all_original_members']==50 and a['independent_actual_versioned_validator_exit']==0
e=s/'evidence/induced-transfer-proof-CI-acceptance-01';shutil.copytree(raw,e)
shutil.copyfile('/workspace/scratch/ct95_accept_induced_proof_CI_01.py',e/'actual-acceptance-command.py')
(e/'REPORT.md').write_text('''# Exact induced-transfer proof CI acceptance

At41e35d8, run43707728617/job132792341744 succeeded. The whole24,931-byte
artifact14159515706, SHA2568522fa8a217f017d87c83135a3248b893532a3380240cbbd2cee7d212bfa2d16,
retains all50 files; the whole run-log ZIP retains all12 members. All16 phases
and73 input guards pass. Both unchanged original gates audit all21 exact
declarations0trusted: nine mathematical roots plus12 structural declarations.
Every one of the nine exact statement bindings passes at the actual head.
Both actual source copies match. Independent execution of the actual
versioned validator reproduces the complete accepted verdict bytes.
[pcc:unverified]

Full ZIPs, all decoded artifact files, whole logs and fresh validation output
are retained. This is unsigned exact proof-CI acceptance of the conditional
quotient-transfer algebra, not an actual HLP/field/Frobenius/Picard/order/
program/lift identification or calibrated advantage. Native CI03 acceptance
a93f80 remains separately scoped to258; the fresh full replay at41 is a
separate observation. All evidence awaits genuineNEW26. [pcc:unverified]
''')
ci_claim=claim('Exact induced-transfer proofCI acceptance41e35d8: originalrun43707728617/job132792341744SUCCESS; whole24931B artifact14159515706 SHA8522fa8a217f017d87c83135a3248b893532a3380240cbbd2cee7d212bfa2d16/all50members/fullZIP; complete25613B runlogZIP/all12members. All16phases0/73sourceguards0/bothunchangedoriginalgates all21declarations0trusted(ninenamed+12structural)/allnineexactstatementbindings actualheadpass/actualconsumer-producerLean sourcebytes equal. Independentactualversioned receiptvalidator0 reproduceswholeacceptedverdictbytes. Allfullsource/logs/ZIPs/decodedfiles retainedforNEW26. Unsignedconditionalquotientalgebraonly/no actualHLP-field-Frobenius-Picard-order-program-liftbridge/calibratedcost/global-currentCI/ECDLPadvantage/signedpromotion.',list(e.rglob('*')))
Path('/workspace/scratch/ct96-induced-proof-CI-acceptance.claim.txt').write_text(ci_claim+'\n')
ff=Path('/workspace/scratch/ct95-single-consumer-ledger-fast-forward-01');d=s/'evidence/single-consumer-ledger-normal-FF-01';d.mkdir()
for name in ['outcome.json','original-command.py','switch.txt','switch.exit','normal-fast-forward.txt','normal-fast-forward.exit','normal-publication-caller.txt','normal-publication-caller.exit','normal-multi-publication-caller02.txt','normal-multi-publication-caller02.exit']:
 shutil.copyfile(ff/name,d/name)
shutil.copytree(ff/'direct-parent-publisher-failed01',d/'direct-parent-publisher-failed01');shutil.copytree(ff/'normal-multi-commit-publication02',d/'normal-multi-commit-publication02')
shutil.copyfile('/workspace/scratch/publish_normal_git_fast_forward.py',d/'normal-multi-commit-publisher.py')
ff_claim=claim('Singleconsumerledger ordinaryFF01: originalresearch/chained-transfer-public-target-20261113 normallyadvances25801fe-to41e35d8 throughfouralreadyexistingcommits; localFF0/normalnonforcepublication0/remoterefindependently41. Entireold457703Bledgerprefix retained in466187Bledger withhashes; noappendonoriginalbranchbeforeFF/no rebase-rechain-force-merge. Soleledgerwriter noworiginalresearchbranch. Initialgenericpublisher direct-parentassertion1 beforepush preserved; correctedmulti-commit helper retainsancestry/expectedremotehead/--no-force checks. Branchcustodyonly/noCI-math-performance-standinginference.',list(d.rglob('*')))
Path('/workspace/scratch/ct96-single-ledger-FF.claim.txt').write_text(ff_claim+'\n')
pros=Path('/workspace/scratch/ct96-original-fixed-model-IC-prospective-01');p=s/'evidence/original-fixed-model-IC-prospective-01'
for f in pros.iterdir():
 if f.is_file():shutil.copyfile(f,p/f.name)
proposal=Path('/workspace/scratch/ct96-original-fixed-model-IC-proposal-01');report=s/'reports/original-fixed-model-IC-proposal-01';report.mkdir()
assert(proposal/'render.exit').read_text().strip()==(proposal/'raster.exit').read_text().strip()=='0'
assert(proposal/'report.pdf').stat().st_size==56847
for name in ['report.typ','report.pdf']:shutil.copyfile(proposal/name,report/name)
inputs=[s/'ORIGINAL_FIXED_MODEL_IC_PROTOCOL_01.md',p/'literal-input-pins.json',p/'all1440-immutable-prior-inputs.sha256',p/'primary-KB-vault-review.json']
(report/'render-inputs.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),input_files=[dict(path=str(f),bytes=f.stat().st_size,sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest())for f in inputs],full_primary_texts=['/workspace/scratch/ct90-prime-descent-primary-review-01/diem-plane-curves-2012.txt','/workspace/scratch/ct90-prime-descent-primary-review-01/tian-cover-2020v1.txt'],protocol_before_new_Rust=True,source_consumer='41e35d8c701484a6ca5406ecbf7bb83278be6073',source_root='66bc048730248baf4f4fc34542c1f489c60ffb3a',scope='prospective editable report source/input links; no outcome inferred'),indent=2)+'\n')
(report/'visual-inspection.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),actually_opened_final_pages=2,pdf_bytes=56847,pdf_sha256=hashlib.file_digest((report/'report.pdf').open('rb'),'sha256').hexdigest(),checks='both pages fully legible; fixedmodeltable/actualopaquechain-versus-independentcheck table/solverboundary/complete60population15casecriteria/input-omission-controls/bounds-cost-limitations readable; no clipping',rasters={f.name:dict(bytes=f.stat().st_size,sha256=hashlib.file_digest(f.open('rb'),'sha256').hexdigest())for f in proposal.glob('page-*.png')}),indent=2)+'\n')
(report/'original-render.py').write_text('from pathlib import Path\nimport typst\np=Path(__file__).resolve().parent\ntypst.compile(str(p/"report.typ"),output=str(p/"report.pdf"),root=str(p))\n')
(report/'REPORT.md').write_text('''# Prospective IC on the fixed original-prime models

The [inspected two-page proposal](report.pdf) and
[protocol](../../ORIGINAL_FIXED_MODEL_IC_PROTOCOL_01.md) freeze all3 D116/39/36
models and all60 IC attempts before new Rust. Acceptance requires correct
target and independent-source verification for all15 public cases; retain
every unsuccessful attempt. The existing literal class-input solver remains
unchanged; only the fixed original-geometry context is adapted. Source input
construction uses the actual opaque Jacobian chain and independent point
maps. The runtime solver receives no scalar witness or source DLP fallback.
[pcc:unverified]

Both final56,847-byte PDF pages were opened; the complete source-input and
primary-review links are in render-inputs.json. All1440 old inputs remain
immutable. Complete primitive/setup/known-point/reference costs, actual model/
program proof bridges and live admission remain explicit; no performance,
novelty or signed outcome is asserted. Four KB commands return127; the vault
remains VLT1-locked and clean at8edec422. Whole source/data/failures/executables/
prepared libraries/reports remain queued for genuineNEW26. [pcc:unverified]
''')
shutil.copyfile(__file__,p/'original-record-command.py')
attrs=r/'.gitattributes';attrs.write_text(attrs.read_text().rstrip()+'\n'+(report/'report.pdf').relative_to(r).as_posix()+' binary\n')
protocol_claim=claim('Prospective original-fixed-model IC protocol01 BEFOREanynewRustsource: retainexactoriginalE2-E3-E4 cases2,0-0,1-2,0/D116-39-36/roots89-40-6/P0s andmasks/KF223cubic/ell2773073/fullorder11092292/allfivepublicinputs/all1440priorhashes. Reusewholeliteralnew-targetclasssolver unchanged withfixedoriginalgeometryNormNew context; actualopaqueJ2-toJ3-J4 packets independentlychecked againstsourcepoint-Phi. SolveronlypublicG-Q/context/ell/params/seed/no scalar-lift-DLPfallback. FreezeALL60attempts3models5public4FB30-36-48-64/seeds102-105/oldparams; requireall15casesverifiedtargetandoriginalsource, preserveallfailures/actualwholeclassomissions/controls/rawwalls/counters. Whole900sserial2GiB/boundedcompile/exactpreparedclosure-runtimecustody/checkpoint/proof/replay/genuineNEW26. Both56847BproposalPDFpages actuallyopened; primariesDiem2012Theorem1/Tian2020 reviewed, fourKB127/vaultlocked8edec422-clean/headeronly4. Completeprimitive-setup-knownpoint-matchedreference/liveadmission unknown; no outcome-novelty-calibrated-ECDLP-signedclaim.',[s/'ORIGINAL_FIXED_MODEL_IC_PROTOCOL_01.md',*p.rglob('*'),*report.rglob('*')])
Path('/workspace/scratch/ct96-original-fixed-model-IC-protocol.claim.txt').write_text(protocol_claim+'\n')
state='# Fresh induced-proof CI accepted; fixed original-model IC prospect frozen\n\n'+ci_claim+' acceptsrun43707728617/job132792341744 at41e35d8/all50files/full24931BZIP/all12runlogs/16phases/73guards/both21declarations0trusted/allnineexactbindings/independentwholeverdictreproduction. '+ff_claim+' recordsordinary258→41FF preservingwholeledgerprefix; originalresearchbranchissoleledgerwriter. '+protocol_claim+' freezesfixedoriginal-modelIC BEFOREnewRust; both56847BproposalPDFpagesopened. [pcc:unverified]\n\n## What was done\nCompleteCI03a93f80 at258/sevenwholepopulations/all749files/153phases/24omissions/both70checks54names16copies/all70bindings/1440guards/actualprepared-runtimecustody retained. Conditionaleddc37/resultd90ad1 sourceproof complete; Root66bc048 mirrorsallwith343sciencehashesunchanged. Freshfullrun43707728514 at41 isseparate; no unobservedconclusion. FourKB127/vault8edec422 lockedclean/primaryDiem-Tian passages retained. [pcc:unverified]\n\n## Decisions made\nPublishthisprotocol/proposal BEFOREcreating original-fixed-model-ic-01 Rustcrate. Keepall60attempts3models5public4FBsettings, requireall15verifiedcases; preserveanyfailure. Literalexistingclasssolverunchanged/contextonlyadapter, actualopaqueJacobianchainplusindependentpoint-Phi equality, scalaranswersoutsideallruntimeinputs. No model/kernel/origin/prime/publicreselection. [pcc:unverified]\n\n## Open threads\nImplement/build/prove/native/auditfixedoriginalIC underpublishedprospect; nextadaptoldnormassistedsampler andcompleteprimitive/setup/knownpoint/strongmatchedreferencecensus. GenuineNEW26 ofwholect92-96 includingoriginalfullZIP749files/fulljoblog/freshproofZIPs/source/exes/fullpreparedcopies/allfailures/reports. Storage83MiBfree; onlyunheldderivedcacheorwholeclosedidenticalbytesmaybereclaimed. Cold12018complete102missing/124/root124/clock101/global-mainledger/livebudget-capacity-isolation-image/review/signing gaps remain. No calibrated/ECDLPadvantage/globalCI/signedpromotion. [pcc:unverified]\n\n## Errors\nAllcustodyprojection/hostkernelmissing-env101/transport403/materializer/publisherdirectparentfailures retained. RootoneattestedAPIJSONliteralEOFwhitespace2 preservedwithoneexactperfileattribute; no source/formula/claimhash/gatecriterion changed. Priorfullnative693failedprefix/test-onlyCRToraclefix andalloldnegativegeometry/proof/cold/globalresults remain. [pcc:unverified]\n\n---\n\n'
for f in [r/'.resume/RESUME.md',s/'CHECKPOINT.md',s/'RESEARCH_QUEUE.md']:f.write_text(state+f.read_text())
f=r/'docs/session-logs/2026-11-15.md';f.write_text(f.read_text().rstrip()+'\n\n'+state.split('\n---')[0].rstrip()+'\n')
