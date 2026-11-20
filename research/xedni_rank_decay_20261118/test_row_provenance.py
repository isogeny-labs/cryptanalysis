from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import row_provenance as rp
import public_boundary
import rank_pari
import source_generator


class FixedCardinalityBackend:
    name = "test-fixed-cardinality"
    last_evidence = None

    def cardinality_and_factors(self, prime, a, b):
        if (prime, a, b) != (101, 72, 90):
            raise AssertionError((prime, a, b))
        return 92, [(2, 2), (23, 1)]


class EvidenceFixture:
    def __init__(self, root: Path):
        self.root = root
        self.artifacts: dict[str, dict] = {}

    def add(self, role: str, content) -> str:
        if isinstance(content, (dict, list)) or content is None:
            raw = rp.canonical_json(content)
            media = "application/json"
        elif isinstance(content, str):
            raw = content.encode()
            media = "text/plain"
        else:
            raw = content
            media = "application/octet-stream"
        filename = role.replace("/", "__").replace(":", "_") + ".evidence"
        path = self.root / filename
        path.write_bytes(raw)
        descriptor = rp.describe_artifact(role, filename, self.root, media)
        self.artifacts[role] = descriptor
        return descriptor["sha256"]

    def base(self) -> dict:
        master_seed = "integration-control-not-natural"
        private = source_generator.generate_source(
            101, "generic", 0, 6, master_seed, FixedCardinalityBackend()
        )
        public, link = public_boundary.redact_private_source(private)
        protocol = self.add("protocol", "frozen protocol")
        amendment = self.add("amendment", "frozen amendment")
        manifest = {
            "schema": "xedni-rank-decay-primes/v1",
            "master_seed": master_seed,
            "bit_sizes": [7],
            "slots_per_bit_size": 1,
            "derivation": "test control only",
            "miller_rabin_bases": [2, 3, 5, 7, 11, 13, 17],
            "generator_sha256": "1" * 64,
            "primes": [
                {
                    "bits": 7,
                    "slot": 0,
                    "hash_candidate": 101,
                    "downward_odd_steps": 0,
                    "prime": 101,
                }
            ],
        }
        prime_manifest = self.add("prime_manifest", manifest)
        row = {
            "stage": "calibration",
            "bits": 7,
            "slot": 0,
            "p": 101,
            "family": "generic",
            "r": 2,
            "lift": "balanced",
            "local_arm": "A_none",
            "index": 0,
            "source_key": "calibration|p=101|family=generic|index=0",
            "source_index": 0,
            "source_master_seed": master_seed,
            "local_seed": "test-local-seed",
            "row_id": "row-1",
            "status": "PLANNED",
        }
        roster_row = self.add("roster_row", row)
        roster_payload = {
            "schema": "xedni.rank-decay-roster/v1",
            "stage": "calibration",
            "status": "PLANNED_NO_NATURAL_ROWS_RUN",
            "factors": {"test_control": True},
            "source_master_seed": master_seed,
            "executable_roster": [row],
            "blocked_roster": [],
            "counts": {"executable": 1, "blocked": 0},
            "input_hashes": {
                "PROTOCOL.md": protocol,
                "AMENDMENT.md": amendment,
                "PRIMES.json": prime_manifest,
            },
        }
        roster = dict(roster_payload)
        roster["roster_sha256"] = rp.object_sha256(roster_payload)
        roster_digest = self.add("roster", roster)
        freeze = {
            "schema": "xedni.rank-decay-freeze/v1",
            "status": "AUTHORIZED_TEST_CONTROL",
            "natural_rows_authorized": True,
            "implementation_commit": "test-control",
            "master_seed": master_seed,
            "blockers": [],
            "files": {
                "research/xedni_rank_decay_20261118/PROTOCOL.md": protocol,
                "research/xedni_rank_decay_20261118/AMENDMENT.md": amendment,
                "research/xedni_rank_decay_20261118/PRIMES.json": prime_manifest,
            },
            "rosters": {"calibration": {"sha256": roster["roster_sha256"]}},
            "binary": {},
            "tools": {},
            "analysis": {},
        }
        freeze_digest = self.add("freeze_manifest", freeze)
        private_digest = self.add("source_private", private)
        public_digest = self.add("source_public", public)
        link_digest = self.add("public_private_link", link)
        ainvs = [0, 0, 0, -1, 1]
        lift_record = {
            "schema": "test-lift/v1",
            "row_id": "row-1",
            "r": 2,
            "ainvs": ainvs,
            "points": [[0, 1], [1, 1]],
        }
        lift = self.add("lift", lift_record)
        local = self.add("local", {})
        bindings = {
            "freeze_manifest_sha256": freeze_digest,
            "roster_sha256": roster_digest,
            "roster_row_sha256": roster_row,
            "prime_manifest_sha256": prime_manifest,
            "protocol_sha256": protocol,
            "amendment_sha256": amendment,
            "master_seed_sha256": rp.object_sha256(master_seed),
            "stage_seed_sha256": rp.object_sha256(master_seed),
            "p": 101,
            "bits": 7,
            "r": 2,
            "source_private_sha256": private_digest,
            "source_public_sha256": public_digest,
            "public_private_link_sha256": link_digest,
            "lift_sha256": lift,
            "local_sha256": local,
        }
        adapter = self.add("tool/pari_rank/adapter", Path(rank_pari.__file__).read_bytes())
        version = self.add("tool/pari_rank/version", "PARI/GP 2.17.2")
        executable = self.add("tool/pari_rank/executable", b"ELF-fake")
        script = self.add(
            "tool/pari_rank/script", rank_pari.make_script(tuple(ainvs), 0)
        )
        transcript_text = (
            f"{rank_pari.BEGIN}\nLOWER=2\nUPPER=2\nSHA2_RANK=0\n"
            f"POINT_COUNT=2\nPARISIZEMAX={rank_pari.DEFAULT_PARISIZEMAX}\n"
            f"{rank_pari.END}\n"
        )
        transcript = self.add("tool/pari_rank/transcript", transcript_text)
        command = ["gp", "-q", "-f"]
        tools = [
            {
                "name": "pari_rank",
                "status": "ran",
                "adapter_sha256": adapter,
                "version": "2.17.2",
                "version_sha256": version,
                "executable_sha256": executable,
                "command": command,
                "command_sha256": rp.object_sha256(command),
                "script_sha256": script,
                "transcript_sha256": transcript,
                "version_returncode": 0,
                "version_timed_out": False,
                "returncode": 0,
                "timed_out": False,
                "effort": 0,
                "timeout_seconds": 60,
            }
        ]
        proposer_payload = {
            "schema": rp.PROPOSER_RECEIPT_SCHEMA,
            "row_id": "row-1",
            "r": 2,
            "status": "complete",
            "complete_for_frozen_budget": True,
            "candidates": [],
        }
        proposer_payload["receipt_sha256"] = rp.object_sha256(proposer_payload)
        proposer = self.add("relation_proposer", proposer_payload)
        inventory = rp.seal_inventory(
            {
                "schema": rp.INVENTORY_SCHEMA,
                "status": "bounded_no_hit",
                "selected_dependence": "UNKNOWN",
                "proposer_report_sha256": proposer,
                "replay_report_sha256": None,
                "complete_for_frozen_budget": True,
                "complete_relation_lattice": False,
                "absence_certificate_sha256": None,
                "candidate_count": 0,
                "replayed_count": 0,
                "exact_relation_count": 0,
                "counted_relation_count": 0,
                "candidates": [],
            }
        )
        work_payload = {
            "schema": rp.WORK_SCHEMA,
            "complete": True,
            "source_generation_candidates": 1,
            "local_construction_candidates": 1,
            "lift_candidates": 1,
            "relation_candidates": 0,
            "relation_replays": 0,
            "rank_calls": 1,
            "rejected_candidates": 0,
            "duplicate_candidates": 0,
            "cpu_ns": 100,
            "wall_ns": 200,
            "peak_rss_bytes": 4096,
            "retained_bytes": 1024,
        }
        work_report = self.add("work_report", work_payload)
        work = rp.seal_work({**work_payload, "work_report_sha256": work_report})
        return rp.seal_envelope(
            {
                "schema": rp.SCHEMA,
                "row_id": "row-1",
                "bindings": bindings,
                "artifacts": list(self.artifacts.values()),
                "tools": tools,
                "relation_inventory": inventory,
                "work": work,
            }
        )

    def certified_relation(self) -> dict:
        envelope = self.base()
        vector = [1, -1]
        proposal = self.add("relation_candidate/c0/proposal", {"vector": vector})
        replay = self.add("relation_candidate/c0/replay", {"identity": True})
        certificate = self.add(
            "relation_candidate/c0/certificate", {"certificate": "exact"}
        )
        replay_payload = {
            "schema": rp.REPLAY_RECEIPT_SCHEMA,
            "row_id": "row-1",
            "status": "complete",
            "replays": [
                {
                    "candidate_id": "c0",
                    "replay_status": "exact_true",
                    "replay_sha256": replay,
                    "certificate_sha256": certificate,
                }
            ],
        }
        replay_payload["receipt_sha256"] = rp.object_sha256(replay_payload)
        replay_report = self.add("relation_replay", replay_payload)
        candidate = {
            "candidate_id": "c0",
            "vector": vector,
            "vector_sha256": rp.object_sha256(vector),
            "proposal_sha256": proposal,
            "eligible_for_replay": True,
            "replay_status": "exact_true",
            "replay_sha256": replay,
            "certificate_sha256": certificate,
            "counted": True,
        }
        envelope["relation_inventory"] = rp.seal_inventory(
            {
                "schema": rp.INVENTORY_SCHEMA,
                "status": "certified_relation",
                "selected_dependence": "CERT_YES",
                "proposer_report_sha256": envelope["relation_inventory"][
                    "proposer_report_sha256"
                ],
                "replay_report_sha256": replay_report,
                "complete_for_frozen_budget": True,
                "complete_relation_lattice": False,
                "absence_certificate_sha256": None,
                "candidate_count": 1,
                "replayed_count": 1,
                "exact_relation_count": 1,
                "counted_relation_count": 1,
                "candidates": [candidate],
            }
        )
        envelope["work"]["relation_candidates"] = 1
        envelope["work"]["relation_replays"] = 1
        envelope["work"] = rp.seal_work(envelope["work"])
        proposer_payload = {
            "schema": rp.PROPOSER_RECEIPT_SCHEMA,
            "row_id": "row-1",
            "r": 2,
            "status": "complete",
            "complete_for_frozen_budget": True,
            "candidates": [
                {
                    "candidate_id": "c0",
                    "vector": vector,
                    "eligible_for_replay": True,
                    "proposal_sha256": proposal,
                }
            ],
        }
        proposer_payload["receipt_sha256"] = rp.object_sha256(proposer_payload)
        proposer_descriptor = self.artifacts["relation_proposer"]
        proposer_path = self.root / proposer_descriptor["path"]
        proposer_path.write_bytes(rp.canonical_json(proposer_payload))
        self.artifacts["relation_proposer"] = rp.describe_artifact(
            "relation_proposer", proposer_descriptor["path"], self.root
        )
        envelope["relation_inventory"]["proposer_report_sha256"] = self.artifacts[
            "relation_proposer"
        ]["sha256"]
        envelope["relation_inventory"] = rp.seal_inventory(
            envelope["relation_inventory"]
        )
        envelope["artifacts"] = list(self.artifacts.values())
        return rp.seal_envelope(envelope)


