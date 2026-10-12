#!/usr/bin/env python3
"""Le composeur de l'accueil devient une barre de recherche (demande de Rémi, 12 octobre).

    WP_AUTH='compte:mdp' python3 outils/barre-recherche-1210.py --essai [--vers page.html]
    WP_AUTH='compte:mdp' python3 outils/barre-recherche-1210.py --appliquer

Rémi, avec une capture de barre de moteur de voyage : « Pour la section
hero, plus comme ceci. Avec la moitié dans le hero, la moitié en bas : elle
coupe les deux sections. »

Ce qui change :
  - les trois colonnes de pastilles deviennent trois champs côte à côte
    (« Vous partez », « Ce qui vous attire », « Vous avez »), chacun avec son
    libellé et sa valeur (« Indifférent » tant que rien n'est choisi). Un
    clic ouvre les pastilles sous le champ ; plusieurs choix restent
    possibles ; une croix vide le champ ;
  - le bouton devient une loupe ronde, avec le nombre de séjours trouvés
    dès qu'un choix est fait ;
  - la barre est à cheval sur le hero et la section suivante : le hero
    laisse dépasser la moitié de sa hauteur.

Ce qui ne change pas : les pastilles (mêmes boutons, mêmes data-val), le
script de filtrage du composeur, la phrase lue par les lecteurs d'écran
(#phrase) et « Tout effacer » (#raz), gardés hors écran. La sauvegarde du
contenu précédent va dans sauvegarde/avant-mise-en-ligne/<date>/.
"""

import argparse
import datetime
import json
import os
import re

import requests

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
URL = 'https://authentiquegypte.com/wp-json/wp/v2/pages/38'
MARQUE = 'data-retours="12-10-barre"'

# Spécificité : l'accueil empile des règles jusqu'à six fois la classe du gabarit.
B = '.elementor-template-canvas' * 6 + ' '
C = B + '.compo.compo.compo--barre'

CHAMPS = [('qui', 'Vous partez'), ('envie', 'Ce qui vous attire'), ('duree', 'Vous avez')]

CHEVRON = ('<svg class="champ__i" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 9l6 6 6-6" fill="none" '
           'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')
CROIX = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" '
         'stroke-width="2" stroke-linecap="round"/></svg>')
LOUPE = ('<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" '
         'stroke-width="2.4"/><path d="M16.5 16.5L21 21" fill="none" stroke="currentColor" stroke-width="2.4" '
         'stroke-linecap="round"/></svg>')

