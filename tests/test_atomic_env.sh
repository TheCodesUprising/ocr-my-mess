#!/bin/bash

# Script de test d'intégration pour simuler l'environnement Fedora Atomic via Podman
# Ce script vérifie que les dépendances système et Python s'installent correctement
# et que les tests unitaires passent dans un environnement Fedora.

set -e

echo "🧪 Simulation de l'environnement Fedora via Podman..."

# 1. Récupérer le chemin absolu du projet
PROJECT_DIR=$(pwd)

# 2. Lancer un conteneur Fedora et exécuter les étapes d'installation et de test
# On monte le projet dans le conteneur et on simule les commandes de install_atomic.sh
podman run -it --rm \
    -v "$PROJECT_DIR":/app:Z \
    -w /app \
    fedora:latest bash -c "
        echo '📦 Installation des dépendances système...'
        dnf install -y tesseract tesseract-langpack-fra tesseract-langpack-eng jbig2dec libreoffice python3-pip python3-tkinter

        echo '🐍 Installation du projet...'
        pip install .

        echo '🧪 Exécution des tests unitaires...'
        pip install pytest pymupdf

        pytest
    "

if [ $? -eq 0 ]; then
    echo "✅ TEST RÉUSSI : L'environnement Fedora est compatible et les tests passent."
else
    echo "❌ TEST ÉCHOUÉ : Un problème est survenu lors de l'installation ou des tests."
    exit 1
fi
