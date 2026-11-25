"""Localize every saved v2 row and cross-check the producer's progress reports."""
from bisect import bisect_left
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

from archived_loops import observations, read


def main():
    print("arm,seed,row,query,lane")
    with TemporaryDirectory() as folder:
        exe = Path(folder) / "positions"
        source = Path(__file__).with_suffix(".cpp")
        subprocess.run(["c++", "-O3", "-std=c++17", source, "-o", exe], check=True)
        for arm, width in (("v2_chain", 1), ("v2_batch", 64)):
            for seed in range(3):
                data, rows = observations(arm, seed)
                header = f'{seed} {width} {data["queries"]}'
                labels = [f'{r["a"]} {r["b"]}' for r in rows]
                out = subprocess.check_output([exe], input="\n".join([header, *labels]), text=True)
                matches = [tuple(map(int, line.split(","))) for line in out.splitlines()]
                assert [i for i, _, _ in matches] == list(range(1, len(rows)+1))
                qs = [q for _, q, _ in matches]
                assert qs[-1] == data["queries"]
                log = read(f"{arm}_seed{seed}", "log").decode()
                progress = re.findall(r"^queries (\d+), relations (\d+),", log, re.M)
                assert len(progress) == qs[-1] // 1_000_000
                for q, count in progress:
                    assert bisect_left(qs, int(q)) == int(count)
                for i, q, lane in matches:
                    print(arm, seed, i, q, lane, sep=",")


if __name__ == "__main__":
    main()