STYLE = (
    '<style ' + MARQUE + '>'
    # le hero laisse dépasser la barre, et passe devant la section suivante
    + B + '.hero.hero:has(.compo--barre){display:flow-root;overflow:visible;z-index:3;padding-bottom:0}'
    + B + '.hero.hero:has(.compo--barre)+.section{padding-top:calc(88px + var(--deborde,44px))}'
    # plus de photo (Rémi : « l'image du hero plus grosse ») : de l'air au-dessus du titre et sous le texte
    + B + '.hero.hero:has(.compo--barre) .wrap{padding-top:clamp(56px,7vw,96px)}'
    # Rémi : « le paragraphe moins large, sur plusieurs lignes » ; aligné à gauche, il n'est plus justifié
    + B + '.hero.hero:has(.compo--barre) .hero__lede{max-width:34em;text-align:left;hyphens:none}'
    + C + '{--deborde:44px;position:relative;z-index:4;transform:none;margin:clamp(72px,11vw,150px) 0 calc(-1 * var(--deborde));'
    'background:rgba(255,255,255,.94);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);'
    'border-radius:30px;padding:12px;box-shadow:0 18px 44px rgba(6,40,50,.22);color:var(--texte,#3E4650)}'
    + C + ' .cb{display:flex;align-items:center;gap:12px}'
    + C + ' .cb__l{flex:1;display:flex;align-items:stretch;min-width:0;background:#fff;border:1px solid #E1E6EA;'
    'border-radius:999px;box-shadow:0 2px 10px rgba(6,40,50,.06)}'
    # un champ
    + C + ' .champ{position:relative;flex:1 1 0;min-width:0;padding:0;border:0;display:flex;align-items:center}'
    + C + ' .champ+.champ::before{content:"";position:absolute;left:0;top:50%;height:34px;margin-top:-17px;'
    'border-left:1px solid #CFD8DD}'
    + C + ' .champ__btn{flex:1;min-width:0;display:flex;align-items:center;gap:12px;background:none;border:0;'
    'text-align:left;padding:12px 18px 12px 26px;border-radius:999px;cursor:pointer;color:inherit;font:inherit}'
    + C + ' .champ__btn:hover{background:#F3F7F8}'
    + C + ' .champ__btn:focus-visible{outline:2px solid var(--nuit,#147894);outline-offset:-2px}'
    + C + ' .champ__txt{flex:1;min-width:0;display:flex;flex-direction:column;gap:2px}'
    + C + ' .champ__l{font:600 .76rem/1.2 "Manrope",sans-serif;color:#56626B;letter-spacing:.02em;word-spacing:normal}'
    + C + ' .champ__v{font:500 1rem/1.3 "Manrope",sans-serif;color:#6B7680;white-space:nowrap;overflow:hidden;'
    'text-overflow:ellipsis}'
    + C + ' .champ.rempli .champ__v{color:var(--nuit-900,#094D60);font-weight:800}'
    + C + ' .champ__i{width:20px;height:20px;flex:none;color:var(--nuit-900,#094D60);transition:transform .2s}'
    + C + ' .champ.ouvert .champ__i{transform:rotate(180deg)}'
    + C + ' .champ.rempli .champ__i{display:none}'
    + C + ' .champ__x{flex:none;width:34px;height:34px;margin-right:12px;border:0;border-radius:50%;background:none;'
    'color:var(--nuit-900,#094D60);display:grid;place-items:center;cursor:pointer}'
    + C + ' .champ__x[hidden]{display:none}'
    + C + ' .champ__x:hover{background:#EEF3F5}'
    + C + ' .champ__x svg{width:18px;height:18px}'
    # les pastilles du champ
    + C + ' .champ__pop{position:absolute;top:calc(100% + 14px);left:0;z-index:20;width:max(100%,330px);'
    'background:#fff;border-radius:20px;padding:16px 18px;box-shadow:0 20px 50px rgba(6,40,50,.24);'
    'border:1px solid #E1E6EA}'
    + C + ' .champ__pop[hidden]{display:none}'
    + C + ' .champ:last-child .champ__pop{left:auto;right:0}'
    + C + ' .champ__aide{margin:0 0 12px;font:600 .8rem "Manrope",sans-serif;color:#56626B}'
    + C + ' .champ__pop .opts{display:flex;flex-wrap:wrap;gap:8px}'
    + C + ' .champ__pied{display:flex;justify-content:flex-end;margin-top:14px}'
    + C + ' .champ__ok{border:0;border-radius:999px;background:var(--nuit-900,#094D60);color:#fff;'
    'font:700 .85rem "Manrope",sans-serif;padding:9px 20px;cursor:pointer}'
    # la loupe
    + C + ' .cb__go{position:relative;flex:none;width:60px;height:60px;border-radius:50%;background:#ECAA24;'
    'color:#094D60;display:grid;place-items:center;text-decoration:none;transition:background .2s,transform .2s;'
    'box-shadow:0 8px 20px rgba(236,170,36,.35)}'
    + C + ' .cb__go:hover,' + C + ' .cb__go:focus-visible{background:#FFC758;transform:scale(1.04)}'
    + C + ' .cb__go svg{width:26px;height:26px}'
    + C + ' .cb__go-t{display:none}'
    + C + ' .cb__n{position:absolute;top:-6px;right:-6px;min-width:24px;height:24px;padding:0 6px;border-radius:999px;'
    'background:var(--nuit-900,#094D60);color:#fff;font:800 .78rem/24px "Manrope",sans-serif;text-align:center;'
    'border:2px solid #fff}'
    + C + ' .cb__n[hidden]{display:none}'
    + C + ' .compo__res{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;'
    'margin:0;padding:0}'
    # téléphone : les champs l'un sous l'autre, le bouton en toutes lettres
    '@media (max-width:760px){'
    + C + '{--deborde:64px;border-radius:24px;padding:10px;margin-top:48px}'
    + B + '.hero.hero:has(.compo--barre) .wrap{padding-top:40px}'
    + B + '.hero.hero:has(.compo--barre)+.section{padding-top:calc(48px + var(--deborde,64px))}'
    + C + ' .cb{flex-direction:column;align-items:stretch;gap:10px}'
    + C + ' .cb__l{flex-direction:column;border-radius:18px}'
    + C + ' .champ{flex-wrap:wrap}'
    + C + ' .champ+.champ::before{left:18px;right:18px;top:0;height:0;margin:0;border-left:0;border-top:1px solid #E1E6EA}'
    + C + ' .champ__btn{padding:12px 16px 12px 20px;border-radius:18px}'
    + C + ' .champ__pop{position:static;width:100%;box-shadow:none;border:0;border-radius:0;padding:4px 20px 16px}'
    + C + ' .cb__go{width:100%;height:54px;border-radius:999px;display:flex;justify-content:center;gap:10px;'
    'font:800 1rem "Manrope",sans-serif}'
    + C + ' .cb__go-t{display:inline}'
    + C + ' .cb__go svg{width:22px;height:22px}'
    + C + ' .cb__n{position:static;border:0;margin-left:2px}}'
    '@media (prefers-reduced-motion:reduce){' + C + ' *{transition:none!important}}'
    '</style>')

