"""Eliminated S4 and retained-point S3 systems, with an infinity branch."""
from itertools import product
import sympy as S
from core import Curve, point_lift


def coord(C, P, model):
    x = P[0]
    if model in ['montgomery', 'montgomery-aa', 'weierstrass', 'weierstrass-aa', 'retained']:
        return x
    if model == 'edwards':
        return (x-1) * pow(x+1, -1, C.p) % C.p
    if model == 'invariant':
        return (x + pow(x, -1, C.p)) % C.p
    raise ValueError(model)


def image(C, P):
    if P is None or P[0] == 0:
        return None
    x, y = P
    return ((x+C.a2+pow(x, -1, C.p)) % C.p,
            y*(1-pow(x*x, -1, C.p)) % C.p)


def s3(C, x, y, z):
    p = C.p
    t = C.a2*pow(3, -1, p) % p
    a = (C.a4-C.a2**2*pow(3, -1, p)) % p
    b = (2*C.a2**3*pow(27, -1, p)-C.a2*C.a4*pow(3, -1, p)+C.a6) % p
    X, Y, Z = S.sympify(x)+t, S.sympify(y)+t, S.sympify(z)+t
    return S.Poly((X-Y)**2*Z**2-2*((X+Y)*(X*Y+a)+2*b)*Z
                  +(X*Y-a)**2-4*b*(X+Y), *sorted(
                      (X.free_symbols | Y.free_symbols | Z.free_symbols), key=str),
                  modulus=p).as_expr()


def member(variable, roots, p):
    return S.Poly(S.prod(variable-v for v in roots), variable,
                  modulus=p).as_expr()


def build(C, base, R, model):
    x1, x2, x3, w = S.symbols('x1 x2 x3 w')
    xs = [x1, x2, x3]
    roots = [coord(C, P, model) for P in base]
    if len(set(roots)) != len(base):
        raise ValueError('coordinate collision beyond sign on base')
    membership = [member(x, roots, C.p) for x in xs]
    if model == 'retained':
        equations = membership + [s3(C, x1, x2, w), s3(C, w, x3, R[0])]
        infinity = [(v, v, R[0]) for v in roots] if R[0] in roots else []
        return equations, [w, x1, x2, x3], roots, infinity
    target_C, target = C, R[0]
    if model == 'invariant':
        target_C = Curve(C.p, -2*C.a2, C.a2*C.a2-4)
        target = image(C, R)[0]
    f = S.Poly(s3(target_C, x1, x2, w), w, x1, x2, x3, modulus=C.p)
    g = S.Poly(s3(target_C, w, x3, target), w, x1, x2, x3, modulus=C.p)
    expanded = S.Poly(S.resultant(f.as_expr(), g.as_expr(), w), *xs, modulus=C.p)
    if model == 'edwards':
        degrees = [expanded.degree(x) for x in xs]
        transformed = 0
        for exps, coefficient in expanded.terms():
            term = int(coefficient)
            for x, e, degree in zip(xs, exps, degrees):
                term *= (1+x)**e*(1-x)**(degree-e)
            transformed += term
        expanded = S.Poly(transformed, *xs, modulus=C.p)
    elif model == 'invariant':
        expanded = S.Poly(expanded.as_expr().subs(
            {x: x+C.a2 for x in xs}, simultaneous=True), *xs, modulus=C.p)
    return membership+[expanded.as_expr()], xs, roots, []


def rational_solutions(basis, variables, p):
    """Lex triangular lifting by finite-field univariate gcd/factorization."""
    polynomials = [g.as_expr() for g in basis.polys]
    if any(not f.free_symbols and int(f) % p for f in polynomials):
        return []
    solutions = []

    def visit(j, assigned):
        if j < 0:
            if all(int(f.subs(assigned)) % p == 0 for f in polynomials):
                solutions.append(dict(assigned))
            return
        variable = variables[j]
        gcd = None
        for f in polynomials:
            specialized = S.expand(f.subs(assigned))
            if not specialized.free_symbols:
                if int(specialized) % p:
                    return
                continue
            if specialized.free_symbols <= {variable}:
                q = S.Poly(specialized, variable, modulus=p)
                gcd = q if gcd is None else S.gcd(gcd, q)
        if gcd is None:
            raise ValueError('unconstrained variable; finite-domain semantics unresolved')
        if gcd.degree() == 0:
            return
        for root in sorted(int(z) % p for z in S.polys.polytools.ground_roots(gcd)):
            visit(j-1, {**assigned, variable: root})

    visit(len(variables)-1, {})
    return solutions


def root_indices(C, base, model, roots):
    lookup = {coord(C, P, model): i for i, P in enumerate(base)}
    return tuple(lookup[int(v) % C.p] for v in roots)


def solve(C, base, R, model, trace=None):
    def stage(name, function):
        if trace:
            trace(name, 'start')
        value = function()
        if trace:
            trace(name, 'end')
        return value
    equations, variables, allowed, infinity = stage(
        'equation_build', lambda: build(C, base, R, model))
    basis = stage('groebner', lambda: S.groebner(
        equations, *variables, modulus=C.p, order='lex', method='f5b'))
    solutions = stage('root_extraction', lambda: rational_solutions(
        basis, variables, C.p))
    xs = S.symbols('x1 x2 x3')
    candidates = {tuple(int(solution[x]) % C.p for x in xs)
                  for solution in solutions} | set(infinity)
    accepted = set()
    rejected = 0
    if trace:
        trace('lifting_and_point_check', 'start')
    for candidate in candidates:
        rows = point_lift(C, base, root_indices(C, base, model, candidate), R)
        if not rows:
            rejected += 1
        accepted |= rows
    if trace:
        trace('lifting_and_point_check', 'end')
    return {'rows': sorted(accepted), 'candidate_coordinate_tuples': len(candidates),
            'rejected_coordinate_tuples': rejected,
            'infinity_branch_candidates': len(infinity),
            'input_variables': len(variables),
            'input_equations': len(equations),
            'input_max_degree': max(S.Poly(f, *variables).total_degree()
                                    for f in equations),
            'groebner_output_terms': sum(len(f.terms()) for f in basis.polys)}
