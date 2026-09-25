# Product specification — sbl-slm

Date: 2026-09-25. Status: draft for human review; not approved.

Active Genesis task: SPEC-1. This is an existing repository. The CLI's `new-product` specification-workflow name does not authorize reinitialization or replacement of existing files. Only specification work is active. Explicit specification approval and a subsequent, separate implementation-plan approval are required before product code is written.

Statements marked **proposed** are concrete options for review, not recorded user decisions. The proposed release boundary below keeps unresolved external-data permissions disabled; approving the specification would accept that boundary, not invent those permissions. A successful `genesis spec check .` checks document structure and identifiers; it does not demonstrate product behavior, privacy compliance, label correctness or human approval.

## Problem

Integrate a verifiable conversation data-labeling and decision workflow governed by the repository's ADRs. Preserve the existing structure and source data. Produce reviewed next-action targets and optional drafts, with sufficient provenance to explain and reproduce accepted artifacts for downstream SLM training or evaluation.

The labeling subjects are **conversation decision points**, not the ADR documents themselves. ADR-001 supplies design rationale and applicable policy references. A historical observed response is evidence to assess, not an automatically correct target.

### Confirmed user decisions

- X contains context and conversation history available before the decision. Y is a reviewed next action, its arguments and an optional draft.
- Link each label to the specific ADR/policy version used to justify it.
- Strong models may approve routine cases; humans handle uncertainty.
- Support accept, reject, revise and uncertain review outcomes, multiple reviewers and explicit resolution of disagreement.
- Export JSON. Preserve existing 93 train / 15 validation / 3 test assignments; this preserves membership, not a guarantee that all rows will be accepted and exported.
- Support exact regeneration of accepted artifacts and reproducible model-call records. Fresh model calls may produce different outputs; captured results must permit exact replay.
- Changed ADR/policy evidence makes affected approvals stale pending review.
- The user selected model `gpt-6-astra` with `reasoning_effort: "low"` for model reviews, clarifying the earlier shorthand `gpt-astra-low`. Preserve this model and reasoning setting without silent substitution. Provider retention and local retention are unresolved; no external transmission is authorized merely by this draft.
- No approved product facts, campaign rules or desired-style examples are currently available.
- The eight-action taxonomy and separate correctness/factual-support/intent/policy/style assessments below are approved by the user.
- Human review is mandatory for conflicting or missing decision-relevant evidence, reviewer disagreement and unclear applicable policy. Evidence-linked rationale is required; numerical confidence stays unset unless measured.
- The review interface is web-based. A separate holdout is required, but its source has not been supplied. Actual model training is outside version one, interpreting the user's affirmative response to that named exclusion; no broader exclusions or retention settings are inferred.
- Follow-up confirmed: local-only web view without authentication; self-declared reviewer names, not verified identities; humans review all uncertain/disputed cases and randomly audit 10% of routine model approvals; the user is final adjudicator. Support a separate holdout and explicitly report `not supplied` until additional conversations are provided. Do not use holdout content for training, prompt/rule tuning or development examples.

### Repository evidence and compatibility baseline

| Finding | Source |
|---|---|
| One Markdown ADR, identifier ADR-001, status expressed in prose | `ADRs/001-decision-point-curation-and-review.md:1`, `:4` |
| The plain-English companion describes the same decision, not another ADR | `ADRs/001-decision-point-curation-and-review-plain-english.md:8` |
| Decision-point learning and independent context-first review are the intended design | `ADRs/001-decision-point-curation-and-review.md:11`, `:13` |
| JSONL input and readable JSON represent the same 111 unreviewed candidates | `data/README.txt:3`, `:5` |
| Extraction metadata, source checksum, splits and ineligibility | `data/manifest.jsonl:1` |
| Input is extracted/pseudonymized, not an untouched database dump; histories may be incomplete | `data/README.txt:9` |
| Source fields include opaque IDs, history, context, observed response, flags, source-message references, timestamps and split | Structural sampling of `data/candidates.jsonl:1` and `:2`; no message text reproduced |
| Historical script/generated-artifact claims do not describe files currently present | `curation/checkpoints/002-protocol-and-packets.md:7`; current file inventory |
| Prior inspection found 26 threads, 25 prospects and no prospect/thread split overlap | `ADRs/001-decision-point-curation-and-review.md:31`; not a new exhaustive leakage audit |