SCRIPT = '''<script>
/* barre de recherche : ouvre les pastilles d'un champ, affiche les choix */
(function(){
  var barre=document.querySelector('.compo--barre'); if(!barre)return;
  var champs=[].slice.call(barre.querySelectorAll('.champ'));
  function fermer(){champs.forEach(function(c){c.classList.remove('ouvert');
    c.querySelector('.champ__btn').setAttribute('aria-expanded','false');c.querySelector('.champ__pop').hidden=true;});}
  function maj(){
    champs.forEach(function(c){
      var sel=[].slice.call(c.querySelectorAll('.opt[aria-pressed="true"]')).map(function(o){return o.textContent.trim();});
      var v=c.querySelector('.champ__v');
      v.textContent=!sel.length?v.getAttribute('data-vide'):sel.length>2?sel.slice(0,2).join(', ')+' +'+(sel.length-2):sel.join(', ');
      c.classList.toggle('rempli',sel.length>0); c.querySelector('.champ__x').hidden=!sel.length;
    });
    var choix=barre.querySelectorAll('.opt[aria-pressed="true"]').length;
    var n=document.querySelectorAll('#liste .carte:not([hidden])').length;
    var badge=barre.querySelector('.cb__n'); badge.hidden=!choix; badge.textContent=n;
    barre.querySelector('.cb__go').setAttribute('aria-label',choix?'Voir les '+n+' séjours qui correspondent':'Voir les séjours');
  }
  champs.forEach(function(c){
    var b=c.querySelector('.champ__btn'),p=c.querySelector('.champ__pop');
    b.addEventListener('click',function(){var ouvrir=p.hidden;fermer();
      if(ouvrir){p.hidden=false;c.classList.add('ouvert');b.setAttribute('aria-expanded','true');}});
    c.querySelector('.champ__ok').addEventListener('click',function(){fermer();b.focus();});
    c.querySelector('.champ__x').addEventListener('click',function(){
      [].slice.call(c.querySelectorAll('.opt[aria-pressed="true"]')).forEach(function(o){o.click();});b.focus();});
  });
  /* après le script du composeur : les clics sur les pastilles l'ont déjà filtré */
  document.addEventListener('click',function(e){if(!barre.contains(e.target))fermer();maj();});
  document.addEventListener('keydown',function(e){if(e.key!=='Escape')return;
    var c=champs.filter(function(c){return c.classList.contains('ouvert');})[0];fermer();
    if(c)c.querySelector('.champ__btn').focus();});
  maj();
})();
</script>'''


