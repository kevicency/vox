# VoiceInk as the base, extended only through its script hooks

We build on VoiceInk (built from source) instead of writing our own dictation app or forking one. Insert and Capture are two VoiceInk Modes with separate hotkeys. All custom behaviour lives in two shell scripts that VoiceInk calls. The cleanup script is wired in as VoiceInk's "Local CLI" enhancement provider rather than its built-in Ollama provider, because that is the only point where the raw Transcript is reachable: the script saves it to `raw/`, then calls Ollama itself. Capture uses a Mode whose output is a custom command, which writes the file immediately and fills in the Title in the background, because VoiceInk kills custom commands after 10 s.

## Considered Options

- **Handy** (MIT, most active): can only paste, so Capture would need a fork or a poller on its SQLite history.
- **OpenWhispr**: has a single dictation hotkey slot, no post-transcription hook, and stores notes only in SQLite.
- **FreeFlow**: has no local speech-to-text and no hooks.

## Consequences

- Every Mode must use the Local CLI cleanup, otherwise its raw Transcript is not saved.
- Each rebuild may make macOS ask again for Accessibility and Microphone permission.
- Upstream does not accept PRs, so changes we need beyond these hooks mean forking.
