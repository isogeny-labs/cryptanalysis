"""Record actual original publication and project exactly two original manifest entries."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,os,shutil,subprocess
r=Path('/workspace/crypto');c=Path('/workspace/cryptanalysis');s=r/'research/chained_jacobian_transfers_20261110';cs=c/'experiments/chained-transfer-public-target';scratch=Path('/workspace/scratch')
source='99cb2b204da7adc85345d3a7e052a9b95f09a1b5';bot='b7bc54fcba9ad9a7ac901037c263c0b8e8a300a8';run=43720549312;job=132831389944
control=scratch/'ct99-whole-closed-science-handoff-26';ff=scratch/'ct99-handoff26-artifact-ff-02';actual=scratch/'ct99-handoff26-actual-publication-01'
assert(scratch/'handoff26-ff-supervisor-02/original.exit').read_text().strip()=='0'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==bot
receipt=json.loads((ff/'dirty-preservation.json').read_text());assert receipt['all_current26_paths_unchanged']and receipt['all_owned_bytes_unchanged']and receipt['whole_archive_ordered_reassembly']
assert receipt['guard26_count']==58919 and len(receipt['all_current26_link_paths_and_targets'])==177 and receipt['original_remote_replays_before_bot']==9 and len(receipt['exact_changed_paths'])==11
jobs=json.loads((actual/'jobs-api.json').read_text())['structuredContent']['jobs'];assert len(jobs)==1 and jobs[0]['id']==job and jobs[0]['conclusion']=='success'
assert all((ff/(name+'.exit')).read_text().strip()=='0'for name in ['fetch','exact-ff','artifact','wiring'])
e=s/'evidence/public-n4-original-IC-sampler-publication-26';e.mkdir()
for p in sorted(ff.iterdir()):
    if p.is_file():shutil.copyfile(p,e/p.name)
for name in ['jobs-api.json','whole-job-api.json','bot-commit-api.json','branch-head-api.json']:shutil.copyfile(actual/name,e/name)
(e/'whole-job.log.xz').write_bytes(lzma.compress((actual/'whole-job.log').read_bytes()))
for p,name in [(scratch/'ct99_handoff26_fast_forward_02.py','original-FF-command.py'),(scratch/'ct99_handoff26_owned_baseline_01.py','original-owned-command.py'),(control/'owned-before.json','owned-before.json'),(scratch/'ct99-root26-payload-publication-01/receipt.json','normal-push-receipt.json'),(scratch/'ct99-root26-payload-publication-01/push.log','normal-push.log'),(scratch/'handoff26-preparation-supervisor-01/whole-caller.txt','whole-preparation-caller.txt'),(scratch/'handoff26-preparation-supervisor-01/original.exit','whole-preparation-caller.exit')]:shutil.copyfile(p,e/name)
for p,name in [(scratch/'handoff26-ff-supervisor-01/whole-caller.txt','failed-FF01-whole-caller.txt'),(scratch/'handoff26-ff-supervisor-01/original.exit','failed-FF01-caller.exit'),(scratch/'ct99_handoff26_fast_forward_01.py','failed-FF01-original-command.py'),(scratch/'ct99-handoff26-bounded-object-prefetch-01/outcome.json','bounded-three-blob-prefetch.json'),(scratch/'ct99_prefetch_exact_bot_metadata_01.py','bounded-three-blob-prefetch-command.py')]:shutil.copyfile(p,e/name)
identity=json.loads((s/'evidence/public-n4-original-IC-sampler-handoff-26/archive-parts.json').read_text());assert identity['bytes']==136572156 and identity['unfiltered_nonsecret_members']==7357
publication=dict(at=datetime.now(timezone.utc).isoformat(),run=run,job=job,source=source,bot=bot,exact_parent=source,original_remote_replays_BEFORE_bot=9,exact_changed_paths=receipt['exact_changed_paths'],all58919_inputs_177_links_ownedbytes=True,whole_archive_bytes=identity['bytes'],whole_archive_sha256=identity['sha256'],whole_unfiltered_archive_members=7357,explicit_whole_closed_roots=68,consumer_delta_files_since_genuine25=3777,all_parts_and_members_roundtripped=True,two_plain_Git_objects_unchanged=True,plain_objects='complete69112B PDF and119B in-root privacy manifest; separate outside-root private authorization inventory also retained in producer Git',all51583_prior25_keys_176_links_both_ledger_prefixes=True,normal_fetch_FF_artifact_wiring=0,hold26='RELEASED',scope='unsigned whole byte custody; native IC7df2ae/sampler4fd903/inducedproofeddc37/fullCIa93f80/proofCI39bb46 retain exact original scopes')
(e/'publication.json').write_text(json.dumps(publication,indent=2)+'\n');shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Actual genuine26 original publisher43720549312/job132831389944SUCCESS: NINE remote objects replayed BEFOREactualbotb7bc54fcba/direct99cb2b204d/exact11paths; two plain Git objects including full69112BPDF unchanged. All58919heldinputs/177links/ownedbytes, whole ordered136572156Barchive/all7357members/68closedroots/every3777consumerdeltafiles sincegenuine25 preserved; all51583prior25keys176links/both exactledgerprefixes/priorarchives held. Full749CIartifact/logs, inducedproof andproofCI, nativeIC100/sampler101/fullrejectedreports, source/executables/fullpreparedcopies/checkpoints20-21/reportdrafts/build-proof-transport-authoring-capacity failures retained. Original policy/tools unchanged, private authorization metadata retained locally with explicit inventories. Normalfetch-FF-artifact-wiring0/HOLD26RELEASED. Full100/101fixture objects genuinely published; completePDF ordinary producer Git as originalpolicy requires. Unsigned byte custody only.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
rootclaim=subprocess.check_output(cmd,cwd=r,text=True).strip();print(rootclaim,flush=True)
p=r/'.gitattributes';p.write_text(p.read_text().rstrip()+'\n'+(e/'normal-push.log').relative_to(r).as_posix()+' -whitespace\n')
origin=s/'evidence/public-n4-original-IC-sampler-handoff-26/.artifacts.json';manifest=json.loads(origin.read_text());objects={Path(row['path']).name:row for row in json.loads((origin.parent/'objects.json').read_text())}
pairs=[('original-fixed-model-IC-whole100.json.xz','original-fixed-model-ic-01','ct96-original-fixed-model-IC-native-01',100),('original-fixed-model-sampler-whole101.json.xz','original-fixed-model-sampler-01','ct97-original-fixed-model-sampler-native-01',101)]
docs=c/'docs/research-artifacts/chained-transfer/original-IC-sampler-26';docs.mkdir();projection=dict(manifest);projection['files']={name:manifest['files'][name]for name,_,_,_ in pairs}
(docs/'.artifacts.json').write_text(json.dumps(projection,indent=2)+'\n');(docs/'.gitignore').write_text(''.join(name+'\n'for name,_,_,_ in pairs))
aliases={}
for name,package,raw,count in pairs:
    p=docs/name;shutil.copyfile(objects[name]['local_original'],p);assert p.stat().st_size==objects[name]['bytes']and hashlib.file_digest(p.open('rb'),'sha256').hexdigest()==objects[name]['sha256']
    assert projection['files'][name]==dict(bytes=p.stat().st_size,sha256=objects[name]['sha256'])
    assert lzma.decompress(p.read_bytes())==(scratch/raw/'all-whole-compared.json').read_bytes()
    alias=cs/package/'expected-native-01.json.xz';assert not alias.exists()and not alias.is_symlink();alias.symlink_to(os.path.relpath(p,alias.parent));assert alias.read_bytes()==p.read_bytes();aliases[alias.relative_to(c).as_posix()]=os.readlink(alias)
    assert subprocess.run(['git','check-ignore','-q',p.relative_to(c).as_posix()],cwd=c).returncode==0
e=cs/'evidence/genuine-original-IC-sampler-publication-26';e.mkdir();shutil.copyfile(origin,e/'original-root-manifest.json');shutil.copyfile(docs/'.artifacts.json',e/'canonical-projection-manifest.json');shutil.copyfile(ff/'dirty-preservation.json',e/'original-terminal-guard-receipt.json');shutil.copyfile(__file__,e/'original-command.py')
pdfrel='research/chained_jacobian_transfers_20261110/evidence/public-n4-original-IC-sampler-handoff-26/original-fixed-model-sampler-result-01.pdf';pdf=r/pdfrel
pdfurl='https://github.com/isogeny-labs/crypto/blob/'+bot+'/'+pdfrel
(e/'projection.json').write_text(json.dumps(dict(rootclaim=rootclaim,publication=publication,exact_two_original_manifest_entry_dicts=projection['files'],canonical_docs=docs.relative_to(c).as_posix(),transparent_relative_aliases=aliases,whole_XZ_roundtrips_equal_entire_actual100_and101=True,no_new_consumer_remote_read_claimed=True,full_PDF=dict(url=pdfurl,bytes=pdf.stat().st_size,sha256=hashlib.file_digest(pdf.open('rb'),'sha256').hexdigest(),publication='ordinary producer Git under original PDF keep policy; no consumer manifest invented'),future_custody='NEW27;26historical',scope='unsigned byte custody; original mathematical/program/proof/cost scopes retained'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Consumer genuine26 canonical projection: original43720549312/job132831389944SUCCESS nine actual remote replays BEFOREb7bc54fcba/direct99cb2b204d/exact11paths/all58919inputs177linksownedbytes/whole136572156Barchive7357members68roots/normalFF-artifact-wiring0/HOLD26RELEASED. TWO original manifest entry dictionaries copied exactly with two transparent relative aliases; whole lossless XZ roundtrips equal entire actual originalIC100 andpairedsampler101 populations including allrejectedreports, no filtering. Full69112BPDF remains unchanged in ordinary producer Git under its original keep policy and linked by immutable bot revision; consumer policy unchanged/no invented PDF manifest. All51583prior25keys176links/bothledgerprefixes/oldarchives and original math-native-proof-report-negative scopes retained. No new consumer remote read claimed; fresh additiveCI next, futurecustodyNEW27. Unsigned byte custody.']
for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(c).as_posix()]
for alias in aliases:cmd+=['--proof','attestation:'+alias]
consumerclaim=subprocess.check_output(cmd,cwd=c,text=True).strip();print(consumerclaim,flush=True)
(control/'actual-publication.claims.json').write_text(json.dumps(dict(root=rootclaim,consumer=consumerclaim),indent=2)+'\n')
report=cs/'reports/original-fixed-model-sampler-result-01/PUBLICATION_26.md'
report.write_text('# Complete inspected report publication\n\nThe full69,112-byte, two-page PDF is now [published in producer Git]('+pdfurl+'). Its bytes are unchanged from inspected report-source346f08. Producer policy explicitly keeps PDFs; consumer policy selects this report, so the existing source/inspection receipts remain immutable and this additive publication record links the full original producer blob. No synthetic PDF manifest or policy change. [pcc:unverified]\n\nGenuine26 publishes the complete evidence archive, both whole100/101-record fixtures and all failures/rejected reports. '+consumerclaim+' records exact publication/terminal held-byte checks. [pcc:unverified]\n')
state='''# Genuine26 settled; whole100/101 fixtures and complete PDF published

## What was done
'''+rootclaim+' / '+consumerclaim+''': original43720549312/job132831389944SUCCESS, nine remote objects replayed BEFORE actualbotb7bc54fcba/direct99cb2b204d/exact11paths; two plain Git objects unchanged. All58919heldinputs177linksownedbytes and whole136572156Barchive7357members68roots/3777consumerdeltafiles preserved. NormalFF-artifact-wiring0/HOLD26RELEASED. All51583prior25keys176links/both exactledgerprefixes/oldarchives held. Two exact original manifest entry dictionaries and two relative aliases roundtrip to the entire actualIC100/sampler101 populations. Full69112BPDF unchanged in ordinary producer Git; additive publication link replaces pending status without rewriting prior attested receipts. [pcc:unverified]

## Decisions made
Normal-publish custody settlement and consumer fixture projection, then add a fresh CI workflow covering the two new native populations with exact source/runtime/prepared custody and actual whole-class omissions. Preserve all prior source guards, workflows, reports, proofs and failed controls. Future whole custody is NEW27. [pcc:unverified]

## Open threads
Fresh IC/sampler CI; prospective FB30 relation-matrix/kernel-rank discriminator after primary-source/KB review; complete primitive/setup/known-point/strongest-reference cost census and live admission. All three norm-prepared points equal already available sourceGpoints; preserve the stronger-reference negative result. [pcc:unverified]

## Errors
First custody governor EOF-whitespace failure and FF01 lazy-fetch128 before merge; exact three-blob hydration preserves refs/HEAD/status, then explicit no-rename path comparison and FF02. Earlier ENOSPC/FUSE/history-inventory and every build/proof/recorder/import/native/control failure retained. FullCI41 artifact remains separate/uncollected, while a93f80 is exact258 and proofCI39bb46 exact41. [pcc:unverified]

---

'''
for repo,study,checkpoint,queue in [(r,s,'PUBLIC_TARGET_CHECKPOINT.md','QUEUE.md'),(c,cs,'CHECKPOINT.md','RESEARCH_QUEUE.md')]:
    for p in [repo/'.resume/RESUME.md',study/checkpoint,study/queue]:p.write_text(state+p.read_text())
    p=repo/'docs/session-logs/2026-11-15.md';p.write_text(p.read_text().rstrip()+'\n\n'+datetime.now(timezone.utc).isoformat()+'\n\n'+state.rstrip()+'\n')
