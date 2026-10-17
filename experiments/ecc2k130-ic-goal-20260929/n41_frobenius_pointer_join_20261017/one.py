import json
import pathlib
import resource
import subprocess
import sys
import time

binary, source, stem = map(pathlib.Path, sys.argv[1:])
t0=time.monotonic()
p=subprocess.run([str(binary),str(source)],capture_output=True,text=True,timeout=180)
wall=time.monotonic()-t0
pathlib.Path(str(stem)+'.stdout').write_text(p.stdout)
pathlib.Path(str(stem)+'.stderr').write_text(p.stderr)
print(json.dumps({'exit_code':p.returncode,'parent_wall_s':wall,
                  'peak_child_rss_bytes':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
                  'lines':p.stdout.splitlines()}))
