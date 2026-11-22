"""Exact W18 code-pair census for materialized two-slot N131 indexes."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = ROOT / 'n131_projected_root_lookup_screen_20261015'
TABLE = SOURCE / 'canonical_table.bin'
SUPPORT = ROOT / 'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv'
SEED = 212
SOURCE_BITS = [bit for bit in range(18) if bit != 7]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (HERE / name).open('x') as file:
        json.dump(value, file, indent=2, sort_keys=True)
        file.write('\n')


def paths():
    return {'script': Path(__file__), 'table': TABLE, 'support': SUPPORT,
            'source_receipt': SOURCE / 'prepare_result.json',
            'n41_result': HERE / 'result.json',
            'n41_group_audit': HERE / 'group_result.json'}


def freeze():
    save('projection_protocol.json', {'status': 'FROZEN_W18_TWO_BLOCK_MATERIALIZATION_SCREEN',
         'curve_id': 'EC1N131Ckb1heb5f1998f20b', 'candidate_id': None,
         'source_sha256': {name: sha(path) for name, path in paths().items()},
         'field_encoding_bytes': 17, 'rss_envelope_bytes': 4*1024**3,
         'memory_model': 'one uncompressed 17-byte root key per ordered column-disjoint code pair; eight keys per pair as a separate conditional projection'})


def run():
    protocol = json.loads((HERE / 'projection_protocol.json').read_text())
    assert protocol['source_sha256'] == {name: sha(path) for name, path in paths().items()}
    source = json.loads((SOURCE / 'prepare_result.json').read_text())
    assert source['status'] == 'PASS_N131_CANONICAL_PROJECTED_ROOT_TABLE'
    assert source['table_sha256'] == sha(TABLE)
    columns = {int(mask): int(column) for mask, column in
               (line.split() for line in SUPPORT.read_text().splitlines())}
    raw = TABLE.read_bytes()
    assert len(raw) == (1 << 17)*68
    edges = []
    degrees = Counter()
    multiplicities = Counter()
    for code in range(1 << 17):
        if not any(raw[code*68:code*68+34]):
            continue
        mask = sum(((code >> j) & 1) << bit
                   for j, bit in enumerate(SOURCE_BITS))
        first, second = columns[mask], columns[mask ^ SEED]
        assert first != second
        edge = tuple(sorted((first, second)))
        edges.append(edge)
        degrees[first] += 1
        degrees[second] += 1
        multiplicities[edge] += 1
    count = len(edges)
    assert count == source['valid_codes'] == 33191
    unordered_total = count*(count-1)//2
    collisions_incidence = sum(deg*(deg-1)//2 for deg in degrees.values()) - \
        sum(mult*(mult-1)//2 for mult in multiplicities.values())
    collisions_vertex = sum(degrees[a]+degrees[b]-multiplicities[a,b]-1
                            for a,b in edges)//2
    assert collisions_incidence == collisions_vertex == 65
    good_unordered = unordered_total-collisions_incidence
    good_ordered = 2*good_unordered
    minimum_bytes = good_ordered*17
    assert good_ordered == 1101609160
    assert minimum_bytes > protocol['rss_envelope_bytes']
    save('projection_result.json', {'status': 'PASS_W18_MATERIALIZED_INDEX_SIZE_SCREEN',
         'candidate_id': None, 'eligible_edge_codes': count,
         'distinct_columns': len(degrees),
         'unordered_distinct_code_pairs': unordered_total,
         'unordered_column_collisions': collisions_incidence,
         'collision_count_independent': collisions_vertex,
         'ordered_column_disjoint_code_pairs': good_ordered,
         'bytes_at_one_17_byte_key_per_pair': minimum_bytes,
         'bytes_at_eight_17_byte_keys_per_pair': 8*minimum_bytes,
         'rss_envelope_bytes': protocol['rss_envelope_bytes'],
         'protocol_sha256': sha(HERE / 'projection_protocol.json')})
    print('PASS_W18_MATERIALIZED_INDEX_SIZE_SCREEN', good_ordered, minimum_bytes)


if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ('freeze', 'run')
    {'freeze': freeze, 'run': run}[sys.argv[1]]()
