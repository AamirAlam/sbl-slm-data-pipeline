# ADR-001: How we choose and review training examples — plain English

Original decision date: 23 September 2026.  
Plain-English version: 24 September 2026.  
Status: The overall approach is accepted as a starting point. Its assumptions, success measures and research plans still need to be checked.  
Scope: Planning and research only. This document does not authorize writing software or training a model.

This is a full plain-English version of [the original ADR](001-decision-point-curation-and-review.md). The original keeps the mathematical notation. This version explains the same decisions and objectives in words; it does not introduce a new architecture decision.

## 1. What we decided, and why

We will train on individual moments when the system needs to decide what to do next. One conversation may contain several such moments, so it may produce several training examples.

We call the information available at that moment **X**. We call the action and optional reply we want the model to produce **Y**.

An old reply tells us what the system did. It does not establish that the system did the right thing. A reviewer should first read the available context and decide what should happen next. Only then should they see and assess the old reply. This reduces the chance that they simply copy its mistakes.

A strong model may approve straightforward examples when there is enough evidence. Humans handle uncertainty. We will record whether each example was approved by a model or a human.

There are two separate questions:

1. Given what was known and allowed at the time, was the old response appropriate?
2. Given the rules we want the new model to follow, what should it do in this situation?

We may be unable to answer the first question because historical information is missing. We may still answer the second if we clearly supply and approve the intended rules and facts. We must label that example as a reconstructed situation rather than an exact replay of the past.

Even a bad old response can give us a useful training example if a reviewer creates a supported replacement.

### Decisions already made by the user

- Stay at the planning and research stage. Do not write code.
- Let models approve routine cases; send uncertainty to humans.
- There are no approved product facts, campaign rules or examples of the desired SBL writing style available yet.
- Record assumptions, reasons and possible failures so future agents can understand the decisions.

### What we know about the supplied data

The earlier inspection found 111 possible decision examples from 26 conversation threads, involving 25 prospects and three campaigns. These are not 111 independent conversations.

Every example has warnings that its history may be incomplete and its attached campaign context may not be the context that applied at the time. Twenty examples have no visible conversation history. The product-knowledge and sender-style fields are empty throughout.

Messages are marked `system` or `company`, but those labels do not tell us which model or person wrote them, or whether a human approved them.

The existing division is 93 examples for training, 15 for development checks and three for final testing. The inspection did not find the same prospect or thread appearing in more than one division. That does not establish that the test set is large or varied enough.

These findings come from [checkpoint 001](../curation/checkpoints/001-inspection.md). They describe the files, not whether the replies are correct. [Checkpoint 003](../curation/checkpoints/003-review-authorization.md) records the later decision to allow model approval of routine cases. Earlier checkpoints are historical records: they do not authorize further implementation or guarantee that files mentioned there still exist.

## 2. What X and Y contain

### X: what the model knows before deciding

X contains the following information when it is available:

| Part of X | What it means | What we must be careful about |
|---|---|---|
| Campaign goal and context | What this campaign is trying to achieve and whom it concerns | Record which version applies to this situation |
| Conversation flow and rules | What actions are permitted or expected | Rules found in an export have not automatically been approved |
| Product facts | Information the model can use to support its answer | Missing facts remain unknown; the model must not invent them |
| Writing style | The approved way SBL wants the reply to sound | There is no approved guide yet; old replies are possible references only |
| Conversation so far | Messages available before this decision, including the customer's latest message when that triggered the decision | Exclude later messages and the response currently being assessed |
| Trigger, channel and time | Why a decision is needed, where the conversation happens and when | Verify what any numeric codes mean |
| Available tools and current state | What the system can actually access or do at that moment | Do not assume it can check a calendar, retrieve information or contact a human |
| Missing information and source details | What is absent, where the information came from and what limitations apply | These warnings explain uncertainty; they do not establish product truth |

Earlier company or AI replies belong in X if the customer saw them, even if they were wrong. The next decision may need to correct an earlier mistake.

We must not silently replace those earlier messages with improved versions. If we rewrite the earlier conversation, we have created a reconstructed or invented example, which must be identified as such.

