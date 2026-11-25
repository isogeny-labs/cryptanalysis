#!/usr/bin/env python3
"""Reuse the owned frozen cache while preserving the archived native recipe."""
import hashlib,json,os,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[1]
prior=ROOT/'experiments/ic-static-witness-map-20261117'
names=['instances.json','baseline-input.json','baseline-source-hashes.json','source_manifest.py','prepared-input.json','anchor-input.json','indexed-input.json','callgrind_parser.py','verify_frozen_units.py','replay_preparation.py','archive_captures.py','readback_bundles.py']+[f'archive-n{n}.json' for n in [15,18,21,24,27]]
for name in names:
    data=(prior/name).read_bytes(); dest=P/name
    if dest.exists(): assert dest.read_bytes()==data
    else: dest.write_bytes(data)
from source_manifest import sources,changed_sources
FROZEN=Path('/tmp/ic-canonical-frozen-source-001')
assert FROZEN.resolve()==prior/'local-frozen-source-stash'
old=json.loads((P/'baseline-source-hashes.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert {name for name in sources if sha(FROZEN/name)!=old[name]} <= set(changed_sources)
for name in changed_sources:
    raw=subprocess.check_output(['git','show','bfd0e5062cbedccbc3b2a28856832dd434533510:'+name],cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest()==old[name]
    path=FROZEN/name; tmp=path.with_name(path.name+'.counterfactual-baseline'); tmp.write_bytes(raw); os.replace(tmp,path)
assert {name:sha(FROZEN/name) for name in sources}==old
for name in changed_sources:
    path=FROZEN/name; tmp=path.with_name(path.name+'.counterfactual-overlay'); tmp.write_bytes((ROOT/name).read_bytes()); os.replace(tmp,path)
actual={name:sha(FROZEN/name) for name in sources}
assert {name for name in sources if actual[name]!=old[name]}==set(changed_sources)
(P/'local-source-manifest.json').write_text(json.dumps(dict(status='pass',source_sha256=actual,changed_sources=changed_sources,baseline='indexed847 full16-source reconstruction',archived_cargo_manifest_retained=True),indent=2)+'\n')
(P/'local-tmp').mkdir(exist_ok=True)
print('Full16-source local recipe checked, exact3-source overlay')
