#!/usr/bin/env python3
"""Refaire /sur-mesure/ au dessin de la refonte, formulaire conservé.

    python3 outils/page-sur-mesure.py --essai       (hors ligne, aucun écrit)
    WP_AUTH='compte:mdp' python3 outils/page-sur-mesure.py --brouillon
    WP_AUTH='compte:mdp' python3 outils/page-sur-mesure.py --appliquer

/sur-mesure/ est la page d'arrivée de tous les boutons « devis » du site :
elle reçoit 312 liens entrants et le formulaire WPForms #7445. Après la
bascule, on y passait du neuf à l'ancien en un clic. Rémi a tranché : la
page passe au nouveau dessin, l'adresse ne bouge pas, le formulaire reste
exactement celui qui tourne aujourd'hui.

Ce que la page dit aujourd'hui, et qu'on ne réécrit pas :
  — le titre « Demander un devis » ;
  — le sous-titre « Votre Voyage sur mesure en Egypte » (seul l'accent
    d'Égypte est posé, comme sur les 54 autres pages) ;
  — le formulaire #7445 et ses douze champs.
Le reste du texte — les trois garanties, la note sur la carte bancaire,
le bouton WhatsApp — est repris mot pour mot du bloc « devis » que
portent déjà les 54 pages de la refonte. Rien n'est inventé, sauf deux
libellés de navigation, signalés en commentaire dans le code.

La coque — feuille de style, bandeau, en-tête, pied, scripts — est reprise
d'une page de référence déjà en ligne, celle dont l'en-tête est la variante
majoritaire (34 pages) et dont les liens sont déjà les adresses
définitives.
"""

import argparse
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAUVE = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne')
SITE = 'https://authentiquegypte.com'
REFERENCE = 8923          # Refonte · Destination · Voyage à Fayoum
CIBLE = 786               # /sur-mesure/, publiée
FORMULAIRE = 7445
COCHE = ('<svg aria-hidden="true" width="17" height="17" viewBox="0 0 24 24" '
         'fill="none" stroke="currentColor" stroke-width="1.7" '
         'stroke-linecap="round" stroke-linejoin="round">'
         '<path d="M5 12l4.5 4.5L19 7"/></svg>')
GARANTIES = ['Devis gratuit, détaillé jour par jour, sans engagement',
             'Guide égyptologue francophone et chauffeur privatif',
             'Acompte seulement une fois l&#x27;itinéraire validé']

# Les quelques règles que la refonte n'a pas, faute d'avoir eu une page
# de formulaire : un h1 dans le bloc devis, et de quoi tenir les champs
# de WPForms dans la même grille que le reste. Tout en jetons existants.
STYLE = """<style>
.elementor-template-canvas .pg .devis h1{font-family:"Archivo",sans-serif;font-weight:600;
 letter-spacing:-.7px;font-size:clamp(1.6rem,2.6vw,2.15rem);line-height:1.18;
 margin:0 0 18px;color:#fff}
.elementor-template-canvas .pg .sm{max-width:860px}
.elementor-template-canvas .pg .sm .wpforms-container{margin:0}
.elementor-template-canvas .pg .sm .wpforms-field{padding:0 0 18px}
.elementor-template-canvas .pg .sm .wpforms-field-label{font-family:"Manrope",sans-serif;
 font-size:.95rem;font-weight:700;color:var(--noir);margin-bottom:7px}
.elementor-template-canvas .pg .sm .wpforms-field-sublabel{font-family:"Manrope",sans-serif;
 font-size:.83rem;color:var(--gris-clair)}
.elementor-template-canvas .pg .sm input[type=text],
.elementor-template-canvas .pg .sm input[type=email],
.elementor-template-canvas .pg .sm input[type=tel],
.elementor-template-canvas .pg .sm input[type=number],
.elementor-template-canvas .pg .sm input[type=date],
.elementor-template-canvas .pg .sm select,
.elementor-template-canvas .pg .sm textarea{width:100%;font-family:"Manrope",sans-serif;
 font-size:1rem;color:var(--noir);background:#fff;border:1px solid var(--ligne);
 border-radius:var(--r-m);padding:13px 15px;min-height:48px}
.elementor-template-canvas .pg .sm textarea{min-height:150px;line-height:1.6}
.elementor-template-canvas .pg .sm input:focus-visible,
.elementor-template-canvas .pg .sm select:focus-visible,
.elementor-template-canvas .pg .sm textarea:focus-visible{outline:3px solid var(--or);
 outline-offset:-1px;border-color:var(--teal-txt)}
.elementor-template-canvas .pg .sm .wpforms-submit{display:inline-flex;align-items:center;
 justify-content:center;gap:9px;font-family:"Manrope",sans-serif;padding:14px 26px;
 border-radius:var(--r-pill);border:1px solid var(--or);background:var(--or);
 color:#3A2A00;font-weight:700;font-size:1.02rem;min-height:48px;cursor:pointer}
.elementor-template-canvas .pg .sm .wpforms-submit:hover{background:var(--or-clair);
 border-color:var(--or-clair)}
.elementor-template-canvas .pg .sm .wpforms-required-label{color:var(--rouge)}
/* Les cases de WPForms font 13 px : sous la cible tactile de 44 px que la
   refonte tient partout ailleurs. On agrandit la case et la ligne entière. */
.elementor-template-canvas .pg .sm .wpforms-field-checkbox li,
.elementor-template-canvas .pg .sm .wpforms-field-radio li,
.elementor-template-canvas .pg .sm .wpforms-field-payment-multiple li{display:flex;
 align-items:center;gap:11px;min-height:44px;margin:0}
.elementor-template-canvas .pg .sm input[type=checkbox],
.elementor-template-canvas .pg .sm input[type=radio]{flex:0 0 auto;width:20px;height:20px;
 min-height:0;margin:0;padding:0;accent-color:var(--teal-txt)}
.elementor-template-canvas .pg .sm .wpforms-field-checkbox label,
.elementor-template-canvas .pg .sm .wpforms-field-radio label{font-weight:400;margin:0;
 font-family:"Manrope",sans-serif;color:var(--texte);cursor:pointer}
@media (max-width:600px){.elementor-template-canvas .pg .sm .wpforms-submit{width:100%}}
</style>"""


