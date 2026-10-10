#!/usr/bin/env bash
#
# Install ocr-my-mess on Fedora Atomic (Silverblue, Kinoite, secureblue) with Toolbx.
#
# The script works in two situations:
#   - run from a clone of the repository: it installs the local source (`pip install .`)
#   - run standalone (e.g. downloaded with curl): it installs the package from PyPI
#
# See the "Fedora Atomic & secureblue (Toolbx)" section of the README for details.

set -euo pipefail

CONTAINER_NAME="${OCR_MY_MESS_CONTAINER:-ocr-my-mess}"

echo "Installing ocr-my-mess on Fedora Atomic with Toolbx (container: $CONTAINER_NAME)"

# 1. Check that toolbox is available.
if ! command -v toolbox >/dev/null 2>&1; then
    echo "Error: toolbox is not installed." >&2
    echo "It ships by default on Fedora Atomic (Silverblue, Kinoite, secureblue)." >&2
    exit 1
fi

# 2. Create the container if it does not exist yet.
if toolbox list | grep -qw "$CONTAINER_NAME"; then
    echo "Container '$CONTAINER_NAME' already exists."
else
    echo "Creating Toolbx container '$CONTAINER_NAME'..."
    toolbox create -c "$CONTAINER_NAME"
fi

# 3. Pick the source to install: local checkout first, PyPI otherwise.
if [ -f pyproject.toml ]; then
    echo "Source checkout detected: installing the local project (pip install .)."
    PY_INSTALL="pip install ."
else
    echo "No source checkout detected: installing from PyPI (pip install ocr-my-mess)."
    PY_INSTALL="pip install --upgrade ocr-my-mess"
fi

# 4. Install the system dependencies and the package inside the container.
echo "Configuring the environment inside the container..."
toolbox run -c "$CONTAINER_NAME" bash -lc "
set -e
echo 'Installing system dependencies...'
sudo dnf install -y tesseract tesseract-langpack-fra tesseract-langpack-eng jbig2dec libreoffice python3-pip python3-tkinter

echo 'Installing the Python package...'
$PY_INSTALL

echo 'Installation complete.'
"

# 5. Print usage instructions.
cat <<EOF
---------------------------------------------------------------------------
Installation complete.

Run the command-line interface (CLI):
  toolbox run -c $CONTAINER_NAME ocr-my-mess --help

Run the graphical interface (GUI):
  toolbox run -c $CONTAINER_NAME ocr-my-mess
  (on secureblue, enable Xwayland first and reboot:
     ujust set-xwayland on)

Enter the container:
  toolbox enter -c $CONTAINER_NAME
---------------------------------------------------------------------------
EOF
