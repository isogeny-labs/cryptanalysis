#!/usr/bin/env python3
"""Cumulative L2 observations for the prospective Go coordinator campaign.

This is a standard-library adaptation of ``crypto/tools/icms/execute.py`` and
``crypto/tools/icms/gates.py``. Missing observations fail closed. Counted
metrics remain usable when L2 is withheld; callers must mark clocks invalid.
"""

from __future__ import annotations

import ctypes
from dataclasses import dataclass, field
import math
import os
from pathlib import Path
import signal
import subprocess
import threading
import time
from typing import Any


SAMPLE_INTERVAL_SECONDS = 0.01
THRESHOLDS = {
    "max_run_delay_fraction": 0.005,
    "min_schedstat_coverage": 0.90,
    "max_steal_fraction": 0.0,
    "max_foreign_sample_fraction": 0.0,
    "max_memory_full_stall_us": 0.0,
    "max_involuntary_switches_per_s": 50.0,
    "parallelism_slack": 0.05,
}
PREFLIGHT_LIMITS = {"settle_s": 2.0, "max_other_cpu": 0.10, "max_psi": 5.0}
_PR_SET_CHILD_SUBREAPER = 36


def read_psi(kind: str) -> dict[str, dict[str, float]] | None:
    try:
        lines = Path(f"/proc/pressure/{kind}").read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    result: dict[str, dict[str, float]] = {}
    try:
        for line in lines:
            if line:
                name, *fields = line.split()
                result[name] = {
                    key: float(value)
                    for key, value in (field.split("=", 1) for field in fields)
                }
    except (ValueError, TypeError):
        return None
    return result if set(result) == {"some", "full"} else None


def proc_stat() -> dict[str, Any]:
    keys = ("user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal")
    result: dict[str, Any] = {}
    try:
        lines = Path("/proc/stat").read_text(encoding="utf-8").splitlines()
    except OSError:
        return result
    for line in lines:
        fields = line.split()
        if fields and fields[0].startswith("cpu") and fields[0][3:].isdigit():
            try:
                values = [int(value) for value in fields[1:9]]
            except ValueError:
                continue
            result[fields[0]] = dict(zip(keys, values, strict=True))
        elif fields[:1] == ["procs_running"] and len(fields) == 2:
            try:
                result["procs_running"] = int(fields[1])
            except ValueError:
                pass
    return result


def _stat_fields(path: str) -> tuple[list[str], str] | None:
    try:
        text = Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None
    right = text.rfind(")")
    if right < 0:
        return None
    return text[right + 2 :].split(), text[text.find("(") + 1 : right]


def _cpu_ticks() -> dict[int, tuple[str, int]]:
    result: dict[int, tuple[str, int]] = {}
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        got = _stat_fields(f"/proc/{name}/stat")
        if got and len(got[0]) > 12:
            try:
                result[int(name)] = (got[1], int(got[0][11]) + int(got[0][12]))
            except ValueError:
                pass
    return result


def quiet_preflight(exclude: set[int]) -> dict[str, Any]:
    limits = dict(PREFLIGHT_LIMITS)
    before = _cpu_ticks()
    time.sleep(limits["settle_s"])
    after = _cpu_ticks()
    tick = os.sysconf("SC_CLK_TCK")
    used: dict[str, float] = {}
    for pid, (name, ticks) in after.items():
        if pid in exclude:
            continue
        delta = ticks - before.get(pid, (name, 0))[1]
        if delta > 0:
            used[f"{name}[{pid}]"] = delta / tick
    used = dict(sorted(used.items(), key=lambda item: (-item[1], item[0])))
    pressures = {kind: read_psi(kind) for kind in ("cpu", "memory")}
    values = [
        pressure["some"]["avg10"]
        for pressure in pressures.values()
        if pressure is not None
    ]
    psi_max = max(values) if values else None
    other = math.fsum(used.values())
    quiet = (
        psi_max is not None
        and other <= limits["max_other_cpu"] * limits["settle_s"]
        and psi_max <= limits["max_psi"]
    )
    return {
        "quiet": quiet,
        "other_cpu_seconds": other,
        "other_cpu_by_task": used,
        "other_top": dict(list(used.items())[:8]),
        "psi_some_avg10_max": psi_max,
        "pressures": pressures,
        "limits": limits,
    }


