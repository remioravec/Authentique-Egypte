# Plus de boutons WhatsApp — 19 octobre

**Demande.** Point du 15 octobre (notes Gemini) : « Supprimer les boutons
WhatsApp et ajouter des formulaires par email pour clarifier la gestion des
demandes voyageurs ». Les demandes arrivaient sur le WhatsApp personnel de
Mélanie, sans trace et sans mesure. Relance de Mélanie le 19 octobre :
« Le formulaire de contact n'a pas été modifié, je reçois toujours les
demandes via WhatsApp. Pouvez-vous le corriger au plus vite ? »

**La cause.** Le formulaire « Recevoir mon devis » des 15 pages de séjour
n'envoyait rien : un script l'interceptait et ouvrait WhatsApp avec un
message prérempli (« Bonjour Mélanie, je souhaite un devis pour… »). Chaque
demande faite par ce formulaire arrivait donc sur son téléphone.

Le script est retiré. Le formulaire part vers /sur-mesure/#formulaire avec
ce que le visiteur a saisi. Là, `outils/relais-devis.py` (en place depuis
septembre) préremplit le formulaire WPForms : séjour, prix, période,
voyageurs, envies. Le visiteur complète ses coordonnées et envoie : la
demande part par e-mail et entre dans le back-office (AE CRM). Parcours
testé de bout en bout, sans envoi réel.

**Fait.** `outils/sans-whatsapp-1910.py`, sur les 61 pages refaites et sur le
programme « Le Caire, Rosette et canal de Suez » publié par Mélanie le
15 octobre :

| Où | Avant | Après |
|---|---|---|
| Bandeau du haut, pied de page | WhatsApp +20 106 661 9098 | « Formulaire de demande » → /sur-mesure/#formulaire |
| Hero des séjours et destinations | « Poser une question sur WhatsApp » | retiré (reste « Personnaliser ce séjour ») |
| Bloc devis, « Qui vous accompagne » | « Poser une question / Nous écrire sur WhatsApp » | retiré (reste « Demander mon devis ») |
| Panneau de devis des séjours | « Une question ? WhatsApp » | retiré (le formulaire est juste au-dessus) |
| Barre mobile, colonnes des guides | bouton « WhatsApp » | retiré (reste « Demander mon devis ») |
| FAQ de 3 pages de catégorie | « Contactez-nous directement sur WhatsApp » | « … par le formulaire de demande » |
| Formulaire « Recevoir mon devis » (15 séjours) | ouvrait WhatsApp | part vers le formulaire prérempli |
| Bulle verte flottante | extension Chaty (seul canal : WhatsApp) | extension désactivée, réactivable |

296 liens et 3 phrases. Restent les liens « Partager sur WhatsApp » des
séjours (wa.me/?text=…) : ils envoient la page à un proche, pas un message
à l'agence.

Chaque contenu est sauvegardé avant écriture dans
`sauvegarde/avant-mise-en-ligne/2026-10-19/sans-whatsapp/` (hors dépôt).

**À vérifier côté WPForms** (non lisible par l'API) : l'adresse qui reçoit
les notifications du formulaire n°7445. Les demandes doivent arriver à la
personne qui les traite. Elles sont aussi conservées dans le back-office
(AE CRM), avec leur état.
