#!/usr/bin/env python3
"""Import authoritative native metadata without backdating bookkeeping."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shlex

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
p = argparse.ArgumentParser()
p.add_argument('record', type=Path)
a = p.parse_args()
rec = json.loads(a.record.read_text())
assert rec['status'] == 'open' and not rec['commands'] and 'coordinator_at_init' not in rec
m = json.loads((P/'setup-fresh-native-job-metadata.json').read_text())
s = json.loads((P/'setup-fresh-runner-status.json').read_text())
h = json.loads((P/'timing-setup-001/host.json').read_text())
assert s['returncode'] == 0 and not m['git']['dirty']
rec['coordinator_at_init'] = {k: rec[k] for k in ['host', 'commit', 'commit_dirty', 'created_utc']}
assert datetime.datetime.fromisoformat(rec['created_utc']).timestamp() < s['started'], 'Record must precede execution'
rec['record_import'] = 'Initialized before execution; original coordinator capture and creation time retained. Native source/hardware/timestamps imported from the original runner receipt.'
rec['commit'] = m['git']['commit']
rec['commit_dirty'] = m['git']['dirty']
rec['host'] = dict(hostname=s['host'], cpu=s['cpu_model'], cpus_online=s['cpus'],
                   platform=h['platform'], isolation='exploratory same-allocation paired CPU comparison; failed A/A gates; no qualified tier',
                   allowed_cpus=h['allowed_cpus'], selected_cpu=h['selected_cpu'],
                   memory_gib=s['mem_gb'], provider='Modal', allocation_id=m['sandboxes'][0])
rec['gpu'] = dict(devices=[], allocation_devices=s['gpus'], arithmetic='CPU only')
rec['commands'] = [dict(argv=shlex.split(m['command']), cwd='/work/repo', exit=s['returncode'],
                        started_utc=datetime.datetime.fromtimestamp(s['started'], datetime.timezone.utc).isoformat(),
                        wall_s=s['seconds'], native_job_id=m['job'])]
rec['native_execution_receipt'] = dict(path=str((P/'setup-fresh-runner-status.json').relative_to(ROOT)),
                                      sha256=hashlib.sha256((P/'setup-fresh-runner-status.json').read_bytes()).hexdigest())
a.record.write_text(json.dumps(rec, indent=2, sort_keys=True)+'\n')
print('Bound native hardware/source/timestamps; retrospective record creation remains explicit')
