"""Partition-safe deterministic release generation."""
from .audit import select
from .schema import CANONICAL_VERSION, SCHEMA_VERSION, ValidationError, canonical, content_hash, require


class Exporter:
    def __init__(self, review):
        self.review = review
        self.store = review.store
        self.root = review.root

    def _accepted(self, db):
        result = {}
        for event in self.store.events(db):
            if event["kind"] == "accepted":
                result[event["data"]["revision"]] = event
            elif event["kind"] in ("rejected", "superseded"):
                result.pop(event["data"].get("revision"), None)
        return result

    def _record(self, db, revision):
        proposal = self.store.get(db, revision)
        packet = self.store.get(db, proposal["packet"])
        return proposal, packet

    def _audit_refs(self, db):
        refs = {}
        for event in self.store.events(db):
            if event["kind"] == "audit_sample":
                sample = self.store.get(db, event["data"]["ref"])
                for revision in sample["selected"]:
                    refs[revision] = event["data"]["ref"]
            if event["kind"] == "audit_result":
                refs[event["data"]["revision"]] = event["data"]["ref"]
        return refs

    def freeze_audit(self, actor, seed, expected):
        with self.store.transaction(expected) as db:
            accepted = self._accepted(db)
            routine = []
            for revision, event in accepted.items():
                if event["data"]["tier"] == "model":
                    routine.append(revision)
            sample = select(routine, seed)
            ref = self.store.put(db, sample)
            self.store.append(db, "audit_sample", actor, {"ref": ref}, [ref, *sample["selected"]])
            return ref, sample

    def audit(self, revision, passed, actor, expected, reason=""):
        require(type(passed) is bool, "audit_result_required", "audit")
        require(passed or bool(reason.strip()), "audit_reason_required", "audit")
        with self.store.transaction(expected) as db:
            require(revision in self._accepted(db), "revision_not_accepted", "audit")
            value = {"revision": revision, "passed": passed, "reason": reason}
            ref = self.store.put(db, value)
            self.store.append(db, "audit_result", actor, {"revision": revision, "ref": ref}, [revision, ref])
            return ref

    def build(self, actor, expected, fixture=False, holdout=None):
        with self.store.transaction(expected) as db:
            accepted = self._accepted(db)
            audits = self._audit_refs(db)
            examples = {"train": [], "validation": [], "test": []}
            seen_ids, seen_messages, seen_prospects = {}, {}, {}
            excluded = []
            for revision, event in sorted(accepted.items()):
                proposal, packet = self._record(db, revision)
                if not self.review._fresh(db, proposal):
                    excluded.append({"revision": revision, "reason": "stale_or_ineligible"}); continue
                if event["data"]["tier"] == "model" and revision not in audits:
                    excluded.append({"revision": revision, "reason": "routine_audit_missing"}); continue
                split = packet["split"]
                identities = [(seen_ids, packet["source"]["id"]), (seen_prospects, packet["group"]["prospect_id"])]
                for seen, value in identities:
                    if value in seen and seen[value] != split:
                        raise ValidationError("cross_partition_conflict", "release")
                    seen[value] = split
                for message in packet["source"]["source_message_ids"]:
                    if message in seen_messages and seen_messages[message] != split:
                        raise ValidationError("cross_partition_conflict", "release")
                    seen_messages[message] = split
                target = proposal["target"]
                item = {"revision_id": revision, "decision_id": packet["decision_id"],
                        "source_id": packet["source"]["id"], "X": packet["X"], "Y": target,
                        "supervision_scope": proposal["scope"], "approval_tier": event["data"]["tier"],
                        "audit_ref": audits.get(revision)}
                examples[split].append(item)
            require(fixture or bool(self._data_use_allowed(db)), "data_use_permission_required", "release")
            result = {"schema_version": SCHEMA_VERSION, "canonical_version": CANONICAL_VERSION,
                      "holdout_status": "supplied" if holdout else "not_supplied",
                      "manifest": {"revision_ids": sorted(x["revision_id"] for values in examples.values() for x in values),
                                   "excluded": excluded, "partitions": {k: len(v) for k, v in examples.items()},
                                   "audit_algorithm": "python-random-sample/v1"},
                      "partitions": examples}
            result["manifest"]["release_sha256"] = content_hash({k: v for k, v in result.items() if k != "manifest"})
            return result, canonical(result)

    def _data_use_allowed(self, db):
        return any(e["kind"] == "evidence" and e["data"].get("key") == "data_use"
                   and self.store.get(db, e["data"]["ref"]).get("allowed") is True
                   for e in self.store.events(db))
