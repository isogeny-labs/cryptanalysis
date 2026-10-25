import json, subprocess, sys, time
from pathlib import Path
root = Path('/home/ec2-user/cryptanalysis-proof-audit-20261021')
checks = sorted(root.glob('experiments/**/check.py'))
checks = [p for p in checks if p.parent.name != 'prime-j0-axis152-20261012']
results = []
out = Path('/var/tmp/cryptanalysis-check-replay-20261021.json')
for path in checks:
    start = time.monotonic()
    try:
        run = subprocess.run([sys.executable, str(path), '--check'], cwd=root, capture_output=True, text=True, timeout=600)
        row = {'path': str(path.relative_to(root)), 'exit': run.returncode, 'seconds': round(time.monotonic()-start, 1), 'stdout': run.stdout, 'stderr': run.stderr}
    except subprocess.TimeoutExpired as exc:
        row = {'path': str(path.relative_to(root)), 'exit': 'TIMEOUT', 'seconds': round(time.monotonic()-start, 1), 'stdout': (exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout,bytes) else exc.stdout or '', 'stderr': (exc.stderr or b'').decode(errors='replace') if isinstance(exc.stderr,bytes) else exc.stderr or ''}
    results.append(row)
    out.write_text(json.dumps(results, indent=2)+'\n')
    print(f"{row['exit']} {row['seconds']}s {row['path']}", flush=True)
print(f"completed {len(results)} checks; {sum(r['exit']==0 for r in results)} passed", flush=True)