### Y: what we want the model to do

Y has three possible parts:

1. **The next action:** for example, answer, ask for clarification, ask a relevant sales question, offer a next step, refer the issue to a human, retrieve information, wait or stop.
2. **The details needed for that action:** for example, what information to clarify or which approved destination to use.
3. **A draft message, if a message is appropriate.** Waiting or retrieving information may require no customer-facing draft at that moment.

We must check that the proposed actions match what the product can actually do.

The desired answer is not something we already know perfectly. A reviewer proposes an answer based on the evidence. Several different actions or phrasings may be acceptable under the same rules; there may be no single correct sentence.

### How we assess the old response

After independently proposing Y, the reviewer sees the old response and checks:

- Was the action appropriate?
- Were factual claims supported?
- Did it address what the customer meant and asked?
- Did it follow the applicable rules?
- Did it match the desired writing style?

Each check can pass, fail, remain uncertain or be irrelevant to that case. Good writing must not cancel out an unsupported claim.

We also keep review records: who reviewed the example, why they made the decision, which evidence they used, and which exact input and output they approved. A file fingerprint can identify the exact version. These records help us check the process; they are not automatically things the model should see or generate.

## 3. What we are assuming

These assumptions need checking. Listing them does not make them true.

| ID | Assumption in plain English | What would challenge it or show we are using it incorrectly? |
|---|---|---|
| A1 | Each selected moment is a genuine opportunity to decide what to do next | We used the wrong triggering event, included future information or counted the same moment twice |
| A2 | Some examples may still contain enough information even when earlier messages are missing | Recovering the missing messages changes the appropriate action |
| A3 | The available facts and rules can support at least one acceptable answer for each accepted example | Rules conflict, needed facts are missing or the suggested action is impossible |
| A4 | Reviewers can help identify good answers, but both models and humans make mistakes | We treat agreement between reviewers as proof that an answer is correct |
| A5 | We can identify which cases are safe enough for routine model approval | Errors repeatedly occur in cases classified as routine |
| A6 | Examples from the same conversation are related | We report 111 examples as though they came from 111 independent prospects |
| A7 | We can define the desired writing style while still requiring correct behavior | We reward pressure, false identity or unsupported promises because they resemble old SBL messages |
| A8 | We need to investigate whether the sample represents real future use | Important customer situations are missing from the selected data |
| A9 | An example can teach the right action even when we cannot yet approve its wording | We mistake an unprovided draft for an instruction to send no message |
| A10 | We can keep historical review separate from examples written for the desired future rules | We silently judge an old response using facts or rules that only became available later |

For missing context, the main question is: **could a plausible missing fact change what we should do?**

The original equation expresses a cautious acceptance rule: consider plausible missing information and accept the proposed target only if it would still be good enough across those possibilities. We have not defined every possibility or chosen how much error is acceptable. We have not demonstrated that any example passes this test.

We also cannot assume missing information is random. For example, the extraction process might omit certain kinds of conversations more often than others.

## 4. What the mathematical objectives mean

This section translates every proposed objective into words. No numerical importance weights, acceptance limits or solutions have been chosen.

### 4.1 Choose examples for usefulness, variety and support

We want to choose a set of examples that:

- Contains useful lessons.
- Covers different relevant situations.
- Does not consist mainly of repeated versions of the same lesson.
- Passes the required evidence and approval checks.
- Fits within the time or money available for review.

The first formula balances usefulness and variety against repetition. Its conditions say that an example cannot be selected unless it passes the required checks, and total review cost must stay within the available budget.

We still need to establish how to measure usefulness. A model saying it is confident is not sufficient evidence that an example is useful or correct.

Choosing carefully from these records cannot recover situations that are absent entirely. We may need more real data. Creating explicitly invented examples would be a separate decision.

### 4.2 Teach the action, its details and the appropriate wording

The proposed learning task can be understood in three steps:

1. Given X, choose the action.
2. Given X and that action, choose the details needed to carry it out.
3. Given X, the action and its details, write the draft if one is needed.

This describes the behavior we want. It does not require three separate models.

