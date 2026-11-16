#!/usr/bin/env python3
"""Correctness and source analysis only; no arithmetic timing experiment."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'validation-linux-005'
OUT.mkdir(exist_ok=False)
BUILD = Path('/tmp/ic-simd-validation')


def run(name, args, mode=None):
    env = dict(os.environ)
    env['CA_IC_TRIAL32'] = mode or '0'
    result = subprocess.run(args, cwd=ROOT, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=240)
    (OUT / (name + '.log')).write_text(result.stdout)
    commands.append({'name': name, 'argv': args, 'mode': mode,
                     'exit_code': result.returncode})
    (OUT / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    return result.returncode


commands = []
source_names = ['src/indexcalc.c', 'src/ic_trial32.h', 'src/ic_rational.h',
                'tests/test_ic_projection.c', 'CMakeLists.txt', '.clang-tidy']
receipt = {'system': platform.platform(), 'machine': platform.machine(),
           'sources': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                       for p in source_names}}
for p in ['/proc/cpuinfo', '/proc/self/cgroup', '/proc/self/mountinfo']:
    try:
        receipt[p] = Path(p).read_text()
    except OSError:
        receipt[p] = None
(OUT / 'host.json').write_text(json.dumps(receipt, indent=2) + '\n')
if run('configure', ['cmake', '-S', str(ROOT), '-B', str(BUILD),
                     '-DCA_WERROR=ON', '-DCA_BUILD_SHARED=OFF',
                     '-DCMAKE_BUILD_TYPE=Debug', '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']):
    raise SystemExit(1)
if run('build', ['cmake', '--build', str(BUILD), '-j3']):
    raise SystemExit(1)
failed = run('ctest-default', ['ctest', '--test-dir', str(BUILD), '--output-on-failure'])
for mode in ['auto', 'portable']:
    failed |= run('ctest-' + mode, ['ctest', '--test-dir', str(BUILD), '-V',
                                   '-R', '^(indexcalc|ic_projection)$'], mode)
failed |= run('clang-tidy', ['clang-tidy', '-p', str(BUILD), '--quiet',
                            'src/indexcalc.c', 'tests/test_ic_projection.c'])
failed |= run('cppcheck', ['cppcheck', '--enable=warning,performance,portability,style',
                          '--inline-suppr', '--std=c11', '--error-exitcode=1',
                          '--suppress=missingIncludeSystem', '-Iinclude', '-Isrc',
                          '--quiet', 'src/indexcalc.c', 'tests/test_ic_projection.c'])
raise SystemExit(bool(failed))
