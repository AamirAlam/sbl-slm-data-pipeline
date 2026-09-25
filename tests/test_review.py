import contextlib
import copy
import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from sbl_slm.cli import main
from sbl_slm.ingest import snapshot
from sbl_slm.review import Review, DIMENSIONS, MODEL_SETTINGS
from sbl_slm.schema import ValidationError, canonical, sha
from tests.test_ingest import candidate, PRIMARY, COMPANION

OWNER = "Fixture Owner"


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        (self.root / "ADRs").mkdir()
        (self.root / PRIMARY).write_text("# ADR-001: Fixture\nStatus: Fixture only.\n")
        (self.root / COMPANION).write_text("# ADR-001: Companion\nStatus: Fixture.\n[Original](001-decision-point-curation-and-review.md)\n")
        data = canonical(candidate())
        (self.root / "data/candidates.jsonl").write_bytes(data)
        (self.root / "data/candidates-readable.json").write_bytes(canonical([candidate()]))
        (self.root / "data/manifest.jsonl").write_bytes(canonical(dict(candidates_sha256=sha(data), candidate_decision_count=1, split_counts=dict(train=1, validation=0, test=0))))
        self.before = snapshot(self.root)
        self.r = Review(self.root)
        self.r.initialize(OWNER, 0)
        self.packet = self.r.sync(OWNER, self.version())[0]
        self.policy = self.evidence("policy", "policy")
        self.target = dict(action="wait", arguments={"event": "fixture customer reply"}, draft=None)
        self.revision = self.propose()

    def version(self):
        return self.r.store.version()

    def evidence(self, key, kind, **extra):
        doc = dict(kind=kind, version="fixture/v1", source_citation="invented fixture", authority=OWNER, text="Fixture evidence", **extra)
        return self.r.evidence(key, doc, OWNER, self.version())

    def propose(self, target=None, parent=None, dependencies=None, method=None):
        return self.r.propose(self.packet, target or self.target, "full", dependencies or {"policy": self.policy},
                              method or {"kind": "human", "actor": OWNER}, OWNER, self.version(), parent)

    def assessment(self, outcome="accept"):
        return dict(outcome=outcome, dimensions={k: "pass" for k in DIMENSIONS},
                    missing_evidence=[], policy_clear=True, rationale="Supported by fixture policy",
                    citations=[self.policy], confidence=None)

    def review(self, actor="Reviewer One", assessment=None, revision=None):
        revision = revision or self.revision
        self.r.phase_a(revision, self.target, "full", "Independent fixture judgment", actor, self.version())
        self.r.view(revision, actor, True, self.version())
        return self.r.review(revision, assessment or self.assessment(), actor, self.version())

    def assertCode(self, code, fn):
        before = self.version()
        with self.assertRaises(ValidationError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(self.version(), before)

    def capture_record(self, result, **updates):
        record = dict(attempt_id="fixture-attempt", provider="fixture-provider", prompt_version="fixture/v1",
                      started_at="2026-01-01T00:00:00Z", finished_at="2026-01-01T00:00:01Z",
                      settings=MODEL_SETTINGS, prompt="fixture prompt", prompt_sha256=sha(b"fixture prompt"),
                      request={"revision": self.revision, "phase_a_saved": True}, result=result,
                      status="completed", fixture=True)
        record.update(updates)
        return record

    def test_context_first_per_reviewer(self):
        initial = self.r.view(self.revision, "Reviewer One")
        self.assertNotIn("target", initial)
        self.assertNotIn("OBSERVATION_SENTINEL", json.dumps(initial))
        self.assertCode("phase_a_required", lambda: self.r.view(self.revision, "Reviewer One", True, self.version()))
        self.r.phase_a(self.revision, self.target, "full", "Independent", "Reviewer One", self.version())
        revealed = self.r.view(self.revision, "Reviewer One", True, self.version())
        self.assertEqual(revealed["observed_response"], "OBSERVATION_SENTINEL")
        self.assertCode("phase_a_required", lambda: self.r.view(self.revision, "Reviewer Two", True, self.version()))
        self.assertCode("already_revealed", lambda: self.r.phase_a(self.revision, self.target, "full", "Changed", "Reviewer One", self.version()))

    def test_explicit_acceptance_and_attribution(self):
        self.assertCode("review_required", lambda: self.r.decide(self.revision, "accept", "Reviewer One", self.version()))
        self.review()
        self.assertEqual(self.r.status(self.revision)["state"], "reviewed")
        self.r.decide(self.revision, "accept", "Reviewer One", self.version())
        self.assertTrue(self.r.status(self.revision)["eligible"])
        with self.r.store.transaction() as db:
            event = self.r.store.events(db)[-1]
            self.assertEqual(event["identity"], "self_declared_unverified")
            self.assertEqual(event["actor"], "Reviewer One")
            self.assertTrue(event["at"].endswith("+00:00"))
        self.assertEqual(snapshot(self.root), self.before)

    def test_disagreement_requires_owner_adjudication(self):
        self.review()
        self.review("Reviewer Two", self.assessment("reject"))
        self.assertCode("adjudication_required", lambda: self.r.decide(self.revision, "accept", "Reviewer One", self.version()))
        self.assertCode("owner_required", lambda: self.r.adjudicate(self.revision, self.assessment(), "Not Owner", self.version()))
        self.r.adjudicate(self.revision, self.assessment(), OWNER, self.version())
        self.r.decide(self.revision, "accept", OWNER, self.version())
        with self.r.store.transaction() as db:
            self.assertEqual(len(self.r._reviews(db, self.revision)), 2)
        self.assertEqual(self.r.status(self.revision)["approval_tier"], "human")

    def test_uncertainty_and_revision_keep_history(self):
        self.review(assessment=self.assessment("uncertain"))
        self.assertEqual(self.r.status(self.revision)["state"], "needs-review")
        self.assertCode("unresolved_reviews", lambda: self.r.decide(self.revision, "accept", "Reviewer One", self.version()))
        target = dict(action="wait", arguments={"event": "different fixture event"}, draft=None)
        revised = self.propose(target, self.revision)
        self.assertEqual(self.r.status(self.revision)["state"], "superseded")
        self.assertEqual(self.r.status(revised)["state"], "proposed")
        self.assertCode("superseded_revision", lambda: self.r.phase_a(self.revision, self.target, "full", "Old", "New Reviewer", self.version()))

    def test_rejection_is_explicit_and_terminal(self):
        self.review(assessment=self.assessment("reject"))
        self.r.decide(self.revision, "reject", "Reviewer One", self.version())
        self.assertFalse(self.r.status(self.revision)["eligible"])
        self.assertCode("already_decided", lambda: self.r.decide(self.revision, "accept", "Reviewer One", self.version()))

    def test_policy_change_stales_approval(self):
        self.review()
        self.r.decide(self.revision, "accept", "Reviewer One", self.version())
        doc = dict(kind="policy", version="fixture/v2", source_citation="fixture update", authority=OWNER, text="Changed fixture")
        self.r.evidence("policy", doc, OWNER, self.version())
        self.assertEqual(self.r.status(self.revision)["state"], "stale")
        with self.r.store.transaction() as db:
            self.assertTrue(any(e["kind"] == "accepted" for e in self.r._events(db, self.revision)))

    def test_source_change_stales_approval(self):
        self.review()
        self.r.decide(self.revision, "accept", "Reviewer One", self.version())
        with (self.root / PRIMARY).open("a") as out:
            out.write("\nChanged fixture policy.\n")
        self.assertEqual(self.r.status(self.revision)["state"], "stale")
        self.assertCode("stale_evidence", lambda: self.r.view(self.revision, "Reviewer One", True, self.version()))

    def test_concurrent_write_rejected_without_partial_state(self):
        second = Review(self.root)
        version = self.version()
        self.r.phase_a(self.revision, self.target, "full", "First", "One", version)
        self.assertCode("concurrent_change", lambda: second.phase_a(self.revision, self.target, "full", "Second", "Two", version))

    def test_conflicting_revision_rejected(self):
        self.propose(parent=self.revision)
        conflicting = dict(action="wait", arguments={"event": "conflicting fixture event"}, draft=None)
        self.assertCode("revision_conflict", lambda: self.propose(conflicting, parent=self.revision))

    def test_no_replay_duplicates(self):
        before = self.version()
        self.assertEqual(self.r.sync(OWNER, before), [self.packet])
        self.assertEqual(self.version(), before)
        self.assertEqual(self.propose(), self.revision)
        self.assertEqual(self.version(), before)

    def test_unmeasured_confidence_and_unknown_citation(self):
        actor = "Reviewer One"
        self.r.phase_a(self.revision, self.target, "full", "Independent", actor, self.version())
        self.r.view(self.revision, actor, True, self.version())
        assessment = self.assessment()
        assessment["confidence"] = 0.99
        self.assertCode("unmeasured_confidence", lambda: self.r.review(self.revision, assessment, actor, self.version()))
        assessment["confidence"] = None
        assessment["citations"] = ["fabricated"]
        self.assertCode("unknown_citation", lambda: self.r.review(self.revision, assessment, actor, self.version()))

    def test_missing_evidence_cannot_be_approved(self):
        assessment = self.assessment()
        assessment["missing_evidence"] = ["fixture missing fact"]
        self.review(assessment=assessment)
        self.assertCode("unresolved_evidence", lambda: self.r.decide(self.revision, "accept", "Reviewer One", self.version()))

    def test_capabilities_and_draft_claims(self):
        target = dict(action="lookup", arguments={"tool": "invented tool"}, draft=None)
        revision = self.propose(target, self.revision)
        self.review(revision=revision)
        self.assertCode("capability_unavailable", lambda: self.r.decide(revision, "accept", "Reviewer One", self.version()))
        facts = self.evidence("facts", "facts")
        style = self.evidence("style", "style")
        deps = {"policy": self.policy, "facts": facts, "style": style}
        draft = dict(action="answer", arguments={}, draft="I performed an action.")
        revised = self.propose(draft, revision, deps)
        self.review(revision=revised)
        self.assertCode("execution_claims_unverified", lambda: self.r.decide(revised, "accept", "Reviewer One", self.version()))

    def test_capture_replay_and_fixture_cannot_approve(self):
        actor = "Fixture Model"
        assessment = self.assessment()
        assessment["routine"] = True
        self.r.phase_a(self.revision, self.target, "full", "Fixture independent target", actor, self.version())
        self.r.view(self.revision, actor, True, self.version())
        record = self.capture_record(assessment)
        ref = self.r.capture(record, OWNER, self.version())
        version = self.version()
        self.assertEqual(self.r.capture(record, OWNER, version), ref)
        self.assertEqual(self.version(), version)
        self.r.review(self.revision, assessment, actor, self.version(), model_capture=ref)
        self.assertCode("fixture_not_model_approval", lambda: self.r.decide(self.revision, "accept", actor, self.version()))
        changed = copy.deepcopy(record)
        changed["prompt"] = "changed"
        changed["prompt_sha256"] = sha(b"changed")
        self.assertCode("attempt_identity_conflict", lambda: self.r.capture(changed, OWNER, self.version()))

    def test_uncertain_capture_and_live_calls_blocked(self):
        record = self.capture_record(self.target, status="uncertain")
        ref = self.r.capture(record, OWNER, self.version())
        self.assertCode("capture_result_mismatch", lambda: self.propose(parent=self.revision, method={"kind": "model", "ref": ref}))
        with self.assertRaises(ValidationError) as caught:
            self.r.call_model()
        self.assertEqual(caught.exception.code, "live_provider_disabled")

    def test_tampered_objects_and_missing_references(self):
        db = sqlite3.connect(self.r.store.path)
        try:
            db.execute("DROP TRIGGER objects_no_update")
            db.execute("UPDATE objects SET body='{}' WHERE ref=?", (self.policy,))
            db.commit()
        finally:
            db.close()
        with self.assertRaises(ValidationError) as caught:
            self.version()
        self.assertEqual(caught.exception.code, "object_tampered")

    def test_deleted_reference_detected(self):
        db = sqlite3.connect(self.r.store.path)
        try:
            db.execute("DROP TRIGGER objects_no_delete")
            db.execute("DELETE FROM objects WHERE ref=?", (self.policy,))
            db.commit()
        finally:
            db.close()
        with self.assertRaises(ValidationError) as caught:
            self.version()
        self.assertEqual(caught.exception.code, "missing_reference")

    def test_journal_truncation_detected(self):
        db = sqlite3.connect(self.r.store.path)
        try:
            db.execute("DROP TRIGGER events_no_delete")
            db.execute("DELETE FROM events WHERE seq=(SELECT max(seq) FROM events)")
            db.commit()
        finally:
            db.close()
        with self.assertRaises(ValidationError) as caught:
            self.version()
        self.assertEqual(caught.exception.code, "journal_head_mismatch")

    def test_private_permissions_and_safe_cli(self):
        self.assertEqual(os.stat(self.root / ".local").st_mode & 0o777, 0o700)
        self.assertEqual(os.stat(self.r.store.path).st_mode & 0o777, 0o600)
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(main(["verify", "--root", str(self.root)]), 0)
            self.assertEqual(main(["review", "--root", str(self.root), "--expected", str(self.version())]), 1)
        self.assertNotIn("SENTINEL", stdout.getvalue() + stderr.getvalue())
        self.assertIn("reviewer_required", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
