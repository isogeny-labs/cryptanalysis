#!/usr/bin/env python3
"""Verify the additive input transition for the chained-transfer replay.

This verifier separates three things that the historical replay used to mix:
the immutable predecessor evidence, the declared successor source closure, and
the exact predecessor checkout needed to replay the old fifty-file baseline.
It does not claim that a replay has run or that any mathematical statement is
independently certified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


SCHEMA = "chained-transfer-input-transition/v1"
PREDECESSOR_COMMIT = "635bd2d2b57af89fb474039db6fcba72631bf681"
PREDECESSOR_TREE = "b328e41853425da220fd19904a2a270745dfd0a9"
BASELINE_PATH = (
    "experiments/chained-transfer-reference/evidence/"
    "fp-chain-primary-01/baseline.json"
)
BASELINE_BYTES = 7_133
BASELINE_SHA256 = "f36ff1dc4e863500e4676550b0d9e588965d3a57323775bd7054492639645053"
BASELINE_COUNT = 50
REFERENCE_MANIFEST_PATH = "experiments/chained-transfer-reference/reference.sha256"
REFERENCE_MANIFEST_BYTES = 418
REFERENCE_MANIFEST_SHA256 = (
    "2234198b617666889eaf69cc26d8192b69de24f63e99d477628c6fc0d31c4fd2"
)
REFERENCE_MANIFEST_COUNT = 4
FROZEN_WORKFLOW_PATH = (
    "experiments/chained-transfer-reference/evidence/"
    "fp-chain-primary-01/five-original-jobs.yml"
)
FROZEN_WORKFLOW_BYTES = 16_651
FROZEN_WORKFLOW_SHA256 = (
    "bf131a55292cc9a9a5fe511737e364d1d1b6a15e90cee0c47357cb4ce1650180"
)
CURRENT_WORKFLOW_PATH = ".github/workflows/chained-transfer-reference.yml"
CURRENT_PREFIX_SHA256 = (
    "0adde6d199b330517bb4498f8568a306f8252a21a420075e98d12c637c608407"
)
BASELINE_REPLACEMENTS = [
    {
        "path": "suite/src/prime_hyperelliptic/mod.rs",
        "predecessor_bytes": 2_688,
        "predecessor_sha256": (
            "b6906f75b4d0eb6b7ac406a0fca1b2cef1786a528d4aedbab414e9fa1e7f7662"
        ),
        "successor_bytes": 4_632,
        "successor_sha256": (
            "32b996fe614230480c11edd695cd778018fac0d7443d6a1f3907d4bf79c78bed"
        ),
    },
    {
        "path": "experiments/chained-transfer-reference/src/main.rs",
        "predecessor_bytes": 9_178,
        "predecessor_sha256": (
            "9043538f18ca55032db06b7f8f65f9af1f4b4b71621a2271287150182b2d255c"
        ),
        "successor_bytes": 9_399,
        "successor_sha256": (
            "cad27d86a308109110654ac157d0b0bd3ddd0d57a1ae54ab2ed76abb00c43915"
        ),
    },
    {
        "path": "experiments/chained-transfer-reference/src/seven.rs",
        "predecessor_bytes": 11_314,
        "predecessor_sha256": (
            "bb640465bfe9406e5b5e275b5127c73417b48cec5a90006d2f2bb87f72f40ae9"
        ),
        "successor_bytes": 11_347,
        "successor_sha256": (
            "6d6270118d33c133e7b24ee7ab4a422faa2652c0633f295e4ac31b5f77c1ca9e"
        ),
    },
]
BASELINE_REPLACEMENT_PATHS = {record["path"] for record in BASELINE_REPLACEMENTS}
HARNESS_FILES = {
    "cargo_toml": {
        "path": "experiments/chained-transfer-reference/Cargo.toml",
        "bytes": 707,
        "sha256": "90217411120ccef1f5886e3af29b55e708017032be905ab577e381ad4e7dd85e",
    },
    "cargo_lock": {
        "path": "experiments/chained-transfer-reference/Cargo.lock",
        "bytes": 6_461,
        "sha256": "ef293c677ca00cfeda4ab29db64a9daa4b6926b564c39e9b53edb47073410521",
    },
}
PREFIX_REPLACEMENT = {
    "zero_based_byte_offset": 4_908,
    "length": 40,
    "before": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    "after": "cf430e030ddbb5b0abf93d22962f4752f3646cd9",
    "change_commit": "9468130a586f5c70d2a25a19872d8f1c178f3e42",
    "merge_commit": "84628f6a93438f1544050815cd46999f07592a78",
}
REFERENCE_INPUTS = [
    (
        "suite/src/prime_hyperelliptic/balanced.rs",
        41_245,
        "5a5f275021cf901e44a2a2a0e3fb9238e55da2772a1620ec153d0d8e4461d451",
    ),
    (
        "suite/src/prime_hyperelliptic/cover_transfer.rs",
        42_227,
        "10bb0b0fd2c35b8fafb9e5570c01c5ff597f43a71bdac49a9b9f7e51ad5093a4",
    ),
    (
        "suite/src/prime_hyperelliptic/curve.rs",
        58_596,
        "7a769bfb7abfe92ce06da7c02340f2a2426827d8066ebef510375149b8c3d5ad",
    ),
    (
        "suite/src/prime_hyperelliptic/fp2.rs",
        12_739,
        "b833bdff5247f2eea0cde7feb89d0378cfe8305671f9065d2dae7ab538c03e55",
    ),
    (
        "suite/src/prime_hyperelliptic/fp_poly.rs",
        11_867,
        "44f7af14d22bed78d85c4bd009ccce7197fa9257e7ff56164c8d891303e49590",
    ),
    (
        "suite/src/prime_hyperelliptic/mod.rs",
        4_632,
        "32b996fe614230480c11edd695cd778018fac0d7443d6a1f3907d4bf79c78bed",
    ),
    (
        "suite/src/prime_hyperelliptic/model_transfer.rs",
        17_517,
        "cf8d723a0aadd9a4bbdcd2dd56e581ee4bdc0253513d6da9deba95fc5f67ec50",
    ),
    (
        "suite/src/prime_hyperelliptic/normalized_cover_transfer.rs",
        20_963,
        "35f81b57d72b4f12e1c14a2392e2510982ca9225843117798c0f1e80d16a571a",
    ),
    (
        "suite/src/prime_hyperelliptic/primality.rs",
        8_218,
        "3b055ac166717960963e4e80b7d75eaba6c1681a7bc2e7ddfbb0d4af4d5aaf1c",
    ),
]
REFERENCE_INPUT_PATHS = {row[0] for row in REFERENCE_INPUTS}
NEW_REFERENCE_PATHS = {
    "suite/src/prime_hyperelliptic/balanced.rs",
    "suite/src/prime_hyperelliptic/cover_transfer.rs",
    "suite/src/prime_hyperelliptic/model_transfer.rs",
    "suite/src/prime_hyperelliptic/normalized_cover_transfer.rs",
    "suite/src/prime_hyperelliptic/primality.rs",
}
AGGREGATE_MANIFEST_BYTES = 988
AGGREGATE_MANIFEST_SHA256 = (
    "934583411129ac6ca7aa7cfab5a687ac14b242fa3866861a5fb7f529866744c8"
)
IMPLEMENTATION_PATHS = {
    "check_sh": "experiments/chained-transfer-reference/check.sh",
    "check_fp_chain_sh": "experiments/chained-transfer-reference/check-fp-chain.sh",
    "verifier": (
        "experiments/chained-transfer-reference/"
        "verify-fp-chain-input-transition.py"
    ),
}


class VerificationError(RuntimeError):
    """A deterministic input-custody check failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_bytes(root: Path, relative: str) -> bytes:
    path = root / relative
    require(path.is_file(), f"missing required file:{relative}")
    return path.read_bytes()