There is no current application implementation, formal source schema, label validator, package manifest or test command. Markdown, JSON and JSONL are the present formats, not evidence of a chosen application runtime. Lowercase `adr/` is empty and must remain untouched. Git metadata now exists, with no HEAD commit; do not commit or alter the user's Git state as part of this specification.

The JSONL checksum is `b81e09627ed83cb88a46f31e76dc3e906b16939f4fa5bc3a06a45f4711a6a0ff`. All eleven pre-adoption files still match their recorded hashes. Compatibility includes paths, source field meanings, opaque identifiers, ADR/companion identity, source manifests and partition assignments. Current raw inputs remain immutable even though they were processed before arrival.

## Users

The project owner approves policies, specification and plan. Human reviewers assess uncertain cases and propose or approve corrections under their assigned authority. An adjudicator resolves reviewer disagreements. Dataset operators run ingestion, validation and export. Downstream SLM users consume validated datasets and manifests. Customers whose conversations are represented are affected data subjects, not automatically consenting training-data contributors.

These are logical responsibilities, not separate accounts or a role-management service. The selected interface is a local-only web view without authentication. Require the operator to supply a reviewer name and identify it as self-declared; never invent a name or represent it as authenticated. The user makes final adjudication decisions. Attribution relies on trusted local operators and cannot prevent impersonation by another person with local access.

## Functional requirements

