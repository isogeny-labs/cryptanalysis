"""Eliminate auxiliary orbit coordinates while keeping actual base membership.

Quadratic norm pairs give a degree-two correspondence in the trace abscissa.
Cubic orbits give a degree-four symmetric Semaev resolvent. Product trees and
F_p root extraction project exactly the chosen parameter set; trace filtering
then recovers the original base. The subsequent solver is trace_fibers.
This is an exact elimination experiment, not a faster reciprocal-surface solver.
"""
import time
from flint import nmod_mpoly_ctx, nmod_poly
from trace_solver import trace_fibers
from progression_blocks import product_tree
from cubic_trace_lift import lift_parameters
from norm_trace_lift import lift


def semaev3(x, y, z, A, b):
    return (x-y)**2*z*z-2*((x+y)*(x*y+A)+2*b)*z+(x*y-A)**2-4*b*(x+y)


def cubic_resolvent(E):
    """S_4 rewritten in elementary symmetric functions of its orbit triple."""
    C = nmod_mpoly_ctx.get(('x1', 'x2', 'x3', 'X', 'w'), E.p)
    x1, x2, x3, X, w = C.gens()
    f = semaev3(x1, x2, w, E.a, E.b).resultant(semaev3(x3, X, w, E.a, E.b), 'w')
    e1, e2, e3 = x1+x2+x3, x1*x2+x1*x3+x2*x3, x1*x2*x3
    terms = {}
    while not f.is_zero():
        original = f.to_dict(); mon = max(original); a, b, c, j, k = mon
        assert k == 0 and a >= b >= c
        coefficient = int(original[mon])
        key = a-b, b-c, c, j
        terms[key] = (terms.get(key, 0)+coefficient) % E.p
        f -= coefficient*e1**(a-b)*e2**(b-c)*e3**c*X**j
    assert max(key[3] for key in terms) <= 4
    return terms


class OrbitProjection:
    def __init__(self, E, family, delta=None):
        tick = time.process_time()
        self.E, self.family, self.delta = E, family, delta
        self.resolvent = cubic_resolvent(E) if family == 'cubic' else None
        self.setup_cpu_s = time.process_time()-tick

    def solve(self, records):
        tick = time.process_time(); E, p = self.E, self.E.p
        parameters = {r['parameter'] for r in records.values()}
        polynomials = []
        for h in parameters:
            if self.family == 'quadratic':
                # nu=1: G(X,h)=X^2(h^2-4)-2((A+1)h+2b)X+(A-1)^2-4bh.
                polynomials.append(nmod_poly([(E.a-1)**2-4*E.b*h,
                                               -2*((E.a+1)*h+2*E.b), h*h-4], p))
            else:
                coeff = [0]*5
                for (i, j, k, ell), value in self.resolvent.items():
                    # e1=-h,e2=d=0,e3=c=1.
                    if j == 0:
                        coeff[ell] = (coeff[ell]+value*pow(-h, i, p)) % p
                polynomials.append(nmod_poly(coeff, p))
        projection = product_tree(polynomials)[-1][0]
        degree = int(projection.degree())
        z = nmod_poly([0, 1], p)
        rational = projection.gcd(z.pow_mod(p, projection)-z)
        projected = rational.roots(); accepted = set()
        for root, _ in projected:
            X = int(root); T = E.lift(X)
            if T is None:
                continue
            if self.family == 'quadratic':
                values = {2*R[0][0] % p for R in lift(E, T, 1, self.delta)}
            else:
                values = {q['h'] for q in lift_parameters(E, T, 1, 0)['candidates']}
            if values & parameters:
                accepted.add(X)
        assert accepted == set(records), (self.family, accepted, set(records))
        projection_cpu = time.process_time()-tick
        result = trace_fibers(E, accepted)
        result.update({'orbit_projection_cpu_s': projection_cpu,
                       'orbit_projection_degree': degree,
                       'projected_fp_abscissae': len(projected),
                       'projected_accepted_trace_abscissae': len(accepted),
                       'projection_and_fibers_cpu_s': projection_cpu+result['cpu_s'],
                       'orbit_projection_setup_cpu_s': self.setup_cpu_s})
        return result
