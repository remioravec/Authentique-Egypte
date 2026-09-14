#!/usr/bin/env python3
"""Construit la version « après » de la page programme Siwa : la page
actuelle, plus les blocs confiance / UX / UI proposés le 14/09.
Chaque bloc ne porte que des faits relevés sur le site en ligne
(qui-sommes-nous, quand-partir, FAQ de la page) ; ce qui manque est
marqué « à remplir »."""
import re, sys, html as H

src, dst = sys.argv[1], sys.argv[2]
h = open(src, encoding='utf-8').read()
LIVE = 'https://authentiquegypte.com/programs/excursion-a-loasis-de-siwa/'
QUI = 'https://authentiquegypte.com/qui-sommes-nous/'
GOOGLE = 'https://search.google.com/local/reviews?placeid=ChIJOZOsXzk5WBQRMujsdlYsBy8'
WA = 'https://wa.me/201066619098'
import os
_ici = os.path.dirname(os.path.abspath(__file__))
PHOTO = open(os.path.join(_ici, 'melanie-640.b64'), encoding='ascii').read().strip()
AVATAR = open(os.path.join(_ici, 'melanie-96.b64'), encoding='ascii').read().strip()

def une(pat, rep, flags=0, n=1):
    global h
    m = re.findall(pat, h, flags)
    assert len(m) == n, ('ancre', pat[:60], len(m))
    h = re.sub(pat, rep, h, flags=flags)

def ico(d, s=16):
    return ('<svg aria-hidden="true" width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">%s</svg>' % (s, s, d))
