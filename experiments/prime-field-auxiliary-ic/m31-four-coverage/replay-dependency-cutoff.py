"""Check the hypotheses of DependencyCutoff.sharp for the three pinned archives."""
import json
import runpy
import subprocess
from pathlib import Path

fixture = runpy.run_path(str(Path(__file__).with_name("replay-smooth-peeling.py")))
read = fixture["read"]
largest_factor = fixture["largest_factor"]


def rank_and_annihilation(rows, weights, columns, prime):
    # GP checks primality, computes rank over F_prime, and multiplies the
    # transposed matrix by the published certificate. All indices in GP start at 1.
    commands = [f"M=matrix({len(rows)},{columns});"]
    for i, codes in enumerate(rows, 1):
        for c in codes:
            assert type(c) is int and 0 <= c < 2 * columns
            commands.append(f"M[{i},{c//2+1}]+={1 if c%2==0 else -1};")
    assert all(type(w) is int and 0 <= w < prime for w in weights)
    commands += [f"A=Mod(1,{prime})*M;", f"w={weights};",
                 f'print([isprime({prime}),matrank(A),w*A==vector({columns})]);']
    result = subprocess.run(["gp", "-fq", "-s", "256M"], input="\n".join(commands),
                            capture_output=True, text=True, check=True)
    if result.stderr:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def main():
    public = json.loads(read("public.json"))
    costs = [largest_factor(x) for x, _ in public["factor_base_representatives"]]
    for seed in range(3):
        prefix = f"seed{seed}/"
        assert json.loads(read(prefix + "public.json")) == public
        rows = [json.loads(line)["codes"] for line in read(prefix + "relations.jsonl").splitlines()]
        cert = json.loads(read(prefix + "certificate.json"))
        w = cert["weights"]
        assert len(w) == len(rows) and any(w)
        assert all(len(row) == 3 for row in rows)
        assert rank_and_annihilation(rows, w, len(costs), public["n"]) == [1, len(w)-1, 1]
        row_cost = [min(costs[c//2] for c in row) for row in rows]
        cutoff = max(t for t, weight in zip(row_cost, w) if weight)
        witness = next(i for i, (t, weight) in enumerate(zip(row_cost, w)) if weight and t == cutoff)
        print(seed, cutoff, witness, sum(t <= cutoff for t in row_cost), len(rows))


if __name__ == "__main__":
    main()
