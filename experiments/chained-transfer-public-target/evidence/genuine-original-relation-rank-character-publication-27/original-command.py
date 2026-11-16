"""Close actual original custody and project exact entries; metadata I/O only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, lzma, os, shutil, subprocess

r=Path('/workspace/crypto'); c=Path('/workspace/cryptanalysis'); scratch=Path('/workspace/scratch')
s=r/'research/chained_jacobian_transfers_20261110'; cs=c/'experiments/chained-transfer-public-target'
source='00800a2b8f20a2812eccbc5200e85a99572b453d'; bot='0b2bee203a133568f1c7e9a35bfe3be1a663a879'
ff=scratch/'ct106-handoff27-artifact-ff-01'; control=scratch/'ct104-whole-closed-science-handoff-27-attempt02'
assert (scratch/'ct106-handoff27-ff-caller01.exit').read_text().strip()=='0'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==bot
receipt=json.loads((ff/'dirty-preservation.json').read_text())
assert receipt['hold27'].startswith('RELEASED') and receipt['all_owned_bytes_exact']
assert receipt['complete_terminal_guard']['content_keys']==65886 and receipt['complete_terminal_guard']['literal_links']==179
assert receipt['original_remote_replays_before_actual_bot']==11 and len(receipt['exact_changed_paths'])==13
for name in ['exact-ff','artifact','wiring']: assert (ff/(name+'.exit')).read_text().strip()=='0'
payload=s/'evidence/public-n4-original-relation-rank-character-handoff-27'
manifest=json.loads((payload/'.artifacts.json').read_text()); assert len(manifest['files'])==11
objects={Path(x['path']).name:x for x in json.loads((payload/'objects.json').read_text())}
fixtures=json.loads((control/'whole-fixtures.json').read_text()); assert len(fixtures)==6
e=s/'evidence/public-n4-original-relation-rank-character-publication-27'; e.mkdir()
for p in sorted(ff.iterdir()):
    if p.is_file(): shutil.copyfile(p,e/p.name)
fetch=scratch/'ct105-handoff27-RAM-bot-fetch-01'
for p in sorted(fetch.iterdir()):
    if p.is_file(): shutil.copyfile(p,e/('fetch-'+p.name))
for p,name in [(scratch/'ct105-handoff27-original-jobs-api.json','original-jobs-api.json'),(scratch/'ct105-handoff27-actual-original-publication-01/whole-job.log.xz','whole-original-job.log.xz'),(scratch/'ct105-handoff27-actual-original-publication-01/observation.json','original-job-observation.json'),(control/'owned-before.json','owned-before.json'),(scratch/'ct105-handoff27-normal-publication-01/receipt.json','normal-push-receipt.json'),(scratch/'ct106-session-access-and-source-review-01/access-error.json','session-access-error-and-source-review.json'),(scratch/'ct106-session-access-and-source-review-01/conductor.txt','conductor.txt'),(scratch/'ct106-session-access-and-source-review-01/conductor.exit','conductor.exit')]:
    shutil.copyfile(p,e/name)
for p,name in [(scratch/'ct105-handoff27-normal-publication-01/push.log','whole-normal-push.log.xz'),(scratch/'ct106-handoff27-ff-caller01.txt','whole-FF-caller.txt.xz')]:
    body=p.read_bytes(); packed=lzma.compress(body); assert lzma.decompress(packed)==body; (e/name).write_bytes(packed)
publication=dict(at=datetime.now(timezone.utc).isoformat(),source=source,bot=bot,run=43745805865,job=132908716494,
    original_remote_replays_BEFORE_actual_bot=11,exact_direct_parent=source,exact_changed_paths=receipt['exact_changed_paths'],
    complete_terminal_guard=receipt['complete_terminal_guard'],all_owned_bytes_exact=True,normalFF_artifact_wiring=0,
    whole_archive=receipt['whole_archive_ordered_reassembly'],whole_members=7005,whole_closed_roots=59,
    all_consumer_delta_paths=3578,all_producer_delta_paths=622,all_prior58919_keys_and177_links_retained=True,
    all15_source_blobs_checked=True,exact11_canonical_entries=True,four_plainGit_keeps_unchanged=True,
    hold27='RELEASED',RAM_cache_recovery='Separate exact closed cache receipts: new immutable payload blobs in original committed governance; exact original remote bot cache in fetch-closed-new-remote-cache.json. Published immutable source and bot commits supply recovery without touching unrelated objects.',
    scope='unsigned byte custody; original native, finite character, conditional Lean, CI and performance scopes unchanged')
(e/'publication.json').write_text(json.dumps(publication,indent=2)+'\n'); shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',
    'Actual original custody27: run43745805865/job132908716494, eleven original remote objects replayed BEFORE actual bot0b2bee203a with exact direct parent00800a2b and exact13 changed paths. All15 whole original source blobs checked; four plain Git keeps including unchanged53962B report remain ordinary Git. Whole125663108B archive SHA27da983f37d3e663529450ea17b98afb579cfe04fc3d06bec7028181ef22bd9a,7005 members59closed roots/all3578 consumer622producer delta paths and all prior58919keys177links retained. All65886held content keys179literal links/full target states/consumer exact ledger/producer ledger prefix/owned bytes pass before and after exact normal FF; original artifact and wiring0, HOLD27 RELEASED. Closed exact bot RAM fetch changed no refs-HEAD-status and moved no existing local/nonpromisor objects; separate source/blob/remote-cache recovery receipts retained. Whole passive/rank/character populations, every failure/control/source/runtime/fullprepared/474CIartifact/log/report draft retained. Unsigned byte custody only.']
for p in sorted(e.iterdir()): cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
rootclaim=subprocess.check_output(cmd,cwd=r,text=True).strip(); print(rootclaim,flush=True)

docs=c/'docs/research-artifacts/chained-transfer/original-relation-rank-character-27'; docs.mkdir()
selected={row['name']:manifest['files'][row['name']] for row in fixtures if objects[row['name']]['original_policy_requires_store']}
assert len(selected)==5 and 'relation-whole60-verdict.json.xz' not in selected
projection=dict(manifest); projection['files']=selected
(docs/'.artifacts.json').write_text(json.dumps(projection,indent=2)+'\n')
(docs/'.gitignore').write_text(''.join(n+'\n' for n in selected))
aliases={}
mapping={
    'passive-whole100-native.json.xz':('original-relation-kernel-01','expected-native-01.json.xz'),
    'passive-whole60-trace.json.xz':('original-relation-kernel-01','expected-trace-01.json.xz'),
    'relation-whole60-certificates.jsonl.xz':('original-relation-rank-01','expected-certificates-01.jsonl.xz'),
    'relation-whole60-verdict.json.xz':('original-relation-rank-01','expected-verdict-01.json.xz'),
    'source-character-whole60-witnesses.jsonl.xz':('original-relation-character-01','expected-witnesses-01.jsonl.xz'),
    'source-character-whole60-verdict.json.xz':('original-relation-character-01','expected-verdict-01.json.xz')}
for row in fixtures:
    name=row['name']; target=docs/name; data=Path(row['path']).read_bytes()
    assert len(data)==objects[name]['bytes'] and hashlib.sha256(data).hexdigest()==objects[name]['sha256']
    decoded=lzma.decompress(data); assert len(decoded)==row['decoded_bytes'] and hashlib.sha256(decoded).hexdigest()==row['decoded_sha256']
    original=Path(row['whole_original']).read_bytes()
    if Path(row['whole_original']).suffix=='.xz': original=lzma.decompress(original)
    assert decoded==original
    target.write_bytes(data)
    if name in selected: assert selected[name]==dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    package,aliasname=mapping[name]; alias=cs/package/aliasname
    assert not alias.exists() and not alias.is_symlink()
    alias.symlink_to(os.path.relpath(target,alias.parent)); assert alias.read_bytes()==data
    aliases[alias.relative_to(c).as_posix()]=os.readlink(alias)
    if name in selected: assert subprocess.run(['git','check-ignore','-q',target.relative_to(c).as_posix()],cwd=c).returncode==0
ce=cs/'evidence/genuine-original-relation-rank-character-publication-27'; ce.mkdir()
for p,name in [(payload/'.artifacts.json','original-root-manifest.json'),(docs/'.artifacts.json','canonical-projection-manifest.json'),(ff/'dirty-preservation.json','original-terminal-guard-receipt.json'),(e/'publication.json','original-publication.json')]: shutil.copyfile(p,ce/name)
shutil.copyfile(__file__,ce/'original-command.py')
pdfrel=(payload/'original-relation-character-result-01.pdf').relative_to(r).as_posix()
pdfurl='https://github.com/isogeny-labs/crypto/blob/'+bot+'/'+pdfrel
(ce/'projection.json').write_text(json.dumps(dict(root_claim=rootclaim,publication=publication,
    exact_five_original_manifest_entry_dicts=selected,canonical_docs=docs.relative_to(c).as_posix(),
    six_transparent_relative_aliases=aliases,all_six_whole_XZ_decoded_byte_roundtrips=True,
    plain_rank_verdict=dict(path=(docs/'relation-whole60-verdict.json.xz').relative_to(c).as_posix(),bytes=3268,sha256=objects['relation-whole60-verdict.json.xz']['sha256'],ordinaryGit=True),
    report=dict(url=pdfurl,bytes=53962,sha256=objects['original-relation-character-result-01.pdf']['sha256'],ordinary_producer_Git=True),
    no_new_consumer_remote_read_claimed=True,future_custody='NEW28;27historical',scope='unsigned byte custody only'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',
    'Consumer genuine27 projection: actual original run43745805865/job132908716494 eleven remote replays BEFORE actual bot0b2bee203a/direct00800a2b/exact13paths, all65886content keys179literal links/full target states/owned bytes/exact consumer ledger/producer prefix held; whole125663108B archive7005members59closed roots/all3578consumer622producerdelta paths retained, normalFF-artifact-wiring0/HOLD27 RELEASED. Five exact original canonical manifest entry dictionaries and six transparent relative aliases preserve whole passive100 native60trace,60rank certificates/verdict and60character witnesses/verdict with full losslessXZ byte roundtrips. Small3268B rank verdict stays ordinary Git without invented entry; full53962B two-opened-page report linked immutably in ordinary producer Git. No new consumer remote read claimed, no pinned source/negative/report bytes changed. Prospective whole diagnostic CI next; future custody NEW28. Unsigned byte custody.']
for p in sorted(ce.iterdir()): cmd+=['--proof','attestation:'+p.relative_to(c).as_posix()]
for name in aliases: cmd+=['--proof','attestation:'+name]
consumerclaim=subprocess.check_output(cmd,cwd=c,text=True).strip(); print(consumerclaim,flush=True)
(scratch/'ct106-handoff27-publication-claims.json').write_text(json.dumps(dict(root=rootclaim,consumer=consumerclaim),indent=2)+'\n')
report=cs/'reports/original-relation-character-result-01/PUBLICATION_27.md'
report.write_text('# Inspected report and complete diagnostic custody\n\nThe full 53,962-byte, two-page PDF is [published at the immutable original bot revision]('+pdfurl+'). Its bytes match report claim2fd6b0 and both actually opened pages. Original producer policy keeps this PDF in ordinary Git. '+consumerclaim+' records actual publication, complete terminal guards and fixture projection. [pcc:unverified]\n\nThe complete archive retains all 60 passive/rank/character calls, every rejected candidate, row/certificate/BSGS table, original CI artifact and logs, full prepared engine/runtime/source, failures, controls and report drafts. Five canonical entry dictionaries and six relative aliases reproduce the entire six fixtures; the small rank verdict remains ordinary Git. [pcc:unverified]\n')
state='''# Genuine27 settled; whole diagnostic fixtures published

## What was done
'''+rootclaim+' / '+consumerclaim+''': original run43745805865/job132908716494 replayed eleven remote objects BEFORE actual bot0b2bee203a, direct parent00800a2b, exact thirteen changed paths. All 65,886 content keys and 179 literal links/full target states/owned bytes/ledger checks retained; exact normal FF and original artifact/wiring checks exit0. HOLD27 RELEASED. Whole 125,663,108-byte archive, 7,005 members, 59 closed roots, all 3,578 consumer/622 producer delta paths retained. Five exact original canonical entry dictionaries and six relative aliases roundtrip the complete passive/rank/character fixtures; small rank verdict and full inspected PDF retain ordinary Git policy. [pcc:unverified]

## Decisions made
Publish custody settlement, then freeze and normally publish the whole diagnostic CI comparison contract BEFORE comparator/driver code. Require the entire population, all mathematical controls, both original conditional Lean gates, original engine/runtime/fullprepared custody and complete artifacts. Future whole custody is NEW28. [pcc:unverified]

## Open threads
Whole diagnostic CI; primary-source/KB review and prospective unassisted relation-completion successor. The finite character separator3a7d56, exact rankc0479c and conditional proof19c467 retain their original scope. Actual global character/program/numeric Lean bridges, complete setup/primitive/strongest-reference calibrated costs and original merge gates remain open. Vault8edec422 remains locked with four-byte VLT1 checks only; KB127 remains an availability gap. [pcc:unverified]

## Errors
All prior archive/governance/source/native/proof/control/report/transport failures remain complete. Conductor is unavailable (actual127). An initial broad AGENTS read accidentally included the locked autoresearcher ciphertext, repeating the recorded access error; no plaintext/key/decryption/execution or file modification occurred. No emitted ciphertext is republished. Future reads obey the exact four-byte-only restriction. [pcc:unverified]

---

'''
for repo,study,checkpoint,queue in [(r,s,'PUBLIC_TARGET_CHECKPOINT.md','QUEUE.md'),(c,cs,'CHECKPOINT.md','RESEARCH_QUEUE.md')]:
    for p in [repo/'.resume/RESUME.md',study/checkpoint,study/queue]: p.write_text(state+p.read_text())
    p=repo/'docs/session-logs/2026-11-15.md'; p.write_text(p.read_text().rstrip()+'\n\n'+datetime.now(timezone.utc).isoformat()+'\n\n'+state.rstrip()+'\n')
print('publication and projection recorded; root and consumer settlement commits next',flush=True)