def barre(ancien):
    """Le nouveau composeur, avec les pastilles de l'ancien."""
    champs = []
    for cle, lib in CHAMPS:
        m = re.search(r'<div class="champ" data-filtre="%s"><span>[^<]*</span>(<div class="opts">.*?</div>)</div>'
                      % cle, ancien, re.S)
        if not m:
            raise SystemExit('Champ introuvable : ' + cle)
        champs.append(
            '<div class="champ" data-filtre="%s"><button type="button" class="champ__btn" aria-expanded="false" '
            'aria-controls="cb-%s"><span class="champ__txt"><span class="champ__l">%s</span><span class="champ__v" '
            'data-vide="Indifférent">Indifférent</span></span>%s</button><button type="button" class="champ__x" '
            'aria-label="Effacer : %s" hidden>%s</button><div class="champ__pop" id="cb-%s" hidden>'
            '<p class="champ__aide">Plusieurs choix possibles</p>%s<div class="champ__pied"><button type="button" '
            'class="champ__ok">OK</button></div></div></div>'
            % (cle, cle, lib, CHEVRON, lib.lower(), CROIX, cle, m.group(1)))
    return ('<div class="compo compo--barre" role="search" aria-label="Composer votre voyage"><div class="cb">'
            '<div class="cb__l">%s</div><a href="#resultats" class="cb__go" aria-label="Voir les séjours">%s'
            '<span class="cb__go-t">Voir les séjours</span><span class="cb__n" hidden></span></a></div>'
            '<div class="compo__res"><p class="compo__phrase" id="phrase" role="status" aria-live="polite"></p>'
            '<div class="compo__act"><button type="button" id="raz">Tout effacer</button></div></div></div>%s'
            % (''.join(champs), LOUPE, SCRIPT))


def transformer(h):
    d = h.find('<div class="compo">')
    if d < 0:
        raise SystemExit('Composeur introuvable')
    f = h.find('</div></section>', d)
    ancien = h[d:f]
    if not ancien.endswith('</a></div></div></div>'):
        raise SystemExit('Fin du composeur inattendue')
    h = h[:d] + barre(ancien) + h[f:]
    i = h.find('<main')
    i = h.find('>', i) + 1
    return h[:i] + STYLE + h[i:]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--essai', action='store_true')
    p.add_argument('--appliquer', action='store_true')
    p.add_argument('--vers')
    a = p.parse_args()
    s = requests.Session()
    s.verify = '/root/.ccr/ca-bundle.crt'
    s.auth = tuple(os.environ['WP_AUTH'].split(':', 1))
    d = s.get(URL, params={'context': 'edit'}, timeout=300).json()
    h = d['content']['raw']
    if MARQUE in h:
        # déjà en place : on ne remet que la feuille de style
        h2 = re.sub(r'<style ' + MARQUE + r'>.*?</style>', lambda m: STYLE, h, count=1, flags=re.S)
        print('feuille de style', 'à jour' if h2 == h else 'remplacée')
        if a.appliquer and h2 != h:
            print('écrit :', s.post(URL, json={'content': h2}, timeout=600).status_code)
        return
    h2 = transformer(h)
    print('composeur → barre de recherche (%+d caractères)' % (len(h2) - len(h)))
    if a.vers:
        open(a.vers, 'w', encoding='utf-8').write(h2)
    if not a.appliquer:
        return
    dos = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne', datetime.date.today().isoformat())
    os.makedirs(dos, exist_ok=True)
    f = os.path.join(dos, 'pages-38-avant-barre.json')
    json.dump({'contenu': h}, open(f, 'w'), ensure_ascii=False)
    print('sauvegardé :', os.path.relpath(f, RACINE))
    print('écrit :', s.post(URL, json={'content': h2}, timeout=600).status_code)


if __name__ == '__main__':
    main()