I = {
    'check': ico('<path d="M5 12l4.5 4.5L19 7"/>'),
    'home': ico('<path d="M4 11l8-7 8 7v9H4z"/><path d="M10 20v-6h4v6"/>'),
    'car': ico('<path d="M5 11l1.5-4.5A2 2 0 0 1 8.4 5h7.2a2 2 0 0 1 1.9 1.5L19 11M4 11h16v6h-2a2 2 0 1 1-4 0H10a2 2 0 1 1-4 0H4z"/>'),
    'sun': ico('<circle cx="12" cy="12" r="4"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>'),
    'walk': ico('<path d="M4 20c4-1 5-6 5-6l3-9 3 9s1 5 5 6"/><path d="M9 14h6"/>'),
    'land': ico('<path d="M3 21h18M5 21V10l7-6 7 6v11M10 21v-5h4v5"/>'),
    'user': ico('<circle cx="12" cy="8" r="3.5"/><path d="M5 20a7 7 0 0 1 14 0"/>'),
    'shield': ico('<path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6z"/><path d="M9 12l2 2 4-4"/>'),
    'phone': ico('<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>'),
    'card': ico('<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18"/>'),
    'cal': ico('<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
    'chat': ico('<path d="M4 6a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H9l-5 4z"/>'),
    'mail': ico('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>'),
    'link': ico('<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>'),
    'cam': ico('<path d="M4 8h3l2-3h6l2 3h3v11H4z"/><circle cx="12" cy="13" r="3.5"/>', 22),
    'pin': ico('<path d="M12 21s-6-5.5-6-11a6 6 0 0 1 12 0c0 5.5-6 11-6 11z"/><circle cx="12" cy="10" r="2.5"/>'),
}

# ---------------------------------------------------------------- ancres de section
une(r'<h2>Vue d&#x27;ensemble</h2>', '<h2 id="t-vue">Vue d&#x27;ensemble</h2>')
une(r'<h2>Le séjour jour par jour</h2>', '<h2 id="t-jpj">Le séjour jour par jour</h2>')
une(r'<h2>Tarif par personne</h2>', '<h2 id="t-tarif">Tarif par personne</h2>')
une(r'<h2>Les questions qui reviennent avant de partir</h2>', '<h2 id="t-faq">Les questions qui reviennent avant de partir</h2>')

# ---------------------------------------------------------------- héros : ligne de réassurance
une(r'(Poser une question sur WhatsApp</a></div>)(\s*</div></div></div></section>)',
    r'\1 <p class="hero__conf">' + I['check'] + ' Devis gratuit sous 48 h ' + I['check'] +
    ' Aucune carte bancaire à cette étape ' + I['check'] + r' Équipe au Caire, assistance 24h/24</p>\2')

# ---------------------------------------------------------------- panneau devis
MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']
opts = '<option value="">Je ne sais pas encore</option>' + ''.join('<option>%s</option>' % m.capitalize() for m in MOIS)
form = (
    '<ul class="pan__inclus">' + ''.join('<li>' + I['check'] + '<span>%s</span></li>' % x for x in ('Guide privatif', 'Chauffeur privatif', 'Transferts en 4x4 climatisé', 'Assistance H24')) + '</ul>'
    '<div class="pan__qui"><img class="pan__av" src="' + AVATAR + '" alt="" width="36" height="36"><span><b>Mélanie vous répond</b>'
    '<small>sous 48 h, hors vendredi et samedi</small></span></div>'
    '<form class="pan__form" action="https://authentiquegypte.com/sur-mesure/" method="get" data-devis>'
    '<select aria-label="Période souhaitée"><option value="">Quand partir ?</option>' + ''.join('<option>%s</option>' % m.capitalize() for m in MOIS) + '</select>'
    '<input type="number" min="1" max="12" placeholder="Voyageurs" aria-label="Nombre de voyageurs">'
    '<input class="pan__l2" type="text" placeholder="Vos envies (facultatif)" aria-label="Vos envies">'
    '<button class="btn btn--or btn--bloc" type="submit">Recevoir mon devis</button>'
    '</form>'
    '<p class="pan__note">Aucune carte bancaire à cette étape</p>'
    '<a class="pan__wa" href="' + WA + '">' + I['chat'] + ' Une question ? WhatsApp</a>'
)
une(r'<div class="pan__act">.*?</div>', form, flags=re.S)
gar = ('<ul class="pan__gar"><li>' + I['shield'] + '<span>Enregistrée en France</span></li>'
       '<li>' + I['shield'] + '<span>Licence en Égypte</span></li>'
       '<li>' + I['phone'] + '<span>Assistance 24h/24</span></li></ul>')
une(r'<p class="pan__note">Réponse sous 48 h, hors vendredi et samedi<br>Aucune carte bancaire demandée à cette étape.</p>', gar)
une(r'<p class="pan__avis">.*?</p>',
    '<p class="pan__avis"><a href="' + GOOGLE + '" target="_blank" rel="noopener"><svg class="gg" aria-hidden="true" width="16" height="16" viewBox="0 0 48 48"><path fill="#4285F4" d="M45.12 24.5c0-1.56-.14-3.06-.4-4.5H24v8.51h11.84c-.51 2.75-2.06 5.08-4.39 6.64v5.52h7.11c4.16-3.83 6.56-9.47 6.56-16.17z"/><path fill="#34A853" d="M24 46c5.94 0 10.92-1.97 14.56-5.33l-7.11-5.52c-1.97 1.32-4.49 2.1-7.45 2.1-5.73 0-10.58-3.87-12.31-9.07H4.34v5.7C7.96 41.07 15.4 46 24 46z"/><path fill="#FBBC05" d="M11.69 28.18C11.25 26.86 11 25.45 11 24s.25-2.86.69-4.18v-5.7H4.34C2.85 17.09 2 20.45 2 24c0 3.55.85 6.91 2.34 9.88l7.35-5.7z"/><path fill="#EA4335" d="M24 10.75c3.23 0 6.13 1.11 8.41 3.29l6.31-6.31C34.91 4.18 29.93 2 24 2 15.4 2 7.96 6.93 4.34 14.12l7.35 5.7c1.73-5.2 6.58-9.07 12.31-9.07z"/></svg><b>23 avis Google</b></a>'
    '<span class="pan__part"><span>Partager</span>'
    '<a href="https://wa.me/?text=' + H.escape('Voyage à l’Oasis de Siwa avec Authentique Égypte : ' + LIVE) + '" target="_blank" rel="noopener" aria-label="Partager sur WhatsApp" title="WhatsApp">' + I['chat'] + '</a>'
    '<a href="mailto:?subject=' + H.escape('Voyage à l’Oasis de Siwa') + '&amp;body=' + H.escape('Regarde ce programme : ' + LIVE) + '" aria-label="Partager par e-mail" title="E-mail">' + I['mail'] + '</a>'
    '<button type="button" data-copier="' + LIVE + '" aria-label="Copier le lien" title="Copier le lien">' + I['link'] + '</button></span></p>', flags=re.S)

# ---------------------------------------------------------------- navigation collante par sections
une(r'<nav class="somm"',
    '<nav class="pg-anc" aria-label="Sections de la page"><a href="#t-vue">Vue d&#x27;ensemble</a><a href="#t-quand">Quand partir</a>'
    '<a href="#t-jpj">Jour par jour</a><a href="#t-tarif">Tarif</a><a href="#t-faq">Questions</a></nav><nav class="somm"')

# ---------------------------------------------------------------- pictos sur les étapes
def picto(m):
    t = m.group(2).lower()
    k = ('home' if 'arriv' in t or 'retour' in t or 'guesthouse' in t or 'hôte' in t else
         'sun' if 'lever' in t or 'coucher' in t else
         'walk' if 'ascension' in t or 'descente' in t or 'marche' in t else
         'land' if 'visite' in t or 'monast' in t or 'temple' in t else 'car')
    return m.group(1) + '<span class="ic">' + I[k] + '</span><span class="t">' + m.group(2) + '</span>'
h = re.sub(r'(<li><span class="n">J\d+</span>)<span class="t">([^<]+)</span>', picto, h)

# ---------------------------------------------------------------- carte cliquable
une(r'(<figcaption class="carte__tete"><h3>Le trajet, étape par étape</h3><p class="eyebrow">Où vous allez</p>)',
    r'\1<p class="carte__aide">' + I['pin'] + ' Cliquez une étape sur la carte pour lire la journée.</p>')

# ---------------------------------------------------------------- tarif : conditions au même endroit
cond = ('<div class="tarif__cond">'
        '<article><h3>' + I['card'] + 'Paiement</h3><p>Virement bancaire ou carte bancaire via un lien sécurisé. Un acompte à la validation, le solde 45 jours avant le départ.</p></article>'
        '<article><h3>' + I['cal'] + 'Annulation</h3><p>Nous faisons tout pour reprogrammer ou adapter votre voyage. Des frais peuvent s’appliquer selon le délai d’annulation. Une assurance voyage est conseillée.</p></article>'
        '<article><h3>' + I['user'] + 'Pourquoi ce prix</h3><p>Ce séjour est privatif : vous ne partagez ni le guide, ni le véhicule. Le devis est gratuit et sans engagement, aucune carte bancaire n’est demandée à cette étape.</p></article>'
        '</div><p class="tarif__lien"><a href="#t-faq">Le détail, question par question</a></p>')
une(r'(<b>595 € <small>/ Personne</small></b></div></div>)(</section>)', r'\1' + cond + r'\2')

# ---------------------------------------------------------------- quand partir (relevé sur quand-partir-en-egypte)
QUAND = [('janv.', '15-22', 'excellent, doux', 'faible'), ('févr.', '16-24', 'excellent', 'faible'),
         ('mars', '19-27', 'très bon, début de saison', 'modérée'), ('avril', '23-32', 'chaud mais supportable', 'forte (vacances)'),
         ('mai', '26-36', 'chaud', 'modérée'), ('juin', '29-39', 'très chaud', 'faible'),
         ('juil.', '31-41', 'caniculaire, éviter', 'faible'), ('août', '30-40', 'caniculaire', 'faible'),
         ('sept.', '27-37', 'encore chaud', 'modérée'), ('oct.', '24-32', 'très bon', 'forte (vacances)'),
         ('nov.', '20-28', 'excellent, idéal', 'faible'), ('déc.', '17-25', 'très bon', 'forte (vacances)')]
def niveau(c):
    return 'q-1' if 'excellent' in c or 'très bon' in c else 'q-3' if 'canic' in c or 'très chaud' in c else 'q-2'
cells = ''.join('<li class="%s%s"><b>%s</b><span class="q-t">%s °C</span><span class="q-c">%s</span><small>affluence %s</small></li>'
                % (niveau(c), ' q-ok' if i in (9, 10, 11, 0, 1, 2) else '', m, t, c, a) for i, (m, t, c, a) in enumerate(QUAND))
quand = ('<section class="quand" id="s-quand"><p class="eyebrow">La bonne période</p><h2 id="t-quand">Quand partir à Siwa ?</h2>'
         '<p class="quand__intro">Pour l’exploration du désert, la période conseillée va <b>d’octobre à mars</b> : journées supportables, nuits fraîches. '
         'Janvier, février et novembre sont les mois les plus calmes.</p>'
         '<ol class="quand__frise">' + cells + '</ol>'
         '<p class="quand__leg"><span class="q-1">conseillé</span><span class="q-2">chaud</span><span class="q-3">à éviter</span>'
         '<span class="q-src">Températures et affluence relevées sur <a href="https://authentiquegypte.com/quand-partir-en-egypte/">notre guide quand partir</a>.</span></p></section>')
i = h.find('<section class="mod mod--duree">'); j = h.find('</section>', i) + len('</section>')
assert i > 0
h = h[:j] + quand + h[j:]

# ---------------------------------------------------------------- qui vous répond + garanties + presse + photos voyageurs
equipe = ('<section class="pg-sec equipe" id="s-equipe"><div class="wrap">'
          '<p class="eyebrow">L’agence</p><h2 id="t-equipe">Qui vous répond</h2>'
          '<div class="equipe__portrait">'
          '<div class="equipe__photo"><img src="' + PHOTO + '" alt="Mélanie, fondatrice d’Authentique Égypte" width="640" height="800"></div>'
          '<div class="equipe__txt"><p class="equipe__cit">« Une aventure née d’un regard curieux sur l’Égypte authentique »</p>'
          '<h3>Mélanie, fondatrice</h3>'
          '<p>Tombée sous le charme de l’Égypte lors d’un premier voyage, elle s’est entourée de professionnels égyptiens passionnés. Structure franco-égyptienne, équipe au Caire.</p>'
          '<a class="btn btn--fantome btn--sm" href="' + QUI + '">Notre histoire</a></div>'
          '</div>'
          '<ul class="equipe__tuiles">'
          '<li>' + I['user'] + '<b>Guides certifiés</b><span>évalués régulièrement</span></li>'
          '<li>' + I['phone'] + '<b>Assistance 24h/24</b><span>un représentant local</span></li>'
          '<li>' + I['shield'] + '<b>Enregistrée en France</b><span class="aremplir">n° à fournir</span></li>'
          '<li>' + I['shield'] + '<b>Licence en Égypte</b><span>partenaire officiel</span></li>'
          '<li>' + I['card'] + '<b>Paiement sécurisé</b><span>remboursement selon CGV</span></li>'
          '</ul>'
          '<div class="equipe__sur">' + I['shield'] + '<p><b>Est-ce dangereux de venir en Égypte ?</b> Venir en Égypte est tout à fait sûr : les zones touristiques majeures sont très bien sécurisées. <a href="#t-faq">Lire la réponse</a></p></div>'
          '<div class="equipe__bas">'
          '<div class="presse"><p class="eyebrow">Ils parlent de nous</p><ul><li><span>Le Figaro</span></li><li><span>Le Figaro Madame</span></li><li><span>Marie Claire</span></li><li><span>Partir.com</span></li><li><span>Evaneos</span></li><li><span>TripAdvisor</span></li></ul></div>'
          '<div class="voyageurs"><p class="eyebrow">Ils sont partis avec nous <span class="aremplir">photos à collecter</span></p>'
          '<ul>' + ''.join('<li>' + I['cam'] + '<span>Prénom, mois</span></li>' for _ in range(4)) + '</ul></div>'
          '</div>'
          '</div></section>')
i = h.find('<section class="pg-sec pg-sec--nuit">'); j = h.find('</section>', i) + len('</section>')
assert i > 0
h = h[:j] + equipe + h[j:]

# ---------------------------------------------------------------- avis reliés à la fiche Google
une(r'(<p class="mur__cpt"><b>23 avis Google sur l&#x27;agence</b><small>Relevé sur la fiche le 10 septembre 2026</small></p>)',
    r'\1<a class="mur__lien btn btn--fantome btn--sm" href="' + GOOGLE + '" target="_blank" rel="noopener">Voir les avis sur Google</a>')

# ---------------------------------------------------------------- styles + script
CSS = r'''
<style id="apres">
/* ===== blocs proposés le 14/09 : confiance, UX, UI ===== */
.pg .aremplir{display:inline-block;background:var(--or-fond);border:1px dashed var(--or);color:#7A5605;font-size:.8rem;line-height:1.4;padding:.15em .55em;border-radius:6px;font-weight:700;font-family:"Manrope",sans-serif;letter-spacing:0;vertical-align:middle}
.pg .hero__conf{display:flex;flex-wrap:wrap;gap:6px 18px;margin:16px 0 0;font-family:"Manrope",sans-serif;font-size:.9rem;color:#fff}
.pg .hero__conf svg{vertical-align:-3px;color:var(--or);margin-right:2px}
.pg .pan__qui{display:flex;gap:12px;align-items:center;margin:0 0 14px;padding:0 0 14px;border-bottom:1px solid var(--ligne-2)}
.pg .pan__av{width:44px;height:44px;border-radius:50%;background:var(--nuit-900);color:var(--or);display:grid;place-items:center;font-family:"Archivo",serif;font-weight:700;font-size:1.3rem;flex:0 0 auto}
.pg .pan__qui b{display:block;font-family:"Manrope",sans-serif;font-weight:700;color:var(--noir);font-size:.98rem}
.pg .pan__qui small{display:block;font-family:"Manrope",sans-serif;font-size:.82rem;color:var(--gris-lis);line-height:1.4}
.pg .pan__form{display:grid;grid-template-columns:1fr 1fr;gap:10px;font-family:"Manrope",sans-serif}
.pg .pan__form label{display:grid;gap:4px;font-size:.8rem;font-weight:700;color:var(--gris-lis);letter-spacing:.02em}
.pg .pan__form .pan__l2,.pg .pan__form button{grid-column:1/-1}
.pg .pan__form select,.pg .pan__form input,.pg .pan__form textarea{font:inherit;font-weight:500;font-size:.95rem;color:var(--noir);padding:10px 12px;border:1px solid var(--ligne-pg);border-radius:var(--r-s);background:#fff;min-height:44px;width:100%}
.pg .pan__form textarea{resize:vertical;min-height:58px}
.pg .pan__form :is(select,input,textarea):focus-visible{outline:2px solid var(--teal-txt);outline-offset:1px}
.pg .pan__alt{margin:10px 0 0;text-align:center;font-family:"Manrope",sans-serif;font-size:.9rem;color:var(--gris-lis)}
.pg .pan__alt a{color:var(--teal-txt);font-weight:700;text-decoration:underline;text-underline-offset:3px}
.pg .pan__alt svg{vertical-align:-3px}
.pg .pan__gar{list-style:none;margin:12px 0 0;padding:12px 0 0;border-top:1px solid var(--ligne-2);display:grid;gap:7px;font-family:"Manrope",sans-serif;font-size:.86rem;color:var(--nuit-900)}
.pg .pan__gar li{display:flex;gap:9px;align-items:flex-start;line-height:1.4}
.pg .pan__gar svg{flex:0 0 auto;color:var(--teal-txt);margin-top:2px}
.pg .pan__avis a{color:inherit;text-decoration:underline;text-underline-offset:3px}
.pg .pan__part{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin:12px 0 0;padding:12px 0 0;border-top:1px solid var(--ligne-2);font-family:"Manrope",sans-serif;font-size:.82rem;color:var(--gris-lis)}
.pg .pan__part>span{flex:1 1 100%;font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:.72rem}
.pg .pan__part a,.pg .pan__part button{display:inline-flex;align-items:center;gap:5px;min-height:36px;padding:0 11px;border-radius:var(--r-pill);border:1px solid var(--ligne-pg);background:#fff;color:var(--nuit-900);font:inherit;font-weight:600;cursor:pointer}
.pg .pan__part a:hover,.pg .pan__part button:hover{border-color:var(--nuit)}
.pg .pan__part button.ok{background:var(--vert-fond);border-color:var(--vert);color:var(--vert)}
.pg .pg-anc{display:flex;flex-wrap:wrap;gap:6px;font-family:"Manrope",sans-serif;font-size:.82rem}
.pg .pg-anc a{padding:7px 11px;border-radius:var(--r-pill);border:1px solid var(--ligne-pg);background:#fff;color:var(--nuit-900);font-weight:600;min-height:34px;display:inline-flex;align-items:center}
.pg .pg-anc a.vu{background:var(--nuit-900);color:#fff;border-color:var(--nuit-900)}
.pg .apercu li .ic{width:30px;height:30px;border-radius:50%;background:#fff;color:var(--teal-txt);display:grid;place-items:center;flex:0 0 auto;align-self:center;border:1px solid #CDE9EA}
.pg .carte__aide{margin:6px 0 0;font-family:"Manrope",sans-serif;font-size:.86rem;color:var(--teal-txt);font-weight:600}
.pg .carte__aide svg{vertical-align:-3px}
.pg .carte__pt{cursor:pointer}
.pg .carte__pt:hover circle{stroke:var(--or);stroke-width:3}
.pg .etape--vise{outline:3px solid var(--or);outline-offset:8px;border-radius:var(--r-m);transition:outline-color 1.2s}
.pg .etape--vise.fin{outline-color:transparent}
.pg .tarif__cond{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:22px 0 0}
.pg .tarif__cond article{background:var(--fond-2);border:1px solid var(--ligne-pg);border-radius:var(--r-m);padding:18px 20px}
.pg .tarif__cond h3{display:flex;gap:9px;align-items:center;font-size:1rem;margin:0 0 8px;color:var(--nuit-900)}
.pg .tarif__cond h3 svg{color:var(--teal-txt)}
.pg .tarif__cond p{margin:0;font-size:.97rem;line-height:1.6;color:var(--texte)}
.pg .tarif__lien{margin:12px 0 0;font-family:"Manrope",sans-serif;font-size:.92rem}
.pg .tarif__lien a{color:var(--teal-txt);font-weight:700;text-decoration:underline;text-underline-offset:3px}
.pg .quand{margin:0}
.pg .quand__intro{font-size:1.06rem;color:var(--texte);margin:0 0 18px}
.pg .quand__intro b{color:var(--nuit-900)}
.pg .quand__frise{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(12,1fr);gap:4px}
.pg .quand__frise li{display:grid;gap:3px;padding:10px 6px;border-radius:var(--r-s);text-align:center;font-family:"Manrope",sans-serif;background:var(--fond);border:1px solid var(--ligne-pg);min-width:0}
.pg .quand__frise b{font-size:.86rem;color:var(--noir)}
.pg .quand__frise .q-t{font-size:.8rem;font-weight:700;color:var(--nuit-900);white-space:nowrap}
.pg .quand__frise .q-c{font-size:.72rem;line-height:1.25;color:var(--gris-lis)}
.pg .quand__frise small{font-size:.66rem;color:var(--gris-clair);line-height:1.2}
.pg .quand__frise .q-1{background:var(--teal-fond);border-color:#CDE9EA}
.pg .quand__frise .q-2{background:var(--or-fond);border-color:#F5D9B0}
.pg .quand__frise .q-3{background:var(--rouge-fond);border-color:#F0C9BE}
.pg .quand__frise .q-ok{box-shadow:inset 0 -3px 0 var(--teal)}
.pg .quand__leg{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;margin:12px 0 0;font-family:"Manrope",sans-serif;font-size:.8rem;color:var(--gris-lis)}
.pg .quand__leg span:not(.q-src){padding:3px 10px;border-radius:var(--r-pill);border:1px solid var(--ligne-pg)}
.pg .quand__leg .q-1{background:var(--teal-fond)}.pg .quand__leg .q-2{background:var(--or-fond)}.pg .quand__leg .q-3{background:var(--rouge-fond)}
.pg .quand__leg .q-src a{color:var(--teal-txt);text-decoration:underline;text-underline-offset:2px}
.pg .equipe{background:var(--fond-2);border-top:1px solid var(--ligne-pg);border-bottom:1px solid var(--ligne-pg);padding:clamp(48px,6vw,80px) 0}
.pg .equipe__g{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin:8px 0 0}
.pg .equipe__c{background:#fff;border:1px solid var(--ligne-pg);border-radius:var(--r-l);padding:26px 26px 24px;display:flex;flex-direction:column;gap:12px}
.pg .equipe__c h3{margin:0;font-size:1.15rem}
.pg .equipe__c p{margin:0;font-size:1rem;line-height:1.65;color:var(--texte)}
.pg .equipe__c ul{list-style:none;margin:0;padding:0;display:grid;gap:9px}
.pg .equipe__c li{display:flex;gap:9px;align-items:flex-start;font-size:.97rem;line-height:1.5;color:var(--texte)}
.pg .equipe__c li svg{flex:0 0 auto;color:var(--teal-txt);margin-top:4px}
.pg .equipe__c .lien-fl{margin-top:auto}
.pg .equipe__av{position:relative;width:64px;height:64px;border-radius:50%;background:var(--nuit-900);color:var(--or);display:grid;place-items:center;font-family:"Archivo",serif;font-weight:700;font-size:1.7rem}
.pg .equipe__av .aremplir{position:absolute;left:72px;top:50%;transform:translateY(-50%);white-space:nowrap}
.pg .equipe__av--eq{background:var(--teal-fond);color:var(--teal-txt)}
.pg .equipe__av--eq svg{width:26px;height:26px}
.pg .equipe__num{margin:4px 0 0}
.pg .equipe__sur{display:grid;grid-template-columns:1.2fr 1fr;gap:22px;margin:22px 0 0;background:var(--nuit-900);color:#DCE6EA;border-radius:var(--r-l);padding:28px 30px}
.pg .equipe__sur h3{color:#fff;margin:0 0 8px;font-size:1.15rem}
.pg .equipe__sur p{margin:0;font-size:1rem;line-height:1.65;color:#C9DDE7}
.pg .equipe__sur a{color:var(--or-clair);font-weight:700;text-decoration:underline;text-underline-offset:3px}
.pg .equipe__sur .eyebrow{color:var(--or-clair)}
.pg .presse{margin:26px 0 0;display:flex;flex-wrap:wrap;gap:10px 28px;align-items:center}
.pg .presse .eyebrow{margin:0}
.pg .presse ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:8px 26px}
.pg .presse li{font-family:"Archivo",serif;font-weight:600;font-size:1.15rem;letter-spacing:-.3px;color:var(--gris-lis)}
.pg .voyageurs{display:grid;grid-template-columns:1fr 1.4fr;gap:24px;align-items:center;margin:28px 0 0}
.pg .voyageurs h3{margin:0 0 8px;font-size:1.15rem}
.pg .voyageurs p{margin:0;font-size:.98rem;color:var(--texte)}
.pg .voyageurs ul{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
.pg .voyageurs li{aspect-ratio:4/5;border:2px dashed #CDE9EA;border-radius:var(--r-m);background:#fff;display:grid;place-content:center;gap:6px;text-align:center;color:var(--teal-txt);font-family:"Manrope",sans-serif;font-size:.78rem;font-weight:600}
.pg .voyageurs li svg{margin:0 auto}
.pg .mur__lien{align-self:center}
@media (max-width:1040px){.pg .pan{position:static}.pg .tarif__cond{grid-template-columns:1fr}.pg .equipe__g{grid-template-columns:1fr}.pg .equipe__sur{grid-template-columns:1fr}.pg .voyageurs{grid-template-columns:1fr}
  .pg .quand__frise{grid-template-columns:repeat(6,1fr)}}
@media (max-width:600px){.pg .pan__form{grid-template-columns:1fr}.pg .quand__frise{grid-template-columns:repeat(3,1fr)}.pg .voyageurs ul{grid-template-columns:repeat(2,1fr)}
  .pg .hero__conf{font-size:.94rem}.pg .quand__frise .q-c,.pg .quand__frise small,.pg .pan__part,.pg .pan__gar,.pg .pg-anc{font-size:.9rem}
  .pg .equipe__av .aremplir{position:static;transform:none;margin-left:8px}}
/* Le côté est collant en entier et tient dans la fenêtre : pas de défilement interne.
   Les cinq repères (durée, rythme, transport, guide, hébergement) sont déjà dans la
   bande sous le héros, le panneau ne les répète plus. */
.pg .pan{position:sticky;top:84px;gap:8px}
.pg .pan__carte{padding:16px 18px}
.pg .pan__liste{display:none}
.pg .pan__prix{line-height:1.2}
.pg .pan__prix b{font-size:1.6rem}
.pg .pan__qui{margin:8px 0;padding:8px 0;border-top:1px solid var(--ligne-2);gap:10px}
.pg .pan__av{width:36px;height:36px;font-size:1.1rem;object-fit:cover;background:var(--fond)}
.pg .pan__qui b{font-size:.92rem;line-height:1.2}
.pg .pan__qui small{font-size:.76rem;line-height:1.3}
.pg .pan__form{gap:6px 8px}
.pg .pan__form label{font-size:.7rem;gap:2px;line-height:1.2}
.pg .pan__form select,.pg .pan__form input{padding:0 10px;height:38px;min-height:0;font-size:.9rem;line-height:1.2}
.pg .pan__form .btn{padding:0 16px;min-height:42px;font-size:.92rem}
.pg .pan__alt{margin:6px 0 0;font-size:.82rem}
.pg .pan__note{margin:6px 0 0;font-size:.74rem;line-height:1.35}
.pg .pan__gar{margin:6px 0 0;padding:6px 0 0;display:flex;flex-wrap:wrap;justify-content:center;gap:2px 10px;font-size:.72rem;line-height:1.3}
.pg .pan__gar li{gap:4px;align-items:center}
.pg .pan__gar svg{width:12px;height:12px;margin:0}
.pg .pan__avis{margin:6px 0 0;padding:6px 0 0;font-size:.8rem;gap:3px 5px}
.pg .pan__avis .gg{width:15px;height:15px}
.pg .pan__part{margin:6px 0 0;padding:6px 0 0;gap:4px;font-size:.72rem;justify-content:center;align-items:center}
.pg .pan__part>span{flex:0 0 auto;font-size:.62rem;margin-right:4px}
.pg .pan__part a,.pg .pan__part button{min-height:30px;padding:0 8px;gap:4px}
.pg .pan__part svg{width:13px;height:13px}
.pg .pan__part i{font-style:normal}
.pg .pg-anc{gap:4px;font-size:.74rem}
.pg .pg-anc a{padding:4px 8px;min-height:28px}
.pg .somm{padding:10px 12px}
.pg .somm__t{margin:0 0 4px;font-size:.68rem}
.pg .somm a{min-height:32px;padding:3px 6px;font-size:.88rem;grid-template-columns:20px 1fr;gap:8px}
.pg .somm a>span:last-child>span{display:none}
.pg .somm__n{width:20px;height:20px;font-size:.7rem}
@media (max-height:920px){.pg .somm{display:none}}
@media (max-height:700px){.pg .pan__part,.pg .pan__gar{display:none}}
@media (max-height:600px){.pg .pan{position:static}}
@media (max-width:1040px){.pg .pan{position:static}.pg .somm{display:block}.pg .pan__part,.pg .pan__gar{display:flex}}

/* ---- v3 : moins de texte, plus de visuel (panneau + « Qui vous répond ») ---- */
.pg .pan__form select,.pg .pan__form input{height:40px;font-size:.92rem}
.pg .pan__form .pan__l2,.pg .pan__form .btn{grid-column:1/-1}
.pg .pan__form input::placeholder{color:var(--gris)}
.pg .pan__note{margin:8px 0 0;font-size:.78rem}
.pg .pan__wa{display:flex;align-items:center;justify-content:center;gap:7px;margin:8px 0 0;min-height:38px;border:1px solid var(--ligne-pg);border-radius:var(--r-pill);font-family:"Manrope",sans-serif;font-size:.86rem;font-weight:700;color:#0B6B3A;background:#F0FBF4}
.pg .pan__wa:hover{border-color:#25D366}
.pg .pan__gar{justify-content:center;gap:5px;padding:10px 0 0;margin:10px 0 0}
.pg .pan__gar li{border:1px solid var(--ligne-pg);border-radius:var(--r-pill);padding:3px 9px;font-size:.72rem;font-weight:600;background:var(--fond-2)}
.pg .pan__avis{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:10px 0 0;padding:10px 0 0;font-size:.82rem;text-align:left}
.pg .pan__avis>a{display:inline-flex;align-items:center;gap:6px;text-decoration:none;color:var(--nuit-900)}
.pg .pan__avis>a b{text-decoration:underline;text-underline-offset:3px}
.pg .pan__part{display:inline-flex;align-items:center;gap:4px;margin:0;padding:0;border:0}
.pg .pan__part>span{font-size:.62rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--gris-lis);margin-right:2px;flex:0 0 auto}
.pg .pan__part a,.pg .pan__part button{width:30px;height:30px;min-height:0;padding:0;justify-content:center;border-radius:50%}
.pg .pan__part button.ok{background:var(--vert-fond);border-color:var(--vert);color:var(--vert)}
.pg .equipe{padding:clamp(48px,6vw,80px) 0}
.pg .equipe__portrait{display:grid;grid-template-columns:260px 1fr;gap:34px;align-items:center;background:#fff;border:1px solid var(--ligne-pg);border-radius:var(--r-l);padding:26px;margin:8px 0 0}
.pg .equipe__photo{position:relative;aspect-ratio:4/5;border-radius:var(--r-m);background:linear-gradient(160deg,var(--nuit-900),var(--nuit));display:grid;place-items:center;overflow:hidden}
.pg .equipe__ini{font-family:"Archivo",serif;font-weight:700;font-size:5rem;color:var(--or);opacity:.9}
.pg .equipe__photo img{width:100%;height:100%;object-fit:cover;display:block}
.pg .equipe__txt{display:grid;gap:10px}
.pg .equipe__cit{margin:0;font-family:"Archivo",serif;font-size:clamp(1.25rem,2vw,1.6rem);font-weight:600;line-height:1.3;letter-spacing:-.5px;color:var(--nuit-900)}
.pg .equipe__txt h3{margin:0;font-size:1.05rem;color:var(--noir)}
.pg .equipe__txt p{margin:0;font-size:1rem;line-height:1.6;color:var(--texte)}
.pg .equipe__txt .btn{justify-self:start;margin-top:4px}
.pg .equipe__tuiles{list-style:none;margin:16px 0 0;padding:0;display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
.pg .equipe__tuiles li{background:#fff;border:1px solid var(--ligne-pg);border-radius:var(--r-m);padding:16px 14px;display:grid;gap:4px;justify-items:center;text-align:center;font-family:"Manrope",sans-serif}
.pg .equipe__tuiles svg{width:26px;height:26px;color:var(--teal-txt);margin-bottom:4px}
.pg .equipe__tuiles b{font-size:.92rem;color:var(--noir);line-height:1.25}
.pg .equipe__tuiles span{font-size:.78rem;color:var(--gris-lis);line-height:1.3}
.pg .equipe .equipe__sur{display:flex;gap:14px;align-items:center;margin:16px 0 0;background:var(--nuit-900);background-color:#0B5170;color:#DCE6EA;border-radius:var(--r-m);padding:16px 22px}
.pg .equipe__sur svg{flex:0 0 auto;width:26px;height:26px;color:var(--or)}
.pg .equipe__sur p{margin:0;font-size:1rem;line-height:1.5}
.pg .equipe__sur b{color:#fff}
.pg .equipe__sur a{color:var(--or-clair);font-weight:700;text-decoration:underline;text-underline-offset:3px;white-space:nowrap}
.pg .equipe__bas{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin:28px 0 0;align-items:start}
.pg .presse{margin:0;display:grid;gap:10px}
.pg .presse ul{gap:6px 18px}
.pg .presse li{font-size:1.05rem}
.pg .voyageurs{display:grid;grid-template-columns:1fr;gap:10px;margin:0}
.pg .voyageurs .eyebrow{margin:0;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.pg .voyageurs ul{grid-template-columns:repeat(4,1fr);gap:10px}
.pg .voyageurs li{aspect-ratio:1}
@media (max-width:1040px){.pg .equipe__tuiles{grid-template-columns:repeat(3,1fr)}.pg .equipe__bas{grid-template-columns:1fr}}
@media (max-width:700px){.pg .equipe__tuiles li:last-child:nth-child(odd){grid-column:1/-1}.pg .equipe__portrait{grid-template-columns:1fr;padding:18px}.pg .equipe__photo{max-width:220px}.pg .equipe__tuiles{grid-template-columns:repeat(2,1fr)}.pg .equipe__sur{flex-direction:column;align-items:flex-start}}

/* ---- v4 : inclus dans le sticky, presse pleine largeur ---- */
.pg .pan__inclus{list-style:none;margin:10px 0 0;padding:10px 0 0;border-top:1px solid var(--ligne-2);display:grid;grid-template-columns:1fr 1fr;gap:5px 8px;font-family:"Manrope",sans-serif;font-size:.8rem;font-weight:600;color:var(--nuit-900)}
.pg .pan__inclus li{display:flex;gap:6px;align-items:center;line-height:1.3}
.pg .pan__inclus svg{flex:0 0 auto;width:14px;height:14px;color:var(--teal-txt)}
.pg .equipe__bas{grid-template-columns:1fr;gap:24px}
.pg .presse{gap:12px}
.pg .presse ul{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;background:#fff;border:1px solid var(--ligne-pg);border-radius:var(--r-l);padding:22px 24px}
.pg .presse li{display:grid;place-items:center;text-align:center;font-family:"Archivo",serif;font-weight:700;font-size:clamp(1.15rem,1.6vw,1.45rem);letter-spacing:-.6px;line-height:1.1;color:var(--nuit-900);min-height:48px}
.pg .presse li span{border-bottom:3px solid var(--or);padding-bottom:4px}
.pg .voyageurs ul{grid-template-columns:repeat(4,1fr)}
.pg .voyageurs li{aspect-ratio:3/2}
@media (max-width:1040px){.pg .presse ul{grid-template-columns:repeat(3,1fr)}.pg .voyageurs ul{grid-template-columns:repeat(4,1fr)}}
@media (max-width:600px){.pg .presse ul{grid-template-columns:repeat(2,1fr);padding:16px}.pg .voyageurs ul{grid-template-columns:repeat(2,1fr)}}

/* ---- v5 : le bleu de marque #21B1B8 comme accent des nouveaux blocs.
   En aplat il ne porte pas de texte (2,6:1 sur blanc) : il souligne, colore les
   pictos et les bordures, et teinte les fonds en clair. ---- */
.pg{--bleu:#21B1B8;--bleu-fond:#E6F6F7}
.pg .hero__conf svg,.pg .pan__inclus svg,.pg .pan__gar svg,.pg .equipe__tuiles svg,.pg .equipe__sur svg,.pg .carte__aide svg,
.pg .tarif__cond h3 svg,.pg .equipe__c li svg,.pg .pan__avis .pan__part a,.pg .pan__avis .pan__part button{color:var(--bleu)}
.pg .apercu li .ic{color:var(--bleu);border-color:var(--bleu)}
.pg .pan__av{box-shadow:0 0 0 2px var(--bleu)}
.pg .pan__gar li{border-color:var(--bleu);background:var(--bleu-fond)}
.pg .pan__part a,.pg .pan__part button{border-color:var(--bleu)}
.pg .pg-anc a.vu{background:var(--bleu-fond);color:var(--nuit-900);border-color:var(--bleu);box-shadow:inset 0 -3px 0 var(--bleu)}
.pg .carte__pt:hover circle{stroke:var(--bleu)}
.pg .etape--vise{outline-color:var(--bleu)}
.pg .quand__frise .q-ok{box-shadow:inset 0 -3px 0 var(--bleu)}
.pg .tarif__cond article{border-top:3px solid var(--bleu)}
.pg .equipe__portrait{border-top:4px solid var(--bleu)}
.pg .equipe__tuiles li{border-top:3px solid var(--bleu)}
.pg .equipe .equipe__sur{background:var(--bleu-fond);background-color:#E6F6F7;color:var(--texte);border-left:5px solid var(--bleu)}
.pg .equipe__sur b{color:var(--nuit-900)}
.pg .equipe__sur a{color:var(--nuit-900)}
.pg .presse li span{border-bottom-color:var(--bleu)}
.pg .voyageurs li{border-color:var(--bleu);color:var(--nuit-900)}
.pg .voyageurs li svg{color:var(--bleu)}
.pg .pan__wa{color:#0B6B3A}
</style>
'''
JS = r'''
<script>
(function(){
  var pg=document.querySelector('.pg')||document;
  // Devis : le formulaire compose un message WhatsApp prérempli (aucun envoi ailleurs).
  var f=pg.querySelector('[data-devis]');
  if(f){f.addEventListener('submit',function(e){
    e.preventDefault();
    var m=f.querySelector('select').value||'dates à définir',n=f.querySelector('input[type=number]').value||'?',t=(f.querySelector('input[type=text]')||{value:''}).value.trim();
    var txt='Bonjour Mélanie, je souhaite un devis pour « Voyage à l’Oasis de Siwa » (à partir de 595 €/pers.).\nPériode : '+m+' · Voyageurs : '+n+(t?'\n'+t:'');
    window.open('https://wa.me/201066619098?text='+encodeURIComponent(txt),'_blank','noopener');
  });}
  // Copier le lien
  var c=pg.querySelector('[data-copier]');
  if(c){c.addEventListener('click',function(){
    var u=c.getAttribute('data-copier');
    (navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(function(){c.classList.add('ok');c.setAttribute('title','Lien copié');c.setAttribute('aria-label','Lien copié');},function(){window.prompt('Copiez ce lien :',u);});
  });}
  // Carte : un clic sur un point ouvre la journée correspondante.
  pg.querySelectorAll('.carte__pt[data-lieu]').forEach(function(p){
    p.setAttribute('tabindex','0');p.setAttribute('role','button');
    function aller(){
      var l=p.getAttribute('data-lieu').split(/\s+/),cible=null;
      pg.querySelectorAll('.etape[data-lieu]').forEach(function(a){if(!cible&&a.getAttribute('data-lieu').split(/\s+/).some(function(x){return l.indexOf(x)>=0}))cible=a;});
      if(!cible)return;
      var d=cible.closest('details');if(d)d.open=true;
      cible.scrollIntoView({behavior:'smooth',block:'start'});
      cible.classList.add('etape--vise');cible.classList.remove('fin');
      setTimeout(function(){cible.classList.add('fin')},1800);setTimeout(function(){cible.classList.remove('etape--vise','fin')},3200);
    }
    p.addEventListener('click',aller);p.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();aller();}});
  });
  // Navigation par sections : l'onglet suit le défilement.
  var liens=[].slice.call(pg.querySelectorAll('.pg-anc a')),cibles=liens.map(function(a){return document.getElementById(a.getAttribute('href').slice(1))});
  if('IntersectionObserver' in window&&liens.length){
    var actif=function(id){liens.forEach(function(a){a.classList.toggle('vu',a.getAttribute('href')==='#'+id)})};
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)actif(e.target.id)})},{rootMargin:'-20% 0px -70% 0px'});
    cibles.forEach(function(t){if(t)io.observe(t)});
  }
})();
</script>
'''
a, b = h.rsplit('</head>', 1); h = a + CSS + '</head>' + b
a, b = h.rsplit('</body>', 1); h = a + JS + '</body>' + b
h = h.replace('<title>', '<title>', 1)
open(dst, 'w', encoding='utf-8').write(h)
print('écrit', dst, len(h))
