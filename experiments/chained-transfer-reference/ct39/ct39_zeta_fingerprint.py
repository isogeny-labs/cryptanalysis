#!/usr/bin/env python3
"""CT39: independent two-field zeta fingerprint for fixed F_101 sextics.
No imports from producer's Jacobian/isogeny arithmetic. [pcc:unverified]
"""
P = 101
D = 2  # nonsquare in F_101; u^2=2 defines F_(101^2)
CURVES = {
    'T0': (31, 75, 74, 54, 71, 55, 1),
    'T1': (95, 26, 19, 27, 94, 91, 1),
    'T2': (95, 93, 43, 39, 92, 17, 1),
}
NEGATIVE = (31, 79, 74, 54, 71, 55, 1)


def require(test, why):
    if not test:
        raise RuntimeError(why)


def mul2(x, y):
    return ((x[0]*y[0] + D*x[1]*y[1]) % P,
            (x[0]*y[1] + x[1]*y[0]) % P)


def pow2(a, n):
    out = (1, 0)
    while n:
        if n & 1:
            out = mul2(out, a)
        a = mul2(a, a)
        n //= 2
    return out


def e1(f, x):
    out = 0
    for c in reversed(f):
        out = (out * x + c) % P
    return out


def e2(f, x):
    out = (0, 0)
    for c in reversed(f):
        out = mul2(out, x)
        out = ((out[0] + c) % P, out[1])
    return out


def character(x, square_set):
    return 0 if x == 0 else (1 if x in square_set else -1)


def counts(f, squares):
    # Leading coefficient is exactly 1: two rational infinities over both fields.
    n1 = P + 2 + sum(character(e1(f, x), squares) for x in range(P))
    n2 = P*P + 2
    for a in range(P):
        for b in range(P):
            v = e2(f, (a, b))
            norm = (v[0]*v[0] - D*v[1]*v[1]) % P
            n2 += character(norm, squares)  # chi_Fp2(v)=chi_Fp(Norm(v))
    return n1, n2


def weil(n1, n2):
    a1 = n1 - (P + 1)
    s2 = P*P + 1 - n2
    require((a1*a1 - s2) % 2 == 0, 'nonintegral Weil a2')
    a2 = (a1*a1 - s2)//2
    return (1, a1, a2, P*a1, P*P)


def smooth(f):
    def clean(a):
        while a and a[-1] % P == 0:
            a.pop()
        return a
    def rem(a, b):
        a = clean(list(a))
        b = clean(list(b))
        while len(a) >= len(b) and a:
            i = len(a) - len(b)
            c = a[-1] * pow(b[-1], -1, P) % P
            for j in range(len(b)):
                a[i+j] = (a[i+j] - c*b[j]) % P
            clean(a)
        return a
    a, b = clean(list(f)), clean([i*f[i] % P for i in range(1, len(f))])
    while b:
        a, b = b, rem(a, b)
    return len(a) == 1


def main():
    squares = {(a*a) % P for a in range(P)}
    require(D not in squares, 'extension polynomial reducible')
    # Independent Euler check (rather than norm) on every distinct field value.
    for a in range(P):
        for b in range(P):
            x = (a, b)
            chi = character((a*a-D*b*b)%P, squares)
            direct = pow2(x, (P*P-1)//2)
            require(direct == ((chi % P), 0), 'norm character disagrees with Euler')
    for name, f in CURVES.items():
        require(smooth(f), name + ' singular sextic')
        n1, n2 = counts(f, squares)
        coeffs = weil(n1, n2)
        jac = sum(coeffs)
        require((n1, n2) == (120, 10436), name + ' point counts')
        require(coeffs == (1, 18, 279, 1818, 10201), name + ' spectrum')
        require(jac == 12317, name + ' Jacobian order')
        print(f'{name}: C(F101)={n1} C(F101^2)={n2} Weil={coeffs} Jac(F101)={jac}')
    require(smooth(NEGATIVE), 'singular mutant')
    n1, n2 = counts(NEGATIVE, squares)
    coeffs = weil(n1, n2)
    require(n1 == 120 and n2 == 10314 and coeffs != (1,18,279,1818,10201), 'negative control')
    print(f'MUTANT: C(F101)={n1} C(F101^2)={n2} Weil={coeffs} Jac(F101)={sum(coeffs)} (same first point count; different spectrum)')
    # Factor match is a *necessary* geometric condition for maps E109/E113 -> Jac(Ti).
    base = (1,7,101)
    other = (1,11,101)
    actual = tuple(sum(base[j]*other[i-j] for j in range(3) if 0 <= i-j < 3) for i in range(5))
    # Polynomials are stored high-to-low, so reversal matches the palindromic q-Weil form.
    require(actual == (1,18,279,1818,10201), 'elliptic factor mismatch')
    print('E109*E113 Frobenius characteristic polynomial: match')


if __name__ == '__main__':
    main()
