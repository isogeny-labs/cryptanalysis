"""Small odd-prime genus-two Jacobian arithmetic for exact research controls."""

from math import isqrt


COEFFICIENTS = (4, 12, 14, 20, 16, 1)
IDENTITY = ((1,), ())


class PrimePolynomials:
    """Low-to-high polynomial tuples over a fixed prime field."""

    def __init__(self, prime):
        self.p = prime

    def canonical(self, coefficients):
        result = [value % self.p for value in coefficients]
        while result and not result[-1]:
            result.pop()
        return tuple(result)

    def add(self, left, right):
        result = list(left) + [0] * max(0, len(right) - len(left))
        for index, value in enumerate(right):
            result[index] += value
        return self.canonical(result)

    def neg(self, polynomial):
        return tuple((-value) % self.p for value in polynomial)

    def sub(self, left, right):
        return self.add(left, self.neg(right))

    def scale(self, polynomial, scalar):
        return self.canonical(value * scalar for value in polynomial)

    def mul(self, left, right):
        if not left or not right:
            return ()
        result = [0] * (len(left) + len(right) - 1)
        for i, a in enumerate(left):
            for j, b in enumerate(right):
                result[i + j] += a * b
        return self.canonical(result)

    def divrem(self, dividend, divisor):
        if not divisor:
            raise ZeroDivisionError("polynomial division by zero")
        if len(dividend) < len(divisor):
            return (), dividend
        inverse_lead = pow(divisor[-1], -1, self.p)
        remainder = list(dividend)
        quotient = [0] * (len(dividend) - len(divisor) + 1)
        for index in range(len(quotient) - 1, -1, -1):
            coefficient = remainder[index + len(divisor) - 1] * inverse_lead % self.p
            quotient[index] = coefficient
            if coefficient:
                for offset, value in enumerate(divisor):
                    remainder[index + offset] -= coefficient * value
        return self.canonical(quotient), self.canonical(remainder[:len(divisor) - 1])

    def exact_quotient(self, dividend, divisor):
        quotient, remainder = self.divrem(dividend, divisor)
        if remainder:
            raise ArithmeticError("expected exact polynomial division")
        return quotient

    def rem(self, dividend, divisor):
        return self.divrem(dividend, divisor)[1]

    def monic(self, polynomial):
        return self.scale(polynomial, pow(polynomial[-1], -1, self.p))

    def xgcd(self, left, right):
        s, t = (1,), ()
        next_s, next_t = (), (1,)
        while right:
            quotient, remainder = self.divrem(left, right)
            left, right = right, remainder
            s, next_s = next_s, self.sub(s, self.mul(quotient, next_s))
            t, next_t = next_t, self.sub(t, self.mul(quotient, next_t))
        if not left:
            return (), (), ()
        factor = pow(left[-1], -1, self.p)
        return tuple(self.scale(polynomial, factor) for polynomial in (left, s, t))

    def evaluate(self, polynomial, x):
        value = 0
        for coefficient in reversed(polynomial):
            value = (value * x + coefficient) % self.p
        return value


