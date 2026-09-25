# Checkpoint 003 — user decisions and updated approval routing

Date: 2026-09-23.

## User decisions

- “Model approval for routine cases; humans handle uncertainty.”
- No approved product facts, campaign rules or desired-style examples are available.

These supersede the provisional human-signoff default and pending-reference question in checkpoints 001–002. Earlier checkpoints remain intact as historical records.

## Changes and rationale

- Updated the protocol to permit documented model approval of routine cases and require human resolution of uncertainty. Confidence alone is insufficient.
- Distinguished the dataset reviewer route from the target action `handoff_human`.
- Kept model-approved and human-approved quality tiers separate; proposed a 10% random human audit plus targeted checks. This sampling rate is a design default, not a user-specified requirement.
- Upgraded prepared review packets/templates to schema v2 with routing, generic approval provenance, human-audit metadata and target scope. No actual review records existed to migrate.
- Added a missing-reference bootstrap process. Source claims/flows and model-proposed style are not approved company authority. Action-only targets may proceed when independently supportable; unresolved full targets remain held.
- Preserved original source files and prior checkpoints. No model reviews, human approvals or training exports have been performed.

## Verification

Regenerated prepared artifacts with the source integrity checks. Confirmed 111 v2 context packets and review templates, blank approvals, false eligibility, unchanged source checksum and matching generated hashes.

## Next work

Build proposed claim/policy/style references with explicit uncertainty, then calibrate review routing. No existing approved reference collection will be requested again unless the user indicates one has become available.
