"""Affine propagation for verified Ri + sign*Rj = aP+bQ witnesses.

Signs are +/-1. Discovery, subgroup tests and final group/scalar replay are
outside this algebraic core and must be charged by a complete constructor.
"""
from collections import deque


def recover_signed_labels(vertex_count, edges, order, anchors=None):
    if order <= 3 or order % 2 == 0:
        raise ValueError('odd prime order greater than three required')
    anchors = anchors or {}
    adjacency = [[] for _ in range(vertex_count)]

    def plus(a, b):
        return tuple((x+y) % order for x, y in zip(a, b))

    def scale(c, a):
        return tuple(c*x % order for x in a)

    def minus(a, b):
        return plus(a, scale(-1, b))

    for i, j, sign, label in edges:
        if sign not in (-1, 1) or not (0 <= i < vertex_count and 0 <= j < vertex_count):
            raise ValueError('invalid signed edge')
        if len(label) != 2:
            raise ValueError('two label coefficients required')
        t = tuple(x % order for x in label)
        adjacency[i].append((j, -sign, scale(sign, t)))
        adjacency[j].append((i, -sign, t))
    labels, unresolved, certificates, visited, seen = {}, [], [], set(), set()

    def certificate(value):
        if value != (0, 0) and value not in seen:
            seen.add(value)
            certificates.append(value)

    for root in range(vertex_count):
        if root in visited:
            continue
        coefficient, offset = {root: 1}, {root: (0, 0)}
        component, queue, root_label = [], deque([root]), None

        def constrain(candidate):
            nonlocal root_label
            if root_label is None:
                root_label = candidate
            else:
                certificate(minus(root_label, candidate))

        while queue:
            i = queue.popleft()
            if i in visited:
                continue
            visited.add(i)
            component.append(i)
            if i in anchors:
                if len(anchors[i]) != 2:
                    raise ValueError('invalid anchor')
                constrain(scale(coefficient[i], minus(anchors[i], offset[i])))
            for j, a, t in adjacency[i]:
                if j not in coefficient:
                    coefficient[j] = a*coefficient[i]
                    offset[j] = plus(scale(a, offset[i]), t)
                    queue.append(j)
                c = (coefficient[j]-a*coefficient[i]) % order
                residual = minus(plus(scale(a, offset[i]), t), offset[j])
                if c:
                    constrain(scale(pow(c, -1, order), residual))
                else:
                    certificate(residual)
        if root_label is None:
            unresolved.append(component)
        else:
            for i in component:
                labels[i] = plus(scale(coefficient[i], root_label), offset[i])
    return {'labels': labels, 'unresolved_components': unresolved,
            'zero_relation_certificates': certificates}
