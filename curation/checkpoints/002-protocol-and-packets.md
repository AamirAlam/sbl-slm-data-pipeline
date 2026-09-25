# Checkpoint 002 — protocol, prepared packets and verification

Date: 2026-09-23.

## Completed

- Wrote `curation/README.md`: decision unit, extraction boundaries, action vocabulary, two-phase review, historical versus desired-policy assessment, evidence gates, provenance, style, split policy and release process.
- Added `scripts/prepare_curation.py` and generated 111 context packets, 111 separately stored observations and 111 blank review templates.
- Saved reproducible audit and artifact checksums in `curation/generated/`.
- Read selected source cases to illustrate concrete review priorities. This is not a completed semantic review of all candidates.

## Decisions and reasons

- Keep all current candidates available for review; structural warnings alone do not determine individual learnability.
- Make no historical correctness claims without historical evidence. Permit explicitly versioned desired-policy reconstruction as a separate target mode.
- Require an action before an optional draft, with null drafts for lookup/wait, so training is not restricted to always replying.
- Retain no-action coverage as a known extraction gap: this source is centered on observed outbound decisions.
- Leave targets blank and all eligibility false. Approved product facts, style and human judgments have not been supplied.
- Use separate actual-review storage and revision IDs so preparation can be rerun without replacing review work.
- Do not add a UI, training run or exporter to this design/preparation task. A future exporter must enforce approval/evidence/split gates rather than trusting a boolean field.

## Validation

Successfully executed the preparation script. Verified all four generated artifact hashes, 111 matching decision-ID joins, absence of the current observed response from phase-A packets, blank targets, ineligible status, source checksum and representation equality, and absence of prospect/thread split overlap. The original source files were not edited.

## State and next checkpoint

Prepared: 111. Human reviewed: 0. Model reviewed under this rubric: 0. Approved: 0. Training exports: 0.

Questions sent to the user: final human approval versus routine model approval; location of approved product/policy/style references. Pending a reply, the protocol states a human-signoff default. Next checkpoint should record supplied evidence, resolved flow conflicts, reviewer calibration results and the exact review revisions created.