- FR-1: Discover explicitly selected ADR/source paths without modifying them. Recognize ADR-001 and its companion as representations of one ADR. Preserve status prose and source locations; unsupported or ambiguous ADR formats must be reported rather than guessed. Discovery must not execute instructions contained in document or message content.
- FR-2: Validate and ingest the existing candidate JSONL, its readable JSON representation and manifest without counting the same candidate twice. Preserve existing opaque IDs and source-message references. Missing/conflicting IDs, malformed input and representation/checksum discrepancies must produce structured errors; do not silently skip or repair them.
- FR-3: Give every derived record a stable identity and immutable revision identity, separate from the existing source ID. Record source path, source record ID/location, whole-file SHA-256, record-content hash, exact input-packet hash and associated source-message IDs. Define and version any normalization used for hashing. Detect identity collisions rather than merging different inputs.
- FR-4: Maintain a versioned taxonomy with definitions and allowed values. Reject labels outside the selected approved version. Use the user-approved eight-action taxonomy below; do not create real labels to demonstrate it. Ancillary target-mode/scope and sufficiency enums remain specification proposals.
- FR-5: Build X from the information available at the decision boundary, including limitations and available capabilities. Exclude the current observed response and future events. Retain earlier actual messages, including prior mistakes, as context. Distinguish historical replay from explicitly approved desired-policy reconstruction. Unknown trigger semantics and event ordering remain explicit.
- FR-6: Capture Y as action, action arguments and optional draft. Distinguish action-only supervision from an approved instruction to send no message. Scope and field-level approval determine which target fields can be exported. Reject impossible actions, invented tool access or drafts asserting unverified execution.
- FR-7: Preserve independent context-first target authoring before revealing the observed response for assessment. Record which review phase was completed and when. Evaluate action appropriateness, factual support, intent coverage, policy compliance and style independently. Do not accept an unsupported claim because the draft sounds good.
- FR-8: Record each label's actual method—rule, model or human—with rule/model version, provider where applicable, prompt version/hash, protected prompt reference, inference settings, captured request/result references, attempt identity and timestamps. Unknown values remain explicitly unknown and may block approval; never fabricate model provenance for historical messages.
- FR-9: Preserve the exact captured inputs/results needed for replay within an approved private retention boundary. Repeating an unchanged local run must reuse valid results unless regeneration is explicitly requested. A fresh external call is a new attempt with its own provenance, not evidence of byte-identical reproducibility. Uncertain external outcomes require reconciliation before retry.
- FR-10: Implement a validated decision lifecycle separating proposals, completed reviews, acceptance, rejection, uncertainty and supersession. Only an authorized approval event may accept an exact revision. Changes to approved input, target or dependencies invalidate current eligibility; never overwrite historical approval events. Proposed transition rules below require specification approval.
- FR-11: Support accept, reject, revise and uncertain review outcomes, independent reviewers, reviewer identity, UTC timestamps and evidence-linked reasons. A revision is a new proposal. Preserve all conflicting reviews and a separate adjudication record naming the actual resolver; do not infer consensus from majority votes or missing responses.
- FR-12: Route documented routine cases to model approval and uncertainty to humans. Preserve model-approved and human-approved tiers. Mandatory human cases are conflicting/missing decision-relevant evidence, reviewer disagreement and unclear applicable policy. Humans randomly audit 10% of routine model approvals; preserve sample membership, selection method/seed and outcomes for reproducibility. Batch definition, rounding and response to audit failures remain proposals under Q2. The user is final adjudicator. An explicit customer request for human help is a target-action question, distinct from which reviewer approves that label.
- FR-13: Store an actionable uncertainty status, missing-evidence list, concise evidence-linked rationale and source citations. Numerical confidence must remain unset unless measured, as confirmed by the user. Record the measurement method/version and supporting evidence for any numerical value; an unsupported self-reported score must never independently authorize acceptance. Hidden chain-of-thought is neither required nor verification evidence.
- FR-14: Attach applicable ADR identity/path/hash and policy, factual-reference, style, taxonomy and schema versions to each decision. Detect changed dependencies and flag affected derived records/approvals as stale. Unaffected records remain traceable. No old approval may authorize a changed target automatically.
- FR-15: Provide explicit, reviewable migrations for derived policies, taxonomies and schemas: preview affected records, create a new version, preserve prior versions, validate and require appropriate re-review. Source migrations remain separately prohibited without explicit authorization. A migration cannot manufacture semantic approval.
- FR-16: Keep raw inputs and derived labels, reviews, attempts and releases in separate logical locations. Derivation must not modify source review-status, eligibility or partition fields. Exact derived paths and storage mechanism are deferred to the approved plan; no directory reorganization is implicit.
- FR-17: Validate derived schemas and cross-record constraints at generation, review transitions and export. Invalid or incomplete records are excluded from accepted releases and reported using safe IDs and reason codes. Material input integrity failures block the run; permitted partial processing, if any, must be explicit and visible in the release manifest.
- FR-18: Preserve authoritative partition membership for each source candidate. Keep each prospect's related threads, prefixes, rewrites and variants within one partition. Check source-record IDs, message IDs and duplicate content across train, validation, test and any configured holdout. Report conflicts and block affected releases rather than silently reassigning examples.
- FR-19: Audit repeated templates and near-duplicate content with an explicit method and policy. Whole-file representation duplicates are not new examples. Model-only labels must be distinguishable from independently human-reviewed evaluation references. No human-gold quality claim is permitted for model-only labels. Support a separate holdout, currently `not supplied`, from additional conversations, ideally different prospects. Preserve current splits; do not carve a holdout from them. Exclude future holdout content from training, prompt/policy tuning and development examples; evaluate only after the model and labeling policy are fixed. Do not claim holdout evaluation passed while it is absent. Similarity thresholds and evaluation-reference requirements remain Q4.
- FR-20: Export JSON containing only eligible, accepted, current revisions whose required checks pass. Preserve X/Y and provenance linkage while preventing observed-response judgments or future-outcome metadata from leaking into model inputs. Generate a manifest listing exact revision IDs, file hashes, policy/taxonomy/schema versions, partitions and exclusions. The proposed JSON shape below is subject to Q3.
- FR-21: Make local reruns idempotent: unchanged inputs, captured model results, review events, configuration and exporter version reproduce byte-identical release files under a documented canonical serialization. Volatile execution metadata belongs outside deterministic release payloads. Do not claim equality for newly sampled model responses.
- FR-22: Maintain an append-only logical audit history of derivation, review, revision, acceptance, rejection, staleness, migration and release events. Bind events to actor, time, before/after revision and evidence. Detect broken references or tampering before release. Cryptographic signatures and malicious-administrator resistance are not implied by hashes alone.
- FR-23: Resume interrupted local runs from recorded attempts without duplicating accepted decisions or approval events. Record uncertain side effects, reconcile them and only retry safe or explicitly authorized actions. Publish releases atomically so consumers cannot observe a half-written valid release. Roll back a release pointer without erasing source or audit history.
- FR-24: Report counts by state, approval tier, uncertainty reason, action and partition, plus schema failures, stale evidence, duplicate conflicts and excluded records. Reports and ordinary logs must not expose source text, prompts, credentials or private drafts. Distinguish unrun checks, failures and passed checks; never report absent tests as passing.
- FR-25: Enforce provider and retention boundaries before any external call. The selected review configuration is model `gpt-6-astra` with `reasoning_effort: "low"`. Provider storage controls, local sensitive-artifact retention and data-use authority must also be resolved before real data is sent. Keep secrets outside artifacts and redact logs. Retention expiry must invalidate replay/export claims if necessary evidence can no longer be accessed.
- FR-26: Provide a local-only web interface without authentication for context-first review and adjudication. Bind it to loopback, not a public/network interface. Record explicitly supplied reviewer names as unverified self-declarations; require an explicit recorded user adjudication event for disputed cases, without claiming authenticated authority. Make ingestion, proposing labels, validation, export, resume and rollback operable through documented mechanisms; the precise web/CLI division for operator functions remains a planning choice subject to review. Product review approval is distinct from Genesis specification/plan approval; none substitutes for another.

