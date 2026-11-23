"""Build the four benchmark libraries in the current directory on ARM64 macOS."""
from pathlib import Path
import platform
import subprocess
import sys

here = Path(__file__).resolve().parent
ffi = here.parent
sys.path.insert(0, str(ffi))
from check_graph_tables import certificate_labels

if platform.machine() != 'arm64' or platform.system() != 'Darwin':
    raise SystemExit('This comparison requires native macOS ARM64 NEON.')

source = (ffi / 'm31.cpp').read_text()
certificate = (ffi / 'GraphReciprocal.lean').read_text()
for arm in ('default', 'coset', 'raw', 'signed'):
    code = source
    if arm in ('raw', 'signed'):
        width, salt, shift = (2048, 2654435787, 21) if arm == 'raw' else (1024, 2654435769, 22)
        lookup = (here / 'lookup.inc.in').read_text()
        for token, value in {
            'WIDTH': width, 'SALT': salt, 'SHIFT': shift,
            'KEY': 'x' if arm == 'raw' else 'x < prime-x ? x : prime-x',
            'SIGN': '0u' if arm == 'raw' else '(x == key ? 0u : prime)',
        }.items():
            lookup = lookup.replace(f'@{token}@', str(value))
        labels = ','.join(map(str, certificate_labels(certificate, arm)))
        start = code.index('// Indexed by public')
        end = code.index('#endif', start)
        code = code[:start] + f'\nconstexpr uint32_t labels[] = {{ {labels} }};\n' + lookup + code[end:]
    if arm != 'default':
        code = '#define M31_PUBLIC_COSET_INVERSE\n' + code
    code += '\n' + (here / 'stream_wrapper.inc').read_text()
    stem = f'{arm}_stream'
    Path(stem + '.cpp').write_text(code)
    subprocess.run(['clang++', '-std=c++17', '-O3', '-mcpu=native', '-I', str(ffi),
                    '-shared', '-fPIC', stem + '.cpp', '-o', stem + '.so'], check=True)
