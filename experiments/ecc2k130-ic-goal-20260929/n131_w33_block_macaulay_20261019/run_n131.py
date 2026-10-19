"""Two-free-left-bit W33 block certificate pilot on N131 resultant rows."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PILOT = ROOT / 'n41_w11_block_macaulay_20261019' / 'run.py'
spec = importlib.util.spec_from_file_location('block_pilot', PILOT)
block = importlib.util.module_from_spec(spec)
spec.loader.exec_module(block)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    cfg = json.loads((HERE / 'protocol.json').read_text())
    assert cfg['status'] == 'FROZEN_BEFORE_N131_W33_BLOCK_PILOT'
    for item in cfg['sources'].values():
        assert sha(item['path']) == item['sha256']
    source = json.loads(Path(cfg['sources']['coefficients']['path']).read_text())
    assert source['seed_mask'] == 898618 and source['free_code_bits'] == 32
    field = block.Field(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
    seed_mask = 898618
    bit_positions = [i for i in range(33) if i != seed_mask.bit_length() - 1]
    assert len(bit_positions) == 32 and bit_positions[:2] == [0, 1]
    block.F = field
    block.WIDTH = 2
    block.VARIABLES = 34
    block.LEFT = block.source_basis(field, seed_mask << 1, bit_positions, 0)
    block.RIGHT = block.source_basis(field, seed_mask << 1, bit_positions, 18)
    assert block.source_value(3, block.LEFT) == source['positive_source_checks'][0]['unrotated_product']
    assert block.source_value(16722, block.RIGHT) == source['rows'][0]['positive_pair_products'][1]
    start = time.monotonic()
    rows = []
    for index in cfg['target_indices']:
        begin = time.monotonic()
        terms = {(i, j): value for i, j, value in source['rows'][index]['terms']}
        assert len(terms) == 13
        anf = block.product_anf(terms, 0)
        built = time.monotonic()
        samples = []
        for left_code in cfg['sample_left_codes']:
            for right_code in cfg['sample_right_codes']:
                value = block.evaluate_anf(anf, left_code, right_code)
                direct = block.evaluate_resultant(field, terms,
                    block.source_value(left_code, block.LEFT),
                    block.source_value(right_code, block.RIGHT))
                assert value == direct
                samples.append([left_code, right_code, value == 0])
        if index == 0:
            assert [3, 16722, True] in samples
        base, equations = block.coordinate_rows(anf)
        levels = []
        for degree in (4, 5):
            level_start = time.monotonic()
            outcome = block.certificate(base, equations, degree)
            outcome['wall_seconds'] = time.monotonic() - level_start
            if index == 0:
                assert not outcome['reject']
            levels.append(outcome)
            if outcome['reject']:
                break
        rows.append({'target_index': index, 'target_name': source['rows'][index]['name'],
                     'anchor': 0, 'anf_terms': len(anf),
                     'anf_degree': max((m.bit_count() for m in anf), default=0),
                     'build_seconds': built - begin, 'samples': samples,
                     'levels': levels, 'wall_seconds': time.monotonic() - begin})
        print(json.dumps({'target_index': index, 'levels': [
            [x['degree'], x['rank'], x['reject']] for x in levels],
            'wall_seconds': rows[-1]['wall_seconds']}, sort_keys=True), flush=True)
    result = {'status': 'COMPLETE_N131_W33_BLOCK_PILOT', 'candidate_id': None,
              'curve_id': cfg['curve_id'], 'rows': rows,
              'wall_seconds': time.monotonic() - start,
              'peak_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(HERE / 'protocol.json'),
              'script_sha256': sha(__file__)}
    (HERE / 'result.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'wall_seconds': result['wall_seconds'],
                      'rows': len(rows)}, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
