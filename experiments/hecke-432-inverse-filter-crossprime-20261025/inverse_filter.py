"""Exact rational C,E-to-B branch filter over a prime field.

The return status preserves exceptional rational resolvent pairs. A valid B
point is not itself a unique level-432 source identifier: source fibers may
contain multiple kernel chains.
"""
from collections import defaultdict


def curve_points(p, kind):
    squares = defaultdict(list)
    for y in range(p):
        squares[y*y % p].append(y)
    out = []
    for x in range(p):
        rhs = (4*(x*x*x-7)+1 if kind == 'C' else x*x*x+432) % p
        for value in squares[rhs]:
            y = (value-1)*pow(2, -1, p) % p if kind == 'C' else value
            out.append((x, y))
    return sorted(out)


def resolvent_coefficients(terms, c, p):
    xc, yc = c
    coeffs = [0]*13
    for term in terms:
        exponent = term['x_E_exponent']
        coeffs[exponent] = (coeffs[exponent] + int(term['integer_coefficient'])
                            * pow(xc, term['x_C_exponent'], p)
                            * pow(yc, term['y_C_exponent'], p)) % p
    return coeffs


def horner(coeffs, x, p):
    value = 0
    for coefficient in reversed(coeffs):
        value = (value*x+coefficient) % p
    return value


def branch_value(terms, c, xe, p):
    xc, yc = c
    return sum(int(term['integer_coefficient'])
               * pow(xc, term['x_C_exponent'], p)
               * pow(yc, term['y_C_exponent'], p)
               * pow(xe, term['x_E_exponent'], p)
               for term in terms) % p


def evaluate_pair(c, e, p, resolvent, branch):
    """Return a status and, only for VALID, the unique rational branch B."""
    xc, yc = c
    xe, ye = e
    if (yc*yc+yc-xc**3+7) % p or (ye*ye-xe**3-432) % p:
        return {'status': 'POINT_OFF_CURVE'}
    if horner(resolvent_coefficients(resolvent['terms'], c, p), xe, p):
        return {'status': 'NOT_RESOLVENT_ROOT'}
    numerator = branch_value(branch['numerator_terms'], c, xe, p)
    denominator = branch_value(branch['denominator_terms'], c, xe, p)
    if denominator == 0:
        return {'status': 'ZERO_DENOMINATOR', 'numerator': numerator}
    xb = numerator*pow(denominator, -1, p) % p
    yden = (xb**3+128) % p
    if xb == 0 or yden == 0:
        return {'status': 'Y_INVERSE_UNDEFINED', 'x_B': xb}
    yb = ye*pow(xb, 3, p)*pow(yden, -1, p) % p
    if (yb*yb-xb**3+16) % p or (xb**3-xe*xb*xb-64) % p:
        return {'status': 'BRANCH_EQUATION_FAILURE', 'B_point': [xb, yb]}
    return {'status': 'VALID', 'B_point': [xb, yb]}
