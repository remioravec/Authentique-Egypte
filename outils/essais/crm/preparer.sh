#!/usr/bin/env bash
# Prépare le banc d'essai : récupère les vraies feuilles de style de
# l'admin WordPress du site, puis copie celles du plugin.
#
# Les feuilles du cœur ne sont pas versionnées ici — elles appartiennent
# à WordPress et changent à chaque mise à jour. On les reprend du site
# pour tester contre ce qui y tourne vraiment.

set -euo pipefail
ici="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
site="${AE_SITE:-https://authentiquegypte.com}"

for f in common forms admin-menu edit list-tables; do
  curl -fsS -o "$ici/$f.css" "$site/wp-admin/css/$f.min.css"
done
for f in buttons dashicons; do
  curl -fsS -o "$ici/$f.css" "$site/wp-includes/css/$f.min.css"
done

cp "$ici/../../../plugin/ae-crm/assets/css/crm.css" "$ici/crm.css"
cp "$ici/../../../plugin/ae-crm/assets/js/crm.js"   "$ici/crm.js"
php "$ici/generer.php"
