"""Version-one contracts; validation errors never echo private field values."""
import hashlib
import json
from datetime import datetime

SCHEMA_VERSION = "decision-packet/v1"
TAXONOMY_VERSION = "actions/v1"
CANONICAL_VERSION = "json-sort-utf8-no-normalization/v1"
ACTIONS = frozenset(("answer", "clarify", "qualify", "invite_next_step",
                     "handoff_human", "lookup", "wait", "stop"))


class ValidationError(ValueError):
    def __init__(self, code, location="input"):
        self.code, self.location = code, location
        super().__init__(f"{code} at {location}")


def require(condition, code, location):
    if not condition:
        raise ValidationError(code, location)


def canonical(value):
    # No normalization of private text: original Unicode is part of identity.
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def content_hash(value):
    return sha(canonical(value))


def strings(value, location, nonempty=False):
    require(type(value) is list and all(type(x) is str and x for x in value),
            "invalid_string_list", location)
    require(not nonempty or bool(value), "empty_list", location)


def timestamp(value, location):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed
    except (AttributeError, TypeError, ValueError):
        raise ValidationError("invalid_timestamp", location) from None


def validate_candidate(row, location):
    require(type(row) is dict, "expected_object", location)
    for key in ("id", "tenant_id", "prospect_id", "thread_id", "campaign_id",
                "speaker_provenance", "observed_at", "snapshot_at", "review_status"):
        require(type(row.get(key)) is str and bool(row[key]), "missing_or_invalid_field", location + "." + key)
    require(type(row.get("observed_response")) is str, "invalid_response", location)
    require(row.get("split") in ("train", "validation", "test"), "invalid_split", location)
    require(type(row.get("training_eligible")) is bool, "invalid_eligibility", location)
    for key in ("trigger", "channel"):
        require(type(row.get(key)) is int, "invalid_integer", location + "." + key)
    for key in ("flags", "source_message_ids"):
        strings(row.get(key), location + "." + key, nonempty=key == "source_message_ids")
    require(len(set(row["source_message_ids"])) == len(row["source_message_ids"]), "duplicate_message_id", location)
    require(type(row.get("context")) is dict, "invalid_context", location)
    require(type(row.get("history")) is list, "invalid_history", location)
    boundary = timestamp(row["observed_at"], location + ".observed_at")
    timestamp(row["snapshot_at"], location + ".snapshot_at")
    seen = set(row["source_message_ids"])
    previous = None
    for i, message in enumerate(row["history"]):
        loc = f"{location}.history[{i}]"
        require(type(message) is dict, "invalid_history_message", loc)
        for key in ("text", "speaker"):
            require(type(message.get(key)) is str, "invalid_history_field", loc + "." + key)
        strings(message.get("message_ids"), loc + ".message_ids", nonempty=True)
        require(len(set(message["message_ids"])) == len(message["message_ids"]), "duplicate_message_id", loc)
        require(not seen.intersection(message["message_ids"]), "history_message_overlap", loc)
        seen.update(message["message_ids"])
        start = timestamp(message.get("created_at"), loc + ".created_at")
        end = timestamp(message.get("last_created_at"), loc + ".last_created_at")
        require(all((t.tzinfo is None) == (boundary.tzinfo is None) for t in (start, end)),
                "mixed_timestamp_zones", loc)
        require(start <= end <= boundary and (previous is None or previous <= start), "invalid_history_order", loc)
        previous = end


def validate_target(target, scope="full"):
    require(type(target) is dict, "invalid_target", "target")
    require(scope in ("action_only", "full"), "invalid_scope", "target")
    require(type(target.get("action")) is str and target["action"] in ACTIONS, "invalid_action", "target.action")
    require(type(target.get("arguments")) is dict, "invalid_arguments", "target.arguments")
    require(set(target) <= {"action", "arguments", "draft"}, "unknown_target_field", "target")
    if scope == "action_only":
        require("draft" not in target, "unapproved_draft", "target")
        return
    require("draft" in target, "missing_draft_approval", "target")
    draft = target["draft"]
    require(draft is None or type(draft) is str, "invalid_draft", "target")
    if target["action"] in ("answer", "clarify", "qualify", "invite_next_step"):
        require(type(draft) is str and bool(draft.strip()), "draft_required", "target")
    if target["action"] in ("lookup", "wait"):
        require(draft is None, "draft_forbidden", "target")
    # Capability, policy and argument semantics are review checks in IMP-2.
