"""Synthetic instrumentation-contract controls; no curve experiment."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('instrument_toy', Path(__file__).with_name('instrument_toy.py'))
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def test_source_boundary_guards():
    for width in M.WIDTHS:
        source = M.generate(width)
        assert source.count('auto setup_end=') == 1
        assert source.count('auto solve_end=') == 1
        assert source.index('auto start=') < source.index('Curve c=trg?')
        assert 'ct135_native.cpp' in source
    with pytest.raises(ValueError): M.replace_one('duplicate duplicate', 'duplicate', 'x')


def fixture():
    return ('schema,cold-phase-width4-v1\nseed,1\ncount,1\n'
            'phase,0,source_batch4_rho,0,1,2,3,4,5,15\n'
            'row,0,source_batch4_rho,1,1,2,3,15,7,1,1,5,0,6\n')


def test_binding_and_unchanged_arithmetic_auditor_schema():
    normalized, phases = M.normalize(fixture(), 4)
    assert len(phases) == 1
    assert normalized.startswith('schema,ct136-batched-cold-v1\n')
    assert 'source_batch32_rho' in normalized
    for bad in [fixture().replace(',15,7,', ',14,7,'),
                fixture().replace(',1,2,3,4,5,15', ',1,2,3,4,6,15'),
                fixture().replace('phase,0', 'phase,1'),
                fixture().replace('phase,0,source', 'phase,0,target'),
                fixture().replace('phase,0,source_batch4_rho,0,1', 'phase,0,source_batch4_rho,0,-1')]:
        with pytest.raises(ValueError): M.normalize(bad, 4)
