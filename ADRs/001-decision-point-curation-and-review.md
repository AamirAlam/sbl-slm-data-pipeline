# ADR-001: Decision-point data curation and review

Date: 2026-09-23  
Status: Architecture accepted as an initial scope; assumptions, objectives and research design remain provisional.  
Scope: Design and research formulation only. No implementation, training or mathematical solution is authorized by this ADR.

Full [plain-English version](001-decision-point-curation-and-review-plain-english.md), including explanations of every mathematical objective.

## 1. Decision and rationale

Use a decision point within a conversation as the unit of learning. The input **X** is the information available at that point. The target **Y** is a reviewed next action, its arguments and an optional draft. A conversation may supply several distinct examples.

The historical observed response is evidence of what happened, not evidence that the behavior was correct. Reviewers first judge the context independently, then inspect the observed response. Strong models may approve routine, sufficiently supported cases; humans resolve uncertainty. Preserve the distinction between model-approved and human-approved targets.

This addresses two different questions:

1. Was the old response justified by the evidence and policy available then?
2. What should the new model do under the policy we want it to follow?

These questions can have different answers. An old response can be unassessable while a new target is authorable under explicitly reconstructed, approved context. A historically poor action can yield a valuable corrected example.

### User decisions that constrain this ADR

- Remain at the architecture/research stage; write no code.
- Permit model approval for routine cases; humans handle uncertainty.
- No approved SBL product facts, campaign rules or desired-style examples are available.
- Preserve assumptions, reasons and potential failures for subsequent agents.

### Known source facts

The recorded source inspection found 111 decision candidates across 26 threads, 25 prospects and three campaigns. They are not 111 independent full conversations. All candidates carry incomplete-history and nonhistorical-context warnings. Twenty have empty histories. Product knowledge and sender-style fields are null throughout. Sender labels are `system` or `company`; verified generator identity and human approval are not established. Existing splits are 93/15/3 with no prospect/thread overlap found in that inspection.

These are structural observations from [checkpoint 001](../curation/checkpoints/001-inspection.md), not semantic approval of the data. The approval policy was subsequently clarified in [checkpoint 003](../curation/checkpoints/003-review-authorization.md). Earlier checkpoints describe work at their dates; they do not authorize continuing implementation or guarantee that earlier artifacts still exist.

## 2. X and Y: definitions and boundaries

For conversation \(c\), at decision time \(t\), define:

$$
X_{c,t} = (C_{c,t}, F_{c,t}, K_{c,t}, S_{c,t}, H_{c,<t}, E_{c,t}, O_{c,t}, M_{c,t}).
$$

| Symbol | Meaning | Important limitation |
|---|---|---|
| \(C\) | Campaign objective and context | Must identify version and applicability |
| \(F\) | Applicable flow and behavioral policy | Exported instructions are not automatically approved |
| \(K\) | Approved factual evidence available to the model | Unknown facts remain unknown |
| \(S\) | Approved style specification | Does not exist yet; legacy replies are only candidate examples |
| \(H_{<t}\) | Conversation prefix available before the decision, including the triggering inbound message when applicable | No future messages or current response |
| \(E\) | Triggering event, channel and time | Numeric codes need verified meanings |
| \(O\) | Operational state and available capabilities | Do not invent access to calendars, tools or handoff queues |
| \(M\) | Missingness, provenance and contextual limitations | Useful uncertainty information, not factual authority |

The prefix includes earlier observed company/AI messages if the customer saw them, even if those messages were wrong. It does not substitute corrected targets into the historical conversation without explicitly creating a synthetic/reconstructed example.

Define the desired target:

$$
Y^*_{c,t} = (A^*_{c,t}, U^*_{c,t}, D^*_{c,t}),
\qquad D^*_{c,t}\in\mathcal{T}\cup\{\varnothing\}.
$$

Here \(A\) is the next action, \(U\) its arguments, \(D\) the draft, and \(\mathcal{T}\) the set of text drafts. Proposed actions include answer, clarify, qualify, invite a next step, hand off, look up, wait and stop. The action set must be reconciled with real product capabilities before approval.

