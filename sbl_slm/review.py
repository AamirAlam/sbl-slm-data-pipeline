"""Transactional review service. No external inference client is installed here."""
from .ingest import ingest, jsonl
from .schema import (ValidationError, require, canonical, sha, content_hash,
                     validate_target, timestamp, strings)
from .store import Store

DIMENSIONS = {"correctness", "factual_support", "intent", "policy", "style"}
MODEL_SETTINGS = {"model": "gpt-6-astra", "reasoning_effort": "low"}


class Review:
    def __init__(self, root):
        self.store = Store(root)
        self.root = self.store.root

    def initialize(self, owner, expected):
        with self.store.transaction(expected) as db:
            prior = [e for e in self.store.events(db) if e["kind"] == "owner"]
            require(not prior or prior[0]["actor"] == owner, "owner_already_set", "owner")
            if not prior:
                self.store.append(db, "owner", owner, {})

    def _owner(self, db, actor):
        owners = [e["actor"] for e in self.store.events(db) if e["kind"] == "owner"]
        require(owners and owners[0] == actor, "owner_required", "actor")

    def sync(self, actor, expected):
        bundle = ingest(self.root)
        with self.store.transaction(expected) as db:
            known = {e["data"]["packet"] for e in self.store.events(db) if e["kind"] == "packet"}
            refs = []
            for packet in bundle["packets"]:
                ref = self.store.put(db, packet)
                refs.append(ref)
                if ref not in known:
                    self.store.append(db, "packet", actor, {"packet": ref}, [ref])
            return refs

    def evidence(self, key, document, actor, expected):
        require(type(key) is str and bool(key.strip()), "evidence_key_required", "evidence")
        require(type(document) is dict, "invalid_evidence", "evidence")
        for field in ("version", "source_citation", "authority", "text"):
            require(type(document.get(field)) is str and bool(document[field].strip()), "incomplete_evidence", field)
        require(document.get("kind") in ("policy", "facts", "style", "capabilities", "measurement", "rule"),
                "invalid_evidence_kind", "evidence")
        with self.store.transaction(expected) as db:
            self._owner(db, actor)
            ref = self.store.put(db, document)
            current = self._evidence(db)
            if current.get(key) != ref:
                self.store.append(db, "evidence", actor, {"key": key, "ref": ref}, [ref])
            return ref

    def _evidence(self, db):
        return {e["data"]["key"]: e["data"]["ref"] for e in self.store.events(db) if e["kind"] == "evidence"}

    def capture(self, record, actor, expected):
        """Import a real or explicitly synthetic attempt; neither implies approval."""
        require(type(record) is dict, "invalid_capture", "capture")
        for field in ("attempt_id", "provider", "prompt_version", "started_at", "finished_at"):
            require(type(record.get(field)) is str and bool(record[field]), "incomplete_capture", field)
        require(record.get("settings") == MODEL_SETTINGS, "unexpected_model_settings", "capture")
        require(type(record.get("prompt")) is str and record.get("prompt_sha256") == sha(record["prompt"].encode()),
                "prompt_hash_mismatch", "capture")
        require(type(record.get("request")) is dict and "result" in record, "missing_capture_payload", "capture")
        require(record.get("status") in ("completed", "uncertain", "failed"), "invalid_attempt_status", "capture")
        require(type(record.get("fixture")) is bool, "fixture_status_required", "capture")
        start, end = timestamp(record["started_at"], "started_at"), timestamp(record["finished_at"], "finished_at")
        require(start.utcoffset() is not None and end.utcoffset() is not None and end >= start, "invalid_attempt_time", "capture")
        with self.store.transaction(expected) as db:
            self._owner(db, actor)
            ref = self.store.put(db, record)
            prior = [e for e in self.store.events(db) if e["kind"] == "capture" and e["data"]["attempt_id"] == record["attempt_id"]]
            require(not prior or prior[0]["data"]["ref"] == ref, "attempt_identity_conflict", "capture")
            if not prior:
                self.store.append(db, "capture", actor, {"attempt_id": record["attempt_id"], "ref": ref}, [ref])
            return ref

    def _method(self, db, method, actor, target):
        require(type(method) is dict, "method_required", "method")
        kind = method.get("kind")
        require(kind in ("human", "rule", "model"), "invalid_method", "method")
        if kind == "human":
            require(method.get("actor") == actor, "method_actor_mismatch", "method")
            return []
        ref = method.get("ref")
        record = self.store.get(db, ref)
        if kind == "rule":
            require(record.get("kind") == "rule" and ref in self._evidence(db).values(), "unapproved_rule", "method")
        else:
            require(any(e["kind"] == "capture" and e["data"]["ref"] == ref for e in self.store.events(db)), "unregistered_capture", "method")
            require(record["status"] == "completed" and record["result"] == target, "capture_result_mismatch", "method")
        return [ref]

    def propose(self, packet_ref, target, scope, dependencies, method, actor, expected, parent=None):
        validate_target(target, scope)
        require(type(dependencies) is dict, "invalid_dependencies", "proposal")
        with self.store.transaction(expected) as db:
            packet = self.store.get(db, packet_ref)
            require(any(e["kind"] == "packet" and e["data"]["packet"] == packet_ref for e in self.store.events(db)), "packet_not_ingested", "proposal")
            current = self._evidence(db)
            require(all(current.get(key) == ref for key, ref in dependencies.items()), "stale_dependency", "proposal")
            method_refs = self._method(db, method, actor, target)
            if method.get("kind") == "model":
                capture = self.store.get(db, method["ref"])
                require(capture["request"].get("input_sha256") == packet["input_sha256"], "capture_input_mismatch", "proposal")
            proposal = dict(packet=packet_ref, decision_id=packet["decision_id"], target=target, scope=scope,
                            dependencies=dependencies, method=method, parent=parent)
            ref = self.store.put(db, proposal)
            prior = [e for e in self.store.events(db) if e["kind"] == "proposed" and e["data"]["decision_id"] == packet["decision_id"]]
            if prior and prior[-1]["data"]["revision"] == ref:
                return ref
            require((not prior and parent is None) or (prior and prior[-1]["data"]["revision"] == parent), "revision_conflict", "proposal")
            refs = [ref, packet_ref, *dependencies.values(), *method_refs] + ([parent] if parent else [])
            self.store.append(db, "proposed", actor, {"revision": ref, "decision_id": packet["decision_id"], "parent": parent}, refs)
            return ref

    def _proposal(self, db, revision):
        proposal = self.store.get(db, revision)
        require(any(e["kind"] == "proposed" and e["data"]["revision"] == revision for e in self.store.events(db)), "unknown_proposal", "revision")
        return proposal

    def _events(self, db, revision):
        return [e for e in self.store.events(db) if e["data"].get("revision") == revision]

    def _fresh(self, db, proposal):
        current = self._evidence(db)
        if any(current.get(k) != v for k, v in proposal["dependencies"].items()):
            return False
        packet = self.store.get(db, proposal["packet"])
        sources = packet["source"]["representations"] + packet["adr"]["representations"]
        for source in sources:
            path = (self.root / source["path"]).resolve()
            if not path.is_relative_to(self.root) or not path.is_file() or sha(path.read_bytes()) != source["sha256"]:
                return False
        return True

    def _current(self, db, revision, proposal):
        prior = [e for e in self.store.events(db) if e["kind"] == "proposed" and e["data"]["decision_id"] == proposal["decision_id"]]
        require(prior[-1]["data"]["revision"] == revision, "superseded_revision", "revision")
        require(self._fresh(db, proposal), "stale_evidence", "revision")

    def phase_a(self, revision, target, scope, rationale, actor, expected):
        validate_target(target, scope)
        require(type(rationale) is str and bool(rationale.strip()), "rationale_required", "phase_a")
        with self.store.transaction(expected) as db:
            proposal = self._proposal(db, revision)
            self._current(db, revision, proposal)
            events = self._events(db, revision)
            require(not any(e["actor"] == actor and e["kind"] == "revealed" for e in events), "already_revealed", "phase_a")
            saved = dict(target=target, scope=scope, rationale=rationale)
            prior = [e for e in events if e["actor"] == actor and e["kind"] == "phase_a"]
            if prior:
                require(self.store.get(db, prior[0]["data"]["ref"]) == saved, "phase_a_immutable", "phase_a")
                return
            ref = self.store.put(db, saved)
            self.store.append(db, "phase_a", actor, {"revision": revision, "ref": ref}, [revision, ref])

    def view(self, revision, actor, reveal=False, expected=None):
        with self.store.transaction(expected) as db:
            proposal = self._proposal(db, revision)
            self._current(db, revision, proposal)
            packet = self.store.get(db, proposal["packet"])
            result = {"X": packet["X"], "revision": revision}
            if reveal:
                require(any(e["kind"] == "phase_a" and e["actor"] == actor for e in self._events(db, revision)), "phase_a_required", "review")
                source = packet["source"]
                data = (self.root / source["path"]).read_bytes()
                require(sha(data) == source["file_sha256"], "stale_evidence", "review")
                row = jsonl(data, "source")[source["line"] - 1]
                require(content_hash(row) == source["record_sha256"], "source_record_changed", "review")
                if not any(e["kind"] == "revealed" and e["actor"] == actor for e in self._events(db, revision)):
                    self.store.append(db, "revealed", actor, {"revision": revision}, [revision])
                result.update(target=proposal["target"], observed_response=row["observed_response"])
            result["version"] = self.store.verify(db)
            return result

    def _assessment(self, db, proposal, assessment):
        require(type(assessment) is dict, "invalid_assessment", "review")
        require(assessment.get("outcome") in ("accept", "reject", "revise", "uncertain"), "invalid_outcome", "review")
        dimensions = assessment.get("dimensions")
        require(type(dimensions) is dict and set(dimensions) == DIMENSIONS and
                all(v in ("pass", "fail", "uncertain", "not_applicable") for v in dimensions.values()), "invalid_dimensions", "review")
        for key in ("missing_evidence", "citations"):
            strings(assessment.get(key), key, nonempty=key == "citations")
        require(type(assessment.get("rationale")) is str and bool(assessment["rationale"].strip()), "rationale_required", "review")
        require(type(assessment.get("policy_clear")) is bool, "policy_status_required", "review")
        allowed = set(proposal["dependencies"].values()) | {proposal["packet"]}
        require(set(assessment["citations"]) <= allowed, "unknown_citation", "review")
        confidence = assessment.get("confidence")
        if confidence is not None:
            require(type(confidence) is dict and type(confidence.get("value")) in (int, float)
                    and 0 <= confidence["value"] <= 1 and confidence.get("method_version"), "unmeasured_confidence", "review")
            ref = confidence.get("evidence")
            require(ref in proposal["dependencies"].values() and self.store.get(db, ref).get("kind") == "measurement", "unmeasured_confidence", "review")

    def review(self, revision, assessment, actor, expected, model_capture=None):
        with self.store.transaction(expected) as db:
            proposal = self._proposal(db, revision)
            self._current(db, revision, proposal)
            events = self._events(db, revision)
            require(any(e["kind"] == "revealed" and e["actor"] == actor for e in events), "reveal_required", "review")
            require(not any(e["kind"] == "reviewed" and e["actor"] == actor for e in events), "review_already_recorded", "review")
            self._assessment(db, proposal, assessment)
            refs = [revision, *assessment["citations"]]
            if model_capture:
                capture = self.store.get(db, model_capture)
                require(any(e["kind"] == "capture" and e["data"]["ref"] == model_capture for e in self.store.events(db)), "unregistered_capture", "review")
                require(capture["status"] == "completed" and capture["result"] == assessment, "capture_result_mismatch", "review")
                require(capture["request"].get("revision") == revision and capture["request"].get("phase_a_saved") is True, "capture_input_mismatch", "review")
                refs.append(model_capture)
            payload = {**assessment, "model_capture": model_capture}
            ref = self.store.put(db, payload)
            self.store.append(db, "reviewed", actor, {"revision": revision, "ref": ref}, [ref, *refs])
            return ref

    def _reviews(self, db, revision):
        return [(e, self.store.get(db, e["data"]["ref"])) for e in self._events(db, revision) if e["kind"] == "reviewed"]

    def adjudicate(self, revision, assessment, actor, expected):
        with self.store.transaction(expected) as db:
            self._owner(db, actor)
            proposal = self._proposal(db, revision)
            self._current(db, revision, proposal)
            require(bool(self._reviews(db, revision)), "review_required", "adjudication")
            self._assessment(db, proposal, assessment)
            ref = self.store.put(db, {**assessment, "model_capture": None})
            self.store.append(db, "adjudicated", actor, {"revision": revision, "ref": ref}, [revision, ref, *assessment["citations"]])

    def _support(self, db, proposal, assessment):
        require(not assessment["missing_evidence"] and assessment["policy_clear"], "unresolved_evidence", "acceptance")
        dims = assessment["dimensions"]
        require(not any(v in ("fail", "uncertain") for v in dims.values()) and
                all(dims[k] == "pass" for k in ("correctness", "intent", "policy")), "failed_assessment", "acceptance")
        evidence = [self.store.get(db, ref) for ref in proposal["dependencies"].values()]
        require(any(e["kind"] == "policy" for e in evidence), "policy_evidence_required", "acceptance")
        target = proposal["target"]
        validate_target(target, proposal["scope"])
        if target["action"] in ("lookup", "handoff_human", "invite_next_step"):
            capabilities = [e for e in evidence if e["kind"] == "capabilities"]
            require(any(target["action"] in e.get("allowed_actions", []) for e in capabilities), "capability_unavailable", "acceptance")
            key = {"lookup": "tool", "handoff_human": "destination", "invite_next_step": "destination"}[target["action"]]
            value = target["arguments"].get(key)
            require(type(value) is str and any(value in e.get("destinations", []) for e in capabilities), "destination_unapproved", "acceptance")
        if target["action"] == "wait":
            require(type(target["arguments"].get("event")) is str and bool(target["arguments"]["event"].strip()), "wait_event_required", "acceptance")
        if proposal["scope"] == "full" and target.get("draft"):
            require(dims["factual_support"] == "pass" and dims["style"] == "pass" and
                    any(e["kind"] == "facts" for e in evidence) and any(e["kind"] == "style" for e in evidence), "draft_evidence_required", "acceptance")
            require(assessment.get("execution_claims_verified") is True, "execution_claims_unverified", "acceptance")

    def decide(self, revision, outcome, actor, expected):
        require(outcome in ("accept", "reject"), "invalid_decision", "decision")
        with self.store.transaction(expected) as db:
            proposal = self._proposal(db, revision)
            self._current(db, revision, proposal)
            events = self._events(db, revision)
            reviews = self._reviews(db, revision)
            require(bool(reviews), "review_required", "decision")
            require(not any(e["kind"] in ("accepted", "rejected") for e in events), "already_decided", "decision")
            disputes = len({r["outcome"] for _, r in reviews}) > 1 or len({canonical(r["dimensions"]) for _, r in reviews}) > 1
            adjudications = [e for e in events if e["kind"] == "adjudicated" and e["seq"] > max(e["seq"] for e, _ in reviews)]
            if disputes:
                require(bool(adjudications), "adjudication_required", "decision")
            if adjudications:
                event = adjudications[-1]
                chosen = self.store.get(db, event["data"]["ref"])
                self._owner(db, actor)
            else:
                own = [(e, r) for e, r in reviews if e["actor"] == actor]
                require(bool(own), "reviewer_required", "decision")
                event, chosen = own[-1]
                require(all(r["outcome"] == outcome for _, r in reviews), "unresolved_reviews", "decision")
            require(chosen["outcome"] == outcome, "review_outcome_mismatch", "decision")
            tier = "human"
            if outcome == "accept":
                self._support(db, proposal, chosen)
                if not adjudications:
                    for _, review in reviews:
                        self._support(db, proposal, review)
                if chosen.get("model_capture"):
                    capture = self.store.get(db, chosen["model_capture"])
                    require(not capture["fixture"], "fixture_not_model_approval", "decision")
                    require(not disputes and chosen.get("routine") is True, "human_review_required", "decision")
                    tier = "model"
            self.store.append(db, "accepted" if outcome == "accept" else "rejected", actor,
                              {"revision": revision, "review": event["data"]["ref"], "tier": tier}, [revision, event["data"]["ref"]])

    def status(self, revision):
        with self.store.transaction() as db:
            proposal = self._proposal(db, revision)
            events = self._events(db, revision)
            state, tier = "proposed", None
            for e in events:
                if e["kind"] == "reviewed":
                    review = self.store.get(db, e["data"]["ref"])
                    state = "needs-review" if review["outcome"] in ("uncertain", "revise") else "reviewed"
                if e["kind"] in ("accepted", "rejected"):
                    state, tier = e["kind"], e["data"]["tier"]
            # Later review activity conservatively invalidates prior acceptance.
            try:
                self._current(db, revision, proposal)
            except ValidationError as error:
                if error.code in ("superseded_revision", "stale_evidence"):
                    state = "superseded" if error.code == "superseded_revision" else "stale"
                else:
                    raise
            return {"revision": revision, "state": state, "approval_tier": tier,
                    "eligible": state == "accepted", "version": self.store.verify(db)}

    def call_model(self, *args, **kwargs):
        raise ValidationError("live_provider_disabled", "provider")
