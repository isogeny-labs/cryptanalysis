"""Prime-field coordinate networks using the existing integer Fourier blocks.

Integer quotient/remainder equalities have enough carry bits to avoid wraparound.
Every field word and remainder is constrained to its canonical range. Python
hints supply test witnesses only; they are absent from compiled tensor networks.
"""

import math

from tensor_encoding import BinaryCurveEncoding


class PrimeCurveEncoding(BinaryCurveEncoding):
    """Short Weierstrass arithmetic, including all exceptional addition cases."""

    def __init__(self, curve):
        super().__init__(curve)
        self.canonical_words = set()

    def canonical(self, word):
        word = tuple(word)
        if word not in self.canonical_words:
            self.canonical_words.add(word)
            less = self.circuit.less_than_constant(word, self.field.size)
            self.circuit.equal((less,), self.circuit.constant(1, 1))
        return word

    def fp_add(self, left, right, subtract=False):
        c, p, b = self.circuit, self.field.size, self.field.degree
        self.canonical(left)
        self.canonical(right)
        quotient, result = c.word(1), c.word(b)
        operation = (lambda v: (int(v[0] < v[1]), (v[0] - v[1]) % p)) if subtract else (lambda v: divmod(sum(v), p))
        c.hint((left, right), (quotient, result), operation)
        self.canonical(result)
        qp = tuple(quotient[0] if p >> i & 1 else c.constant(0, 1)[0] for i in range(b))
        if subtract:
            lhs, rhs = c.add_integer(left, qp, b + 1), c.add_integer(right, result, b + 1)
        else:
            lhs, rhs = c.add_integer(left, right, b + 1), c.add_integer(qp, result, b + 1)
        c.equal(lhs, rhs)
        return result

    def fp_sub(self, left, right):
        return self.fp_add(left, right, subtract=True)

    def fp_mul(self, left, right):
        c, p, b = self.circuit, self.field.size, self.field.degree
        self.canonical(left)
        self.canonical(right)
        quotient, result = c.word(b), c.word(b)
        c.hint((left, right), (quotient, result), lambda v: divmod(v[0] * v[1], p))
        self.canonical(quotient)
        self.canonical(result)
        product = c.integer_multiply(left, right)
        qp = c.integer_multiply(quotient, c.constant(p, b))
        # 2b+1 bits suffice even for a malicious b-bit quotient plus remainder.
        lhs = product + c.constant(0, 1)
        rhs = c.add_integer(qp, result, 2 * b + 1)
        c.equal(lhs, rhs)
        return result

    def valid(self, point):
        if point in self.validated:
            return
        self.validated.add(point)
        c, b = self.circuit, self.field.degree
        zero = c.constant(0, b)
        self.canonical(point.x)
        self.canonical(point.y)
        c.equal(point.x, zero, point.infinity[0])
        c.equal(point.y, zero, point.infinity[0])
        x2, y2 = self.fp_mul(point.x, point.x), self.fp_mul(point.y, point.y)
        x3 = self.fp_mul(x2, point.x)
        ax = self.fp_mul(c.constant(self.curve.a, b), point.x)
        rhs = self.fp_add(self.fp_add(x3, ax), c.constant(self.curve.b, b))
        c.equal(y2, rhs, c.not_bit(point.infinity[0]))

    def add(self, left, right):
        c, p, b = self.circuit, self.field.size, self.field.degree
        result = self.point()
        c.hint(left.words + right.words, result.words,
               lambda v: self.values(self.curve.add(self.decoded(v[:3]), self.decoded(v[3:]))))
        for point in (left, right, result):
            self.valid(point)
        both = c.and_bit(c.not_bit(left.infinity[0]), c.not_bit(right.infinity[0]))
        dx, dy = self.fp_sub(right.x, left.x), self.fp_sub(right.y, left.y)
        equal_x, equal_y, zero_y = c.is_zero(dx), c.is_zero(dy), c.is_zero(left.y)
        generic = c.and_bit(both, c.not_bit(equal_x))
        doubling = c.and_bit(both, equal_x, equal_y, c.not_bit(zero_y))
        inverse = c.and_bit(both, equal_x, c.not_bit(c.and_bit(equal_y, c.not_bit(zero_y))))
        active = c.xor_bit(generic, doubling)
        slope = c.word(b)

        def slope_hint(v):
            P, Q = self.decoded(v[:3]), self.decoded(v[3:])
            if P is None or Q is None:
                return (0,)
            if P[0] != Q[0]:
                return ((Q[1] - P[1]) * pow((Q[0] - P[0]) % p, -1, p) % p,)
            if P == Q and P[1]:
                return ((3 * P[0] * P[0] + self.curve.a) * pow(2 * P[1] % p, -1, p) % p,)
            return (0,)

        c.hint(left.words + right.words, (slope,), slope_hint)
        self.canonical(slope)
        c.equal(slope, c.constant(0, b), c.not_bit(active))
        c.equal(self.fp_mul(slope, dx), dy, generic)
        x2 = self.fp_mul(left.x, left.x)
        twice_x2 = self.fp_add(x2, x2)
        numerator = self.fp_add(self.fp_add(twice_x2, x2), c.constant(self.curve.a, b))
        twice_y = self.fp_add(left.y, left.y)
        c.equal(self.fp_mul(slope, twice_y), numerator, doubling)
        expected_x = self.fp_sub(self.fp_sub(self.fp_mul(slope, slope), left.x), right.x)
        expected_y = self.fp_sub(self.fp_mul(slope, self.fp_sub(left.x, result.x)), left.y)
        c.equal(result.x, expected_x, active)
        c.equal(result.y, expected_y, active)
        c.equal(result.infinity, c.constant(0, 1), active)
        c.equal(result.infinity, c.constant(1, 1), inverse)
        self.equal_points(result, right, left.infinity[0])
        self.equal_points(result, left, c.and_bit(c.not_bit(left.infinity[0]), right.infinity[0]))
        return result

    def in_subgroup_image(self, point, order, cofactor):
        if cofactor < 1 or math.gcd(cofactor, order) != 1:
            raise ValueError("cofactor must be positive and coprime to subgroup order")
        self.valid(point)
        self.circuit.equal(point.infinity, self.circuit.constant(0, 1))
        if cofactor == 1:
            return
        witness = self.point()
        inverse = pow(cofactor, -1, order)
        self.circuit.hint(point.words, witness.words,
                          lambda v: self.values(self.curve.mul(inverse, self.decoded(v))))
        self.valid(witness)
        image = self.constant_point(None)
        for bit in bin(cofactor)[2:]:
            image = self.add(image, image)
            if bit == "1":
                image = self.add(image, witness)
        self.equal_points(point, image)

    def hashed_membership(self, point, prime, alpha, beta, threshold):
        c, p = self.circuit, self.field.size
        if not (prime > 2 * p and 0 < alpha < prime and 0 <= beta < prime and 0 < threshold <= prime):
            raise ValueError("invalid affine factor-base parameters")
        # In odd characteristic the selector is y mod 2, not y/x mod 2.
        encoded = (point.y[0],) + point.x
        width = prime.bit_length()
        quotient, residue = c.word(width), c.word(width)
        c.hint((encoded,), (quotient, residue), lambda v: divmod(alpha * v[0] + beta, prime))
        left = c.integer_multiply(c.constant(alpha, width), encoded)
        right = c.integer_multiply(quotient, c.constant(prime, width))
        lhs = c.add_integer(left, c.constant(beta, width), 2 * width + 1)
        rhs = c.add_integer(right, residue, 2 * width + 1)
        c.equal(lhs, rhs)
        c.equal((c.less_than_constant(residue, threshold),), c.constant(1, 1))
