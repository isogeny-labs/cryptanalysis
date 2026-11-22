#!/usr/bin/env python3
"""Compare selected frozen control assembly text, explicitly ignoring relocations."""
import hashlib, json, re
from pathlib import Path
P = Path(__file__).resolve().parent
D = P / 'profile-n24-001'
selectors = ['<cryptanalysis_suite::cryptanalysis::ic_boundary::PairTable>::probe::<cryptanalysis_suite::cryptanalysis::ic_boundary::BinaryGroup>', '<cryptanalysis_suite::cryptanalysis::ic_boundary::PairWitnessMap>::get']
def extract(path):
    functions = {}; current = None
    for line in path.read_text().splitlines():
        match = re.fullmatch(r'([0-9a-f]+) <(.*)>:', line)
        if match:
            current = match[2]
            functions[current] = dict(address=int(match[1], 16), instructions=[])
        elif current is not None:
            ins = re.match(r'\s*[0-9a-f]+:\s*(.*)', line)
            if ins:
                value = ins[1].split('#', 1)[0].strip()
                value = re.sub(r'\b[0-9a-f]+ <(.*)>', r'<\1>', value)
                value = re.sub(r'-?0x[0-9a-f]+\(%rip\)', 'RELOC(%rip)', value)
                functions[current]['instructions'].append(value)
    return functions
inputs = {tag: D / (tag + '-disassembly.stdout') for tag in ['compact', 'packed', 'indexed']}
parsed = {tag: extract(path) for tag, path in inputs.items()}
rows = []
for name in selectors:
    baseline = parsed['compact'][name]['instructions']
    for tag in inputs:
        item = parsed[tag][name]; body = item['instructions']
        differences = [dict(position=i, compact=a, candidate=b) for i, (a,b) in enumerate(zip(baseline,body)) if a!=b]
        rows.append(dict(function=name, tag=tag, address=item['address'], address_mod64=item['address']%64, instruction_lines=len(body), normalized_sha256=hashlib.sha256('\n'.join(body).encode()).hexdigest(), normalized_equal_to_compact=(body==baseline), paired_differences=len(differences), first_differences=differences[:8]))
out = dict(status='pass', scope='post-analysis of existing disassembly text only; comments and RIP displacement/branch address relocations ignored, padding retained; neither binary-byte equality nor address/data/cache equivalence established; no new native timing or causal verdict', inputs_sha256={tag:hashlib.sha256(path.read_bytes()).hexdigest() for tag,path in inputs.items()}, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), rows=rows)
(P/'lookup-disassembly-comparison.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
