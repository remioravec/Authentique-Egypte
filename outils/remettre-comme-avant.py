#!/usr/bin/env python3
"""Remettre une cible dans son état d'avant la bascule, et elle seule.

    WP_AUTH='compte:mot de passe' python3 outils/remettre-comme-avant.py pages 105

Trois gestes, dans cet ordre — l'ordre compte : si on rendait la main à
Elementor avant d'avoir remis le gabarit, la page passerait un instant par
un état où elle rend ses anciennes données sans en-tête.

  1. le contenu et le gabarit, repris de la sauvegarde du jour ;
  2. `_elementor_edit_mode` remis à builder, pour qu'Elementor reprenne la
     main sur l'affichage (ses `_elementor_data` n'ont jamais été touchées) ;
  3. relecture : on vérifie en ligne que la page rend bien ce qu'elle rendait.

On ne touche ni au titre, ni au slug, ni aux méta Yoast.
"""
import base64, json, os, re, sys, time, gzip, urllib.request
import requests

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://authentiquegypte.com'
SAUVE = os.path.join(RACINE, 'sauvegarde', 'avant-mise-en-ligne')

typ, pid = sys.argv[1], int(sys.argv[2])
jours = sorted(j for j in os.listdir(SAUVE) if len(j) == 10 and j[4] == '-')
d = os.path.join(SAUVE, jours[-1])
s = json.load(open(os.path.join(d, '%s-%d.json' % (typ, pid))))
if not s.get('contenu'):
    sys.exit('Sauvegarde vide pour %s #%d : je ne touche à rien.' % (typ, pid))

S = requests.Session(); S.verify = '/root/.ccr/ca-bundle.crt'
u, m = os.environ['WP_AUTH'].split(':', 1)
S.headers['Authorization'] = 'Basic ' + base64.b64encode(('%s:%s' % (u, m)).encode()).decode()
B = SITE + '/wp-json/wp/v2/'

def lire():
    r = S.get(B + '%s/%d' % (typ, pid), params={'context': 'edit'}, timeout=90)
    x = r.json(); mt = x.get('meta') or {}
    dat = mt.get('_elementor_data')
    return {'modele': x.get('template') or '(défaut)',
            'edit_mode': mt.get('_elementor_edit_mode'),
            'data': len(dat) if isinstance(dat, str) else 0,
            'contenu': len((x.get('content') or {}).get('raw', ''))}

def ecrire(charge):
    for essai in range(4):
        r = S.post(B + '%s/%d' % (typ, pid), json=charge, timeout=180)
        if r.status_code < 300:
            return
        print('   reprise %d/3 — HTTP %d' % (essai + 1, r.status_code))
        time.sleep(2 ** essai)
    sys.exit('Écriture refusée : %s' % r.text[:200])

print('sauvegarde du %s · %s #%d · %s' % (jours[-1], typ, pid, s['url']))
print('avant :', lire())
ecrire({'content': s['contenu'], 'template': s['modele']})
ecrire({'meta': {'_elementor_edit_mode': 'builder'}})
print('après :', lire())

q = urllib.request.Request(s['url'] + '?cb=%d' % time.time(),
                           headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'})
r = urllib.request.urlopen(q, timeout=90); b = r.read()
if r.headers.get('Content-Encoding') == 'gzip': b = gzip.decompress(b)
h = b.decode('utf-8', 'replace'); bas = h.lower()
print('en ligne : %d Ko · vieil Elementor %s · masthead %d · header refonte %d · h1 « %s »'
      % (len(h) // 1024,
         'data-elementor-type="wp-page"' in bas or 'data-elementor-type="wp-post"' in bas,
         bas.count('id="masthead"'), bas.count('<header class="entete"'),
         re.sub(r'<[^>]+>', '', (re.search(r'<h1[^>]*>(.*?)</h1>', h, re.S) or [None, ''])[1]).strip()[:60]))
