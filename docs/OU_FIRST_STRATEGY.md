# KIN for Oakland University: institutional-first strategy

**Status:** Proposal for stakeholder discovery, not an OU-approved product or a commitment by Oakland University.  
**Updated:** 12 November 2026  
**Product:** KIN — Kinetic Intelligence Network. *Life changes. KIN moves with you.*

## 1. North star

**First target customer: Oakland University (OU).** Seek an authorized, evidence-driven path to making KIN an optional, officially supported companion for OU students, then faculty and staff. A subsequent university licensing model is a hypothesis to validate, not an existing contract.

**Value proposition:** KIN connects *approved* university information with a user's personal planning context to help them understand what needs attention, spot conflicts, find trustworthy sources, and approve safe next steps. It does **not** replace OU's existing systems, institutional decision-makers, or its existing AI tools.

**Not a generic AI chatbot.** KIN's proposed value is in university-specific, cited workflows, deterministic schedule and conflict logic, consent boundaries, verified state changes, and useful daily follow-through.

**Branding constraint:** The application and repository are student-founded and unaffiliated with OU. Any official OU identity, logo use, endorsement, campus-wide claims, or deployment requires separate written authorization.

## 2. Users and jobs to be done

| Audience | First useful job | Later possibilities (subject to approval) |
|---|---|---|
| Students (initial focus) | Create a verified daily briefing from user-supplied schedules, public OU dates/events/resources and current weather; identify and explain scheduling conflicts | Opt-in, authorized Moodle/course deadlines; OU Google Calendar; accessible student-success referrals |
| Faculty | Manage teaching, office hours, lab/research meetings and OU resources without conflating personal and institutional information | Opt-in authorized calendar workflows, deadline triage and source-grounded faculty resources |
| Staff | Navigate official OU policies, events, work calendars and internal resources | Authorized workflows and role-specific systems, with stronger enterprise controls |

**Do not claim** that private course schedules, Moodle, MySAIL, staff HR systems or OU email are currently connected. Public content must be dated and linked, with stale/unavailable states visible.

## 3. The first flagship experience: OU Daily Briefing

1. User chooses **student** (first pilot); faculty/staff prototypes can follow.
2. User adds synthetic or manually entered, non-restricted commitments, or imports an allowed .ics file.
3. KIN presents today's priorities, upcoming events/deadlines, weather context, source-linked OU announcements, conflicts, and accessible university resources.
4. Deterministic logic validates time zones, prioritization inputs, and scheduling collisions.
5. Optional AI explains the rule-based findings, marks uncertainty, and cites provenance. It cannot create an authoritative university status or silently execute changes.
6. Any change to KIN's *own* local schedule requires explicit confirmation and read-back verification. No changes to external OU systems without new approvals and technical gates.
7. A clearly labeled **source timestamp** and **unsupported/unavailable** state appears for each external feed.

**Why OU might care:** fewer wasted navigation steps, more discoverable campus resources, improved student planning, accessible information, and evidence of safe AI adoption. These are pilot hypotheses; no measured outcomes or institutional endorsement exist yet.

## 4. Product principles

- **OU-first, not OU-exclusive:** institutionally useful in the first market, with university connectors modular so a future standalone KIN remains possible.
- **Complement Gemini, do not compete with the Gemini chat app:** model-agnostic AI orchestration, trusted workflow logic and source-grounded OU context. See [OU_GEMINI_DECISION.md](OU_GEMINI_DECISION.md).
- **No shadow IT:** no OU passwords, unofficial Moodle/MySAIL scraping, unapproved OAuth scopes, employee/student data harvesting, or unauthorized data transfers.
- **Personal autonomy:** a university sponsor does not gain access to a user's private workspaces, routines, assistant chats, or inferred life details.
- **Human control:** no autonomous university/student decisions; explicit approval for side effects; no AI-only decisions on student status, course cancellations, employment, awards or disciplinary matters.
- **Accessibility by design:** keyboard navigation, screen-reader support, readable motion/contrast and testing, with OU's publicly stated WCAG 2.1 AA compliance deadline of **26 April 2027** (stricter design targets may be adopted).
- **Grounded facts:** distinguish official notices, estimated data, model suggestions, and user input.
- **Respect the existing product:** preserve Streamlit MVP and deterministic/offline core while validating a future enterprise architecture.

## 5. Clear boundaries: now vs proposed

