"""Generate kernel-checkable observed x-coordinate fiber ledger."""
import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    result = json.loads((HERE/'holdout_result.json').read_text())
    groups = defaultdict(lambda: [0, 0])
    for shard in result['shards']:
        path = HERE/shard['file']
        assert sha256(path.read_bytes()).hexdigest() == shard['sha256']
        for row in json.loads(path.read_text()):
            multiplicity = len(row['chain_candidates'])
            assert multiplicity in (1, 2)
            groups[row['B_point'][0]][multiplicity-1] += 1
    ledger = [{'x_B': x, 'single': counts[0], 'double': counts[1]}
              for x, counts in sorted(groups.items())]
    assert sum(row['single'] for row in ledger) == 1296
    assert sum(row['double'] for row in ledger) == 72
    record = {'status': 'OBSERVED_P1231_X_FIBER_LEDGER',
              'holdout_result_sha256': sha256((HERE/'holdout_result.json').read_bytes()).hexdigest(),
              'groups': ledger}
    (HERE/'observed_groups.json').write_text(json.dumps(record, sort_keys=True, indent=2)+'\n')
    triples = ',\n    '.join(f"({row['x_B']}, {row['single']}, {row['double']})" for row in ledger)
    source = f'''import Std

namespace P1231ObservedGroups

def groups : List (Nat × Nat × Nat) := [
    {triples}]

/-- The 30 observed x-coordinate classes have double fibers exactly
at the three cube roots of one. The audit binds these compressed counts
to all 1,368 concrete (C,E,B) rows and the independent source census. -/
theorem double_iff_special :
    groups.all (fun g => decide (g.2.2 > 0 ↔ g.1^3 % 1231 = 1)) = true := by decide

theorem single_double_totals :
    groups.foldl (fun a g => (a.1 + g.2.1, a.2 + g.2.2)) (0, 0) =
      (1296, 72) := by decide

theorem group_count : groups.length = 30 := by decide

#print axioms double_iff_special
#print axioms single_double_totals
#print axioms group_count

end P1231ObservedGroups
'''
    folder = HERE/'formal'
    folder.mkdir(exist_ok=True)
    (folder/'ObservedGroups.lean').write_text(source)
    print(json.dumps({'group_count': len(ledger), 'single': 1296, 'double': 72}))


if __name__ == '__main__':
    main()
