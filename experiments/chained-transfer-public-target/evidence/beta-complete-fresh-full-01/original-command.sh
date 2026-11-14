#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$HOME/.elan/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
export ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0
cd /workspace/scratch/ct73-complete-replay-layout-01/cryptanalysis
out=/workspace/scratch/ct73-complete-full-01
date -u +%FT%TZ > "$out/start.txt"
timeout 2400 bash experiments/chained-transfer-public-target/ci_beta_complete/check.sh ../crypto /workspace/scratch/ct73-complete-driver-01 > "$out/native.txt" 2>&1
status=$?
printf '%s\n' "$status" > "$out/native.exit"
date -u +%FT%TZ > "$out/finish.txt"
python3 - "$out" <<'GUARDS'
from pathlib import Path
import hashlib,json,re,shutil,sys
o=Path(sys.argv[1]);d=Path('/workspace/scratch/ct73-complete-driver-01');before=json.loads((o/'before.json').read_text());after={p:hashlib.sha256(Path(p).read_bytes()).hexdigest()for p in before};changed=[p for p in before if before[p]!=after[p]];(o/'after.json').write_text(json.dumps(after,indent=2)+'\n');(o/'guards.json').write_text(json.dumps(dict(count=len(before),changed=changed),indent=2)+'\n')
receipt={'derived_cache_outside_captured_roots':str(d)+'-build-cache','actual_executable_paths':[]}
compile_text=(d/'compile.txt').read_text()if(d/'compile.txt').exists()else'';native_text=(d/'native.txt').read_text()if(d/'native.txt').exists()else''
a=re.search(r'Executable unittests src/lib.rs \(([^\n]+)\)',compile_text);b=re.search(r'Running unittests src/lib.rs \(([^\n]+)\)',native_text)
if a and b:
 assert a[1]==b[1];p=Path(a[1]);dest=o/'actual-test-executable.bin';shutil.copyfile(p,dest);receipt['actual_executable_paths'].append(dict(kind='unit',path=str(p),copied=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
 for name in['compare_native','audit_accounting_change','crt_identity','legacy_count_control']:
  p=Path(str(d)+'-build-cache')/'release'/name
  if p.is_file():
   dest=o/(name+'-executable.bin');shutil.copyfile(p,dest);receipt['actual_executable_paths'].append(dict(kind=name,path=str(p),copied=str(dest),sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
(o/'binary-custody.json').write_text(json.dumps(receipt,indent=2)+'\n')
if(o/'native.exit').read_text().strip()=='0':assert len(receipt['actual_executable_paths'])==5
raise SystemExit(bool(changed))
GUARDS
guard=$?
printf '%s\n' "$guard" > "$out/guard.exit"
if [ "$status" -ne 0 ]; then exit "$status"; fi
exit "$guard"
