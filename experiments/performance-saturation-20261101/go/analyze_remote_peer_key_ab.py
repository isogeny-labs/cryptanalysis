#!/usr/bin/env python3
"""Preregistered deterministic analysis for the fixed-peer-key Go A/B study.

The interval calculation enumerates the exact empirical paired-bootstrap
median distribution.  It uses no pseudo-random generator or Monte Carlo draw.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from pathlib import PurePosixPath
import re
import subprocess
import sys
from typing import Any


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
shared: Any = None
campaign_core: Any = None
l2_core: Any = None
export_core: Any = None


SCHEMA = "go-coordinator-peer-key-ab-aa-analysis/2"
BASELINE_ARM = "go-baseline"
CANDIDATE_ARM = "go-candidate"
AA_LEFT_ARM = "go-baseline-aa-left"
AA_RIGHT_ARM = "go-baseline-aa-right"
EXPECTED_ARMS = (BASELINE_ARM, CANDIDATE_ARM, AA_LEFT_ARM, AA_RIGHT_ARM)
EXPECTED_BINARY_FILES = {
    BASELINE_ARM: "coord-baseline.test",
    CANDIDATE_ARM: "coord-candidate.test",
    AA_LEFT_ARM: "coord-baseline-aa-left.test",
    AA_RIGHT_ARM: "coord-baseline-aa-right.test",
}
ORDER_CYCLE = (
    (BASELINE_ARM, CANDIDATE_ARM, AA_LEFT_ARM, AA_RIGHT_ARM),
    (CANDIDATE_ARM, BASELINE_ARM, AA_RIGHT_ARM, AA_LEFT_ARM),
    (AA_LEFT_ARM, AA_RIGHT_ARM, BASELINE_ARM, CANDIDATE_ARM),
    (AA_RIGHT_ARM, AA_LEFT_ARM, CANDIDATE_ARM, BASELINE_ARM),
)
EXPECTED_ROWS = 552
EXPECTED_WARMUPS = 72
EXPECTED_MEASURED = 480
EXPECTED_AB_PAIRS = 120
EXPECTED_AA_PAIRS = 120
EXPECTED_CORRECTNESS_CELLS = 138
EXPECTED_REPLICATES = 20
ALLOCATION_THRESHOLD = Fraction(1, 20)
TIMING_THRESHOLD = Fraction(21, 20)
LOWER_QUANTILE = Fraction(1, 960)
UPPER_QUANTILE = Fraction(959, 960)
AA_EQUIVALENCE = Fraction(21, 20)
EXPECTED_SOURCE_IDENTITIES = {
    "baseline_commit": "7c712913b7e912494e87c35e854cfd0129bad89c",
    "baseline_tree": "735e671e9492fb890a4e87825644c46bace88e4a",
    "baseline_coord_blob": "0d3f53806361e7442bc1d108c16b8b847f029918",
    "benchmark_commit": "050af6a5edbaccee4028574492597049a06cfd83",
    "benchmark_blob": "650f6a4a953d5adef537ce87aa3e114b432f32d7",
    "candidate_commit": "37b96362a53a7364dd4cc2a18f450a3627ec08d3",
    "candidate_parent": "7c712913b7e912494e87c35e854cfd0129bad89c",
    "candidate_tree": "5a2653198b943e93c9f7ae7906ad39d74baf7a79",
    "candidate_coord_blob": "edba225c5a1ff613d71a21aa8d2c528096831b6f",
    "candidate_merge_base": "7c712913b7e912494e87c35e854cfd0129bad89c",
}
EXPECTED_BENCHMARK_SHA256 = (
    "b13eafcc112ada81b104c3fde3ad51a75cb80e9a051f9644a66fc27d30218dbd"
)
EXPECTED_DIFF_SHA256 = (
    "e29818ed168eaa886dfdc4be3c90777b1026b89246b760fd76d31614f33e8417"
)
EXPECTED_COMMON_TEST = {
    "common_test_commit": "37b96362a53a7364dd4cc2a18f450a3627ec08d3",
    "common_test_blob": "b487d974638f5fe81a2921fa002b8ce481b956ad",
    "common_test_sha256": "4bf65f9fa27f46e04d287e8fc49ce33d00e9fb74e176a25677b04d9f883e35b8",
    "common_test_path": "bindings/go/coord_test.go",
}
EXPECTED_CPU_GUARD = {
    "flavor": "cpu3c",
    "no_gpu": True,
    "provider_memory_value": 64,
    "vcpu_count": 32,
}
EXPECTED_MEMORY_BYTES = 64_000_000_000
STABLE_PLACEMENT_SCHEMA = "go-cpu-placement-identity/v1"
STABLE_TOPOLOGY_FIELDS = (
    "cpu", "package", "die", "numa", "core", "thread_siblings",
)
GO_ARCHIVE = "go1.27.3.linux-amd64.tar.gz"
GO_ARCHIVE_BYTES = 70_588_678
GO_ARCHIVE_SHA256 = "65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40"
PROTOCOL_TOOL_SHA256 = "0f46a2b856bb1df2d155c4a676b46c6118d82c45cf8e5cc0492315aeb45c84e4"
PROTOCOL_SCHEMA_SHA256 = "a9b948f2be323f862b98301eb7a5aa147ecc29db35041737f0aa3dfd03ad2443"
EXPORT_SCHEMA_SHA256 = "108f0ae9c1be3ed141bca3c22216eba049f2c76677f11013109a4740f19bd757"
EXPECTED_PROTOCOL_ID = "GO-COORD-PEER-KEY-20261101-REMOTE-AB-AA-V9"
EXPECTED_PROTOCOL_VERSION = 9
EXPECTED_PROTOCOL_PATH = "experiments/performance-saturation-20261101/go/protocol.v9.json"
EXPECTED_SOURCE_ORIGIN = "https://github.com/isogeny-labs/cryptanalysis.git"
EXPECTED_SOURCE_REF = "refs/heads/codex/go-peer-key-ab-aa-v9-20261101"
EXPECTED_STARTUP_SHA256 = "15d32b2c8eb6e004b3b4fbb60c6be0bbd88486561dc373cca7140b3e8286ec9b"
PROTOCOL_HASH_TOKEN = "V9_CANONICAL_SHA256_FROM_FREEZE"
EXPECTED_OUTPUT = "go-peer-key-ab-aa-v9-run"
EXPECTED_COMMAND_TEMPLATE = (
    "python3 experiments/performance-saturation-20261101/go/run_remote_peer_key_ab.py "
    "--mode combined --phase fixed-peer-key-ab-aa-v9 --out go-peer-key-ab-aa-v9-run "
    "--protocol-sha256 V9_CANONICAL_SHA256_FROM_FREEZE --expected-cpus 32 "
    "--expected-memory-bytes 64000000000 --expected-cpu-flavor cpu3c"
)
EXPECTED_REQUEST_ENVIRONMENT_KEYS = [
    "POD_BOOT_B64",
    "POD_MAX_SECONDS",
    "RUNPOD_BATCH_BOOTSTRAP_B64",
    "RUNPOD_BATCH_CHUNK_BYTES",
    "RUNPOD_BATCH_COMMAND_B64",
    "RUNPOD_BATCH_COMMAND_SHA256",
    "RUNPOD_BATCH_JOB_ID",
    "RUNPOD_BATCH_MAX_RESULT_BYTES",
    "RUNPOD_BATCH_OUTPUTS_B64",
    "RUNPOD_BATCH_OWNERSHIP_ID",
    "RUNPOD_BATCH_PORT",
    "RUNPOD_BATCH_SOURCE_ARCHIVE_SHA256",
    "RUNPOD_BATCH_SOURCE_COMMIT",
    "RUNPOD_BATCH_SOURCE_REF",
    "RUNPOD_BATCH_SOURCE_TREE",
    "RUNPOD_BATCH_SOURCE_URL",
    "RUNPOD_BATCH_TIMEOUT_SECONDS",
    "RUNPOD_BATCH_TOKEN",
]
EXPECTED_CASES = [
    "BenchmarkStateVersionVector/log_1024",
    "BenchmarkStateVersionVector/log_8192",
    "BenchmarkStateDeltaSinceCaughtUp/log_1024",
    "BenchmarkStateDeltaSinceCaughtUp/log_8192",
    "BenchmarkStateDeltaSinceOneBehind/log_1024",
    "BenchmarkStateDeltaSinceOneBehind/log_8192",
]
EXPECTED_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "TZ": "UTC",
    "GOMAXPROCS": "1",
    "CGO_ENABLED": "1",
}
EXPECTED_ENVIRONMENT_SHA256 = hashlib.sha256(
    json.dumps(EXPECTED_ENVIRONMENT, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
EXPECTED_BUILD_ENVIRONMENT_FIXED = {
    "PATH": "/usr/bin:/bin",
    "LANG": "C",
    "LC_ALL": "C",
    "TZ": "UTC",
    "CGO_ENABLED": "1",
    "CGO_CFLAGS": "-O2 -g",
    "CGO_CPPFLAGS": "",
    "CGO_CXXFLAGS": "-O2 -g",
    "CGO_FFLAGS": "-O2 -g",
    "CGO_LDFLAGS": "-O2 -g",
    "GO111MODULE": "on",
    "GOENV": "off",
    "GOEXPERIMENT": "",
    "GOWORK": "off",
    "GOTOOLCHAIN": "local",
    "GOFLAGS": "-buildvcs=false -mod=readonly",
    "GOMAXPROCS": "1",
    "GOOS": "linux",
    "GOARCH": "amd64",
    "GOAMD64": "v1",
    "GOPROXY": "https://proxy.golang.org",
    "GOSUMDB": "sum.golang.org",
    "GONOSUMDB": "",
    "GONOPROXY": "",
    "GOPRIVATE": "",
    "GOVCS": "*:off",
    "CC": "/usr/bin/gcc",
    "CXX": "/usr/bin/g++",
    "AR": "/usr/bin/ar",
}
EXPECTED_BUILD_DYNAMIC_PATHS = {
    "HOME": "go-home",
    "TMPDIR": "tmp",
    "GOROOT": "toolchain/go",
    "GOPATH": "gopath",
    "GOCACHE": "gocache",
    "GOMODCACHE": "gomodcache",
}
EXPECTED_AFFINITY_POLICY = (
    "require exactly 32 distinct allowed CPU ids; order by "
    "(package,die,numa,core,cpu), with missing topology sorting last; choose the first "
    "ordered CPU whose complete thread_siblings set is allowed, excludes CPU0, and "
    "leaves at least one housekeeping CPU; reserve that complete SMT sibling set"
)


def raw_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json_file(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def checked_command(argv: list[str], *, cwd: Path | None = None) -> str:
    result = subprocess.run(
        argv,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"verification command failed: {' '.join(argv[:3])}\n{result.stdout}")
    return result.stdout.strip()


def verify_freeze_fields(protocol: dict[str, Any], canonical_hash: str) -> None:
    freeze = protocol.get("freeze", {})
    if (
        freeze.get("status") != "frozen"
        or freeze.get("protocol_sha256") != canonical_hash
        or freeze.get("filed_before_affected_data") is not True
        or re.fullmatch(r"[0-9a-f]{40}", str(freeze.get("commit", ""))) is None
    ):
        raise ValueError("canonical protocol freeze identity mismatch")


def verify_frozen_protocol(
    protocol_path: Path,
    protocol: dict[str, Any],
    tool_path: Path,
) -> dict[str, Any]:
    """Validate canonical bytes and the registration-to-freeze identity chain.

    This function deliberately has no protocol-selected imports.  It is the
    root of trust for every dependency loaded later.
    """

    tool_path = tool_path.resolve()
    schema_dir = tool_path.parents[1] / "schemas"
    protocol_schema = schema_dir / "experiment-protocol.v1.json"
    export_schema = schema_dir / "experiment-export.v1.json"
    if raw_sha256(tool_path) != PROTOCOL_TOOL_SHA256:
        raise ValueError("canonical protocol tool SHA-256 mismatch")
    if raw_sha256(protocol_schema) != PROTOCOL_SCHEMA_SHA256:
        raise ValueError("canonical protocol schema SHA-256 mismatch")
    if raw_sha256(export_schema) != EXPORT_SCHEMA_SHA256:
        raise ValueError("canonical export schema SHA-256 mismatch")
    links = protocol.get("links", {})
    expected_tool_links = {
        "protocol_validator_sha256": PROTOCOL_TOOL_SHA256,
        "protocol_schema_sha256": PROTOCOL_SCHEMA_SHA256,
        "export_validator_sha256": PROTOCOL_TOOL_SHA256,
        "export_schema_sha256": EXPORT_SCHEMA_SHA256,
    }
    for key, value in expected_tool_links.items():
        if links.get(key) != value:
            raise ValueError(f"protocol canonical-tool binding mismatch: {key}")
    if (
        protocol.get("protocol_id") != EXPECTED_PROTOCOL_ID
        or protocol.get("version") != EXPECTED_PROTOCOL_VERSION
        or protocol_path != REPO / EXPECTED_PROTOCOL_PATH
    ):
        raise ValueError("unexpected protocol identity or path")
    checked_command([sys.executable, str(tool_path), "validate", str(protocol_path)])
    canonical_hash = checked_command(
        [sys.executable, str(tool_path), "hash", str(protocol_path)]
    )
    verify_freeze_fields(protocol, canonical_hash)
    freeze = protocol["freeze"]

    registration = freeze["commit"]
    relative = protocol_path.relative_to(REPO).as_posix()
    registered_text = checked_command(
        ["git", "show", f"{registration}:{relative}"], cwd=REPO
    )
    registered = json.loads(registered_text)
    if not isinstance(registered, dict):
        raise ValueError("registered protocol is not an object")
    expected_draft = {
        "status": "draft",
        "protocol_sha256": None,
        "commit": None,
        "frozen_at": None,
        "filed_before_affected_data": True,
    }
    if registered.get("freeze") != expected_draft:
        raise ValueError("freeze commit does not identify the registered draft")
    current_without_freeze = {key: value for key, value in protocol.items() if key != "freeze"}
    registered_without_freeze = {
        key: value for key, value in registered.items() if key != "freeze"
    }
    if current_without_freeze != registered_without_freeze:
        raise ValueError("frozen protocol differs from its registration beyond freeze metadata")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", registration, "HEAD"],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if ancestry.returncode != 0:
        raise ValueError("protocol registration commit is not in the analyzed history")
    return {
        "canonical_sha256": canonical_hash,
        "raw_file_sha256": raw_sha256(protocol_path),
        "registration_commit": registration,
        "validator_sha256": PROTOCOL_TOOL_SHA256,
        "protocol_schema_sha256": PROTOCOL_SCHEMA_SHA256,
        "export_schema_sha256": EXPORT_SCHEMA_SHA256,
    }


def load_verified_module(path: Path, expected_sha256: str, name: str) -> Any:
    if raw_sha256(path) != expected_sha256:
        raise ValueError(f"verified dependency SHA-256 mismatch: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load verified dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def bind_verified_dependencies(protocol: dict[str, Any]) -> dict[str, str]:
    global shared, campaign_core, l2_core, export_core
    links = protocol["links"]
    shared_path = REPO / links["analysis_primitives"]
    campaign_path = REPO / links["campaign_core"]
    l2_path = REPO / links["l2_measure"]
    shared = load_verified_module(
        shared_path,
        links["analysis_primitives_sha256"],
        "go_remote_ab_verified_primitives",
    )
    campaign_core = load_verified_module(
        campaign_path,
        links["campaign_core_sha256"],
        "go_remote_ab_verified_campaign_core",
    )
    l2_core = load_verified_module(
        l2_path,
        links["l2_measure_sha256"],
        "go_remote_ab_verified_l2_measure",
    )
    export_path = REPO / links["exporter"]
    export_core = load_verified_module(
        export_path,
        links["exporter_sha256"],
        "go_remote_ab_verified_exporter",
    )
    controller_dependencies = {}
    for path_key, hash_key in (
        ("transport_driver", "transport_driver_sha256"),
        ("transport_server", "transport_server_sha256"),
        ("transport_pod", "transport_pod_sha256"),
        ("transport_ship", "transport_ship_sha256"),
    ):
        path = REPO / links[path_key]
        if raw_sha256(path) != links[hash_key]:
            raise ValueError(f"verified transport dependency SHA-256 mismatch: {path}")
        controller_dependencies[hash_key] = raw_sha256(path)
    return {
        "analysis_primitives_sha256": raw_sha256(shared_path),
        "campaign_core_sha256": raw_sha256(campaign_path),
        "l2_measure_sha256": raw_sha256(l2_path),
        "exporter_sha256": raw_sha256(export_path),
        **controller_dependencies,
    }


def verify_extracted_run(
    run: Path,
    receipt: dict[str, Any],
    expected_output: str,
) -> dict[str, Any]:
    """Bind every extracted scientific byte to the authenticated result archive."""

    if run.name != expected_output or PurePosixPath(expected_output).name != expected_output:
        raise ValueError("--run does not name the frozen archive output root")
    records = receipt.get("result", {}).get("files")
    if not isinstance(records, list):
        raise ValueError("receipt result-file inventory is absent")
    prefix = expected_output + "/"
    expected: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise ValueError("receipt result-file record is malformed")
        name = record["path"]
        if name.startswith(prefix):
            relative = name[len(prefix) :]
            if not relative or PurePosixPath(relative).as_posix() != relative:
                raise ValueError("receipt output member path is malformed")
            if relative in expected:
                raise ValueError("receipt output member is duplicated")
            expected[relative] = record
    if not expected:
        raise ValueError("authenticated archive has no frozen output members")

    actual: dict[str, Path] = {}
    for path in sorted(run.rglob("*")):
        if path.is_symlink() or (path.exists() and not path.is_file() and not path.is_dir()):
            raise ValueError("extracted run contains a non-regular entry")
        if path.is_file():
            relative = path.relative_to(run).as_posix()
            actual[relative] = path
    if set(actual) != set(expected):
        missing = sorted(set(expected) - set(actual))[:3]
        extra = sorted(set(actual) - set(expected))[:3]
        raise ValueError(f"--run/archive inventory mismatch: missing={missing} extra={extra}")
    for relative, path in actual.items():
        record = expected[relative]
        if (
            path.stat().st_size != record.get("bytes")
            or raw_sha256(path) != record.get("sha256")
        ):
            raise ValueError(f"--run/archive content mismatch: {relative}")
    return {
        "output": expected_output,
        "files": len(actual),
        "bytes": sum(path.stat().st_size for path in actual.values()),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--protocol-tool",
        type=Path,
        default=Path("/workspace/crypto-autoresearcher/tools/experiment_protocol.py"),
    )
    return parser.parse_args()


def counter_map(text: Any) -> dict[str, int]:
    if not isinstance(text, str):
        raise ValueError("cgroup counter record is absent or not text")
    result: dict[str, int] = {}
    for line in text.splitlines():
        fields = line.split()
        if (
            len(fields) != 2
            or re.fullmatch(r"[A-Za-z0-9_.-]+", fields[0]) is None
            or re.fullmatch(r"[0-9]+", fields[1]) is None
            or fields[0] in result
        ):
            raise ValueError(f"malformed cgroup counter line: {line!r}")
        result[fields[0]] = int(fields[1])
    if not result:
        raise ValueError("empty cgroup counter record")
    return result


def counter_deltas(before: Any, after: Any) -> dict[str, int]:
    left = counter_map(before)
    right = counter_map(after)
    if set(left) != set(right):
        raise ValueError("cgroup counter inventory changed")
    deltas = {key: right[key] - left[key] for key in sorted(left)}
    if any(value < 0 for value in deltas.values()):
        raise ValueError("cgroup counter decreased")
    return deltas


def choose_verdict(
    *,
    complete: bool,
    correctness: bool,
    allocation: bool,
    timing_numeric: bool,
    timing_isolation: bool,
) -> str:
    """Apply the preregistered terminal order without data-dependent choices."""

    if not complete:
        return "inconclusive"
    if not correctness:
        return "wrong_answer"
    timing = timing_numeric and timing_isolation
    if allocation and timing:
        return "supported_within_scope"
    if allocation:
        return "allocation_only"
    if timing:
        return "timing_only"
    if not timing_isolation:
        return "invalid_measurement"
    return "unsupported"


def transport_is_complete(returncode: Any, mismatches: int) -> bool:
    """Accept the deliberate post-seal mismatch exit for wrong-answer reporting."""

    return returncode == 0 or (returncode == 1 and mismatches > 0)


def claim_statuses(
    *,
    complete: bool,
    correctness: bool,
    allocation: bool,
    timing_numeric: bool,
    timing_isolation: bool,
) -> dict[str, str]:
    if not complete:
        return {
            "C-ab-correct": "not_evaluated",
            "C-ab-allocation": "not_evaluated",
            "C-ab-timing": "not_evaluated",
        }
    if not correctness:
        return {
            "C-ab-correct": "wrong_answer",
            "C-ab-allocation": "unsupported",
            "C-ab-timing": "unsupported",
        }
    return {
        "C-ab-correct": "supported",
        "C-ab-allocation": "supported" if allocation else "unsupported",
        "C-ab-timing": (
            "supported"
            if timing_numeric and timing_isolation
            else "invalid_measurement"
            if not timing_isolation
            else "unsupported"
        ),
    }


def compute_case_results(
    rows: list[dict[str, Any]], cases: list[str]
) -> tuple[list[dict[str, Any]], bool, bool, bool, int]:
    measured = [row for row in rows if not row["warmup"]]
    by_cell = {(row["case"], row["replicate"], row["arm"]): row for row in measured}
    matching_pairs = 0
    allocation_pass = True
    timing_pass = True
    aa_calibration_pass = True
    results: list[dict[str, Any]] = []
    for case in cases:
        ratios: dict[str, list[Fraction]] = defaultdict(list)
        for replicate in range(1, EXPECTED_REPLICATES + 1):
            baseline = by_cell[(case, replicate, BASELINE_ARM)]["parsed"]
            candidate = by_cell[(case, replicate, CANDIDATE_ARM)]["parsed"]
            aa_left = by_cell[(case, replicate, AA_LEFT_ARM)]["parsed"]
            aa_right = by_cell[(case, replicate, AA_RIGHT_ARM)]["parsed"]
            if baseline["fingerprints"] != candidate["fingerprints"]:
                raise ValueError("case analysis called before correctness passed")
            if aa_left["fingerprints"] != aa_right["fingerprints"]:
                raise ValueError("A/A analysis called before correctness passed")
            matching_pairs += 2
            left = baseline["metrics"]
            right = candidate["metrics"]
            for metric in ("B/op", "allocs/op"):
                ratios[metric].append(Fraction(right[metric], left[metric]))
            for metric in ("ns/op", "cpu-ns/op"):
                ratios[f"ab:{metric}"].append(Fraction(left[metric], right[metric]))
                ratios[f"aa:{metric}"].append(
                    Fraction(aa_left["metrics"][metric], aa_right["metrics"][metric])
                )

        metrics: dict[str, Any] = {}
        for metric in ("B/op", "allocs/op"):
            median = shared.median_fraction(ratios[metric])
            passes = median <= ALLOCATION_THRESHOLD
            allocation_pass = allocation_pass and passes
            metrics[metric] = {
                "direction": "candidate_over_baseline",
                "paired_median": shared.fraction_json(median),
                "threshold": shared.fraction_json(ALLOCATION_THRESHOLD),
                "passes": passes,
            }
        for metric in ("ns/op", "cpu-ns/op"):
            aa_values = ratios[f"aa:{metric}"]
            aa_median = shared.median_fraction(aa_values)
            aa_distribution = shared.exact_bootstrap_median_distribution(aa_values)
            aa_lower = shared.exact_quantile(aa_distribution, LOWER_QUANTILE)
            aa_upper = shared.exact_quantile(aa_distribution, UPPER_QUANTILE)
            aa_contains_one = aa_lower <= 1 <= aa_upper
            aa_equivalent = (
                aa_lower > 0
                and aa_lower >= 1 / AA_EQUIVALENCE
                and aa_upper <= AA_EQUIVALENCE
            )
            noise = max(aa_upper, 1 / aa_lower) if aa_lower > 0 else None

            ab_values = ratios[f"ab:{metric}"]
            median = shared.median_fraction(ab_values)
            distribution = shared.exact_bootstrap_median_distribution(ab_values)
            lower = shared.exact_quantile(distribution, LOWER_QUANTILE)
            aa_passes = aa_contains_one and aa_equivalent and noise is not None
            passes = (
                noise is not None
                and median >= TIMING_THRESHOLD
                and lower > max(Fraction(1), noise)
            )
            aa_calibration_pass = aa_calibration_pass and aa_passes
            timing_pass = timing_pass and passes
            metrics[metric] = {
                "direction": "baseline_over_candidate",
                "paired_median": shared.fraction_json(median),
                "median_threshold": shared.fraction_json(TIMING_THRESHOLD),
                "simultaneous_lower_bound": shared.fraction_json(lower, decimals=15),
                "lower_quantile": "1/960",
                "bootstrap_support_points": len(distribution),
                "aa": {
                    "direction": "aa_left_over_aa_right",
                    "paired_median": shared.fraction_json(aa_median),
                    "simultaneous_interval": {
                        "lower": shared.fraction_json(aa_lower, decimals=15),
                        "upper": shared.fraction_json(aa_upper, decimals=15),
                        "quantiles": ["1/960", "959/960"],
                    },
                    "contains_one": aa_contains_one,
                    "equivalence_band": ["20/21", "21/20"],
                    "equivalent": aa_equivalent,
                    "passes": aa_passes,
                    "symmetric_noise_factor": (
                        shared.fraction_json(noise, decimals=15) if noise is not None else None
                    ),
                    "bootstrap_support_points": len(aa_distribution),
                },
                "required_lower_bound": (
                    shared.fraction_json(max(Fraction(1), noise), decimals=15)
                    if noise is not None else None
                ),
                "passes": passes,
            }
        results.append({"case": case, "pairs": EXPECTED_REPLICATES, "metrics": metrics})
    return results, allocation_pass, timing_pass, aa_calibration_pass, matching_pairs


def correctness_inventory(rows: list[dict[str, Any]], cases: list[str]) -> dict[str, int]:
    by_cell = {
        (row["case"], row["warmup"], row["replicate"], row["arm"]): row
        for row in rows
    }
    matches = mismatches = 0
    for case in cases:
        reference = None
        rounds = [(True, replicate) for replicate in range(1, 4)]
        rounds += [(False, replicate) for replicate in range(1, 21)]
        for warmup, replicate in rounds:
            values = [
                by_cell[(case, warmup, replicate, arm)]["parsed"]["fingerprints"]
                for arm in EXPECTED_ARMS
            ]
            if reference is None:
                reference = values[0]
            if all(value == reference for value in values):
                matches += 1
            else:
                mismatches += 1
    return {"matches": matches, "mismatches": mismatches}


def load_verified_rows(
    run: Path, protocol: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    campaign = run / "campaign"
    rows_path = campaign / "rows.jsonl"
    rows = [
        json.loads(line)
        for line in rows_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    manifest = shared.load_json(campaign / "manifest.json")
    summary = shared.load_json(campaign / "summary.json")
    protocol_sha = protocol["freeze"]["protocol_sha256"]
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} rows, got {len(rows)}")
    if [row.get("sequence") for row in rows] != list(range(1, EXPECTED_ROWS + 1)):
        raise ValueError("row sequence is not exact and contiguous")
    if manifest.get("protocol_sha256") != protocol_sha or summary.get("protocol_sha256") != protocol_sha:
        raise ValueError("campaign protocol SHA-256 mismatch")
    if any(row.get("protocol_sha256") != protocol_sha for row in rows):
        raise ValueError("row protocol SHA-256 mismatch")
    if (
        summary.get("planned") != EXPECTED_ROWS
        or summary.get("attempted") != EXPECTED_ROWS
        or summary.get("failures") != 0
        or summary.get("rows_sha256") != shared.sha256(rows_path)
    ):
        raise ValueError("campaign summary flow mismatch")
    if any(
        row.get("status") != "completed"
        or row.get("outcome_class") != "verified"
        or row.get("exit_status") != 0
        or row.get("timed_out") is not False
        or row.get("parsed", {}).get("iterations") != 100
        for row in rows
    ):
        raise ValueError("campaign contains a failed, timed-out, or non-100x row")
    warmups = [row for row in rows if row["warmup"]]
    measured = [row for row in rows if not row["warmup"]]
    if len(warmups) != EXPECTED_WARMUPS or len(measured) != EXPECTED_MEASURED:
        raise ValueError("campaign warmup/measured inventory mismatch")
    arms = {record["id"]: record for record in manifest.get("arms", [])}
    if set(arms) != set(EXPECTED_ARMS):
        raise ValueError("campaign arm inventory mismatch")
    return rows, {
        "rows_sha256": shared.sha256(rows_path),
        "campaign_manifest_sha256": shared.sha256(campaign / "manifest.json"),
        "campaign_summary_sha256": shared.sha256(campaign / "summary.json"),
        "cases": manifest.get("cases"),
        "arms": arms,
        "warmups": warmups,
        "measured": measured,
    }


def verify_frozen_schedule(
    run: Path,
    rows: list[dict[str, Any]],
    protocol: dict[str, Any],
) -> dict[str, Any]:
    manifest = shared.load_json(run / "campaign" / "manifest.json")
    summary = shared.load_json(run / "campaign" / "summary.json")
    protocol_sha256 = protocol["freeze"]["protocol_sha256"]
    if protocol["links"]["benchmark_cases"] != EXPECTED_CASES:
        raise ValueError("protocol benchmark-case list mismatch")
    if manifest.get("cases") != EXPECTED_CASES:
        raise ValueError("campaign benchmark-case order differs from the frozen protocol")
    if (
        not isinstance(manifest.get("session_affinity"), list)
        or len(manifest["session_affinity"]) != 32
        or manifest["session_affinity"] != sorted(set(manifest["session_affinity"]))
        or manifest.get("benchmark_cpu") not in manifest.get("reservation", {}).get("cpus", [])
        or manifest.get("runner_affinity")
        != [
            cpu
            for cpu in manifest.get("session_affinity", [])
            if cpu not in manifest.get("reservation", {}).get("cpus", [])
        ]
    ):
        raise ValueError("campaign session/reserved/runner affinity mismatch")
    if (
        manifest.get("schema") != "go-coordinator-peer-key-campaign/2"
        or manifest.get("protocol_sha256") != protocol_sha256
        or manifest.get("warmups") != 3
        or manifest.get("replicates") != 20
        or manifest.get("benchtime") != "100x"
        or manifest.get("benchmark_source_sha256") != EXPECTED_BENCHMARK_SHA256
        or manifest.get("runner_sha256") != protocol["links"]["campaign_runner_sha256"]
        or manifest.get("phase") != "fixed-peer-key-ab-aa-v9"
        or manifest.get("order_cycle") != [list(order) for order in ORDER_CYCLE]
        or manifest.get("l2_measure_sha256") != protocol["links"]["l2_measure_sha256"]
        or manifest.get("environment") != EXPECTED_ENVIRONMENT
        or manifest.get("environment_sha256") != EXPECTED_ENVIRONMENT_SHA256
        or manifest.get("environment_sha256") != protocol["links"]["benchmark_environment_sha256"]
        or manifest.get("session_lock", {}).get("path") != "/tmp/crypto-bench.lock"
        or manifest.get("session_lock", {}).get("exclusive") is not True
        or manifest.get("session_lock", {}).get("nonblocking") is not True
    ):
        raise ValueError("campaign manifest differs from the frozen schedule")
    manifest_arms = manifest.get("arms", [])
    if [arm.get("id") for arm in manifest_arms] != list(EXPECTED_ARMS):
        raise ValueError("campaign arm order differs from the frozen schedule")
    binary_names = {
        BASELINE_ARM: "coord-baseline.test",
        CANDIDATE_ARM: "coord-candidate.test",
        AA_LEFT_ARM: "coord-baseline-aa-left.test",
        AA_RIGHT_ARM: "coord-baseline-aa-right.test",
    }
    arm_records: dict[str, dict[str, Any]] = {}
    for arm in manifest_arms:
        arm_id = arm["id"]
        binary = arm.get("binary")
        if (
            not isinstance(binary, str)
            or tuple(PurePosixPath(binary).parts[-3:])
            != (EXPECTED_OUTPUT, "build", binary_names[arm_id])
            or re.fullmatch(r"[0-9a-f]{64}", str(arm.get("sha256", ""))) is None
        ):
            raise ValueError(f"campaign binary identity mismatch: {arm_id}")
        arm_records[arm_id] = arm

    expected: list[dict[str, Any]] = []
    sequence = 0
    for case_index, case in enumerate(EXPECTED_CASES, 1):
        rounds = [(True, replicate) for replicate in range(1, 4)]
        rounds += [(False, replicate) for replicate in range(1, 21)]
        for warmup, replicate in rounds:
            arms = ORDER_CYCLE[(replicate - 1) % len(ORDER_CYCLE)]
            for position, arm in enumerate(arms, 1):
                sequence += 1
                kind = "warmup" if warmup else "measured"
                stem = (
                    f"{sequence:04d}_{kind}_case{case_index:02d}_r{replicate:02d}_"
                    f"p{position}_{arm}"
                )
                expected.append(
                    {
                        "sequence": sequence,
                        "case": case,
                        "case_index": case_index,
                        "warmup": warmup,
                        "replicate": replicate,
                        "order_position": position,
                        "arm": arm,
                        "run_id": stem,
                    }
                )
    if len(expected) != EXPECTED_ROWS:
        raise AssertionError("internal frozen schedule length mismatch")
    benchmark_cpu = str(manifest["benchmark_cpu"])
    for row, planned in zip(rows, expected, strict=True):
        for key, value in planned.items():
            if row.get(key) != value:
                raise ValueError(
                    f"row {planned['sequence']} schedule mismatch for {key}: "
                    f"observed={row.get(key)!r} expected={value!r}"
                )
        if (
            row.get("schema") != "go-coordinator-peer-key-row/2"
            or row.get("protocol_sha256") != protocol_sha256
            or row.get("phase") != "fixed-peer-key-ab-aa-v9"
            or row.get("benchmark_source_sha256") != EXPECTED_BENCHMARK_SHA256
            or row.get("session_affinity") != manifest["session_affinity"]
            or row.get("runner_affinity") != manifest["runner_affinity"]
            or row.get("reservation_cpus") != manifest["reservation"]["cpus"]
            or row.get("expected_child_affinity") != [manifest["benchmark_cpu"]]
            or row.get("environment") != manifest["environment"]
            or row.get("environment_sha256") != manifest["environment_sha256"]
            or row.get("status") != "completed"
            or row.get("outcome_class") != "verified"
            or row.get("exit_status") != 0
            or row.get("timed_out") is not False
            or row.get("binary") != arm_records[row["arm"]]["binary"]
            or row.get("binary_sha256") != arm_records[row["arm"]]["sha256"]
        ):
            raise ValueError(f"row {row['sequence']} frozen identity mismatch")
        command = row.get("command")
        suffix = [
            "-test.run=^$",
            f"-test.bench=^{row['case']}$",
            "-test.benchmem",
            "-test.benchtime=100x",
            "-test.count=1",
            "-test.cpu=1",
            "-test.v",
            "-test.timeout=20m",
        ]
        if (
            not isinstance(command, list)
            or command[:3] != ["/usr/bin/taskset", "-c", benchmark_cpu]
            or command[3] != row["binary"]
            or command[4:] != suffix
        ):
            raise ValueError(f"row {row['sequence']} benchmark argv mismatch")
        expected_artifacts = {
            "stdout": f"raw/benchmark-output/{row['run_id']}.txt",
            "stderr": f"raw/benchmark-stderr/{row['run_id']}.txt",
            "metadata": f"raw/run-metadata/{row['run_id']}.json",
        }
        for kind, path in expected_artifacts.items():
            if row.get("artifacts", {}).get(kind) != path:
                raise ValueError(f"row {row['sequence']} {kind} path mismatch")
        campaign = run / "campaign"
        stdout_path = campaign / expected_artifacts["stdout"]
        stderr_path = campaign / expected_artifacts["stderr"]
        metadata_path = campaign / expected_artifacts["metadata"]
        if (
            row.get("artifacts", {}).get("stdout_sha256") != shared.sha256(stdout_path)
            or row.get("artifacts", {}).get("stderr_sha256") != shared.sha256(stderr_path)
        ):
            raise ValueError(f"row {row['sequence']} raw log hash mismatch")
        reparsed = campaign_core.parse_output(stdout_path.read_bytes())
        if row.get("parsed") != reparsed:
            raise ValueError(f"row {row['sequence']} parsed stdout mismatch")
        if shared.load_json(metadata_path) != row:
            raise ValueError(f"row {row['sequence']} metadata content mismatch")
        metrics = reparsed.get("metrics", {})
        fingerprints = reparsed.get("fingerprints", {})
        expected_fingerprints = (
            {"vector_sha256"}
            if row["case"].startswith("BenchmarkStateVersionVector/")
            else {"lines_sha256", "reached_vector_sha256"}
        )
        if (
            reparsed.get("iterations") != 100
            or not {"ns/op", "cpu-ns/op", "B/op", "allocs/op"}.issubset(metrics)
            or set(fingerprints) != expected_fingerprints
            or not isinstance(row.get("outer_wall_ns"), int)
            or row["outer_wall_ns"] < 0
        ):
            raise ValueError(f"row {row['sequence']} parsed benchmark contract mismatch")
    if (
        summary.get("schema") != "go-coordinator-peer-key-campaign-summary/2"
        or summary.get("protocol_sha256") != protocol_sha256
        or summary.get("planned") != EXPECTED_ROWS
        or summary.get("attempted") != EXPECTED_ROWS
        or summary.get("failures") != 0
        or summary.get("rows_sha256") != shared.sha256(run / "campaign" / "rows.jsonl")
        or summary.get("phase") != "fixed-peer-key-ab-aa-v9"
        or summary.get("benchmark_cpu") != manifest["benchmark_cpu"]
        or summary.get("session_affinity") != manifest["session_affinity"]
        or summary.get("runner_affinity") != manifest["runner_affinity"]
        or summary.get("reservation") != manifest["reservation"]
        or summary.get("session_lock") != manifest["session_lock"]
        or summary.get("environment_sha256") != manifest["environment_sha256"]
        or summary.get("order_cycle") != manifest["order_cycle"]
    ):
        raise ValueError("campaign summary differs from the frozen schedule")
    return {"rows": len(expected), "cases": EXPECTED_CASES}


def verify_test_record(record: Any, go_command: str, expected_log: str) -> None:
    if (
        not isinstance(record, dict)
        or set(record) != {
            "command", "cwd", "environment_sha256", "exit_status",
            "log", "log_bytes", "log_sha256",
        }
        or record["exit_status"] != 0
        or record.get("command") != [go_command, "test", "./..."]
        or record.get("cwd") != "bindings/go"
        or record.get("log") != expected_log
        or type(record.get("log_bytes")) is not int
        or record["log_bytes"] < 0
        or re.fullmatch(r"[0-9a-f]{64}", str(record.get("log_sha256", ""))) is None
    ):
        raise ValueError("correctness-test command/receipt is not exact")


def verify_tests(run: Path, protocol_sha256: str) -> dict[str, Any]:
    path = run / "tests" / "manifest.json"
    manifest = shared.load_json(path)
    if manifest != {
        "schema": "go-coordinator-remote-tests/v1",
        "protocol_sha256": protocol_sha256,
        "build_environment": manifest.get("build_environment"),
        "build_environment_sha256": manifest.get("build_environment_sha256"),
        "arms": manifest.get("arms"),
    }:
        raise ValueError("test manifest top-level contract mismatch")
    arms = manifest["arms"]
    environment_digest = verify_build_environment(
        manifest.get("build_environment"), manifest.get("build_environment_sha256")
    )
    go_command = str(PurePosixPath(manifest["build_environment"]["GOROOT"]) / "bin" / "go")
    if set(arms) != {BASELINE_ARM, CANDIDATE_ARM}:
        raise ValueError("test manifest arm inventory mismatch")
    expected_logs = {BASELINE_ARM: "baseline.txt", CANDIDATE_ARM: "candidate.txt"}
    for arm, record in arms.items():
        try:
            verify_test_record(record, go_command, expected_logs[arm])
        except ValueError as error:
            raise ValueError(f"correctness tests did not pass for {arm}") from error
        if record.get("environment_sha256") != environment_digest:
            raise ValueError(f"correctness tests did not pass for {arm}")
        log = run / "tests" / record["log"]
        if (
            not log.is_file()
            or log.stat().st_size != record["log_bytes"]
            or shared.sha256(log) != record["log_sha256"]
        ):
            raise ValueError(f"correctness test log binding mismatch for {arm}")
    return {
        "manifest_sha256": shared.sha256(path),
        "arms": arms,
        "environment": manifest.get("build_environment"),
        "environment_sha256": environment_digest,
    }


def verify_build_environment(environment: Any, digest: Any) -> str:
    if not isinstance(environment, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in environment.items()
    ):
        raise ValueError("build environment is not an exact string mapping")
    if set(environment) != set(EXPECTED_BUILD_ENVIRONMENT_FIXED) | set(
        EXPECTED_BUILD_DYNAMIC_PATHS
    ):
        raise ValueError("build environment allowlist mismatch")
    for key, value in EXPECTED_BUILD_ENVIRONMENT_FIXED.items():
        if environment.get(key) != value:
            raise ValueError(f"build environment fixed value mismatch: {key}")
    home = PurePosixPath(environment["HOME"])
    root = home.parent
    if (
        not root.is_absolute()
        or root.parent != PurePosixPath("/tmp")
        or not root.name.startswith("go-coord-remote-ab-")
    ):
        raise ValueError("build environment root is outside the frozen temp namespace")
    for key, relative in EXPECTED_BUILD_DYNAMIC_PATHS.items():
        value = PurePosixPath(environment[key])
        expected = root / PurePosixPath(relative)
        if not value.is_absolute() or value != expected:
            raise ValueError(f"build environment dynamic path mismatch: {key}")
    computed = hashlib.sha256(
        json.dumps(environment, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if digest != computed:
        raise ValueError("build environment SHA-256 mismatch")
    return computed


def verify_go_toolchain(toolchain: dict[str, Any]) -> None:
    if (
        toolchain.get("url") != "https://go.dev/dl/" + GO_ARCHIVE
        or toolchain.get("archive") != GO_ARCHIVE
        or toolchain.get("archive_bytes") != GO_ARCHIVE_BYTES
        or toolchain.get("archive_sha256") != GO_ARCHIVE_SHA256
        or toolchain.get("go_version") != "go version go1.27.3 linux/amd64"
        or toolchain.get("go_env", {}).get("GOOS") != "linux"
        or toolchain.get("go_env", {}).get("GOARCH") != "amd64"
        or "retained_archive" in toolchain
    ):
        raise ValueError("Go download/toolchain identity mismatch")


def verify_binary_artifacts(
    run: Path,
    build_arms: dict[str, Any],
    campaign_arms: dict[str, Any],
) -> None:
    filenames = EXPECTED_BINARY_FILES
    if set(build_arms) != set(filenames) or set(campaign_arms) != set(filenames):
        raise ValueError("build/campaign binary arm inventory mismatch")
    for arm in EXPECTED_ARMS:
        record = build_arms[arm]
        binary = run / "build" / filenames[arm]
        if (
            not binary.is_file()
            or record.get("binary") != filenames[arm]
            or record.get("binary_bytes") != binary.stat().st_size
            or record.get("binary_sha256") != shared.sha256(binary)
            or record["binary_sha256"] != campaign_arms[arm]["sha256"]
            or PurePosixPath(campaign_arms[arm]["binary"]).name != filenames[arm]
        ):
            raise ValueError(f"build/campaign binary mismatch: {arm}")
    if not (
        build_arms[BASELINE_ARM]["binary_sha256"]
        == build_arms[AA_LEFT_ARM]["binary_sha256"]
        == build_arms[AA_RIGHT_ARM]["binary_sha256"]
    ):
        raise ValueError("A/A binaries are not byte-identical to the A/B baseline")
    if build_arms[CANDIDATE_ARM]["binary_sha256"] == build_arms[BASELINE_ARM]["binary_sha256"]:
        raise ValueError("candidate binary unexpectedly equals baseline")


def verify_build_record(
    record: Any,
    arm: str,
    go_command: str,
    baseline_record: dict[str, Any] | None,
) -> None:
    filename = EXPECTED_BINARY_FILES[arm]
    if not isinstance(record, dict):
        raise ValueError("build receipt is not an object")
    if arm in {BASELINE_ARM, CANDIDATE_ARM}:
        command = record.get("command")
        output_path = (
            PurePosixPath(command[5])
            if isinstance(command, list) and len(command) == 7
            and isinstance(command[5], str)
            else None
        )
        if (
            set(record) != {
                "command", "cwd", "environment_sha256", "stdout", "binary",
                "binary_bytes", "binary_sha256",
            }
            or not isinstance(record.get("stdout"), str)
            or command is None
            or command[:5] != [go_command, "test", "-c", "-trimpath", "-o"]
            or command[6] != "."
            or output_path is None
            or not output_path.is_absolute()
            or output_path.parts[-3:] != (EXPECTED_OUTPUT, "build", filename)
            or record.get("cwd") != "bindings/go"
        ):
            raise ValueError("compiled build command/receipt is not exact")
        return
    if baseline_record is None:
        raise ValueError("A/A copy receipt lacks its baseline receipt")
    expected = {
        **baseline_record,
        "command": ["byte-identical copy", EXPECTED_BINARY_FILES[BASELINE_ARM]],
        "binary": filename,
        "binary_bytes": record.get("binary_bytes"),
        "binary_sha256": record.get("binary_sha256"),
        "derived_from": EXPECTED_BINARY_FILES[BASELINE_ARM],
    }
    if record != expected:
        raise ValueError("A/A copy receipt is not exact")


def verify_build(
    run: Path,
    protocol: dict[str, Any],
    campaign_arms: dict[str, Any],
    transport: dict[str, Any],
) -> dict[str, Any]:
    path = run / "build" / "manifest.json"
    manifest = shared.load_json(path)
    if manifest.get("schema") != "go-coordinator-remote-build/v1" or manifest.get("mode") != "combined":
        raise ValueError("build manifest is not the preregistered combined mode")
    if manifest.get("expected_cpu_flavor") != "cpu3c":
        raise ValueError("build manifest CPU flavor mismatch")
    sources = manifest.get("sources", {})
    for key, expected in EXPECTED_SOURCE_IDENTITIES.items():
        if sources.get(key) != expected:
            raise ValueError(f"build source identity mismatch: {key}")
    if sources.get("benchmark_sha256") != EXPECTED_BENCHMARK_SHA256:
        raise ValueError("benchmark source SHA-256 mismatch")
    if sources.get("candidate_diff_sha256") != EXPECTED_DIFF_SHA256:
        raise ValueError("candidate diff SHA-256 mismatch")
    for key, expected in EXPECTED_COMMON_TEST.items():
        if sources.get(key) != expected:
            raise ValueError(f"common correctness-test identity mismatch: {key}")
    if sources.get("only_changed_path") != "bindings/go/coord.go":
        raise ValueError("synthetic arms differ outside coord.go")
    toolchain = manifest.get("toolchain", {})
    verify_go_toolchain(toolchain)
    build_environment_digest = verify_build_environment(
        manifest.get("build_environment"), manifest.get("build_environment_sha256")
    )
    source_plan = protocol["extensions"]["remote_execution"]["source"]
    source_archive = manifest.get("source_archive", {})
    if source_archive != {
        "commit": source_plan["commit"],
        "tree": source_plan["tree"],
        "bytes": source_plan["archive_bytes"],
        "sha256": source_plan["archive_sha256"],
        "retained": False,
    }:
        raise ValueError("registered source-archive build receipt mismatch")
    if source_archive["sha256"] != transport["source_archive_sha256"]:
        raise ValueError("build/transport source archive mismatch")
    runner = manifest.get("runner", {})
    links = protocol["links"]
    expected_support = [
        {
            "path": links["campaign_core"],
            "sha256": links["campaign_core_sha256"],
        },
        {
            "path": links["analysis_primitives"],
            "sha256": links["analysis_primitives_sha256"],
        },
    ]
    expected_bound = {
        "engine": links["remote_runner"],
        "engine_sha256": links["remote_runner_sha256"],
        "binding": links["remote_binding"],
        "binding_sha256": links["remote_binding_sha256"],
        "exporter": links["exporter"],
        "exporter_sha256": links["exporter_sha256"],
        "analyzer": links["formal_analyzer"],
        "analyzer_sha256": links["formal_analyzer_sha256"],
        "campaign": links["campaign_runner"],
        "campaign_sha256": links["campaign_runner_sha256"],
        "l2_measure": links["l2_measure"],
        "l2_measure_sha256": links["l2_measure_sha256"],
        "support": expected_support,
    }
    for key, value in expected_bound.items():
        if runner.get(key) != value:
            raise ValueError(f"runner or constant-binding wrapper mismatch: {key}")
    retained = runner.get("retained")
    expected_retained_paths = {
        links["remote_runner"],
        links["remote_binding"],
        links["exporter"],
        links["formal_analyzer"],
        links["campaign_runner"],
        links["l2_measure"],
        links["campaign_core"],
        links["analysis_primitives"],
    }
    if not isinstance(retained, dict) or set(retained) != expected_retained_paths:
        raise ValueError("runner or constant-binding wrapper mismatch")
    source_hashes = {
        links["remote_runner"]: links["remote_runner_sha256"],
        links["remote_binding"]: links["remote_binding_sha256"],
        links["exporter"]: links["exporter_sha256"],
        links["formal_analyzer"]: links["formal_analyzer_sha256"],
        links["campaign_runner"]: links["campaign_runner_sha256"],
        links["l2_measure"]: links["l2_measure_sha256"],
        links["campaign_core"]: links["campaign_core_sha256"],
        links["analysis_primitives"]: links["analysis_primitives_sha256"],
    }
    for source, expected_sha in source_hashes.items():
        record = retained[source]
        retained_path = run / "tooling" / Path(source).name
        if (
            record
            != {
                "path": f"tooling/{Path(source).name}",
                "bytes": retained_path.stat().st_size,
                "sha256": expected_sha,
            }
            or shared.sha256(retained_path) != expected_sha
        ):
            raise ValueError(f"retained tooling binding mismatch: {source}")
    if manifest.get("runner_sha256") != links["remote_runner_sha256"]:
        raise ValueError("legacy runner SHA-256 field mismatch")
    if set(manifest.get("arms", {})) != set(EXPECTED_ARMS):
        raise ValueError("build arm inventory mismatch")
    go_command = str(PurePosixPath(manifest["build_environment"]["GOROOT"]) / "bin" / "go")
    for arm, record in manifest["arms"].items():
        if record.get("environment_sha256") != build_environment_digest:
            raise ValueError(f"build arm environment mismatch: {arm}")
        try:
            verify_build_record(
                record,
                arm,
                go_command,
                manifest["arms"][BASELINE_ARM] if arm not in {BASELINE_ARM, CANDIDATE_ARM} else None,
            )
        except ValueError as error:
            raise ValueError(f"build arm command mismatch: {arm}") from error
    verify_binary_artifacts(run, manifest["arms"], campaign_arms)
    return {
        "manifest_sha256": shared.sha256(path),
        "manifest": manifest,
        "environment_sha256": build_environment_digest,
    }


def verify_export(
    run: Path,
    protocol_path: Path,
    protocol: dict[str, Any],
    summary: dict[str, Any],
    build: dict[str, Any],
    tool_path: Path,
) -> dict[str, Any]:
    export_path = run / "campaign" / "export.json"
    if summary.get("export_path") != "campaign/export.json":
        raise ValueError("remote summary export path mismatch")
    if summary.get("export_sha256") != shared.sha256(export_path):
        raise ValueError("remote summary export SHA-256 mismatch")
    export = shared.load_json(export_path)
    if (
        export.get("schema") != "experiment.export/v1"
        or export.get("protocol", {}).get("sha256") != protocol["freeze"]["protocol_sha256"]
        or export.get("protocol", {}).get("protocol_id") != protocol["protocol_id"]
        or export.get("protocol", {}).get("version") != protocol["version"]
        or export.get("source", {}).get("commit")
        != protocol["extensions"]["remote_execution"]["source"]["commit"]
        or len(export.get("runs", [])) != EXPECTED_ROWS
    ):
        raise ValueError("export protocol/source/run binding mismatch")
    if not isinstance(export.get("created"), str) or not export["created"]:
        raise ValueError("export creation timestamp is malformed")
    expected_export = export_core.produce(
        run,
        protocol["freeze"]["protocol_sha256"],
        protocol["extensions"]["remote_execution"]["source"]["commit"],
        export_path,
        created=export["created"],
    )
    if export != expected_export:
        raise ValueError("export differs from exact raw recomputation")
    export_arms = {arm["id"]: arm for arm in export.get("arms", [])}
    if set(export_arms) != set(EXPECTED_ARMS):
        raise ValueError("export arm inventory mismatch")
    for arm in export_arms:
        if export_arms[arm]["binary_sha256"] != build["manifest"]["arms"][arm]["binary_sha256"]:
            raise ValueError(f"export binary SHA-256 mismatch: {arm}")
    copied_script = export.get("analysis", {}).get("script")
    if not isinstance(copied_script, dict) or copied_script.get("sha256") != protocol[
        "analysis_plan"
    ]["script"]["sha256"]:
        raise ValueError("export analysis-script binding mismatch")

    tool_path = tool_path.resolve()
    schema_path = tool_path.parents[1] / "schemas" / "experiment-export.v1.json"
    if shared.sha256(tool_path) != protocol["links"]["export_validator_sha256"]:
        raise ValueError("canonical export validator SHA-256 mismatch")
    if shared.sha256(schema_path) != protocol["links"]["export_schema_sha256"]:
        raise ValueError("canonical export schema SHA-256 mismatch")
    result = subprocess.run(
        [
            sys.executable,
            str(tool_path),
            "check-export",
            str(export_path),
            "--protocol",
            str(protocol_path),
            "--verify-files",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError("canonical export validation failed:\n" + result.stdout)
    return {
        "path": "campaign/export.json",
        "sha256": shared.sha256(export_path),
        "runs": len(export["runs"]),
        "canonical_validator_sha256": shared.sha256(tool_path),
        "canonical_schema_sha256": shared.sha256(schema_path),
        "canonical_check": result.stdout.strip(),
    }


def verify_failure_export(
    run: Path,
    protocol_path: Path,
    protocol: dict[str, Any],
    summary: dict[str, Any],
    tool_path: Path,
) -> dict[str, Any]:
    """Authenticate the failure-total export without evaluating science."""

    expected_summary_keys = {
        "schema", "status", "protocol_sha256", "source_commit", "failure_path",
        "failure_sha256", "failure_stage", "usable_prefix_rows", "export_path",
        "export_sha256", "remote_returncode", "claims_evaluated",
        "output_budget_bytes", "output_bytes_before_summary",
        "output_files_before_summary", "remote_summary_reserve_bytes",
    }
    protocol_sha = protocol["freeze"]["protocol_sha256"]
    source_commit = protocol["extensions"]["remote_execution"]["source"]["commit"]
    export_path = run / "campaign" / "export.json"
    failure_path = run / "failure.json"
    if (
        set(summary) != expected_summary_keys
        or summary.get("schema") != "go-coordinator-remote-summary/v1"
        or summary.get("status") != "mechanical_failure"
        or summary.get("protocol_sha256") != protocol_sha
        or summary.get("source_commit") != source_commit
        or summary.get("failure_path") != "failure.json"
        or summary.get("export_path") != "campaign/export.json"
        or summary.get("remote_returncode") != 2
        or summary.get("claims_evaluated") is not False
        or summary.get("failure_sha256") != shared.sha256(failure_path)
        or summary.get("export_sha256") != shared.sha256(export_path)
    ):
        raise ValueError("mechanical-failure remote summary mismatch")
    pre_summary = {"files": 0, "bytes": 0}
    for path in run.rglob("*"):
        if path.is_file() and path != run / "remote-summary.json":
            pre_summary["files"] += 1
            pre_summary["bytes"] += path.stat().st_size
    if (
        summary.get("output_budget_bytes") != 96_000_000
        or summary.get("output_bytes_before_summary") != pre_summary["bytes"]
        or summary.get("output_files_before_summary") != pre_summary["files"]
        or summary.get("remote_summary_reserve_bytes") != 65_536
        or pre_summary["bytes"] + 65_536 > 96_000_000
    ):
        raise ValueError("mechanical-failure output budget mismatch")

    failure = shared.load_json(failure_path)
    if (
        set(failure) != {
            "schema", "protocol_sha256", "source_commit", "phase", "stage",
            "error", "usable_prefix_rows",
        }
        or failure.get("schema") != "go-coordinator-remote-failure/v1"
        or failure.get("protocol_sha256") != protocol_sha
        or failure.get("source_commit") != source_commit
        or failure.get("phase") != "fixed-peer-key-ab-aa-v9"
        or failure.get("stage") != summary.get("failure_stage")
        or failure.get("usable_prefix_rows") != summary.get("usable_prefix_rows")
        or type(failure.get("usable_prefix_rows")) is not int
        or not 0 <= failure["usable_prefix_rows"] <= EXPECTED_ROWS
        or not isinstance(failure.get("stage"), str)
        or not failure["stage"]
        or not isinstance(failure.get("error"), dict)
        or set(failure["error"]) != {"type", "detail"}
        or any(not isinstance(failure["error"].get(key), str) for key in ("type", "detail"))
    ):
        raise ValueError("mechanical-failure receipt mismatch")

    export = shared.load_json(export_path)
    backend = export.get("backend_record", {})
    prefix = failure["usable_prefix_rows"]
    if (
        export.get("schema") != "experiment.export/v1"
        or export.get("protocol", {}).get("sha256") != protocol_sha
        or export.get("protocol", {}).get("protocol_id") != protocol["protocol_id"]
        or export.get("protocol", {}).get("version") != protocol["version"]
        or export.get("source", {}).get("commit") != source_commit
        or len(export.get("runs", [])) != EXPECTED_ROWS
        or backend.get("completion_status") != "mechanical_failure"
        or backend.get("planned_rows") != EXPECTED_ROWS
        or backend.get("usable_prefix_rows") != prefix
        or backend.get("failure_record_sha256") != shared.sha256(failure_path)
    ):
        raise ValueError("mechanical-failure export binding mismatch")
    if not isinstance(export.get("created"), str) or not export["created"]:
        raise ValueError("mechanical-failure export creation timestamp is malformed")
    expected_export = export_core.produce_failure(
        run,
        protocol_sha,
        source_commit,
        export_path,
        failure_path,
        created=export["created"],
        rewrite_failure_receipt=False,
    )
    if export != expected_export:
        raise ValueError("mechanical-failure export differs from exact raw recomputation")
    schedule: list[dict[str, Any]] = []
    sequence = 0
    for case_index, case in enumerate(EXPECTED_CASES, 1):
        rounds = [(True, value) for value in range(1, 4)]
        rounds.extend((False, value) for value in range(1, 21))
        for warmup, replicate in rounds:
            for position, arm in enumerate(ORDER_CYCLE[(replicate - 1) % 4], 1):
                sequence += 1
                kind = "warmup" if warmup else "measured"
                schedule.append(
                    {
                        "run_id": (
                            f"{sequence:04d}_{kind}_case{case_index:02d}_r{replicate:02d}_"
                            f"p{position}_{arm}"
                        ),
                        "arm": arm,
                        "instance_id": str(case_index - 1),
                        "replicate": replicate - 1,
                        "warmup": warmup,
                    }
                )
    for index, (observed, planned) in enumerate(zip(export["runs"], schedule, strict=True)):
        if any(observed.get(key) != value for key, value in planned.items()):
            raise ValueError("mechanical-failure export schedule mismatch")
        if index >= prefix and (
            observed.get("status") != "infra_error"
            or observed.get("outcome_class") != "not_completed"
            or observed.get("attempts") != 1
            or observed.get("artifacts") != []
            or observed.get("measurements", {}).get("wall_valid") is not False
            or observed.get("verification", {}).get("status") != "not_run"
            or observed.get("exclusion") != {"excluded": False, "rule": None}
        ):
            raise ValueError("mechanical-failure export suffix was forged")

    rows_path = run / "campaign" / "rows.jsonl"
    if prefix:
        if not rows_path.is_file():
            raise ValueError("mechanical-failure export claims an absent raw prefix")
        try:
            raw_rows = [
                json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line
            ]
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("mechanical-failure raw prefix is malformed") from error
        if len(raw_rows) < prefix:
            raise ValueError("mechanical-failure raw prefix is shorter than reported")
        raw_prefix = raw_rows[:prefix]
        raw_schedule = export_core.expected_schedule()
        mismatches = export_core.mismatch_cells(raw_prefix)
        expected_prefix = [
            export_core.make_run(
                row,
                base=run / "campaign",
                timing_valid=False,
                mismatches=mismatches,
            )
            for row in raw_prefix
        ]
        for index, raw_row in enumerate(raw_prefix):
            if (
                any(raw_row.get(key) != value for key, value in raw_schedule[index].items())
                or raw_row.get("protocol_sha256") != protocol_sha
            ):
                raise ValueError("mechanical-failure raw prefix schedule mismatch")
            artifacts = raw_row.get("artifacts", {})
            if not isinstance(artifacts, dict) or any(
                not isinstance(artifacts.get(key), str)
                for key in ("stdout", "stderr", "metadata")
            ):
                raise ValueError("mechanical-failure raw prefix artifact paths are malformed")
            stdout_path = run / "campaign" / artifacts.get("stdout", "")
            stderr_path = run / "campaign" / artifacts.get("stderr", "")
            metadata_path = run / "campaign" / artifacts.get("metadata", "")
            if (
                not stdout_path.is_file()
                or not stderr_path.is_file()
                or not metadata_path.is_file()
                or artifacts.get("stdout_sha256") != shared.sha256(stdout_path)
                or artifacts.get("stderr_sha256") != shared.sha256(stderr_path)
                or shared.load_json(metadata_path) != raw_row
                or campaign_core.parse_output(stdout_path.read_bytes()) != raw_row.get("parsed")
                or export["runs"][index] != expected_prefix[index]
            ):
                raise ValueError("mechanical-failure raw/export prefix binding mismatch")
            exported_artifacts = export["runs"][index].get("artifacts", [])
            for artifact in exported_artifacts:
                path = export_path.parent / artifact["path"]
                if (
                    not path.is_file()
                    or path.stat().st_size != artifact["bytes"]
                    or shared.sha256(path) != artifact["sha256"]
                ):
                    raise ValueError("mechanical-failure prefix artifact mismatch")

    tool_path = tool_path.resolve()
    schema_path = tool_path.parents[1] / "schemas" / "experiment-export.v1.json"
    result = subprocess.run(
        [
            sys.executable, str(tool_path), "check-export", str(export_path),
            "--protocol", str(protocol_path), "--verify-files",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError("canonical failure export validation failed:\n" + result.stdout)
    return {
        "path": "campaign/export.json",
        "sha256": shared.sha256(export_path),
        "runs": EXPECTED_ROWS,
        "usable_prefix_rows": prefix,
        "failure_sha256": shared.sha256(failure_path),
        "canonical_validator_sha256": shared.sha256(tool_path),
        "canonical_schema_sha256": shared.sha256(schema_path),
        "canonical_check": result.stdout.strip(),
    }


def expected_controller_argv(planned: dict[str, Any]) -> list[str]:
    source = planned["source"]
    return [
        "python3",
        "cloud/runpod_http_batch.py",
        "go-peer-key-ab-aa-v9",
        "--cpu",
        "32",
        "--cpu-flavor",
        "cpu3c",
        "--cpu-memory",
        "64",
        "--cloud",
        "SECURE",
        "--image",
        "runpod/base:1.0.2-ubuntu2404",
        "--disk",
        "60",
        "--max-hours",
        "8",
        "--wait",
        "900",
        "--source-ref",
        EXPECTED_SOURCE_REF,
        "--source-commit",
        source["commit"],
        "--out",
        EXPECTED_OUTPUT,
        "--receipt",
        "/workspace/.benchmarks/performance-saturation/go/peer-key-ab-aa-v9/http-receipt.json",
        "--archive",
        "/workspace/.benchmarks/performance-saturation/go/peer-key-ab-aa-v9/result.tar.gz",
        "--timeout",
        "25200",
        "--max-result-mib",
        "128",
        "--max-price",
        "1.0",
        "--",
        *EXPECTED_COMMAND_TEMPLATE.split(),
    ]


def verify_launch_contract(protocol: dict[str, Any]) -> dict[str, Any]:
    planned = protocol["extensions"]["remote_execution"]
    source = planned.get("source", {})
    if (
        planned.get("protocol_hash_token") != PROTOCOL_HASH_TOKEN
        or planned.get("command_template") != EXPECTED_COMMAND_TEMPLATE
        or planned.get("output") != EXPECTED_OUTPUT
        or planned.get("image") != "runpod/base:1.0.2-ubuntu2404"
        or planned.get("container_disk_gb") != 60
        or planned.get("max_price_usd_per_hour") != 1.0
        or planned.get("request_startup_sha256") != EXPECTED_STARTUP_SHA256
        or planned.get("build_test_environment")
        != {
            "inherit_provider_environment": False,
            "fixed": EXPECTED_BUILD_ENVIRONMENT_FIXED,
            "dynamic_paths": EXPECTED_BUILD_DYNAMIC_PATHS,
            "shared_by": ["baseline build", "candidate build", "baseline tests", "candidate tests"],
        }
        or planned.get("controller_launch_argv") != expected_controller_argv(planned)
        or planned.get("request_environment_keys") != EXPECTED_REQUEST_ENVIRONMENT_KEYS
        or source.get("origin") != EXPECTED_SOURCE_ORIGIN
        or source.get("ref") != EXPECTED_SOURCE_REF
        or re.fullmatch(r"[0-9a-f]{40}", str(source.get("commit", ""))) is None
        or re.fullmatch(r"[0-9a-f]{40,64}", str(source.get("tree", ""))) is None
        or re.fullmatch(r"[0-9a-f]{64}", str(source.get("archive_sha256", ""))) is None
        or type(source.get("archive_bytes")) is not int
        or source["archive_bytes"] <= 0
        or planned.get("result_size_budget")
        != {
            "scientific_output_bytes": 96_000_000,
            "transport_overhead_bytes": 8_000_000,
            "controller_max_result_mib": 128,
            "bulk_archives_retained": False,
        }
    ):
        raise ValueError("frozen controller launch/source/output contract mismatch")
    return {
        "source_commit": source["commit"],
        "source_tree": source["tree"],
        "source_archive_sha256": source["archive_sha256"],
        "source_archive_bytes": source["archive_bytes"],
        "output": EXPECTED_OUTPUT,
        "max_result_mib": 128,
    }


def verify_transport(receipt: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    planned = protocol["extensions"]["remote_execution"]
    launch = verify_launch_contract(protocol)
    expected_top_keys = {
        "schema", "provider_actions", "source", "command", "command_sha256",
        "outputs", "request", "transport", "cpu_guard", "started_at", "pod",
        "remote_status", "result", "cleanup", "error", "finished_at",
    }
    if set(receipt) != expected_top_keys or receipt.get("error") is not None:
        raise ValueError("transport receipt terminal schema/error mismatch")
    if (
        receipt.get("schema") != "runpod.http-batch.receipt/v1"
        or not isinstance(receipt.get("started_at"), str)
        or not isinstance(receipt.get("finished_at"), str)
    ):
        raise ValueError("transport receipt identity/timestamps are malformed")
    token = planned["protocol_hash_token"]
    template = planned["command_template"]
    if template.count(token) != 1:
        raise ValueError("remote command template must contain one protocol-hash token")
    expected_command = template.replace(token, protocol["freeze"]["protocol_sha256"])
    command_sha256 = hashlib.sha256(expected_command.encode("utf-8")).hexdigest()
    if receipt.get("command") != expected_command:
        raise ValueError("transport command differs from frozen template")
    if receipt.get("command_sha256") != command_sha256:
        raise ValueError("transport command SHA-256 mismatch")
    if receipt.get("outputs") != [planned["output"]]:
        raise ValueError("transport output inventory mismatch")
    if receipt.get("provider_actions") is not True:
        raise ValueError("transport did not record the single provider action path")
    if receipt.get("transport") != planned["transport"]:
        raise ValueError("transport mechanism mismatch")

    source = receipt.get("source", {})
    if set(source) != {
        "origin", "ref", "commit", "tree", "archive_sha256",
        "public_ref_checked", "public_checked_at",
    }:
        raise ValueError("transport source receipt schema mismatch")
    for key in ("origin", "ref", "commit", "tree"):
        if source.get(key) != planned["source"][key]:
            raise ValueError(f"transport source identity mismatch: {key}")
    if source.get("public_ref_checked") is not True or not isinstance(
        source.get("public_checked_at"), str
    ):
        raise ValueError("transport did not verify the dedicated public source ref")
    archive_sha = source.get("archive_sha256")
    if archive_sha != launch["source_archive_sha256"]:
        raise ValueError("source archive SHA-256 differs from the frozen launch")

    request = receipt.get("request", {})
    expected_request = {
        "cloudType": "SECURE",
        "computeType": "CPU",
        "containerDiskInGb": planned["container_disk_gb"],
        "cpuFlavorIds": ["cpu3c"],
        "cpuFlavorPriority": "custom",
        "environment_keys": planned["request_environment_keys"],
        "gpuCount": None,
        "gpuTypeIds": None,
        "imageName": planned["image"],
        "minRAMPerGPU": None,
        "minVCPUPerGPU": None,
        "ports": ["8888/http"],
        "secrets_redacted": True,
        "startup_sha256": EXPECTED_STARTUP_SHA256,
        "vcpuCount": 32,
        "name": request.get("name"),
    }
    if request != expected_request:
        raise ValueError("RunPod request differs from frozen CPU request")
    name = request.get("name")
    if not isinstance(name, str) or re.fullmatch(
        re.escape(planned["pod_name_prefix"]) + r"[0-9a-f]{12}", name
    ) is None:
        raise ValueError("RunPod job name/nonce mismatch")

    pod = receipt.get("pod", {})
    expected_pod_keys = {
        "cloud", "cost", "cpu", "createdAt", "creation_response_ambiguous",
        "cudaVersion", "dataCenterId", "gpu", "id", "image", "name",
        "startedAt", "status",
    }
    cost = pod.get("cost")
    if (
        set(pod) != expected_pod_keys
        or pod.get("name") != name
        or pod.get("cloud") != "SECURE"
        or pod.get("cpu") != {"id": "cpu3c", "memory": 64, "vcpuCount": 32}
        or pod.get("image") != planned["image"]
        or pod.get("gpu") is not None
        or pod.get("cudaVersion") is not None
        or pod.get("creation_response_ambiguous") is not False
        or not isinstance(cost, (int, float))
        or isinstance(cost, bool)
        or not math.isfinite(cost)
        or not 0 < cost <= planned["max_price_usd_per_hour"]
        or re.fullmatch(r"[A-Za-z0-9_-]{3,128}", str(pod.get("id", ""))) is None
        or pod.get("status") != "RUNNING"
        or not isinstance(pod.get("createdAt"), str)
        or not isinstance(pod.get("startedAt"), str)
        or not isinstance(pod.get("dataCenterId"), str)
        or not pod["dataCenterId"]
    ):
        raise ValueError("observed RunPod placement differs from frozen request")

    remote = receipt.get("remote_status", {})
    expected_remote_keys = {
        "archive", "archive_ready", "chunks", "command_sha256",
        "command_started_unix", "done", "finished_unix", "hardware", "job_id",
        "returncode", "schema", "source_archive_sha256", "source_commit",
        "source_tree", "stage", "started_unix", "timed_out", "worker_error_type",
    }
    numeric_times = (
        remote.get("started_unix"), remote.get("command_started_unix"),
        remote.get("finished_unix"),
    )
    if (
        set(remote) != expected_remote_keys
        or remote.get("schema") != "runpod.http-batch.status/v1"
        or remote.get("stage") != "complete"
        or remote.get("done") is not True
        or remote.get("archive_ready") is not True
        or remote.get("timed_out") is not False
        or remote.get("worker_error_type") is not None
        or type(remote.get("returncode")) is not int
        or remote["returncode"] not in {0, 1, 2}
        or any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value <= 0
            for value in numeric_times
        )
        or not (numeric_times[0] <= numeric_times[1] <= numeric_times[2])
        or remote.get("command_sha256") != command_sha256
        or remote.get("source_archive_sha256") != archive_sha
        or remote.get("source_commit") != planned["source"]["commit"]
        or remote.get("source_tree") != planned["source"]["tree"]
        or remote.get("job_id") != name
        or set(remote.get("hardware", {})) != {"pod_id", "gpus", "nvcc"}
        or remote.get("hardware", {}).get("pod_id") != pod["id"]
        or remote.get("hardware", {}).get("gpus") != []
        or not isinstance(remote.get("hardware", {}).get("nvcc"), str)
    ):
        raise ValueError("remote worker source/command/hardware binding mismatch")
    remote_archive = remote.get("archive", {})
    sha_pattern = r"[0-9a-f]{64}"
    if (
        not isinstance(remote_archive, dict)
        or set(remote_archive) != {
            "bytes", "files", "manifest_sha256", "sha256", "uncompressed_bytes"
        }
        or type(remote_archive.get("bytes")) is not int
        or not 0 < remote_archive["bytes"] <= 128 * 1024 * 1024
        or type(remote_archive.get("files")) is not int
        or remote_archive["files"] <= 0
        or type(remote_archive.get("uncompressed_bytes")) is not int
        or not 0 < remote_archive["uncompressed_bytes"] <= 104_000_000
        or re.fullmatch(sha_pattern, str(remote_archive.get("sha256", ""))) is None
        or re.fullmatch(sha_pattern, str(remote_archive.get("manifest_sha256", ""))) is None
    ):
        raise ValueError("remote result exceeds the frozen output-size budget")
    chunks = remote.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("remote result chunk inventory is absent")
    offset = total = 0
    for index, chunk in enumerate(chunks):
        if (
            not isinstance(chunk, dict)
            or set(chunk) != {"bytes", "index", "offset", "path", "sha256"}
            or chunk.get("index") != index
            or chunk.get("offset") != offset
            or chunk.get("path") != f"/v1/result/{index:06d}"
            or type(chunk.get("bytes")) is not int
            or not 0 < chunk["bytes"] <= 4_194_304
            or re.fullmatch(sha_pattern, str(chunk.get("sha256", ""))) is None
        ):
            raise ValueError("remote result chunk inventory is malformed")
        offset += chunk["bytes"]
        total += chunk["bytes"]
    if total != remote_archive["bytes"]:
        raise ValueError("remote result chunks do not cover the archive")

    result = receipt.get("result", {})
    expected_archive_path = planned["controller_archive_path"]
    expected_metadata_path = str(Path(planned["controller_receipt_path"]).with_suffix(".remote"))
    if (
        not isinstance(result, dict)
        or set(result) != {
            "archive", "archive_bytes", "archive_sha256", "metadata", "files"
        }
        or result.get("archive") != expected_archive_path
        or result.get("metadata") != expected_metadata_path
        or result.get("archive_bytes") != remote_archive["bytes"]
        or result.get("archive_sha256") != remote_archive["sha256"]
        or not isinstance(result.get("files"), list)
        # The server's count includes .runpod-batch/files.sha256; the verified
        # extraction inventory intentionally omits that self-authenticating
        # manifest and retains every member it names.
        or len(result["files"]) != remote_archive["files"] - 1
        or any(
            not isinstance(record, dict)
            or set(record) != {"bytes", "path", "sha256"}
            or type(record.get("bytes")) is not int
            or record["bytes"] < 0
            or not isinstance(record.get("path"), str)
            or not record["path"]
            or re.fullmatch(sha_pattern, str(record.get("sha256", ""))) is None
            for record in result["files"]
        )
    ):
        raise ValueError("downloaded result receipt differs from remote archive")
    if receipt.get("cleanup") != {
        "absence_verified": True,
        "delete_requested": True,
        "id": pod["id"],
    }:
        raise ValueError("transport cleanup receipt mismatch")
    return {
        "pod_id": pod["id"],
        "pod_name": name,
        "source_commit": source["commit"],
        "source_tree": source["tree"],
        "source_archive_sha256": archive_sha,
        "command_sha256": command_sha256,
        "provider_actions": receipt["provider_actions"],
        "output": planned["output"],
        "source_archive_bytes": launch["source_archive_bytes"],
        "result_uncompressed_bytes": remote_archive["uncompressed_bytes"],
    }


def _topology_order(affinity: list[int], topology: list[dict[str, Any]]) -> list[int]:
    by_cpu = {row.get("cpu"): row for row in topology}
    if set(by_cpu) != set(affinity) or len(by_cpu) != len(topology):
        raise ValueError("CPU topology does not cover affinity exactly once")

    def value(row: dict[str, Any], key: str) -> int:
        item = row.get(key)
        return item if type(item) is int and item >= 0 else 1 << 62

    return sorted(
        affinity,
        key=lambda cpu: (
            value(by_cpu[cpu], "package"),
            value(by_cpu[cpu], "die"),
            value(by_cpu[cpu], "numa"),
            value(by_cpu[cpu], "core"),
            cpu,
        ),
    )


def _parse_cpu_set(text: object) -> set[int]:
    if not isinstance(text, str) or not text:
        return set()
    cpus: set[int] = set()
    try:
        for field in text.split(","):
            if "-" in field:
                left, right = field.split("-", 1)
                cpus.update(range(int(left), int(right) + 1))
            else:
                cpus.add(int(field))
    except ValueError:
        return set()
    return cpus


def stable_placement_identity(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Recompute the allowlisted placement identity from raw host fields."""

    model = snapshot.get("cpu_model")
    logical_cpus = snapshot.get("logical_cpus")
    affinity = snapshot.get("affinity")
    raw_topology = snapshot.get("cpu_topology")
    order = snapshot.get("topology_order")
    cpuset = snapshot.get("cpuset_cpus")
    memory_max = snapshot.get("memory_max")
    devices = snapshot.get("nvidia_devices")
    if not isinstance(model, str) or not model.strip():
        raise ValueError("stable placement requires a nonempty CPU model")
    if type(logical_cpus) is not int or logical_cpus <= 0:
        raise ValueError("stable placement requires a positive logical CPU count")
    if (
        not isinstance(affinity, list)
        or not affinity
        or any(type(cpu) is not int or cpu < 0 for cpu in affinity)
        or len(set(affinity)) != len(affinity)
        or logical_cpus < len(affinity)
    ):
        raise ValueError("stable placement affinity is malformed")
    if not isinstance(raw_topology, list) or len(raw_topology) != len(affinity):
        raise ValueError("stable placement topology is malformed")
    topology: list[dict[str, Any]] = []
    for raw in raw_topology:
        if not isinstance(raw, dict):
            raise ValueError("stable placement topology row is malformed")
        row = {field: raw.get(field) for field in STABLE_TOPOLOGY_FIELDS}
        if type(row["cpu"]) is not int or row["cpu"] < 0:
            raise ValueError("stable placement topology CPU is malformed")
        for field in ("package", "die", "numa", "core"):
            if row[field] is not None and (
                type(row[field]) is not int or row[field] < 0
            ):
                raise ValueError(f"stable placement topology {field} is malformed")
        if row["thread_siblings"] is not None and not isinstance(
            row["thread_siblings"], str
        ):
            raise ValueError("stable placement thread-sibling set is malformed")
        topology.append(row)
    if {row["cpu"] for row in topology} != set(affinity):
        raise ValueError("stable placement topology does not cover affinity")
    if (
        not isinstance(order, list)
        or any(type(cpu) is not int or cpu < 0 for cpu in order)
        or len(order) != len(affinity)
        or set(order) != set(affinity)
        or order != _topology_order(affinity, topology)
    ):
        raise ValueError("stable placement topology order is malformed")
    if _parse_cpu_set(cpuset) != set(affinity):
        raise ValueError("stable placement cgroup cpuset differs from affinity")
    if not isinstance(memory_max, str) or re.fullmatch(r"[1-9][0-9]*", memory_max) is None:
        raise ValueError("stable placement memory limit is malformed")
    if (
        not isinstance(devices, list)
        or any(not isinstance(path, str) or not path for path in devices)
        or len(set(devices)) != len(devices)
    ):
        raise ValueError("stable placement GPU inventory is malformed")
    return {
        "schema": STABLE_PLACEMENT_SCHEMA,
        "cpu_model": model.strip(),
        "logical_cpus": logical_cpus,
        "affinity": list(affinity),
        "cpu_topology": topology,
        "topology_order": list(order),
        "cpuset_cpus": sorted(_parse_cpu_set(cpuset)),
        "memory_limit_bytes": int(memory_max),
        "nvidia_devices": sorted(devices),
    }