def evaluate_preflight(preflight: dict[str, Any]) -> dict[str, Any]:
    """Recompute the quiet-session decision from retained raw observations."""

    limits = preflight.get("limits")
    tasks = preflight.get("other_cpu_by_task")
    pressures = preflight.get("pressures")
    valid = (
        limits == PREFLIGHT_LIMITS
        and isinstance(tasks, dict)
        and isinstance(pressures, dict)
        and set(pressures) == {"cpu", "memory"}
        and all(_finite_nonnegative(value) for value in tasks.values())
    )
    psi_values: list[float] = []
    if valid:
        for kind in ("cpu", "memory"):
            pressure = pressures[kind]
            if not isinstance(pressure, dict) or set(pressure) != {"some", "full"}:
                valid = False
                break
            if any(
                not isinstance(pressure.get(scope), dict)
                or not {"avg10", "avg60", "avg300", "total"} <= set(pressure[scope])
                or any(
                    not _finite_nonnegative(pressure[scope][field])
                    for field in ("avg10", "avg60", "avg300", "total")
                )
                for scope in ("some", "full")
            ):
                valid = False
                break
            psi_values.append(float(pressure["some"]["avg10"]))
    other = math.fsum(float(value) for value in tasks.values()) if valid else None
    psi_max = max(psi_values) if valid and psi_values else None
    quiet = bool(
        valid
        and other is not None
        and psi_max is not None
        and other <= PREFLIGHT_LIMITS["max_other_cpu"] * PREFLIGHT_LIMITS["settle_s"]
        and psi_max <= PREFLIGHT_LIMITS["max_psi"]
    )
    receipt_matches = bool(
        valid
        and preflight.get("other_cpu_seconds") == other
        and preflight.get("psi_some_avg10_max") == psi_max
        and preflight.get("quiet") is quiet
        and preflight.get("other_top")
        == dict(list(sorted(tasks.items(), key=lambda item: (-item[1], item[0])))[:8])
    )
    return {
        "passes": quiet and receipt_matches,
        "raw_valid": valid,
        "receipt_matches": receipt_matches,
        "other_cpu_seconds": other,
        "psi_some_avg10_max": psi_max,
        "limits": dict(PREFLIGHT_LIMITS),
    }


