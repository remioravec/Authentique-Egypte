#!/usr/bin/env bash
# Fabrique les ZIP des extensions.
#
#   ./outils/construire.sh
#     → dist/ae-commentaires.zip   relecture façon Google Docs
#     → dist/ae-back-office.zip    contenus rangés par gabarit

set -euo pipefail

racine="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dist="$racine/dist"

echo "→ Contrôle de la syntaxe PHP"
find "$racine/plugin" -name '*.php' -print0 | xargs -0 -n1 php -l >/dev/null

echo "→ Contrôle de la syntaxe JS"
find "$racine/plugin" -name '*.js' -print0 | xargs -0 -n1 node --check

# Un écran qui affiche du balisage « abo- » sans demander la feuille de
# style commune s'affiche entièrement nu. C'est arrivé une fois, sans
# rien casser d'autre : rien ne le signalait.
echo "→ Contrôle des feuilles de style demandées"
manque=0
for fichier in "$racine"/plugin/ae-back-office/includes/class-abo-*.php; do
  if grep -q 'class="wrap abo' "$fichier" && ! grep -q "wp_enqueue_style( 'abo-admin'" "$fichier"; then
    echo "  ✗ $(basename "$fichier") affiche un écran sans demander abo-admin"
    manque=1
  fi
done
[ "$manque" -eq 0 ] || { echo "Feuille de style manquante."; exit 1; }

echo "→ Fabrication des ZIP"
rm -rf "$dist"
mkdir -p "$dist"
for extension in ae-commentaires ae-back-office; do
  ( cd "$racine/plugin" && zip -qr "$dist/$extension.zip" "$extension" -x '*.DS_Store' )
  printf "✓ %s (%s)\n" "$dist/$extension.zip" "$(du -h "$dist/$extension.zip" | cut -f1)"
done
