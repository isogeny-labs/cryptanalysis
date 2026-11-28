"""Frozen M31 high-bit versus dual high/low bitmap screen."""
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
helpers = runpy.run_path(str(HERE.parent / "m31-full-rust-comparison" / "replay.py"))
ROOT = helpers["ROOT"]
frozen = helpers["frozen"]
generate = helpers["generate"]


def main():
    with tempfile.TemporaryDirectory(prefix="m31-bitmap-size-", dir=os.environ.get("M31_REPLAY_TMPDIR")) as temporary:
        directory = Path(temporary)
        archive = subprocess.check_output(["git", "archive", "HEAD", "crates/prime-field-auxiliary-ic"], cwd=ROOT)
        subprocess.run(["tar", "-xf", "-", "-C", str(directory)], input=archive, check=True)
        shutil.copy2(Path(ROOT) / "crates/prime-field-auxiliary-ic/src/field.rs", directory / "crates/prime-field-auxiliary-ic/src/field.rs")
        (directory / "src").mkdir()
        (directory / "src/main.rs").write_bytes((HERE / "main.rs").read_bytes())
        (directory / "Cargo.toml").write_text('[package]\nname="m31-full-comparison"\nversion="0.1.0"\nedition="2021"\n[dependencies]\nprime-field-auxiliary-ic={path="crates/prime-field-auxiliary-ic"}\n')
        binaries = {}
        for label in ("high", "dual"):
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
            env.pop("M31_X_DUAL", None)
            for size in (18, 19, 21, 22):
                env.pop(f"M31_BLOOM_{size}", None)
            env["M31_BLOOM_22"] = "1"
            env.pop("M31_BLOOM_HASH_HIGH", None)
            env.pop("M31_BLOOM_HASH_LOW", None)
            env["M31_BLOOM_HASH_HIGH"] = "1"
            if label == "dual":
                env["M31_X_DUAL"] = "1"
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
            for label, binary in binaries.items():
                dump = directory / f"{basis}-{label}-index.bin"
                audit_env = os.environ.copy()
                audit_env["M31_DUMP_INDEX"] = str(dump)
                result = json.loads(subprocess.check_output([str(binary), str(public), "flat", "0"], cwd=directory, text=True, env=audit_env))
                if result["scalar"] != 123456789:
                    raise ValueError("audit answer differs from frozen fixture")
                images[label] = dump.read_bytes()
                if len(images[label]) != 8 * result["entries"]:
                    raise ValueError("index dump length differs from entry count")
            if len(set(images.values())) != 1:
                raise ValueError(f"exact indexed payload map differs on {basis}")
            print(f"{basis} exact index map SHA-256 {hashlib.sha256(images['high']).hexdigest()}", file=sys.stderr)
        if os.environ.get("M31_AUDIT_ONLY") == "1":
            return
        blocks = [(basis, seed, repeat) for basis in fixtures for seed in range(3) for repeat in range(4)]
        random.Random(112628).shuffle(blocks)
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["basis", "seed", "repeat", "position", "configuration", "basis_sha256", "scalar", "trials", "relations", "entries", "table_ns", "rust_total_ns", "charged_wall_ns", "charged_cpu_ns"])
        for basis, seed, repeat in blocks:
            fixture = fixtures[basis]
            labels = ("high", "dual")
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
                identity = (digest, result["scalar"], result["trials"], result["relations"], result["entries"])
                if matched and identity != next(iter(matched.values())):
                    raise ValueError(f"bitmap-mapping collector changed matched workload: {basis} {seed} {repeat}")
                matched[label] = identity
                writer.writerow([basis, seed, repeat, position, label, digest, result["scalar"], result["trials"], result["relations"], result["entries"], result["table_ns"], result["total_ns"], elapsed, cpu])
                sys.stdout.flush()


if __name__ == "__main__":
    main()
