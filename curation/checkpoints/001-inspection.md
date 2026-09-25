# Checkpoint 001 — source inspection

Date: 2026-09-23. Source files remain unchanged.

## Evidence

- 111 unique decision candidates, 26 threads, 25 prospects, three campaigns.
- JSONL matches the readable JSON exactly; its SHA-256 matches the supplied manifest.
- Existing split: 93 train / 15 validation / 3 test. No prospect or thread crosses these splits.
- All candidates are unreviewed and training-ineligible. All carry current-context, potentially truncated-history, unverified-delivery-time and pseudonymization warnings.
- 20 candidates have empty histories. Last visible speaker: prospect 72, company 14, system 5, empty 20.
- Observed speaker provenance: system 62, company 49. These are source labels, not verified authorship or approval.
- Knowledge and sender_style are null in all 111 inputs.

## Decisions and reasons

1. Preserve each existing decision as a review candidate; do not multiply overlapping histories into apparent new examples.
2. Separate context-only target authoring from observed-response evaluation, to reduce copying and anchoring.
3. Do not infer AI authorship from company age or company/system labels. Record unknown model, prompt and human approval explicitly.
4. Require context sufficiency assessment rather than rejecting all truncated histories or assuming all are sufficient.
5. Preserve original splits provisionally; three test decisions cannot support a broad performance claim.
6. Default the pilot to human approval for every accepted target, pending the user's preference.

## Inspection correction

An initial diagnostic used Python str.splitlines(), which also splits embedded Unicode line separators in valid JSON strings. This produced a false parsing alarm. File iteration with newline delimiters correctly reads all 111 JSONL records. No source repair was necessary.

## Pending

Approved historical/current product evidence, authoritative campaign rules, desired human style samples, and author/model execution logs are not supplied. Build review artifacts without inventing these or approving targets.
