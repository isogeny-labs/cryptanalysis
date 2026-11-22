#!/usr/bin/env python3
"""CT197: independent-schema offline reader for CT196 producer JSON.

Fail-closed structural and paired-pricing diagnostic, NOT an execution or PCC verifier.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path

SCHEMA = 'ct196-public48-observed-norm-counters/v1'
SOURCE_BLOB = 'b80eb91a39ae1e87f0fcde95e52ea3d3634558bc'
FIXTURE_BLOB = '9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3'
ROUTES = ('direct_composite', 'strongest_retained_lift_chain')
FIELDS = frozenset(('schema', 'parent_schema', 'standing', 'scope', 'source_git_blob',
    'fixture_git_blob', 'source_prime', 'source_group_prime',
    'admission_producer_asserted_only', 'public_packets', 'true_route_operands',
    'original_recorded_slots', 'extra_counter_control_recorded_slots',
    'observed_actual_norm_calls_total', 'same_process_setup_ns_decimal',
    'in_process_total_ns_decimal', 'peak_rss_kib_linux', 'target_arch',
    'target_os', 'raw_operands', 'complete_single_target_ecdlp_solved'))
ROW_FIELDS = frozenset(('packet_index', 'from', 'to', 'sector', 'scalar_label_outside_runtime',
    'physical_transfer_route', 'raw_slots', 'counter_control_slots',
    'observed_actual_norm_calls_original_panel',
    'observed_actual_norm_calls_counter_control_panel'))
SLOT_FIELDS = frozenset(('block', 'slot', 'arm', 'recorded', 'repetitions', 'raw_slot_ns_decimal'))

class EvidenceError(ValueError):
    pass

def require(condition, explanation):
    if not condition:
        raise EvidenceError(explanation)

def keys(value, expected, where):
    require(type(value) is dict and value.keys() == expected, f'{where}: wrong exact object fields')

def uint(value, where):
    require(type(value) is int and 0 <= value <= (1 << 64) - 1, f'{where}: not u64')
    return value

def decimal(value, where, positive=False):
    require(type(value) is str and value.isascii() and value.isdecimal()
            and len(value) <= 39 and (value == '0' or not value.startswith('0')),
            f'{where}: not canonical decimal nanoseconds')
    n = int(value)
    require(n <= (1 << 128) - 1 and (n > 0 if positive else True),
            f'{where}: out of bounds or zero')
    return n

def object_no_duplicates(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise EvidenceError('duplicate JSON key: ' + k)
        d[k] = v
    return d

def load_strict(data: bytes):
    require(len(data) <= 12_000_000, 'oversized raw diagnostic')
    try:
        return json.loads(data, object_pairs_hook=object_no_duplicates,
                          parse_constant=lambda v: (_ for _ in ()).throw(EvidenceError('nonfinite JSON')))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as e:
        raise EvidenceError('invalid JSON: ' + str(e)) from e

def expected_order(panel: str, block: int):
    if panel == 'original':
        return ('N2_actual', 'D_padd', 'D_padd', 'N2_actual') if block % 2 == 0 else (
            'D_padd', 'N2_actual', 'N2_actual', 'D_padd')
    return ('N2_actual', 'N2_arith_no_counter', 'N2_arith_no_counter', 'N2_actual') if block % 2 == 0 else (
        'N2_arith_no_counter', 'N2_actual', 'N2_actual', 'N2_arith_no_counter')

def check_panel(slots, panel, row_index):
    require(type(slots) is list and len(slots) == 64, f'operand {row_index}: {panel} requires 64 slots')
    paired = []
    cumulative_ns = 0
    for block in range(16):
        order = expected_order(panel, block)
        values = []
        for i in range(4):
            item = slots[4 * block + i]
            keys(item, SLOT_FIELDS, f'operand {row_index} {panel} block {block} slot {i}')
            require(type(item['block']) is int and item['block'] == block and
                    type(item['slot']) is int and item['slot'] == i and
                    type(item['arm']) is str and item['arm'] == order[i] and
                    type(item['recorded']) is bool and item['recorded'] == (block >= 4) and
                    type(item['repetitions']) is int and item['repetitions'] == 64,
                    f'operand {row_index}: {panel} wrong treatment/order/warmup/repetition')
            ns = decimal(item['raw_slot_ns_decimal'], 'slot ns', positive=True)
            cumulative_ns += ns
            values.append(ns)
        if block >= 4:
            a = (values[order.index('N2_actual')] + values[3-order.index('N2_actual')]) / 2
            b = (sum(values) - 2*a) / 2
            require(a > 0 and b > 0, 'unusable timing')
            paired.append(math.log(a) - math.log(b))
    require(len(paired) == 12, 'exactly 12 recorded blocks required')
    return cumulative_ns, math.exp(statistics.mean(paired))

def adjudicate(doc: dict, fixture_rows: list):
    """Returns scoped producer-only diagnostics; fixture_rows MUST be externally pin-checked."""
    keys(doc, FIELDS, 'root')
    require(doc['schema'] == SCHEMA and doc['parent_schema'] == 'ct192-public48-actual-norm-price/v1'
            and doc['standing'] == '[pcc:unverified]' and type(doc['scope']) is str
            and 'no complete ECDLP' in doc['scope'], 'schema/standing/scope mismatch')
    require(doc['source_git_blob'] == SOURCE_BLOB and doc['fixture_git_blob'] == FIXTURE_BLOB,
            'immutable source/fixture blob mismatch')
    require(type(doc['admission_producer_asserted_only']) is bool and
            doc['admission_producer_asserted_only'] is True and
            type(doc['complete_single_target_ecdlp_solved']) is bool and
            doc['complete_single_target_ecdlp_solved'] is False,
            'producer admission or complete solve misrepresented')
    for field, n in (('source_prime', 223), ('public_packets', 48), ('true_route_operands', 96),
                     ('original_recorded_slots', 4608), ('extra_counter_control_recorded_slots', 4608),
                     ('observed_actual_norm_calls_total', 393216)):
        require(type(doc[field]) is int and doc[field] == n, f'{field}: inconsistent header')
    uint(doc['source_group_prime'], 'source_group_prime')
    require(doc['source_group_prime'] > 2, 'invalid source subgroup')
    require(type(doc['target_arch']) is str and 1 <= len(doc['target_arch']) <= 50 and
            type(doc['target_os']) is str and 1 <= len(doc['target_os']) <= 50,
            'missing host platform')
    rss = doc['peak_rss_kib_linux']
    if rss is not None: uint(rss, 'peak RSS')
    setup = decimal(doc['same_process_setup_ns_decimal'], 'setup ns', positive=True)
    total = decimal(doc['in_process_total_ns_decimal'], 'in-process elapsed', positive=True)
    require(setup <= total, 'setup exceeds total elapsed')
    require(type(fixture_rows) is list and len(fixture_rows) == 48, 'frozen 48-row input missing')
    require(type(doc['raw_operands']) is list and len(doc['raw_operands']) == 96,
            'native output missing 96 true operands')
    by_group = {}
    slot_total = 0
    for i, row in enumerate(fixture_rows):
        require(type(row) is dict, 'invalid pinned fixture row')
        for j, route in enumerate(ROUTES):
            k = 2*i + j
            operand = doc['raw_operands'][k]
            keys(operand, ROW_FIELDS, f'operand {k}')
            for field, target in (('packet_index', i), ('from', row['from']), ('to', row['to']),
                                  ('sector', row['sector']),
                                  ('scalar_label_outside_runtime', row['scalar_OUTSIDE_runtime'])):
                require(type(operand[field]) is int and operand[field] == target,
                        f'operand {k}: wrong pinned cohort field {field}')
            require(operand['physical_transfer_route'] == route,
                    f'operand {k}: wrong or duplicated physical route')
            for panel, name in (('original', 'raw_slots'), ('control', 'counter_control_slots')):
                cost, ratio = check_panel(operand[name], panel, k)
                slot_total += cost
                ident = row['scalar_OUTSIDE_runtime'] == 0
                label = (row['from'], row['to'], row['sector'], route, ident, panel)
                by_group.setdefault(label, []).append(ratio)
            for field in ('observed_actual_norm_calls_original_panel',
                          'observed_actual_norm_calls_counter_control_panel'):
                require(type(operand[field]) is int and operand[field] == 2048,
                        f'operand {k}: wrong norm counter panel delta')
    require(slot_total <= total, 'sum of nested slot durations exceeds total process time')
    require(len(by_group) == 64, 'missing direction/sector/route/identity/panel strata')
    report = []
    for (frm, to, sector, route, exceptional, panel), ratios in sorted(by_group.items()):
        require(len(ratios) == (1 if exceptional else 5),
                'stratum has missing or duplicated packet')
        report.append({'direction': [frm, to], 'sector': sector, 'route': route,
                       'exceptional': exceptional, 'panel': panel,
                       'packets': len(ratios), 'packet_ratio_median': statistics.median(ratios)})
    return {'schema': 'ct197-unverified-native-diagnostic-reader/v1',
            'standing': '[pcc:unverified]',
            'scientific_scope': 'within-block, within-packet primitive timing diagnostics ONLY',
            'native_execution_authenticated': False, 'independent_pcc': False,
            'complete_single_target_ecdlp_solved': False,
            'raw_operands': 96, 'recorded_slots_per_panel': 4608,
            'observed_actual_norm_calls': 393216,
            'peak_rss_kib_linux_producer_asserted': rss,
            'nested_slot_time_ns': slot_total, 'in_process_ns_producer_asserted': total,
            'strata': report}

def run_cli():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True, type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    # Imported only from the very same guarded CT192 study directory.
    from source_contract import FROZEN, validate_fixture, blob
    fixture_bytes = FROZEN.read_bytes()
    validate_fixture(fixture_bytes)
    require(blob(fixture_bytes) == FIXTURE_BLOB, 'fixture digest mismatch')
    fixture_rows = load_strict(fixture_bytes)['all48']
    input_bytes = args.input.read_bytes()
    report = adjudicate(load_strict(input_bytes), fixture_rows)
    report['input_sha256_producer_only'] = hashlib.sha256(input_bytes).hexdigest()
    result = json.dumps(report, sort_keys=True, indent=2) + '\n'
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end='')

if __name__ == '__main__':
    try:
        run_cli()
    except (EvidenceError, OSError, KeyError, TypeError) as error:
        raise SystemExit('CT197 REFUSED: ' + str(error)) from error