def check_bytes(root: Path, relative: str, size: int, digest: str) -> bytes:
    data = read_bytes(root, relative)
    require(len(data) == size, f"wrong byte count:{relative}")
    require(sha256_bytes(data) == digest, f"wrong sha256:{relative}")
    return data


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot load JSON:{path}:{exc}") from exc
    require(isinstance(value, dict), f"JSON root is not an object:{path}")
    return value


def git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise VerificationError(f"git command failed:{' '.join(args)}") from exc
    return result.stdout.strip()


def validate_transition(value: dict[str, Any]) -> None:
    require(value.get("schema") == SCHEMA, "wrong transition schema")
    require(
        value.get("record_state") == "declared_successor_inputs",
        "wrong transition record state",
    )
    require(
        value.get("authority")
        == "input declaration; not a replay receipt or scientific certificate",
        "wrong transition authority",
    )
    predecessor = value.get("predecessor")
    require(isinstance(predecessor, dict), "missing predecessor record")
    require(
        predecessor.get("repository") == "aburan28/cryptanalysis",
        "wrong predecessor repository",
    )
    require(
        predecessor.get("commit") == PREDECESSOR_COMMIT,
        "wrong predecessor commit",
    )
    require(predecessor.get("tree") == PREDECESSOR_TREE, "wrong predecessor tree")
    expected_artifacts = {
        "baseline": (BASELINE_PATH, BASELINE_BYTES, BASELINE_SHA256, "entry_count", 50),
        "reference_manifest": (
            REFERENCE_MANIFEST_PATH,
            REFERENCE_MANIFEST_BYTES,
            REFERENCE_MANIFEST_SHA256,
            "entry_count",
            4,
        ),
        "workflow_prefix": (
            FROZEN_WORKFLOW_PATH,
            FROZEN_WORKFLOW_BYTES,
            FROZEN_WORKFLOW_SHA256,
            None,
            None,
        ),
    }
    for key, (path, size, digest, count_key, count) in expected_artifacts.items():
        record = predecessor.get(key)
        require(isinstance(record, dict), f"missing predecessor artifact:{key}")
        require(record.get("path") == path, f"wrong predecessor path:{key}")
        require(record.get("bytes") == size, f"wrong predecessor size:{key}")
        require(record.get("sha256") == digest, f"wrong predecessor digest:{key}")
        if count_key is not None:
            require(record.get(count_key) == count, f"wrong predecessor count:{key}")

    successor = value.get("successor")
    require(isinstance(successor, dict), "missing successor record")
    require(
        successor.get("retained_baseline_entry_count") == 47,
        "wrong retained baseline count",
    )
    replacements = successor.get("replaced_baseline_entries")
    require(replacements == BASELINE_REPLACEMENTS, "wrong replacement records")
    harness = successor.get("harness_files")
    require(harness == HARNESS_FILES, "wrong successor harness file records")
    require(
        set(successor.get("new_reference_paths", [])) == NEW_REFERENCE_PATHS,
        "wrong new reference path set",
    )
    require(
        successor.get("reference_manifest_serialization")
        == "sorted ASCII '<sha256>  <path>\\n'",
        "wrong aggregate manifest serialization",
    )
    require(
        successor.get("reference_manifest_bytes") == AGGREGATE_MANIFEST_BYTES,
        "wrong aggregate manifest size",
    )
    require(
        successor.get("reference_manifest_sha256") == AGGREGATE_MANIFEST_SHA256,
        "wrong aggregate manifest digest",
    )
    rows = successor.get("reference_inputs")
    require(isinstance(rows, list), "missing reference input rows")
    normalized_rows = []
    for row in rows:
        require(
            isinstance(row, list)
            and len(row) == 3
            and isinstance(row[0], str)
            and isinstance(row[1], int)
            and isinstance(row[2], str),
            "malformed reference input row",
        )
        normalized_rows.append((row[0], row[1], row[2]))
    require(normalized_rows == REFERENCE_INPUTS, "wrong reference input closure")

    workflow_prefix = successor.get("workflow_prefix")
    require(isinstance(workflow_prefix, dict), "missing successor workflow prefix")
    require(
        workflow_prefix.get("bytes") == FROZEN_WORKFLOW_BYTES,
        "wrong successor prefix size",
    )
    require(
        workflow_prefix.get("sha256") == CURRENT_PREFIX_SHA256,
        "wrong successor prefix digest",
    )
    require(
        workflow_prefix.get("allowed_replacements") == [PREFIX_REPLACEMENT],
        "wrong workflow-prefix replacement",
    )

    full_workflow = successor.get("full_workflow")
    require(isinstance(full_workflow, dict), "missing full workflow record")
    require(full_workflow.get("path") == CURRENT_WORKFLOW_PATH, "wrong workflow path")
    require(
        isinstance(full_workflow.get("bytes"), int) and full_workflow["bytes"] > 0,
        "missing full workflow size",
    )
    require(
        isinstance(full_workflow.get("sha256"), str)
        and len(full_workflow["sha256"]) == 64,
        "missing full workflow digest",
    )
    implementation = successor.get("implementation_files")
    require(isinstance(implementation, dict), "missing implementation file records")
    require(set(implementation) == set(IMPLEMENTATION_PATHS), "wrong implementation file set")
    for key, path in IMPLEMENTATION_PATHS.items():
        record = implementation[key]
        require(isinstance(record, dict), f"malformed implementation record:{key}")
        require(record.get("path") == path, f"wrong implementation path:{key}")
        require(
            isinstance(record.get("bytes"), int) and record["bytes"] > 0,
            f"missing implementation size:{key}",
        )
        require(
            isinstance(record.get("sha256"), str) and len(record["sha256"]) == 64,
            f"missing implementation digest:{key}",
        )
    require(
        value.get("claims")
        == {
            "historical_inputs_verified": True,
            "historical_run_reexecuted": False,
            "successor_replay_required": True,
            "mathematical_claim_changed": False,
        },
        "wrong transition claim boundary",
    )


