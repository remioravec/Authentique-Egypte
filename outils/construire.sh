#!/usr/bin/env bash
# Fabrique les ZIP des extensions.
#
#   ./outils/construire.sh
#     → dist/ae-refonte-review.zip   relecture et annotations client
#     → dist/ae-back-office.zip      contenus rangés par gabarit
#
# Les fichiers de maquette vivent dans /maquettes à la racine du dépôt :
# c'est la source unique. Ce script les recopie dans le plugin au moment
# de la construction, pour qu'un seul ZIP suffise à déployer.

set -euo pipefail

racine="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
plugin="$racine/plugin/ae-refonte-review"
dist="$racine/dist"

echo "→ Contrôle de la syntaxe PHP"
find "$racine/plugin" -name '*.php' -print0 | xargs -0 -n1 php -l >/dev/null

echo "→ Contrôle de la syntaxe JS"
node --check "$plugin/assets/js/calque.js"

echo "→ Copie des maquettes"
rm -f "$plugin/maquettes/"*.html
rm -rf "$plugin/maquettes/assets"
cp "$racine/maquettes/"*.html "$plugin/maquettes/"
cp -r "$racine/maquettes/assets" "$plugin/maquettes/assets"
ls -1 "$plugin/maquettes/" | sed 's/^/   /'

echo "→ Fabrication des ZIP"
rm -rf "$dist"
mkdir -p "$dist"
for extension in ae-refonte-review ae-back-office; do
  ( cd "$racine/plugin" && zip -qr "$dist/$extension.zip" "$extension" -x '*.DS_Store' )
  printf "✓ %s (%s)\n" "$dist/$extension.zip" "$(du -h "$dist/$extension.zip" | cut -f1)"
done