A **loss** is a penalty used during training when a prediction differs from the approved target. The proposed training objective combines penalties for getting the action wrong, getting its details wrong and producing the wrong draft. We have not chosen how much importance to give each part.

Only approved parts of an example should contribute to that training penalty. If we know the correct action but do not have an approved draft, we can teach the action without teaching any wording.

That is different from approving “send no message.” In the first case, the draft is unknown. In the second, the absence of a draft is part of the correct behavior.

Examples may receive different importance weights, but those weights would need justification. The objective averages the penalties across the selected examples, taking those weights into account. There must be at least one accepted example for that average to be meaningful.

We train on the approved new output. Earlier unapproved messages in the conversation are context to understand, not text to copy as the desired answer.

When evaluating a response, matching one reference sentence word for word is not enough. The other formula says to compare the response with the acceptable answers and assess how close it is to a valid one. That comparison must consider meaning, action and rules—not just spelling. We have not yet defined a reliable way to measure that closeness.

### 4.3 Improve helpful behavior while limiting serious mistakes

We want the model to make better action choices, address the customer's needs and use the approved writing style in situations it will actually encounter.

At the same time, we want explicit limits on unsupported factual claims and serious violations of the rules. Better wording must not compensate for a serious factual or behavioral failure.

The formula therefore separates the behavior we want to improve from failures we want to keep below agreed limits. SBL's responsible owners still need to define those limits and what counts as a serious failure.

A sale or booked meeting may be a useful secondary outcome. However, this historical export cannot tell us whether a particular reply caused the sale. Other factors may have influenced the result.

### 4.4 Decide when models can approve and when humans should review

Each case can go to a model, go to a human or remain on hold.

The proposed model-approval rule requires enough evidence, no unresolved uncertainty and a sufficiently low estimated chance of an incorrect approval. That estimate should come from checking actual review results. A model's statement that it is “90% confident” does not establish that it is wrong only 10% of the time.

We have not chosen the error limit or shown that the model's estimates are reliable.

The cost objective asks: how can we use review time efficiently while keeping incorrect model approvals below an agreed limit?

There is a possible misleading result: a process could avoid approval errors simply by putting everything on hold. To avoid calling that success, we would also measure whether the process resolves a meaningful number of cases when the evidence allows it.

This is not permission to approve unsupported examples to meet a quota. If the evidence is insufficient, a case must stay unresolved. Until we have checked the approval process, there may reasonably be no model-approved cases. That does not demonstrate that we have a useful automated reviewer yet. If there are no model approvals, we cannot measure their error rate.

Humans also take time and make mistakes. We must audit some model-approved routine cases, not just cases already sent to humans. Otherwise, mistakes in identifying routine cases will remain hidden. No audit percentage or promised error rate has been approved by this formulation.

### 4.5 Find and reduce bias without claiming it is absent

We should examine performance across relevant groups of cases, such as different languages, campaign stages, company types or communication styles, where collecting and using those distinctions is appropriate.

For each group, measure how often or how badly the model gets things wrong. Then compare groups and investigate the largest differences. One possible objective is to improve the worst-served group while also improving overall performance.

Every result needs a sample count and an explanation of how uncertain the estimate is. A result from very few examples may be misleading. Our reference answers are reviewed judgments rather than perfect truth, so their limitations also matter.

Fairness does not necessarily mean giving everyone identical replies or identical reply rates. Different needs may justify different actions. We should compare outcomes while considering relevant differences in difficulty and available evidence.

Bias can enter at two selection stages: which situations were exported in the first place, and which exported situations we accept for training. The final training set may therefore differ substantially from the situations encountered in real use.

We should also check which groups are more often sent to humans, approved, held or rejected. Giving some examples more weight may help only if we understand the real population and have enough examples of the relevant situations. Weighting cannot repair a category that is entirely absent.

A finite review cannot prove that the dataset is free of every possible bias.

## 5. What we know, what we do not know, and what we have not considered

X and Y describe the learning task. Knowns and unknowns describe our understanding of it. **X does not mean “known,” and Y does not mean “unknown.”** Some input information is missing, and some parts of a target can be supported while others remain uncertain.

