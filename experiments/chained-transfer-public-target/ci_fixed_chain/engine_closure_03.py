"""Compare complete Cargo engine dependency/features/targets closures, I/O only."""
from pathlib import Path
import json, sys
out, producer = map(Path, sys.argv[1:3]); label = sys.argv[3]
def closure(path):
    data = json.loads(path.read_text())
    packages = {p['id']: p for p in data['packages']}
    nodes = {n['id']: n for n in data['resolve']['nodes']}
    roots = [key for key, package in packages.items()
             if Path(package['manifest_path']).resolve() == (producer/'isogeny_algos/Cargo.toml').resolve()]
    if label == 'original-kernel':
        assert not roots
        return None
    assert len(roots) == 1
    seen = set(); pending = roots[:]
    while pending:
        key = pending.pop()
        if key in seen: continue
        seen.add(key); pending.extend(dep['pkg'] for dep in nodes[key]['deps'])
    return {key: dict(node=nodes[key], package={name: packages[key][name]
                 for name in ['id','manifest_path','dependencies','features','targets']}) for key in sorted(seen)}
actual = closure(out/(label+'-metadata.txt'))
if label != 'original-kernel':
    baseline = closure(out/'chain-metadata.txt')
    assert actual == baseline, 'entire field-engine dependency/features/targets closure changed'
(out/('engine-closure-'+label+'.json')).write_text(json.dumps(dict(
    label=label, exact_complete_closure=actual,
    field_engine='none' if actual is None else 'complete baseline equality; no second preparation permitted'), indent=2)+'\n')
