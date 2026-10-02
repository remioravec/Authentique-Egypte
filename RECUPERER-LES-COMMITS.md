# Les neuf commits en attente

Le droit d'écriture sur le dépôt a sauté en cours de session : `git fetch`
passe, `git push` répond 403, y compris pour un commit de sept octets sur
une branche jetable. Ce n'est donc ni la taille, ni le contenu.

En attendant que l'accès revienne, les neuf commits sont dans
`refonte-commits-en-attente.bundle`, vérifié par `git bundle verify`.

## Les récupérer depuis ta machine

    git clone https://github.com/remioravec/Authentique-Egypte
    cd Authentique-Egypte
    git fetch /chemin/vers/refonte-commits-en-attente.bundle \
        claude/authentique-egypte-redesign-qilf37
    git checkout -B claude/authentique-egypte-redesign-qilf37 FETCH_HEAD
    git push -u origin claude/authentique-egypte-redesign-qilf37

## Ce qu'ils contiennent

    498e06e  Sauvegarde de l'existant, et l'outil de bascule
    3ab80e0  Le plan de mise en ligne, et le contrôle des URL
    adb8fbb  « L'agence » sortie de la corbeille, et les gabarits
    15fa102  Les traces de chantier retirées des 58 pages
    c763eab  Le balisage ne garde que ce qu'il peut prouver, bascule à 55
    0129419  Trois finitions, et ce qu'il ne fallait pas corriger
    3b32721  Cinq retouches de mise en page
    782e0e6  Une seule liste pour Mélanie, et une correction

Le travail lui-même n'est pas dans le dépôt : il est déjà déployé sur les
58 pages brouillon du site, vérifié, et les 25 pages publiées n'ont pas
bougé. Ces commits portent les outils qui l'ont fait, la sauvegarde
d'avant bascule et les documents.

## Rétablir l'accès

Reconnecter GitHub depuis https://claude.ai/connect-github, et vérifier
que l'app Claude a les droits d'écriture sur `remioravec/Authentique-Egypte`.
