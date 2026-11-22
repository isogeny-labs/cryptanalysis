"""Non-secret host observations; placement is not exclusive isolation."""
import os
from pathlib import Path
import platform
import sys


def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def snapshot(cpu):
    cgroup = {name: read('/sys/fs/cgroup/'+name) for name in [
        'cpu.max', 'cpu.stat', 'memory.max', 'memory.current', 'memory.events',
        'cpu.pressure', 'memory.pressure']}
    cpuinfo = read('/proc/cpuinfo') or ''
    stat = read('/proc/stat') or ''
    return {'platform': platform.platform(), 'python': platform.python_version(),
            'python_executable': sys.executable,
            'cpu_model': next((line.split(':', 1)[1].strip() for line in cpuinfo.splitlines()
                               if line.startswith('model name')), 'unknown'),
            'aggregate_proc_stat_cpu': next((line for line in stat.splitlines()
                                             if line.startswith('cpu ')), None),
            'allowed_cpus': sorted(os.sched_getaffinity(0)), 'selected_cpu': cpu,
            'numa_nodes_visible_for_cpu': [p.name for p in Path(
                f'/sys/devices/system/cpu/cpu{cpu}').glob('node*')],
            'governor': read(f'/sys/devices/system/cpu/cpu{cpu}/cpufreq/scaling_governor'),
            'memory': read('/proc/meminfo'), 'cgroup': cgroup,
            'placement_is_exclusive': False, 'isolation_receipt': None,
            'dimm_configuration': 'unknown', 'first_touch_numa_policy': 'unknown',
            'standing': 'unverified'}
