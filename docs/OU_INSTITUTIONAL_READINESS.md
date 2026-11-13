# OU institutional readiness: security, accessibility, procurement and governance

**Status:** Gap analysis, not an attestation of compliance or approval.  
**Updated:** 12 November 2026  
**Scope:** Future KIN deployment to OU students, faculty and staff. Review scope with OU University Technology Services (UTS).

## Critical policy references

- [Policy #820 — Artificial Intelligence Security (issued May 2026)](https://www.oakland.edu/policies/information-technology/820/). AI applications are subject to university software/hosted-solution review; unauthorized entry of OU Confidential/Internal data into AI services is prohibited. University-data IT services require the Technology Investment Intake process.
- [OU AI usage guidelines](https://support.oakland.edu/TDClient/33/Support-Center/KB/PrintArticle?ID=757). Human responsibility, data classification, transparency, academic integrity and AI model-change review.
- [OU IT Procurement and Sourcing Needs](https://support.oakland.edu/TDClient/33/Support-Center/KB/Article/140/IT-Procurement-and-Sourcing-Needs). UTS review may request HECVAT, SOC 2 Type II reports and VPATs; review addresses security, accessibility, compliance, architecture and contracts. This **does not mean every artifact is mandatory in all cases**.
- [OU Digital Accessibility](https://www.oakland.edu/digital-accessibility/). OU references WCAG 2.1 AA and a Title II deadline of **April 26, 2027**.
- [OU Google Workspace](https://www.oakland.edu/uts/services/g-suite/) and [AI@OU](https://oakland.edu/ai/general-resources/). Gemini application access != sanctioned Gemini API for KIN.

## Deployment tiers

| Tier | Allowed focus | Non-negotiable boundary |
|---|---|---|
| 0: Public demo | Synthetic schedules, public OU links, no real student/employee data | Explicitly unofficial, no account/credential collection, no sensitive Gemini API calls |
| 1: Voluntary usability pilot | Manually entered minimal, permitted data in a reviewed environment | Written sponsor approval, applicable research/ethics determination, defined data flows, secure identities and operations if personal data used |
| 2: Authorized institutional integrations | Scoped OU identity, schedules, LMS/calendar or employee features | Formal UTS procurement/security approval, contracts, supported APIs, role-based authorization, user consent and operational support |
| 3: University-wide service | Approved OU-branded optional production service | Institutional owner, vendor support/SLA, incident response, accessibility, privacy/data retention, rollout governance, procurement/licensing |

**No tier is assumed approved today.** Prototype guest SQLite is **not** ready for Tier 1 with real private data or multi-user hosting.

## Readiness checklist with owners to confirm

| Area | Current gap / action | Evidence to produce |
|---|---|---|
| Sponsor and ownership | Identify an OU business unit sponsor and product contact; confirm founders' IP, university trademark permissions and MIT licensing implications | Signed sponsor/scope decision; legal/IP notes |
| Procurement | Ask UTS which Technology Investment Intake process and review artifacts apply | UTS response, review checklist and approvals |
| Data map | Inventory data categories by source, purpose, retention, controller/processor, model destination | Data-flow diagram, approved classification matrix |
| Authn/authz | No secure multi-user accounts today | Independent auth or approved SSO design, tenant isolation, least privilege and tests |
| Storage | Unencrypted single-user SQLite | Encryption, backup/restore, retention and deletion procedures, access-control audit |
| AI provider | Current optional Gemma through Gemini API is not OU approved | Documented OU AI data policy and model/API/contract decision |
| Network and app security | Need external assessment, secrets/CI, dependency and supply-chain review | Threat model, remediation list, scans and verified CI |
| Accessibility | No formal audit | WCAG task-based audit, VPAT if requested, screen reader and keyboard test evidence |
| Operations | No production SLA/support/incident response | On-call ownership, runbook, breach/reporting route, reliability targets |
| Research/consent | No authorized student study | Recruitment/consent/ethics determination and minimum-data plan |
| AI reliability | Source errors, hallucinations, prompt injection and spoofed notices | Synthetic regression suite and red-team test results |
| Integration | No approved OU private-data connectors | OU-approved protocols, consent scopes, API docs and revocation plan |
| Institutional governance | No OU service agreement or data processing agreement | Roles, review board, vendor agreements, change-management process |

## Required product behavior

- Source-linked official information with retrieval timestamps; never assert an OU closure without verified official notice.
- Model output treated as untrusted explanatory text; deterministic checks and role rules are authoritative for schedule updates.
- Separate student, work and personal contexts; default-deny cross-tenant and institutional visibility.
- Safe, accessible fallback when the LLM, campus source or network is unavailable.
- Document why and when a user-facing AI feature sends data to a third party. Enforce data-classification restrictions at the backend.
- Avoid employee scoring, academic/disciplinary decisions, inferred protected traits and covert monitoring.
- Maintain user-facing export/delete rights subject to applicable agreements and legitimate retention obligations.
- No unofficial scraping of OU services or storage of OU credentials.

## Immediate technical priorities (before a real OU pilot)

1. Review the publicly listed demo and **disable real/private schedule entry** until multi-user isolation, proper auth and risk review exist. Public demo must clearly warn users it is synthetic only.
2. Rotate any previously exposed Gemini/AI Studio credentials; search repository and history, revoke old keys and verify secrets protections.
3. Establish green CI, reproducible dependencies and independent security/dependency review; do not claim tests are passing unless a current run confirms it.
4. Produce a threat model, data map and accessibility audit; keep zero-LLM fallback.
5. Implement authorized user accounts, secure multi-user persistence and approved data handling **before** real student/employee onboarding.
6. Obtain institutional decisions before adding OAuth, SSO, Moodle, MySAIL, email or official OU branding.

## Review checklist for OU INC introductory discussion

- What specific student-success problem warrants exploration?
- Which internal OU department could sponsor a pilot?
- Could a synthetic-data demonstration proceed without university private data?
- Who handles product/IP/licensing guidance, UTS intake and accessibility review?
- Which KIN activities are feasible for the founders under their current student/visa status? Refer individual questions to appropriate OU and qualified legal advisers.
- What support, budget and procurement pathway might be realistic **if** evidence warrants it?

**No HECVAT, SOC 2 Type II, VPAT, FERPA certification, security clearance, OU endorsement or contract is asserted here.**
