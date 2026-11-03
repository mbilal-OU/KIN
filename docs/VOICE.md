# KIN local voice assistant — first prototype

This is an **optional, free-first voice prototype** for natural-language questions and help resolving timetable conflicts. It does **not** require a paid AI API, OU integration, or an always-on microphone.

## What works

- Push-to-talk microphone recording within **Ask the assistant** using Streamlit's built-in recorder.
- Offline English speech-to-text through **faster-whisper**, `tiny.en` by default (optional install).
- A review step: you see and can correct the recognized words **before asking KIN**.
- Deterministic answers to basic timetable questions from your KIN workspace(s).
- Conflict assistance: KIN can identify a *flexible* KIN event and suggest non-overlapping alternative times considering your other local KIN workspaces.
- Offline, optional spoken replies via **eSpeak NG**, played as audio in the browser.

**No spoken instruction can move an event.** To change a schedule, open **Planner → Resolve conflicts**, review the current options and click an explicit approval control there. Official OU courses or employer schedules are never changed.

## Install on Ubuntu

From a checkout of this version of KIN, activate your virtual environment, then:

```bash
python3 -m pip install -r requirements-voice.txt
sudo apt update
sudo apt install -y espeak-ng
```

Set `KIN_AI_PROVIDER=off` for zero hosted AI requests. The optional speech model is selected by `KIN_VOICE_MODEL=tiny.en` or `base.en` (English), but `tiny.en` is the default and fastest option for modest hardware. **The initial speech-model download requires internet and stores model weights in the host's model cache.** Thereafter inference is local to the KIN process. No speech-to-text API key or request charge is needed, but CPU, RAM and hosting still have costs.

Open **Ask the assistant**; record a message, press **Transcribe locally**, review the words, then press **Ask KIN using local rules**. For spoken replies press **Read this answer aloud**. You can type into the review box instead if speech dependencies are unavailable.

## Essential requirement: HTTPS or localhost

Browser microphone permissions require a **secure context**: normally **HTTPS** or `localhost`. The existing historic demo URL, `http://141.210.133.171:8501/`, is **plain HTTP**, so browsers generally will not allow the mic on that address. KIN needs a correctly configured HTTPS origin before remote browser voice can be tested. This release does not deploy HTTPS or fix the server's current connection timeout.

## Privacy and safety boundaries

- The browser requests microphone permission explicitly. KIN does not listen in the background, implement a wake word, or record continuously.
- Clicking Record makes a local audio file in the browser. Streamlit uploads it to the KIN server for speech recognition. The transcript appears in the user's browser session until cleared/ended.
- A temporary WAV file exists on the server only while transcription or speech generation is running; KIN deletes it afterward. The audio widget may retain recording bytes during the open browser session.
- Voice replies come from deterministic Python rules. No hosted Gemma/Gemini inference is invoked through the new voice workflow.
- No recorded audio, audio transcript, or generated voice file is saved by the voice feature to SQLite. The separate existing **text Ask** feature can have different optional AI-provider handling.
- The voice workflow relies on only the KIN guest session's stored commitments. It does not access OU academic, email, or Moodle records. Never use private or regulated records in a public demo.
- Do **not** use this prototype for emergency warnings, medical assistance, official cancellations, guaranteed commute durations, or safety-critical reminders.

## Current limitations

English push-to-talk only, not a Siri-like full-time assistant. No wake word, offline phone-native alarms, hands-free voice approvals, mobile OS notifications, voice commands that save schedule changes, or speaker diarization. If another user has access to the same guest-mode SQLite database, this is **not** a secure multi-user product. Voice quality and processing speed vary with CPU and environment.

See [Development Hub](DEVELOPMENT_HUB.md), [Free-first guide](FREE_FIRST.md), and GitHub issue [#13](https://github.com/mbilal-OU/KIN/issues/13) for the remaining work.
