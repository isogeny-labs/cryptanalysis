#!/usr/bin/env python3
"""Static instruction/call listing, not execution or a timing claim."""
import subprocess, hashlib, json, re
from pathlib import Path
P = Path(__file__).resolve().parent
BASE = P.parent / 'ic-vector-inverse-20261116/timing-001'
out = {}
for label, name in [('anchor', 'probe-anchor'), ('current', 'probe')]:
    binary = BASE / name
    pin = json.loads((P / ('anchor-input.json' if label == 'anchor' else 'prepared-input.json')).read_text())
    assert hashlib.sha256(binary.read_bytes()).hexdigest() == pin['binary_sha256']
    process = subprocess.Popen(['/Library/Developer/CommandLineTools/usr/bin/llvm-objdump', '-d', '--no-show-raw-insn', str(binary)], stdout=subprocess.PIPE, text=True)
    sections = {}; current = None
    for line in process.stdout:
        match = re.match(r'^[0-9a-f]+ <(.*)>:', line)
        if match:
            fn = match[1]
            current = fn if 'FastCurve' in fn and 'add_pairwise_vector' in fn else None
            if current: sections[current] = []
        elif current:
            sections[current].append(line)
    assert process.wait() == 0 and sections
    (P / (label + '-pairwise-disassembly.txt')).write_text(''.join(fn + '\n' + ''.join(lines) + '\n' for fn, lines in sections.items()))
    out[label] = {fn: {'instruction_lines': sum(bool(re.match(r'\s*[0-9a-f]+:', x)) for x in lines),
                       'calls': [x.strip() for x in lines if re.search(r'\bcallq?\b', x)]} for fn, lines in sections.items()}
(P / 'pairwise-codegen.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out))
