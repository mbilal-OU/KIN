# KIN Campus Edition — OU-Inspired Design Handoff

> Independent student-built hackathon prototype; **not an official Oakland University product**. KIN stands for **Kinetic Intelligence Network**. Tagline: **Life changes. KIN moves with you.**

## Research-based theme choice

Oakland University's official core palette is gold (#BC945B), black (#000000), and white (#FFFFFF). Its published expanded gold family includes #877148. Sources:
- https://www.oakland.edu/brand/design-with-purpose/
- https://www.oakland.edu/ucm/merchandising/

**Do not reproduce official Golden Grizzlies mascot art, interlocking OU mark, or university seal** without permission. University trademark rules restrict these marks. Brand KIN with an original connected-path icon; mention OU and Golden Grizzlies only descriptively for verified campus context. Do not imply affiliation or endorsement.

## Tokens

| Purpose | Hex |
| --- | --- |
| Primary identity / dark | #000000 |
| OU-inspired primary gold | #BC945B |
| Deep gold | #877148 |
| White | #FFFFFF |
| KIN warm neutral background (not an official OU color) | #F7F5F0 |
| KIN ink for light background | #202020 |
| KIN dark surface | #191919 |
| KIN warning tint | #FFF0CE |

Use white/black legible body text; gold as accent/controls, not low-contrast small text. Test foreground/background combinations to WCAG 2.2 AA. Other status colors must have accompanying icons/text. Use Inter or system sans; do not copy OU's licensed official fonts unless properly licensed.

## Mobile information architecture

Five major destinations: **Today**, **Schedule**, **Discover**, **KIN AI**, **Settings**. Approval center is reachable from action cards/header; for hackathon retain existing separate Approval tab if easier.

**Today**
1. Greeting: “Here's what matters today.”
2. Next up: event title, time, location, source/synthetic label.
3. Possible disruption: sourced NWS data with check timestamp, or **SIMULATION** with prominent fake-data notice. Never imply OU canceled classes without verified institutional decision.
4. One recommended action: “Review possible impact” / “Check official campus updates”.
5. Opportunity card: verified, source-linked campus event with time compatibility.
6. Minimal footer: “Independent student-built prototype; not affiliated with OU.”

**Schedule**
- Single agenda of exam, class, work, study, and optional leisure commitments.
- Natural-language Gemma 4 extraction -> structured preview -> time-zone validation -> approval -> local save with confirmation.
- Visually distinguish tentative plans and estimated event end times.

**Discover**
- “For You”, “Golden Grizzlies sports”, “Gaming & esports”, “Campus activities”.
- Event tiles need official source URL, verified start, venue, status, possible schedule conflict, and **Review to add**.
- Do not present event admission, tickets, current game status, or live data as verified when not checked.

**KIN AI**
- Assistant nickname customizable.
- Show answer sections: Situation, Confirmed, Uncertain, Options.
- Weather-alert source status and simulated status clear.
- An actual model invocation label, or explicit non-AI fallback. Never present canned text as live model response.

**Settings**
- Assistant nickname distinct from KIN company/app brand.
- Approximate commute location and user-defined preparation buffer.
- Interest preferences, privacy descriptions.
- Later: dark mode, contextual aliases, organization connections.

## Ten benchmarks and exactly 3 lessons for each

These are **ten relevant references, not a statistically justified 'world top 10' ranking**.

1. **Google Calendar** — calendar/task aggregation; distinct work/personal calendars; one-step event entry. https://workspace.google.com/products/calendar/
2. **Todoist** — daily priority ordering; time blocks; low-clutter Today view. https://www.todoist.com/help/todoist/get-started/plan-your-day-with-the-today-view-UVUXaiSs
3. **Notion Calendar** — link dated records to context; independent workspace connections; detailed info behind minimal views. https://www.notion.com/en-us/help/use-notion-calendar-with-notion
4. **Motion** — account for duration and deadlines; respond to changes; show proposed impact rather than auto-move consequences. https://www.usemotion.com/help/time-management/auto-scheduling
5. **Reclaim** — protect recurring routines; distinguish fixed tasks from flexible focus time; preserve time for personal priorities. https://help.reclaim.ai/en/articles/11325700-habits-vs-tasks-vs-focus-time-when-to-use-each-in-reclaim
6. **Fantastical** — natural-language input; event preview; multiple distinct calendars and interest subscriptions. https://flexibits.com/fantastical
7. **Apple Weather** — clear hourly context; relevant weather alerts; multiple saved locations. https://support.apple.com/en-euro/guide/iphone/iph39ae9474a/ios
8. **Waze** — combine event time/location; context-sensitive departure nudges; explain location/permission dependencies. https://support.google.com/waze/answer/6341187
9. **ESPN** — favorite team personalization; opt-in specific notifications; find upcoming games quickly. https://plus.espn.com/app
10. **CampusGroups** — mobile campus event discovery; filter by interest; recognizable but institution-specific campus identity. https://blog.campusgroups.com/campusgroups/2022/7/20/how-to-better-engage-students-with-our-new-mobile-app

## Interaction proof: two flows

### A. Weather and exam
Fictional “9 AM exam” -> selected approximate commute area -> public NWS forecast/alerts -> deterministic time overlap with user planning buffer -> Gemma grounded explanation -> direct OU campus closing source. **Never claim official closure, safe route, or guaranteed departure time.** Simulation must be clear.

### B. Campus leisure
Verified OU athletics event -> check scheduled start time + temporary buffer -> display overlaps if any -> propose local calendar insertion -> user approves -> verify in memory + action history.

## Hackathon priority
**P0:** two complete interaction flows, actual Gemma integration, sourced data, truthful states, approvals.
**P1:** black/gold/white theme and coherent cards, custom assistant nickname, responsive sizing.
**P2:** animations, persistent accounts, deeper campus sources, automatic sports feeds and real notifications.

Avoid marketing with unsupported “life-saving” claims; promise a calmer, better-informed day.
