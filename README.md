# vox

Local Wispr Flow replacement: [VoiceInk](https://github.com/Beingpax/VoiceInk) (built from source) for speech-to-text, Ollama for Cleanup and Titles, one script (`bin/vox.py`) for the parts VoiceInk can't do. Terms are defined in `GLOSSARY.md`; the reasoning is in `docs/adr/0001-voiceink-with-script-hooks.md`.

- **Insert**: press the hotkey, speak, and the Clean text is pasted into the focused field.
- **Capture**: press the Capture hotkey and you get `~/vox/<ts>-<title>.md`.
- Every Dictation's raw Transcript is also saved to `~/vox/raw/<ts>.md`.

## Setup

1. Install the cleanup model: `ollama pull gemma3:4b`
2. Configure: `cp .env.example .env` (Capture folder, models). `VOX_LLM=anthropic` switches Cleanup and Titles from local Ollama to Claude (default `claude-haiku-5-5`) and needs `ANTHROPIC_API_KEY`. Speech-to-text stays local either way. Requires `uv`, which provides Python and the `anthropic` SDK for `bin/vox.py`.
3. Build VoiceInk: `scripts/build-voiceink.sh` (installs to `/Applications` and restarts VoiceInk)
4. Run the self-check: `bin/vox.py selftest`

## VoiceInk setup

Do it in this order: the prompt and the Local CLI command must exist before a mode can select them.

### 1. Speech model

Download **Whisper Large v3 Turbo (Quantized)** (`ggml-large-v3-turbo-q5_0`). Onboarding only offers Parakeet v3, so download Whisper from the model library afterwards.

### 2. Local CLI command (global)

In the AI provider settings, select **Local CLI** and set its **Command** to:

```
~/code/vox/bin/vox.py clean
```

VoiceInk runs it via `zsh -lc`, so `~` and your login `PATH` (for `uv`) work. It must finish within 45 s; `vox.py` gives up on the LLM after 35 s and returns the raw text.

### 3. Prompt "Rewrite"

Create a prompt (the **+** next to the Prompt picker) titled **Rewrite**, with **"Use system instructions" off**, and this text:

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

Keep system instructions off: VoiceInk's built-in system prompt says "Use the same language as <TRANSCRIPT>", and with it gemma3:4b and qwen3:4b both translate mixed German/English into one language. With this prompt alone, neither does (about 0.5 s per Dictation).

### 4. Modes

The speech model, language, prompt and output are set **per mode**.

| Setting           | **Dictation** (default mode)       | **Capture** (new mode)                                  |
| ----------------- | ---------------------------------- | ------------------------------------------------------- |
| Hotkey            | your Insert hotkey                 | its own hotkey                                          |
| Transcription     | Large v3 Turbo (Quantized)         | Large v3 Turbo (Quantized)                              |
| Language          | Auto-detect                        | Auto-detect                                             |
| AI Enhancement    | on                                 | on                                                      |
| AI Provider       | Local CLI                          | Local CLI                                               |
| Prompt            | **Rewrite**                        | **Rewrite**                                             |
| Output            | Paste                              | Custom command: `~/code/vox/bin/vox.py capture`         |

Press **Save** in each mode. The form pre-fills the first prompt in the picker **without saving it**, and VoiceInk silently skips enhancement when a mode has no saved prompt (`AIEnhancementService.isConfigured`): no raw file, and Capture writes `cleanup: unknown`. If that happens, pick a different prompt, pick Rewrite again and Save.

### 5. Recording shortcut (global)

Activation mode **Hybrid** (tap toggles, hold talks). It applies to every mode's hotkey.

### Notes

- Every mode must use the Local CLI provider, otherwise its raw Transcript is not saved.
- The Capture command only gets the final text (`VOICEINK_TRANSCRIPT`) and is killed after 10 s, so the Title runs detached in the background.
- To check what a Dictation actually sent to the model, the history is in `~/Library/Application Support/com.prakashjoshipax.VoiceInk/default.store` (`ZTRANSCRIPTION`: `ZTEXT`, `ZENHANCEDTEXT`, `ZPROMPTNAME`, `ZAIREQUESTSYSTEMMESSAGE`).

## Failure behaviour

- **Ollama down or slow (>35 s):** the raw Transcript is pasted or saved instead. The Capture file shows `cleanup: failed` and a notification appears.
- **Title fails:** the file stays `<ts>-untitled.md` with `title_error` in its header, and a notification appears.
- **`bin/vox.py` fails to start at all** (e.g. `uv` missing): the raw dump is skipped. VoiceInk's own history in `~/Library/Application Support/com.prakashjoshipax.VoiceInk/` still has the Dictation.
- **After a rebuild:** macOS may ask for Accessibility and Microphone permission again, because local builds are signed only on this machine.
