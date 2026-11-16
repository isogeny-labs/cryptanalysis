"""Exercise the actual analysis job inputs/commands without any artifact store.

Producer development control only. It uses tracked blobs and the existing
tests, not historical benchmark outputs or a fresh performance panel.
"""
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
WORKFLOW = '.github/workflows/n83-opcounts.yml'
SOURCE = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
text = subprocess.check_output(['git', 'show', f'{SOURCE}:{WORKFLOW}'], cwd=ROOT, text=True)
job = text.split('  analysis-gate-tests:\n', 1)[1].split('  opcounts:\n', 1)[0]
assert 'Pull store data' not in job and 'AWS_' not in job
patterns = job.split('          sparse-checkout: |\n', 1)[1].split('      - uses:', 1)[0]
paths = [line.strip().removeprefix('/') for line in patterns.splitlines() if line.strip()]
assert len(paths) == 9 and all('*' not in path for path in paths)
commands = job.split('      - name: Verify and test complete-panel analysis gate\n        run: |\n', 1)[1]
commands = [shlex.split(line.strip()) for line in commands.splitlines() if line.strip()]
assert len(commands) == 2 and commands[0][0] == 'sha256sum' and commands[1][0] == 'python3'
results = []
inputs = []


def run(name, argv, expected, cwd, env):
    path = OUT / (name + '.log')
    assert not path.exists(), path
    with path.open('wb') as stream:
        result = subprocess.run(argv, cwd=cwd, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=60)
    row = {'name': name, 'argv': argv, 'expected_exit': expected,
           'exit_code': result.returncode, 'log': path.name,
           'log_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    results.append(row)
    assert result.returncode == expected, row


with tempfile.TemporaryDirectory(prefix='n83-source-only-') as directory:
    scratch = Path(directory)
    for path in paths:
        payload = subprocess.check_output(['git', 'show', f'{SOURCE}:{path}'], cwd=ROOT)
        target = scratch / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        inputs.append({'path': path, 'sha256': hashlib.sha256(payload).hexdigest(), 'bytes': len(payload)})
    assert not list(scratch.rglob('.artifacts.json'))
    assert not list(scratch.rglob('run_github_*'))
    guard = scratch / '_audit'
    guard.mkdir()
    guard_source = '''import os, sys
def deny(event, args):
    if event.startswith('socket.') or event in {'subprocess.Popen', 'os.system', 'os.posix_spawn'}:
        raise RuntimeError('source-only control forbids network and child processes')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = os.fsdecode(args[0])
        if '.artifacts.json' in path or 'run_github_' in path:
            raise RuntimeError('source-only control forbids historical artifact reads')
sys.addaudithook(deny)
print('source-only audit guard active', file=sys.stderr)
'''
    (guard / 'sitecustomize.py').write_text(guard_source)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(('AWS_', 'ARTIFACTS_', 'CHECKPOINT_'))}
    env.update(PYTHONPATH=str(guard), PYTHONDONTWRITEBYTECODE='1')
    run('source-checksums', commands[0], 0, scratch, env)
    run('source-analysis-tests', commands[1], 0, scratch, env)
    output = (OUT / 'source-analysis-tests.log').read_text()
    assert 'source-only audit guard active' in output
    assert 'Ran 8 tests' in output and output.rstrip().endswith('OK')
    run('network-refusal', ['python3', '-c', 'import socket; socket.socket()'], 1, scratch, env)
    run('archive-refusal', ['python3', '-c', "open('.artifacts.json')"], 1, scratch, env)
    protocol = scratch / 'experiments/koblitz-n83-stacked-20261016/protocol.json'
    protocol.unlink()
    run('missing-protocol-refusal', commands[1], 1, scratch, env)
    assert 'FileNotFoundError' in (OUT / 'missing-protocol-refusal.log').read_text()
    source = scratch / 'experiments/koblitz-n83-opcounts-20261023/analyze_v2.py'
    source.write_bytes(source.read_bytes() + b'\n')
    run('changed-source-refusal', commands[0], 1, scratch, env)
    assert 'FAILED' in (OUT / 'changed-source-refusal.log').read_text()

receipt = {'schema': 'source-only-analysis-control/v1', 'source_commit': SOURCE,
           'independent': False, 'workflow': WORKFLOW, 'inputs': inputs,
           'commands_from_workflow': commands, 'results': results,
           'python': platform.python_version(), 'platform': platform.platform(),
           'audit_guard_sha256': hashlib.sha256(guard_source.encode()).hexdigest(),
           'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'environment_overrides': {'PYTHONPATH': '<temporary audit guard>', 'PYTHONDONTWRITEBYTECODE': '1'},
           'removed_environment_prefixes': ['AWS_', 'ARTIFACTS_', 'CHECKPOINT_'],
           'scope': 'Existing unit checks and intentional refusal controls only; no benchmark or independent replay.'}
(OUT / 'source-only-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('Eight existing analysis tests pass on nine tracked inputs with network/artifact reads denied.')
print('Network, archive, missing-protocol and changed-source controls refuse as expected.')
