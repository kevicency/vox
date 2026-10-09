# vox

Local Wispr Flow replacement: [VoiceInk](https://github.com/Beingpax/VoiceInk) (built from source) for speech-to-text, Ollama for Cleanup and Titles, one script (`bin/vox.py`) for the parts VoiceInk can't do. Terms are defined in `GLOSSARY.md`; the reasoning is in `docs/adr/0001-voiceink-with-script-hooks.md`.

- **Insert**: press the hotkey, speak, and the Clean text is pasted into the focused field.
- **Capture**: press the Capture hotkey and you get `~/vox/<ts>-<title>.md`.
- Every Dictation's raw Transcript is also saved to `~/vox/raw/<ts>.md`.

## Setup

1. Install the cleanup model: `ollama pull gemma3:4b`
2. Configure: `cp .env.example .env` (Capture folder, models). `VOX_LLM=anthropic` switches Cleanup and Titles from local Ollama to Claude (default `claude-haiku-5-5`) and needs `ANTHROPIC_API_KEY`. Speech-to-text stays local either way. Requires `uv`, which provides Python and the `anthropic` SDK for `bin/vox.py`.
3. Build VoiceInk: `scripts/build-voiceink.sh`, then `mv ~/Downloads/VoiceInk.app /Applications/`
4. Run the self-check: `bin/vox.py selftest`

## VoiceInk settings

| Where                                    | Setting                                                                                               |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Speech model                             | Whisper large-v3-turbo, language auto-detect                                                          |
| Recording shortcut                       | your Insert hotkey, mode **Hybrid** (tap toggles, hold talks)                                         |
| AI provider → Local CLI → custom command | `~/code/vox/bin/vox.py clean`                                                                         |
| Default mode (**Insert**)                | enhancement on, provider Local CLI, output Paste                                                      |
| New mode **Capture**                     | own hotkey, enhancement on, provider Local CLI, output Custom command `~/code/vox/bin/vox.py capture` |

Notes:

- Every mode must use the Local CLI provider, otherwise its raw Transcript is not saved.
- The hotkey mode (toggle / hold / hybrid) is global in VoiceInk, so the Capture hotkey is Hybrid too. A tap still toggles.
- The enhancement prompt is VoiceInk's, so edit it in VoiceInk. Small models tend to translate mixed German/English, so add to the prompt: _"Keep every word in the language it was spoken. Never translate. Output only the cleaned text."_

## Failure behaviour

- **Ollama down or slow (>35 s):** the raw Transcript is pasted or saved instead. The Capture file shows `cleanup: failed` and a notification appears.
- **Title fails:** the file stays `<ts>-untitled.md` with `title_error` in its header, and a notification appears.
- **After a rebuild:** macOS may ask for Accessibility and Microphone permission again, because local builds are signed only on this machine.
