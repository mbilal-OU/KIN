# KIN | Ideas, Tasks & Roadmap

> **Life changes. KIN moves with you.**

This is the central record of ideas, requested modifications, development tasks, bugs, research, decisions and completed work for KIN. The source of truth is **GitHub Issues and pull requests**, not a temporary chat or private to-do list.

## Current product direction — OU first (12 November 2026)

Our first institutional target is **Oakland University**: pursue an authorized, optional **KIN OU Companion**, initially for students, with a later path to faculty and staff. The first proposed experience is a verified, source-linked **OU Daily Briefing** with scheduling/conflict explanations and user-approved changes.

This remains an independent project. OU's availability of the Gemini *chat app* does not imply KIN has access to OU-funded Gemini APIs or permission to process OU Confidential/Internal data. Any real OU pilot requires the proper approvals; the current guest prototype is fictional-data only.

Review: [OU-first product strategy](OU_FIRST_STRATEGY.md), [OU pilot](OU_PILOT_PLAN.md), [OU Gemini architecture](OU_GEMINI_DECISION.md), [Institutional readiness](OU_INSTITUTIONAL_READINESS.md).

**Issue tracking:** Avoid duplicate tickets: [#19](https://github.com/mbilal-OU/KIN/issues/19) already tracks OU pilot evidence, [#21](https://github.com/mbilal-OU/KIN/issues/21) tracks Gemini evaluation, and [#14–18](https://github.com/mbilal-OU/KIN/issues/14) cover identity, storage and possible integrations. Track new gaps only after checking existing work.

**Feature audit:** Old issue descriptions and the original hackathon roadmap are historical; they are not a current shipped-feature matrix. Consult the latest README, source and tests for implemented behavior. Working guest-only features are **not** proof of secure enterprise readiness.

## Quick links

- [All issues](https://github.com/mbilal-OU/KIN/issues)
- [Open tasks](https://github.com/mbilal-OU/KIN/issues?q=is%3Aissue+is%3Aopen)
- [Completed / closed issues](https://github.com/mbilal-OU/KIN/issues?q=is%3Aissue+is%3Aclosed)
- [Create a new issue](https://github.com/mbilal-OU/KIN/issues/new/choose)
- [Roadmap](ROADMAP.md)
- [Pull requests](https://github.com/mbilal-OU/KIN/pulls)

## How to record an idea or change

1. Open **New issue** and select **Feature / Idea**, **Modification / Suggestion**, or **Bug report**. For research or decisions, use a blank issue.
2. State the problem, who benefits, proposed behavior, priority and how we will know it is done. Attach screenshots only after removing personal information.
3. Use a title prefix: `[Idea]`, `[Feature]`, `[Improvement]`, `[Bug]`, `[Security]`, `[Integration]`, or `[Research]`. Include `[P0]`, `[P1]` or `[P2]` when triaged.
4. Discuss tradeoffs in issue comments. Link design notes, decisions, relevant code and related issues.
5. Link the implementing pull request to the issue, for example `Closes #11`. Close only when acceptance criteria are met; otherwise document why it was deferred.
6. Reopen the issue or create a follow-up if a completed feature needs improvement. The discussion history remains available.

## Workflow (GitHub Issues)

| Status | Meaning | How we record it |
|---|---|---|
| **Ideas** | Not yet scoped or approved | Open issue titled `[Idea]` or `[Research]` |
| **To Do** | Scoped, accepted, not started | Open issue with acceptance criteria and `**Status:** To Do` |
| **In Progress** | Someone is implementing it | Assign an owner, link a branch/PR, and add a status comment |
| **Blocked** | Waiting on a dependency or external permission | Open issue with a `Blocked on` note and next action |
| **Completed** | Implemented, tested and documented | Close issue and link merged PR / release |
| **Deferred** | Not planned for current release | Explain decision in issue; close as not planned when appropriate |

A GitHub Projects kanban board can later visualize these states, but **the issue tracker works immediately without a Projects board**. No Projects board is claimed to exist yet.

## Priority definitions

- **P0 — Foundation:** Core trust, private data handling, schedule integrity and safe conflict resolution.
- **P1 — Next:** Voice, time tools, authentication, storage design and pilot validation.
- **P2 — Later / dependent:** Mobile product decisions and OU integrations requiring university approval.

Priority is not a commitment or delivery date. Record an owner and estimate only after review.

## Minimum fields for each issue

- **Type:** Idea, feature, modification, bug, research, security, integration.
- **Problem / user value:** Why it matters.
- **Desired behavior:** What KIN should do.
- **Privacy and security:** What data is used, stored or sent to AI services.
- **Dependencies:** Including OU approval or external services.
- **Acceptance criteria:** Testable checklist.
- **Priority / status / owner:** Update as work proceeds.
- **Decision log:** Important choices and reasons in comments.
- **Evidence:** Screenshots (redacted), tests, demo, linked PR and outcome.

## Safety and honest product claims

- The **current hackathon prototype** already includes basic scheduling, deterministic conflict detection, weather context, Gemma explanations, SQLite storage and .ics import/export.
- **Proposed features** such as automatic resolution suggestions, voice interaction, alarms, secure accounts and production-grade privacy controls must not be described as shipped.
- OU email, calendar, MySAIL or Moodle access requires official technical feasibility, authorization, student consent and security review. Do not collect OU passwords or scrape restricted systems.
- Keep real student schedules, private voice transcripts, secrets, access tokens and identifying information **out of this public repository and public issues**.
- KIN must not claim that OU has canceled classes unless verified through an official announcement.

## First backlog

See [ROADMAP.md](ROADMAP.md) for links to the initial twelve tracked issues and their proposed phases.

## Future board setup

If the team wants drag-and-drop cards, create a GitHub **Projects** board manually from the repository or GitHub profile and add the existing issues. Suggested columns: Ideas, To Do, In Progress, Blocked, Completed. A Projects board is optional; issue comments, linked PRs and issue closure already preserve the permanent record.
