"""Independent bitmap checks for XOR overlaps and discovered affine flats."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BITMAP = HERE.parent / 'n131_w20_code_trace_bitset_20261014/valid_bitmap.bin'
N = 1 << 19


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def span(directions):
    out = [0]
    for direction in directions:
        out += [x ^ direction for x in out]
    assert len(set(out)) == len(out)
    return out


def main():
    bitmap = BITMAP.read_bytes()
    assert len(bitmap) == N // 8
    def allowed(code):
        return bool(bitmap[code >> 3] >> (code & 7) & 1)
    valid = [code for code in range(N) if allowed(code)]
    assert len(valid) == 132045
    autocorr_protocol_path = HERE / 'autocorr_protocol.json'
    autocorr_result_path = HERE / 'autocorr_result.json'
    autocorr_protocol = json.loads(autocorr_protocol_path.read_text())
    autocorr_result = json.loads(autocorr_result_path.read_text())
    assert autocorr_result['status'] == 'PASS_W20_VALID_CODE_XOR_AUTOCORRELATION'
    assert autocorr_result['protocol_sha256'] == sha(autocorr_protocol_path)
    assert autocorr_protocol['source_sha256']['valid_bitmap.bin'] == sha(BITMAP)
    checks = []
    for row in autocorr_result['source']['top_shifts']:
        direction = row['direction']
        overlap = sum(allowed(code ^ direction) for code in valid)
        assert overlap == row['valid_overlap']
        checks.append({'direction': direction, 'overlap': overlap})
    assert len(checks) == 20
    flat_checks = []
    for suffix in ('', '_v2'):
        protocol_path = HERE / ('flat_protocol' + suffix + '.json')
        result_path = HERE / ('flat_result' + suffix + '.json')
        protocol = json.loads(protocol_path.read_text())
        result = json.loads(result_path.read_text())
        assert result['status'] == 'PASS_BOUNDED_W20_VALID_AFFINE_FLAT_SEARCH'
        assert result['protocol_sha256'] == sha(protocol_path)
        assert result['source_sha256'] == protocol['source_sha256']
        assert protocol['source_sha256']['valid_bitmap.bin'] == sha(BITMAP)
        assert result['peak_self_rss_raw'] < protocol['resource_envelope']['rss_boundary_bytes']
        panels = [result['source_panel']] + result['random_control_panels']
        assert all(sum(p['dimension_histogram'].values()) == protocol['attempts'] for p in panels)
        source = result['source_panel']
        rows = ([] if source['first_four'] is None else [source['first_four']])
        rows += source['dimension_five_flats']
        for row in rows:
            directions = row['directions']
            offsets = span(directions)
            codes = sorted(row['base'] ^ offset for offset in offsets)
            assert len(codes) == (1 << row['dimension'])
            assert codes == row['codes']
            assert all(allowed(code) for code in codes)
            if row is source['first_four']:
                observed = []
                for depth in range(5):
                    points = [row['base'] ^ value for value in span(directions[:depth])]
                    count = sum(all(allowed(point ^ translation) for point in points)
                                for translation in range(N))
                    observed.append(count)
                assert observed == row['candidate_counts']
            flat_checks.append({'version': suffix or 'v1', 'dimension': row['dimension'],
                                'attempt_index': row['attempt_index'],
                                'codes_sha256': hashlib.sha256(
                                    b''.join(code.to_bytes(4, 'little') for code in codes)).hexdigest()})
    cover_protocol_path = HERE / 'cover_protocol.json'
    cover_result_path = HERE / 'cover_result.json'
    block_path = HERE / 'cover_blocks.jsonl'
    cover_protocol = json.loads(cover_protocol_path.read_text())
    cover_result = json.loads(cover_result_path.read_text())
    assert cover_result['status'] == 'PASS_BOUNDED_VALID_AFFINE_FLAT_COVER_PILOT'
    assert cover_result['protocol_sha256'] == sha(cover_protocol_path)
    assert cover_result['source_sha256'] == cover_protocol['source_sha256']
    assert cover_protocol['source_sha256']['valid_bitmap.bin'] == sha(BITMAP)
    assert cover_result['blocks_sha256'] == sha(block_path)
    assert cover_result['peak_self_rss_raw'] < cover_protocol['resource_envelope']['rss_boundary_bytes']
    covered = set()
    dimensions = {}
    additions = {}
    attempts = 0
    pointer = 0
    checkpoints = []
    with block_path.open() as source:
        for index, line in enumerate(source):
            block = json.loads(line)
            while pointer < N and (not allowed(pointer) or pointer in covered):
                pointer += 1
            assert block['block_index'] == index
            assert block['anchor'] == pointer
            directions = block['directions']
            codes = sorted(pointer ^ offset for offset in span(directions))
            assert len(codes) == 1 << block['dimension']
            assert codes == block['codes'] and all(allowed(code) for code in codes)
            assert 1 <= block['attempts_for_anchor'] <= cover_protocol['retries_per_anchor']
            attempts += block['attempts_for_anchor']
            added = len(set(codes) - covered)
            assert added == block['added']
            covered.update(codes)
            key = str(block['dimension'])
            dimensions[key] = dimensions.get(key, 0) + 1
            additions[str(added)] = additions.get(str(added), 0) + 1
            if (index + 1) % cover_protocol['checkpoint_every'] == 0:
                checkpoints.append((index + 1, len(covered)))
    assert index + 1 == cover_result['blocks']
    assert attempts == cover_result['attempts']
    assert len(covered) == cover_result['covered_codes']
    assert dimensions == cover_result['dimension_histogram']
    assert additions == cover_result['added_per_block_histogram']
    assert checkpoints == [(x['blocks'], x['covered']) for x in cover_result['checkpoints']]
    compare_protocol_path = HERE / 'compare_protocol.json'
    compare_result_path = HERE / 'compare_result.json'
    compare_protocol = json.loads(compare_protocol_path.read_text())
    compare_result = json.loads(compare_result_path.read_text())
    assert compare_result['status'] == 'PASS_BOUNDED_MATCHED_W20_FLAT_COVER_CONTINUATION'
    assert compare_result['protocol_sha256'] == sha(compare_protocol_path)
    assert compare_result['source_sha256'] == compare_protocol['source_sha256']
    assert compare_result['start_covered_codes'] == len(covered)
    assert compare_result['peak_self_rss_raw'] < compare_protocol['resource_envelope']['rss_boundary_bytes']
    compare_checks = []
    for arm in compare_result['arms']:
        policy = arm['policy']
        path = HERE / ('compare_' + policy + '.jsonl')
        assert sha(path) == arm['blocks_sha256']
        now_covered = covered.copy()
        next_anchor = 0
        new_codes = 0
        attempts = 0
        added_histogram = {}
        with path.open() as source:
            for block_index, line in enumerate(source):
                block = json.loads(line)
                while next_anchor < N and (not allowed(next_anchor) or next_anchor in now_covered):
                    next_anchor += 1
                assert block['block_index'] == block_index
                assert block['anchor'] == next_anchor
                codes = sorted(next_anchor ^ offset for offset in span(block['directions']))
                assert codes == block['codes']
                assert len(codes) == 1 << block['dimension']
                assert all(allowed(code) for code in codes)
                assert 1 <= block['trials_used'] <= compare_protocol['trials_per_anchor']
                attempts += block['trials_used']
                added = len(set(codes) - now_covered)
                assert added == block['added']
                now_covered.update(codes)
                new_codes += added
                key = str(added)
                added_histogram[key] = added_histogram.get(key, 0) + 1
        assert block_index + 1 == arm['blocks'] == compare_protocol['blocks_per_arm']
        assert attempts == arm['attempts']
        assert new_codes == arm['new_codes']
        assert len(now_covered) == arm['covered_after']
        assert added_histogram == arm['added_per_block_histogram']
        compare_checks.append({'policy': policy, 'new_codes': new_codes,
                               'blocks_checked': arm['blocks']})
    receipt = {'status': 'PASS_INDEPENDENT_W20_AFFINE_SOURCE_REPLAY',
               'bitmap_sha256': sha(BITMAP), 'autocorr_top_shift_checks': checks,
               'flat_checks': flat_checks,
               'cover_blocks_checked': cover_result['blocks'],
               'covered_codes': len(covered),
               'compare_checks': compare_checks,
               'autocorr_result_sha256': sha(autocorr_result_path),
               'flat_result_sha256': sha(HERE / 'flat_result.json'),
               'flat_result_v2_sha256': sha(HERE / 'flat_result_v2.json'),
               'cover_result_sha256': sha(cover_result_path),
               'compare_result_sha256': sha(compare_result_path),
               'verifier_sha256': sha(Path(__file__))}
    (HERE / 'verification.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(receipt['status'], len(checks), len(flat_checks), len(covered), compare_checks)


if __name__ == '__main__':
    main()
