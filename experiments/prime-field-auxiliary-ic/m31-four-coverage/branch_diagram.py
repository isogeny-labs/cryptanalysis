"""Exact reduced ordered diagram costs for the seven Torus7 branch bits."""
import itertools
import random
import statistics
from pathlib import Path

P = 2**31 - 1
WIDTH = 7
DIR = Path(__file__).resolve().parent


def coordinates(terminal=None):
    def forward(x):
        return (x*x - 2) % P

    def iterate(x, n):
        for _ in range(n):
            x = forward(x)
        return x

    if terminal is None:
        trace = next(x for x in range(4096) if iterate(x, 30) == P-2)
        terminal = iterate(trace, WIDTH)
    roots = {terminal}
    for _ in range(WIDTH):
        children = set()
        for x in roots:
            z = pow((x+2) % P, 2**29, P)
            assert forward(z) == x
            children.update((z, -z % P))
        roots = children
    rows = []
    for x in roots:
        key, u = 0, x
        for bit in range(WIDTH):
            key |= (u > P//2) << bit
            u = forward(u)
        rhs = (x**3 + 2*x + 14) % P
        y = pow(rhs, 2**29, P)
        positive = y*y % P == rhs
        assert u == terminal and rhs and y*y % P == (rhs if positive else -rhs % P)
        rows.append((key, x, int(positive), min(y, -y % P)))
    rows.sort()
    assert [r[0] for r in rows] == list(range(128))
    return terminal, rows


def halves(table, bit, n):
    block = 1 << bit
    mask = (1 << block) - 1
    lo = hi = 0
    for start in range(0, 1 << n, 2*block):
        lo |= ((table >> start) & mask) << (start//2)
        hi |= ((table >> (start+block)) & mask) << (start//2)
    return lo, hi


def costs(table):
    # Every order with the same fixed variables has the same set of cofactors.
    residuals = {0: {table}}
    cost = {}
    for mask in range(127):
        free = [i for i in range(WIDTH) if not (mask >> i & 1)]
        for j, bit in enumerate(free):
            pairs = [halves(t, j, len(free)) for t in residuals[mask]]
            cost[mask, bit] = sum(lo != hi for lo, hi in pairs)
            dest = mask | 1 << bit
            sub = {v for pair in pairs for v in pair}
            assert dest not in residuals or residuals[dest] == sub
            residuals[dest] = sub
    return cost


def order_cost(cost, order):
    mask = total = 0
    for bit in order:
        total += cost[mask, bit]
        mask |= 1 << bit
    return total


def minimum(cost):
    best = {127: 0}
    for mask in reversed(range(127)):
        best[mask] = min(cost[mask, i] + best[mask | 1 << i]
                         for i in range(WIDTH) if not (mask >> i & 1))
    return best[0]


def diagram(table, order):
    nodes, memo = [], {}
    def visit(level, key):
        if level == WIDTH:
            return (table >> key) & 1
        bit = order[level]
        lo, hi = visit(level+1, key), visit(level+1, key | 1 << bit)
        if lo == hi:
            return lo
        triple = bit, lo, hi
        if triple not in memo:
            memo[triple] = 2 + len(nodes)
            nodes.append(triple)
        return memo[triple]
    root = visit(0, 0)
    return root, nodes


if __name__ == "__main__":
    terminal, rows = coordinates()
    table = sum(label << key for key, _, label, _ in rows)
    c = costs(table)
    scores = sorted((order_cost(c, p), p) for p in itertools.permutations(range(WIDTH)))
    assert all(len(diagram(table, p)[1]) == k for k, p in scores)
    n, order = scores[0]
    assert n == minimum(c)
    root, nodes = diagram(table, order)
    assert len(nodes) == n
    for key, _, label, _ in rows:
        idx = root
        while idx >= 2:
            bit, lo, hi = nodes[idx-2]
            idx = hi if key >> bit & 1 else lo
        assert idx == label
    rng = random.Random(20261123)
    null = [minimum(costs(sum(1 << i for i in rng.sample(range(128),71)))) for _ in range(128)]
    print("terminal, positives, mask", terminal, table.bit_count(), hex(table))
    print("min, optimal orders, median, max, natural", n, sum(k == n for k,_ in scores),
          statistics.median(k for k,_ in scores), scores[-1][0], order_cost(c,range(WIDTH)))
    print("order, root", order, root)
    print("null min, median, max, <=observed", min(null), statistics.median(null), max(null),
          sum(k <= n for k in null))
    print("nodes", nodes)