def load_baseline(root: Path) -> dict[str, str]:
    baseline = load_json(root / BASELINE_PATH)
    mapping = baseline.get("non_workflow_inputs")
    require(isinstance(mapping, dict), "baseline input map missing")
    require(
        all(isinstance(key, str) and isinstance(digest, str) for key, digest in mapping.items()),
        "baseline input map malformed",
    )
    require(len(mapping) == BASELINE_COUNT, "wrong baseline map count")
    require(baseline.get("count") == BASELINE_COUNT, "wrong baseline declared count")
    require(
        baseline.get("five_whole_job_prefix_bytes") == FROZEN_WORKFLOW_BYTES,
        "wrong baseline workflow-prefix size",
    )
    require(
        baseline.get("five_whole_job_prefix_sha256") == FROZEN_WORKFLOW_SHA256,
        "wrong baseline workflow-prefix digest",
    )
    for record in BASELINE_REPLACEMENTS:
        require(
            mapping.get(record["path"]) == record["predecessor_sha256"],
            f"baseline replacement mismatch:{record['path']}",
        )
    return mapping


def reconstructed_prefix(frozen: bytes) -> bytes:
    replacement = PREFIX_REPLACEMENT
    offset = replacement["zero_based_byte_offset"]
    length = replacement["length"]
    before = replacement["before"].encode("ascii")
    after = replacement["after"].encode("ascii")
    require(len(before) == length and len(after) == length, "replacement length mismatch")
    require(frozen[offset : offset + length] == before, "historical prefix replacement mismatch")
    result = frozen[:offset] + after + frozen[offset + length :]
    require(len(result) == FROZEN_WORKFLOW_BYTES, "reconstructed prefix size mismatch")
    require(sha256_bytes(result) == CURRENT_PREFIX_SHA256, "reconstructed prefix digest mismatch")
    return result