### User-approved action taxonomy and proposed target contract

| Action | Definition | Draft behavior |
|---|---|---|
| answer | Resolve a question using available approved evidence | Required |
| clarify | Ask for information necessary to decide or answer | Required |
| qualify | Ask a relevant sales question permitted at this stage | Required |
| invite_next_step | Offer an appropriate authorized meeting or other next step | Required; approved destination in arguments |
| handoff_human | Request available human assistance | Optional acknowledgment; no claim of successful handoff without evidence |
| lookup | Request available evidence retrieval | No customer draft for the retrieval action itself |
| wait | Await a specified event or permitted time | No draft |
| stop | End contact or honor an opt-out under applicable rules | Only an acknowledgment permitted by the applicable policy |

The user approved the action taxonomy and separate assessment dimensions. Proposed assessment values: `pass`, `fail`, `uncertain`, `not_applicable`. Proposed context sufficiency: `sufficient`, `recoverable`, `insufficient`. Proposed target modes: `historical_replay`, `desired_policy_reconstruction`; target scopes: `action_only`, `full`. These detailed enums are submitted for specification review. Missing/unapproved draft is not equivalent to an approved null draft.

Proposal for Q3: one JSON object per release containing a schema version, manifest and partition arrays; each example has stable source/revision references, X, Y, supervision scope and an audit reference. Sensitive audit content remains separately protected. Final consumer-specific field names and token/chat serialization are not selected yet. Export is not a fine-tuning job.

### Proposed lifecycle — FR-10 and FR-11

| Current condition | Event | Result |
|---|---|---|
| No proposal | Valid proposal created | proposed |
| proposed / needs-review | A completed review is recorded | reviewed; the review outcome remains explicit |
| reviewed | Authorized acceptance; all evidence and checks current; disagreements resolved | accepted, with approval tier |
| reviewed | Authorized rejection with reason | rejected |
| proposed / reviewed | Uncertainty or unresolved disagreement | needs-review |
| Any existing revision | Revision requested | New proposed revision; original history preserved |
| Existing revision | Valid replacement takes effect through a recorded event | superseded, linked to replacement |
| Previously accepted | Source, target, ADR or policy evidence changes | Original acceptance preserved historically; effective eligibility becomes stale and needs review |

Staleness is a validity condition as well as a review-routing reason. Accepted historical state alone never makes a record exportable. Invalid transition attempts produce errors and no partial state change. A model-authored proposal is not automatically a model approval; the distinct review event must satisfy the approved routine criteria. Final adjudication belongs to the user. Without authentication, the tool records a declared actor and explicit action but does not verify the person's identity.

