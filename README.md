# SBL decision-point curation

IMP-1 provides read-only ingestion and deterministic, unreviewed phase-A packets.
The review database, web interface, audit/export and recovery are later tasks.
No model calls, labels or accepted training examples are produced by ingestion.

## Run

```sh
python3 -m sbl_slm.cli ingest
python3 -m unittest -v tests.test_ingest
```

Uses only Python's standard library. Verified with Python 3.14.7 and SQLite
3.53.4; SQLite is reserved for the next task. Run from this repository or use
`--root PATH`. `--adr RELATIVE_PATH` selects a primary Markdown ADR;
`--companion RELATIVE_PATH` selects its companion (`--companion ''` omits it).
Only files inside the selected root's `ADRs/` and `data/` are valid inputs.

The CLI prints safe counts and a deterministic bundle checksum, never source
text. It validates all 111 current candidates, preserving 93 train, 15 validation
and 3 test assignments. Any integrity error fails the entire operation with a
structured reason and source location; no partial accepted output is returned.
The library entry point `sbl_slm.ingest.ingest(root)` returns private packets in
memory. Do not print or commit them. Disk persistence will be added in IMP-2.

## Packet contract

- `decision_id` hashes the versioned namespace, original tenant ID and source ID.
  `revision_id` hashes the entire packet before adding the revision field.
- Source references retain the JSONL record's physical line, original ID,
  source-message IDs, file/record hashes and equivalent representation hashes.
- `X` contains an explicit allowlist of earlier messages and opaque channel and
  trigger values. Current context is withheld because historical availability
  is not established. Observed replies, future metadata and prior approvals
  never enter X. History warnings and unverified event order, timezone, trigger
  semantics and capabilities remain explicit. Earlier mistaken replies remain
  in history. Naive source timestamps stay naive; no UTC assumption is invented.
- `Y` is null, status is `unreviewed`, and eligibility is false regardless of
  flags in the source. This is an input packet, not a proposal or approval.
- ADR companions share one identity; each file's path, checksum and status prose
  is retained. Unrecognized Markdown headers, missing status and conflicting or
  unlinked companions are rejected rather than guessed.
- Canonical version `json-sort-utf8-no-normalization/v1` sorts object keys, retains
  array order and original Unicode, forbids nonfinite numbers, uses compact JSON
  separators, and appends one LF. SHA-256 is applied to those UTF-8 bytes. JSONL
  is split on LF bytes, preserving legal Unicode separators inside strings.

Both input representations must contain the same unique records; representation
order may differ. IDs duplicated within either representation fail even if the
rows match. Manifest checksum, count and split counts must match the input.
Source snapshots cover all files under `data/` and `ADRs/` before and after each
successful ingestion. Nothing in this command writes to either directory.

Target shape validation recognizes the eight approved actions and distinguishes
an absent action-only draft from an explicitly approved null draft. It does not
approve targets or establish factual support, capabilities or argument semantics;
those require IMP-2 review checks.

Private derived storage will live under ignored `.local/`. Review configuration
is `gpt-6-astra` with `reasoning_effort: low`; live calls remain disabled pending
the provider/data-use conditions in the approved specification.
