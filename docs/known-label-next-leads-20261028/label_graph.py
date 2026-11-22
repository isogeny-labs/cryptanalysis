"""Recover labels from verified pair-sum witnesses; no point-search oracle.

An edge (i, j, (a,b)) certifies R_i + R_j = [a]P + [b]Q.
Inputs must be verified by the caller. Returned cycle certificates must also
be checked by group arithmetic before accepting a recovered logarithm.
"""
from collections import deque


def recover_labels(vertex_count, edges, order, anchors=None):
    """Return labels, unresolved components and zero-relation certificates.

    order is an odd prime. A nonzero certificate (a,b), b != 0, gives
    candidate log_P(Q) = -a/b; this function does not verify that candidate.
    Cost excludes discovering/verifying edges and all final group checks.
    """
    if order <= 2 or order % 2 == 0:
        raise ValueError('odd prime order required')
    anchors = anchors or {}
    adjacency = [[] for _ in range(vertex_count)]
    for i, j, label in edges:
        if not (0 <= i < vertex_count and 0 <= j < vertex_count):
            raise ValueError('vertex outside graph')
        t = tuple(x % order for x in label)
        if len(t) != 2:
            raise ValueError('two label coefficients required')
        adjacency[i].append((j, t))
        adjacency[j].append((i, t))

    def add(a, b):
        return tuple((x+y) % order for x, y in zip(a, b))

    def sub(a, b):
        return tuple((x-y) % order for x, y in zip(a, b))

    def scale(c, a):
        return tuple(c*x % order for x in a)

    labels, unresolved, certificates, visited = {}, [], [], set()
    certificate_seen = set()

    def certificate(value):
        if value != (0, 0):
            if value not in certificate_seen:
                certificate_seen.add(value)
                certificates.append(value)

    for root in range(vertex_count):
        if root in visited:
            continue
        sign, offset = {root: 1}, {root: (0, 0)}
        component, queue = [], deque([root])
        root_label = None

        def constrain(candidate):
            nonlocal root_label
            if root_label is None:
                root_label = candidate
            else:
                certificate(sub(root_label, candidate))

        while queue:
            i = queue.popleft()
            if i in visited:
                continue
            visited.add(i)
            component.append(i)
            if i in anchors:
                constrain(scale(sign[i], sub(anchors[i], offset[i])))
            for j, t in adjacency[i]:
                if j not in sign:
                    sign[j] = -sign[i]
                    offset[j] = sub(t, offset[i])
                    queue.append(j)
                coefficient = sign[i] + sign[j]
                residual = sub(t, add(offset[i], offset[j]))
                if coefficient:
                    constrain(scale(pow(coefficient % order, -1, order), residual))
                else:
                    certificate(residual)
        if root_label is None:
            unresolved.append(component)
        else:
            for i in component:
                labels[i] = add(scale(sign[i], root_label), offset[i])
    return {'labels': labels, 'unresolved_components': unresolved,
            'zero_relation_certificates': certificates}


def prony_parameters(s1, s2, s3, order):
    """Recover k, i+j, i*j from moments i^m+j^m-k^m, m=1,2,3.

    All three indices must be distinct and order must be prime > 3.
    The caller still checks the two quadratic roots, index range and points.
    """
    if order <= 3:
        raise ValueError('prime order greater than three required')
    delta = (s1*s1-s2)*pow(2, -1, order) % order
    if not delta:
        raise ValueError('degenerate signed signature')
    k = (-s1**3+3*s1*s2-2*s3)*pow(6*delta % order, -1, order) % order
    return k, (s1+k) % order, (delta+k*s1) % order
