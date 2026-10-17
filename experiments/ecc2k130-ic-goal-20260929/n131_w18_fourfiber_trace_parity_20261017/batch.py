"""Batch exact terminal residual subtraction and reciprocal coordinates."""
import time


def batch_invert(nonzero, mul, inverse):
    """Montgomery trick: one field inversion for all nonzero inputs."""
    assert all(nonzero)
    if not nonzero:
        return [], 0
    prefix = [1]
    for value in nonzero:
        prefix.append(mul(prefix[-1], value))
    inverse_total = inverse(prefix[-1])
    output = [0] * len(nonzero)
    for index in range(len(nonzero) - 1, -1, -1):
        output[index] = mul(inverse_total, prefix[index])
        inverse_total = mul(inverse_total, nonzero[index])
    assert inverse_total == 1
    assert all(mul(value, inv) == 1 for value, inv in zip(nonzero, output))
    return output, 1


def residuals(raw_target, joint_states, arithmetic):
    """Preserve the prior ordered row schema, including exceptional points."""
    start = time.monotonic_ns()
    x_target, y_target = raw_target
    plans = []
    denominators = []
    fallback_count = 0
    for index, row in enumerate(joint_states):
        joint = row['raw_sum']
        if joint is None or x_target == joint[0]:
            plans.append(('fallback', index, joint))
            fallback_count += 1
        else:
            x_joint, y_joint = joint
            plans.append(('batch', index, (x_joint, y_joint ^ x_joint)))
            denominators.append(x_target ^ x_joint)
    prepared_ns = time.monotonic_ns() - start
    start = time.monotonic_ns()
    slopes_inv, first_inversions = batch_invert(denominators, arithmetic.mul,
                                                 arithmetic.inverse)
    denominator_ns = time.monotonic_ns() - start
    start = time.monotonic_ns()
    points = [None] * len(joint_states)
    next_inv = 0
    for kind, index, data in plans:
        if kind == 'fallback':
            if data is None:
                point = tuple(raw_target)
            else:
                x_joint, y_joint = data
                point = arithmetic.point_add(tuple(raw_target),
                    (x_joint, y_joint ^ x_joint))
        else:
            x_joint, negated_y = data
            slope = arithmetic.mul(y_target ^ negated_y, slopes_inv[next_inv])
            next_inv += 1
            x = arithmetic.square(slope) ^ slope ^ x_target ^ x_joint
            y = arithmetic.mul(slope, x_target ^ x) ^ x ^ y_target
            point = (x, y)
        points[index] = point
    assert next_inv == len(denominators)
    point_ns = time.monotonic_ns() - start
    start = time.monotonic_ns()
    regular = [(index, point[0]) for index, point in enumerate(points)
               if point is not None and point[0] not in (0, 1)]
    x_inverses, second_inversions = batch_invert(
        [x for _, x in regular], arithmetic.mul, arithmetic.inverse)
    reciprocals = [None] * len(points)
    for (index, x), inv in zip(regular, x_inverses):
        reciprocals[index] = inv
    reciprocal_ns = time.monotonic_ns() - start
    start = time.monotonic_ns()
    result = [{'left_state_id': row['left_state_id'],
               'right_state_id': row['right_state_id'],
               'point': list(points[index]) if points[index] is not None else None,
               'standard_reciprocal': reciprocals[index]}
              for index, row in enumerate(joint_states)]
    output_ns = time.monotonic_ns() - start
    return result, {'preparation_ns': prepared_ns, 'denominator_batch_ns': denominator_ns,
                    'point_arithmetic_ns': point_ns, 'reciprocal_batch_ns': reciprocal_ns,
                    'output_ns': output_ns, 'batch_inversions': first_inversions+second_inversions,
                    'fallback_point_additions': fallback_count,
                    'nonexceptional_residuals': len(regular),
                    'exceptional_residuals': len(points)-len(regular)}