The star denotes a desired target, not an already known ground truth. The actual reviewer-produced estimate is \(\widehat Y\). There may be a set \(\mathcal{Y}_{\mathrm{ok}}(X;\Pi)\) of acceptable targets under policy \(\Pi\), rather than one uniquely correct sentence.

Let \(R^{\mathrm{obs}}_{c,t}\) be the historical response. It is revealed during response assessment, but is not the current target by default:

$$
\widehat Y = g(X;\Pi),
\qquad
J^{\mathrm{obs}} = j(X,R^{\mathrm{obs}};\Pi),
\qquad
R^{\mathrm{obs}}\not\equiv Y^*.
$$

\(J^{\mathrm{obs}}\) is a vector of judgments: action appropriateness, factual support, intent coverage, policy compliance and style fit. Each may be pass, fail, uncertain or not applicable. Do not collapse an unsupported claim into a passing judgment because the response sounds good.

Reviewer identity, rationale, evidence citations, approval tier and hashes are audit metadata. They are not automatically model outputs or training features.

## 3. Assumptions — explicit and testable

| ID | Assumption | Mathematical formulation or operational meaning | What would invalidate it? |
|---|---|---|---|
| A1 | Each boundary captures a real decision opportunity | \(b_{c,t}\in\mathcal{B}_{\mathrm{valid}}\), where validity depends on verified event order | A future message, wrong trigger, or duplicate boundary |
| A2 | Some available prefixes are sufficient despite truncation | Let \(Z\) be missing decision-relevant state; for an accepted case, missing plausible \(Z\) should not change the admissible target materially | Recovered history changes the correct action |
| A3 | Policy and evidence can support a target | \(\mathcal{Y}_{\mathrm{ok}}(X;\Pi)\neq\varnothing\) for accepted examples | Conflicting rules, unsupported facts, or impossible actions |
| A4 | Reviewer decisions are informative but fallible | \(\Pr(\widehat Y\notin\mathcal{Y}_{\mathrm{ok}}\mid X,\text{reviewer})\) is generally nonzero and unknown | Review agreement is mistaken for truth |
| A5 | Routine cases can be routed reliably | Conditional model-approval error can be estimated on audited cases, within uncertainty bounds | Errors concentrate in cases the router calls routine |
| A6 | Decision examples within a conversation are dependent | In general \(P(Y_t,Y_s\mid c)\neq P(Y_t\mid c)P(Y_s\mid c)\) | Treating 111 examples as 111 independent prospects |
| A7 | Approved style can be specified without endorsing bad behavior | Style optimization is conditional on factual/action admissibility | Brand voice rewards pressure, false identity or unsupported promises |
| A8 | Deployment coverage must be investigated, not presumed | \(P_{\mathrm{source}}(X,Y)\neq P_{\mathrm{deploy}}(X,Y)\) is possible | Sample selection excludes important situations |
| A9 | Action-only supervision may be useful | If only \(A\) is supported, supervise \(A\); do not treat unknown \(D\) as a desired null response | Missing draft is mistaken for a wait/no-message label |
| A10 | Historical and desired-policy examples can be distinguished | Every example has target mode and versioned input policy | Today's facts are silently used to grade yesterday's response |

For A2, one possible conservative criterion for accepting a proposed target \(y\) is:

$$
\sup_{z\in\mathcal{Z}_{\mathrm{plausible}}(X)}
\ell_{\mathrm{decision}}(y;X,z,\Pi)\leq\epsilon.
$$

Neither the plausible-state set nor \(\epsilon\) is known yet. This formulation expresses the question: **could a plausible missing fact change what we should do?** It is not a claim that robustness has been measured. Missingness may be selective rather than random.

## 4. Mathematical objectives — formulations only

No coefficients, thresholds or solutions are selected here. These objectives state what a later research/implementation phase would need to define and measure.

### 4.1 Choose useful, supportable training data

