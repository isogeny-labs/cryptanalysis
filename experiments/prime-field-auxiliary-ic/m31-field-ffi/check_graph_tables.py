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
    assembly = re.search(rf"^def {name}Table : Array Nat := (.+)$", source, re.M)
    chunks = []
    for part in assembly[1].split(" ++ "):
        match = re.search(rf"private def {re.escape(part)} : Array Nat := #\[([\d,\s]+)\]", source)
        chunks.extend(int(value) for value in match[1].split(","))
    return chunks


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
