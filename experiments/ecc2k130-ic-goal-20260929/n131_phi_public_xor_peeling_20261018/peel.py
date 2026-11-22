"""Peel noninterface variables from the exact public-Q native XOR system."""
from collections import deque
import hashlib
import json
import resource
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg_path = HERE / 'protocol.json'
    cfg = json.loads(cfg_path.read_text())
    for name, item in cfg['sources'].items():
        assert sha(item['path']) == item['sha256'], name
    interface = set(cfg['interface_variables'])
    source = Path(cfg['sources']['formula']['path'])
    start = time.monotonic()
    with source.open('rb') as stream:
        header = stream.readline().split()
        assert header[:2] == [b'p', b'cnf'] and len(header) == 4
        nvars = int(header[2])
        assert nvars == cfg['formula_variables']
        row_vars = []
        direct_rows = 0
        xor_count = 0
        incidence = [[] for _ in range(nvars + 1)]
        degree = [0] * (nvars + 1)
        for line in stream:
            if not line.startswith(b'x'):
                continue
            fields = line[1:].split()
            assert fields and fields[-1] == b'0'
            variables = [abs(int(lit)) for lit in fields[:-1]]
            assert variables and all(1 <= v <= nvars for v in variables)
            private = tuple(v for v in variables if v not in interface)
            # The serialized equations have no duplicate variable in a row.
            assert len(private) == len(set(private))
            row = len(row_vars)
            row_vars.append(private)
            xor_count += 1
            if not private:
                direct_rows += 1
            for variable in private:
                incidence[variable].append(row)
                degree[variable] += 1
    assert xor_count == cfg['native_xor_rows']
    active = bytearray(b'\x01') * xor_count
    queue = deque(i for i in range(1, nvars + 1) if degree[i] == 1 and i not in interface)
    pivots = 0
    checked_occurrences = 0
    while queue:
        variable = queue.popleft()
        if degree[variable] != 1:
            continue
        live = [row for row in incidence[variable] if active[row]]
        checked_occurrences += len(incidence[variable])
        assert len(live) == 1
        row = live[0]
        active[row] = 0
        pivots += 1
        for member in row_vars[row]:
            degree[member] -= 1
            assert degree[member] >= 0
            if degree[member] == 1:
                queue.append(member)
    residual = xor_count - pivots
    residual_edge_count = sum(len(row_vars[i]) for i in range(xor_count) if active[i])
    result = {
        'status': 'COMPLETE_XOR_INTERFACE_PEEL',
        'claim_boundary': ('full-row-rank certificate for noninterface XOR variables'
                           if residual == 0 else 'partial peeling only; residual linear rank unmeasured'),
        'interface_variables': sorted(interface),
        'formula_variables': nvars, 'native_xor_rows': xor_count,
        'direct_interface_rows': direct_rows,
        'peeled_rows': pivots, 'residual_rows': residual,
        'residual_noninterface_occurrences': residual_edge_count,
        'residual_degree_one_noninterface_variables': sum(
            degree[i] == 1 for i in range(1, nvars + 1) if i not in interface),
        'checked_incidence_entries': checked_occurrences,
        'wall_seconds': time.monotonic() - start,
        'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256': sha(cfg_path)}
    with (HERE / 'result.json').open('x') as output:
        json.dump(result, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'peeled_rows',
                                             'residual_rows', 'wall_seconds',
                                             'peak_rss_bytes')}, sort_keys=True))


if __name__ == '__main__':
    main()