## Non-functional requirements

- NFR-1: Every operation must preserve the path set and bytes of existing ADRs and source data, verified against an immutable baseline manifest. No operation may silently rewrite raw inputs or existing checkpoints.
- NFR-2: The provenance chain from each accepted output back to source bytes, exact input, policy and actual review must be complete and verifiable without trusting a model explanation. Missing, stale, failed, skipped or tampered mandatory evidence blocks eligibility.
- NFR-3: Deterministic replay and artifact reproduction must be distinguishable from new stochastic inference. Canonical serialization, hash algorithms and normalizations must be versioned and documented; equivalent reruns must not create new logical decisions.
- NFR-4: Default reports must contain only safe operational metadata. Private text/prompts require controlled local access and an explicit transmission/retention policy. Tests must use invented fixtures rather than publishing real examples. No credentials belong in prompts, outputs, Genesis records or version control.
- NFR-5: Failures must leave recoverable, inspectable state. Concurrent or repeated review operations must not accept conflicting revisions silently; integrity checks and atomic publication must protect accepted history and releases.
- NFR-6: Preserve compatibility with existing source IDs, field meanings, ADR companions and partition assignments. No runtime, database, framework or dependency is selected merely because Genesis uses Node.js. Choose minimal tooling only in the approved plan.
- NFR-7: Maintain stable requirement identifiers and trace every later task and executable gate to them. Keep public/safe evidence distinct from protected source material; record only actual approval and actual verification results.
- NFR-8: Report dataset and evaluation limitations: 111 candidate decisions are not 111 independent prospects, three test decisions do not establish broad quality, and an audit cannot certify universal absence of bias. Performance targets and group-specific fairness criteria must be approved before they are claimed achieved.

## Constraints

### Proposed release boundary for specification approval

The first implementation supports local ingestion, review, adjudication, audit, validation, deterministic JSON export and recovery. Live GPT calls remain disabled until a separately recorded provider policy records the selected model `gpt-6-astra` with `reasoning_effort: "low"` and identifies data-use authority and retention conditions. Support for recording/replaying genuine captured model results remains in scope; tests use invented fixtures, and a fixture response never becomes evidence that a real model review occurred.

Proposed local retention: preserve local review/audit artifacts until the owner explicitly requests a reviewed purge; do not introduce automatic expiration or deletion. Store private content locally, outside ordinary logs and version-control staging. Reference immutable source files rather than multiplying copies where possible. A later purge must describe consequences for replay, invalidate missing-evidence claims and never silently delete raw source files. This retention rule becomes effective only if the user approves this specification.

Implement the export mechanism and validate it using invented fixtures. Real-data training/evaluation releases additionally require a recorded owner declaration of permitted data use; absent that declaration, allow local review/inspection but block a training/evaluation release. A schema-valid artifact does not itself establish permission to train on it. Source-data rights are not inferred from repository access or specification approval.

Holdout absence does not block local curation or an otherwise eligible training/validation/test release, but the manifest must report `holdout_status: not_supplied`; no holdout score or validation-pass claim is allowed. Additional holdout data must pass prospect/source/content isolation checks before use.

The runtime and concrete file layout will be proposed in the implementation plan, which requires separate approval. This specification does not grant permission to install application dependencies, run external inference or implement product code.

### Proposed audit and duplicate-review mechanics

For each frozen release candidate, take a uniform random sample of 10% of its routine model-approved revisions, rounding up to a whole record (zero if the population is empty). Persist the population, seed, algorithm version and selected revision IDs. Audit each selected exact revision; reuse a prior human audit only if its input, target and policy evidence remain current. A changed release population creates a new documented sampling event, not a reroll to discard inconvenient failures.

A material audit error is an unsupported factual claim, wrong action, applicable-policy violation, missing required evidence or invalid approval provenance. Any such failure blocks the candidate release while the user adjudicates and identifies affected cases for re-review. Preserve the failed audit, corrections and new release revision. Cosmetic changes still create a revised target needing approval. The 10% audit is not a statistical correctness guarantee or a replacement for reviewing every uncertain case.

