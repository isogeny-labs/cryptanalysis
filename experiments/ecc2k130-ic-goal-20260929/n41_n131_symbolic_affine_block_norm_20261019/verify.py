"""Audit immutable block-norm receipts after copying this directory."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORIGINAL = '/private/tmp/n41_symbolic_pblock_norm_20261019/'


def mapped(path):
    if path.startswith(ORIGINAL):
        return HERE / path[len(ORIGINAL):]
    return Path(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name in ['protocol.json', 'retry_protocol.json',
             'compress_protocol.json', 'n131_transfer_protocol.json']:
    protocol = json.loads((HERE / name).read_text())
    for path, expected in protocol['sources'].items():
        actual = sha(mapped(path))
        assert actual == expected, (name, path, actual, expected)

failure = json.loads((HERE/'first_attempt_failure.json').read_text())
retry = json.loads((HERE/'retry_result.json').read_text())
compact = json.loads((HERE/'compress_result.json').read_text())
transfer = json.loads((HERE/'n131_transfer_result.json').read_text())
assert failure['status'] == 'ASSERTION_FAILURE_POSITIVE_BLOCK_SCOPE'
assert retry['status'] == 'PASS_N41_SYMBOLIC_LEFT_BLOCK_NORM'
assert compact['status'] == 'PASS_N41_COMPRESSED_AFFINE_BLOCK_NORM'
assert transfer['status'] == 'PASS_N131_SAMPLED_BLOCK_TRANSFER'
assert retry['rows'][-1]['block_code_count'] == 16
assert compact['norm_monomials'] == 1386 and compact['compact_monomials'] == 258
assert compact['retained_prefixes'] == [14]
assert [(row['target'],row['prefix'],row['gcd_degree']) for row in transfer['rows']
        if row['gcd_degree']] == [('constructed_w20_subset_positive',0,1)]
for protocol_name, result in [('protocol.json',failure),
                              ('retry_protocol.json',retry),
                              ('compress_protocol.json',compact),
                              ('n131_transfer_protocol.json',transfer)]:
    assert result['protocol_sha256'] == sha(HERE/protocol_name)
lean_log = (HERE/'lean_check.log').read_text()
assert 'error:' not in lean_log and 'sorryAx' not in lean_log
assert "'AffineNorm.normFn_translate_span' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean_log
assert 'sorry' not in (HERE/'AffineNorm.lean').read_text()
print(json.dumps({'status':'PASS_BLOCK_NORM_RECEIPT_AUDIT',
                  'n41_prefixes':len(compact['rows']),
                  'n131_rows':len(transfer['rows']),
                  'lean_translation_proof':'checked'},sort_keys=True))