### Known knowns: things we know we know

We know the recorded file structure, source identifiers, visible messages and explicit warnings. We have agreed on the target structure and on model approval for routine cases with humans handling uncertainty.

We should preserve these facts and record their versions without claiming that they establish more than they do.

### Known unknowns: gaps we can name

We know that some history, historical rules, product facts, intended writing style and meanings of trigger codes are missing or unverified. We also do not know the right action in every ambiguous case, whether every proposed draft is factually supported or how reliable the reviewers are.

We should list each gap, investigate it and hold the affected part of an example when necessary.

### Unknown knowns: answers may exist elsewhere

An employee may know an important product fact or exception that has never been documented. An operational record may contain a customer commitment that reviewers have not seen. Experienced sales staff may have useful judgment they have not explained.

We should ask the appropriate people, inspect records we are allowed to access and turn relevant knowledge into documented guidance.

### Unknown unknowns: problems we have not identified yet

We may encounter unfamiliar customer situations, hidden extraction errors or blind spots shared by human and model reviewers. Our current checklist may not contain the right question to detect them.

We need reviews that allow people to report unexpected problems, perspectives from different reviewers, records of failures and repeated checks over time.

We cannot finish a complete list of unknown unknowns. Once we discover one, it becomes a known unknown with a specific question to investigate.

## 6. What can go wrong and what to consider

These are possible failures to investigate. We are not claiming that every one has occurred in the supplied data.

1. **The reviewer copies the old reply's mistake.** A confident or well-written reply can influence the reviewer. Compare judgments made before and after seeing the reply, and save the independent judgment first.

2. **We judge an old response using today's facts.** A historical answer may look wrong only because a product or rule changed. Check the dates and keep historical review separate from examples based on future rules.

3. **Missing history hides an important instruction.** An earlier promise or request to stop contact could change the right action. Ask whether recovering the missing messages would change the decision, and hold uncertain cases.

4. **We only collect moments when the system replied.** The model may learn that it should always respond. Investigate real opportunities to wait or stay silent; do not invent them merely because an outbound message is absent.

5. **Messages are placed in the wrong order.** Information from the future may accidentally appear in X. Verify actual event or delivery order rather than assuming creation timestamps establish it.

6. **Repeated conversations make the dataset look bigger than it is.** Overlapping histories and repeated templates can exaggerate diversity and evaluation reliability. Count prospects, distinct events and repeated content, and keep related examples in the same training or evaluation group.

7. **Repeated AI claims become accepted facts.** Several old replies may repeat the same unsupported statement. Look for evidence independent of those replies; keep the collected claim unverified until it is properly checked.

8. **The writing model and reviewing model share the same blind spot.** Agreement may give false reassurance. Record which models were involved and check routine approvals with humans as well as examining disagreements.

9. **A human's personal sales preferences become the definition of correctness.** Reviewers may favor aggressive persuasion or a familiar way of speaking. Use explicit criteria, compare reasons across reviewers and groups, and resolve disagreements. Humans can be biased too.

10. **Nobody knows which source has authority.** A convenient document may be treated as official without justification. Record who approved a fact, when it applies and which situations it covers.

11. **Imitating SBL's voice reproduces bad behavior.** Old messages may include pressure, misleading identity or unsupported promises. Approve the action and content before judging the style.

12. **An absent draft is mistaken for an instruction to stay silent.** “We have not approved wording” and “no message should be sent” are different labels. Keep that distinction explicit when deciding what the example teaches.

13. **The draft claims an action happened when it did not.** The model may say a meeting was booked or a human was contacted without evidence. Distinguish a proposed action, an attempted action and a confirmed result. Verify the capability actually exists.

14. **We rewrite the past but keep the customer's original reaction.** That creates a conversation that did not happen. Preserve actual history or clearly identify the rewritten example as constructed.

15. **Removing difficult examples removes certain users.** Rejecting unclear, multilingual or otherwise challenging cases may make the dataset look cleaner while making it less representative. Compare reasons for holds and rejections across relevant groups.

16. **An edited example keeps an outdated approval.** A review applies to the exact input and target that were checked. Changed examples need renewed review, with records that identify the approved versions.