def verify_current(
    repo: Path, transition: dict[str, Any], *, check_full_workflow: bool
) -> dict[str, Any]:
    validate_transition(transition)
    predecessor = transition["predecessor"]
    check_bytes(repo, BASELINE_PATH, BASELINE_BYTES, BASELINE_SHA256)
    check_bytes(
        repo,
        REFERENCE_MANIFEST_PATH,
        REFERENCE_MANIFEST_BYTES,
        REFERENCE_MANIFEST_SHA256,
    )
    frozen = check_bytes(
        repo, FROZEN_WORKFLOW_PATH, FROZEN_WORKFLOW_BYTES, FROZEN_WORKFLOW_SHA256
    )
    require(predecessor["baseline"]["entry_count"] == BASELINE_COUNT, "baseline count drift")
    require(
        predecessor["reference_manifest"]["entry_count"] == REFERENCE_MANIFEST_COUNT,
        "reference manifest count drift",
    )

    baseline = load_baseline(repo)
    retained = 0
    for relative, digest in sorted(baseline.items()):
        if relative in BASELINE_REPLACEMENT_PATHS:
            continue
        data = read_bytes(repo, relative)
        require(sha256_bytes(data) == digest, f"changed retained baseline input:{relative}")
        retained += 1
    require(retained == 47, "wrong checked retained baseline count")
    for record in BASELINE_REPLACEMENTS:
        check_bytes(
            repo,
            record["path"],
            record["successor_bytes"],
            record["successor_sha256"],
        )
    for record in HARNESS_FILES.values():
        check_bytes(repo, record["path"], record["bytes"], record["sha256"])

    suite_dir = repo / "suite/src/prime_hyperelliptic"
    actual_suite = {
        path.relative_to(repo).as_posix()
        for path in suite_dir.glob("*.rs")
        if path.is_file()
    }
    require(actual_suite == REFERENCE_INPUT_PATHS, "wrong successor Rust source file set")
    for relative, size, digest in REFERENCE_INPUTS:
        check_bytes(repo, relative, size, digest)
    aggregate = "".join(
        f"{digest}  {relative}\n"
        for relative, _size, digest in sorted(REFERENCE_INPUTS, key=lambda row: row[0])
    ).encode("ascii")
    require(len(aggregate) == AGGREGATE_MANIFEST_BYTES, "wrong computed manifest size")
    require(
        sha256_bytes(aggregate) == AGGREGATE_MANIFEST_SHA256,
        "wrong computed manifest digest",
    )

    implementation = transition["successor"]["implementation_files"]
    for key, relative in IMPLEMENTATION_PATHS.items():
        record = implementation[key]
        check_bytes(repo, relative, record["bytes"], record["sha256"])

    result = {
        "aggregate_manifest_bytes": len(aggregate),
        "aggregate_manifest_sha256": sha256_bytes(aggregate),
        "harness_files": HARNESS_FILES,
        "reference_input_count": len(REFERENCE_INPUTS),
        "retained_baseline_entry_count": retained,
        "replacement_count": len(BASELINE_REPLACEMENTS),
    }
    if check_full_workflow:
        expected_prefix = reconstructed_prefix(frozen)
        current_workflow = read_bytes(repo, CURRENT_WORKFLOW_PATH)
        require(
            current_workflow.startswith(expected_prefix),
            "undeclared current workflow-prefix drift",
        )
        workflow_record = transition["successor"]["full_workflow"]
        require(
            len(current_workflow) == workflow_record["bytes"],
            "wrong full workflow size",
        )
        require(
            sha256_bytes(current_workflow) == workflow_record["sha256"],
            "wrong full workflow digest",
        )
        result["workflow_prefix_bytes"] = len(expected_prefix)
        result["workflow_prefix_sha256"] = sha256_bytes(expected_prefix)
        result["full_workflow_bytes"] = len(current_workflow)
        result["full_workflow_sha256"] = sha256_bytes(current_workflow)
        result["implementation_files"] = implementation
    return result


