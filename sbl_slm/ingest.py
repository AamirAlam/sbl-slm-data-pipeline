"""Read-only ingestion and deterministic, unapproved phase-A packets."""
import json
import re
from pathlib import Path

from .schema import (SCHEMA_VERSION, TAXONOMY_VERSION, CANONICAL_VERSION,
                     ValidationError, require, sha, content_hash, validate_candidate)


def decode(data, location):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate_json_key", location)
            result[key] = value
        return result
    def invalid_constant(_):
        raise ValidationError("nonfinite_json_number", location)
    try:
        return json.loads(data, object_pairs_hook=unique, parse_constant=invalid_constant)
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, ValidationError):
            raise
        raise ValidationError("invalid_json", location) from None


def jsonl(data, location):
    # splitlines also splits U+2028 and other characters legal inside JSON strings.
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    require(bool(lines), "empty_jsonl", location)
    return [decode(line, f"{location}:{i}") for i, line in enumerate(lines, 1)]


def source_files(root):
    return sorted(p for name in ("data", "ADRs") for p in (root / name).rglob("*") if p.is_file())


def snapshot(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in source_files(root)}


def discover_adr(root, primary, companion, blobs):
    paths = [primary] + ([companion] if companion else [])
    result = []
    for rel in paths:
        try:
            text = blobs[rel].decode("utf-8")
        except UnicodeError:
            raise ValidationError("invalid_adr_encoding", rel) from None
        match = re.match(r"# (ADR-\d+):[^\n]+", text)
        require(match is not None, "unsupported_adr_format", rel)
        status = re.search(r"^Status: (.+)$", text, re.MULTILINE)
        require(status is not None, "missing_adr_status", rel)
        result.append({"identity": match[1], "path": rel, "sha256": sha(blobs[rel]),
                       "status": status[1].strip(), "status_line": text[:status.start()].count("\n") + 1})
    if companion:
        require(result[0]["identity"] == result[1]["identity"], "adr_identity_conflict", companion)
        require(f"]({Path(primary).name})" in blobs[companion].decode("utf-8"),
                "ambiguous_adr_companion", companion)
    return {"identity": result[0]["identity"], "representations": result}


def ingest(root, primary="ADRs/001-decision-point-curation-and-review.md",
           companion="ADRs/001-decision-point-curation-and-review-plain-english.md"):
    root = Path(root).resolve()
    before = snapshot(root)
    selected = ["data/candidates.jsonl", "data/candidates-readable.json", "data/manifest.jsonl", primary]
    if companion:
        selected.append(companion)
    blobs = {}
    for rel in selected:
        path = (root / rel).resolve()
        require(path.is_relative_to(root) and rel in before, "invalid_source_path", "selection")
        blobs[rel] = path.read_bytes()
        require(sha(blobs[rel]) == before[rel], "source_changed", rel)
    rows = jsonl(blobs[selected[0]], selected[0])
    readable = decode(blobs[selected[1]], selected[1])
    manifests = jsonl(blobs[selected[2]], selected[2])
    require(len(manifests) == 1 and type(manifests[0]) is dict, "invalid_manifest", selected[2])
    manifest = manifests[0]
    require(manifest.get("candidates_sha256") == sha(blobs[selected[0]]), "checksum_mismatch", selected[2])
    require(type(readable) is list, "invalid_readable_representation", selected[1])
    representations = []
    for items, name in ((rows, selected[0]), (readable, selected[1])):
        indexed = {}
        for i, row in enumerate(items, 1):
            loc = f"{name}:{i}"
            validate_candidate(row, loc)
            require(row["id"] not in indexed, "duplicate_source_id", loc)
            indexed[row["id"]] = row
        representations.append(indexed)
    require(representations[0] == representations[1], "representation_mismatch", selected[1])
    require(type(manifest.get("candidate_decision_count")) is int and manifest["candidate_decision_count"] == len(rows), "count_mismatch", selected[2])
    counts = {key: sum(row["split"] == key for row in rows) for key in ("train", "validation", "test")}
    require(type(manifest.get("split_counts")) is dict and
            all(type(v) is int for v in manifest["split_counts"].values()) and
            manifest["split_counts"] == counts, "split_count_mismatch", selected[2])
    adr = discover_adr(root, primary, companion, blobs)
    packets = []
    identities = set()
    for i, row in enumerate(rows, 1):
        # Context is a current snapshot, not established historical evidence.
        x = {"history": [{key: m[key] for key in ("text", "speaker", "message_ids", "created_at", "last_created_at")} for m in row["history"]],
             "context": None, "channel": row["channel"], "trigger": row["trigger"],
             "limitations": sorted(set(row["flags"]) | {"context_not_historically_verified", "trigger_semantics_unverified", "capabilities_not_supplied", "event_order_not_verified", "source_timezone_not_verified"})}
        identity = content_hash({"namespace": "decision/v1", "tenant_id": row["tenant_id"], "source_id": row["id"]})
        require(identity not in identities, "derived_identity_collision", f"candidate:{i}")
        identities.add(identity)
        packet = {"schema_version": SCHEMA_VERSION, "taxonomy_version": TAXONOMY_VERSION,
                  "canonical_version": CANONICAL_VERSION, "decision_id": identity,
                  "source": {"path": selected[0], "line": i, "id": row["id"], "file_sha256": before[selected[0]],
                             "record_sha256": content_hash(row), "source_message_ids": row["source_message_ids"],
                             "representations": [{"path": name, "sha256": before[name]} for name in selected[:3]]},
                  "group": {key: row[key] for key in ("tenant_id", "prospect_id", "thread_id", "campaign_id")},
                  "split": row["split"], "adr": adr, "mode": "historical_replay",
                  "X": x, "input_sha256": content_hash(x), "Y": None,
                  "review_status": "unreviewed", "training_eligible": False}
        packet["revision_id"] = content_hash(packet)
        packets.append(packet)
    require(snapshot(root) == before, "source_changed", "source_snapshot")
    return {"schema_version": SCHEMA_VERSION, "source_snapshot": before,
            "split_counts": counts, "packets": packets}