17. **Replacing names fails to remove identifying details.** Free text or combinations of rare details may still identify someone. Review privacy separately from whether the response is good.

18. **Customer text manipulates the reviewer.** A message may contain instructions telling an AI grader how to behave. Treat customer content as material to assess, not as instructions governing the review. Test whether the boundary holds.

19. **A tiny test set supports an exaggerated claim.** Good results on a few related cases do not prove broad quality. Report counts, related groups and uncertainty, and obtain fresh evaluation data before making strong claims.

20. **Real use changes.** New products, channels or customer needs can make old examples unreliable. Look for new kinds of errors, record rule changes and revisit the dataset's coverage.

## 7. Research clusters

These are connected sets of research questions, not completed research findings. Each connects X, Y and a gap in our knowledge to a decision that could change the design.

The two main questions are: **How do we obtain the right data? How do we detect and reduce relevant bias?** This sample cannot certify that bias is absent.

### R1 — Choosing and collecting the right examples

**Knowledge gap:** We do not know how well X covers the situations the model will encounter. The available Y examples are influenced by which moments produced an outbound message.

**Questions:** Which moments represent genuine decisions? Which situations are missing? Which records repeat the same lesson, and which teach a distinct lesson such as recovering from an earlier mistake?

**Possible investigation:** Compare the extracted examples with complete event records we are allowed to access, then map which situations are present or absent.

**Decision this informs:** What additional data to obtain and which apparent examples should not be counted repeatedly.

### R2 — Deciding how much context is enough

**Knowledge gap:** Missing parts of X may prevent us from knowing the right Y.

**Questions:** How much history does each action require? How often does recovered history or the correct historical rule change a reviewer's answer?

**Possible investigation:** Review cases with and without the recovered information, without showing reviewers the earlier labels.

**Decision this informs:** When context is sufficient, when an example must remain on hold and how reconstructed examples should be identified.

### R3 — Defining a correct reviewed target

**Knowledge gap:** We have not fully defined acceptable Y values or how to resolve reasonable differences between reviewers.

**Questions:** What makes an action correct? Can two different actions both be acceptable? Which judgments need independent factual evidence?

**Possible investigation:** Ask several reviewers to assess the same cases, record their reasons and identify acceptable alternatives.

**Decision this informs:** The review criteria and which disagreements require a final decision from an appropriate owner.

### R4 — Checking whether model reviewers are trustworthy

**Knowledge gap:** We do not know the reviewers' error rates or how much the observed reply influences their choice of Y.

**Questions:** Does showing the old response change the judgment? Can a model recognize unsupported approvals? Do different reviewing models make the same mistakes?

**Possible investigation:** Randomly compare context-first and response-first review. Have humans independently audit routine cases and disagreements without seeing earlier labels first.

**Decision this informs:** How review information should be presented and what evidence is needed before a case qualifies for routine model approval.

### R5 — Using human review time well

**Knowledge gap:** Many useful examples and uncertain answers compete for limited review time.

**Questions:** Which review resolves the most uncertainty across the dataset? Should a human review individual cases first, or settle a fact or rule that affects many cases?

**Possible investigation:** Compare ways of prioritizing uncertain cases, varied situations and shared unresolved questions. Measure how much useful correction each requires in review effort.

**Decision this informs:** How to allocate the review budget.

### R6 — Establishing trustworthy product facts

**Knowledge gap:** Approved factual evidence is missing from X. Repeated claims in old Y-like responses cannot establish truth.

**Questions:** Which claims can be checked independently? Which vary with time, plan or customer group? What should the model do when the needed answer is unsupported?

**Possible investigation:** Collect claims and contradictions as unverified items, then ask responsible owners to confirm their meaning, scope and dates.

**Decision this informs:** Which sources may support an answer and how those sources stay current.

### R7 — Defining the desired SBL writing style

**Knowledge gap:** X has no approved style guide, and several different phrasings of Y may be appropriate.

**Questions:** What voice does SBL want? Can a reviewer like a message's style while correctly rejecting its action or factual content?

