# KIN — Brand & Experience Guidelines (v0.1)

> **Working brand:** KIN — **Kinetic Intelligence Network**  
> **Primary tagline:** *Life changes. KIN moves with you.*  
> **Consumer promise:** *More than a calendar. A calmer way to live.*  
> **Status:** Design direction for review. The KIN name and slogans have not been cleared for trademark use.

## What KIN is
KIN is a privacy-first personal life-coordination assistant. It helps people understand **today's commitments**, recognize **verified changes** that might affect their plans, and discover **useful opportunities** that fit their schedules. The first prototype focuses on Oakland University students and Michigan weather, with campus sports and events as a second workflow. Future users may add work, family, or personal contexts.

KIN is **not** an emergency-alert replacement and must never imply it guarantees safety, prevents emergencies, or knows when OU cancels classes without an authoritative announcement.

## Brand voice
- **Calm:** Say “A weather alert may overlap your commute” instead of “Your day is in danger!”
- **Precise:** Separate *verified fact*, *possible impact*, *simulation*, and *unknown*.
- **Empowering:** Offer options; never imply the AI made a consequential decision for the user.
- **Brief:** Lead with what changed and why the user should care.
- **Respectful:** No guilt, pressure, compulsory streaks, or constant interruption.
- **Personalizable:** KIN is the platform name; users can choose a name for their own assistant.

## Visual identity tokens
Design palette (prototype proposal; validate WCAG contrast for every foreground/background combination):

| Token | Hex | Intended use |
| --- | --- | --- |
| Midnight Navy | `#14263B` | Wordmark, primary surfaces, body text |
| KIN Teal | `#38BFA8` | Active navigation, decorative accents, approved state |
| Mist | `#F3F7F6` | Light-mode background |
| Cool Slate | `#667987` | Secondary labels when contrast permits |
| Warm Amber | `#E6A54B` | Attention accent, not the sole warning indicator |

**Font:** Inter (with system sans fallback), subject to its applicable font license. **Shape:** rounded but restrained, generous spacing and strong hierarchy. **Icon:** simple connected paths/nodes, *not* a robot or an anthropomorphic “friend.” Use KIN alone on the app icon.

### App typography
- Display: 32–36 px / 1.15
- Section heading: 22–24 px / 1.3
- Body: 16 px / 1.5
- Caption: 14 px / 1.45
- Keep at least 44 × 44 CSS px for primary touch targets when feasible. Visible focus styles and keyboard navigation required.
- Evaluate accessible color contrast for both light/dark modes; do not use color alone to encode severity.

## Information architecture (prototype)
1. **Today** — next commitment, short briefing, relevant changes.
2. **Weather** — NWS alerts and forecasts with time/source; possible schedule impacts.
3. **Discover** — OU sports/gaming/campus activities, schedule checks.
4. **Approvals** — proposed calendar action, accept/reject, verified outcome.
5. **Settings** — assistant alias, commute buffer, permissions and source provenance.

### Cards & microcopy
**Normal day:** “Here’s what matters today.”
**Possible disruption:** “This NWS alert overlaps your selected commute window. Oakland University has not been confirmed closed.”
**Simulated demo:** “SIMULATION — fictional weather warning, not an official alert.”
**Opportunity:** “This OU event appears to fit your example schedule. Check the official event page before attending.”
**Permission:** “Review before adding. Nothing changes until you approve.”
**Failure:** “Current alert data is unavailable; KIN cannot verify active warnings right now.”

## Three UX promises
1. **Understand:** Show what matters in a single glance.
2. **Prepare:** Give source-linked context about relevant disruptions.
3. **Enjoy:** Make room for events and activities people choose.

## MVP acceptance checks
- A student can rename their companion without modifying the KIN product name.
- Example calendar events are explicitly marked as fictional.
- Weather information retains authoritative source + timestamp; API failure never displays “no warnings.”
- A hypothetical warning clearly says “SIMULATION.”
- OU events link to a verified official source; unverified end times are explicitly estimates.
- Proposed calendar changes require approval and report actual insertion status.
- Mobile UI remains readable; all essential state is understandable without color alone.
- No real student data is required for the hackathon demo.

## Near-term implementation handoff
1. Apply color tokens and text hierarchy to existing screens **without rewriting core scheduling or AI logic**.
2. Add small “verified / simulated / unavailable” labels to weather and event cards.
3. Make the top of Today show *next commitment* and *one recommended next step*.
4. Keep a visible link to source details and approval history.
5. Prefer shipping a working demo over elaborate animation.

## Assets and governance
The KIN wordmark and connected-path icon concept are **proposed** visual directions. Do not assume any generated concept board is an editable vector logo or that all pictured mockups reflect currently implemented functionality. Before production distribution, verify brand/trademark clearance, font licenses, accessible contrast, and intellectual-property ownership.