class GenusTwo:
    """Jacobian of y²=f(x), with one rational base point at infinity.

    Elements are reduced Mumford pairs (u, v) with u monic, degree at most
    two, and u dividing f-v². The public arithmetic expects canonical pairs.
    """

    identity = IDENTITY

    def __init__(self, prime, coefficients=COEFFICIENTS):
        if prime <= 2 or prime % 2 == 0 or any(
            prime % candidate == 0 for candidate in range(3, isqrt(prime) + 1, 2)
        ):
            raise ValueError("expected an odd prime")
        self.p = prime
        self.poly = PrimePolynomials(prime)
        self.coefficients = self.poly.canonical(coefficients)
        if len(self.coefficients) != 6 or self.coefficients[-1] != 1:
            raise ValueError("expected a monic quintic")
        self.derivative = self.poly.canonical(
            index * value for index, value in enumerate(self.coefficients) if index
        )
        if self.poly.xgcd(self.coefficients, self.derivative)[0] != (1,):
            raise ValueError("the quintic is not squarefree modulo p")
        # These are small-field controls. The table gives deterministic roots
        # and requires O(p) setup, separately from any target inversion.
        self.square_roots = {}
        for root in range((prime + 1) // 2):
            self.square_roots[root * root % prime] = root
        self.inverse_two = pow(2, -1, prime)

    def f(self, x):
        return self.poly.evaluate(self.coefficients, x)

    def sqrt(self, value):
        return self.square_roots.get(value % self.p)

    def square_root_choices(self, value):
        root = self.sqrt(value)
        if root is None:
            return ()
        return (root, self.p - root) if root else (0,)

    def roots(self, x):
        return self.square_root_choices(self.f(x))

    def point_divisor(self, x, y):
        x, y = x % self.p, y % self.p
        if y * y % self.p != self.f(x):
            raise ValueError("point does not lie on the curve")
        return ((-x % self.p, 1), (y,) if y else ())

    def neg(self, divisor):
        u, v = divisor
        return u, self.poly.neg(v)

    def add(self, left, right):
        if left == IDENTITY:
            return right
        if right == IDENTITY:
            return left
        u1, v1 = left
        u2, v2 = right
        poly = self.poly
        common, a, b = poly.xgcd(u1, u2)
        d, c, e = poly.xgcd(common, poly.add(v1, v2))
        u = poly.exact_quotient(poly.mul(u1, u2), poly.mul(d, d))
        v_num = poly.add(
            poly.add(poly.mul(poly.mul(poly.mul(c, a), u1), v2),
                     poly.mul(poly.mul(poly.mul(c, b), u2), v1)),
            poly.mul(e, poly.add(poly.mul(v1, v2), self.coefficients)),
        )
        v = poly.rem(poly.exact_quotient(v_num, d), u)
        while len(u) > 3:
            u = poly.monic(poly.exact_quotient(
                poly.sub(self.coefficients, poly.mul(v, v)), u
            ))
            v = poly.rem(poly.neg(v), u)
        return u, v

    def mul(self, scalar, divisor):
        if scalar < 0:
            return self.mul(-scalar, self.neg(divisor))
        result = IDENTITY
        while scalar:
            if scalar & 1:
                result = self.add(result, divisor)
            scalar >>= 1
            if scalar:
                divisor = self.add(divisor, divisor)
        return result

    def monic_key(self, serial):
        if serial == 0:
            return (1,)
        if serial <= self.p:
            return (serial - 1, 1)
        b, a = divmod(serial - self.p - 1, self.p)
        return (a, b, 1)

    def quadratic_v_choices(self, u):
        """Return all reduced v over one monic quadratic u."""
        p = self.p
        a, b, _ = u
        midpoint = -b * self.inverse_two % p
        delta = (midpoint * midpoint - a) % p
        choices = []
        if not delta:
            for y in self.roots(midpoint):
                if y:
                    slope = self.poly.evaluate(self.derivative, midpoint) * pow(2*y, -1, p) % p
                    choices.append(self.poly.canonical((y - slope*midpoint, slope)))
            return tuple(sorted(choices))

        offset = self.sqrt(delta)
        if offset is not None:
            first, second = (midpoint + offset) % p, (midpoint - offset) % p
            inverse_difference = pow(first - second, -1, p)
            for y1 in self.roots(first):
                for y2 in self.roots(second):
                    slope = (y1-y2) * inverse_difference % p
                    choices.append(self.poly.canonical((y1 - slope*first, slope)))
            return tuple(sorted(choices))

        # In the quadratic residue field, write x=midpoint+w and w²=delta.
        # A square root c+d*w is found from its norm and one F_p square root.
        remainder = self.poly.rem(self.coefficients, u)
        constant, linear = (remainder + (0, 0))[:2]
        real = (constant + linear * midpoint) % p
        imaginary = linear
        if not imaginary:
            real_roots = self.square_root_choices(real)
            choices.extend(self.poly.canonical((root,)) for root in real_roots)
            if real and not real_roots:
                for root in self.square_root_choices(real * pow(delta, -1, p)):
                    choices.append(self.poly.canonical((-root*midpoint, root)))
            return tuple(sorted(choices))

        for norm in self.square_root_choices(real*real - delta*imaginary*imaginary):
            real_root = self.sqrt((real + norm) * self.inverse_two)
            if real_root:
                w_root = imaginary * pow(2*real_root, -1, p) % p
                choices = [
                    self.poly.canonical((real_root - w_root*midpoint, w_root)),
                    self.poly.canonical((-real_root + w_root*midpoint, -w_root)),
                ]
                return tuple(sorted(choices))
        return ()

    def v_choices(self, u):
        if len(u) == 1:
            return ((),)
        if len(u) == 2:
            return tuple(self.poly.canonical((root,)) for root in self.roots(-u[0]))
        return self.quadratic_v_choices(u)

    def sample_class(self, rng):
        """Uniform by rejection over monic u and one of four root slots."""
        key_count = 1 + self.p + self.p * self.p
        attempts = 0
        while True:
            attempts += 1
            u = self.monic_key(rng.randrange(key_count))
            slot = rng.randrange(4)
            choices = self.v_choices(u)
            if slot < len(choices):
                return (u, choices[slot]), attempts