For the initial bounded dataset, automatically reject cross-partition source-ID, message-ID, prospect-group and exact-content conflicts. Additionally compare full X/Y conversation content after a versioned normalization of Unicode, case and whitespace; keep original bytes and hashes. Normalized matches are potential duplicates requiring an explicit owner resolution, not permission to merge or move records. Require a recorded human near-duplicate review of the release's cross-partition content before release; the first version makes no claim of automatic semantic-duplicate detection. Shared generic greetings alone need not disqualify independent cases, but any exception requires evidence and rationale. Holdout review must not feed its content into development or policy tuning; a discovered conflict blocks release rather than silently modifying the development set.

Evaluation references labeled `human_gold` require human approval of each exact target revision. Model-only references may be retained with their distinct quality tier but cannot receive that designation.

Raw source data, existing ADRs and directory structure are immutable within this scope. Existing data is private/potentially identifying despite pseudonyms, and no training license or consent evidence has been established. The system must not infer that the data is suitable for training merely because it exists locally.

No product facts, style or campaign-policy authority can be created from repeated historical AI claims. Humans must resolve relevant uncertainty; a model explanation is not independent evidence. Do not infer actual authorship from `system` or `company` fields.

Specification and plan approvals are separate and must be recorded only after actual user approval. No implementation tasks, code, real label generation, source migration or external calls are authorized by this draft. Requirements below describe future behavior, not completed work.

## Non-goals

Confirmed exclusions: labeling ADR documents as training subjects; reorganizing or rewriting raw inputs; retroactively fabricating approvals or authorship; executing sales actions against customers; claiming the dataset is bias-free; treating this specification as authorization to train or deploy a model.

Actual SLM training is outside version one. Web review is in scope. Proposed additional exclusions pending Q3: deployment of the SLM, multiple external providers and autonomous promotion of policies. Source-data migration is separately forbidden without authorization. Support for additional ADR formats or arbitrary future datasets is not presumed.

## Acceptance criteria

These are executable test contracts for the later implementation plan, **not tests implemented or run now**. Each describes a controlled input, operation and binary assertion. The approved plan must bind each applicable criterion to an actual command and current-source evidence. Use invented fixtures and temporary copies for corruption/change tests; never mutate the real source files to test immutability.

