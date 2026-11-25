"""Independent binary-field arithmetic for the N41 product-span census."""

N = 41
D = 6
MOD = (1 << N) | (1 << 3) | 1


def multiply(a, b):
    out = 0
    while b:
        if b & 1:
            out ^= a
        b >>= 1
        a <<= 1
        if a >> N:
            a ^= MOD
    return out


def square(a):
    return multiply(a, a)


def inverse(a):
    assert a
    u, v, x, y = a, MOD, 1, 0
    while u != 1:
        shift = u.bit_length() - v.bit_length()
        if shift < 0:
            u, v = v, u
            x, y = y, x
            shift = -shift
        u ^= v << shift
        x ^= y << shift
    while x.bit_length() > N:
        x ^= MOD << (x.bit_length() - N - 1)
    assert multiply(a, x) == 1
    return x


def halftrace(value):
    result = value
    power = value
    for _ in range((N - 1) // 2):
        power = square(square(power))
        result ^= power
    return result


def trace(value):
    h = halftrace(value)
    out = square(h) ^ h ^ value
    assert out in (0, 1)
    return out


def pair_outputs(a, b):
    seed = a ^ b
    product = multiply(a, b)
    assert product not in (0, 1)
    coefficient = 1 ^ square(product)
    rhs = multiply(multiply(coefficient, square(seed)), inverse(square(product)))
    assert trace(rhs) == 0
    h = halftrace(rhs)
    scale = multiply(product, inverse(coefficient))
    roots = [multiply(scale, h), multiply(scale, h ^ 1)]
    assert all(multiply(coefficient, square(c)) ^ multiply(product, c) ^
               square(seed) == 0 for c in roots)
    return roots
