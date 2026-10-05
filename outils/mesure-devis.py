#!/usr/bin/env python3
"""Mesurer le parcours de devis, qui ne l'était pas.

    WP_AUTH='compte:mdp' python3 outils/mesure-devis.py --essai
    WP_AUTH='compte:mdp' python3 outils/mesure-devis.py --appliquer
    WP_AUTH='compte:mdp' python3 outils/mesure-devis.py --retirer

GTM et GA4 sont bien posés sur toutes les pages, y compris celles passées
en Canvas — Site Kit les injecte dans l'en-tête, pas le thème. Mais rien
ne remonte du parcours qui compte : on sait combien de visiteurs arrivent,
pas combien demandent un devis.

Quatre événements, poussés dans le dataLayer, à déclarer ensuite comme
conversions dans GTM :

    ae_devis_relais   le mini-formulaire d'une page séjour est envoyé,
                      avec le nom du séjour et le mois choisi
    ae_devis_envoye   le formulaire WPForms de /sur-mesure/ a confirmé
    ae_whatsapp       un lien WhatsApp est cliqué
    ae_email          une adresse e-mail est cliquée

Le succès de WPForms n'émet pas d'événement propre sans jQuery : on
observe l'apparition de son conteneur de confirmation. Tout est enveloppé
de try/catch — un script de mesure ne doit jamais casser une page.
"""

import argparse
import base64
import json
import os
import time

import requests

SITE = 'https://authentiquegypte.com'
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HORS_JEU = {SITE + '/qui-sommes-nous/'}
MARQUE = 'ae-mesure'

SCRIPT = """<script id="%s">/* Mesure du parcours de devis. Pousse dans le
dataLayer ; les conversions se déclarent ensuite dans GTM. */
(function(){try{
var dl=window.dataLayer=window.dataLayer||[];
function envoyer(nom,donnees){try{dl.push(Object.assign({event:nom},donnees||{}))}catch(e){}}
document.addEventListener('submit',function(e){try{
 var f=e.target;
 if(f&&f.classList&&f.classList.contains('pan__form')){
  var sel=f.querySelector('select[name="periode"]'),nb=f.querySelector('input[name="voyageurs"]');
  envoyer('ae_devis_relais',{sejour:f.getAttribute('data-sejour')||'',
   prix:f.getAttribute('data-prix')||'',periode:sel?sel.value:'',
   voyageurs:nb?nb.value:''});
 }}catch(x){}},true);
document.addEventListener('click',function(e){try{
 var a=e.target&&e.target.closest?e.target.closest('a'):null;
 if(!a||!a.href)return;
 if(a.href.indexOf('wa.me')>-1)envoyer('ae_whatsapp',{depuis:location.pathname});
 else if(a.href.indexOf('mailto:')===0)envoyer('ae_email',{depuis:location.pathname});
}catch(x){}},true);
function guetter(){try{
 if(document.querySelector('.wpforms-confirmation-container')){
  envoyer('ae_devis_envoye',{page:location.pathname});return true}
 return false}catch(x){return false}}
if(!guetter()&&window.MutationObserver){
 var o=new MutationObserver(function(){if(guetter())o.disconnect()});
 try{o.observe(document.body,{childList:true,subtree:true})}catch(x){}}
}catch(e){}})();</script>""" % MARQUE


def retirer(h):
    i = h.find('<script id="%s">' % MARQUE)
    if i < 0:
        return h
    j = h.find('</script>', i)
    return h[:i] + h[j + 9:]


def poser(h):
    h = retirer(h)
    return h + SCRIPT


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument('--essai', action='store_true')
    g.add_argument('--appliquer', action='store_true')
    g.add_argument('--retirer', action='store_true')
    a = p.parse_args()

    S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
    u, m = os.environ['WP_AUTH'].split(':', 1)
    S.headers['Authorization'] = 'Basic ' + base64.b64encode(
        ('%s:%s' % (u, m)).encode()).decode()
    B = SITE + '/wp-json/wp/v2/'
    man = json.load(open(os.path.join(
        RACINE, 'sauvegarde/avant-mise-en-ligne/2026-10-02/MANIFESTE.json')))
    couples = [c for c in man['couples']
               if (c['url'].rstrip('/') + '/') not in HORS_JEU]
    couples.append({'type': 'pages', 'cible': 786, 'url': SITE + '/sur-mesure/'})

    print('script de mesure : %d octets' % len(SCRIPT))
    print('%d page(s) visées' % len(couples))
    if a.essai:
        print(SCRIPT[:400] + ' …')
        return

    n = 0
    for c in couples:
        r = S.get(B + '%s/%d' % (c['type'], c['cible']),
                  params={'context': 'edit'}, timeout=120)
        h = (r.json().get('content') or {}).get('raw', '')
        neuf = retirer(h) if a.retirer else poser(h)
        if neuf == h:
            continue
        for essai in range(4):
            rr = S.post(B + '%s/%d' % (c['type'], c['cible']),
                        json={'content': '<!-- wp:html -->\n' + neuf + '\n<!-- /wp:html -->'},
                        timeout=300)
            if rr.status_code < 300:
                break
            time.sleep(2 ** essai)
        else:
            raise SystemExit('écriture refusée sur %s' % c['url'])
        n += 1
    print('%d page(s) %s.' % (n, 'nettoyées' if a.retirer else 'équipées'))


if __name__ == '__main__':
    main()
