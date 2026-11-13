# Proposed KIN for OU pilot: evidence before adoption

**Status:** Draft for OU INC and appropriate OU review; **no recruitment, institutional authorization, or pilot enrollment is claimed**.  
**Updated:** 12 November 2026

## 1. Evaluation question

Does the **OU Daily Briefing** help consenting OU students plan a day, identify a genuine schedule clash and find an official campus resource **more accurately and efficiently** than their usual workflow, without undermining privacy, accessibility or trust?

This is a proposal, not a registered university study. Consult appropriate OU review offices to determine whether human-subjects research/IRB review or other consent and institutional approvals are required.

## 2. Three phases and gating conditions

### Phase A — Public/synthetic prototype demonstration

**No real academic records or OU credentials.** Use the existing fictional timetable, static campus events and public source links. Test the reliability, safe fallback, accessibility and source-freshness UX.

Exit gate: demo tasks are reproducible; synthetic source links work; no private OU system access or unsupported branding; documented risk review.

### Phase B — Discovery with students and campus stakeholders

**Proposed scope:** 20–30 interviews, potentially including students, faculty and staff to capture needs. Interviews are voluntary; seek any required approvals before recruitment. Do not collect login credentials or protected student records.

Questions: Which planning problem matters daily? Which existing OU tools address it? What is missing? What would users trust KIN to read/change? What would they refuse to share? What value would justify ongoing use?

Exit gate: a sharply defined first workflow, a documented competitor/current-workflow baseline, and a stakeholder who will sponsor next-stage evaluation.

### Phase C — Limited consented pilot (only after required approvals)

**Proposed planning assumption:** 25–50 voluntary students over roughly four weeks. Prefer manually entered, permitted/non-sensitive schedules and public OU data at first. Any real student data or institution-controlled integration needs explicit authorization, a reviewed environment and a clear lawful basis/consent process.

Consider a separately approved, limited faculty/staff demonstration later; employees should not be included by default due to distinct confidentiality, HR, privacy and employment risks.

## 3. Pilot tasks and measures

| Workflow task | Primary measure | Guardrail |
|---|---|---|
| Find today's two most important obligations | Time to correct answer; accuracy vs source | No invented deadline |
| Detect a conflict and propose a safe adjustment | Correct conflict detection; explicit approve/reject | Fixed/protected items never silently moved |
| Find an OU resource or announcement | Successful authoritative link; freshness | Never invent closures or support office claims |
| Return for another daily briefing | Weekly repeat use; opt-out/retention | Voluntary; transparent analytics, no sensitive content |
| Use keyboard/screen reader | Task completion and usability feedback | Accessibility issues documented and prioritized |

**Illustrative success thresholds for discussion, not promises:** >=90% correct outcomes on curated, synthetic task set; 0 unauthorized writes or private-data transfers; measurable reduction in task-completion time vs baseline; strong user understanding of what is and is not official; no critical accessibility blockers. Establish final thresholds with reviewers *before* pilot data is collected. Avoid cherry-picking favorable examples.

## 4. Data minimization and protections

- Use test accounts and synthetic data for Phase A; keep publicly accessible demo **fictional-data only**.
- Do not use student IDs, course grades, protected records, employee HR data, passwords, sensitive messages or private research material in a public/guest deployment.
- Collect only necessary consent/usage metrics with documented retention and deletion procedures; assess if participant compensation is appropriate and permitted.
- Pseudonymize survey/analytics data and limit who can access it; never expose personal planning routines to university administrators.
- Hosted LLM requests require verified provider terms and UTS approval for relevant data classifications. UI consent alone is not sufficient.
- Define escalation, withdrawal, support, backup, access, retention and incident-response arrangements **before** any real user pilot.
- Publish an honest description of availability, limitations, model use and data handling.

## 5. Comparison and analysis plan

- Compare KIN with existing workflows (OU portal links, standard calendar, Gemini chat) **on identical tasks** where feasible.
- Record median task time, completion success, false conflict/notice rate, weekly active participation, subjective usefulness and accessibility findings.
- Report small-sample uncertainty and selection bias; do not describe directional improvements as statistically proven without suitable design.
- Separate baseline measured results from anecdotal testimonials and from forecasts.

## 6. Deliverables for stakeholders

1. Two-page OU Daily Briefing demo brief and a 3-minute synthetic-data walkthrough.
2. Source/provenance matrix, Gemini/Gemma distinction and AI-off fallback.
3. Privacy data-flow map, lightweight threat model, consent and ethics-review decision.
4. Accessibility findings with remediation plan.
5. Pilot protocol, sample and metrics; after authorization, anonymized results.
6. Six-month budget with assumptions and an optional institutional licensing hypothesis.

## 7. Decision meeting agenda

- Does OU need the proposed workflow, and which office would sponsor it?
- Is it distinct enough from Google Calendar, Gemini and existing portals?
- Which role should be served first: students vs employee workflows?
- What is OU's Technology Investment Intake / security review sequence?
- Who approves communications and student recruitment?
- What evidence would justify a larger pilot or vendor procurement?

Related: [strategy](OU_FIRST_STRATEGY.md), [readiness](OU_INSTITUTIONAL_READINESS.md), [Gemini decision](OU_GEMINI_DECISION.md), and [GitHub pilot issue #19](https://github.com/mbilal-OU/KIN/issues/19).