def verify_predecessor_identity(head: str, tree: str) -> None:
    require(head == PREDECESSOR_COMMIT, "predecessor checkout HEAD mismatch")
    require(tree == PREDECESSOR_TREE, "predecessor checkout tree mismatch")


def verify_predecessor(predecessor_root: Path) -> dict[str, Any]:
    head = git(predecessor_root, "rev-parse", "HEAD")
    tree = git(predecessor_root, "rev-parse", "HEAD^{tree}")
    verify_predecessor_identity(head, tree)
    require(
        git(predecessor_root, "status", "--porcelain", "--untracked-files=all") == "",
        "predecessor checkout is dirty",
    )
    check_bytes(predecessor_root, BASELINE_PATH, BASELINE_BYTES, BASELINE_SHA256)
    check_bytes(
        predecessor_root,
        REFERENCE_MANIFEST_PATH,
        REFERENCE_MANIFEST_BYTES,
        REFERENCE_MANIFEST_SHA256,
    )
    frozen = check_bytes(
        predecessor_root,
        FROZEN_WORKFLOW_PATH,
        FROZEN_WORKFLOW_BYTES,
        FROZEN_WORKFLOW_SHA256,
    )
    baseline = load_baseline(predecessor_root)
    for relative, digest in sorted(baseline.items()):
        require(
            sha256_bytes(read_bytes(predecessor_root, relative)) == digest,
            f"changed predecessor baseline input:{relative}",
        )
    for record in BASELINE_REPLACEMENTS:
        check_bytes(
            predecessor_root,
            record["path"],
            record["predecessor_bytes"],
            record["predecessor_sha256"],
        )
    historical_workflow = check_bytes(
        predecessor_root,
        CURRENT_WORKFLOW_PATH,
        FROZEN_WORKFLOW_BYTES,
        FROZEN_WORKFLOW_SHA256,
    )
    require(historical_workflow == frozen, "historical workflow snapshot mismatch")
    return {
        "baseline_entry_count": len(baseline),
        "commit": head,
        "tree": tree,
        "workflow_bytes": len(historical_workflow),
        "workflow_sha256": sha256_bytes(historical_workflow),
    }


