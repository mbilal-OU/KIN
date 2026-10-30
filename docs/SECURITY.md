# Security and privacy

## Credentials

- The API key lives only in `.env`, which is git-ignored.
- `.env.example` contains a placeholder and is the only version committed.
- `provider_status()` reports *whether* a key is configured and never returns
  its value. A test asserts the secret cannot appear in its output.
- The key is never placed in a prompt, log line, screenshot, or UI element.
- The literal `replace_with_your_own_key` is treated as unconfigured.

**A key was exposed during development of this project. Treat it as
compromised: revoke it at <https://aistudio.google.com/apikey> and issue a
replacement.** Rotating is the only remedy — a leaked key cannot be un-leaked.

### Verifying before you push

```bash
git status
git diff --cached --stat
git ls-files | grep -E '\.env$|\.db$'      # must print nothing
grep -rn "AQ\.\|AIza" --include=*.py --include=*.md . | grep -v example
```

## Prompt injection

External text — event titles, notes, `.ics` descriptions, user input — is
untrusted data. Defenses:

1. The system rule precedes the data and states that the data is not
   instructions.
2. User text is `json.dumps`-quoted, so it cannot break out of its slot.
3. The model has **no tools**. There is no code path from a model response to a
   database write.
4. Extraction output must pass `validate_event_proposal` regardless of what the
   text claimed.
5. Nothing is stored without a human click.

`test_ai.py` covers an injection attempt that tries to assert a university
closure and insert an event: the proposal is refused at validation, so nothing
reaches the calendar.

## Data handling

| Concern | Position |
|---|---|
| What is stored | Commitments, preferences, workspaces, action log, notifications — in a local SQLite file |
| Where | `kin_local.db` beside the code, git-ignored, overridable via `KIN_DB_PATH` |
| Encryption | None. A local file with filesystem permissions only |
| Export | One click, full JSON, on Settings → Your data |
| Erasure | One click, all tables, behind a confirmation checkbox |
| Sent to the AI provider | Commitment titles, types and times, plus weather status. Revocable with one checkbox, which reduces the payload to counts |
| Never sent | API keys, the user's name unless they typed one, addresses, coordinates beyond the approximate city they chose |
| Analytics | Disabled (`gatherUsageStats = false`) |

Only approximate city-level coordinates are sent to the NWS, from a fixed list.
KIN never requests device location.

## Input validation

- Datetimes must be ISO 8601 with an explicit offset; naive values are rejected.
- Buffers are bounded 0–180 minutes.
- Titles are 3–100 characters.
- Durations must be positive and under 24 hours.
- Extraction input is 10–1,200 characters, checked *before* any model call.
- Questions are 3–500 characters.
- All SQL uses parameterized queries. No string interpolation of user values.
- `update_workspace` allow-lists column names.
- All user-supplied text rendered through the HTML helpers is escaped with
  `html.escape`.

## Error handling

Exceptions are caught at the UI boundary and shown as the exception *type* plus
message, never a raw traceback. Network failures are classified (`timeout`,
`network`, `http_503`) so the user learns what went wrong without internals
leaking.

## What KIN deliberately does not claim

- Not FERPA, SOC 2, HIPAA, GDPR or WCAG **certified**. WCAG 2.2 AA is a design
  target that has not been formally audited.
- Not affiliated with, endorsed by, or operated by Oakland University.
- Not an emergency notification system.
- No road-safety or travel-time prediction.
- No Moodle, MySAIL, or university account access.
- No push, SMS or email delivery — in-app messages only.
- Guest mode means **no account**, not anonymity.

## If this were deployed for real users

Current local-only storage would be insufficient. Required first:
authenticated identities, per-tenant isolation, encryption at rest and in
transit, session security, secret management outside `.env`, audit logging,
rate limiting, dependency scanning, and an incident-response plan. Shared or
family features must not ship before invitation-based permissions exist.
