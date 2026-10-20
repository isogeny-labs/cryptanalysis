#!/usr/bin/env python3
"""Reuse-panel runner with exact per-child Linux peak RSS receipts.

The previous runner is retained for replay of its frozen panels. This runner
uses the same serial queue, host probes, and timing boundary. Only child
collection changes: wait4 returns the resource use of one measured process.
"""

import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time

import run_tier1_rho_closeout as base


def wait_child(proc, deadline):
    """Reap exactly one child and return (timed_out, wait4 rusage)."""
    timed_out = False
    while True:
        try:
            pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
        except InterruptedError:
            continue
        if pid:
            proc.returncode = os.waitstatus_to_exitcode(status)
            return timed_out, usage
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            while True:
                try:
                    _, status, usage = os.wait4(proc.pid, 0)
                    break
                except InterruptedError:
                    continue
            proc.returncode = os.waitstatus_to_exitcode(status)
            return timed_out, usage
        time.sleep(min(remaining, 0.005))


def arm_peak(manifest, case, repeat, variant, serial, folder):
    cpu = manifest['isolation']['execution_cpu']
    argv = case[variant]
    before = base.counters(cpu)
    stem = f'{serial:05d}'
    stdout_path = folder / f'{stem}.stdout.txt'
    stderr_path = folder / f'{stem}.stderr.txt'
    begin = time.monotonic_ns()

    def pin():
        os.sched_setaffinity(0, {cpu})

    with stdout_path.open('wb') as stdout_file, stderr_path.open('wb') as stderr_file:
        proc = subprocess.Popen(argv, cwd=manifest['workdir'], env=base.env(),
                                stdout=stdout_file, stderr=stderr_file,
                                preexec_fn=pin, start_new_session=True)
        timed_out, usage = wait_child(
            proc, time.monotonic() + manifest['timeout_s'])
    outer_ms = (time.monotonic_ns() - begin) / 1e6
    after = base.counters(cpu)
    stdout = stdout_path.read_text(errors='replace')
    stderr = stderr_path.read_text(errors='replace')
    fields = base.parse_fields(stdout)
    delta = base.deltas(before, after)
    peak_rss_kib = int(usage.ru_maxrss)  # Linux wait4 reports KiB.
    issues = []
    if proc.returncode != 0 or timed_out or stderr:
        issues.append('process failed, timed out, or wrote stderr')
    if fields.get('verified') != '1' or fields.get('point') != case['expected_result']:
        issues.append('point verification failed')
    try:
        online = float(fields['online_ms'])
        if not math.isfinite(online) or online <= 0:
            raise ValueError()
    except (KeyError, ValueError):
        online = None
        issues.append('online metric missing')
    if peak_rss_kib <= 0:
        issues.append('child peak RSS missing')
    if delta['cgroup_v1_cpu_stat'].get('nr_throttled', 0) or delta[
            'cgroup_v2_cpu_stat'].get('nr_throttled', 0):
        issues.append('CPU throttling')
    if delta['cgroup_v2_memory_events'].get('oom', 0) or delta[
            'cgroup_v2_memory_events'].get('oom_kill', 0):
        issues.append('memory OOM')
    if delta['cpu_times'] and len(delta['cpu_times']) > 7 and delta['cpu_times'][7]:
        issues.append('CPU steal time')
    if usage.ru_majflt > 0:
        issues.append('major fault')
    postflight = base.probe(manifest)
    if not postflight['ok']:
        issues.append('postflight failed')
    return {
        'serial': serial, 'case': case['id'], 'repeat': repeat, 'variant': variant,
        'status': 'valid' if not issues else 'invalid', 'issues': issues,
        'measurement_tier': 'tier1_instance', 'command': argv,
        'binary_sha256': base.digest(argv[0]), 'returncode': proc.returncode,
        'timed_out': timed_out, 'environment': base.env(), 'online_ms': online,
        'outer_ms': outer_ms, 'fields': fields,
        'before': before, 'after': after,
        'tier1_observations': {'counter_deltas': delta},
        'child_involuntary_switches': usage.ru_nivcsw,
        'child_major_faults': usage.ru_majflt,
        'child_peak_rss_kib': peak_rss_kib,
        'child_peak_rss_method': 'linux_wait4_ru_maxrss_kib',
        'postflight': postflight, 'stdout_file': stdout_path.name,
        'stderr_file': stderr_path.name,
    }


old_run = base.run


def run_peak(manifest, folder):
    result = old_run(manifest, folder)
    summary_path = folder / 'summary.json'
    summary = json.loads(summary_path.read_text())
    summary['runner_sha256'] = base.digest(Path(__file__))
    summary['runner_dependency_sha256'] = base.digest(Path(base.__file__))
    summary['child_peak_rss_method'] = 'linux_wait4_ru_maxrss_kib'
    base.write(summary_path, summary)
    return summary


def main():
    base.arm = arm_peak
    base.run = run_peak
    base.main()


if __name__ == '__main__':
    main()