- AC-1: Integrity baseline (FR-1, FR-16, NFR-1). Hash and enumerate every existing ADR/data file before and after ingest, label, review, export, failure and recovery scenarios. Assert identical paths and SHA-256 values; attempted source writes are rejected.
- AC-2: Ingestion compatibility (FR-1–FR-3). Ingest equivalent JSONL/readable-JSON fixtures and an ADR with a companion. Assert one record per source ID and one ADR identity. Conflicting representations, duplicate conflicting IDs, malformed JSON, missing required fields and checksum mismatches produce explicit errors with no accepted artifacts.
- AC-3: Derived-schema validation (FR-4, FR-6, FR-17). Validate every generated fixture record against its pinned schema/taxonomy. Assert zero invalid accepted records. Unknown action values, missing arguments, ambiguous draft scope and wrong field types fail validation.
- AC-4: Complete provenance (FR-3, FR-8, FR-14, NFR-2). Traverse every accepted fixture's source record/file, input hash, ADR/policy, schema/taxonomy, labeling attempt and review references. Recompute hashes. Remove or alter one mandatory reference at a time and assert release rejection.
- AC-5: Legal lifecycle only (FR-10, FR-11). Exercise every approved transition and reject all unlisted transitions. Assert no direct unreviewed-to-accepted promotion, no approval inferred from silence, and no acceptance with unresolved disagreement. Each rejection leaves prior state intact.
- AC-6: Review attribution and uncertainty (FR-11–FR-13). Record disagreeing reviewers, a revision and an uncertain outcome. Assert all originals remain accessible, uncertainty blocks export, and disagreement requires an explicit user-adjudication record. Missing reviewer names, missing adjudication records and unsupported confidence cannot authorize acceptance. Assert attribution is marked self-declared/unverified; do not claim this test detects impersonation without authentication.
- AC-7: Historical separation (FR-5, FR-7). Place distinguishable sentinels in the current observed response and future events of a fixture. Assert phase-A X excludes them and phase B reveals only the permitted observation after phase A is saved. Earlier actual bad messages remain context. A reconstructed example is explicitly versioned and not labeled historical replay.
- AC-8: Exact replay (FR-9, FR-21). Run the same captured inputs, responses, reviews and pinned configuration twice. Assert byte-identical deterministic exports, unchanged accepted decision counts and zero extra external requests. Explicit regeneration produces a separate attempt, never silently replaces the captured result.
- AC-9: Stale dependencies (FR-14). Change source bytes or an applicable ADR/policy version in a fixture. Assert affected prior approvals become ineligible and exports fail until re-reviewed; original approval records remain unchanged. Unaffected records retain their evidence linkage.
- AC-10: Partition isolation (FR-18, FR-19). Assert pairwise disjoint source-record IDs, source-message identities and prospect groups across train, validation, test and configured holdout. Deliberately introduce an overlapping prefix or variant and assert release failure without automatic reassignment. Verify existing partition membership is preserved, while excluded records reduce export counts visibly.
- AC-11: Duplicate isolation (FR-2, FR-19). Feed duplicate file representations and repeated/near-duplicate fixtures under the approved similarity policy. Assert no duplicate ingestion and cross-partition conflicts are reported or rejected as that policy requires. Explicitly distinguish absent holdout from successfully validated holdout.
- AC-12: JSON release validation (FR-20). Parse each exported JSON file and validate its schema, eligibility, references, partition membership and manifest hashes. Assert stale, rejected, uncertain, incomplete or superseded revisions are excluded; action-only records have correct supervision scope. Assert no private review rationale or observed-response field leaks into training X/Y.
- AC-13: Interrupted local run (FR-23, NFR-5). Stop a fixture run between generation, review persistence and publication. Resume and assert no duplicated accepted decisions or events, no partial visible release and the same final valid artifact as uninterrupted replay.
- AC-14: Uncertain external attempt (FR-9, FR-23). Simulate a timeout after a provider may have processed a request. Assert the attempt is recorded as uncertain and no automatic second external request occurs until reconciliation or explicit retry authorization.
- AC-15: Version migration and rollback (FR-15, FR-22, FR-23). Preview and apply an authorized derived-taxonomy change to fixtures. Assert affected records are identified, prior versions preserved and semantic approvals not carried forward silently. Roll back the active release and verify old hashes and audit history remain available.
- AC-16: Evidence tampering (FR-17, FR-22, NFR-2). Alter a captured result, review reference or manifest in a fixture; delete or mark a mandatory check skipped. Assert export fails with a reason identifying the failed evidence class and does not treat a model explanation as a replacement check.
- AC-17: Privacy boundary (FR-24, FR-25, NFR-4). Insert fake secrets and distinctive private-text sentinels into fixtures. Assert ordinary logs, summary reports and Genesis records omit them. With retention/sharing policy unset or incompatible, assert external transmission is blocked. Check controlled expiry produces the documented loss of replay eligibility rather than a false reproducibility claim.
- AC-18: Summary accuracy (FR-24). Compare report counts against known fixture states, tiers, partitions and failure reasons. Assert totals reconcile, uncertainty and exclusions are visible, and pending/unrun/failed checks are never counted as passing.
- AC-19: Regression preservation (NFR-6, NFR-7). At implementation planning, inventory then-current project tests and bind each to mandatory gates. Run them on current source and require pass. Today's inventory contains no existing test commands; report that explicitly rather than recording a vacuous pass. New checks must cover the active task's applicable ACs.
- AC-20: Capability and drafting constraints (FR-6). For a fixture with no calendar/lookup/handoff capability, reject targets claiming those actions were performed. Distinguish a proposed invitation from a booking and an absent draft label from an approved wait action.
- AC-21: Review concurrency (FR-10, FR-11, NFR-5). Submit conflicting approvals/revisions against the same prior revision. Assert at most one current accepted revision, no lost review events, and an explicit conflict for the stale operation.
- AC-22: Web review (FR-7, FR-11, FR-26). Using invented fixtures and explicitly entered test-reviewer names, exercise accept, reject, revise, uncertain and adjudication in the browser. Assert the view binds only to loopback, has no authentication requirement, records supplied names as unverified, and never invents approval events. Conflicts remain visible until explicit user adjudication. The current observed response must not reach the browser until phase A is saved and reveal is allowed.
- AC-23: Routine-approval audit (FR-12). For a known fixture population of routine model approvals, apply the approved 10% sampling rule. Assert the selected count matches the approved rounding/batch rule, saved selection provenance reproduces the sample, and human audit results link to the sampled revisions. Include a fixture with a failed audit and assert the approved failure-handling rule is applied. These detailed rules must be resolved before implementing the gate.

