#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["anthropic"]
# ///
"""VoiceInk hooks. See README.md for wiring.

  vox.py clean            Local CLI enhancement: saves the raw Transcript, prints the Clean text
  vox.py capture          Custom command output: writes the Capture file, titles it in the background
  vox.py title <file>     (internal) generates the Title and renames the Capture file
"""
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env():
    env = {"VOX_DIR": "~/vox", "VOX_LLM": "ollama", "VOX_OLLAMA_MODEL": "gemma3:4b",
           "VOX_CLAUDE_MODEL": "claude-haiku-5-5", "OLLAMA_URL": "http://localhost:11434", "ANTHROPIC_API_KEY": ""}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text().splitlines():
            k, sep, v = line.partition("=")
            if sep and not k.strip().startswith("#"):
                env[k.strip().removeprefix("export ").strip()] = v.strip().strip("'\"")
    env.update({k: os.environ[k] for k in env if k in os.environ})
    return env


ENV = load_env()
VOX = Path(os.path.expanduser(ENV["VOX_DIR"]))
RAW = VOX / "raw"
LAST = RAW / ".last"  # "<ts> <ok|failed>" from the latest clean, links a Capture to its Transcript


def model_name():
    return ENV["VOX_CLAUDE_MODEL"] if ENV["VOX_LLM"] == "anthropic" else ENV["VOX_OLLAMA_MODEL"]


def llm(system, user, timeout):
    """One-shot completion via the provider picked by VOX_LLM. Raises on any failure."""
    ask = claude if ENV["VOX_LLM"] == "anthropic" else ollama
    return strip_preamble(ask(system, user, timeout))


def claude(system, user, timeout):
    import anthropic  # only needed when VOX_LLM=anthropic

    client = anthropic.Anthropic(api_key=ENV["ANTHROPIC_API_KEY"] or None, timeout=timeout, max_retries=1)
    try:
        resp = client.messages.create(
            model=ENV["VOX_CLAUDE_MODEL"],
            max_tokens=16000,
            # cleanup and titles are simple rewrites, skip thinking for latency
            thinking={"type": "disabled"},
            output_config={"effort": "low"},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except anthropic.APIStatusError as e:
        raise RuntimeError(f"claude API {e.status_code}: {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise RuntimeError(f"claude unreachable: {e}") from e
    if resp.stop_reason == "refusal":
        raise RuntimeError("claude refused")
    return "".join(b.text for b in resp.content if b.type == "text")


def ollama(system, user, timeout):
    req = urllib.request.Request(
        ENV["OLLAMA_URL"] + "/api/chat",
        data=json.dumps({"model": ENV["VOX_OLLAMA_MODEL"], "stream": False,
                         "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                         "options": {"temperature": 0.2}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)["message"]["content"]


def strip_preamble(text):
    # small models like to open with "Here is the cleaned text:"
    text = text.strip()
    first, _, rest = text.partition("\n")
    if rest and first.rstrip().endswith(":") and len(first) < 80:
        text = rest.strip()
    return text


def slugify(title, max_words=6):
    t = title.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", t)[:max_words]
    return "-".join(words) or "untitled"


def extract_transcript(user_prompt):
    m = re.search(r"<TRANSCRIPT>\n?(.*?)\n?</TRANSCRIPT>", user_prompt, re.S)
    return m.group(1).strip() if m else user_prompt.strip()


def now_ts():
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")


def notify(msg):
    subprocess.run(["/usr/bin/osascript", "-e", f"display notification {json.dumps(msg)} with title \"vox\""])


def clean():
    sys.stdin.read()  # VoiceInk writes the full prompt to stdin synchronously, drain it so large prompts can't block
    system = os.environ.get("VOICEINK_SYSTEM_PROMPT", "")
    user = os.environ.get("VOICEINK_USER_PROMPT", "")
    transcript = extract_transcript(user)
    ts = now_ts()
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{ts}.md").write_text(transcript + "\n")
    try:
        # ponytail: stays under VoiceInk's 45 s Local CLI timeout so the raw fallback below still wins
        out = llm(system, user, timeout=35)
        status = "ok" if out else "failed"
    except Exception as e:
        print(f"vox clean: {e}", file=sys.stderr)
        out, status = "", "failed"
    LAST.write_text(f"{ts} {status}\n")
    print(out or transcript)


def capture():
    text = os.environ.get("VOICEINK_TRANSCRIPT") or sys.stdin.read()
    text = text.strip()
    ts, cleanup = now_ts(), "unknown"
    # reuse the clean step's timestamp only if it belongs to this Dictation
    if LAST.exists() and time.time() - LAST.stat().st_mtime < 120:
        ts, _, cleanup = LAST.read_text().strip().partition(" ")
    VOX.mkdir(parents=True, exist_ok=True)
    path = VOX / f"{ts}-untitled.md"
    created = datetime.strptime(ts, "%Y-%m-%d_%H%M%S").isoformat()
    path.write_text(
        f"---\ncreated: {created}\ntitle: untitled\nraw: raw/{ts}.md\ncleanup: {cleanup}\nmodel: {model_name()}\n---\n\n{text}\n"
    )
    if cleanup == "failed":
        notify("Cleanup failed, saved raw text")
    # VoiceInk kills custom commands after 10 s, so the Title is done detached
    subprocess.Popen([sys.executable, __file__, "title", str(path)], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


TITLE_PROMPT = (
    "Write a short title (3 to 6 words) for the following note, in the same language as the note. "
    "Output only the title, no quotes, no punctuation at the end."
)


def title(path):
    path = Path(path)
    content = path.read_text()
    body = content.split("\n---\n", 1)[-1].strip()
    try:
        t = llm(TITLE_PROMPT, body[:4000], timeout=120).splitlines()[0].strip(" \"'#*.")
    except Exception:
        t = ""
    slug = slugify(t) if t else "untitled"
    if slug == "untitled":
        path.write_text(content.replace("title: untitled\n", "title: untitled\ntitle_error: generation failed\n", 1))
        notify(f"Title generation failed: {path.name}")
        return
    ts = path.name.removesuffix("-untitled.md")
    path.write_text(content.replace("title: untitled\n", f"title: {json.dumps(t, ensure_ascii=False)}\n", 1))
    path.rename(path.with_name(f"{ts}-{slug}.md"))


def selftest():
    assert slugify("Meeting mit Änne zur Roadmap: Q4!") == "meeting-mit-aenne-zur-roadmap-q4"
    assert slugify("Größe über Straße eins zwei drei vier") == "groesse-ueber-strasse-eins-zwei-drei"
    assert slugify("???") == "untitled"
    assert extract_transcript("ctx\n<TRANSCRIPT>\nhallo welt\n</TRANSCRIPT>") == "hallo welt"
    assert strip_preamble("Here is the cleaned text:\nHallo Welt.") == "Hallo Welt."
    assert strip_preamble("Hallo Welt.") == "Hallo Welt."
    print("ok")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or [""]
    cmds = {"clean": clean, "capture": capture, "title": title, "selftest": selftest}
    if cmd not in cmds:
        sys.exit(__doc__)
    cmds[cmd](*args)
