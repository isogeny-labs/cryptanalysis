"""Cold full M31 screen of native table build and fused scan at two basis sizes."""
import csv
import hashlib
import json
import os
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
COMMON = HERE.parent / "m31-basis-sweep"
helpers = runpy.run_path(str(COMMON / "replay.py"))
ROOT = helpers["ROOT"]
frozen = helpers["frozen"]
generate = helpers["generate"]


def main():
    seeds = (0, 1, 2)
    with tempfile.TemporaryDirectory(prefix="m31-native-table-", dir=os.environ.get("M31_REPLAY_TMPDIR")) as temporary:
        directory = Path(temporary)
        archive = subprocess.check_output(["git", "archive", "HEAD", "crates/prime-field-auxiliary-ic"], cwd=ROOT)
        subprocess.run(["tar", "-xf", "-", "-C", str(directory)], input=archive, check=True)
        (directory / "src").mkdir()
        (directory / "src/main.rs").write_bytes((HERE / "main.rs").read_bytes())
        (directory / "Cargo.toml").write_text('[package]\nname="m31-full-comparison"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nprime-field-auxiliary-ic={path="crates/prime-field-auxiliary-ic"}\n')
        native_object = directory / "m31.o"
        scan_object = directory / "scan.o"
        native_library = directory / "libm31table.a"
        shared_library = directory / "libm31table.dylib"
        subprocess.run(["clang++", "-std=c++17", "-O3", "-mcpu=native", "-c", str(HERE / "m31.cpp"), "-o", str(native_object)], check=True)
        subprocess.run(["clang++", "-std=c++17", "-O3", "-mcpu=native", "-c", str(HERE / "scan.cpp"), "-o", str(scan_object)], check=True)
        subprocess.run(["ar", "rcs", str(native_library), str(native_object), str(scan_object)], check=True)
        subprocess.run(["clang++", "-std=c++17", "-O3", "-mcpu=native", "-shared", "-fPIC", str(HERE / "m31.cpp"), str(HERE / "scan.cpp"), "-o", str(shared_library)], check=True)
        subprocess.run([sys.executable, str(HERE / "check_inverse.py"), str(shared_library)], check=True, stdout=sys.stderr)
        subprocess.run([sys.executable, str(HERE / "check_row.py"), str(shared_library)], check=True, stdout=sys.stderr)
        binaries = {}
        for label in ("control", "table", "both", "audit_both"):
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
            env.pop("M31_NATIVE_TABLE", None)
            env.pop("M31_NATIVE_SCAN", None)
            env.pop("M31_AUDIT_NATIVE", None)
            env["RUSTFLAGS"] = f"-L native={directory} -l static=m31table"
            if label in ("table", "both", "audit_both"):
                env["M31_NATIVE_TABLE"] = "1"
            if label in ("both", "audit_both"):
                env["M31_NATIVE_SCAN"] = "1"
            if label == "audit_both":
                env["M31_AUDIT_NATIVE"] = "1"
            subprocess.run(["cargo", "build", "--release", "--offline"], cwd=directory, env=env, check=True)
            binaries[label] = build_dir / "release/m31-full-comparison"
        fixtures = {basis: json.loads(frozen(f"comparison/field31/{basis}/public.json"))
                    for basis in ("auxiliary", "plain")}
        def write_public(basis, size, path):
            fixture = fixtures[basis]
            points = generate(basis, size, fixture)
            if size == 500 and points != [tuple(p) for p in fixture["factor_base_representatives"]]:
                raise ValueError("500-point basis differs from frozen fixture")
            path.write_text(f'{fixture["p"]} {fixture["n"]} {fixture["a"]} {fixture["b"]}\n{fixture["P"][0]} {fixture["P"][1]} {fixture["Q"][0]} {fixture["Q"][1]}\n{size}\n' + ''.join(f'{x} {y}\n' for x, y in points))
            return hashlib.sha256(path.read_bytes()).hexdigest()
        for basis in fixtures:
            for size in (500, 1013):
                public = directory / "audit-public.txt"
                write_public(basis, size, public)
                images = {}
                for label in ("control", "table", "both"):
                    dump = directory / f"{basis}-{size}-{label}-index.bin"
                    audit_env = os.environ.copy()
                    audit_env["M31_DUMP_INDEX"] = str(dump)
                    result = json.loads(subprocess.check_output([str(binaries[label]), str(public), "flat", "0"], cwd=directory, text=True, env=audit_env))
                    if result["scalar"] != 123456789:
                        raise ValueError("audit answer differs from frozen fixture")
                    images[label] = dump.read_bytes()
                    if len(images[label]) != 8 * result["entries"]:
                        raise ValueError("index dump length differs from entry count")
                if len(set(images.values())) != 1:
                    raise ValueError(f"exact indexed payload map differs: {basis} {size}")
                print(f"{basis} {size} exact map SHA-256 {hashlib.sha256(images['control']).hexdigest()}", file=sys.stderr)
                for seed in seeds:
                    result = json.loads(subprocess.check_output([str(binaries["audit_both"]), str(public), "flat", str(seed)], cwd=directory, text=True))
                    if result["scalar"] != 123456789 or result["native_calls"] == 0:
                        raise ValueError("native full-run scan audit failed")
        if os.environ.get("M31_AUDIT_ONLY") == "1":
            return
        blocks = [(basis, size, seed, repeat) for basis in fixtures for size in (500, 1013)
                  for seed in seeds for repeat in range(4)]
        random.Random(2026112507).shuffle(blocks)
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["basis", "size", "seed", "repeat", "position", "configuration", "basis_sha256", "scalar", "trials", "relations", "entries", "setup_ns", "table_ns", "elimination_ns", "rust_total_ns", "charged_wall_ns", "charged_cpu_ns", "native_calls", "native_fallbacks", "native_candidates"])
        for basis, size, seed, repeat in blocks:
            labels = ("control", "table", "both")
            shift = repeat % len(labels)
            order = labels[shift:] + labels[:shift]
            matched = {}
            for position, label in enumerate(order):
                before_child = resource.getrusage(resource.RUSAGE_CHILDREN)
                before_self = resource.getrusage(resource.RUSAGE_SELF)
                started = perf_counter_ns()
                public = directory / "public.txt"
                digest = write_public(basis, size, public)
                output = subprocess.check_output([str(binaries[label]), str(public), "flat", str(seed)], cwd=directory, text=True)
                result = json.loads(output)
                if result["scalar"] != 123456789:
                    raise ValueError("unexpected public answer")
                elapsed = perf_counter_ns() - started
                child = resource.getrusage(resource.RUSAGE_CHILDREN)
                own = resource.getrusage(resource.RUSAGE_SELF)
                cpu = round(1e9 * (child.ru_utime - before_child.ru_utime + child.ru_stime - before_child.ru_stime + own.ru_utime - before_self.ru_utime + own.ru_stime - before_self.ru_stime))
                identity = (digest, result["scalar"], result["trials"], result["relations"], result["entries"])
                if matched and identity != next(iter(matched.values())):
                    raise ValueError(f"native collector changed matched workload: {basis} {size} {seed} {repeat}")
                matched[label] = identity
                if label == "both" and result["native_calls"] == 0:
                    raise ValueError("native scan not called during timing")
                writer.writerow([basis, size, seed, repeat, position, label, digest, result["scalar"], result["trials"], result["relations"], result["entries"], result["setup_ns"], result["table_ns"], result["elimination_ns"], result["total_ns"], elapsed, cpu, result["native_calls"], result["native_fallbacks"], result["native_candidates"]])
                sys.stdout.flush()


if __name__ == "__main__":
    main()
