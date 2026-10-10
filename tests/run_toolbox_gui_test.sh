#!/usr/bin/env bash
#
# Build a Fedora Toolbx container (the kind of environment created by
# scripts/install_atomic.sh on Fedora Atomic / secureblue) and run the GUI
# smoke tests inside it.
#
# Usage:
#   tests/run_toolbox_gui_test.sh                # run every GUI test
#   tests/run_toolbox_gui_test.sh -k widgets     # forward args to pytest
#
# Environment variables:
#   CONTAINER_ENGINE             podman (default) or docker
#   TOOLBOX_IMAGE                base image, default registry.fedoraproject.org/fedora-toolbox:44
#   OCR_MY_MESS_TOOLBOX_TEST_IMAGE  tag of the built test image
#   OCR_MY_MESS_USE_HOST_DISPLAY   set to 1 to reuse the host X display instead of Xvfb
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# --- Container engine -------------------------------------------------------
ENGINE="${CONTAINER_ENGINE:-}"
if [ -z "$ENGINE" ]; then
    if command -v podman >/dev/null 2>&1; then
        ENGINE=podman
    elif command -v docker >/dev/null 2>&1; then
        ENGINE=docker
    else
        echo "❌ Neither podman nor docker was found in PATH." >&2
        exit 1
    fi
fi

IMAGE="${OCR_MY_MESS_TOOLBOX_TEST_IMAGE:-localhost/ocr-my-mess-toolbox-test:latest}"
TOOLBOX_IMAGE="${TOOLBOX_IMAGE:-registry.fedoraproject.org/fedora-toolbox:44}"

echo "🐳 Engine : $ENGINE"
echo "📦 Image  : $IMAGE"
echo "🧱 Base   : $TOOLBOX_IMAGE"

# --- Lean build context -----------------------------------------------------
# The repository root also contains large build/dist/.venv directories, so we
# copy only what the image needs into a temporary context.
BUILD_DIR="$(mktemp -d)"
cleanup() { rm -rf "$BUILD_DIR"; }
trap cleanup EXIT

cp "$PROJECT_DIR/pyproject.toml" "$PROJECT_DIR/README.md" "$PROJECT_DIR/pytest.ini" "$BUILD_DIR/"
cp -r "$PROJECT_DIR/pdf_pipeline" "$BUILD_DIR/pdf_pipeline"
mkdir -p "$BUILD_DIR/tests"
cp "$SCRIPT_DIR/Dockerfile.toolbox" "$SCRIPT_DIR/test_toolbox_gui.py" "$BUILD_DIR/tests/"

# --- Build ------------------------------------------------------------------
echo "🔨 Building the Toolbx GUI test image (this may take a while the first time)..."
"$ENGINE" build \
    -f "$BUILD_DIR/tests/Dockerfile.toolbox" \
    --build-arg "TOOLBOX_IMAGE=$TOOLBOX_IMAGE" \
    -t "$IMAGE" \
    "$BUILD_DIR"

# --- Run --------------------------------------------------------------------
run_args=(--rm -e OCR_MY_MESS_TOOLBOX_TEST=1)

# Optionally reuse the host display; otherwise the test starts its own Xvfb.
if [ "${OCR_MY_MESS_USE_HOST_DISPLAY:-0}" = "1" ] && [ -n "${DISPLAY:-}" ]; then
    echo "🖥️  Forwarding the host display ($DISPLAY)"
    run_args+=(-e "DISPLAY=$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix)
fi

echo "🧪 Running the GUI tests inside the container..."
"$ENGINE" run "${run_args[@]}" "$IMAGE" "$@"

echo "✅ Toolbx GUI tests passed."
