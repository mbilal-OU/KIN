# KIN App — Navigation & Interface Specification v0.1
**Status:** Implementation handoff for the Hacktoberfest student prototype; not a claim that screens exist.

## Product experience
Within five seconds of opening KIN, the student should see: **what's next**, **what might affect it**, and **what to do next**. Two end-to-end workflows are essential: (a) an NWS weather warning affecting an illustrative commute/exam, and (b) a verified OU event proposed for a free time slot.

Keep the app brand KIN — Kinetic Intelligence Network; assistant nickname is independently user-editable. Tagline: *Life changes. KIN moves with you.*

## IA / Navigation
| Destination | Primary question | Contents | Main action |
| --- | --- | --- | --- |
| Today | What matters now? | next commitment, daily briefing, important sourced changes, 1 suggested opportunity | Review impact or action |
| Schedule | When am I free? | agenda with classes, exams, work, saved events, buffer rules | Add/approve commitment |
| Discover | What could I enjoy? | official OU sporting events, esports/gaming, campus activities, interest filters | Check availability, then propose |
| KIN AI | What does this mean for me? | structured grounded explanations and natural-language event extraction | Submit question or approve extracted proposal |
| Settings | What can KIN access? | assistant name, workspace labels, sample commute location, notification preference, theme, privacy | Change settings |

**Approvals** is a cross-cutting action center, reached from proposed actions and header icon. For the existing Streamlit MVP, keeping a visible Approvals tab is acceptable to minimize code churn. On mobile, a five-item bottom nav is a future target, not a requirement for today's demo.

## Home screen layout
1. Header: KIN wordmark; user/guest indicator; review actions/notifications icon.
2. Greeting: “Here's what matters today.” Avoid over-personal or anxiety-inducing phrasing.
3. **Next Up** card: event name, 9:00 AM style time, fictional/real provenance if applicable, location, chosen buffer.
4. **Changes that matter** card: official data source, last checked timestamp, possible time conflict, severity. Badges/text: VERIFIED NWS, SIMULATED, STALE, or UNAVAILABLE. Never “OU is closed” unless explicitly verified against a real university announcement.
5. **Recommended next step**: single clear action, e.g., “Check official OU closing information” or “Review options”.
6. **Make room for life** card: one OU event matching a free slot; direct official event link; propose saving.
7. Bottom of page: explicit privacy note and accessible source history.

## Schedule screen
- Default agenda view with each event showing title, start/end, category, optional source.
- Exam, study meeting, work shift, family commitment, OU activity all use the same event model.
- For the hackathon: fake events and session state. Do not claim a real academic or personal calendar sync.
- Student adds events via form or uses Gemma to extract a **proposal** from natural-language fictional text.
- Validate time zone and end > start; show overlap warnings; require approval before insertion.
- For events with estimated end time, display "End time estimated."

## Weather / Ripple view
- Show actual NWS data only where fetched successfully; show source + retrieval time.
- Demonstration warning must say "SIMULATION" next to its headline and explanation, and must never be mixed into an actual alert counter.
- Example flow: fictional exam -> commute planning buffer -> source alert time overlap -> grounded explanation -> official OU closing link.
- No unsupported road-safety, class cancellation, or precise commute-duration claims.
- On failure display “Unable to verify current alerts” not “All clear.”

## Discover / Opportunity Radar
- Categories: OU sports, esports & gaming, student events, clubs.
- Card: title, verified start, venue, official source URL, source checked date, event status, time-overlap result, estimated duration disclosure.
- Filters: category and interests; later favorite teams, price, accessible needs, location.
- Click **Check my schedule** -> deterministic overlap assessment -> **Propose add** -> user approval -> session calendar insertion -> verified receipt.
- If event overlaps, explain the conflict and let user decide; no autonomous rescheduling.

## KIN AI view
- Show assistant nickname, and an explicit legend: verified information / AI explanation / unavailable.
- Accept natural-language student requests; Gemma extracts structured date/time proposals; deterministic code validates before offering Save.
- For grounded briefings: Situation, Confirmed, Uncertain, Suggested next steps.
- Model failure shows a labeled non-AI fallback.
- Do not present ordinary deterministic text as model output.

## Approval center / activity history
States: Proposed -> Approved -> Executing -> Verified, or Rejected / Failed.
- Proposal summary names exact item and destination (in-memory demo calendar).
- Separate Approve and Cancel controls; neither is implicit.
- On success, visibly update agenda and action log.
- On failure, show error and avoid “completed” label.

## Guest onboarding
- Three steps max: choose nickname (optional), approximate commute area (optional), use fictional sample schedule.
- No OU email/password; never ask real users to paste real private course records into third-party model on free-tier demo.
- Allow users to start with no name.

## Themes & accessibility
| Token | Hex | Role |
| --- | --- | --- |
| Navy | #14263B | primary brand |
| Teal | #38BFA8 | active/affirmative accents |
| Mist | #F3F7F6 | soft light background |
| Slate | #667987 | secondary UI |
| Amber | #E6A54B | caution accent |

- Inter with system sans fallback; body >= 16px when possible; visible keyboard focus and reduced motion.
- Contrast test all text / backgrounds. Do not encode warnings solely by color.
- Layout: single-column mobile, sidebar + wide content on desktop.
- Use calm icons for calendar, alert, campus, activity, approval; no emergency sirens or animated panic.
- Never add decorative fake weather forecasts or unverified real event times.

## Suggested component tree (logical structure; adapt to existing Python/Streamlit app)
```
KINApp
  BrandHeader
  TodayPage
    Greeting
    NextCommitmentCard
    SourceAwareImpactCard
    NextActionCard
    OpportunityCard
  SchedulePage
    EventAgenda
    EventForm
    AIExtractionProposal
  WeatherPanel
    NWSStatus
    WarningImpactList
    SourceList
  DiscoverPage
    InterestFilter
    OfficialEventCard
    TimeConflictSummary
  KINAssistantPanel
    MessageInput
    EvidenceSummary
    ActionProposal
  ApprovalCenter
    PendingProposal
    ActionHistory
  SettingsPanel
    AssistantAlias
    LocationPreferences
    PrivacyDisclosure
```

## End-to-end demo sequence (90 seconds)
1. Today: show fictional student exam & assistant nickname.
2. AI: paste fictional language describing a commitment; use real Gemma inference, then approve.
3. Weather: show a clearly simulated overlap with the sample commute; cite NWS for live information and official OU closing URL for university status.
4. Discover: inspect a source-linked OU event, check conflicts, propose adding it.
5. Approvals: click Approve; show agenda update and confirmed local action history.

## Acceptance checks
- First viewport displays next commitment and meaningful update.
- Every primary action has a meaningful result or clearly marked disabled state.
- Sample events and simulation labels are visible without opening menus.
- Error conditions distinguish unavailable source from no current warnings.
- Approve is required to modify the sample calendar.
- Users can rename assistant without renaming KIN.
- No source-less academic cancellation assertion.
- Test at narrow and wide viewport, keyboard navigation, and contrast.
- Do not rewrite tested Python logic just to apply the UI.

## Priority order
**P0 (demo):** clear Today view, weather-source and simulation labels, Gemma proposal/approval, Discover event/approval, functional run.
**P1:** typography & tokens, consistent icons/cards, user nickname customization, source timestamps.
**P2:** dark mode, richer responsive nav, real calendar connectors, new workspaces.
