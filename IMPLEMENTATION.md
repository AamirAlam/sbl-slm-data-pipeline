# Implementation design for plan review

Status: proposed; specification approved, implementation plan not yet approved.
The canonical task scopes, dependencies and gates are managed by Genesis and
rendered in `.genesis/PLAN.md`. No application code or tests exist yet.

## Runtime and storage

Use Python 3 and its standard library: `sqlite3` for transactional local state,
`json` and `hashlib` for artifacts, `unittest` for fixture checks, and a small
loopback HTTP server with plain HTML, CSS and JavaScript for review. No frontend
build pipeline, ORM, model SDK or application dependency is initially needed.
Verify the installed Python/SQLite versions during IMP-1 and document the tested
runtime. Reconsider the server only if browser requirements exceed this bounded
local tool; no public hosting is included.

Keep existing ADRs and `data/` read-only. Put private derived state in an ignored
`.local/` directory with restrictive filesystem permissions: SQLite database,
captured attempts and release files. Add ignore rules before generating private
artifacts. Never stage private source data or captured prompts as part of a task.
Preserve source and policy hashes; do not overwrite existing checkpoints.

SQLite stores immutable revisions and append-only review/audit events. A
transaction checks the expected prior revision before updating current pointers.
Application-level append-only rules and hashes detect corruption; they do not
claim protection against a malicious administrator. Store sensitive captured
results privately with hashes and explicit provenance. No fabricated fixture
result can qualify as an actual model review.

## Operator and reviewer flow

`python3 -m sbl_slm.cli` will expose ingest, propose, validate, serve, export,
resume and rollback operations. Commands return safe IDs/counts and errors;
private conversation text appears only in the local review interface.

The web server binds to `127.0.0.1`. Require a self-declared reviewer name and
explicit action for every review. Check Host/Origin and use a per-session
anti-CSRF token for mutations; this does not add user authentication. Escape
conversation content and render it as text. Before phase A is saved, the server
must omit the observed response from every browser payload, not merely hide it.

Reviews separately assess action correctness, factual support, intent, policy
and style. Save action arguments and draft approval scope explicitly. Missing
evidence, unclear policy and disagreement require humans; final disagreement
resolution requires an explicit owner adjudication event. Revisions and changed
dependencies invalidate eligibility without erasing prior approval history.

The selected review settings are `model: gpt-6-astra` and
`reasoning_effort: low`. This plan implements capture/replay and the provider
permission boundary, not live inference. Enabling live calls requires recorded
provider retention and data-use authority plus a separately scoped integration.
No silent model substitution or automatic retry after an uncertain external
outcome is permitted.

## Releases and reproducibility

Freeze eligible exact revision IDs before selecting the uniform random 10%
human audit sample, rounded up. Save the seed, algorithm version, population,
sample and outcomes. A material failure blocks publication pending adjudication
and re-review; changing the population produces a new recorded sampling event.

Check source/message/prospect identities, exact content and normalized content
across partitions. Require recorded human near-duplicate review; do not claim
automatic semantic detection. Preserve existing split membership. Keep holdout
content out of development and report `not_supplied` when absent.

Produce one canonical UTF-8 JSON release containing `schema_version`, `manifest`
and `partitions` (`train`, `validation`, `test`, and a separate holdout when
supplied). Examples contain source/revision references, X, Y, supervision scope
and an audit reference. Detailed private rationale remains outside X/Y. Define
canonical key ordering, Unicode normalization, newline and numeric handling in
the versioned exporter contract. Keep timestamps of repeated export executions
outside deterministic payloads. Put the release-file hash in a separate checksum
sidecar to avoid a self-referential hash.

Validate before atomic publication; retain immutable releases and atomically
replace the active pointer. Require a permitted-data-use declaration for real
training/evaluation releases. Fixture exports exercise the full mechanism without
granting real-data permission. Rollback changes pointers, not accepted history.

## Sequence and verification

1. **IMP-1:** validate sources, schema and independent X packets. Snapshot source
   hashes and preserve opaque IDs. Invented fixture failures cover malformed
   inputs, conflicting duplicates and response/future-event leakage.
2. **IMP-2:** implement transactional reviews, provenance, evidence invalidation,
   concurrent-write rejection and the disabled provider boundary.
3. **IMP-3:** expose the review workflow locally. In addition to HTTP tests,
   independently walk all review outcomes in a real browser with invented
   fixtures; attach safe evidence to the human review gate. Check mobile layout,
   keyboard operation and phase-A data separation.
4. **IMP-4:** implement auditing, partition checks, reports and deterministic
   release publication. Demonstrate identical bytes on unchanged replay and
   visible exclusion reasons for ineligible cases.
5. **IMP-5:** exercise interrupted writes/publication, uncertain external-attempt
   reconciliation using fixtures, explicit derived migrations and rollback.
   Run the full accumulated regression suite and recheck source immutability.

Each task depends on its predecessor. Only IMP-1 is eligible to start after plan
approval; later tasks remain queued until predecessor proof and independent
human review pass. The full backlog provides coverage of all 57 requirements
without treating the entire product as one implementation task.

The commands in the generated plan are future executable gates. Implement their
test modules within each task; a missing module must fail rather than count as
success. No product tests have run at planning time. Re-run accumulated relevant
tests whenever a task changes shared modules, after checking Genesis impact.
Every medium-risk task also requires independent human review of current source
and proof. Plan approval does not satisfy those review gates.

Operational limits remain explicit: no actual model training, no supplied
holdout, no inferred product facts, no provider/data-use permissions invented by
this plan, and no broad quality claims from three test decisions.