def copy_current_fixture(repo: Path, destination: Path, transition: dict[str, Any]) -> None:
    paths = set(load_baseline(repo))
    paths.update(REFERENCE_INPUT_PATHS)
    paths.update(
        {
            BASELINE_PATH,
            REFERENCE_MANIFEST_PATH,
            FROZEN_WORKFLOW_PATH,
            CURRENT_WORKFLOW_PATH,
            *(record["path"] for record in HARNESS_FILES.values()),
            *IMPLEMENTATION_PATHS.values(),
        }
    )
    for relative in sorted(paths):
        source = repo / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    validate_transition(transition)


def run_self_test(repo: Path, transition_path: Path) -> None:
    transition = load_json(transition_path)
    verify_current(repo, transition, check_full_workflow=True)
    baseline = load_baseline(repo)
    retained_path = next(
        path for path in sorted(baseline) if path not in BASELINE_REPLACEMENT_PATHS
    )

    with tempfile.TemporaryDirectory(prefix="fp-chain-transition-self-test-") as temp:
        seed = Path(temp) / "seed"
        copy_current_fixture(repo, seed, transition)

        def expect_file_failure(name: str, mutate: Callable[[Path], None], *, full: bool = False) -> None:
            case = Path(temp) / name
            shutil.copytree(seed, case)
            mutate(case)
            try:
                verify_current(case, transition, check_full_workflow=full)
            except VerificationError:
                return
            raise VerificationError(f"self-test unexpectedly accepted:{name}")

        expect_file_failure(
            "retained-change",
            lambda root: (root / retained_path).write_bytes(
                (root / retained_path).read_bytes() + b"self-test"
            ),
        )
        for index, record in enumerate(BASELINE_REPLACEMENTS):
            relative = record["path"]
            expect_file_failure(
                f"missing-replacement-{index}",
                lambda root, relative=relative: (root / relative).unlink(),
            )
            expect_file_failure(
                f"wrong-replacement-{index}",
                lambda root, relative=relative: (root / relative).write_bytes(
                    b"wrong successor input\n"
                ),
            )
        for key, record in HARNESS_FILES.items():
            relative = record["path"]
            expect_file_failure(
                f"missing-harness-{key}",
                lambda root, relative=relative: (root / relative).unlink(),
            )
            expect_file_failure(
                f"wrong-harness-{key}",
                lambda root, relative=relative: (root / relative).write_bytes(
                    b"wrong successor harness input\n"
                ),
            )
        expect_file_failure(
            "unexpected-suite-file",
            lambda root: (
                root / "suite/src/prime_hyperelliptic/unexpected.rs"
            ).write_text("// unexpected\n", encoding="utf-8"),
        )
        expect_file_failure(
            "altered-frozen-artifact",
            lambda root: (root / REFERENCE_MANIFEST_PATH).write_bytes(
                (root / REFERENCE_MANIFEST_PATH).read_bytes() + b"self-test"
            ),
        )

        def drift_prefix(root: Path) -> None:
            path = root / CURRENT_WORKFLOW_PATH
            data = bytearray(path.read_bytes())
            data[100] ^= 1
            path.write_bytes(bytes(data))

        expect_file_failure("workflow-prefix-drift", drift_prefix, full=True)
        for key, relative in IMPLEMENTATION_PATHS.items():
            expect_file_failure(
                f"altered-{key}",
                lambda root, relative=relative: (root / relative).write_bytes(
                    (root / relative).read_bytes() + b"self-test"
                ),
            )
        expect_file_failure(
            "altered-full-workflow",
            lambda root: (root / CURRENT_WORKFLOW_PATH).write_bytes(
                (root / CURRENT_WORKFLOW_PATH).read_bytes() + b"# self-test\n"
            ),
            full=True,
        )

    for name, key, wrong in (
        ("wrong-predecessor-commit", "commit", "0" * 40),
        ("wrong-predecessor-tree", "tree", "1" * 40),
    ):
        altered = json.loads(json.dumps(transition))
        altered["predecessor"][key] = wrong
        try:
            validate_transition(altered)
        except VerificationError:
            continue
        raise VerificationError(f"self-test unexpectedly accepted:{name}")

    for name, head, tree in (
        ("wrong-checkout-head", "0" * 40, PREDECESSOR_TREE),
        ("wrong-checkout-tree", PREDECESSOR_COMMIT, "1" * 40),
    ):
        try:
            verify_predecessor_identity(head, tree)
        except VerificationError:
            continue
        raise VerificationError(f"self-test unexpectedly accepted:{name}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("mode", nargs="?", choices=("current-reference", "full"))
    result.add_argument("--repo", type=Path)
    result.add_argument("--predecessor-root", type=Path)
    result.add_argument("--transition", type=Path)
    result.add_argument("--self-test", action="store_true")
    return result


def main() -> int:
    args = parser().parse_args()
    script = Path(__file__).resolve()
    default_repo = script.parents[2]
    default_transition = (
        script.parent / "evidence/fp-chain-successor-inputs-01/transition.json"
    )
    repo = (args.repo or default_repo).resolve()
    transition_path = (args.transition or default_transition).resolve()
    try:
        if args.self_test:
            require(args.mode is None, "--self-test does not take a mode")
            run_self_test(repo, transition_path)
            print("PASS fp-chain input-transition verifier self-test:22 rejection classes")
            return 0
        require(args.mode is not None, "a verification mode is required")
        transition = load_json(transition_path)
        if args.mode == "current-reference":
            current = verify_current(repo, transition, check_full_workflow=False)
            receipt = {
                "schema": "chained-transfer-current-reference-check/v1",
                "status": "pass",
                "message": "PASS successor reference execution inputs verified",
                "authority": "input custody only; not a replay receipt or scientific certificate",
                "current": current,
            }
        else:
            require(args.predecessor_root is not None, "full mode requires --predecessor-root")
            current = verify_current(repo, transition, check_full_workflow=True)
            predecessor = verify_predecessor(args.predecessor_root.resolve())
            receipt = {
                "schema": "chained-transfer-input-transition-check/v1",
                "status": "pass",
                "authority": "input custody only; successor replay remains required",
                "current": current,
                "current_repository": {
                    "commit": git(repo, "rev-parse", "HEAD"),
                    "tree": git(repo, "rev-parse", "HEAD^{tree}"),
                },
                "predecessor": predecessor,
                "transition": {
                    "bytes": transition_path.stat().st_size,
                    "sha256": sha256_bytes(transition_path.read_bytes()),
                },
                "transition_schema": SCHEMA,
            }
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return 0
    except VerificationError as exc:
        print(f"FAIL fp-chain input transition:{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
