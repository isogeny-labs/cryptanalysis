"""Frozen signed-pair orbit index versus flat-row index, both with fused scan."""
import csv
import hashlib
import json
import os
import platform
from pathlib import Path
import random
import resource
import runpy
import shutil
import subprocess
import sys
import tempfile
from time import perf_counter_ns

HERE = Path(__file__).resolve().parent
COMMON = HERE.parent / "m31-full-rust-comparison"
helpers = runpy.run_path(str(COMMON / "replay.py"))
ROOT = helpers["ROOT"]
frozen = helpers["frozen"]
generate = helpers["generate"]
MEASURED_CRATE_COMMIT = "85395a80b871ee4440fc540e18f14708653f0779"


def main():
    seeds = [int(x) for x in os.environ.get("M31_SEEDS", "0,1,2").split(",")]
    with tempfile.TemporaryDirectory(prefix="m31-orbit-hash-", dir=os.environ.get("M31_REPLAY_TMPDIR")) as temporary:
        directory = Path(temporary)
        archive = subprocess.check_output(["git", "archive", MEASURED_CRATE_COMMIT,
                                           "crates/prime-field-auxiliary-ic"], cwd=ROOT)
        subprocess.run(["tar", "-xf", "-", "-C", str(directory)], input=archive, check=True)
        (directory / "src").mkdir()
        (directory / "src/main.rs").write_bytes((HERE / "main.rs").read_bytes())
        (directory / "Cargo.toml").write_text('[package]\nname="m31-full-comparison"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nprime-field-auxiliary-ic={path="crates/prime-field-auxiliary-ic"}\n')
        native_object = directory / "m31.o"
        scan_object = directory / "scan.o"
        native_library = directory / "libm31scan.a"
        shared_library = directory / "libm31scan.dylib"
        cpu_flag = "-mcpu=native" if platform.machine() in ("arm64", "aarch64") else "-march=native"
        subprocess.run(["clang++", "-std=c++17", "-O3", cpu_flag, "-c", str(HERE / "m31.cpp"), "-o", str(native_object)], check=True)
        subprocess.run(["clang++", "-std=c++17", "-O3", cpu_flag, "-c", str(HERE / "scan.cpp"), "-o", str(scan_object)], check=True)
        subprocess.run(["ar", "rcs", str(native_library), str(native_object), str(scan_object)], check=True)
        subprocess.run(["clang++", "-std=c++17", "-O3", cpu_flag, "-shared", "-fPIC", str(HERE / "m31.cpp"), str(HERE / "scan.cpp"), "-o", str(shared_library)], check=True)
        subprocess.run([sys.executable, str(HERE / "check_inverse.py"), str(shared_library)], check=True, stdout=sys.stderr)
        subprocess.run([sys.executable, str(HERE / "check_scan.py"), str(shared_library)], check=True, stdout=sys.stderr)
        binaries = {}
        for label in ("control", "orbit", "audit_orbit"):
            build_dir = directory / f"target-{label}"
            env = os.environ.copy()
            env.pop("M31_X_FILTER", None)
            env.pop("M31_X_BLOOM", None)
            env["CARGO_TARGET_DIR"] = str(build_dir)
            env["TMPDIR"] = str(directory)
            env["M31_FAST_HASH"] = "1"
            env["M31_TRUSTED_BATCH"] = "1"
            env["M31_PACKED_SIGN"] = "1"
            env["M31_PAIR_BATCH"] = "1"
            env["M31_X_BLOOM"] = "1"
            for size in (18, 19, 21, 22):
                env.pop(f"M31_BLOOM_{size}", None)
            env["M31_BLOOM_22"] = "1"
            env["M31_BLOOM_HASH_HIGH"] = "1"
            env.pop("M31_BLOOM_HASH_LOW", None)
            env.pop("M31_NATIVE_SCAN", None)
            env.pop("M31_AUDIT_NATIVE", None)
            env.pop("M31_ORBIT_INDEX", None)
            env.pop("M31_AUDIT_ORBIT", None)
            env["RUSTFLAGS"] = f"-L native={directory} -l static=m31scan"
            env["M31_NATIVE_SCAN"] = "1"
            if label in ("orbit", "audit_orbit"):
                env["M31_ORBIT_INDEX"] = "1"
            if label == "audit_orbit":
                env["M31_AUDIT_ORBIT"] = "1"
                env["M31_AUDIT_NATIVE"] = "1"
            subprocess.run(["cargo", "build", "--release", "--offline"], cwd=directory, env=env, check=True)
            binaries[label] = build_dir / "release/m31-full-comparison"
        fixtures = {basis: json.loads(frozen(f"comparison/field31/{basis}/public.json"))
                    for basis in ("auxiliary", "plain")}
        for basis, fixture in fixtures.items():
            points = generate(basis, fixture)
            if points != [tuple(p) for p in fixture["factor_base_representatives"]]:
                raise ValueError("regenerated audit basis differs from frozen fixture")
            public = directory / "audit-public.txt"
            public.write_text(f'{fixture["p"]} {fixture["n"]} {fixture["a"]} {fixture["b"]}\n{fixture["P"][0]} {fixture["P"][1]} {fixture["Q"][0]} {fixture["Q"][1]}\n500\n' + ''.join(f'{x} {y}\n' for x, y in points))
            images = {}
            for label, binary in (("control", binaries["control"]), ("orbit", binaries["audit_orbit"])):
                dump = directory / f"{basis}-{label}-index.bin"
                trace = directory / f"{basis}-{label}-trace.bin"
                audit_env = os.environ.copy()
                audit_env["M31_DUMP_INDEX"] = str(dump)
                audit_env["M31_TRACE_HITS"] = str(trace)
                result = json.loads(subprocess.check_output([str(binary), str(public), "flat", "0"], cwd=directory, text=True, env=audit_env))
                if result["scalar"] != 123456789:
                    raise ValueError("audit answer differs from frozen fixture")
                images[label] = dump.read_bytes()
                images[label + "_trace"] = trace.read_bytes()
                if len(images[label]) != 8 * result["entries"]:
                    raise ValueError("index dump length differs from entry count")
            def keys(blob):
                return [int.from_bytes(blob[i:i+4], "little") for i in range(0, len(blob), 8)]
            if keys(images["control"]) != keys(images["orbit"]):
                raise ValueError(f"exact indexed key set differs on {basis}")
            common = min(len(images["control_trace"]), len(images["orbit_trace"]))
            if images["control_trace"][:common] != images["orbit_trace"][:common]:
                raise ValueError(f"first-hit trace differs on {basis}")
            print(f"{basis} exact key set SHA-256 {hashlib.sha256(b''.join(k.to_bytes(4, 'little') for k in keys(images['control']))).hexdigest()} common traced trials {common // 4}", file=sys.stderr)
        for basis, fixture in fixtures.items():
            points = generate(basis, fixture)
            public = directory / "audit-public.txt"
            public.write_text(f'{fixture["p"]} {fixture["n"]} {fixture["a"]} {fixture["b"]}\n{fixture["P"][0]} {fixture["P"][1]} {fixture["Q"][0]} {fixture["Q"][1]}\n500\n' + ''.join(f'{x} {y}\n' for x, y in points))
            for seed in seeds:
                traces = {}
                for label in ("control", "audit_orbit"):
                    trace = directory / f"{basis}-{seed}-{label}-trace.bin"
                    audit_env = os.environ.copy()
                    audit_env["M31_TRACE_HITS"] = str(trace)
                    result = json.loads(subprocess.check_output([str(binaries[label]), str(public), "flat", str(seed)], cwd=directory, text=True, env=audit_env))
                    if result["scalar"] != 123456789 or result["native_calls"] == 0:
                        raise ValueError("full-run audit failed answer or scan invocation")
                    traces[label] = trace.read_bytes()
                common = min(map(len, traces.values()))
                if traces["control"][:common] != traces["audit_orbit"][:common]:
                    raise ValueError(f"first-hit trace differs on {basis} seed {seed}")
        if os.environ.get("M31_AUDIT_ONLY") == "1":
            return
        blocks = [(basis, seed, repeat) for basis in fixtures for seed in seeds for repeat in range(8)]
        random.Random(int(os.environ.get("M31_REPLAY_ORDER_SEED", "2026112611"))).shuffle(blocks)
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["basis", "seed", "repeat", "position", "configuration", "basis_sha256", "scalar", "trials", "relations", "entries", "setup_ns", "table_ns", "elimination_ns", "rust_total_ns", "charged_wall_ns", "charged_cpu_ns", "native_calls", "native_fallbacks", "native_candidates"])
        for basis, seed, repeat in blocks:
            fixture = fixtures[basis]
            labels = ("control", "orbit")
            shift = repeat % len(labels)
            order = labels[shift:] + labels[:shift]
            matched = {}
            for position, label in enumerate(order):
                before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
                before_self = resource.getrusage(resource.RUSAGE_SELF)
                started = perf_counter_ns()
                points = generate(basis, fixture)
                if points != [tuple(p) for p in fixture["factor_base_representatives"]]:
                    raise ValueError("regenerated basis differs from frozen fixture")
                public = directory / "public.txt"
                public.write_text(f'{fixture["p"]} {fixture["n"]} {fixture["a"]} {fixture["b"]}\n{fixture["P"][0]} {fixture["P"][1]} {fixture["Q"][0]} {fixture["Q"][1]}\n500\n' + ''.join(f'{x} {y}\n' for x, y in points))
                output = subprocess.check_output([str(binaries[label]), str(public), "flat", str(seed)], cwd=directory, text=True)
                result = json.loads(output)
                if result["scalar"] != 123456789:
                    raise ValueError("unexpected public answer")
                elapsed = perf_counter_ns() - started
                child = resource.getrusage(resource.RUSAGE_CHILDREN)
                own = resource.getrusage(resource.RUSAGE_SELF)
                cpu = round(1e9 * (child.ru_utime - before_child.ru_utime + child.ru_stime - before_child.ru_stime + own.ru_utime - before_self.ru_utime + own.ru_stime - before_self.ru_stime))
                digest = hashlib.sha256(public.read_bytes()).hexdigest()
                identity = (digest, result["scalar"], result["entries"])
                if matched and identity != next(iter(matched.values())):
                    raise ValueError(f"orbit index changed basis, answer or entry count: {basis} {seed} {repeat}")
                matched[label] = identity
                if result["native_calls"] == 0:
                    raise ValueError("native scan not called during timing")
                writer.writerow([basis, seed, repeat, position, label, digest, result["scalar"], result["trials"], result["relations"], result["entries"], result["setup_ns"], result["table_ns"], result["elimination_ns"], result["total_ns"], elapsed, cpu, result["native_calls"], result["native_fallbacks"], result["native_candidates"]])
                sys.stdout.flush()


if __name__ == "__main__":
    main()
