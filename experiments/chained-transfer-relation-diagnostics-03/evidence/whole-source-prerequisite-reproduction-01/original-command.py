"""File custody only: complete frozen guard before/after source publication."""
from pathlib import Path
import hashlib, json, lzma, shutil, subprocess

repo = Path('/workspace/cryptanalysis')
base = Path('/dev/shm/ct158-original-CI-source-preparation-01')
base.mkdir()
cold = base / 'cryptanalysis'
cold.mkdir()
out = base / 'whole-observation'
out.mkdir()
shutil.copyfile(__file__, out / 'original-command.py')
reference = repo / 'experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256'
assert hashlib.sha256(reference.read_bytes()).hexdigest() == '3714c4a2e2d696f917b905a8882a2325c9d32aeec2cd39a20ccc4d60c6a702e1'
rows = [line.split('  ', 1) for line in reference.read_text().splitlines()]
study = Path('experiments/chained-transfer-public-target')
ci = study / 'ci_fixed_chain'
manifest = json.loads((repo / ci / 'successor-sources-03.json').read_text())
missing = {str(study / row['relative_to_study']) for row in manifest['files']}
assert len(rows) == 1605 and len(missing) == 21
for sha, name in rows:
    source = repo / name
    assert hashlib.sha256(source.read_bytes()).hexdigest() == sha
    if name not in missing:
        target = cold / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
refcopy = cold / reference.relative_to(repo)
refcopy.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(reference, refcopy)

def observe(label, command, expected):
    result = subprocess.run(command, cwd=cold, capture_output=True)
    (out / (label + '.stdout.xz')).write_bytes(lzma.compress(result.stdout))
    (out / (label + '.stderr.xz')).write_bytes(lzma.compress(result.stderr))
    (out / (label + '.exit')).write_text(str(result.returncode) + '\n')
    assert result.returncode == expected, label
    print(label, result.returncode, flush=True)
    return result

negative = observe('whole-original-guard-missing21', ['sha256sum', '--check', str(refcopy)], 1)
actual_missing = {line.split(': No such file or directory')[0].removeprefix('sha256sum: ') for line in negative.stderr.decode().splitlines() if ': No such file or directory' in line}
assert actual_missing == missing
(out / 'entire-missing-source-set.json').write_text(json.dumps(sorted(missing), indent=2) + '\n')
tree = Path('/workspace/scratch/ct158-source-preparation-tree.txt').read_text().strip()
installed = []
for row in manifest['files']:
    name = str(study / row['relative_to_study'])
    body = subprocess.check_output(['git', 'show', tree + ':' + name], cwd=repo)
    assert len(body) == row['bytes'] and hashlib.sha256(body).hexdigest() == row['sha256']
    destination = cold / name
    assert not destination.exists()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(body)
    installed.append(dict(path=name, sha256=row['sha256'], bytes=row['bytes'], staged_tree=tree))
(out / 'entire-staged-source-installation.json').write_text(json.dumps(installed, indent=2) + '\n')
observe('whole-original-guard-present21', ['sha256sum', '--check', str(refcopy)], 0)
for index in [1, 2]:
    installer_out = out / ('original-idempotent-installer-' + str(index))
    installer_out.mkdir()
    observe('original-idempotent-installer-' + str(index), ['python3', str(cold / ci / 'install_sources_03.py'), str(cold / ci), str(cold / study), str(installer_out)], 0)
    observe('whole-original-guard-after-installer-' + str(index), ['sha256sum', '--check', str(refcopy)], 0)
    assert json.loads((installer_out / 'installed-literal-successor-sources.json').read_text()) == manifest['files']
for sha, name in rows:
    assert hashlib.sha256((cold / name).read_bytes()).hexdigest() == sha
receipt = dict(scope='source/data I-O only; no mathematical population executed', original_guard_count=1605, exactly_missing_before=21, exact_original_source_bytes_published=102647, staged_tree=tree, full_guard_after=0, both_original_idempotent_installer_exits=[0, 0], full_guards_after_each=[0, 0], all1605_byte_exact=True, whole_ram_fixture=str(base), fresh_GitHub_CI_unobserved=True)
(out / 'complete-source-preparation-custody.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt), flush=True)