Let \(q_i\in\{0,1\}\) indicate selection of candidate \(i\), \(e_i\) denote satisfaction of evidence/approval gates, \(c_i\) its review cost, and \(w_i>0\) a proposed utility weight. Let \(\mathrm{Cov}_k(q)\) measure coverage of situation \(k\) and \(\mathrm{Red}(q)\) penalize redundancy.

$$
\max_q\quad
\sum_i q_iw_i
+\lambda_{\mathrm{cov}}\sum_k\mathrm{Cov}_k(q)
-\lambda_{\mathrm{red}}\mathrm{Red}(q)
$$

$$
\text{subject to}\quad
q_i\leq e_i,\qquad
\sum_i q_ic_i\leq B.
$$

This separates useful coverage from mere dataset size. The formulation cannot generate situations missing from the source; acquisition or explicitly synthetic data is a separate decision. Utility is a hypothesis to validate, not a model's confidence score renamed as quality.

### 4.2 Learn action selection and conditional drafting

A possible factorization is:

$$
p_\theta(Y\mid X)
=p_\theta(A\mid X)
\,p_\theta(U\mid X,A)
\,p_\theta(D\mid X,A,U).
$$

This is a behavioral decomposition, not a decision to build three separate models. An illustrative supervised objective is:

$$
\mathcal{L}_{\mathrm{SFT}}(\theta)
=\frac{1}{\sum_i q_iw_i}
\sum_i q_iw_i
\left[
\lambda_A\ell_A(\theta;X_i,\widehat A_i)
+m_i^U\lambda_U\ell_U(\theta;X_i,\widehat A_i,\widehat U_i)
+m_i^D\lambda_D\ell_D(\theta;X_i,\widehat A_i,\widehat U_i,\widehat D_i)
\right].
$$

The supervision masks \(m_i^U,m_i^D\) indicate which fields are actually approved. An action-only example has no draft loss; an explicitly approved no-draft action can supervise the null draft. These are different conditions. Text loss applies to approved output tokens, not earlier unapproved replies in X. A nonempty accepted set is required for the normalization.

For evaluation, exact text match is insufficient. One conceptual loss is:

$$
\ell_{\mathrm{acceptable}}(\widehat y,X)
=\min_{y\in\mathcal{Y}_{\mathrm{ok}}(X;\Pi)} d(\widehat y,y),
$$

where \(d\) must capture action, meaning and constraints rather than spelling alone. Defining this distance is a research question.

### 4.3 Optimize useful behavior subject to constraints

$$
\min_\theta\quad
\mathbb{E}_{P_{\mathrm{deploy}}}
\left[
\lambda_a\ell_{\mathrm{action}}
+\lambda_i\ell_{\mathrm{intent}}
+\lambda_s\ell_{\mathrm{style}}
\right]
$$

$$
\text{subject to}\quad
\Pr(\text{unsupported factual claim})\leq\delta_f,
\quad
\Pr(\text{critical policy failure})\leq\delta_p.
$$

Evidence and critical-policy failures should not be traded away simply for fluent style. The thresholds and the definition of a critical failure require owner decisions. Observed conversion is a secondary outcome: this observational export does not identify the causal effect of a reply on a sale.

### 4.4 Route model approval versus human uncertainty review

Let \(r(X)\in\{\mathrm{model},\mathrm{human},\mathrm{hold}\}\). Let \(\widehat p_{\mathrm{err}}(X)\) be an empirically calibrated error estimate, not verbal confidence. A conceptual routine route is:

$$
r(X)=\mathrm{model}
\quad\text{only if}\quad
e(X)=1,\quad u(X)=0,\quad
\widehat p_{\mathrm{err}}(X)\leq\tau,
$$

where \(e\) covers applicable evidence gates and \(u\) flags unresolved uncertainty. Threshold \(\tau\) is not set. Without calibration, the numeric condition is not established and must not be asserted as achieved.

The operating tradeoff can be expressed as:

$$
\min_r\quad
\mathbb{E}[c_{r(X)}]
\quad\text{subject to}\quad
\Pr(\widehat Y\notin\mathcal{Y}_{\mathrm{ok}}\mid r(X)=\mathrm{model})\leq\alpha.
$$

