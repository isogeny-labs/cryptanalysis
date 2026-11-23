"""Regenerate the two M31 XOR graphs and compare their labels with the Lean certificate."""

from pathlib import Path
import re

P = 2**31 - 1
ORDER = 2046
GENERATOR = 1448159583


def generate(keys, width, salt):
    """An edge requires label[left] XOR label[right] to equal the reciprocal."""
    graph = {}
    for key in keys:
        left = key % width
        right = width + ((key * salt) % 2**32 * width // 2**32)
        reciprocal = pow(key, -1, P)
        graph.setdefault(left, []).append((right, reciprocal))
        graph.setdefault(right, []).append((left, reciprocal))

    labels = [None] * (2 * width)
    for root in graph:
        if labels[root] is not None:
            continue
        labels[root] = 0
        stack = [root]
        while stack:
            vertex = stack.pop()
            for neighbor, reciprocal in graph[vertex]:
                required = labels[vertex] ^ reciprocal
                if labels[neighbor] is None:
                    labels[neighbor] = required
                    stack.append(neighbor)
                elif labels[neighbor] != required:
                    return None
    return [0 if value is None else value for value in labels]


def certificate_labels(source, name):
    body = source.split(f"private def {name}Block : Nat → Nat\n", 1)[1].split("  | _ => 0", 1)[0]
    labels = []
    for expected, line in enumerate(body.splitlines()):
        match = re.fullmatch(r"  \| (\d+) => (0x[0-9a-f]+)", line)
        if match is None or int(match[1]) != expected:
            raise ValueError(f"invalid {name} block {expected}")
        packed = int(match[2], 16)
        if packed.bit_length() > 32 * 64:
            raise ValueError(f"oversized {name} block {expected}")
        labels.extend((packed >> (32 * i)) & 0xffffffff for i in range(64))
    return labels


def main():
    source = Path(__file__).with_name("GraphReciprocal.lean").read_text()
    keys = [pow(GENERATOR, exponent, P) for exponent in range(ORDER)]
    if len(set(keys)) != ORDER or pow(GENERATOR, ORDER, P) != 1:
        raise ValueError("invalid subgroup generator")
    for name, width in [("raw", 2048), ("signed", 1024)]:
        active = keys if name == "raw" else [key for key in keys if key <= P // 2]
        for trial in range(256):
            salt = 2654435761 + 2 * trial
            labels = generate(active, width, salt)
            if labels is not None:
                break
        else:
            raise ValueError(f"no consistent labeling for {name}")
        if labels != certificate_labels(source, name):
            raise ValueError(f"{name} graph differs from certificate")
        print(f"{name}: {len(active)} keys, {len(labels)} matching words, salt {salt}")


if __name__ == "__main__":
    main()
