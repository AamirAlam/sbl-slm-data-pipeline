import json
import secrets
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from sbl_slm.ingest import snapshot
from sbl_slm.review import Review
from sbl_slm.schema import canonical, sha
from sbl_slm.web import dispatch
from tests.test_ingest import candidate, PRIMARY, COMPANION


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir(); (self.root / "ADRs").mkdir()
        (self.root / PRIMARY).write_text("# ADR-001: Fixture\nStatus: Fixture.\n")
        (self.root / COMPANION).write_text("# ADR-001: Companion\nStatus: Fixture.\n[Original](001-decision-point-curation-and-review.md)\n")
        data = canonical(candidate())
        (self.root / "data/candidates.jsonl").write_bytes(data)
        (self.root / "data/candidates-readable.json").write_bytes(canonical([candidate()]))
        (self.root / "data/manifest.jsonl").write_bytes(canonical(dict(candidates_sha256=sha(data), candidate_decision_count=1, split_counts=dict(train=1, validation=0, test=0))))
        self.before = snapshot(self.root)
        self.review = Review(self.root); self.review.initialize("Owner", 0)
        self.packet = self.review.sync("Owner", self.review.store.version())[0]
        self.policy = self.review.evidence("policy", dict(kind="policy", version="v1", source_citation="fixture", authority="Owner", text="fixture policy"), "Owner", self.review.store.version())
        self.revision = self.review.propose(self.packet, dict(action="wait", arguments={"event":"fixture event"}, draft=None), "full", {"policy": self.policy}, {"kind":"human","actor":"Owner"}, "Owner", self.review.store.version())
        self.server = SimpleNamespace(review=self.review, csrf=secrets.token_urlsafe(24))

    def close(self):
        pass

    def request(self, path, method="GET", body=None, csrf=None, host=None):
        headers = [f"Host: {host or '127.0.0.1'}", "Connection: close"]
        if body is not None:
            raw = json.dumps(body).encode(); headers += ["Content-Type: application/json", f"Content-Length: {len(raw)}", f"X-CSRF-Token: {csrf or ''}"]
        else:
            raw = b""
        request = f"{method} {path} HTTP/1.1\r\n" + "\r\n".join(headers) + "\r\n\r\n"
        response_headers = {item.split(": ", 1)[0]: item.split(": ", 1)[1] for item in headers if ": " in item}
        status, extra_headers, response = dispatch(self.server, method, path, response_headers, body)
        response_headers.update(extra_headers)
        return status, response_headers, response if isinstance(response, str) else json.dumps(response)

    def test_loopback_review_hides_response_until_phase_a(self):
        status, headers, body = self.request("/review?revision=" + self.revision)
        self.assertEqual(status, 200)
        self.assertIn("hidden until phase A is saved", body)
        self.assertNotIn("OBSERVATION_SENTINEL", body)
        self.assertNotIn("genesis", body.lower())
        self.assertNotIn("dashboard", body.lower())
        self.assertIn("Save phase A", body)
        self.assertIn("Content-Security-Policy", headers)
        csrf = self.server.csrf
        payload = dict(revision=self.revision, actor="Reviewer", target=dict(action="wait", arguments={"event":"fixture event"}, draft=None), scope="full", rationale="Context-first fixture rationale")
        status, _, body = self.request("/phase-a", "POST", payload, csrf)
        self.assertEqual(status, 200); self.assertIn("saved", body)
        status, _, body = self.request("/reveal", "POST", dict(revision=self.revision, actor="Reviewer"), csrf)
        self.assertEqual(status, 200); self.assertIn("OBSERVATION_SENTINEL", body)
        self.assertEqual(snapshot(self.root), self.before)

    def test_csrf_host_and_phase_rules(self):
        status, _, body = self.request("/reveal", "POST", dict(revision=self.revision, actor="Reviewer"))
        self.assertEqual(status, 400); self.assertIn("csrf_required", body)
        status, _, body = self.request("/reveal", "POST", dict(revision=self.revision, actor="Reviewer"), self.server.csrf)
        self.assertEqual(status, 400); self.assertIn("phase_a_required", body)
        status, _, body = self.request("/review?revision=" + self.revision, host="192.0.2.1")
        self.assertEqual(status, 200)  # GET is harmless; mutations enforce loopback Host.
        status, _, body = self.request("/reveal", "POST", dict(revision=self.revision, actor="Reviewer"), self.server.csrf, host="192.0.2.1")
        self.assertEqual(status, 403); self.assertIn("loopback_only", body)

    def test_unknown_route_and_xss_escaping(self):
        status, _, body = self.request("/missing")
        self.assertEqual(status, 404); self.assertIn("not_found", body)
        status, _, body = self.request("/review?revision=" + self.revision)
        self.assertNotIn("<script>alert", body)
        self.assertIn("&quot;", body)


if __name__ == "__main__":
    unittest.main()
