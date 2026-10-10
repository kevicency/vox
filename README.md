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
| Default mode (**Insert**)                | enhancement on, **a prompt selected**, Local CLI, output Paste                                                    |
| New mode **Capture**                     | own hotkey, enhancement on, prompt selected, Local CLI, output Custom command `~/code/vox/bin/vox.py capture` |

Notes:

- Every mode must use the Local CLI provider, otherwise its raw Transcript is not saved.
- The hotkey mode (toggle / hold / hybrid) is global in VoiceInk, so the Capture hotkey is Hybrid too. A tap still toggles.
- The enhancement prompt is VoiceInk's, so edit it in VoiceInk. Use a custom prompt with **"Use system instructions" off**: VoiceInk's built-in system prompt says "Use the same language as <TRANSCRIPT>", which makes small models translate mixed German/English into one language. This prompt keeps gemma3:4b from translating and removes fillers (about 0.5 s):

  ```
  You clean up dictated text that mixes German and English.
  - Keep every word in the language it was spoken. Mixed German/English is intentional. Never translate a single word.
  - Remove filler words (ähm, äh, öh, um, uh) and stutters.
  - Fix punctuation and capitalization only.
  - Output only the cleaned text, nothing else.

  Example:
  Input: So, ähm, ich hab das Feature, äh, deployed and it works.
  Output: So, ich hab das Feature deployed and it works.
  ```
- VoiceInk silently skips enhancement when a mode has no prompt saved (`AIEnhancementService.isConfigured`): no raw file, and the Capture header says `cleanup: unknown`. The mode form pre-fills the first prompt without saving it, so re-pick the prompt and press Save.

## Failure behaviour

- **Ollama down or slow (>35 s):** the raw Transcript is pasted or saved instead. The Capture file shows `cleanup: failed` and a notification appears.
- **Title fails:** the file stays `<ts>-untitled.md` with `title_error` in its header, and a notification appears.
- **`bin/vox.py` fails to start at all** (e.g. `uv` missing): the raw dump is skipped. VoiceInk's own history in `~/Library/Application Support/com.prakashjoshipax.VoiceInk/` still has the Dictation.
- **After a rebuild:** macOS may ask for Accessibility and Microphone permission again, because local builds are signed only on this machine.