def stable_placement_sha256(identity: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(
        identity, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")).hexdigest()


def stable_placement_snapshot_valid(snapshot: dict[str, Any]) -> bool:
    try:
        identity = stable_placement_identity(snapshot)
    except (KeyError, TypeError, ValueError):
        return False
    return (
        snapshot.get("placement_identity") == identity
        and snapshot.get("placement_identity_sha256")
        == stable_placement_sha256(identity)
    )


def stable_placement_unchanged(*snapshots: dict[str, Any]) -> bool:
    if not snapshots or not all(stable_placement_snapshot_valid(item) for item in snapshots):
        return False
    identity = snapshots[0]["placement_identity"]
    digest = snapshots[0]["placement_identity_sha256"]
    return all(
        item["placement_identity"] == identity
        and item["placement_identity_sha256"] == digest
        for item in snapshots[1:]
    )


def _verify_restoration(
    restoration: dict[str, Any], reservation: dict[str, Any], expected_affinity: list[int]
) -> bool:
    records = restoration.get("records")
    count_keys = ("attempted", "restored", "exited", "failures")
    if (
        not isinstance(records, list)
        or any(type(restoration.get(key)) is not int or restoration[key] < 0 for key in count_keys)
        or restoration.get("attempted") != len(records)
        or expected_affinity != sorted(set(expected_affinity))
        or any(type(cpu) is not int or cpu < 0 for cpu in expected_affinity)
    ):
        raise ValueError("reservation restoration inventory mismatch")
    tids: set[int] = set()
    restored = exited = failures = 0
    reservation_cpus = reservation.get("cpus")
    if (
        not isinstance(reservation_cpus, list)
        or reservation_cpus != sorted(set(reservation_cpus))
        or not reservation_cpus
        or any(type(cpu) is not int or cpu < 0 for cpu in reservation_cpus)
        or not set(reservation_cpus) < set(expected_affinity)
        or type(reservation.get("threads_moved")) is not int
        or reservation["threads_moved"] < 0
    ):
        raise ValueError("reservation CPU/count domain mismatch")
    reserved = set(reservation_cpus)
    allowed = set(expected_affinity)
    for record in records:
        if (
            not isinstance(record, dict)
            or type(record.get("pid")) is not int
            or record["pid"] <= 0
            or type(record.get("tid")) is not int
            or record["tid"] <= 0
            or type(record.get("starttime_ticks")) is not int
            or record["starttime_ticks"] <= 0
            or record["tid"] in tids
        ):
            raise ValueError("restoration thread identity is malformed")
        tids.add(record["tid"])
        affinity = record.get("affinity")
        evicted = record.get("evicted_affinity")
        if (
            not isinstance(affinity, list)
            or not isinstance(evicted, list)
            or affinity != sorted(set(affinity))
            or evicted != sorted(set(evicted))
            or not affinity
            or not evicted
            or any(type(cpu) is not int or cpu < 0 for cpu in affinity + evicted)
            or not set(affinity) <= allowed
            or set(evicted) != set(affinity) - reserved
            or not reserved.intersection(affinity)
            or reserved.intersection(evicted)
        ):
            raise ValueError("restoration affinity provenance mismatch")
        status = record.get("status")
        if status == "restored":
            restored += 1
            if set(record) != {
                "pid", "tid", "starttime_ticks", "affinity", "evicted_affinity",
                "status", "restored_affinity",
            } or record.get("restored_affinity") != affinity:
                raise ValueError("restoration readback mismatch")
        elif status == "exited":
            exited += 1
            if set(record) != {
                "pid", "tid", "starttime_ticks", "affinity", "evicted_affinity", "status"
            }:
                raise ValueError("exited restoration record has unexpected fields")
        elif status == "error":
            failures += 1
            if (
                set(record) != {
                    "pid", "tid", "starttime_ticks", "affinity", "evicted_affinity",
                    "status", "errno",
                }
                or type(record.get("errno")) is not int
                or record["errno"] <= 0
            ):
                raise ValueError("restoration error record is malformed")
        elif status == "identity_mismatch":
            failures += 1
            if set(record) != {
                "pid", "tid", "starttime_ticks", "affinity", "evicted_affinity", "status"
            }:
                raise ValueError("restoration identity record is malformed")
        elif status == "readback_mismatch":
            failures += 1
            readback = record.get("restored_affinity")
            if (
                set(record) != {
                    "pid", "tid", "starttime_ticks", "affinity", "evicted_affinity",
                    "status", "restored_affinity",
                }
                or not isinstance(readback, list)
                or readback != sorted(set(readback))
                or any(type(cpu) is not int or cpu < 0 for cpu in readback)
            ):
                raise ValueError("restoration readback-mismatch record is malformed")
        else:
            raise ValueError("unknown restoration status")
    passes = bool(
        restoration.get("attempted") == reservation.get("threads_moved")
        and restoration.get("restored") == restored
        and restoration.get("exited") == exited
        and restoration.get("failures") == failures
        and restoration["restored"] + restoration["exited"] + restoration["failures"]
        == restoration["attempted"]
        and restoration.get("runner_affinity_after_restore") == expected_affinity
        and restoration.get("runner_affinity_passes") is True
        and failures == 0
    )
    if restoration.get("passes") is not passes:
        raise ValueError("restoration pass receipt mismatch")
    return passes


def verify_isolation(
    run: Path,
    rows: list[dict[str, Any]],
    isolation: dict[str, Any],
    receipt: dict[str, Any],
    build_manifest: dict[str, Any],
) -> dict[str, Any]:
    if receipt.get("cpu_guard") != EXPECTED_CPU_GUARD:
        raise ValueError("transport CPU placement mismatch")
    manifest = shared.load_json(run / "campaign" / "manifest.json")
    summary = shared.load_json(run / "campaign" / "summary.json")
    placement = isolation.get("placement")
    initial = build_manifest["host"]
    if not isinstance(placement, dict):
        raise ValueError("placement receipt is malformed")
    allowed = placement.get("allowed_cpus")
    topology = initial.get("cpu_topology")
    if (
        not isinstance(allowed, list)
        or len(allowed) != 32
        or len(set(allowed)) != 32
        or any(type(cpu) is not int or cpu < 0 for cpu in allowed)
        or not isinstance(topology, list)
    ):
        raise ValueError("placement CPU inventory mismatch")
    order = _topology_order(allowed, topology)
    by_cpu = {row["cpu"]: row for row in topology}
    eligible: list[tuple[int, list[int]]] = []
    for cpu in order:
        siblings = l2_core.parse_cpu_list(by_cpu[cpu].get("thread_siblings") or "")
        if (
            siblings
            and cpu in siblings
            and siblings <= set(allowed)
            and 0 not in siblings
            and set(allowed) - siblings
        ):
            eligible.append((cpu, sorted(siblings)))
    if not eligible:
        raise ValueError("no eligible complete non-CPU0 SMT core")
    expected_placement = {
        "policy": EXPECTED_AFFINITY_POLICY,
        "allowed_cpus": allowed,
        "topology_order": order,
        "benchmark_cpus": [eligible[0][0]],
        "reservation_cpus": eligible[0][1],
        "memory_limit_bytes": EXPECTED_MEMORY_BYTES,
    }
    exact_placement = build_manifest.get("placement") == placement == expected_placement
    before, after = isolation.get("before"), isolation.get("after")
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError("session isolation snapshots are absent")
    initial_identity = initial.get("placement_identity")
    exact_placement = bool(
        exact_placement
        and stable_placement_unchanged(initial, before, after)
        and isinstance(initial_identity, dict)
        and initial_identity.get("affinity") == allowed
        and initial_identity.get("cpu_topology") == [
            {field: row.get(field) for field in STABLE_TOPOLOGY_FIELDS}
            for row in topology
        ]
        and initial_identity.get("topology_order") == order
        and initial_identity.get("cpuset_cpus") == sorted(allowed)
        and initial_identity.get("memory_limit_bytes") == EXPECTED_MEMORY_BYTES
        and initial_identity.get("nvidia_devices") == []
    )
    reservation = manifest.get("reservation")
    if (
        not isinstance(reservation, dict)
        or reservation.get("cpus") != eligible[0][1]
        or reservation.get("smt_siblings") != eligible[0][1]
        or reservation.get("evicted") is not True
        or type(reservation.get("threads_moved")) is not int
        or reservation["threads_moved"] < 0
        or not isinstance(reservation.get("left_on_reserved"), dict)
    ):
        raise ValueError("whole-core reservation receipt mismatch")
    restoration = summary.get("restoration")
    if not isinstance(restoration, dict) or isolation.get("restoration") != restoration:
        raise ValueError("restoration receipt is not consistently bound")
    restoration_passes = _verify_restoration(restoration, reservation, allowed)
    lock_receipt = manifest.get("session_lock")
    if (
        not isinstance(lock_receipt, dict)
        or lock_receipt.get("path") != "/tmp/crypto-bench.lock"
        or lock_receipt.get("exclusive") is not True
        or lock_receipt.get("nonblocking") is not True
        or type(lock_receipt.get("device")) is not int
        or type(lock_receipt.get("inode")) is not int
        or type(lock_receipt.get("owner_pid")) is not int
        or summary.get("session_lock") != lock_receipt
        or isolation.get("session_lock") != lock_receipt
    ):
        raise ValueError("exclusive session-lock receipt mismatch")
    preflight = manifest.get("preflight")
    preflight_result = l2_core.evaluate_preflight(preflight)
    preflight_passes = bool(
        isolation.get("preflight") == preflight and preflight_result["passes"]
    )
    l2_failures = 0
    blocking: dict[str, int] = {}
    for row in rows:
        execution = row.get("execution")
        if not isinstance(execution, dict) or row.get("instrumentation_error") is not None:
            raise ValueError(f"row {row.get('sequence')} execution receipt is malformed")
        expected_rusage = {
            "user_seconds": execution.get("rusage", {}).get("user_s"),
            "system_seconds": execution.get("rusage", {}).get("sys_s"),
            "max_rss_kib": execution.get("rusage", {}).get("maxrss_kib"),
            "minor_faults": execution.get("rusage", {}).get("minflt"),
            "major_faults": execution.get("rusage", {}).get("majflt"),
            "voluntary_context_switches": execution.get("rusage", {}).get("nvcsw"),
            "involuntary_context_switches": execution.get("rusage", {}).get("nivcsw"),
        }
        if (
            row.get("outer_wall_ns") != execution.get("wall_ns")
            or row.get("exit_status") != execution.get("exit", {}).get("returncode")
            or row.get("timed_out") != execution.get("exit", {}).get("timed_out")
            or execution.get("exit", {}).get("signal") is not None
            or row.get("rusage") != expected_rusage
            or execution.get("pinned_cpus") != placement["benchmark_cpus"]
            or execution.get("reserved_cpus") != placement["reservation_cpus"]
        ):
            raise ValueError(f"row {row['sequence']} raw execution binding mismatch")
        recomputed = l2_core.evaluate_l2(execution, preflight, reservation)
        if row.get("isolation") != recomputed:
            raise ValueError(f"row {row['sequence']} L2 receipt differs from raw recomputation")
        l2_failures += int(not recomputed["passes"])
        for name in recomputed["blocking"]:
            blocking[name] = blocking.get(name, 0) + 1
    cpu_deltas = counter_deltas(before["cpu_stat"], after["cpu_stat"])
    memory_deltas = counter_deltas(before["memory_events"], after["memory_events"])
    throttle_delta = cpu_deltas.get("nr_throttled")
    global_steal_zero = (
        type(before.get("steal_ticks")) is int
        and before["steal_ticks"] == after.get("steal_ticks")
    )
    passes = bool(
        exact_placement
        and preflight_passes
        and restoration_passes
        and l2_failures == 0
        and global_steal_zero
        and throttle_delta == 0
        and all(delta == 0 for delta in memory_deltas.values())
    )
    reported = {
        "rows": len(rows),
        "rows_passing_l2": len(rows) - l2_failures,
        "rows_failing_l2": l2_failures,
        "l2_blocking_counts": dict(sorted(blocking.items())),
        "cgroup_nr_throttled_delta": throttle_delta,
        "memory_event_deltas": memory_deltas,
        "placement_unchanged": exact_placement,
        "timing_valid": passes,
    }
    for key, value in reported.items():
        if isolation.get(key) != value:
            raise ValueError(f"runner isolation field disagrees with analyzer: {key}")
    if (
        isolation.get("schema") != "go-coordinator-remote-isolation/v2"
        or isolation.get("required_level") != "L2"
        or isolation.get("l2_thresholds") != l2_core.THRESHOLDS
        or summary.get("l2_failures") != l2_failures
    ):
        raise ValueError("cumulative L2 aggregate contract mismatch")
    return {
        "passes": passes,
        "exact_placement": exact_placement,
        "provider_cpu_guard": receipt["cpu_guard"],
        "preflight": preflight_result,
        "restoration_passes": restoration_passes,
        "global_steal_zero": global_steal_zero,
        "rows_passing_l2": len(rows) - l2_failures,
        "rows_failing_l2": l2_failures,
        "l2_blocking_counts": dict(sorted(blocking.items())),
        "cgroup_nr_throttled_delta": throttle_delta,
        "memory_event_deltas": memory_deltas,
    }


def analyze(options: argparse.Namespace) -> dict[str, Any]:
    run = options.run.resolve()
    protocol_path = options.protocol.resolve()
    receipt_path = options.receipt.resolve()
    archive_path = options.archive.resolve()
    protocol = load_json_file(protocol_path)
    protocol_identity = verify_frozen_protocol(
        protocol_path, protocol, options.protocol_tool
    )
    protocol_sha256 = protocol["freeze"]["protocol_sha256"]
    expected_analysis_script = {
        "path": Path(__file__).name,
        "sha256": raw_sha256(Path(__file__).resolve()),
    }
    if protocol["analysis_plan"]["script"] != expected_analysis_script:
        raise ValueError("protocol analysis script SHA-256 mismatch")
    dependencies = bind_verified_dependencies(protocol)
    receipt = shared.load_json(receipt_path)
    if receipt.get("schema") != "runpod.http-batch.receipt/v1":
        raise ValueError("unexpected transport receipt schema")
    if receipt.get("remote_status", {}).get("timed_out"):
        raise ValueError("remote job timed out")
    if receipt.get("cleanup") != {
        "absence_verified": True,
        "delete_requested": True,
        "id": receipt.get("pod", {}).get("id"),
    }:
        raise ValueError("transport cleanup binding is incomplete")
    transport = verify_transport(receipt, protocol)
    archive = shared.verify_archive(archive_path, receipt)
    extracted_run = verify_extracted_run(run, receipt, EXPECTED_OUTPUT)
    summary_path = run / "remote-summary.json"
    summary = shared.load_json(summary_path)
    if summary.get("status") == "mechanical_failure":
        if receipt.get("remote_status", {}).get("returncode") != 2:
            raise ValueError("sealed mechanical failure must exit exactly 2")
        failure_export = verify_failure_export(
            run, protocol_path, protocol, summary, options.protocol_tool
        )
        export_doc = shared.load_json(run / "campaign" / "export.json")
        return {
            "schema": SCHEMA,
            "protocol_sha256": protocol_sha256,
            "protocol": protocol_identity,
            "analysis": {
                "script": expected_analysis_script["path"],
                "script_sha256": expected_analysis_script["sha256"],
                "status": "preregistered_deterministic",
                "verified_dependencies": dependencies,
            },
            "inputs": {
                "protocol_file_sha256": shared.sha256(protocol_path),
                "receipt_sha256": shared.sha256(receipt_path),
                "archive_sha256": archive["sha256"],
                "archive_manifest_sha256": archive["manifest_sha256"],
                "remote_summary_sha256": shared.sha256(summary_path),
                "failure_sha256": failure_export["failure_sha256"],
                "export_sha256": failure_export["sha256"],
            },
            "transport": transport,
            "adherence": {
                "archive_bound_run": extracted_run,
                "frozen_schedule": {
                    "rows": EXPECTED_ROWS,
                    "usable_prefix_rows": failure_export["usable_prefix_rows"],
                    "status": "failure_total",
                },
                "export": failure_export,
            },
            "flow": {
                **export_doc["flow"],
                "remote_returncode": 2,
                "mechanically_complete": False,
            },
            "correctness": {
                "passes": None,
                "status": "not_evaluated",
                "rule": "mechanical completeness precedes every scientific claim",
            },
            "isolation": {"passes": None, "status": "not_evaluated"},
            "inference": {"status": "not_evaluated"},
            "cases": [],
            "claims": claim_statuses(
                complete=False,
                correctness=False,
                allocation=False,
                timing_numeric=False,
                timing_isolation=False,
            ),
            "verdict": {
                "overall": "inconclusive",
                "reason": "sealed mechanical failure",
                "allocation_gate_passes": None,
                "timing_numeric_gate_passes": None,
                "aa_calibration_gate_passes": None,
                "timing_l2_gate_passes": None,
                "timing_control_gate_passes": None,
                "timing_claim_status": "not_evaluated",
            },
        }
    rows, inventory = load_verified_rows(run, protocol)
    schedule = verify_frozen_schedule(run, rows, protocol)
    tests = verify_tests(run, protocol_sha256)
    build = verify_build(run, protocol, inventory["arms"], transport)
    if (
        tests["environment"] != build["manifest"].get("build_environment")
        or tests["environment_sha256"] != build["environment_sha256"]
    ):
        raise ValueError("build and test commands did not share one exact environment")
    isolation_path = run / "isolation.json"
    isolation_record = shared.load_json(isolation_path)
    expected_summary_hashes = {
        "build_manifest_sha256": build["manifest_sha256"],
        "tests_manifest_sha256": tests["manifest_sha256"],
        "campaign_rows_sha256": inventory["rows_sha256"],
        "isolation_sha256": shared.sha256(isolation_path),
    }
    if summary.get("protocol_sha256") != protocol_sha256:
        raise ValueError("remote summary protocol SHA-256 mismatch")
    for key, value in expected_summary_hashes.items():
        if summary.get(key) != value:
            raise ValueError(f"remote summary {key} mismatch")
    pre_summary = {
        "files": 0,
        "bytes": 0,
    }
    for path in run.rglob("*"):
        if path.is_file() and path != summary_path:
            pre_summary["files"] += 1
            pre_summary["bytes"] += path.stat().st_size
    if (
        summary.get("schema") != "go-coordinator-remote-summary/v1"
        or summary.get("status") != "complete"
        or summary.get("output_budget_bytes") != 96_000_000
        or summary.get("output_bytes_before_summary") != pre_summary["bytes"]
        or summary.get("output_files_before_summary") != pre_summary["files"]
        or summary.get("remote_summary_reserve_bytes") != 65_536
        or pre_summary["bytes"] + 65_536 > 96_000_000
        or extracted_run["bytes"] > 96_000_000
    ):
        raise ValueError("remote summary output-size budget mismatch")
    export = verify_export(
        run,
        protocol_path,
        protocol,
        summary,
        build,
        options.protocol_tool,
    )

    correctness_cells = correctness_inventory(rows, inventory["cases"])
    matches = correctness_cells["matches"]
    mismatches = correctness_cells["mismatches"]
    correctness = mismatches == 0 and matches == EXPECTED_CORRECTNESS_CELLS
    if summary.get("fingerprint_pair_mismatches") != mismatches:
        raise ValueError("remote summary correctness count mismatch")
    if summary.get("fingerprint_mismatches_by_comparison") != {
        "all_four_or_case_invariant": mismatches
    }:
        raise ValueError("remote summary correctness detail mismatch")
    isolation = verify_isolation(run, rows, isolation_record, receipt, build["manifest"])
    if summary.get("timing_valid") != isolation["passes"]:
        raise ValueError("remote summary timing-valid field mismatch")

    remote_returncode = receipt["remote_status"]["returncode"]
    # A complete cross-arm mismatch is a scientific wrong answer even when the
    # runner deliberately exits nonzero after sealing all rows and manifests.
    campaign_returncode = summary.get("campaign_returncode")
    if type(campaign_returncode) is not int:
        raise ValueError("remote summary campaign return code is malformed")
    expected_remote_returncode = (
        1 if mismatches and campaign_returncode == 0 else campaign_returncode
    )
    if remote_returncode != expected_remote_returncode:
        raise ValueError("remote return code differs from the sealed campaign outcome")
    transport_complete = transport_is_complete(remote_returncode, mismatches)
    mechanical_complete = transport_complete and len(rows) == EXPECTED_ROWS
    cases: list[dict[str, Any]] = []
    allocation_pass = False
    ab_timing_pass = False
    aa_calibration_pass = False
    analyzed_pairs = 0
    if correctness and transport_complete:
        (
            cases,
            allocation_pass,
            ab_timing_pass,
            aa_calibration_pass,
            analyzed_pairs,
        ) = compute_case_results(rows, inventory["cases"])
    timing_control_valid = isolation["passes"] and aa_calibration_pass
    verdict = choose_verdict(
        complete=mechanical_complete,
        correctness=correctness,
        allocation=allocation_pass,
        timing_numeric=ab_timing_pass,
        timing_isolation=timing_control_valid,
    )
    return {
        "schema": SCHEMA,
        "protocol_sha256": protocol_sha256,
        "protocol": protocol_identity,
        "analysis": {
            "script": expected_analysis_script["path"],
            "script_sha256": expected_analysis_script["sha256"],
            "status": "preregistered_deterministic",
            "verified_dependencies": dependencies,
        },
        "inputs": {
            "protocol_file_sha256": shared.sha256(protocol_path),
            "receipt_sha256": shared.sha256(receipt_path),
            "archive_sha256": archive["sha256"],
            "archive_manifest_sha256": archive["manifest_sha256"],
            "build_manifest_sha256": build["manifest_sha256"],
            "tests_manifest_sha256": tests["manifest_sha256"],
            "rows_sha256": inventory["rows_sha256"],
            "isolation_sha256": shared.sha256(isolation_path),
            "remote_summary_sha256": shared.sha256(summary_path),
            "export_sha256": export["sha256"],
        },
        "transport": transport,
        "adherence": {
            "archive_bound_run": extracted_run,
            "frozen_schedule": schedule,
            "export": export,
        },
        "flow": {
            "planned": EXPECTED_ROWS,
            "completed": len(rows),
            "warmups": len(inventory["warmups"]),
            "measured": len(inventory["measured"]),
            "matching_correctness_cells": matches,
            "mismatching_correctness_cells": mismatches,
            "analyzed_pairs": analyzed_pairs,
            "remote_returncode": remote_returncode,
            "campaign_returncode": campaign_returncode,
            "mechanically_complete": mechanical_complete,
        },
        "correctness": {
            "passes": correctness,
            "rule": (
                "all four arms agree in every one of 138 warmup/measured cells and "
                "the deterministic fingerprint is invariant across all 23 rounds per case"
            ),
        },
        "isolation": isolation,
        "inference": {
            "method": "exact_empirical_paired_bootstrap_median_distribution",
            "pairs_per_case": EXPECTED_REPLICATES,
            "statistic": "average_of_bootstrap_order_statistics_10_and_11",
            "distribution": "exhaustive_joint_order_statistic_distribution",
            "probability_arithmetic": "exact_rational",
            "rng": None,
            "monte_carlo_draws": None,
            "family_alpha": "1/20",
            "timing_interval_cells": 24,
            "correction": "two_sided_bonferroni",
            "lower_quantile": "1/960",
            "upper_quantile": "959/960",
            "quantile_definition": "inf{x: CDF(x) >= q}",
            "aa_labels": "fixed prospective left/right labels; no reciprocal-orientation claim",
            "aa_equivalence_band": ["20/21", "21/20"],
            "aa_noise_factor": "max(AA upper, reciprocal AA lower)",
        },
        "cases": cases,
        "claims": claim_statuses(
            complete=mechanical_complete,
            correctness=correctness,
            allocation=allocation_pass,
            timing_numeric=ab_timing_pass,
            timing_isolation=timing_control_valid,
        ),
        "verdict": {
            "overall": verdict,
            "allocation_gate_passes": allocation_pass,
            "timing_numeric_gate_passes": ab_timing_pass,
            "aa_calibration_gate_passes": aa_calibration_pass,
            "timing_l2_gate_passes": isolation["passes"],
            "timing_control_gate_passes": timing_control_valid,
            "timing_claim_status": (
                "supported" if ab_timing_pass and timing_control_valid
                else "invalid_measurement" if not timing_control_valid
                else "unsupported"
            ),
        },
    }


def main() -> int:
    options = parse_args()
    result = analyze(options)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if options.output:
        options.output.parent.mkdir(parents=True, exist_ok=True)
        options.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