| Capability | Current public prototype | OU-target future requirement |
|---|---|---|
| Scheduling and conflict detection | Manual/local, deterministic; some cross-workspace awareness | Role-aware, accessible UX and robust tenant isolation |
| Campus context | Curated official OU links/athletics with source labels | Approved public feed adapters and freshness monitoring |
| AI | Optional Gemma via Gemini API, local Ollama, or AI-off fallback | Gemini-model feasibility *subject to separate API approval*, model selection, cost/privacy reviews |
| Data | Local guest SQLite; not encrypted/authenticated for production | Authentication, encryption, access controls, lifecycle/incident response |
| Integrations | None with private OU systems | Supported APIs, OU UTS authorization, consent, least privilege |
| University endorsement | None | Separate official review, contract, procurement, approval |

## 6. How KIN would create measurable institutional value

Proposed *evaluation outcomes*, not promises:

- Time to identify deadlines/conflicts and find an official OU resource.
- Correctness of source links and confidence calibrated to stale/unavailable data.
- User task success, accessibility task completion, and perceived utility.
- Four-week voluntary repeat use, opt-out rate, trust, privacy understanding.
- Support and hosting cost per active pilot user; security incidents and escalation rate.
- Staff/faculty administrative time spent on recurring informational requests (in separately approved future studies).

Evaluate against a control or current workflow when feasible. Never equate downloads, one-time demo satisfaction or AI usage with retention/ROI.

## 7. Commercial model and stakeholder route

**Commercial concept:** an institution-funded annual SaaS/service license, perhaps following a limited departmental pilot. This is **not a claim of OU demand, budget availability or procurement approval**. Separate founder funding, grants, institutional licensing, and equity financing. No valuation or revenue claims without evidence.

**Potential discovery stakeholders (roles, not endorsements):** OU INC SmartZone entrepreneurship advisors; student-success/student affairs staff; faculty and employee representatives; University Technology Services (UTS); academic technology/e-LIS; accessibility and privacy/security teams; purchasing/legal; institutional research/assessment where permitted.

**Suggested approach:**
1. Incubator intake and feedback: market discovery, entity/IP/branding and founder responsibilities.
2. Ask OU INC to help identify a *business owner* or pilot sponsor at OU.
3. Conduct interviews and a synthetic-data workflow demonstration before requesting OU system access.
4. Seek UTS guidance on the Technology Investment Intake and AI security requirements.
5. Design an approved voluntary pilot and validate outcomes.
6. Only then discuss paid procurement, service ownership and possible official deployment.

## 8. Next decisions to record

- Which student segment and **one** highest-value daily workflow should lead?
- Who at OU can sponsor evaluation? Who owns support and security review?
- Which public OU sources can be ingested under documented terms?
- What, if any, approved Gemini API and data path could be used?
- Is this a non-research usability pilot or human-subjects research requiring OU determination/approval?
- What is the funding vehicle, IP position, founders' agreement, and work authorization pathway? Seek appropriate university/legal advice.
- What accessible, secure pilot infrastructure and incident response are needed?

## 9. Related documents and tracking

- [OU Gemini architecture and decision gates](OU_GEMINI_DECISION.md)
- [OU pilot protocol and metrics](OU_PILOT_PLAN.md)
- [Institutional readiness and risk checklist](OU_INSTITUTIONAL_READINESS.md)
- [Technical roadmap](ROADMAP.md)
- [Security boundaries](SECURITY.md)
- [GitHub development hub](DEVELOPMENT_HUB.md)
- Existing issues: [#19 OU pilot](https://github.com/mbilal-OU/KIN/issues/19), [#21 Gemini evaluation](https://github.com/mbilal-OU/KIN/issues/21), [#14 accounts](https://github.com/mbilal-OU/KIN/issues/14), [#15 encrypted storage](https://github.com/mbilal-OU/KIN/issues/15), [#16–18 OU connectors](https://github.com/mbilal-OU/KIN/issues/16).

## OU sources verified 12 November 2026

- [AI@OU: available generative AI tools](https://oakland.edu/ai/general-resources/)
- [OU Google Workspace](https://www.oakland.edu/uts/services/g-suite/)
- [OU AI Security Policy #820 (May 2026)](https://www.oakland.edu/policies/information-technology/820/)
- [OU AI usage guidelines](https://support.oakland.edu/TDClient/33/Support-Center/KB/PrintArticle?ID=757)
- [OU IT procurement review](https://support.oakland.edu/TDClient/33/Support-Center/KB/Article/140/IT-Procurement-and-Sourcing-Needs)
- [OU digital accessibility initiative](https://www.oakland.edu/digital-accessibility/)

**Caution:** Policies, contracts, availability and university positions can change. Reconfirm with UTS before representing any requirement as approved.
