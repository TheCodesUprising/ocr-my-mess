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

echo "🚀 Installation de ocr-my-mess pour Fedora Atomic via Toolbx"

# 1. Vérifier que toolbox est disponible
if ! command -v toolbox >/dev/null 2>&1; then
    echo "❌ Erreur : toolbox n'est pas installé." >&2
    echo "   Il est fourni par défaut sur Fedora Atomic (Silverblue, Kinoite, secureblue)." >&2
    exit 1
fi

# 2. Créer le conteneur s'il n'existe pas déjà
if toolbox list | grep -qw "$CONTAINER_NAME"; then
    echo "ℹ️  Le conteneur '$CONTAINER_NAME' existe déjà."
else
    echo "📦 Création du conteneur Toolbx '$CONTAINER_NAME'..."
    toolbox create -c "$CONTAINER_NAME"
fi

# 3. Choisir la source à installer : checkout local, sinon PyPI.
if [ -f pyproject.toml ]; then
    echo "📁 Dépôt source détecté : installation locale du projet (pip install .)."
    PY_INSTALL="pip install ."
else
    echo "📦 Aucun dépôt source détecté : installation depuis PyPI (pip install ocr-my-mess)."
    PY_INSTALL="pip install --upgrade ocr-my-mess"
fi

# 4. Installer les dépendances système et le package dans le conteneur
echo "🔧 Configuration de l'environnement à l'intérieur du conteneur..."
toolbox run -c "$CONTAINER_NAME" bash -lc "
set -e
echo '🛠️  Installation des dépendances système...'
sudo dnf install -y tesseract tesseract-langpack-fra tesseract-langpack-eng jbig2dec libreoffice python3-pip python3-tkinter

echo '🐍 Installation du package Python...'
$PY_INSTALL

echo '✅ Installation terminée !'
"

# 5. Afficher les instructions d'utilisation
cat <<EOF
---------------------------------------------------------------------------
🎉 Installation réussie !

Lancer l'interface en ligne de commande (CLI) :
  toolbox run -c $CONTAINER_NAME ocr-my-mess --help

Lancer l'interface graphique (GUI) :
  toolbox run -c $CONTAINER_NAME ocr-my-mess
  (sur secureblue, activez d'abord Xwayland puis redémarrez :
     ujust set-xwayland on)

Entrer dans le conteneur :
  toolbox enter -c $CONTAINER_NAME
---------------------------------------------------------------------------
EOF
