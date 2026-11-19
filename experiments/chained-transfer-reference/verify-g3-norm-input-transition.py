#!/usr/bin/env python3
"""Verify the additive successor input set for the genus-three norm replay.

The historical 437-row manifest and six-job workflow prefix remain immutable.
This verifier accepts only the six declared consumer replacements, checks every
other historical producer and consumer byte, and binds the exact predecessor
checkout.  It is an input-custody verifier, not a replay or theorem receipt.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


SCHEMA = "g3-norm-input-transition/v1"
PREDECESSOR_COMMIT = "069644bf59499e4172eb8bcdce5de8a6665da93f"
PREDECESSOR_TREE = "6eebf810da5a0afd7959e57d16b83c2ca31f910f"
UPSTREAM_COMMIT = "3d49af7f3d0a28e76b79e4825c9d2324e85853d2"
MANIFEST_PATH = (
    "experiments/chained-transfer-reference/g3-norm-reference-01.sha256"
)
MANIFEST_BYTES = 54_565
MANIFEST_SHA256 = "3a05cbaa3cb36f291c327aa0f4d82680900bb11581cc4f194f464d99006f6f0c"
MANIFEST_COUNT = 437
FROZEN_PREFIX_PATH = (
    "experiments/chained-transfer-reference/evidence/"
    "g3-norm-primary-01/six-original-jobs.yml"
)
FROZEN_PREFIX_BYTES = 20_796
FROZEN_PREFIX_SHA256 = (
    "d548374029d8142cbff7b812ff4bd8bc85e99f791edeab88cd9885250c445b60"
)
CURRENT_WORKFLOW_PATH = ".github/workflows/chained-transfer-reference.yml"
CURRENT_PREFIX_MARKER = b"\n\n  g3-canonical-norm:\n"
CURRENT_PREFIX_BYTES = 21_786
CURRENT_PREFIX_SHA256 = (
    "f9a431b4fec25045e3fc30011ea4b8c5d36f3e24d623ee4a08246d8a8e49b3b9"
)
REPLACEMENTS = [
    {
        "path": ".github/workflows/chained-transfer-reference.yml",
        "predecessor_bytes": 25_057,
        "predecessor_sha256": (
            "2de4d8510b610416106df77d97b80f4af68bd681d8a9db0f91b5bfee0cdd3086"
        ),
        "successor_bytes": 27_474,
        "successor_sha256": (
            "4b62af0a920872ae88efe9da4436cc5da49f143c859d2b36f074541ea822655a"
        ),
    },
    {
        "path": "pcc/keyring.json",
        "predecessor_bytes": 335,
        "predecessor_sha256": (
            "ceb7f66f25b10cccf322f23ec9d15fddb0750334e492070d20e1577bd82708ad"
        ),
        "successor_bytes": 473,
        "successor_sha256": (
            "a78a1c946de0b683d28dfd7257f7e350fcf39349aca4f46dd84abb46ae04909d"
        ),
    },
    {
        "path": "tools/lean/current-corpus-gate.py",
        "predecessor_bytes": 64_743,
        "predecessor_sha256": (
            "2e06576d5ff960b2d685e7b0cc6aafbac41338ac39cbc17c766a72555b088bf6"
        ),
        "successor_bytes": 73_416,
        "successor_sha256": (
            "e3431f0d7a27e6b0d883390a85343f4bf439fc7519f8b89b6f3407f561c2379f"
        ),
    },
    {
        "path": "tools/lean/test_current_corpus_gate.py",
        "predecessor_bytes": 55_102,
        "predecessor_sha256": (
            "a2087bb7c56264ff46bca3f033e4f21e1d2ad800d19a0c1987f0c25238090800"
        ),
        "successor_bytes": 59_940,
        "successor_sha256": (
            "4302066973b280afe04cfbf49a7fbc1d8a87bad4f1b7ae84776bc54823bb40d5"
        ),
    },
    {
        "path": "tools/pcc/pcc.py",
        "predecessor_bytes": 90_004,
        "predecessor_sha256": (
            "04440683f8a2a3a6e9bbee070df37643e20c4c40b2e075cede866df4301bb5b0"
        ),
        "successor_bytes": 100_142,
        "successor_sha256": (
            "acfd841b13c21db3f1d1a89d2bd7339a3faf8a2a63dc3cac623ef55a03b1444a"
        ),
    },
    {
        "path": "tools/pcc/test_pcc.py",
        "predecessor_bytes": 18_003,
        "predecessor_sha256": (
            "df8904ceea914b1755c3596b72dd51fd4783c0852b10533a703e3037a9a0dd40"
        ),
        "successor_bytes": 25_430,
        "successor_sha256": (
            "7b6a96f8539b5b2e6c5f92ae09b61728d24b1e2e712a5200fb41b0765c4c5e4e"
        ),
    },
]
REPLACEMENT_BY_PATH = {row["path"]: row for row in REPLACEMENTS}
DRIVER_PATH = (
    "experiments/chained-transfer-reference/check-g3-norm-successor.sh"
)
DRIVER_BYTES = 7_803
DRIVER_SHA256 = "7ac0e9892f1e08c399ab5431716cd13628c2f74f8330db41ea1766ecb5618d9a"
VERIFIER_PATH = (
    "experiments/chained-transfer-reference/verify-g3-norm-input-transition.py"
)
FROZEN_DRIVER_PATH = "experiments/chained-transfer-reference/check-g3-norm.sh"
REPLAY_BODY_START = b"run_logged() {\n"
FROZEN_REPLAY_BODY_END = b"printf 'G3 norm replay complete:"
SUCCESSOR_REPLAY_BODY_END = b"printf 'G3 norm successor replay complete:"
REPLAY_BODY_BYTES = 2_576
REPLAY_BODY_SHA256 = "63afb094e0e0f3700046e0e2798e682f73957ab399ea5a1f457881a1cb7c27fc"


class VerificationError(RuntimeError):
    """A deterministic custody condition failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check_file(root: Path, relative: str, size: int, expected: str) -> bytes:
    path = root / relative
    require(path.is_file(), f"missing required file:{relative}")
    data = path.read_bytes()
    require(len(data) == size, f"wrong byte count:{relative}")
    require(digest(data) == expected, f"wrong sha256:{relative}")
    return data


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


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot load transition:{path}:{exc}") from exc
    require(isinstance(value, dict), "transition root is not an object")
    return value


