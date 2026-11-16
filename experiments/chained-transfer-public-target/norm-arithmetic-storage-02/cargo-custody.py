#!/usr/bin/env python3
"""Diagnostic-only Cargo forwarding and actual compiler-binary custody."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
real='/home/agent/.rustup/toolchains/1.99.1-x86_64-unknown-linux-gnu/bin/cargo'
args=sys.argv[1:];root=Path(os.environ['CT80_CARGO_CUSTODY']);root.mkdir(exist_ok=True)
capture=bool(args) and (args[0]=='build' or (args[0]=='test' and '--no-run' in args))
if not capture:
 q=subprocess.run([real,*args]);raise SystemExit(q.returncode)
if not any(x.startswith('--message-format') for x in args):args+=['--message-format=json']
o=root/str(len(list(root.iterdir()))+1);o.mkdir()
(o/'command.json').write_text(json.dumps(dict(actual_cargo=real,original_args=sys.argv[1:],diagnostic_args=args),indent=2)+'\n')
q=subprocess.run([real,*args],stdout=subprocess.PIPE);sys.stdout.buffer.write(q.stdout);sys.stdout.buffer.flush();(o/'whole-compiler.jsonl').write_bytes(q.stdout);(o/'compile.exit').write_text(str(q.returncode)+'\n')
records=[]
for line in q.stdout.splitlines():
 try:x=json.loads(line)
 except json.JSONDecodeError:continue
 if x.get('reason')=='compiler-artifact' and x.get('executable'):
  p=Path(x['executable']);dest=o/p.name;shutil.copyfile(p,dest)
  records.append(dict(Cargo_artifact=x,actual_copy=str(dest),bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
(o/'actual-executables.json').write_text(json.dumps(records,indent=2)+'\n')
raise SystemExit(q.returncode)
