# Glossary

**Dictation**: one hotkey-triggered recording of speech, turned into text.

**Transcript**: the raw text the speech-to-text engine produces from a Dictation, before any Cleanup.

**Cleanup**: the local LLM pass that turns a Transcript into readable text (removes fillers, fixes punctuation) without changing meaning. Its output is the **Clean text**.

**Insert**: delivering the Clean text into the currently focused text input. Triggered by its own hotkey; hold-to-talk or tap-to-toggle.

**Capture**: delivering the Clean text as a new file in the Capture folder. Triggered by its own hotkey, usually tapped to toggle. Meant for longer brain dumps.

**Title**: a short LLM-generated summary of a Capture's content, used in its file name.

**Capture folder**: the single, user-configured folder where Capture files land.

**History**: the Transcript of every Dictation (Insert and Capture alike), kept so nothing spoken is ever lost. A Capture and its Transcript share the same timestamp; the Capture holds only Clean text.
