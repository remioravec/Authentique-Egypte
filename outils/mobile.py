#!/usr/bin/env python3
"""
Injecte le plancher tactile et typographique mobile dans les maquettes.

Retour cliente du 24/08/2026 : « les polices ne sont pas adaptées à la
version mobile ». Mesure faite au navigateur sur les quatre maquettes,
à 375, 390 et 412 px : aucun débordement horizontal, mais 18 à 22
éléments de texte sous 14 px — jusqu'à 11,2 px — et 5 à 6 cibles
tactiles sous 40 px de haut.

Le bloc ci-dessous relève tout cela sans toucher aux proportions du
bureau. Il est injecté à la FIN du <style> de chaque maquette, pour
passer après les règles de la page à spécificité égale.

Idempotent : relancé, il remplace le bloc au lieu d'en ajouter un
second. Les quatre maquettes restent ainsi rigoureusement identiques
sur ce point.

    ./outils/mobile.py maquettes/index.html …
"""

import re
import sys

DEBUT = '/* ===== AE-MOBILE : début du bloc généré — ne pas éditer à la main ===== */'
FIN = '/* ===== AE-MOBILE : fin du bloc généré ===== */'

BLOC = DEBUT + """
/* ------------------------------------------------------------------
   NOTES DE PRODUCTION
   Les paragraphes d'avertissement portaient leur taille en style en
   ligne (font-size:.86rem), qu'aucune feuille ne peut battre. La taille
   est passée dans cette classe ; l'attribut ne garde que la couleur.
   ------------------------------------------------------------------ */
.note{font-size:.9rem;line-height:1.6}

/* ------------------------------------------------------------------
   PLANCHER MOBILE
   Retour cliente du 24/08/2026, mesuré au navigateur à 375/390/412 px.

   Trois choses, et rien d'autre :
   1. plus aucun texte sous 15 px — ils descendaient à 11,2 px ;
   2. toute cible tactile isolée fait au moins 44 px de haut ;
   3. la barre fixe du bas ne recouvre plus la fin de la page.

   Le seuil est à 900 px, pas 700 : mesuré, une tablette en portrait
   (768 px) gardait les tailles du bureau, jusqu'à 11,5 px.

   Les liens en ligne dans un paragraphe gardent leur hauteur : les
   agrandir casserait l'interligne, et la règle des 44 px ne s'applique
   pas à eux.
   ------------------------------------------------------------------ */
@media (max-width:900px){

  /* 1 ─ Texte ------------------------------------------------------ */
  body{font-size:17px;line-height:1.7}

  h1{font-size:clamp(1.85rem,7.2vw,2.3rem);letter-spacing:-1px;line-height:1.18}
  h2{font-size:clamp(1.42rem,5.6vw,1.8rem);letter-spacing:-.5px}
  h3{font-size:1.12rem}
  h4{font-size:1.02rem}

  .eyebrow{font-size:.88rem;letter-spacing:.12em}
  .lede,.chapeau p,.chapeau .sous,.reponse,.encart,.alerte{font-size:1.04rem}

  /* Tout ce qui descendait sous 15 px remonte au même palier. */
  .bandeau,.ariane,.compte,.legende,.legende span,
  .pied,.pied__bas,.pied ul,.mm-legende,.aremplir,
  .carte__route,.carte__meta,.carte__tag,.puce,.prix,.prix small,.prix i,
  .fille__nb,.fille__txt span,.guide span,.guide b,
  .gens span,.avis footer,.avis blockquote,.avis .et,
  .chapeau__st,.chapeau__meta,
  .tab,.tab th,.tab td,.et,.jours,.choix,.choix th,.choix td,
  .tag-a,.fbtn,.fbtn .n,.filtres__d,.fpan label,.fpan label span,
  .route span,.route em,.route b,
  .som,.som a,.som h4,.lat__b,.lat__b ul,.lat__b li a,.lat__b p,
  .resa,.resa ul,.resa li,.resa .prix small,.resa .prix i,
  .incl,.incl ul,.incl li,.jour p,.etape p,.etape h4,
  .fig figcaption,.galerie__leg,.galerie__plus,
  .faq__c,.moment,.duree,.site p,.site__meta,
  .compo__phrase,.compo__t p,.champ>span,.opts,
  .ruban a,.ruban a span,
  small,.lien-fl,.lien-txt,
  /* Ces trois-là gagnent contre `h4` seul : leur règle porte une classe. */
  .som h4,.pied h4,.lat__b h4,.incl h3,
  .quand,.etape .quand,.fig__sur,.mm-btn,
  .choix tbody th,.choix thead th,.tab tbody th,.tab thead th,
  .jours tbody th,.jours thead th,
  .prix i,.resa .prix i,.resa .prix small,
  .carte__pied,.filtres label,.compo__res,
  .galerie a:first-child .galerie__leg,
  .avis .et,.reperes .km,.site h3,
  /* Derniers relevés à la sonde, à 375 et 768 px. */
  .note,.jeton,.ini,.opt,.vers,.etape .vers,.vign span,.vign b,
  .devis__act small,.resa-mob .p small,.resa-mob .p i,
  .bande b,.bande b span,.figcaption,.fig figcaption b,
  .som h4,.compte,.chapeau__meta span{font-size:.95rem}

  /* Le ruban des douze mois est le seul endroit où l'on peut serrer :
     il est décoratif, et le tableau qui suit dit la même chose en clair. */
  .ruban a{font-size:.95rem;padding:13px 2px 11px}
  .ruban a span{font-size:.9rem}

  .faq summary{font-size:1.06rem;padding-right:42px}
  .faq__c{padding-right:0}

  /* 2 ─ Cibles tactiles -------------------------------------------- */
  /* 44 px : la hauteur d'un doigt. On ne l'applique qu'aux cibles
     isolées — un lien au milieu d'une phrase garde sa hauteur. */
  .btn{font-size:1rem;padding:15px 24px;min-height:48px}
  .btn--sm{font-size:.95rem;padding:13px 20px;min-height:46px}

  .nav>a,.menu__pan a,.burger,
  .pied li a,.lat__b li a,.som a,
  .filtres button,.fbtn,.fpan label,.filtres__d select,
  .opt,.mm-btn,.tri,#tri,
  .lien-fl,.vers,.remonte,.carte .lien-fl,
  .faq summary,.guide,.carte h3 a{
    min-height:44px;
    display:flex;
    align-items:center;
  }
  .som a,.pied li a,.lat__b li a{padding-top:9px;padding-bottom:9px}
  .opt{padding:11px 16px;justify-content:center}
  .fpan label{padding:11px 10px}
  .mm-btn{padding:11px 16px}
  .carte h3 a,.guide{display:block} /* ces deux-là englobent déjà leur cible */
  .faq summary{display:block;padding-top:19px;padding-bottom:19px}

  /* Les cartes entières sont cliquables : rien à agrandir dedans. */
  a.carte,a.guide,a.fille,a.une{min-height:0}

  /* Le logo doit rester une cible confortable. */
  .logo img{height:44px}
}

/* 3 ─ Barre fixe du bas ---------------------------------------------
   Elle n'apparaît qu'en dessous de 860 px : le rembourrage ne vaut
   que là, sinon il ajoute du vide en bas de page sur tablette. */
@media (max-width:860px){
  body{padding-bottom:calc(96px + env(safe-area-inset-bottom))}
}

/* Écrans très étroits : on desserre les gouttières avant le texte. */
@media (max-width:380px){
  .wrap{width:calc(100% - 28px)}
  .btn{padding:15px 18px}
}
""" + FIN


def injecter(chemin: str) -> None:
    with open(chemin, encoding='utf-8') as f:
        page = f.read()

    # Remplacement si le bloc est déjà là.
    motif = re.compile(re.escape(DEBUT) + r'.*?' + re.escape(FIN), re.S)
    if motif.search(page):
        page = motif.sub(BLOC, page)
        action = 'remplacé'
    else:
        # On l'ajoute à la fin du dernier <style> du document.
        derniere = page.rfind('</style>')
        if derniere < 0:
            sys.exit('%s : aucun <style> trouvé' % chemin)
        page = page[:derniere] + '\n' + BLOC + '\n' + page[derniere:]
        action = 'ajouté'

    with open(chemin, 'w', encoding='utf-8') as f:
        f.write(page)

    print('%-30s bloc mobile %s' % (chemin.split('/')[-1], action))


if __name__ == '__main__':
    for chemin in sys.argv[1:]:
        injecter(chemin)