def _finite_nonnegative(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _nonnegative_int(value: Any) -> bool:
    return type(value) is int and value >= 0


def parse_cpu_list(text: str) -> set[int]:
    result: set[int] = set()
    for field in text.strip().split(","):
        if not field:
            continue
        if "-" in field:
            left, right = field.split("-", 1)
            result.update(range(int(left), int(right) + 1))
        else:
            result.add(int(field))
    return result


def smt_siblings(cpu: int) -> set[int]:
    path = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/thread_siblings_list")
    try:
        return parse_cpu_list(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()


def evict(cpus: set[int], keep_pids: set[int]) -> dict[int, dict[str, Any]]:
    moved: dict[int, dict[str, Any]] = {}
    for task in Path("/proc").glob("[0-9]*/task/[0-9]*"):
        tid = int(task.name)
        pid = int(task.parent.parent.name)
        if pid in keep_pids:
            continue
        try:
            current = os.sched_getaffinity(tid)
        except OSError:
            continue
        target = current - cpus
        if not current & cpus or not target:
            continue
        try:
            got = _stat_fields(str(task / "stat"))
            if got is None or len(got[0]) <= 19:
                continue
            starttime = int(got[0][19])
            os.sched_setaffinity(tid, target)
            moved[tid] = {
                "pid": pid,
                "tid": tid,
                "starttime_ticks": starttime,
                "affinity": sorted(current),
                "evicted_affinity": sorted(os.sched_getaffinity(tid)),
            }
        except OSError:
            pass
    return moved


def unmovable_on(cpus: set[int], keep_pids: set[int]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {"user_threads": [], "kernel_threads": []}
    for task in Path("/proc").glob("[0-9]*/task/[0-9]*"):
        tid = int(task.name)
        pid = int(task.parent.parent.name)
        if pid in keep_pids:
            continue
        try:
            affinity = os.sched_getaffinity(tid)
        except OSError:
            continue
        if not affinity & cpus:
            continue
        got = _stat_fields(str(task / "stat"))
        record = {"pid": pid, "tid": tid, "comm": got[1] if got else None,
                  "affinity": sorted(affinity)}
        try:
            kernel_thread = not Path(f"/proc/{pid}/cmdline").read_bytes()
        except OSError:
            kernel_thread = False
        kind = "kernel_threads" if kernel_thread else "user_threads"
        if len(result[kind]) < 8:
            result[kind].append(record)
    return result


def restore(moved: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """Restore every affinity changed by :func:`evict`, with an auditable receipt.

    A task that exited during the session is not a restoration failure.  Every
    other error is retained and makes ``passes`` false; callers must not infer
    successful restoration merely because the cleanup path was attempted.
    """

    records: list[dict[str, Any]] = []
    for tid, identity in sorted(moved.items()):
        affinity = set(identity["affinity"])
        record = dict(identity)
        try:
            got = _stat_fields(f"/proc/{identity['pid']}/task/{tid}/stat")
            if got is None:
                raise ProcessLookupError
            if len(got[0]) <= 19 or int(got[0][19]) != identity["starttime_ticks"]:
                record["status"] = "identity_mismatch"
                records.append(record)
                continue
            os.sched_setaffinity(tid, affinity)
        except ProcessLookupError:
            record["status"] = "exited"
            records.append(record)
        except OSError as error:
            record.update({"status": "error", "errno": error.errno})
            records.append(record)
        else:
            readback = sorted(os.sched_getaffinity(tid))
            record.update(
                {
                    "status": "restored" if readback == sorted(affinity) else "readback_mismatch",
                    "restored_affinity": readback,
                }
            )
            records.append(record)
    failures = sum(
        record["status"] in {"error", "identity_mismatch", "readback_mismatch"}
        for record in records
    )
    return {
        "attempted": len(moved),
        "restored": sum(record["status"] == "restored" for record in records),
        "exited": sum(record["status"] == "exited" for record in records),
        "failures": failures,
        "passes": failures == 0,
        "records": records,
    }


def _become_subreaper() -> bool:
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        return libc.prctl(_PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) == 0
    except (OSError, AttributeError):
        return False


def _proc_table() -> dict[int, tuple[int, str, int, str]]:
    result: dict[int, tuple[int, str, int, str]] = {}
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        got = _stat_fields(f"/proc/{name}/stat")
        if got and len(got[0]) > 36:
            try:
                result[int(name)] = (int(got[0][1]), got[0][0], int(got[0][36]), got[1])
            except ValueError:
                pass
    return result


def _tree(root: int, table: dict[int, tuple[int, str, int, str]]) -> set[int]:
    children: dict[int, list[int]] = {}
    for pid, (ppid, *_rest) in table.items():
        children.setdefault(ppid, []).append(pid)
    result, stack = {root}, [root]
    while stack:
        for child in children.get(stack.pop(), []):
            if child not in result:
                result.add(child)
                stack.append(child)
    return result


def _descendants(root: int, me: int) -> set[int]:
    table: dict[int, tuple[int, int]] = {}
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        got = _stat_fields(f"/proc/{name}/stat")
        if got and len(got[0]) > 3:
            try:
                table[int(name)] = (int(got[0][1]), int(got[0][3]))
            except ValueError:
                pass
    process_table = {pid: (ppid, "", 0, "") for pid, (ppid, _sid) in table.items()}
    result = {pid for pid, (ppid, sid) in table.items() if sid == root or ppid == me}
    result |= _tree(root, process_table)
    result.discard(root)
    result.discard(me)
    return result


def _kill_descendants(root: int, me: int) -> int:
    killed: set[int] = set()
    for _ in range(5):
        remaining = _descendants(root, me) - killed
        if not remaining:
            break
        for pid in remaining:
            try:
                os.kill(pid, signal.SIGKILL)
                killed.add(pid)
            except ProcessLookupError:
                pass
        for pid in remaining:
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass
        time.sleep(0.01)
    return len(killed)


def _tids(pid: int) -> list[int]:
    try:
        return [int(value) for value in os.listdir(f"/proc/{pid}/task")]
    except OSError:
        return []


def _schedstat(pid: int, tid: int) -> tuple[int, int, int] | None:
    try:
        fields = Path(f"/proc/{pid}/task/{tid}/schedstat").read_text().split()[:3]
        values = tuple(int(field) for field in fields)
    except (OSError, ValueError):
        return None
    return values if len(values) == 3 else None  # type: ignore[return-value]


def _iter_tasks():
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        pid = int(name)
        for tid in _tids(pid):
            got = _stat_fields(f"/proc/{pid}/task/{tid}/stat")
            if got and len(got[0]) > 36:
                try:
                    yield pid, tid, got[0][0], int(got[0][36]), got[1], int(got[0][3])
                except ValueError:
                    pass


def _foreign_runnable(cpus: set[int], exclude: set[int], session: int):
    return [
        {"pid": pid, "tid": tid, "comm": comm, "cpu": cpu}
        for pid, tid, state, cpu, comm, sid in _iter_tasks()
        if state == "R" and cpu in cpus and pid not in exclude and sid != session
    ]


@dataclass(eq=False)
class Sampler(threading.Thread):
    tree_cpus: set[int]
    foreign_scan_cpus: set[int]
    own: set[int]
    interval: float
    child_pid: int = 0
    samples: int = 0
    samples_foreign: int = 0
    foreign_examples: list[dict[str, Any]] = field(default_factory=list)
    max_threads: int = 0
    schedstat: dict[int, tuple[int, int, int]] = field(default_factory=dict)
    cpus_seen: set[int] = field(default_factory=set)
    outside: int = 0
    outside_examples: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.halt = threading.Event()

    def poll_tree(self) -> set[int]:
        tree = _tree(self.child_pid, _proc_table()) if self.child_pid else set()
        threads = 0
        for pid in tree:
            for tid in _tids(pid):
                threads += 1
                schedstat = _schedstat(pid, tid)
                if schedstat is not None:
                    self.schedstat[tid] = schedstat
                try:
                    mask = os.sched_getaffinity(tid)
                except OSError:
                    mask = None
                got = _stat_fields(f"/proc/{pid}/task/{tid}/stat")
                last = int(got[0][36]) if got and len(got[0]) > 36 else None
                if last is not None:
                    self.cpus_seen.add(last)
                if ((mask is not None and not mask <= self.tree_cpus)
                        or (last is not None and last not in self.tree_cpus)):
                    self.outside += 1
                    if len(self.outside_examples) < 8:
                        self.outside_examples.append({
                            "pid": pid, "tid": tid,
                            "mask": sorted(mask) if mask is not None else None,
                            "last_cpu": last, "comm": got[1] if got else None,
                        })
        self.max_threads = max(self.max_threads, threads)
        return tree

    def run(self) -> None:
        while not self.halt.is_set():
            tree = self.poll_tree()
            foreign = _foreign_runnable(
                self.foreign_scan_cpus, self.own | tree, self.child_pid
            )
            self.samples += 1
            if foreign:
                self.samples_foreign += 1
                if len(self.foreign_examples) < 8:
                    self.foreign_examples.append(foreign[0])
            self.halt.wait(self.interval)


def _jiffies(snapshot: dict[str, Any], cpus: set[int]) -> dict[str, int]:
    keys = ("user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal")
    result = dict.fromkeys(keys, 0)
    for cpu in cpus:
        row = snapshot.get(f"cpu{cpu}") or {}
        for key in keys:
            result[key] += int(row.get(key, 0))
    return result


def _psi_totals() -> dict[str, Any]:
    result = {}
    for resource_name in ("cpu", "memory"):
        pressure = read_psi(resource_name)
        result[resource_name] = (None if pressure is None else {
            kind: values.get("total") for kind, values in pressure.items()
        })
    return result


def run_measured(argv: list[str], cpus: set[int], env: dict[str, str],
                 stdout_path: Path, stderr_path: Path, timeout_s: float,
                 reserved_cpus: set[int] | None = None) -> dict[str, Any]:
    me = os.getpid()
    reserved = set(cpus if reserved_cpus is None else reserved_cpus)
    if not cpus or not cpus <= reserved:
        raise ValueError("measured CPUs must be a nonempty subset of the reserved core")
    subreaper = _become_subreaper()
    psi0, stat0 = _psi_totals(), proc_stat()
    sampler = Sampler(set(cpus), reserved, {me}, SAMPLE_INTERVAL_SECONDS)

    def pin_child() -> None:
        os.sched_setaffinity(0, cpus)

    process: subprocess.Popen[bytes] | None = None
    sampler_started = False
    reaped = False
    status: int | None = None
    usage = None
    observed_affinity: list[int] | None = None
    timed_out = False
    descendants_killed = 0
    started = finished = time.monotonic_ns()
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            started = time.monotonic_ns()
            process = subprocess.Popen(
                argv,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                preexec_fn=pin_child,
                start_new_session=True,
            )
            sampler.child_pid = process.pid
            sampler.start()
            sampler_started = True
            try:
                observed_affinity = sorted(os.sched_getaffinity(process.pid))
            except OSError:
                observed_affinity = None
            deadline = time.monotonic() + timeout_s
            while True:
                info = os.waitid(
                    os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT
                )
                if info is not None:
                    finished = time.monotonic_ns()
                    sampler.poll_tree()
                    _, status, usage = os.wait4(process.pid, 0)
                    reaped = True
                    break
                if time.monotonic() > deadline:
                    timed_out = True
                    os.killpg(process.pid, signal.SIGKILL)
                    _, status, usage = os.wait4(process.pid, 0)
                    reaped = True
                    finished = time.monotonic_ns()
                    break
                time.sleep(0.002)
        finally:
            sampler.halt.set()
            if process is not None and not reaped:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                descendants_killed += _kill_descendants(process.pid, me)
                try:
                    os.waitpid(process.pid, 0)
                except ChildProcessError:
                    pass
            if sampler_started:
                sampler.join()
            if process is not None:
                descendants_killed += _kill_descendants(process.pid, me)
    psi1, stat1 = _psi_totals(), proc_stat()
    j0, j1 = _jiffies(stat0, reserved), _jiffies(stat1, reserved)
    psi_delta: dict[str, Any] = {}
    for resource_name, after in psi1.items():
        before = psi0.get(resource_name)
        psi_delta[resource_name] = (None if before is None or after is None else {
            kind: after[kind] - before.get(kind, 0.0) for kind in after
        })
    assert process is not None and usage is not None and status is not None
    code = os.waitstatus_to_exitcode(status)
    return {
        "pinned_cpus": sorted(cpus),
        "reserved_cpus": sorted(reserved),
        "child_affinity_observed": observed_affinity,
        "tree_affinity": {"tasks_outside": sampler.outside,
                          "cpus_seen": sorted(sampler.cpus_seen),
                          "examples": sampler.outside_examples},
        "subreaper": subreaper,
        "descendants_killed": descendants_killed,
        "exit": {"returncode": code if code >= 0 else None,
                 "signal": -code if code < 0 else None, "timed_out": timed_out},
        "wall_ns": finished - started,
        "rusage": {"user_s": usage.ru_utime, "sys_s": usage.ru_stime,
                   "maxrss_kib": usage.ru_maxrss, "minflt": usage.ru_minflt,
                   "majflt": usage.ru_majflt, "nvcsw": usage.ru_nvcsw,
                   "nivcsw": usage.ru_nivcsw},
        "schedstat": {"run_ns": sum(value[0] for value in sampler.schedstat.values()),
                      "wait_ns": sum(value[1] for value in sampler.schedstat.values()),
                      "slices": sum(value[2] for value in sampler.schedstat.values()),
                      "threads_seen": len(sampler.schedstat),
                      "sample_interval_seconds": SAMPLE_INTERVAL_SECONDS},
        "max_threads_observed": sampler.max_threads,
        "contention": {"samples": sampler.samples,
                       "samples_with_foreign_runnable": sampler.samples_foreign,
                       "foreign_examples": sampler.foreign_examples,
                       "pinned_cpu_jiffies_delta": {key: j1[key] - j0[key] for key in j0},
                       "psi_total_delta_us": psi_delta,
                       "procs_running_after": stat1.get("procs_running")},
    }


def evaluate_l2(execution: dict[str, Any], preflight: dict[str, Any],
                reservation: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, level: str, observed: Any, threshold: Any, passes: bool) -> None:
        checks.append({"id": name, "level": level, "observed": observed, "threshold": threshold,
                       "status": "pass" if passes else "fail"})

    pinned = execution.get("pinned_cpus")
    tree = execution.get("tree_affinity") or {}
    wall = execution.get("wall_ns")
    rusage = execution.get("rusage") or {}
    sched = execution.get("schedstat") or {}
    contention = execution.get("contention") or {}
    jiffies = contention.get("pinned_cpu_jiffies_delta")
    psi_delta = contention.get("psi_total_delta_us")
    jiffy_keys = {"user", "nice", "system", "idle", "iowait", "irq", "softirq", "steal"}
    domains_ok = (
        isinstance(pinned, list) and bool(pinned)
        and all(_nonnegative_int(value) for value in pinned)
        and len(pinned) == len(set(pinned))
        and _nonnegative_int(wall) and wall > 0
        and all(_finite_nonnegative(rusage.get(key)) for key in ("user_s", "sys_s"))
        and all(_nonnegative_int(rusage.get(key)) for key in
                ("maxrss_kib", "minflt", "majflt", "nvcsw", "nivcsw"))
        and all(_nonnegative_int(sched.get(key)) for key in
                ("run_ns", "wait_ns", "slices", "threads_seen"))
        and _finite_nonnegative(sched.get("sample_interval_seconds"))
        and type(contention.get("samples")) is int
        and type(contention.get("samples_with_foreign_runnable")) is int
        and 0 <= contention["samples_with_foreign_runnable"] <= contention["samples"]
        and isinstance(jiffies, dict) and set(jiffies) == jiffy_keys
        and all(_nonnegative_int(value) for value in jiffies.values())
        and isinstance(psi_delta, dict) and set(psi_delta) == {"cpu", "memory"}
        and all(
            isinstance(psi_delta[kind], dict)
            and set(psi_delta[kind]) == {"some", "full"}
            and all(_finite_nonnegative(value) for value in psi_delta[kind].values())
            for kind in ("cpu", "memory")
        )
        and _nonnegative_int(tree.get("tasks_outside"))
        and isinstance(tree.get("cpus_seen"), list)
        and all(_nonnegative_int(value) for value in tree["cpus_seen"])
        and _nonnegative_int(execution.get("descendants_killed"))
    )
    check("raw_observation_domains", "L1", {"valid": domains_ok},
          "finite nonnegative exact-domain cumulative observations", domains_ok)
    check(
        "whole_tree_affinity", "L1",
        {"root": execution.get("child_affinity_observed"),
         "tasks_outside": tree.get("tasks_outside"), "cpus_seen": tree.get("cpus_seen")},
        pinned,
        domains_ok and execution.get("child_affinity_observed") == pinned
        and tree.get("tasks_outside") == 0
        and set(tree.get("cpus_seen", [])) <= set(pinned),
    )
    check("excludes_cpu0", "L1", pinned, "CPU 0 excluded",
          isinstance(pinned, list) and 0 not in pinned)
    check("process_tree_cleanup", "L1",
          {"subreaper": execution.get("subreaper"),
           "descendants_killed": execution.get("descendants_killed")},
          {"subreaper": True, "descendants_killed": 0},
          execution.get("subreaper") is True and execution.get("descendants_killed") == 0)
    reserved = execution.get("reserved_cpus")
    left = reservation.get("left_on_reserved") or {}
    reservation_ok = (
        reservation.get("evicted") is True
        and isinstance(reserved, list)
        and reserved == reservation.get("cpus") == reservation.get("smt_siblings")
        and isinstance(left, dict)
        and set(left) == {"user_threads", "kernel_threads"}
        and isinstance(left.get("user_threads"), list)
        and not left["user_threads"]
    )
    check("whole_core_reservation", "L1",
          {"execution_reserved": reserved, "receipt": reservation},
          "all SMT siblings reserved; foreign user threads evicted", reservation_ok)

    cpu_ns = ((rusage["user_s"] + rusage["sys_s"]) * 1_000_000_000
              if domains_ok else None)
    parallelism = max(cpu_ns, sched["run_ns"]) / wall if domains_ok else None
    check("parallelism", "L1", parallelism, 1 + THRESHOLDS["parallelism_slack"],
          parallelism is not None and parallelism <= 1 + THRESHOLDS["parallelism_slack"])
    coverage = sched["run_ns"] / cpu_ns if domains_ok and cpu_ns > 0 else None
    check("schedstat_coverage", "L2", coverage, THRESHOLDS["min_schedstat_coverage"],
          coverage is not None and coverage >= THRESHOLDS["min_schedstat_coverage"])
    total_runnable = sched["run_ns"] + sched["wait_ns"] if domains_ok else 0
    delay = sched["wait_ns"] / total_runnable if total_runnable > 0 else None
    check("run_delay", "L2", delay, THRESHOLDS["max_run_delay_fraction"],
          delay is not None and coverage is not None
          and coverage >= THRESHOLDS["min_schedstat_coverage"]
          and delay <= THRESHOLDS["max_run_delay_fraction"])
    total_jiffies = sum(jiffies.values()) if domains_ok else 0
    steal = jiffies["steal"] / total_jiffies if total_jiffies > 0 else None
    check("steal", "L2", steal, THRESHOLDS["max_steal_fraction"],
          steal is not None and steal <= THRESHOLDS["max_steal_fraction"])
    samples = contention["samples"] if domains_ok else 0
    foreign = (contention["samples_with_foreign_runnable"] / samples
               if samples > 0 else None)
    check("foreign_runnable", "L2", foreign, THRESHOLDS["max_foreign_sample_fraction"],
          foreign is not None and foreign <= THRESHOLDS["max_foreign_sample_fraction"])
    memory = psi_delta["memory"] if domains_ok else None
    memory_full = None if memory is None else memory["full"]
    check("memory_full_stall_us", "L2", memory_full,
          THRESHOLDS["max_memory_full_stall_us"],
          memory_full is not None and memory_full <= THRESHOLDS["max_memory_full_stall_us"])
    switch_rate = rusage["nivcsw"] / (wall / 1_000_000_000) if domains_ok else None
    check("involuntary_switches_per_s", "L2", switch_rate,
          THRESHOLDS["max_involuntary_switches_per_s"],
          switch_rate is not None
          and switch_rate <= THRESHOLDS["max_involuntary_switches_per_s"])
    preflight_result = evaluate_preflight(preflight)
    check("quiet_preflight", "L2", preflight_result, PREFLIGHT_LIMITS,
          preflight_result["passes"])
    l1_passes = all(item["status"] == "pass" for item in checks if item["level"] == "L1")
    l2_passes = l1_passes and all(
        item["status"] == "pass" for item in checks if item["level"] == "L2"
    )
    earned = "L2" if l2_passes else "L1" if l1_passes else "L0"
    return {"required_level": "L2", "earned_level": earned,
            "passes": l2_passes,
            "blocking": [item["id"] for item in checks if item["status"] != "pass"],
            "checks": checks, "thresholds": dict(THRESHOLDS)}
