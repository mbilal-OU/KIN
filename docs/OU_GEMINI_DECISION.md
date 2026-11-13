# Gemini, Gemma and KIN: OU-first AI architecture decision

**Status:** Architecture proposal / research decision, **not** an approved OU Gemini integration.  
**Updated:** 12 November 2026

## Verified facts and critical distinction

1. **OU offers Google Gemini as a tool.** OU's [AI@OU resources](https://oakland.edu/ai/general-resources/) state that OU Google accounts can access the **free Gemini app**, and separately describe NotebookLM and other platforms.
2. **KIN currently uses Gemma 4** (an open-weight model) **through the Gemini API**, not a Gemini-branded model. KIN also supports a local Ollama model and a fully deterministic AI-off mode. See [README](../README.md) and [integrations](INTEGRATIONS.md).
3. **Gemini chat entitlement is not API entitlement.** OU Gemini access does **not** establish paid/enterprise model licensing, programmatic API access, Google Cloud project permissions, quotas, billing, data-processing terms, or permission to share OU data with KIN.
4. **No claim of OU authorization:** KIN is independent. Do not suggest OU Gemini automatically secures KIN or that KIN is a university-supported app.

## Product stance

**KIN = verified OU-workflow layer + deterministic decision engine + optional LLM.**

- Models classify/explain **minimized, permitted** data; they are not the source of institutional truth.
- Source adapters provide explicit provenance, freshness, availability, source URLs and OU policy caveats.
- Rule engines calculate time conflicts and permitted alternative slots.
- An approval service gates changes; authorized writes are auditable and verified.
- AI-off mode remains valuable for campus pilots, procurement evaluation and model outages.
- No unapproved sensitive university data to **any** third-party model, including a personally obtained Gemini API key.

## Proposed provider matrix

| Path | Present state | Usage gate |
|---|---|---|
| Deterministic / off | Implemented | Default option for demo; no hosted model requests |
| Gemma 4 via Gemini API | Implemented as opt-in | Only synthetic/non-sensitive content in current demo; user-controlled key and privacy setting |
| Local Gemma via Ollama | Implemented optional | Suitable hardware and local operational controls |
| Gemini *model* via API | **Not implemented** | Verified API availability, OU UTS security/data approval for any OU use, data processing terms, billing, support and tests |
| OU Google Workspace/Gemini account identity | **Not integrated** | Written authorization, supported auth protocols and scoped enterprise accounts; no browser-session or credential scraping |

Gemma is **not** Gemini. The Gemini API is a transport/interface that can provide access to different model families. A switch from Gemma to Gemini requires a model choice, code/tests, a cost and privacy review, and separate contractual permission where applicable.

## Recommended architecture (future)

```text
[Streamlit MVP / future accessible clients]
              |
[Profile + workspaces + per-source consent]
              |
[OU source adapters] ----> [Source provenance + freshness]
              |                         |
              +---------------> [Deterministic KIN rules]
                                      |
                             [Bounded explanation context]
                                      |
                 +--------------------+--------------------+
                 |                    |                    |
             [AI OFF]           [Local model]      [Approved cloud model]
                 |                    |                    |
                 +--------------------+--------------------+
                                      |
                           [Validated proposal / citation]
                                      |
                             [Human review and approval]
                                      |
                          [Authorized write + verification]
```

**OU-specific trust boundary:** authenticated identity and role claims must originate from an approved OU identity/SSO process (if approved), not from the LLM, the email domain alone, or user-provided text.

## Decision gates before implementation

- [ ] Written confirmation from UTS of allowed model/API deployment architecture, billing owner and data classes.
- [ ] Model/API costs and quotas measured using **synthetic** test schedules; graceful fallback tested.
- [ ] Approved data processing terms, retention and training/use policies for selected services reviewed.
- [ ] User consent and a *server-enforced* egress policy by data classification, not UI checkbox alone.
- [ ] Prompt injection, malicious source text, fabricated citations and false closing notices tested.
- [ ] Model cannot bypass deterministic rules, role checks or explicit approval.
- [ ] Accessibility and reliability tested for the no-AI fallback and the AI experience.
- [ ] Provider/model changes go through regression and any required institutional re-review.

## Questions for OU INC / UTS

1. Does OU provide **Gemini chat** only, or is there an approved Google Cloud/Gemini API program for institutional application development?
2. Which institution-approved account, project, billing and security model would apply?
3. Which OU data classifications may be processed by the selected model, and under what contract?
4. Can KIN serve a consented voluntary pilot before private university integrations?
5. Can UTS recommend a pathway for vendor review, architecture and accessibility?

## Official sources

- [OU AI tools](https://oakland.edu/ai/general-resources/)
- [OU Policy #820](https://www.oakland.edu/policies/information-technology/820/)
- [OU AI usage guidelines](https://support.oakland.edu/TDClient/33/Support-Center/KB/PrintArticle?ID=757)
- [OU Google Workspace](https://www.oakland.edu/uts/services/g-suite/)
- [OU IT procurement](https://support.oakland.edu/TDClient/33/Support-Center/KB/Article/140/IT-Procurement-and-Sourcing-Needs)

**Decision at this stage:** Maintain Gemma/local/off options, investigate Gemini-model integration rather than promising it, and prioritize safe OU-specific workflows over model branding.
