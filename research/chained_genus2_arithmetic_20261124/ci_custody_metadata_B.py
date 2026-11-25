"""Portable CI file/hash/JSON custody only; never executes a research algorithm."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys

STUDY = Path(__file__).resolve().parent
ROOT = STUDY.parents[1]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return {'bytes': path.stat().st_size, 'sha256': h.hexdigest(), 'mode': path.stat().st_mode & 0o777}

def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')

def snapshot(out, context):
    return {'original': {p: digest(ROOT/p) for p in context['paths']},
            'copied': {p: digest(out/'source'/p) for p in context['paths']},
            'tools': {p: digest(Path(p)) for p in context['tools']},
            'qualifiers': {n: digest(out/n) for n in ('qualifier',) if (out/n).exists()}}

def main():
    action, target = sys.argv[1:3]
    out = Path(target)
    if action == 'prepare':
        lock_path = STUDY/'SOURCE_LOCK_A.json'
        lock = json.loads(lock_path.read_text())
        claim = json.loads((ROOT/'pcc/claims/PCC-20261124-674f2c.json').read_text())
        assert digest(lock_path)['sha256'] == claim['proofs'][0]['subject']['sha256']
        paths = list(lock['files']) + [str(lock_path.relative_to(ROOT))] + ['research/chained_genus2_arithmetic_20261124/ci_custody_metadata_B.py', 'research/chained_genus2_arithmetic_20261124/run_ci_B.sh', '.github/workflows/chained-genus2-arithmetic.yml', 'pcc/claims/PCC-20261124-674f2c.json']
        for name in paths:
            p = ROOT/name
            if name in lock['files']:
                actual, expected = digest(p), lock['files'][name]
                assert actual['bytes'] == expected['bytes'] and actual['sha256'] == expected['sha256'], name
                assert bool(actual['mode'] & 0o111) == bool(expected['mode'] & 0o111), name
            dest = out/'source'/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
        tools = []
        for name in ('rustc', 'rustfmt', 'clippy-driver'):
            p = Path(subprocess.check_output(['rustup', 'which', '--toolchain', '1.99.1', name]).decode().strip())
            assert digest(p)['sha256'] == lock['tool_binary_sha256'][name], name
            tools.append(str(p))
        context = {'recorded': datetime.now(timezone.utc).isoformat(), 'paths': paths, 'tools': tools,
                   'CI': {k: os.environ.get(k) for k in ('GITHUB_SHA','GITHUB_RUN_ID','GITHUB_RUN_ATTEMPT','GITHUB_JOB')},
                   'uname': list(platform.uname()), 'affinity': sorted(os.sched_getaffinity(0)),
                   'profile': 'Portable complete actual inert-sextic ideal/Cantor/cover/BSGS mathematical correctness regression; same source/compiler bytes and scientific bounds. Checkout permissions use Git executable bits. Host libraries/OS remain ambient; not identical to original Cloud run or a benchmark.'}
        write(out/'CONTEXT.json', context)
        write(out/'CI_BUILD_MANIFEST.json', snapshot(out, context))
    elif action == 'phase':
        name, status = sys.argv[3], int(sys.argv[4])
        write(out/(name+'.phase.json'), {'recorded': datetime.now(timezone.utc).isoformat(), 'exit': status,
              'stdout': digest(out/(name+'.stdout')), 'stderr': digest(out/(name+'.stderr'))})
    elif action == 'pre':
        context = json.loads((out/'CONTEXT.json').read_text())
        write(out/'PRE_CALL_MANIFEST.json', snapshot(out, context))
    elif action == 'finish':
        status = int(sys.argv[3])
        if not (out/'CONTEXT.json').exists():
            write(out/'POST_CALL_MANIFEST.json', {'outer_exit': status, 'init_incomplete': True})
            return
        context = json.loads((out/'CONTEXT.json').read_text())
        post = snapshot(out, context)
        build = json.loads((out/'CI_BUILD_MANIFEST.json').read_text())
        failures = [k for k in ('original','copied','tools') if post[k] != build[k]]
        if (out/'PRE_CALL_MANIFEST.json').exists():
            pre = json.loads((out/'PRE_CALL_MANIFEST.json').read_text())
            if post['qualifiers'] != pre['qualifiers']: failures.append('qualifier')
        elif status == 0:
            failures.append('missing pre-call manifest')
        post.update({'outer_exit': status, 'guard_failures': failures})
        for name in ('native-built',):
            if (out/name).exists(): post[name] = digest(out/name)
        write(out/'POST_CALL_MANIFEST.json', post)
        if status == 0 and failures: raise RuntimeError('CI post-call guard failure')
    else:
        raise RuntimeError('unknown metadata action')

if __name__ == '__main__':
    main()
