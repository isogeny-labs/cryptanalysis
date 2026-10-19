"""Check frozen source hashes and the retained rank/audit receipt chain."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


for name in ('protocol.json', 'audit_protocol.json', 'translated_protocol.json',
             'translated_extend_protocol.json', 'translated_audit_protocol.json'):
    cfg = read(name)
    for source_name, entry in cfg['sources'].items():
        actual = hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()
        assert actual == entry['sha256'], (name, source_name)

result = read('result.json')
audit = read('audit_result.json')
first_translation = read('translated_result.json')
extended = read('translated_extended_result.json')
translation_audit = read('translated_audit_result.json')
witness = read('witness.json')
extra = read('translated_extra_witness.json')
indices = read('translated_extended_indices.json')
assert result['status'] == 'FULL_RANK' and result['rank'] == 8647
assert len(witness) == 8647 and audit['status'] == 'PASS_INDEPENDENT_LOW_PIVOT_REPLAY'
assert audit['rank'] == 8647
assert first_translation['rank_by_lift'] == [8646, 8645, 8646, 8647]
assert first_translation['status'] == 'ALL_FOUR_FULL_RANK'  # retained producer-label error
assert extended['status'] == 'ALL_FOUR_FULL_RANK'
assert extended['rank_by_lift'] == [8647] * 4
assert extended['extra_draws'] == len(extra) == 3
assert len(indices) == 4 and all(len(row) == 8647 for row in indices)
assert all(0 <= i < len(witness) + len(extra) for row in indices for i in row)
assert translation_audit['status'] == 'PASS_FOUR_TRANSLATED_LOW_PIVOT_REPLAYS'
assert translation_audit['rank_by_lift'] == [8647] * 4
assert translation_audit['distinct_pair_witnesses_reconstructed'] == 8650
print('REPLAY_PASS: source hashes, rank receipts, first-trial label correction, audits')
