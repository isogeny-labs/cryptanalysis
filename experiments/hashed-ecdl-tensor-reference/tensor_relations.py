"""Hashed factor-base relation search using a Boolean tensor backend.

Indexed networks are useful executable validation fixtures. They explicitly
contain factor-base lists and do not have the compact coordinate encoding's
asymptotic guarantees. The coordinate encoder is a separate construction.
"""

from tensor_contraction import TensorContraction, WorkBudget
from tensor_network import BooleanNetwork, Tensor


class IndexedTensorRelations:
    def __init__(self, curve, bases, max_operations, deadline):
        self.curve, self.bases = curve, bases
        import time
        self.engine = TensorContraction(budget=WorkBudget(max_operations, max(0.001, deadline - time.monotonic())))
        self.widths = [max(1, (len(base.points) - 1).bit_length()) for base in bases]
        self.edges = sum(self.widths)
        self.offsets, offset = [], 0
        for width in self.widths:
            self.offsets.append(offset)
            offset += width

    def network(self, target):
        widths, offsets, bases, curve = self.widths, self.offsets, self.bases, self.curve

        def relation(bits):
            indices = [sum(bits[offset + j] << j for j in range(width)) for offset, width in zip(offsets, widths)]
            if any(index >= len(base.points) for index, base in zip(indices, bases)):
                return 0
            return int(curve.total(base.points[index] for index, base in zip(indices, bases)) == target)

        tensors = [Tensor(0, tuple(range(self.edges)), relation, "indexed_point_sum")]
        for base, width, offset in zip(bases, widths, offsets):
            def valid_index(bits, count=len(base.points)):
                return int(sum(bit << j for j, bit in enumerate(bits)) < count)
            tensors.append(Tensor(1, tuple(range(offset, offset + width)), valid_index, "index_domain"))
        return BooleanNetwork(tuple(tensors))

    def find(self, target):
        bits = self.engine.boolean_witness(self.network(target), tuple(range(self.edges)))
        if bits is None:
            return None
        return tuple(sum(bits[offset + j] << j for j in range(width))
                     for offset, width in zip(self.offsets, self.widths))


class CoordinateTensorRelations:
    def __init__(self, instance, bases, max_operations, deadline):
        import time
        self.instance, self.bases = instance, bases
        self.engine = TensorContraction(budget=WorkBudget(max_operations, max(0.001, deadline - time.monotonic())))

    def find(self, target):
        from tensor_encoding import BinaryCurveEncoding, bits_value
        if self.instance.as_dict().get("field_type") == "prime":
            from tensor_prime import PrimeCurveEncoding
            encoding = PrimeCurveEncoding(self.instance.curve)
        else:
            encoding = BinaryCurveEncoding(self.instance.curve)
        seeds = [{"prime": b.prime, "alpha": b.alpha, "beta": b.beta, "threshold": b.threshold} for b in self.bases]
        points = encoding.relation(target, seeds, self.instance.order, self.instance.cofactor)
        interface = tuple(v for point in points for word in point.words for v in word)
        network, mapping = encoding.circuit.builder.compile(interface)
        bits = self.engine.witness(network, [mapping[v] for v in interface])
        if bits is None:
            return None
        b, offset, indices = self.instance.curve.field.degree, 0, []
        for base in self.bases:
            flag, x, y = bits[offset], bits_value(bits[offset + 1:offset + 1 + b]), bits_value(bits[offset + 1 + b:offset + 1 + 2 * b])
            if flag:
                raise ArithmeticError("coordinate witness returned an identity base point")
            point = x, y
            if point not in base.points:
                raise ArithmeticError("coordinate witness is not in its factor base")
            indices.append(base.points.index(point))
            offset += 1 + 2 * b
        return tuple(indices)