def corps():
    """Le <main> de la page, construit avec les textes existants."""
    lis = ''.join('<li>%s<span>%s</span></li>' % (COCHE, g) for g in GARANTIES)
    return (
        '<main class="pg">'
        '<section class="pg-sec"><div class="wrap"><div class="devis"><div>'
        '<p class="eyebrow eyebrow--clair">Votre projet</p>'
        '<h1>Demander un devis</h1>'
        '<ul>' + lis + '</ul>'
        '</div><div class="devis__act">'
        # libellé de navigation, ajouté : la page n'en avait pas
        '<a class="btn btn--or btn--bloc" href="#formulaire">Remplir le formulaire</a>'
        '<a class="btn btn--wa btn--bloc" href="https://wa.me/201066619098">'
        'Poser une question sur WhatsApp</a>'
        '<small>Aucune carte bancaire demandée à cette étape.</small>'
        '</div></div></div></section>'
        '<section class="pg-sec pg-sec--fond" id="formulaire">'
        '<div class="wrap sm">'
        '<h2>Votre voyage sur mesure en Égypte</h2>'
        '[wpforms id="%d"]'
        '</div></section>'
        '</main>' % FORMULAIRE)


def batir(ref):
    """La coque de la référence, le corps de /sur-mesure/ entre les deux."""
    i = ref.find('<main class="pg">')
    j = ref.find('<footer class="pied"')
    if i < 0 or j < 0:
        raise SystemExit('coque introuvable dans la référence')
    tete, queue = ref[:i], ref[j:]
    # La coque ne doit rien garder du CORPS de la page dont elle vient.
    # On ne cherche pas des mots : le mega menu cite les destinations, donc
    # « Fayoum » s'y trouve légitimement. On vérifie la structure.
    for marque, n in (('<section', 0), ('<h1', 0), ('<main', 0),
                      ('<header class="entete"', 1), ('<div class="bandeau"', 1)):
        vu = len(re.findall(re.escape(marque) + r'[\s>]', tete))
        if vu != n:
            raise SystemExit('tête de coque : %s vu %d fois, attendu %d'
                             % (marque, vu, n))
    for marque, n in (('<footer class="pied"', 1), ('<section', 0), ('<h1', 0)):
        vu = len(re.findall(re.escape(marque) + r'[\s>]', queue))
        if vu != n:
            raise SystemExit('queue de coque : %s vu %d fois, attendu %d'
                             % (marque, vu, n))
    return tete + corps() + queue + STYLE


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--brouillon', action='store_true',
                   help='écrit dans un brouillon, rien en ligne')
    g.add_argument('--appliquer', action='store_true',
                   help='remplace le contenu de /sur-mesure/ en ligne')
    p.add_argument('--brouillon-id', type=int, default=0)
    a = p.parse_args()

    jours = sorted(j for j in os.listdir(SAUVE) if len(j) == 10 and j[4] == '-')
    D = os.path.join(SAUVE, jours[-1], 'brouillons')
    ref = json.load(open(os.path.join(D, '%d.json' % REFERENCE)))['contenu']
    page = batir(ref)

    print('   coque de #%d · page bâtie : %d octets' % (REFERENCE, len(page)))
    o = len(re.findall(r'<(section|div|main|header|footer|ul|li)[\s>]', page))
    f = len(re.findall(r'</(section|div|main|header|footer|ul|li)>', page))
    print('   balises ouvertes %d · fermées %d %s' % (o, f, '' if o == f else '← ÉCART'))
    for attendu in ('Demander un devis', 'Votre voyage sur mesure en Égypte',
                    '[wpforms id="%d"]' % FORMULAIRE, '<header class="entete"',
                    '<footer class="pied"'):
        print('   %-42s %s' % (attendu[:42], 'présent' if attendu in page else 'ABSENT'))
    print('   en-tête : %d · pied : %d · h1 : %d · h2 : %d'
          % (page.count('<header class="entete"'), page.count('<footer class="pied"'),
             len(re.findall(r'<h1[\s>]', page)), len(re.findall(r'<h2[\s>]', page))))
    chemin = os.path.join(os.environ.get('SP', '/tmp'), 'sur-mesure.html')
    open(chemin, 'w').write(page)
    print('   écrit dans %s' % chemin)
    if a.essai:
        return

    import base64, time, requests
    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'
    charge = {'content': '<!-- wp:html -->\n' + page + '\n<!-- /wp:html -->'}

    if a.brouillon:
        pid = a.brouillon_id
        charge['title'] = 'Refonte · Sur mesure'
        charge['status'] = 'draft'
        r = (S.post(B + 'pages/%d' % pid, json=charge, timeout=300) if pid
             else S.post(B + 'pages', json=charge, timeout=300))
        r.raise_for_status()
        pid = r.json()['id']
        rr = S.get(B + 'pages/%d' % pid, params={'context': 'edit'}, timeout=120).json()
        rendu = (rr.get('content') or {}).get('rendered', '')
        print('\n   brouillon #%d · rendu %d octets · <form %s · champs %d'
              % (pid, len(rendu), '<form' in rendu,
                 len(re.findall(r'wpforms-field-label', rendu))))
        open(os.path.join(os.environ.get('SP', '/tmp'), 'sur-mesure-rendu.html'),
             'w').write(rendu)
        return

    # en ligne : on sauvegarde l'état d'avant, puis on écrit
    av = S.get(B + 'pages/%d' % CIBLE, params={'context': 'edit'}, timeout=120).json()
    d = os.path.join(SAUVE, jours[-1])
    json.dump({'type': 'pages', 'id': CIBLE, 'url': SITE + '/sur-mesure/',
               'modele': av.get('template') or '', 'titre': (av.get('title') or {}).get('raw', ''),
               'slug': av.get('slug'), 'statut': av.get('status'),
               'meta': av.get('meta') or {},
               'contenu': (av.get('content') or {}).get('raw', ''), 'entier': av},
              open(os.path.join(d, 'pages-%d.json' % CIBLE), 'w'), ensure_ascii=False)
    print('\n   état d avant sauvegardé dans %s/pages-%d.json' % (d, CIBLE))

    charge['template'] = 'elementor_canvas'
    for essai in range(4):
        r = S.post(B + 'pages/%d' % CIBLE, json=charge, timeout=300)
        if r.status_code < 300:
            break
        print('      reprise %d/3 — HTTP %d' % (essai + 1, r.status_code))
        time.sleep(2 ** essai)
    else:
        sys.exit('écriture refusée : %s' % r.text[:200])
    # et Elementor doit se taire, sans quoi il rendrait encore ses données
    S.post(B + 'pages/%d' % CIBLE, json={'meta': {'_elementor_edit_mode': ''}},
           timeout=120).raise_for_status()
    ap = S.get(B + 'pages/%d' % CIBLE, params={'context': 'edit'}, timeout=120).json()
    mt = ap.get('meta') or {}
    print('   écrit · gabarit %s · edit_mode %r · données Elementor %d octets (intactes)'
          % (ap.get('template'), mt.get('_elementor_edit_mode'),
             len(mt.get('_elementor_data') or '')))


if __name__ == '__main__':
    main()