## Risks

The source carries incomplete-history and nonhistorical-context warnings throughout. Missing facts can change the right action; formatting/schema checks cannot settle correctness. Current-policy reconstruction requires approved context and must not masquerade as historical truth.

The user-selected no-authentication local view provides declared attribution, not verified reviewer identity or protection from a malicious local operator. Do not expose it on a network or claim stronger identity guarantees. A separate holdout is not yet supplied; report that limitation rather than delaying all local curation or inventing held-out evidence.

Duplicate file representations, repeated templates and shared conversation prefixes can inflate apparent data size or contaminate evaluation. Authoritative source split assignments may conflict with a new leakage finding: block the release and request a versioned partition decision, rather than silently changing assignments.

Model judges can share a generator's errors; human reviewers can also be biased. Separate evidence from explanation, preserve disagreement, and measure routine-approval errors before claiming a numerical confidence guarantee. Relevant fairness groups and tolerances are not yet selected.

Exact artifact replay requires retained captured evidence; privacy retention may limit how long that evidence can remain available. Resolve this tradeoff explicitly. Hashes support integrity checks but alone do not prevent a privileged actor rewriting all records.

Unapproved product facts and voice references limit which full targets can be accepted. An action-only target is useful only when the action itself is supported. Historical source labels and legacy checkpoints cannot establish real human approval or present code existence.

The installed Genesis checker checks sections, requirement IDs and template placeholders; it does not reject every substantive open question. A structural pass must not be represented as an implementation-ready specification. Its later plan checker currently expects coverage of all requirement IDs: reconciling that with the user's one-initial-task rule is a planning-stage question, not permission to create an oversized first task or bypass gates.

## Open questions

The user answered the latest clarification questions on 2026-09-25. Confirmed choices are recorded above; the remaining items below are not silently selected defaults.

- Q1 — Resolved for the eight actions and separate assessment dimensions. Detailed assessment/sufficiency/mode/scope enum values remain explicit proposals for specification approval, not additional already-approved facts.
- Q2 — Mandatory-human categories, evidence/confidence rule, random 10% human audit and the user as final adjudicator are confirmed. Concrete batch, rounding, sampling and failure-handling rules are now proposed in Constraints for approval with this specification. No calibrated numerical-confidence guarantee is established by a 10% audit.
- Q3 — Local-only web review without authentication is confirmed; reviewer names are self-declared, and actual training is excluded. Still proposed for approval: final JSON consumer shape and additional exclusions. Runtime can be proposed in the implementation plan; no existing application language dictates the choice.
- Q4 — Support a separate holdout and mark it `not supplied` until additional conversations arrive. The user agreed to keep it out of development/training/prompt-policy tuning and preserve existing splits. Acquisition remains future work, not permission to invent or reassign records. The initial duplicate-review and human-gold requirements are now proposed in Constraints for specification approval.
- Q5 — Review-model choice and reasoning setting resolved: model `gpt-6-astra` with `reasoning_effort: "low"`. Provider retention and data-use authority remain unresolved. The proposed release boundary blocks live GPT calls and real-data training/evaluation release until the applicable permissions are recorded. A concrete local retention proposal is provided above for specification approval; approving it does not authorize provider retention or transmission.

The user may approve this specification with its explicitly proposed local release boundary and mechanics, or request changes. Deferred provider permissions and real-data release authority remain operational blockers even after specification approval. Runtime is a separately reviewed planning choice. Approval must reference this exact specification version; later substantive changes require renewed review.
