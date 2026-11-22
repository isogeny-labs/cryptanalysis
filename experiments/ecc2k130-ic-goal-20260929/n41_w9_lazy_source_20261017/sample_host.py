"""Read-only host and worker resource sample for the native retry."""
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent
assert len(sys.argv) == 2
worker = psutil.Process(int(sys.argv[1]))
path = HERE / 'host_sample_retry1.json'
result = {'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'load_average': os.getloadavg(),
          'host_cpu_percent_over_one_second': psutil.cpu_percent(interval=1),
          'virtual_memory': psutil.virtual_memory()._asdict(),
          'worker_pid': worker.pid,
          'worker_cpu_times': worker.cpu_times()._asdict(),
          'worker_rss_bytes': worker.memory_info().rss,
          'worker_status': worker.status(),
          'worker_executable': worker.exe(),
          'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
with path.open('x') as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write('\n')
print(json.dumps({'load_average': result['load_average'],
                  'host_cpu_percent': result['host_cpu_percent_over_one_second'],
                  'worker_cpu_times': result['worker_cpu_times'],
                  'worker_rss_bytes': result['worker_rss_bytes']}))