def reseal(envelope: dict, *, inventory: bool = False, work: bool = False) -> dict:
    if inventory:
        envelope["relation_inventory"] = rp.seal_inventory(
            envelope["relation_inventory"]
        )
    if work:
        envelope["work"] = rp.seal_work(envelope["work"])
    return rp.seal_envelope(envelope)


class RowProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = EvidenceFixture(self.root)
        self.envelope = self.fixture.base()

    def tearDown(self):
        self.temporary.cleanup()

    def assert_code(self, code: str, envelope: dict | None = None):
        with self.assertRaises(rp.ProvenanceError) as raised:
            rp.validate_envelope(envelope or self.envelope, self.root)
        self.assertEqual(raised.exception.code, code)

    def test_valid_bounded_no_hit_stays_unknown(self):
        result = rp.validate_envelope(self.envelope, self.root)
        self.assertEqual(result["status"], "HASH_GRAPH_ONLY")
        self.assertFalse(result["production_eligible"])
        self.assertEqual(result["relation_status"], "bounded_no_hit")
        self.assertEqual(result["selected_dependence"], "UNKNOWN")

    def test_runner_style_row_id_is_accepted(self):
        self.envelope["row_id"] = (
            "calibration|b=16|slot=0|p=65521|family=generic|r=2|"
            "lift=balanced|local=A_none|index=0"
        )
        result = rp.validate_envelope(reseal(self.envelope))
        self.assertEqual(result["row_id"], self.envelope["row_id"])

    def test_valid_certified_relation(self):
        envelope = self.fixture.certified_relation()
        self.assert_code("relation_certificate", envelope)

    def test_valid_certified_absence(self):
        absence = self.fixture.add("relation_absence", {"complete_lattice": True})
        envelope = copy.deepcopy(self.envelope)
        inventory = envelope["relation_inventory"]
        inventory.update(
            status="certified_absence",
            selected_dependence="CERT_NO",
            complete_relation_lattice=True,
            absence_certificate_sha256=absence,
        )
        envelope["artifacts"] = list(self.fixture.artifacts.values())
        self.assert_code(
            "absence_verifier_unavailable", reseal(envelope, inventory=True)
        )

    def test_valid_unknown_incomplete(self):
        envelope = copy.deepcopy(self.envelope)
        envelope["relation_inventory"].update(
            status="unknown", complete_for_frozen_budget=False
        )
        envelope["work"].update(complete=False)
        proposer = {
            "schema": rp.PROPOSER_RECEIPT_SCHEMA,
            "row_id": "row-1",
            "r": 2,
            "status": "incomplete",
            "complete_for_frozen_budget": False,
            "candidates": [],
        }
        proposer["receipt_sha256"] = rp.object_sha256(proposer)
        descriptor = self.fixture.artifacts["relation_proposer"]
        (self.root / descriptor["path"]).write_bytes(rp.canonical_json(proposer))
        descriptor = rp.describe_artifact(
            "relation_proposer", descriptor["path"], self.root
        )
        self.fixture.artifacts["relation_proposer"] = descriptor
        envelope["relation_inventory"]["proposer_report_sha256"] = descriptor[
            "sha256"
        ]
        work_payload = {
            key: value
            for key, value in envelope["work"].items()
            if key not in {"work_report_sha256", "work_sha256"}
        }
        work_digest = self.fixture.add("work_report", work_payload)
        envelope["work"]["work_report_sha256"] = work_digest
        envelope["artifacts"] = list(self.fixture.artifacts.values())
        result = rp.validate_envelope(
            reseal(envelope, inventory=True, work=True), self.root
        )
        self.assertEqual(result["relation_status"], "unknown")

    def test_root_extra_key_rejected(self):
        self.envelope["extra"] = True
        self.assert_code("schema")

    def test_nested_missing_key_rejected(self):
        del self.envelope["bindings"]["local_sha256"]
        self.assert_code("schema")

    def test_envelope_mutation_without_reseal_rejected(self):
        self.envelope["row_id"] = "row-2"
        self.assert_code("self_hash")

    def test_binding_mutation_with_reseal_rejected(self):
        self.envelope["bindings"]["lift_sha256"] = "0" * 64
        self.assert_code("artifact_binding", reseal(self.envelope))

    def test_public_source_cannot_alias_private_source(self):
        self.envelope["bindings"]["source_public_sha256"] = self.envelope["bindings"][
            "source_private_sha256"
        ]
        self.assert_code("source_link", reseal(self.envelope))

    def test_forged_roster_row_is_rejected_after_rehash(self):
        envelope = copy.deepcopy(self.envelope)
        descriptor = self.fixture.artifacts["roster_row"]
        row = json.loads((self.root / descriptor["path"]).read_text())
        row["r"] = 3
        new_digest = self.fixture.add("roster_row", row)
        envelope["bindings"]["roster_row_sha256"] = new_digest
        envelope["artifacts"] = list(self.fixture.artifacts.values())
        self.assert_code("roster_row", reseal(envelope))

    def test_scalar_leak_in_public_source_is_rejected_after_rehash(self):
        envelope = copy.deepcopy(self.envelope)
        descriptor = self.fixture.artifacts["source_public"]
        public = json.loads((self.root / descriptor["path"]).read_text())
        public["ordered_scalars"] = [7, 11]
        new_digest = self.fixture.add("source_public", public)
        envelope["bindings"]["source_public_sha256"] = new_digest
        envelope["artifacts"] = list(self.fixture.artifacts.values())
        self.assert_code("public_boundary", reseal(envelope))

    def test_proposer_omitted_candidate_is_rejected(self):
        envelope = copy.deepcopy(self.envelope)
        proposer = {
            "schema": rp.PROPOSER_RECEIPT_SCHEMA,
            "row_id": "row-1",
            "r": 2,
            "status": "complete",
            "complete_for_frozen_budget": True,
            "candidates": [
                {
                    "candidate_id": "omitted",
                    "vector": [1, -1],
                    "eligible_for_replay": True,
                    "proposal_sha256": "3" * 64,
                }
            ],
        }
        proposer["receipt_sha256"] = rp.object_sha256(proposer)
        proposer_digest = self.fixture.add("relation_proposer", proposer)
        envelope["relation_inventory"]["proposer_report_sha256"] = proposer_digest
        envelope["artifacts"] = list(self.fixture.artifacts.values())
        self.assert_code("relation_inventory", reseal(envelope, inventory=True))

    def test_not_pari_version_transcript_is_rejected(self):
        envelope = copy.deepcopy(self.envelope)
        digest = self.fixture.add("tool/pari_rank/version", "NOT PARI 2.17.2")
        envelope["tools"][0]["version_sha256"] = digest
        envelope["artifacts"] = list(self.fixture.artifacts.values())
        self.assert_code("tool_version", reseal(envelope))

    def test_hardlink_artifact_alias_is_rejected(self):
        envelope = copy.deepcopy(self.envelope)
        adapter = self.fixture.artifacts["tool/pari_rank/adapter"]
        version = self.fixture.artifacts["tool/pari_rank/version"]
        link_path = self.root / "hardlink-version.evidence"
        link_path.hardlink_to(self.root / adapter["path"])
        aliased = {
            "role": "tool/pari_rank/version",
            "path": link_path.name,
            "sha256": adapter["sha256"],
            "bytes": adapter["bytes"],
            "media_type": "text/plain",
        }
        self.fixture.artifacts["tool/pari_rank/version"] = aliased
        envelope["tools"][0]["version_sha256"] = adapter["sha256"]
        envelope["artifacts"] = list(self.fixture.artifacts.values())
        self.assert_code("artifact_collision", reseal(envelope))

    def test_rank_calls_999_is_rejected_even_when_resealed(self):
        envelope = copy.deepcopy(self.envelope)
        envelope["work"]["rank_calls"] = 999
        self.assert_code("work_count", reseal(envelope, work=True))

    def test_arbitrary_absence_text_cannot_certify_independence(self):
        envelope = copy.deepcopy(self.envelope)
        absence = self.fixture.add("relation_absence", "trust me: complete lattice")
        envelope["relation_inventory"].update(
            status="certified_absence",
            selected_dependence="CERT_NO",
            complete_relation_lattice=True,
            absence_certificate_sha256=absence,
        )
        envelope["artifacts"] = list(self.fixture.artifacts.values())
        self.assert_code(
            "absence_verifier_unavailable", reseal(envelope, inventory=True)
        )

    def test_underlying_file_tamper_rejected(self):
        descriptor = next(
            item for item in self.envelope["artifacts"] if item["role"] == "lift"
        )
        (self.root / descriptor["path"]).write_bytes(b"tampered")
        self.assert_code("artifact_size")

    def test_same_size_file_tamper_rejected(self):
        descriptor = next(
            item for item in self.envelope["artifacts"] if item["role"] == "protocol"
        )
        path = self.root / descriptor["path"]
        path.write_bytes(b"x" * descriptor["bytes"])
        self.assert_code("artifact_hash")

    def test_absolute_path_rejected(self):
        self.envelope["artifacts"][0]["path"] = "/etc/passwd"
        self.assert_code("path", reseal(self.envelope))

    def test_parent_traversal_rejected(self):
        self.envelope["artifacts"][0]["path"] = "../escape"
        self.assert_code("path", reseal(self.envelope))

    def test_backslash_path_rejected(self):
        self.envelope["artifacts"][0]["path"] = "a\\b"
        self.assert_code("path", reseal(self.envelope))

    def test_symlink_path_rejected(self):
        descriptor = self.envelope["artifacts"][0]
        target = self.root / descriptor["path"]
        link = self.root / "evidence-link"
        link.symlink_to(target.name)
        descriptor["path"] = link.name
        self.assert_code("path", reseal(self.envelope))

    def test_duplicate_artifact_role_rejected(self):
        self.envelope["artifacts"].append(copy.deepcopy(self.envelope["artifacts"][0]))
        self.assert_code("artifact_collision", reseal(self.envelope))

    def test_duplicate_artifact_path_rejected(self):
        duplicate = copy.deepcopy(self.envelope["artifacts"][0])
        duplicate["role"] = "new-role"
        self.envelope["artifacts"].append(duplicate)
        self.assert_code("artifact_collision", reseal(self.envelope))

    def test_unexpected_artifact_role_rejected(self):
        self.fixture.add("unexpected", b"x")
        self.envelope["artifacts"] = list(self.fixture.artifacts.values())
        self.assert_code("artifact_schema", reseal(self.envelope))

    def test_prime_bit_mismatch_rejected(self):
        self.envelope["bindings"]["bits"] = 17
        self.assert_code("prime", reseal(self.envelope))

    def test_composite_prime_rejected(self):
        self.envelope["bindings"].update(p=65520, bits=16)
        self.assert_code("prime", reseal(self.envelope))

    def test_uppercase_hash_rejected(self):
        self.envelope["bindings"]["master_seed_sha256"] = "A" * 64
        self.assert_code("hash", reseal(self.envelope))

    def test_tool_command_mutation_rejected(self):
        self.envelope["tools"][0]["command"][0] = "evil-gp"
        self.assert_code("tool_command", reseal(self.envelope))

    def test_tool_transcript_binding_rejected(self):
        self.envelope["tools"][0]["transcript_sha256"] = "0" * 64
        self.assert_code("artifact_binding", reseal(self.envelope))

    def test_run_tool_requires_script_and_transcript(self):
        self.envelope["tools"][0]["script_sha256"] = None
        self.assert_code("tool_evidence", reseal(self.envelope))

    def test_duplicate_tool_name_rejected(self):
        self.envelope["tools"].append(copy.deepcopy(self.envelope["tools"][0]))
        self.assert_code("tool_collision", reseal(self.envelope))

    def test_bounded_no_hit_cannot_certify_independence(self):
        self.envelope["relation_inventory"]["selected_dependence"] = "CERT_NO"
        self.assert_code("inventory_status", reseal(self.envelope, inventory=True))

    def test_absence_requires_certificate(self):
        self.envelope["relation_inventory"].update(
            status="certified_absence",
            selected_dependence="CERT_NO",
            complete_relation_lattice=True,
        )
        self.assert_code("inventory_status", reseal(self.envelope, inventory=True))

    def test_candidate_count_mismatch_rejected(self):
        envelope = self.fixture.certified_relation()
        envelope["relation_inventory"]["candidate_count"] = 2
        self.assert_code("inventory_count", reseal(envelope, inventory=True))

    def test_duplicate_canonical_vector_rejected(self):
        envelope = self.fixture.certified_relation()
        first = envelope["relation_inventory"]["candidates"][0]
        second = copy.deepcopy(first)
        second["candidate_id"] = "c1"
        second["proposal_sha256"] = self.fixture.add(
            "relation_candidate/c1/proposal", {"vector": [1, -1]}
        )
        second["replay_sha256"] = self.fixture.add(
            "relation_candidate/c1/replay", {"identity": True}
        )
        second["certificate_sha256"] = self.fixture.add(
            "relation_candidate/c1/certificate", {"certificate": "exact"}
        )
        inventory = envelope["relation_inventory"]
        inventory["candidates"].append(second)
        inventory.update(
            candidate_count=2,
            replayed_count=2,
            exact_relation_count=2,
            counted_relation_count=2,
        )
        envelope["work"].update(relation_candidates=2, relation_replays=2)
        envelope["artifacts"] = list(self.fixture.artifacts.values())
        self.assert_code(
            "candidate_collision", reseal(envelope, inventory=True, work=True)
        )

    def test_candidate_id_cannot_smuggle_role_path(self):
        envelope = self.fixture.certified_relation()
        envelope["relation_inventory"]["candidates"][0]["candidate_id"] = "c0/replay"
        self.assert_code("token", reseal(envelope, inventory=True))

    def test_nonprimitive_candidate_rejected(self):
        envelope = self.fixture.certified_relation()
        candidate = envelope["relation_inventory"]["candidates"][0]
        candidate["vector"] = [2, -2]
        candidate["vector_sha256"] = rp.object_sha256(candidate["vector"])
        self.assert_code("relation_vector", reseal(envelope, inventory=True))

    def test_sign_alias_candidate_rejected(self):
        envelope = self.fixture.certified_relation()
        candidate = envelope["relation_inventory"]["candidates"][0]
        candidate["vector"] = [-1, 1]
        candidate["vector_sha256"] = rp.object_sha256(candidate["vector"])
        self.assert_code("relation_vector", reseal(envelope, inventory=True))

    def test_eligible_unreplayed_invalid_for_complete_budget(self):
        envelope = self.fixture.certified_relation()
        candidate = envelope["relation_inventory"]["candidates"][0]
        candidate.update(
            replay_status="not_replayed",
            replay_sha256=None,
            certificate_sha256=None,
            counted=False,
        )
        inventory = envelope["relation_inventory"]
        inventory.update(
            status="bounded_no_hit",
            selected_dependence="UNKNOWN",
            replay_report_sha256=None,
            replayed_count=0,
            exact_relation_count=0,
            counted_relation_count=0,
        )
        envelope["work"].update(relation_replays=0)
        self.assert_code(
            "inventory_incomplete", reseal(envelope, inventory=True, work=True)
        )

    def test_work_candidate_accounting_mismatch_rejected(self):
        envelope = self.fixture.certified_relation()
        envelope["work"]["relation_candidates"] = 0
        self.assert_code("work_count", reseal(envelope, work=True))

    def test_inventory_self_hash_rejected(self):
        self.envelope["relation_inventory"]["inventory_sha256"] = "0" * 64
        self.assert_code("self_hash", reseal(self.envelope))

    def test_work_self_hash_rejected(self):
        self.envelope["work"]["work_sha256"] = "0" * 64
        self.assert_code("self_hash", reseal(self.envelope))

    def test_strict_json_rejects_duplicate_keys(self):
        path = self.root / "duplicate.json"
        path.write_text('{"a":1,"a":2}', encoding="utf-8")
        with self.assertRaises(rp.ProvenanceError) as raised:
            rp.load_strict_json(path)
        self.assertEqual(raised.exception.code, "json")

    def test_strict_json_rejects_nonfinite(self):
        path = self.root / "nan.json"
        path.write_text('{"a":NaN}', encoding="utf-8")
        with self.assertRaises(rp.ProvenanceError) as raised:
            rp.load_strict_json(path)
        self.assertEqual(raised.exception.code, "json")

    def test_structural_validation_without_files_is_not_file_verification(self):
        result = rp.validate_envelope(self.envelope)
        self.assertEqual(result["status"], "HASH_GRAPH_ONLY")
        self.assertFalse(result["files_verified"])

    def test_object_hash_is_order_stable_and_type_sensitive(self):
        self.assertEqual(rp.object_sha256({"a": 1, "b": 2}), rp.object_sha256({"b": 2, "a": 1}))
        self.assertNotEqual(rp.object_sha256([1]), rp.object_sha256({"0": 1}))


if __name__ == "__main__":
    unittest.main()

