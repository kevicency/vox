repo-type: config

# vox

Local dictation setup: VoiceInk + Ollama + `bin/vox.py` hooks. Read `README.md` for wiring, `GLOSSARY.md` for terms, `docs/adr/` for decisions.

- `bin/vox.py` runs from VoiceInk via `zsh -lc` as a `uv run --script` (inline deps: `anthropic` only). Keep everything else stdlib.
- Check: `bin/vox.py selftest`.
- VoiceInk source lives in `~/code/VoiceInk` (GPL, not vendored here).
