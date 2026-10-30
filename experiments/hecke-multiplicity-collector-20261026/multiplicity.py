"""Multiplicity-aware rational Hecke neighbor reconstruction for X_0(11)."""
import hashlib
import importlib.util
import itertools
import math
from pathlib import Path

from sage.all import matrix, vector


BASE = Path(__file__).resolve().parent.parent / "ecdlp-hecke-floor-rank-20261012" / "tools"
SOURCE = BASE / "hecke11.py"
EXPECTED = "7e66144e76bf62f7e645d87cc58be2bb0f7cc5e52601665650ef0706a6f715fb"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED
_spec = importlib.util.spec_from_file_location("_archived_hecke11", SOURCE)
assert _spec is not None and _spec.loader is not None
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)


class MultiplicityReduced(H.Reduced):
    """Preserve the old simple-root branch and recover unique repeated-root fibers."""

    MAX_ASSIGNMENTS = 65536

    def recover(self, ell, source):
        degree = ell + 1
        roots = self.neighbour_x(ell, source).roots()
        if sum(int(m) for _, m in roots) != degree:
            return "NONRATIONAL_X", None
        if all(int(m) == 1 for _, m in roots):
            points = super().neighbours_all(ell, source)
            return ("SIMPLE" if points is not None else "SIMPLE_REJECTED"), points

        moments = [self.funcs[(ell, "xy", k)](source[0], source[1])
                   for k in range(degree)]
        xs = [x for x, _ in roots]
        distinct = len(xs)
        vandermonde = matrix(self.Fp, [[x ** k for x in xs]
                                        for k in range(distinct)])
        aggregates = vandermonde.solve_right(vector(self.Fp, moments[:distinct]))
        if any(sum(aggregates[i] * xs[i] ** k for i in range(distinct)) != moments[k]
               for k in range(degree)):
            return "POWER_SUM_MISMATCH", None
        choices = []
        for (x, multiplicity), y_sum in zip(roots, aggregates):
            lifts = self.E.lift_x(x, all=True)
            if not lifts:
                return "NO_RATIONAL_POINT", None
            local = []
            count = int(multiplicity)
            if len(lifts) == 1:
                candidate = [lifts[0]] * count
                if count * lifts[0][1] == y_sum:
                    local.append(candidate)
            elif len(lifts) == 2:
                for first in range(count + 1):
                    candidate = [lifts[0]] * first + [lifts[1]] * (count - first)
                    if first * lifts[0][1] + (count - first) * lifts[1][1] == y_sum:
                        local.append(candidate)
            if not local:
                return "NO_Y_ASSIGNMENT", None
            choices.append(local)
        if math.prod(len(local) for local in choices) > self.MAX_ASSIGNMENTS:
            return "ASSIGNMENT_CAP", None
        valid = []
        for assignment in itertools.product(*choices):
            points = [P for block in assignment for P in block]
            if len(points) != degree:
                continue
            if any(sum(P[0] ** k for P in points) !=
                   self.funcs[(ell, "x", k)](source[0], source[1])
                   for k in range(1, degree + 1)):
                continue
            if any(sum(P[0] ** k * P[1] for P in points) != moments[k]
                   for k in range(degree)):
                continue
            if sum(points, self.E(0)) == self.a_l[ell] * source:
                valid.append(points)
        if len(valid) == 1:
            return "RECOVERED_REPEATED", valid[0]
        return ("AMBIGUOUS_Y_ASSIGNMENT" if valid else "GROUP_OR_MOMENT_MISMATCH"), None

    def neighbours_all(self, ell, source):
        return self.recover(ell, source)[1]
