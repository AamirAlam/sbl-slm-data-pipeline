import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from sbl_slm.cli import main
from sbl_slm.ingest import ingest, snapshot
from sbl_slm.schema import ValidationError, canonical, content_hash, sha, validate_target

PRIMARY = "ADRs/001-decision-point-curation-and-review.md"
COMPANION = "ADRs/001-decision-point-curation-and-review-plain-english.md"


def candidate():
    return dict(id="fixture-1", tenant_id="tenant-fixture", prospect_id="prospect-fixture",
                thread_id="thread-fixture", campaign_id="campaign-fixture", channel=1, trigger=2,
                observed_at="2026-01-02T00:00:00Z", snapshot_at="2026-01-03T00:00:00Z",
                observed_response="OBSERVATION_SENTINEL", speaker_provenance="unverified",
                review_status="unreviewed", training_eligible=False, split="train",
                source_message_ids=["current-message"], flags=["sampled_history_may_be_truncated"],
                context={"objective": "FUTURE_CONTEXT_SENTINEL"},
                history=[dict(text="Earlier incorrect reply\u2028still context", speaker="company",
                              message_ids=["prior-message"], created_at="2026-01-01T00:00:00Z",
                              last_created_at="2026-01-01T00:00:00Z")])


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        (self.root / "ADRs").mkdir()
        (self.root / PRIMARY).write_text("# ADR-001: Fixture\n\nStatus: Provisional fixture only.\n")
        (self.root / COMPANION).write_text("# ADR-001: Fixture companion\n\nStatus: Provisional.\n[Original](001-decision-point-curation-and-review.md)\n")
        self.write([candidate()])

    def write(self, rows, readable=None):
        data = b"".join(canonical(row) for row in rows)
        (self.root / "data/candidates.jsonl").write_bytes(data)
        (self.root / "data/candidates-readable.json").write_bytes(canonical(rows if readable is None else readable))
        manifest = dict(candidates_sha256=sha(data), candidate_decision_count=len(rows),
                        split_counts={key: sum(r.get("split") == key for r in rows) for key in ("train", "validation", "test")})
        (self.root / "data/manifest.jsonl").write_bytes(canonical(manifest))

    def fails(self, code):
        before = snapshot(self.root)
        with self.assertRaises(ValidationError) as caught:
            ingest(self.root)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(snapshot(self.root), before)
        self.assertNotIn("SENTINEL", str(caught.exception))

    def test_deterministic_packet_and_source_preservation(self):
        before = snapshot(self.root)
        first = ingest(self.root)
        self.assertEqual(canonical(first), canonical(ingest(self.root)))
        self.assertEqual(snapshot(self.root), before)
        packet, = first["packets"]
        self.assertEqual(packet["source"]["id"], "fixture-1")
        self.assertEqual(packet["source"]["record_sha256"], content_hash(candidate()))
        self.assertEqual(packet["input_sha256"], content_hash(packet["X"]))
        revision = packet.pop("revision_id")
        self.assertEqual(revision, content_hash(packet))
        self.assertEqual(len(packet["adr"]["representations"]), 2)
        self.assertIsNone(packet["Y"])
        self.assertFalse(packet["training_eligible"])

    def test_phase_a_excludes_response_and_future_context(self):
        packet = ingest(self.root)["packets"][0]
        encoded = canonical(packet["X"]).decode()
        self.assertNotIn("OBSERVATION_SENTINEL", encoded)
        self.assertNotIn("FUTURE_CONTEXT_SENTINEL", encoded)
        self.assertIn("Earlier incorrect reply\u2028still context", encoded)
        self.assertIsNone(packet["X"]["context"])
        self.assertIn("event_order_not_verified", packet["X"]["limitations"])

    def test_changed_source_keeps_identity_but_changes_revision(self):
        first = ingest(self.root)["packets"][0]
        row = candidate()
        row["observed_response"] = "different observed response"
        self.write([row])
        second = ingest(self.root)["packets"][0]
        self.assertEqual(first["decision_id"], second["decision_id"])
        self.assertNotEqual(first["revision_id"], second["revision_id"])
        self.assertEqual(first["input_sha256"], second["input_sha256"])

    def test_missing_id_and_wrong_types(self):
        for field, value in (("id", None), ("trigger", True), ("history", {}), ("source_message_ids", [])):
            with self.subTest(field=field):
                row = candidate()
                row[field] = value
                self.write([row])
                with self.assertRaises(ValidationError):
                    ingest(self.root)

    def test_conflicting_and_identical_duplicate_ids_rejected(self):
        for response in ("OBSERVATION_SENTINEL", "conflicting"):
            row = candidate()
            row["observed_response"] = response
            self.write([candidate(), row])
            self.fails("duplicate_source_id")

    def test_representation_mismatch(self):
        other = candidate()
        other["observed_response"] = "different"
        self.write([candidate()], [other])
        self.fails("representation_mismatch")

    def test_corruption_and_checksum(self):
        path = self.root / "data/candidates.jsonl"
        path.write_bytes(b'{"private":')
        self.fails("invalid_json")
        self.write([candidate()])
        path.write_bytes(path.read_bytes() + b" ")
        self.fails("invalid_json")
        self.write([candidate()])
        path.write_bytes(path.read_bytes().replace(b'"trigger":2', b'"trigger":3'))
        self.fails("checksum_mismatch")

    def test_count_and_split_mismatch(self):
        for field, value, code in (("candidate_decision_count", 2, "count_mismatch"),
                                   ("split_counts", {"train": 2}, "split_count_mismatch")):
            self.write([candidate()])
            path = self.root / "data/manifest.jsonl"
            manifest = json.loads(path.read_bytes())
            manifest[field] = value
            path.write_bytes(canonical(manifest))
            self.fails(code)

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        for payload, code in ((b'{"x":1,"x":2}\n', "duplicate_json_key"),
                              (b'{"x":NaN}\n', "nonfinite_json_number")):
            (self.root / "data/candidates.jsonl").write_bytes(payload)
            self.fails(code)

    def test_future_and_current_messages_rejected_in_history(self):
        row = candidate()
        row["history"][0]["last_created_at"] = "2026-01-04T00:00:00Z"
        self.write([row])
        self.fails("invalid_history_order")
        row = candidate()
        row["history"][0]["message_ids"] = ["current-message"]
        self.write([row])
        self.fails("history_message_overlap")

    def test_adr_ambiguity_and_identity_conflict(self):
        (self.root / COMPANION).write_text("# ADR-002: Wrong companion\nStatus: Fixture.\n")
        self.fails("adr_identity_conflict")
        (self.root / COMPANION).write_text("# ADR-001: Unlinked companion\nStatus: Fixture.\n")
        self.fails("ambiguous_adr_companion")

    def test_cli_safe_summary_and_errors(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(main(["ingest", "--root", str(self.root)]), 0)
        self.assertEqual(json.loads(stdout.getvalue())["candidate_count"], 1)
        self.assertNotIn("SENTINEL", stdout.getvalue() + stderr.getvalue())
        (self.root / "data/candidates.jsonl").write_bytes(b'"PRIVATE_SENTINEL')
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(main(["ingest", "--root", str(self.root)]), 1)
        self.assertNotIn("PRIVATE_SENTINEL", stderr.getvalue())

    def test_naive_source_timestamps_are_preserved_without_inventing_utc(self):
        row = candidate()
        row["observed_at"] = "2026-01-02 00:00:00.000000"
        row["snapshot_at"] = "2026-01-03 00:00:00.000000"
        for key in ("created_at", "last_created_at"):
            row["history"][0][key] = "2026-01-01 00:00:00.000000"
        self.write([row])
        packet = ingest(self.root)["packets"][0]
        self.assertEqual(packet["X"]["history"][0]["created_at"], row["history"][0]["created_at"])
        self.assertIn("source_timezone_not_verified", packet["X"]["limitations"])
        row["history"][0]["created_at"] = "2026-01-01T00:00:00Z"
        self.write([row])
        self.fails("mixed_timestamp_zones")

    def test_target_contract(self):
        validate_target(dict(action="answer", arguments={}, draft="Supported fixture answer."))
        validate_target(dict(action="wait", arguments={}, draft=None))
        validate_target(dict(action="answer", arguments={}), "action_only")
        for target in (dict(action="invented", arguments={}, draft=None),
                       dict(action="answer", arguments={}),
                       dict(action="answer", arguments=[], draft="text"),
                       dict(action="wait", arguments={}, draft="text")):
            with self.assertRaises(ValidationError):
                validate_target(target)
        with self.assertRaises(ValidationError):
            validate_target(dict(action="answer", arguments={}, draft=None), "action_only")


if __name__ == "__main__":
    unittest.main()
