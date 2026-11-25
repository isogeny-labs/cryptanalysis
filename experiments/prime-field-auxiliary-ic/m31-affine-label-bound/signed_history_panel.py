"""Build, time and byte-check the full M31 census in balanced process pairs."""
import csv
from pathlib import Path
import random
import resource
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent


def cpu():
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return usage.ru_utime + usage.ru_stime


def main():
    expected = (HERE / "smooth_history.csv").read_bytes()
    with tempfile.TemporaryDirectory() as temp:
        obj = Path(temp) / "product.o"
        subprocess.run(["clang", "-O3", "-mcpu=native", "-c", "../m31-native-product/product.c",
                        "-o", obj], cwd=HERE, check=True)
        for name, flags in [("canonical", []), ("signed", ["-DSIGNED_BATCH_HISTORY"])]:
            subprocess.run(["clang++", "-O3", "-mcpu=native", "-std=c++17", "-DBATCH_HISTORY",
                            *flags, "smooth_history.cpp", obj, "-o", Path(temp)/name],
                           cwd=HERE, check=True)

        orders = [("canonical", "signed"), ("signed", "canonical")] * 10
        random.Random(1953).shuffle(orders)
        writer = csv.writer(sys.stdout, lineterminator="\n")
        writer.writerow(["pair", "position", "build", "wall_s", "cpu_s"])
        for pair, order in enumerate(orders):
            for position, name in enumerate(order):
                start_cpu = cpu()
                start = time.perf_counter_ns()
                result = subprocess.check_output([Path(temp)/name])
                if result != expected:
                    raise ValueError(f"{name} produced a different histogram in pair {pair}")
                wall = (time.perf_counter_ns() - start) / 1e9
                writer.writerow([pair, position, name, f"{wall:.9f}", f"{cpu()-start_cpu:.9f}"])


if __name__ == "__main__":
    main()
