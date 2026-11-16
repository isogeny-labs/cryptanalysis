#!/usr/bin/env python3
"""Static same-binary symbol sizes, not executed cost or latency."""
import hashlib,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent
binary=P/'build-001/probe'
argv=['/Library/Developer/CommandLineTools/usr/bin/llvm-objdump','-d','--demangle','--no-show-raw-insn',str(binary)]
raw=subprocess.check_output(argv,text=True);rows=[]
for chunk in re.split(r'(?m)^(?=[0-9a-f]+ <)',raw):
 header=chunk.splitlines()[0] if chunk else ''
 if 'add_cached_narrow' not in header:continue
 rows.append(dict(symbol=header,disassembly_lines=len(chunk.splitlines()),instructions=len(re.findall(r'(?m)^\s+[0-9a-f]+:',chunk))))
(P/'codegen-001.json').write_text(json.dumps(dict(binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),argv=argv,rows=rows,standing='unsigned static compiler diagnostic; not execution or performance'),indent=2)+'\n')
print(json.dumps(rows))
