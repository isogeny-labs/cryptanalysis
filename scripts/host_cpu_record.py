#!/usr/bin/env python3
"""Record the CPU a measurement ran on: model, ISA flags, microcode, caches, kernel.

`scripts/isolated_bench.py probe-host` (the host probe every n=83 workflow
writes to `host-probe.json`) records the kernel, cgroups and NUMA nodes but not
the CPU model, its flags or its microcode. GitHub's `ubuntu-24.04` runners
rotate between at least AMD EPYC 7763 (Zen 3: AVX2 and 256-bit VPCLMULQDQ, no
AVX-512, no GFNI), AMD EPYC 9V74 and Intel Xeon Platinum 8573C hosts, so a
per-probe wall time can depend on which one a job drew. This helper records
that, so a receipt names its host class.

It is a new, standalone helper (standard library only) so that frozen
experiments and running workflows keep the `isolated_bench.py` they pinned.
New experiments call it in one of three ways:

* `python3 scripts/host_cpu_record.py > host-cpu.json`
* `python3 scripts/host_cpu_record.py --merge-into host-probe.json`: adds the
  record under the key `cpu_record` to an existing `probe-host` JSON (the file
  is rewritten with sorted keys; nothing else in it changes);
* `import host_cpu_record; host_cpu_record.record()` from Python, with
  `scripts/` on `sys.path`.

What it records (fields that the host does not expose are `null`, never
guessed):

* `model_name`, `vendor_id`, `cpu_family`, `model`, `stepping`, `microcode`
  and `cpu_mhz` of the execution CPU (the lowest CPU in the affinity mask, or
  `--cpu`), plus whether every logical CPU reports the same model, microcode
  and flags;
* `flags_of_interest`: true/false for `pclmulqdq`, `vpclmulqdq`, `gfni`,
  `avx`, `avx2`, `bmi1`, `bmi2`, `adx`, `aes`, `vaes`, `sha_ni`, `popcnt`,
  `fma`, every `avx512*` flag the vocabulary below lists, and `hypervisor`;
  `avx512_flags_present` lists every `avx512*` flag the CPU reports;
* `flags_sha256` and the full sorted `flags` list, so two receipts compare
  exactly; `bugs` as reported;
* `host_class`: one short string, `<model name> | avx512=<y/n> gfni=<y/n>
  vpclmulqdq=<y/n> avx2=<y/n> bmi2=<y/n>`, for grouping receipts;
* `caches`: every `/sys/devices/system/cpu/cpu<N>/cache/index*` entry of the
  execution CPU (level, type, size, ways, line size, sets, shared CPU list),
  and the `cache size` line of `/proc/cpuinfo`;
* `topology`: logical CPUs online, siblings, cores per socket, threads per
  core and sockets (from `lscpu` when present), and the process affinity;
* `kernel`: `uname` release, version and machine, `/proc/version`, the boot
  command line and the transparent-huge-page settings;
* `lscpu`: the raw `lscpu -J` fields when the tool is installed.

No timing is read or produced.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "host-cpu-record-v1"
FLAGS_OF_INTEREST = (
    "pclmulqdq", "vpclmulqdq", "gfni", "avx", "avx2", "bmi1", "bmi2", "adx", "aes", "vaes",
    "sha_ni", "popcnt", "fma", "avx512f", "avx512dq", "avx512cd", "avx512bw", "avx512vl",
    "avx512ifma", "avx512vbmi", "avx512_vbmi2", "avx512_vnni", "avx512_bitalg",
    "avx512_vpopcntdq", "avx512_bf16", "avx512_fp16", "avx512_vp2intersect", "hypervisor",
)
CLASS_FLAGS = ("gfni", "vpclmulqdq", "avx2", "bmi2")


def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def processors(text):
    """[{key: value}] per logical CPU block of /proc/cpuinfo."""
    blocks, current = [], {}
    for line in (text or "").splitlines():
        if not line.strip():
            if current:
                blocks.append(current)
                current = {}
            continue
        if ":" in line:
            key, value = (part.strip() for part in line.split(":", 1))
            current.setdefault(key, value)
    if current:
        blocks.append(current)
    return blocks


def execution_cpu(requested):
    if requested is not None:
        return requested
    try:
        return min(os.sched_getaffinity(0))
    except (AttributeError, OSError, ValueError):
        return 0


def caches(cpu):
    out = []
    root = Path("/sys/devices/system/cpu/cpu%d/cache" % cpu)
    for index in sorted(root.glob("index[0-9]*"), key=lambda p: int(p.name[5:])):
        out.append({"index": index.name, "level": read(index / "level"), "type": read(index / "type"),
                    "size": read(index / "size"), "ways_of_associativity": read(index / "ways_of_associativity"),
                    "coherency_line_size": read(index / "coherency_line_size"),
                    "number_of_sets": read(index / "number_of_sets"),
                    "shared_cpu_list": read(index / "shared_cpu_list")})
    return out


def lscpu():
    tool = shutil.which("lscpu")
    if not tool:
        return None
    try:
        proc = subprocess.run([tool, "-J"], capture_output=True, text=True, timeout=10,
                              env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
        fields = json.loads(proc.stdout)["lscpu"]
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired):
        return None
    flat = {}

    def walk(items):
        for item in items:
            flat[item.get("field", "").rstrip(":")] = item.get("data")
            walk(item.get("children") or [])
    walk(fields)
    flat.pop("Flags", None)  # recorded once, in `flags`
    return flat


def number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def record(cpu=None):
    blocks = processors(read("/proc/cpuinfo"))
    cpu = execution_cpu(cpu)
    mine = next((b for b in blocks if number(b.get("processor")) == cpu), blocks[0] if blocks else {})
    flags = sorted(set((mine.get("flags") or mine.get("Features") or "").split()))
    have = set(flags)
    avx512 = sorted(flag for flag in flags if flag.startswith("avx512"))
    model_name = mine.get("model name") or mine.get("Hardware") or mine.get("Processor")
    lscpu_fields = lscpu()

    def uniform(key):
        values = {b.get(key) for b in blocks}
        return len(values) == 1 if blocks else None

    host_class = "%s | avx512=%s %s" % (model_name, "y" if avx512 else "n",
                                         " ".join("%s=%s" % (f, "y" if f in have else "n") for f in CLASS_FLAGS))
    try:
        affinity = sorted(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        affinity = None
    uname = platform.uname()
    thp = {name: read(Path("/sys/kernel/mm/transparent_hugepage") / name) for name in ("enabled", "defrag")}
    return {
        "schema": SCHEMA,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "execution_cpu": cpu,
        "model_name": model_name,
        "vendor_id": mine.get("vendor_id"),
        "cpu_family": mine.get("cpu family"),
        "model": mine.get("model"),
        "stepping": mine.get("stepping"),
        "microcode": mine.get("microcode"),
        "cpu_mhz": mine.get("cpu MHz"),
        "cache_size_cpuinfo": mine.get("cache size"),
        "flags_of_interest": {flag: flag in have for flag in FLAGS_OF_INTEREST},
        "avx512_flags_present": avx512,
        "host_class": host_class,
        "flags": flags,
        "flags_sha256": hashlib.sha256(" ".join(flags).encode()).hexdigest(),
        "bugs": (mine.get("bugs") or "").split() or None,
        "all_cpus_uniform": {"model_name": uniform("model name"), "microcode": uniform("microcode"),
                             "flags": uniform("flags")},
        "caches": caches(cpu),
        "topology": {"logical_cpus_in_cpuinfo": len(blocks), "online": read("/sys/devices/system/cpu/online"),
                     "siblings": mine.get("siblings"), "cpu_cores": mine.get("cpu cores"),
                     "threads_per_core": (lscpu_fields or {}).get("Thread(s) per core"),
                     "cores_per_socket": (lscpu_fields or {}).get("Core(s) per socket"),
                     "sockets": (lscpu_fields or {}).get("Socket(s)"),
                     "affinity": affinity},
        "kernel": {"release": uname.release, "version": uname.version, "machine": uname.machine,
                   "proc_version": read("/proc/version"), "cmdline": read("/proc/cmdline"),
                   "transparent_hugepage": thp},
        "lscpu": lscpu_fields,
        "source": "scripts/host_cpu_record.py (/proc/cpuinfo, /sys/devices/system/cpu, uname, lscpu -J)",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cpu", type=int, help="execution CPU (default: lowest CPU of the affinity mask)")
    parser.add_argument("--merge-into", type=Path,
                        help="add the record as `cpu_record` to this existing host-probe JSON file")
    parser.add_argument("--out", type=Path, help="also write the record here")
    args = parser.parse_args()
    result = record(args.cpu)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text)
    if args.merge_into:
        probe = json.loads(args.merge_into.read_text())
        if "cpu_record" in probe:
            raise SystemExit("%s already has a cpu_record" % args.merge_into)
        probe["cpu_record"] = result
        args.merge_into.write_text(json.dumps(probe, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"merged_into": str(args.merge_into), "host_class": result["host_class"],
                          "microcode": result["microcode"]}, sort_keys=True))
        return
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