def validate_record(value: dict[str, Any]) -> None:
    require(value.get("schema") == SCHEMA, "wrong transition schema")
    require(
        value.get("record_state") == "declared_successor_inputs",
        "wrong transition state",
    )
    require(
        value.get("authority")
        == "input declaration; not a replay receipt or scientific certificate",
        "wrong transition authority",
    )
    predecessor = value.get("predecessor")
    require(isinstance(predecessor, dict), "missing predecessor")
    require(
        predecessor.get("repository") == "aburan28/cryptanalysis",
        "wrong predecessor repository",
    )
    require(predecessor.get("commit") == PREDECESSOR_COMMIT, "wrong predecessor commit")
    require(predecessor.get("tree") == PREDECESSOR_TREE, "wrong predecessor tree")
    require(
        predecessor.get("manifest")
        == {
            "path": MANIFEST_PATH,
            "bytes": MANIFEST_BYTES,
            "sha256": MANIFEST_SHA256,
            "entry_count": MANIFEST_COUNT,
        },
        "wrong predecessor manifest record",
    )
    require(
        predecessor.get("workflow_prefix")
        == {
            "path": FROZEN_PREFIX_PATH,
            "bytes": FROZEN_PREFIX_BYTES,
            "sha256": FROZEN_PREFIX_SHA256,
        },
        "wrong frozen workflow-prefix record",
    )
    successor = value.get("successor")
    require(isinstance(successor, dict), "missing successor")
    require(successor.get("retained_manifest_entry_count") == 431, "wrong retained count")
    require(successor.get("replaced_manifest_entries") == REPLACEMENTS, "wrong replacements")
    require(
        successor.get("workflow_prefix")
        == {
            "boundary": "all bytes before the g3-canonical-norm job",
            "bytes": CURRENT_PREFIX_BYTES,
            "sha256": CURRENT_PREFIX_SHA256,
            "lineage_commits": [
                "9468130a586f5c70d2a25a19872d8f1c178f3e42",
                "84628f6a93438f1544050815cd46999f07592a78",
                "46e0d4e800983dcb6527c59b0c537d2ac7300345",
            ],
        },
        "wrong successor workflow-prefix record",
    )
    require(
        successor.get("unchanged_arithmetic_replay_body")
        == {
            "predecessor_path": FROZEN_DRIVER_PATH,
            "successor_path": DRIVER_PATH,
            "start_marker": "run_logged() {\\n",
            "predecessor_end_marker": "printf 'G3 norm replay complete:",
            "successor_end_marker": "printf 'G3 norm successor replay complete:",
            "bytes": REPLAY_BODY_BYTES,
            "sha256": REPLAY_BODY_SHA256,
        },
        "wrong unchanged arithmetic-body record",
    )
    implementation = successor.get("implementation_files")
    require(isinstance(implementation, dict), "missing implementation records")
    require(
        implementation.get("driver")
        == {"path": DRIVER_PATH, "bytes": DRIVER_BYTES, "sha256": DRIVER_SHA256},
        "wrong driver record",
    )
    verifier = implementation.get("verifier")
    require(isinstance(verifier, dict), "missing verifier record")
    require(verifier.get("path") == VERIFIER_PATH, "wrong verifier path")
    require(isinstance(verifier.get("bytes"), int) and verifier["bytes"] > 0, "bad verifier size")
    require(
        isinstance(verifier.get("sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", verifier["sha256"]) is not None,
        "bad verifier digest",
    )
    require(
        value.get("claims")
        == {
            "historical_inputs_verified": True,
            "historical_run_reexecuted": False,
            "successor_replay_required": True,
            "mathematical_claim_changed": False,
        },
        "wrong claim boundaries",
    )


def parse_manifest(data: bytes) -> dict[str, str]:
    try:
        lines = data.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise VerificationError("manifest is not ASCII") from exc
    require(len(lines) == MANIFEST_COUNT, "wrong manifest row count")
    rows: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\x00\r\n]+)", line)
        require(match is not None, "malformed manifest row")
        expected, path = match.groups()
        require(path not in rows, f"duplicate manifest path:{path}")
        require(not Path(path).is_absolute(), f"absolute manifest path:{path}")
        rows[path] = expected
    require(set(REPLACEMENT_BY_PATH) <= set(rows), "replacement missing from manifest")
    for path, row in REPLACEMENT_BY_PATH.items():
        require(rows[path] == row["predecessor_sha256"], f"wrong old digest:{path}")
    return rows


