# AE CRM — les demandes reçues

Conserve les demandes envoyées depuis les formulaires du site et les présente
en pipeline : quatre colonnes, une carte par demande qu'on fait glisser de
l'une à l'autre, la fiche client au clic.

## Ce qu'il ne fait pas

**Il ne modifie aucun formulaire et aucun courriel.** Il écoute
`wpforms_process_complete`, une action qui se déclenche *après* que WPForms a
validé la soumission et envoyé ses notifications. Une action, pas un filtre :
rien de ce qui est fait ici ne remonte à WPForms. Le désactiver ne change rien
à la réception des demandes par courriel — on perd seulement l'archive.

La captation est enveloppée dans un `try/catch` : même une erreur de notre
côté ne peut pas empêcher la page de confirmation de s'afficher après un envoi
réussi.

## Pourquoi une extension séparée

Les demandes étaient un module de **AE Back-office**. Deux écrans y partageaient
une feuille de style qu'un seul déclarait : ouvert directement, le tableau
s'affichait entièrement nu. Le symptôme est anodin, la leçon ne l'est pas — un
outil dont l'agence se sert tous les jours ne doit dépendre de rien d'autre
pour fonctionner.

Cette extension est autonome : elle ne suppose la présence d'aucune autre, et
charge ses propres fichiers. Si l'ancienne version de AE Back-office est encore
installée, son module « Demandes » est débranché au démarrage — sans quoi
chaque formulaire envoyé serait enregistré **deux fois**.

## L'écran

Quatre colonnes — *Nouvelle · En cours · Traitée · Archivée*. Une carte porte
l'essentiel sans qu'on l'ouvre : la personne, le formulaire d'origine, le
renseignement le plus parlant qu'elle a laissé (budget, voyageurs, durée,
dates), son adresse, l'ancienneté de la demande. La couleur de pastille est
calculée à partir du nom : la même personne garde la sienne d'une colonne à
l'autre et d'un jour à l'autre.

**Glisser-déposer** : le déplacement est enregistré aussitôt. Si le serveur
refuse, la carte revient d'où elle vient plutôt que de mentir sur son état.

**Au clic — ou à Entrée, les cartes sont focalisables — la fiche client
s'ouvre** dans un tiroir : tous les champs remplis, la page d'origine, un
bouton **Répondre** qui ouvre le courriel prérempli, un sélecteur de colonne, un
journal de suivi interne. Échap referme.

Sur un écran étroit les quatre colonnes restent côte à côte et le tableau défile
horizontalement ; en dessous de 960 px, on empile. Le glisser-déposer natif
HTML5 n'existe pas au doigt : sur téléphone, c'est le sélecteur de colonne de
la fiche qui prend le relais.

## Si l'écran s'affiche sans mise en forme

Un bandeau rouge le dit et explique quoi faire. Il est masqué par la feuille de
style elle-même : s'il apparaît, c'est qu'elle n'est pas arrivée — presque
toujours un cache à vider (LiteSpeed → *Purger tout*, puis
<kbd>Ctrl</kbd>+<kbd>Maj</kbd>+<kbd>R</kbd>).

Les fichiers sont versionnés par leur date de modification, pas par la version
de l'extension : une retouche est visible sans changer de numéro, et aucun cache
ne peut servir l'ancienne.

## Données personnelles

Ces enregistrements contiennent noms, adresses et numéros. Ils vivent dans un
type de contenu **privé** (`ae_demande`, `public => false`), invisible du site
public, exclu de la recherche, des flux et des plans de site.

Une durée de conservation est réglable dans **Demandes → Réglages** et vaut
politique de conservation. Tant qu'elle n'est pas choisie, **rien n'est
supprimé** : une purge silencieuse par défaut serait pire que pas de purge du
tout.

## Note technique

Les clés de méta gardent leur ancien préfixe `_abo_`. Cette extension succède au
module « Demandes » de AE Back-office, et les demandes déjà reçues portent ces
clés-là. Les renommer pour la cohérence du nom aurait imposé une migration —
donc un risque de perte — pour un bénéfice nul côté agence.