To prevent a trivial “hold everything” solution, include a nonzero resolved-coverage requirement where evidence permits:

$$
\Pr(r(X)\neq\mathrm{hold})\geq\kappa,\qquad \kappa>0.
$$

Feasibility depends on available evidence; coverage must never override approval gates. The conditional model-risk constraint applies only when model approval has positive probability. Choosing no model-approved cases is a possible conservative outcome until routing is calibrated, not proof of a useful automated reviewer.

Human review has cost and error too; it is not an oracle. Audit routine approvals as well as escalations, or routing errors will be invisible. No audit fraction or error guarantee is ratified by this formulation.

### 4.5 Measure bias without promising “bias-free” data

Define a deployment-relevant slice \(G\), such as language, campaign stage, company type or communication style, where collection and use are appropriate. For loss \(\ell\):

$$
R_g=\mathbb{E}[\ell(\widehat Y,Y^*)\mid G=g],
\qquad
\Delta_R=\max_{g,h}|R_g-R_h|.
$$

A candidate objective is to reduce worst-slice risk \(\max_g R_g\), alongside overall risk, with counts and uncertainty reported. Since \(Y^*\) is not directly observed, practical estimates use adjudicated references and must account for their limitations. Different slices can require legitimately different actions; identical reply rates or identical outputs are not automatically fairness. Review routing, approval and rejection rates should also be compared conditional on relevant case difficulty and evidence availability.

Selection indicators matter:

$$
S_i=1\;\text{if a situation enters the export},
\qquad
Q_i=1\;\text{if it is accepted},
$$

$$
P(X,Y\mid S=1,Q=1)
\not\equiv P_{\mathrm{deploy}}(X,Y).
$$

Sampling or importance weights require an estimable target distribution and adequate support. They cannot recover an entirely absent situation type. No finite audit can establish universal absence of bias.

## 5. Knowns and unknowns

X/Y describes the learning problem. Known/unknown describes our knowledge about that problem. They are different axes; **X is not synonymous with known, and Y is not synonymous with unknown**. Parts of X are missing, and parts of a proposed Y may be supported while others remain unknown.

| Knowledge category | In X | In Y or its assessment | Response |
|---|---|---|---|
| Known knowns | Export structure, source IDs, recorded prefix, explicit warnings | Target shape and authorized routine-model/human-uncertainty routing | Preserve and version; do not overinterpret |
| Known unknowns | Missing history, historical policy, product truth, desired voice, trigger semantics | Correct action for ambiguous cases, trustworthy factual draft, reviewer accuracy | List blockers; investigate or hold affected scope |
| Unknown knowns | Facts an employee or operational log may contain but reviewers cannot access yet | Tacit sales judgment, undocumented exceptions, customer-specific commitments | Interview owners, inspect authorized records, document exceptions |
| Unknown unknowns | Unanticipated deployment situations or hidden extraction defects | Failure patterns not yet in the rubric; shared model/human blind spots | Open-ended error discovery, diverse review, incident feedback and periodic re-audits |

“Unknown unknowns” are not a list we can complete. Examples here are discovery prompts, not claims of exhaustive coverage. Newly discovered risks move into known unknowns and receive explicit investigation questions.

## 6. Failure modes and considerations