def verify_immutable(root: Path) -> dict[str, str]:
    manifest = check_file(root, MANIFEST_PATH, MANIFEST_BYTES, MANIFEST_SHA256)
    check_file(root, FROZEN_PREFIX_PATH, FROZEN_PREFIX_BYTES, FROZEN_PREFIX_SHA256)
    return parse_manifest(manifest)


def verify_predecessor(root: Path) -> None:
    require(git(root, "rev-parse", "HEAD^{tree}") == PREDECESSOR_TREE, "predecessor tree mismatch")
    require(git(root, "rev-parse", "HEAD") == PREDECESSOR_COMMIT, "predecessor HEAD mismatch")
    require(
        git(root, "status", "--porcelain", "--untracked-files=all") == "",
        "dirty predecessor checkout",
    )
    verify_immutable(root)
    for row in REPLACEMENTS:
        check_file(
            root,
            row["path"],
            row["predecessor_bytes"],
            row["predecessor_sha256"],
        )


def verify_current(repo: Path, upstream: Path, transition: dict[str, Any]) -> None:
    require(git(upstream, "rev-parse", "HEAD") == UPSTREAM_COMMIT, "producer HEAD mismatch")
    rows = verify_immutable(repo)
    workflow_path = repo / CURRENT_WORKFLOW_PATH
    require(workflow_path.is_file(), "missing successor workflow")
    workflow = workflow_path.read_bytes()
    require(
        len(workflow) == REPLACEMENT_BY_PATH[CURRENT_WORKFLOW_PATH]["successor_bytes"],
        "wrong successor workflow size",
    )
    require(workflow.count(CURRENT_PREFIX_MARKER) == 1, "ambiguous G3 workflow boundary")
    prefix = workflow[: workflow.index(CURRENT_PREFIX_MARKER) + 2]
    require(len(prefix) == CURRENT_PREFIX_BYTES, "wrong successor six-job prefix size")
    require(digest(prefix) == CURRENT_PREFIX_SHA256, "wrong successor six-job prefix digest")
    require(
        digest(workflow) == REPLACEMENT_BY_PATH[CURRENT_WORKFLOW_PATH]["successor_sha256"],
        "wrong successor workflow digest",
    )
    for row in REPLACEMENTS:
        check_file(repo, row["path"], row["successor_bytes"], row["successor_sha256"])
    implementation = transition["successor"]["implementation_files"]
    for record in implementation.values():
        check_file(repo, record["path"], record["bytes"], record["sha256"])
    frozen_driver = (repo / FROZEN_DRIVER_PATH).read_bytes()
    successor_driver = (repo / DRIVER_PATH).read_bytes()
    require(frozen_driver.count(REPLAY_BODY_START) == 1, "ambiguous frozen replay-body start")
    require(successor_driver.count(REPLAY_BODY_START) == 1, "ambiguous successor replay-body start")
    require(frozen_driver.count(FROZEN_REPLAY_BODY_END) == 1, "ambiguous frozen replay-body end")
    require(successor_driver.count(SUCCESSOR_REPLAY_BODY_END) == 1, "ambiguous successor replay-body end")
    frozen_body = frozen_driver[
        frozen_driver.index(REPLAY_BODY_START) : frozen_driver.index(FROZEN_REPLAY_BODY_END)
    ]
    successor_body = successor_driver[
        successor_driver.index(REPLAY_BODY_START) : successor_driver.index(SUCCESSOR_REPLAY_BODY_END)
    ]
    require(frozen_body == successor_body, "arithmetic replay body changed")
    require(len(successor_body) == REPLAY_BODY_BYTES, "wrong arithmetic replay-body size")
    require(digest(successor_body) == REPLAY_BODY_SHA256, "wrong arithmetic replay-body digest")
    for path, expected in rows.items():
        if path in REPLACEMENT_BY_PATH:
            continue
        if path.startswith("../crypto/"):
            target = upstream / path.removeprefix("../crypto/")
        else:
            require(".." not in Path(path).parts, f"escaping consumer path:{path}")
            target = repo / path
        require(target.is_file(), f"missing manifest input:{path}")
        require(digest(target.read_bytes()) == expected, f"undeclared manifest drift:{path}")


