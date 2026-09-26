import copy
import json
import tempfile
import unittest
from pathlib import Path

from sbl_slm.audit import select
from sbl_slm.export import Exporter
from sbl_slm.ingest import snapshot
from sbl_slm.review import Review
from sbl_slm.schema import ValidationError, canonical, sha
from tests.test_ingest import candidate, PRIMARY, COMPANION


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); (self.root / "data").mkdir(); (self.root / "ADRs").mkdir()
        (self.root / PRIMARY).write_text("# ADR-001: Fixture\nStatus: Fixture.\n")
        (self.root / COMPANION).write_text("# ADR-001: Companion\nStatus: Fixture.\n[Original](001-decision-point-curation-and-review.md)\n")
        data = canonical(candidate())
        (self.root / "data/candidates.jsonl").write_bytes(data)
        (self.root / "data/candidates-readable.json").write_bytes(canonical([candidate()]))
        (self.root / "data/manifest.jsonl").write_bytes(canonical(dict(candidates_sha256=sha(data), candidate_decision_count=1, split_counts=dict(train=1, validation=0, test=0))))
        self.before = snapshot(self.root)
        self.review = Review(self.root); self.review.initialize("Owner", 0)
        packet = self.review.sync("Owner", self.review.store.version())[0]
        policy = self.review.evidence("policy", dict(kind="policy", version="v1", source_citation="fixture", authority="Owner", text="fixture policy"), "Owner", self.review.store.version())
        target = dict(action="wait", arguments={"event":"fixture event"}, draft=None)
        self.revision = self.review.propose(packet, target, "full", {"policy": policy}, {"kind":"human","actor":"Owner"}, "Owner", self.review.store.version())
        self.review.phase_a(self.revision, target, "full", "Fixture rationale", "Reviewer", self.review.store.version())
        self.review.view(self.revision, "Reviewer", True, self.review.store.version())
        assessment = dict(outcome="accept", dimensions={k:"pass" for k in ("correctness","factual_support","intent","policy","style")}, missing_evidence=[], policy_clear=True, rationale="Fixture support", citations=[policy], confidence=None)
        self.review.review(self.revision, assessment, "Reviewer", self.review.store.version())
        self.review.decide(self.revision, "accept", "Reviewer", self.review.store.version())
        self.exporter = Exporter(self.review)

    def test_audit_rounding_and_reproducibility(self):
        self.assertEqual(select([], 5)["selected"], [])
        self.assertEqual(len(select([str(i) for i in range(11)], 7)["selected"]), 2)
        before = self.review.store.version()
        release, raw = self.exporter.build("Owner", before, fixture=True)
        self.assertEqual(release["holdout_status"], "not_supplied")
        self.assertEqual(release["manifest"]["partitions"], {"train": 1, "validation": 0, "test": 0})
        self.assertNotIn("observed_response", raw.decode())
        self.assertNotIn("rationale", raw.decode())
        again, raw_again = self.exporter.build("Owner", self.review.store.version(), fixture=True)
        self.assertEqual(raw, raw_again); self.assertEqual(release, again)

    def test_permission_boundary_and_exclusions(self):
        with self.assertRaises(ValidationError) as caught:
            self.exporter.build("Owner", self.review.store.version(), fixture=False)
        self.assertEqual(caught.exception.code, "data_use_permission_required")
        self.review.evidence("data_use", dict(kind="rule", version="v1", source_citation="fixture", authority="Owner", text="owner permission", allowed=True), "Owner", self.review.store.version())
        release, _ = self.exporter.build("Owner", self.review.store.version(), fixture=False)
        self.assertEqual(len(release["partitions"]["train"]), 1)

    def test_stale_approval_excluded_and_source_immutable(self):
        with (self.root / PRIMARY).open("a") as out: out.write("changed")
        release, _ = self.exporter.build("Owner", self.review.store.version(), fixture=True)
        self.assertEqual(release["partitions"]["train"], [])
        self.assertEqual(release["manifest"]["excluded"][0]["reason"], "stale_or_ineligible")
        self.assertNotEqual(snapshot(self.root), self.before)  # fixture mutation is detected, never repaired

if __name__ == "__main__": unittest.main()
