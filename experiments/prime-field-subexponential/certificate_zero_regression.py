#!/usr/bin/env python3
"""Regression for a zero constant in a sparse certificate target row."""

from sympy import Poly, symbols

from binary_graeffe_macaulay import certificate_panel


z = symbols("z")
result = certificate_panel([Poly(z, z, modulus=101)], [0], (z,), 101, limit=1)
assert result["minimum_static_certificate_degree"] == 1
assert result["all_parameter_linear_forms_recovered"]
print("zero-parameter regression: ok")
