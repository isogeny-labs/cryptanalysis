"""Accept only complete process/file custody; do not compute research results."""
from pathlib import Path
import hashlib
import json
import sys

repo, output = (Path(value).resolve() for value in sys.argv[1:3])
ci = repo / 'experiments/chained-transfer-public-target/ci_original_relation'
expected = [line.split() for line in (ci / 'phase-plan-01.txt').read_text().splitlines()]
actual = [line.split() for line in (output / 'phases.txt').read_text().splitlines()]
assert actual == [[name, code, code] for name, code in expected]
assert len({name for name, _ in expected}) == len(expected)
for name, code in expected:
    assert (output / (name + '.pipe-exits')).read_text().split() == [code, '0']
assert (output / 'original.exit').read_text().strip() == '0'
assert (output / 'final-source-guards.exit').read_text().strip() == '0'
assert (ci / 'reference-01.sha256').read_bytes() == (output / 'original-reference.sha256').read_bytes()
assert (ci / 'phase-plan-01.txt').read_bytes() == (output / 'original-phase-plan.txt').read_bytes()
prior_path = output / 'whole-operational-custody-before-final-exits.json'
prior = json.loads(prior_path.read_text())
assert prior['completed_prefix_phase_process_exits_and_tee_exits_match_frozen_plan'] is True
assert prior['all_captured_compiled_runtime_source_and_original_prepared_file_bytes_equal'] is True
assert prior['whole_controls_actual_files_and_no_negative_outputs_checked'] is True
assert prior['remaining_caller_obligations'] == [
    'this validator process exit0 recorded in phases and pipe-exits',
    'final-published-source-guards phase0',
    'finish final-source-guards.exit0',
    'original.exit0',
    'entire ordered phase-plan equality',
]
receipt = {
    'schema': 'chained-transfer.complete-operational-custody/v1',
    'consumer': (output / 'consumer-head.txt').read_text().strip(),
    'producer': (output / 'producer-head.txt').read_text().strip(),
    'complete_ordered_process_and_tee_exits': actual,
    'original_exit': 0,
    'final_source_guard_exit': 0,
    'prior_entire_receipt_sha256': hashlib.sha256(prior_path.read_bytes()).hexdigest(),
    'prior_caller_obligations_now_observed': prior['remaining_caller_obligations'],
    'remaining_caller_obligations': [
        'this acceptor process exit0 retained by caller',
        'whole CI artifact custody and independent inspection',
    ],
    'scope': 'unsigned operational process/file custody; existing Rust and Lean gates check mathematics; no signed execution standing',
}
(output / 'completed-operational-custody.json').write_text(json.dumps(receipt, indent=2) + '\n')
print('complete ordered process/file custody accepted; caller must retain this process exit')