**Possible investigation:** After approving the meaning and action, compare differently worded versions that preserve that meaning. Collect style judgments separately from correctness judgments.

**Decision this informs:** The first approved writing-style guide.

### R8 — Finding unfair gaps and biased judgments

**Knowledge gap:** Both the situations included in X and the criteria used to approve Y may favor some groups over others.

**Questions:** Whose situations are absent? Are brief messages, non-native writing or multilingual users more often misunderstood? Do humans and models disagree more for some groups?

**Possible investigation:** Compare coverage, action errors, unsupported claims and review decisions across relevant groups, with counts and uncertainty. Compare differently worded versions of the same underlying need.

**Decision this informs:** What fairness means for this task and which gaps need correction, without assuming that everyone should receive the same action.

### R9 — Checking whether results carry over to real use

**Knowledge gap:** Each historical outcome follows the action that was actually taken. We do not observe what would have happened under every alternative Y.

**Questions:** Does better performance against reviewed answers mean better customer assistance? Can a conversion be attributed to the response? What independent test data is needed?

**Possible investigation:** Evaluate on separate groups of prospects, then, if later authorized, assess new cases as they occur.

**Decision this informs:** How to evaluate the model and which claims the evidence supports. Historical accuracy alone does not establish that a reply caused a business outcome.

### R10 — Discovering failures outside our current checklist

**Knowledge gap:** There may be problems in X, Y or the review process that we have not considered.

**Questions:** What would reviewers notice if they could report anything rather than only select checklist categories? Which failures do reviewers agree on incorrectly? What new problems appear after rules change?

**Possible investigation:** Use reviewers with different perspectives, deliberately difficult examples, records of failures and recurring updates to the error categories.

**Decision this informs:** When to reopen assumptions and revise the architecture.

### Suggested research order

1. First establish whether examples contain valid decision moments and enough trustworthy evidence: R1, R2 and R6.
2. Then establish how targets earn approval and how human effort is allocated: R3, R4 and R5.
3. Define the desired voice and examine bias: R7 and R8. Bias checks also belong in the earlier steps, not just at the end.
4. Check performance on independent situations and look for unexpected failures: R9 and R10.

For every future experiment, record what we expect to learn, which population the data comes from, what X contains, what Y means, how cases are selected, what earlier information reviewers can see, how results will be measured, the limitations and which design decision the result could change.

Writing an equation or stating a research question does not answer it.

## 8. Other approaches we considered

| Alternative | Why it is not the chosen approach |
|---|---|
| Train on every old reply | This would copy past behavior, including unsupported claims, without establishing that it is desirable |
| Use each whole conversation as one target | This would hide the separate action choices within the conversation and make individual decisions harder to assess |
| Require human approval for every routine example | The user has authorized model approval for routine cases |
| Allow a strong model to approve everything | A model cannot resolve missing company facts or rules simply by sounding certain, and reviewers can share blind spots |
| Assess only the wording | A well-written reply may still be the wrong action when clarification, waiting or human help was needed |
| Declare the dataset bias-free | We have neither a universal definition nor enough representative evidence to justify that claim |

The chosen approach requires more review and record-keeping. In exchange, it makes uncertainty visible. Some examples may remain on hold, and some may teach only the action. A large approval count or an elegant formula does not replace evidence that the data represents the task.

## 9. What remains undecided and when to revisit this ADR

We still need to decide:

- Who has authority to approve product facts, rules and writing style.
- Which actions the model may choose and which capabilities actually exist.
- What privacy checks are required.
- How to measure reviewer reliability and what error levels are acceptable.
- Which groups and situations matter for bias assessment.
- How much review effort is available.
- How to obtain and organize independent evaluation data.
- What qualifies as routine after the review process has been checked.

This ADR does not select a specific model, dashboard, training method, importance weight or audit percentage.

Revisit it if recovered history changes approved answers, audits find mistakes in routine approvals, conflicting rules keep appearing, a new group or situation exposes errors, independent testing gives worse results than expected, or product capabilities change.

This document records the reasoning and research questions. It does not approve product facts, approve any of the 111 examples, solve the proposed objectives or authorize implementation.