def run_process(
    args: list[str],
    *,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
) -> str:
    try:
        result = subprocess.run(
            args,
            check=True,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise VerificationError(f"self-test command failed:{' '.join(args)}") from exc
    return result.stdout.strip()


def link_file(root: Path, relative: str, source: Path) -> None:
    require(source.is_file(), f"self-test source missing:{source}")
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() and not target.is_symlink():
        target.symlink_to(source.resolve())


def replace_with_mutation(path: Path, offset: int = 0) -> tuple[Path, str]:
    source = path.resolve()
    original = path.read_bytes()
    data = bytearray(original)
    require(bool(data), f"cannot mutate empty self-test file:{path}")
    require(0 <= offset < len(data), f"mutation offset outside file:{path}")
    path.unlink()
    require(not path.exists() and not path.is_symlink(), f"failed to detach fixture link:{path}")
    data[offset] ^= 1
    path.write_bytes(data)
    require(digest(source.read_bytes()) == digest(original), f"mutation touched source:{source}")
    return source, digest(original)


def restore_link(path: Path, source: Path, original_digest: str) -> None:
    path.unlink()
    path.symlink_to(source)
    require(digest(source.read_bytes()) == original_digest, f"source changed after restore:{source}")


def expect_rejection(label: str, action: Callable[[], None]) -> None:
    try:
        action()
    except VerificationError:
        return
    raise VerificationError(f"filesystem self-test accepted mutation:{label}")


def current_filesystem_selftest(
    value: dict[str, Any], repo: Path, upstream: Path, temporary: Path
) -> int:
    rows = verify_immutable(repo)
    current_fixture = temporary / "current"
    current_fixture.mkdir()
    producer_fixture = temporary / "producer"
    run_process(
        [
            "git",
            "clone",
            "--quiet",
            "--shared",
            "--no-checkout",
            str(upstream),
            str(producer_fixture),
        ]
    )
    run_process(
        [
            "git",
            "-C",
            str(producer_fixture),
            "update-ref",
            "refs/heads/g3-selftest",
            UPSTREAM_COMMIT,
        ]
    )
    run_process(
        [
            "git",
            "-C",
            str(producer_fixture),
            "symbolic-ref",
            "HEAD",
            "refs/heads/g3-selftest",
        ]
    )
    consumer_paths = {
        MANIFEST_PATH,
        FROZEN_PREFIX_PATH,
        FROZEN_DRIVER_PATH,
        DRIVER_PATH,
        VERIFIER_PATH,
        *REPLACEMENT_BY_PATH,
    }
    consumer_paths.update(path for path in rows if not path.startswith("../crypto/"))
    producer_paths = {
        path.removeprefix("../crypto/")
        for path in rows
        if path.startswith("../crypto/")
    }
    for path in sorted(consumer_paths):
        link_file(current_fixture, path, repo / path)
    for path in sorted(producer_paths):
        link_file(producer_fixture, path, upstream / path)
    verify_current(current_fixture, producer_fixture, value)

    rejected = 0
    mutations = [
        (
            "retained-consumer-byte",
            current_fixture / "experiments/chained-transfer-reference/G3_NORM_DERIVATION.md",
            0,
        ),
        (
            "retained-producer-byte",
            producer_fixture / "src/cryptanalysis/diem_quartic.rs",
            0,
        ),
        ("declared-replacement-byte", current_fixture / "pcc/keyring.json", 0),
        ("workflow-prefix-byte", current_fixture / CURRENT_WORKFLOW_PATH, 100),
        (
            "workflow-full-byte",
            current_fixture / CURRENT_WORKFLOW_PATH,
            CURRENT_PREFIX_BYTES + 100,
        ),
    ]
    source_digests: dict[Path, str] = {}
    for label, path, offset in mutations:
        source, original_digest = replace_with_mutation(path, offset)
        source_digests[source] = original_digest
        expect_rejection(
            label,
            lambda: verify_current(current_fixture, producer_fixture, value),
        )
        rejected += 1
        restore_link(path, source, original_digest)
    verify_current(current_fixture, producer_fixture, value)
    for source, expected in source_digests.items():
        require(digest(source.read_bytes()) == expected, f"self-test changed source:{source}")
    return rejected


def predecessor_filesystem_selftest(predecessor: Path, temporary: Path) -> int:
    predecessor_fixture = temporary / "predecessor"
    run_process(
        [
            "git",
            "clone",
            "--quiet",
            "--shared",
            "--no-checkout",
            str(predecessor),
            str(predecessor_fixture),
        ]
    )
    predecessor_paths = [
        MANIFEST_PATH,
        FROZEN_PREFIX_PATH,
        *REPLACEMENT_BY_PATH,
        "experiments/chained-transfer-reference/G3_NORM_REPLAY_PROTOCOL.md",
    ]
    run_process(
        [
            "git",
            "-C",
            str(predecessor_fixture),
            "sparse-checkout",
            "set",
            "--no-cone",
            *predecessor_paths,
        ]
    )
    run_process(
        [
            "git",
            "-C",
            str(predecessor_fixture),
            "checkout",
            "--quiet",
            "--detach",
            PREDECESSOR_COMMIT,
        ]
    )
    verify_predecessor(predecessor_fixture)
    rejected = 0

    parent = git(predecessor_fixture, "rev-parse", f"{PREDECESSOR_COMMIT}^")
    run_process(["git", "-C", str(predecessor_fixture), "update-ref", "HEAD", parent])
    expect_rejection("predecessor-wrong-tree", lambda: verify_predecessor(predecessor_fixture))
    rejected += 1
    run_process(
        ["git", "-C", str(predecessor_fixture), "update-ref", "HEAD", PREDECESSOR_COMMIT]
    )

    commit_env = os.environ.copy()
    commit_env.update(
        {
            "GIT_AUTHOR_NAME": "G3 self-test",
            "GIT_AUTHOR_EMAIL": "g3-selftest.invalid",
            "GIT_COMMITTER_NAME": "G3 self-test",
            "GIT_COMMITTER_EMAIL": "g3-selftest.invalid",
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
        }
    )
    same_tree_commit = run_process(
        ["git", "-C", str(predecessor_fixture), "commit-tree", PREDECESSOR_TREE],
        input_text="G3 input-transition self-test\n",
        env=commit_env,
    )
    run_process(
        ["git", "-C", str(predecessor_fixture), "update-ref", "HEAD", same_tree_commit]
    )
    expect_rejection("predecessor-wrong-head", lambda: verify_predecessor(predecessor_fixture))
    rejected += 1
    run_process(
        ["git", "-C", str(predecessor_fixture), "update-ref", "HEAD", PREDECESSOR_COMMIT]
    )

    dirty_path = predecessor_fixture / "pcc/keyring.json"
    dirty_path.write_bytes(dirty_path.read_bytes() + b"\n")
    expect_rejection("predecessor-dirty-custody", lambda: verify_predecessor(predecessor_fixture))
    rejected += 1
    run_process(
        ["git", "-C", str(predecessor_fixture), "checkout", "--", "pcc/keyring.json"]
    )

    unrelated_relative = "experiments/chained-transfer-reference/G3_NORM_REPLAY_PROTOCOL.md"
    unrelated_tracked = predecessor_fixture / unrelated_relative
    unrelated_tracked.write_bytes(unrelated_tracked.read_bytes() + b"\n")
    expect_rejection(
        "predecessor-unrelated-modified",
        lambda: verify_predecessor(predecessor_fixture),
    )
    rejected += 1
    run_process(
        ["git", "-C", str(predecessor_fixture), "checkout", "--", unrelated_relative]
    )

    unrelated_untracked = predecessor_fixture / "unrelated-g3-selftest.tmp"
    unrelated_untracked.write_bytes(b"untracked\n")
    expect_rejection(
        "predecessor-unrelated-untracked",
        lambda: verify_predecessor(predecessor_fixture),
    )
    rejected += 1
    unrelated_untracked.unlink()
    verify_predecessor(predecessor_fixture)
    return rejected


def selftest(
    value: dict[str, Any], repo: Path, upstream: Path, predecessor: Path
) -> tuple[int, int]:
    mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("schema", lambda x: x.__setitem__("schema", "bad")),
        ("authority", lambda x: x.__setitem__("authority", "replay receipt")),
        ("commit", lambda x: x["predecessor"].__setitem__("commit", "0" * 40)),
        ("tree", lambda x: x["predecessor"].__setitem__("tree", "0" * 40)),
        ("manifest", lambda x: x["predecessor"]["manifest"].__setitem__("sha256", "0" * 64)),
        ("frozen-prefix", lambda x: x["predecessor"]["workflow_prefix"].__setitem__("bytes", 0)),
        ("retained", lambda x: x["successor"].__setitem__("retained_manifest_entry_count", 432)),
        ("remove-replacement", lambda x: x["successor"]["replaced_manifest_entries"].pop()),
        ("replacement-digest", lambda x: x["successor"]["replaced_manifest_entries"][0].__setitem__("successor_sha256", "0" * 64)),
        ("successor-prefix", lambda x: x["successor"]["workflow_prefix"].__setitem__("sha256", "0" * 64)),
        ("arithmetic-body", lambda x: x["successor"]["unchanged_arithmetic_replay_body"].__setitem__("sha256", "0" * 64)),
        ("driver", lambda x: x["successor"]["implementation_files"]["driver"].__setitem__("bytes", 0)),
        ("verifier", lambda x: x["successor"]["implementation_files"]["verifier"].__setitem__("sha256", "bad")),
        ("replay-claim", lambda x: x["claims"].__setitem__("historical_run_reexecuted", True)),
        ("math-claim", lambda x: x["claims"].__setitem__("mathematical_claim_changed", True)),
    ]
    validate_record(value)
    rejected = 0
    for name, mutate in mutations:
        candidate = copy.deepcopy(value)
        mutate(candidate)
        try:
            validate_record(candidate)
        except VerificationError:
            rejected += 1
        else:
            raise VerificationError(f"self-test accepted mutation:{name}")
    with tempfile.TemporaryDirectory(prefix="g3-norm-input-selftest-") as raw_tmp:
        temporary = Path(raw_tmp)
        filesystem_rejected = current_filesystem_selftest(
            value, repo, upstream, temporary
        )
        filesystem_rejected += predecessor_filesystem_selftest(
            predecessor, temporary
        )
    print(
        json.dumps(
            {
                "schema": "g3-norm-input-transition-selftest/v1",
                "record_mutations_rejected": rejected,
                "filesystem_mutations_rejected": filesystem_rejected,
                "rejected": rejected + filesystem_rejected,
            },
            sort_keys=True,
        )
    )
    return rejected, filesystem_rejected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("current", "predecessor", "full", "selftest"))
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--upstream-root", type=Path)
    parser.add_argument("--predecessor-root", type=Path)
    parser.add_argument("--transition", required=True, type=Path)
    args = parser.parse_args()
    value = load_json(args.transition)
    validate_record(value)
    if args.mode == "selftest":
        require(
            args.repo is not None
            and args.upstream_root is not None
            and args.predecessor_root is not None,
            "all three roots required for self-test",
        )
        selftest(
            value,
            args.repo.resolve(),
            args.upstream_root.resolve(),
            args.predecessor_root.resolve(),
        )
        return 0
    if args.mode in ("current", "full"):
        require(args.repo is not None and args.upstream_root is not None, "current roots required")
        verify_current(args.repo.resolve(), args.upstream_root.resolve(), value)
    if args.mode in ("predecessor", "full"):
        require(args.predecessor_root is not None, "predecessor root required")
        verify_predecessor(args.predecessor_root.resolve())
    print(
        json.dumps(
            {
                "schema": "g3-norm-input-transition-verification/v1",
                "mode": args.mode,
                "manifest_entries": MANIFEST_COUNT,
                "retained_entries": 431,
                "replaced_entries": len(REPLACEMENTS),
                "status": "pass",
                "authority": "input custody only; no replay or theorem claim",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        print(f"G3 input-transition verification failed:{exc}", file=sys.stderr)
        raise SystemExit(1)