| Failure mode | Why it matters | Detection or question | Design consideration |
|---|---|---|---|
| Reviewer anchors on observed reply | Copies a fluent but wrong answer into Y | Compare independent context-only judgments with response-first judgments | Save phase A before revealing the response |
| Current facts judge historical behavior | False historical verdicts | Can the cited evidence be dated to the decision? | Separate replay and desired-policy reconstruction |
| Truncation hides commitments or opt-outs | Wrong action despite plausible local wording | Would recovered history change the label? | Assess sufficiency per target; hold unresolved cases |
| Outbound-only extraction omits silence | Model learns to always reply | Which inbound/event boundaries have no outbound record? | Acquire no-response opportunities; do not infer them blindly |
| Incorrect event ordering | Future information leaks into X | Verify delivery/event order rather than creation time alone | Keep order uncertainty explicit |
| Repeated prefixes inflate sample size | Overstates diversity and test reliability | Count independent prospects, source events and templates | Group splits; account for clustered dependence |
| Legacy AI claims become “facts” | Repeated hallucinations gain authority | Is evidence independent of generated replies? | A source claim register is unverified until adjudicated |
| Shared judge/generator bias | Model agreement appears reliable while both are wrong | Human audits and disagreement/error taxonomy | Retain provenance; audit routine approvals |
| Human sales preference becomes truth | Aggressive persuasion or familiar dialect is rewarded | Compare reviewers and reason codes across slices | Explicit rubric and adjudication; humans can also err |
| Unclear reference authority | Any convenient source clears a gate | Who approved the fact, scope and date? | Record authority, applicability and version |
| Style conflicts with correctness | Brand imitation reproduces false identity or pressure | Can style preference change an otherwise invalid label? | Validate behavior/facts before voice |
| Action-only null is misread | Model learns silence instead of an unprovided draft | Is null approved behavior or absent annotation? | Separate target scope and supervision masks |
| Invented tool or handoff state | Draft promises an action that never occurred | Was capability available and execution observed? | Separate intention, tool call and confirmed outcome |
| Rewriting history creates false trajectories | Later customer reply no longer follows actual input | Did rewritten prior text enter the next historical example? | Label synthetic trajectories explicitly |
| Selection rejects difficult users disproportionately | Cleaner data reduces relevant coverage | Compare hold/reject reasons across slices | Review representativeness, not only acceptance rate |
| Approval persists after edits | Approved hash no longer matches target | Are approval and exact input/target version bound? | Re-review changed examples |
| Pseudonyms leave identifying details | Data handling assumptions fail | Inspect free text and rare combinations | Separate privacy review from response quality |
| Prompt-like text inside customer content controls reviewer | Labeling can be manipulated by untrusted conversation text | Adversarial examples and instruction-boundary review | Treat conversation text as evidence, not grading instructions |
| Tiny test set supports inflated conclusions | “Excellent” model claim lacks support | Report sample counts, clusters and uncertainty | Fresh prospective evaluation before broad claims |
| Unknown deployment shift | New products, channels or user needs break labels | Monitor novel clusters and out-of-distribution errors | Version policy; revise coverage and re-audit |

These are risks to investigate, not assertions that every failure has occurred in the supplied records.

## 7. Research clusters

This is a research agenda, not a completed literature review. Each cluster connects X, Y and our uncertainty to a question that could change the design. The two overarching questions are **how to obtain the right data** and **how to detect and reduce relevant bias**. “Bias-free” is not an achievable certification from this sample.

