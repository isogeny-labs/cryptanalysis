"""Compare structural and exact dependence on the six fixed archived prefixes."""
import json
import subprocess

from flint import fmpz_mat, nmod_mat
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching

from audit import BASE, ROOT, core

ORDER = 2147505293
COLUMNS = 500


def first_true(length, predicate):
    # Both endpoints include the row at the indicated one-based position.
    if not predicate(length):
        return None
    low, high = 0, length
    while high - low > 1:
        mid = (low + high) // 2
        if predicate(mid):
            high = mid
        else:
            low = mid
    return high


def audit(arm, seed):
    path = f"{BASE}/{arm}/seed{seed}/relations.jsonl"
    records = subprocess.check_output(["git", "show", f"HEAD:{path}"], cwd=ROOT)
    entries = []
    supports = []
    for line in records.splitlines():
        row = [0] * COLUMNS
        codes = json.loads(line)["codes"]
        assert len(codes) == 3 and all(0 <= code < 2*COLUMNS for code in codes)
        for code in codes:
            row[code // 2] += 1 if code % 2 == 0 else -1
        entries.extend(row)
        supports.append({j for j, value in enumerate(row) if value})

    total = len(supports)
    matrix = csr_matrix([entries[i:i+COLUMNS] for i in range(0, len(entries), COLUMNS)])

    def rank(n, modulus):
        return nmod_mat(n, COLUMNS, entries[:n*COLUMNS], modulus).rank()

    def deficient(n):
        matching = maximum_bipartite_matching(matrix[:n], perm_type="column")
        return (matching < 0).any()

    return (total, first_true(total, lambda n: bool(core(supports[:n]))),
            first_true(total, lambda n: rank(n, 2) < n),
            first_true(total, deficient), rank(total-1, ORDER), rank(total, ORDER),
            fmpz_mat(total, COLUMNS, entries).rank())


if __name__ == "__main__":
    print("arm seed rows first_core first_mod2 first_unmatched prefix_rank full_rank rational_rank")
    for arm in ("auxiliary", "plain"):
        for seed in range(3):
            print(arm, seed, *audit(arm, seed))
