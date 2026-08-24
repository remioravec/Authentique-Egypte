#!/usr/bin/env bash
# Fabrique le ZIP du plugin, maquettes incluses.
#
#   ./outils/construire.sh          → dist/ae-refonte-review.zip
#
# Les fichiers de maquette vivent dans /maquettes à la racine du dépôt :
# c'est la source unique. Ce script les recopie dans le plugin au moment
# de la construction, pour qu'un seul ZIP suffise à déployer.

set -euo pipefail

racine="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
plugin="$racine/plugin/ae-refonte-review"
dist="$racine/dist"

echo "→ Contrôle de la syntaxe PHP"
find "$plugin" -name '*.php' -print0 | xargs -0 -n1 php -l >/dev/null

echo "→ Contrôle de la syntaxe JS"
node --check "$plugin/assets/js/calque.js"

echo "→ Copie des maquettes"
rm -f "$plugin/maquettes/"*.html
cp "$racine/maquettes/"*.html "$plugin/maquettes/"
ls -1 "$plugin/maquettes/" | sed 's/^/   /'

echo "→ Fabrication du ZIP"
rm -rf "$dist"
mkdir -p "$dist"
( cd "$racine/plugin" && zip -qr "$dist/ae-refonte-review.zip" ae-refonte-review -x '*.DS_Store' )

echo "✓ $dist/ae-refonte-review.zip"