| Cluster / research area | X/Y and knowledge gap | Research questions | Proposed investigation and decision informed |
|---|---|---|---|
| R1 — Dataset construction and sampling | X coverage is a known unknown; Y distribution reflects outbound selection | Which event boundaries represent real decisions? What situations are missing? How many candidates are duplicates versus useful recovery examples? | Compare full authorized event logs with extracted boundaries; build coverage map. Decide what to acquire and what not to multiply |
| R2 — Partial observability and temporal validity | Missing X may make Y unidentifiable | What minimum context is sufficient for each action? How often does recovered history or historical policy change a label? | Paired review with/without recovered context, blinded to prior labels. Define sufficiency rules and reconstruction policy |
| R3 — Label validity and adjudication | Desired Y and acceptable alternatives are known unknowns | What makes an action correct? Can reasonable reviewers disagree without either being wrong? Which dimensions need independent evidence? | Multi-reviewer calibration with reason codes and acceptable-action sets. Define rubric and adjudication scope |
| R4 — Model judges, anchoring and calibration | Reviewer error is unknown; observed replies may bias Y | Does revealing the old response change labels? Can a model identify its own unsupported approvals? Do judge models share failure modes? | Randomized context-first/response-first comparison; blinded human audit of routine cases and disagreements. Choose reviewer workflow and routing evidence |
| R5 — Active learning and review economics | Informative X and uncertain Y compete for human time | Which review resolves the most reusable uncertainty? Should humans review cases, shared facts, or policy conflicts first? | Compare uncertainty, diversity and shared-blocker prioritization by corrected labels per review effort. Allocate review budget |
| R6 — Factual grounding and knowledge provenance | K is absent; factual Y cannot be certified from repetition | Which claims can be verified independently? Which are time-sensitive or segment-specific? How should unsupported questions be handled? | Build unverified claim/conflict register; obtain owner confirmation with scope/date. Define evidence authority and update process |
| R7 — Preference learning and style disentanglement | S is absent; style Y is not uniquely defined | What voice does SBL actually want? Can humans prefer a draft's style while rejecting its claims or action? | Compare meaning-preserving rewrites only after content approval; collect separate style/action judgments. Establish style version 1 |
| R8 — Fairness, representation and measurement bias | X slices and Y approval criteria may embed bias | Whose situations are absent? Are terse, non-native or multilingual users more often misunderstood? Do model/human reviewers disagree unevenly? | Slice coverage, action errors, unsupported claims and routing rates with uncertainty; paired meaning-preserving variants. Define relevant fairness criteria without requiring identical actions |
| R9 — Offline evaluation and causal inference | Observed outcomes follow one historical action, not alternatives | Does lower label loss improve real assistance? Can conversion be attributed to the reply? What independent holdout is needed? | Grouped held-out evaluation followed, if later authorized, by prospective evaluation. Keep causal claims out of retrospective accuracy results |
| R10 — Open-set discovery and sociotechnical reliability | Unknown unknowns in X, Y and reviewer workflow | What would an open-ended reviewer flag outside our taxonomy? Which failures escape agreement-based checks? What new cases appear after policy changes? | Diverse error review, adversarial probes, incident collection and recurring taxonomy revision. Reopen assumptions when novel failures appear |

### Priority research sequence

1. **Boundary and evidence validity:** R1, R2 and R6 establish whether an example can be meaningfully judged.
2. **Label and routing validity:** R3 and R4 establish how a reviewed Y earns approval; R5 helps allocate human effort.
3. **Voice and bias:** R7 and R8 define desired expression and test who benefits or is overlooked. Bias checks also apply to the earlier stages, not only the final dataset.
4. **Generalization and surprise:** R9 and R10 assess whether the design survives independent data and new situations.

For each future experiment, record the hypothesis, source population, X fields, Y definition, sampling unit, reviewer blinding, outcome metric, limitations and the architecture decision its result could change. Do not treat a research question as settled just because an equation can be written for it.

## 8. Alternatives and consequences

| Alternative | Why it is not the current scope |
|---|---|
| Train directly on every observed reply | Confuses historical behavior with desired behavior and copies unsupported claims |
| Treat each whole conversation as one target | Hides distinct action choices and makes local correctness harder to review |
| Require humans to approve every routine target | Conflicts with the user's authorized model-approval route |
| Let a strong model approve every target | Cannot resolve missing company authority or shared blind spots |
| Grade only drafts, not actions | Rewards well-written answers when the appropriate action was clarification, waiting or handoff |
| Certify the dataset as bias-free | No defined universal bias criterion or representative evidence supports that claim |

The chosen scope adds review and provenance work but makes uncertainty explicit. Some candidates may remain held; some may support only action labels. Approval counts and mathematical elegance are not substitutes for representative evidence.

## 9. Open decisions and revisit conditions

Open: authoritative owners for facts/policy/style, action vocabulary and real capabilities, privacy criteria, calibration method, acceptable risk thresholds, relevant fairness slices, review budget, holdout design and the exact meaning of a routine case after calibration. No specific model, dashboard, training method, loss weight or sampling percentage is selected here.

Revisit this ADR when recovered history changes labels, routine approvals fail audits, policy conflicts recur, a new user/situation slice exposes errors, independent evaluation contradicts apparent quality, or deployment capabilities change.

Documentation checkpoint: this ADR captures the initial architecture rationale and research agenda. It does not approve product facts, label any candidate, solve an optimization problem, or authorize implementation.
