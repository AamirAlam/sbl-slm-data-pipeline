"""Local curation commands; stdout contains safe metadata, never review text."""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

from .ingest import ingest, decode
from .review import Review
from .schema import ValidationError, content_hash, require

COMMANDS = ["ingest", "init", "sync", "evidence", "capture", "propose", "phase-a",
            "reveal", "review", "adjudicate", "decide", "status", "verify"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--root", default=".")
    parser.add_argument("--adr", default="ADRs/001-decision-point-curation-and-review.md")
    parser.add_argument("--companion", default="ADRs/001-decision-point-curation-and-review-plain-english.md")
    parser.add_argument("--actor")
    parser.add_argument("--expected", type=int)
    parser.add_argument("--input", help="Private JSON arguments file; contents never echoed")
    parser.add_argument("--revision")
    args = parser.parse_args(argv)
    try:
        if args.command == "ingest":
            result = ingest(args.root, args.adr, args.companion or None)
            summary = {"status": "validated", "candidate_count": len(result["packets"]),
                       "split_counts": result["split_counts"], "bundle_sha256": content_hash(result),
                       "accepted_count": 0, "training_eligible_count": 0}
        else:
            service = Review(args.root)
            if args.command == "verify":
                summary = {"status": "verified", "version": service.store.version()}
            elif args.command == "status":
                require(bool(args.revision), "revision_required", "arguments")
                summary = service.status(args.revision)
            else:
                require(type(args.actor) is str and bool(args.actor.strip()), "reviewer_required", "actor")
                require(args.expected is not None, "expected_version_required", "arguments")
                payload = decode(Path(args.input).read_bytes(), "arguments") if args.input else {}
                require(type(payload) is dict, "invalid_arguments", "arguments")
                if args.command == "init":
                    service.initialize(args.actor, args.expected)
                    result = None
                elif args.command == "sync":
                    result = service.sync(args.actor, args.expected)
                elif args.command == "reveal":
                    require(bool(args.revision), "revision_required", "arguments")
                    service.view(args.revision, args.actor, reveal=True, expected=args.expected)
                    result = None  # Private text is reserved for the local UI/library.
                else:
                    method = {"evidence": service.evidence, "capture": service.capture,
                              "propose": service.propose, "phase-a": service.phase_a,
                              "review": service.review, "adjudicate": service.adjudicate,
                              "decide": service.decide}[args.command]
                    require(not ({"actor", "expected"} & payload.keys()), "reserved_argument", "arguments")
                    result = method(**payload, actor=args.actor, expected=args.expected)
                summary = {"status": "recorded", "version": service.store.version()}
                if type(result) is str:
                    summary["ref"] = result
                elif type(result) is list:
                    summary["packet_refs"] = result
        print(json.dumps(summary, sort_keys=True))
        return 0
    except ValidationError as error:
        print(json.dumps({"status": "error", "code": error.code, "location": error.location}), file=sys.stderr)
    except (OSError, sqlite3.Error):
        print(json.dumps({"status": "error", "code": "storage_io_error"}), file=sys.stderr)
    except (TypeError, KeyError, ValueError):
        print(json.dumps({"status": "error", "code": "invalid_arguments_or_storage"}), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
