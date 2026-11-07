"""Implicit arithmetic graphs for coordinate-based hashed relation search.

Integer multiplication uses the paper's two-stage Fourier construction over
Z/(2^J+1). Binary-polynomial multiplication uses odd-length Fourier transforms
over F2[U]/(U^(2J)+U^J+1), with J a power of three. The latter is an adaptation
for binary curves; it is tested independently, not asserted as a formal proof
of the paper's prime-field theorem for every binary field.
"""

from dataclasses import dataclass
import math

from ecc2k import BinaryField, BinaryCurve
from tensor_network import ConstraintBuilder


def bits_value(bits):
    return sum(bit << i for i, bit in enumerate(bits))


def field_power(field, value, exponent):
    result = 1
    while exponent:
        if exponent & 1:
            result = field.mul(result, value)
        value = field.square(value)
        exponent >>= 1
    return result


class WordCircuit:
    def __init__(self):
        self.builder = ConstraintBuilder()
        self.steps = []
        self.constants = {}
        self.mul_metadata = []

    def word(self, width):
        return self.builder.word(width)

    def constant(self, value, width):
        word = []
        for i in range(width):
            bit = value >> i & 1
            if bit not in self.constants:
                variable = self.builder.bit()
                self.builder.pin(variable, bit)
                self.constants[bit] = variable
            word.append(self.constants[bit])
        return tuple(word)

    def compute(self, inputs, widths, function, name):
        inputs, widths = tuple(map(tuple, inputs)), tuple(widths)
        outputs = tuple(self.word(width) for width in widths)
        sizes = tuple(map(len, inputs)) + widths
        offsets, current = [], 0
        for size in sizes:
            offsets.append(current)
            current += size

        def predicate(bits):
            values = [bits_value(bits[start:start + size]) for start, size in zip(offsets, sizes)]
            expected = tuple(function(tuple(values[:len(inputs)])))
            return tuple(values[len(inputs):]) == expected

        self.builder.constraint(tuple(v for word in inputs + outputs for v in word), predicate, name)
        self.steps.append((inputs, outputs, function))
        return outputs

    def hint(self, inputs, outputs, function):
        # Hints are only a way to construct a complete test witness. The network
        # contains no hint oracle; its arithmetic constraints enforce the values.
        self.steps.append((tuple(map(tuple, inputs)), tuple(map(tuple, outputs)), function))

    def xor_bit(self, *variables):
        if not variables:
            return self.constant(0, 1)[0]
        result = variables[0]
        for variable in variables[1:]:
            if variable == result:
                result = self.constant(0, 1)[0]
            else:
                result = self.compute(((result,), (variable,)), (1,), lambda v: (v[0] ^ v[1],), "xor")[0][0]
        return result

    def xor(self, *words):
        if not words or len({len(w) for w in words}) != 1:
            raise ValueError("word XOR requires equal widths")
        return tuple(self.xor_bit(*values) for values in zip(*words))

    def and_bit(self, *variables):
        if not variables:
            return self.constant(1, 1)[0]
        result = variables[0]
        for variable in variables[1:]:
            result = self.compute(((result,), (variable,)), (1,), lambda v: (v[0] & v[1],), "and")[0][0]
        return result

    def not_bit(self, variable):
        return self.xor_bit(variable, self.constant(1, 1)[0])

    def equal(self, left, right, selector=None):
        if len(left) != len(right):
            raise ValueError("equality width mismatch")
        for a, b in zip(left, right):
            if a == b:
                continue
            if selector is None:
                self.builder.constraint((a, b), lambda v: v[0] == v[1], "equal")
            else:
                self.builder.constraint((selector, a, b), lambda v: not v[0] or v[1] == v[2], "gated_equal")

    def is_zero(self, word):
        result = self.constant(1, 1)[0]
        for bit in word:
            result = self.and_bit(result, self.not_bit(bit))
        return result

    def add_integer(self, left, right, width):
        left = tuple(left) + self.constant(0, max(0, width - len(left)))
        right = tuple(right) + self.constant(0, max(0, width - len(right)))
        carry = self.constant(0, 1)
        result = []
        for a, b in zip(left[:width], right[:width]):
            output, carry = self.compute(((a,), (b,), carry), (1, 1),
                                         lambda v: ((sum(v) & 1), sum(v) >> 1), "full_adder")
            result.append(output[0])
        self.equal(carry, self.constant(0, 1))
        return tuple(result)

    def less_than_constant(self, word, constant):
        if not 0 <= constant <= 1 << len(word):
            raise ValueError("comparison constant out of range")
        if constant == 1 << len(word):
            return self.constant(1, 1)[0]
        equal, less = self.constant(1, 1)[0], self.constant(0, 1)[0]
        for i in range(len(word) - 1, -1, -1):
            bit = word[i]
            fixed = constant >> i & 1
            output = self.compute(((equal,), (less,), (bit,)), (1, 1),
                                  lambda v, fixed=fixed: (v[0] & (v[2] == fixed),
                                                          v[1] | (v[0] & fixed & (1 - v[2]))), "compare")
            equal, less = output[0][0], output[1][0]
        return less

    def transform(self, words, L1, L2, word_width, powers, add, multiply, scale=1, name="fft"):
        L = L1 * L2
        columns = []
        for j2 in range(L2):
            inputs = tuple(words[L2 * j1 + j2] for j1 in range(L1))

            def stage1(values, j2=j2):
                result = []
                for t1 in range(L1):
                    value = 0
                    for j1, item in enumerate(values):
                        value = add(value, multiply(item, powers[(L2 * j1 * t1) % L]))
                    result.append(multiply(powers[j2 * t1 % L], value))
                return tuple(result)

            columns.append(self.compute(inputs, (word_width,) * L1, stage1, name + "_columns"))
        outputs = [None] * L
        for t1 in range(L1):
            inputs = tuple(columns[j2][t1] for j2 in range(L2))

            def stage2(values):
                result = []
                for t2 in range(L2):
                    value = 0
                    for j2, item in enumerate(values):
                        value = add(value, multiply(item, powers[(L1 * j2 * t2) % L]))
                    result.append(multiply(value, scale))
                return tuple(result)

            transformed = self.compute(inputs, (word_width,) * L2, stage2, name + "_rows")
            for t2, word in enumerate(transformed):
                outputs[t1 + L1 * t2] = word
        return outputs

    def integer_multiply(self, left, right):
        d = max(len(left), len(right))
        left = tuple(left) + self.constant(0, d - len(left))
        right = tuple(right) + self.constant(0, d - len(right))
        J = 16
        while J * J < 64 * (d + 1):
            J *= 2
        k, n = J // 4, (d + J // 4 - 1) // (J // 4)
        L = 1
        while L < 2 * n:
            L *= 2
        if L > J // 2:
            raise ArithmeticError("integer FFT parameter inequality failed")
        exponent = L.bit_length() - 1
        L1, L2 = 1 << (exponent // 2), 1 << ((exponent + 1) // 2)
        modulus, root = (1 << J) + 1, 1 << (2 * J // L)
        add = lambda a, b: (a + b) % modulus
        multiply = lambda a, b: a * b % modulus
        powers = [pow(root, i, modulus) for i in range(L)]
        inverse_powers = [powers[-i % L] for i in range(L)]

        def chunks(word):
            padded = word + self.constant(0, n * k - d)
            return [padded[i * k:(i + 1) * k] for i in range(n)] + [self.constant(0, k)] * (L - n)

        transformed = [self.transform(chunks(word), L1, L2, J + 1, powers, add, multiply, name="integer_fft")
                       for word in (left, right)]
        products = [self.compute((a, b), (J + 1,), lambda v: (multiply(*v),), "integer_ring_product")[0]
                    for a, b in zip(*transformed)]
        coefficients = self.transform(products, L1, L2, J + 1, inverse_powers, add, multiply,
                                      pow(L, -1, modulus), "integer_ifft")
        for word in coefficients[2 * n - 1:]:
            self.equal(word, self.constant(0, len(word)))
        coefficients = coefficients[:2 * n - 1] + [self.constant(0, J + 1)]
        carry, result = self.constant(0, J + 1), []
        for coefficient in coefficients:
            low, carry = self.compute((coefficient, carry), (k, J + 1),
                                      lambda v: ((v[0] + v[1]) % (1 << k), (v[0] + v[1]) >> k), "carry")
            result.extend(low)
        self.equal(carry, self.constant(0, len(carry)))
        self.equal(tuple(result[2 * d:]), self.constant(0, len(result) - 2 * d))
        self.mul_metadata.append({"type": "integer", "input_bits": d, "ring_bits": J + 1,
                                  "transform_length": L, "stages": [L1, L2]})
        return tuple(result[:2 * d])

    def polynomial_multiply(self, left, right):
        d = max(len(left), len(right))
        left = tuple(left) + self.constant(0, d - len(left))
        right = tuple(right) + self.constant(0, d - len(right))
        J = 3
        while True:
            k = max(1, J // 4)
            n, L = (d + k - 1) // k, 1
            while L < 2 * n - 1:
                L *= 3
            if L <= 3 * J:
                break
            J *= 3
        exponent, temp = 0, L
        while temp > 1:
            exponent += 1
            temp //= 3
        L1, L2 = 3 ** (exponent // 2), 3 ** ((exponent + 1) // 2)
        field = BinaryField(2 * J, (1 << (2 * J)) | (1 << J) | 1)
        root = field.reduce(1 << (3 * J // L))
        powers = [field_power(field, root, i) for i in range(L)]
        if field_power(field, root, L) != 1 or (L > 1 and field_power(field, root, L // 3) == 1):
            raise ArithmeticError("binary Fourier root has incorrect order")
        add, multiply = lambda a, b: a ^ b, field.mul

        def chunks(word):
            padded = word + self.constant(0, n * k - d)
            return [padded[i * k:(i + 1) * k] for i in range(n)] + [self.constant(0, k)] * (L - n)

        transformed = [self.transform(chunks(word), L1, L2, 2 * J, powers, add, multiply, name="binary_fft")
                       for word in (left, right)]
        products = [self.compute((a, b), (2 * J,), lambda v: (multiply(*v),), "binary_ring_product")[0]
                    for a, b in zip(*transformed)]
        coefficients = self.transform(products, L1, L2, 2 * J, [powers[-i % L] for i in range(L)],
                                      add, multiply, name="binary_ifft")
        result = []
        for bit in range(2 * d - 1):
            terms = [coefficients[j][bit - j * k] for j in range(2 * n - 1) if 0 <= bit - j * k < 2 * k - 1]
            result.append(self.xor_bit(*terms))
        self.mul_metadata.append({"type": "binary_polynomial", "input_bits": d, "ring_bits": 2 * J,
                                  "transform_length": L, "stages": [L1, L2]})
        return tuple(result)

    def gf_reduce(self, word, field):
        work = list(word)
        taps = [i for i in range(field.degree) if field.polynomial >> i & 1]
        zero = self.constant(0, 1)[0]
        for position in range(len(work) - 1, field.degree - 1, -1):
            high = work[position]
            for tap in taps:
                index = position - field.degree + tap
                work[index] = self.xor_bit(work[index], high)
            work[position] = zero
        return tuple(work[:field.degree])

    def gf_multiply(self, left, right, field):
        return self.gf_reduce(self.polynomial_multiply(left, right), field)

    def gf_square(self, word, field):
        raw = [self.constant(0, 1)[0]] * (2 * len(word) - 1)
        raw[::2] = word
        return self.gf_reduce(raw, field)

    def assignment(self, inputs):
        values = {}
        for word, number in inputs.items():
            if not 0 <= number < 1 << len(word):
                raise ValueError("input does not fit its word")
            values.update({variable: (number >> i) & 1 for i, variable in enumerate(word)})
        values.update({variable: bit for bit, variable in self.constants.items()})
        for words, outputs, function in self.steps:
            arguments = tuple(bits_value(tuple(values[v] for v in word)) for word in words)
            result = tuple(function(arguments))
            if len(result) != len(outputs):
                raise ArithmeticError("wrong number of computed output words")
            for word, value in zip(outputs, result):
                if not 0 <= value < 1 << len(word):
                    raise ArithmeticError("computed value does not fit output word")
                for i, variable in enumerate(word):
                    bit = value >> i & 1
                    if variable in values and values[variable] != bit:
                        raise ValueError("inconsistent supplied witness")
                    values[variable] = bit
        return values

    def check(self, assignment):
        return [name for variables, entry, name in self.builder.constraints
                if not entry(tuple(assignment[v] for v in variables))]

    def statistics(self, interface=()):
        occurrences = [0] * self.builder.variables
        for variables, _, _ in self.builder.constraints:
            for v in variables:
                occurrences[v] += 1
        for v in dict.fromkeys(interface):
            occurrences[v] += 1
        edges = sum(0 if d == 0 else (1 if d <= 2 else 2 * d - 3) for d in occurrences)
        return {"variables": self.builder.variables, "constraints": len(self.builder.constraints),
                "boolean_network_edges": 2 * edges,
                "maximum_degree": max(3, max((len(v) for v, _, _ in self.builder.constraints), default=0)),
                "multiplication_encodings": self.mul_metadata}


@dataclass(frozen=True)
class PointWords:
    infinity: tuple
    x: tuple
    y: tuple

    @property
    def words(self):
        return self.infinity, self.x, self.y


class BinaryCurveEncoding:
    def __init__(self, curve: BinaryCurve):
        self.curve, self.field = curve, curve.field
        self.circuit = WordCircuit()
        self.validated = set()

    def point(self):
        c, b = self.circuit, self.field.degree
        return PointWords(c.word(1), c.word(b), c.word(b))

    @staticmethod
    def values(point):
        return (1, 0, 0) if point is None else (0, point[0], point[1])

    @staticmethod
    def decoded(values):
        return None if values[0] else (values[1], values[2])

    def constant_point(self, point):
        c, b = self.circuit, self.field.degree
        flag, x, y = self.values(point)
        return PointWords(c.constant(flag, 1), c.constant(x, b), c.constant(y, b))

    def equal_points(self, left, right, selector=None):
        for a, b in zip(left.words, right.words):
            self.circuit.equal(a, b, selector)

    def valid(self, point):
        if point in self.validated:
            return
        self.validated.add(point)
        c, f = self.circuit, self.field
        finite = c.not_bit(point.infinity[0])
        zero = c.constant(0, f.degree)
        c.equal(point.x, zero, point.infinity[0])
        c.equal(point.y, zero, point.infinity[0])
        x2, y2 = c.gf_square(point.x, f), c.gf_square(point.y, f)
        xy = c.gf_multiply(point.x, point.y, f)
        x3 = c.gf_multiply(x2, point.x, f)
        a_x2 = zero if self.curve.a == 0 else (x2 if self.curve.a == 1 else c.gf_multiply(c.constant(self.curve.a, f.degree), x2, f))
        c.equal(c.xor(y2, xy), c.xor(x3, a_x2, c.constant(self.curve.b, f.degree)), finite)

    def add(self, left, right):
        c, f = self.circuit, self.field
        result = self.point()
        c.hint(left.words + right.words, result.words,
               lambda v: self.values(self.curve.add(self.decoded(v[:3]), self.decoded(v[3:]))))
        for point in (left, right, result):
            self.valid(point)
        both = c.and_bit(c.not_bit(left.infinity[0]), c.not_bit(right.infinity[0]))
        xdiff, ydiff = c.xor(left.x, right.x), c.xor(left.y, right.y)
        equal_x, equal_y, zero_x = c.is_zero(xdiff), c.is_zero(ydiff), c.is_zero(left.x)
        generic = c.and_bit(both, c.not_bit(equal_x))
        doubling = c.and_bit(both, equal_x, equal_y, c.not_bit(zero_x))
        inverse = c.and_bit(both, equal_x, c.not_bit(c.and_bit(equal_y, c.not_bit(zero_x))))
        pass_right, pass_left = left.infinity[0], c.and_bit(c.not_bit(left.infinity[0]), right.infinity[0])
        slope = c.word(f.degree)

        def slope_hint(v):
            P, Q = self.decoded(v[:3]), self.decoded(v[3:])
            if P is None or Q is None:
                return (0,)
            if P[0] != Q[0]:
                return (f.div(P[1] ^ Q[1], P[0] ^ Q[0]),)
            return (P[0] ^ f.div(P[1], P[0]),) if P == Q and P[0] else (0,)

        c.hint(left.words + right.words, (slope,), slope_hint)
        c.equal(c.gf_multiply(slope, xdiff, f), ydiff, generic)
        c.equal(c.gf_multiply(slope, left.x, f), c.xor(c.gf_square(left.x, f), left.y), doubling)
        active = c.xor_bit(generic, doubling)
        c.equal(slope, c.constant(0, f.degree), c.not_bit(active))
        expected_x = c.xor(c.gf_square(slope, f), slope, left.x, right.x, c.constant(self.curve.a, f.degree))
        c.equal(result.x, expected_x, active)
        expected_y = c.xor(c.gf_multiply(slope, c.xor(left.x, result.x), f), result.x, left.y)
        c.equal(result.y, expected_y, active)
        c.equal(result.infinity, c.constant(0, 1), active)
        c.equal(result.infinity, c.constant(1, 1), inverse)
        self.equal_points(result, right, pass_right)
        self.equal_points(result, left, pass_left)
        return result

    def in_subgroup_image(self, point, order, cofactor):
        if cofactor < 1 or cofactor & (cofactor - 1):
            raise ValueError("this encoder supports a power-of-two fixed cofactor")
        witness = self.point()
        inverse = pow(cofactor, -1, order)
        self.circuit.hint(point.words, witness.words,
                          lambda v: self.values(self.curve.mul(inverse, self.decoded(v))))
        image = witness
        for _ in range(cofactor.bit_length() - 1):
            image = self.add(image, image)
        self.equal_points(point, image)
        self.circuit.equal(point.infinity, self.circuit.constant(0, 1))

    def hashed_membership(self, point, prime, alpha, beta, threshold):
        c, f = self.circuit, self.field
        if not (prime > 2 * f.size and 0 < alpha < prime and 0 <= beta < prime and 0 < threshold <= prime):
            raise ValueError("invalid affine factor-base parameters")
        ratio = c.word(f.degree)
        c.hint((point.x, point.y), (ratio,), lambda v: (f.div(v[1], v[0]) if v[0] else 0,))
        c.equal(c.gf_multiply(point.x, ratio, f), point.y)
        encoded = (ratio[0],) + point.x
        width = prime.bit_length()
        quotient, residue = c.word(width), c.word(width)
        c.hint((encoded,), (quotient, residue), lambda v: divmod(alpha * v[0] + beta, prime))
        left = c.integer_multiply(c.constant(alpha, width), encoded)
        right = c.integer_multiply(quotient, c.constant(prime, width))
        lhs = c.add_integer(left, c.constant(beta, width), 2 * width + 1)
        rhs = c.add_integer(right, residue, 2 * width + 1)
        c.equal(lhs, rhs)
        less = c.less_than_constant(residue, threshold)
        c.equal((less,), c.constant(1, 1))

    def relation(self, target, seeds, order, cofactor):
        points = [self.point() for _ in seeds]
        # All point coordinates are free interface inputs. All other values are
        # constrained witnesses; the testing hints do not enter the graph.
        for point, seed in zip(points, seeds):
            self.valid(point)
            self.in_subgroup_image(point, order, cofactor)
            self.hashed_membership(point, seed["prime"], seed["alpha"], seed["beta"], seed["threshold"])
        total = points[0]
        for point in points[1:]:
            total = self.add(total, point)
        self.equal_points(total, self.constant_point(target))
        return points
