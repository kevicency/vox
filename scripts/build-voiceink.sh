#!/usr/bin/env bash
# Clone or update VoiceInk next to this repo and build it from source into ~/Downloads/VoiceInk.app.
set -euo pipefail
SRC="${VOICEINK_SRC:-$HOME/code/VoiceInk}"
DEPS="$HOME/VoiceInk-Dependencies"
# xcode-select may point at the Command Line Tools, VoiceInk needs full Xcode
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
command -v cmake >/dev/null || brew install cmake
# MLX needs the Metal compiler, which Xcode ships as a separate download
xcrun -f metal >/dev/null 2>&1 || xcodebuild -downloadComponent MetalToolchain

if [[ -d "$SRC/.git" ]]; then
  git -C "$SRC" pull --ff-only
else
  git clone https://github.com/Beingpax/VoiceInk.git "$SRC"
fi

# whisper.cpp's build-xcframework.sh also targets iOS/visionOS/tvOS and fails without those SDKs.
# Build a macOS-only xcframework first; VoiceInk's `make whisper` skips when it already exists.
if [[ ! -d "$DEPS/whisper.cpp/build-apple/whisper.xcframework" ]]; then
  mkdir -p "$DEPS"
  [[ -d "$DEPS/whisper.cpp" ]] || git clone https://github.com/ggerganov/whisper.cpp.git "$DEPS/whisper.cpp"
  cd "$DEPS/whisper.cpp"
  # drop every non-macOS cmake block and every reference to non-macOS build dirs
  /usr/bin/python3 - <<'PY'
import re
src = open("build-xcframework.sh").read()
src = re.sub(r'echo "Building for (iOS|visionOS|tvOS)[^\n]*\n.*?cmake --build build-\S+ --config Release[^\n]*\n', "", src, flags=re.S)
src = "\n".join(l for l in src.splitlines() if l.startswith("rm -rf") or not re.search(r"build-(ios|visionos|tvos)", l))
open("build-xcframework-macos.sh", "w").write(src + "\n")
PY
  bash build-xcframework-macos.sh
  cd - >/dev/null
fi

make -C "$SRC" local
echo "Built. Move it into place: mv ~/Downloads/VoiceInk.app /Applications/"
