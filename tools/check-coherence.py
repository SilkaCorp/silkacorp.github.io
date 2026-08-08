#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Silka - audit de coherence
==========================

Verifie que le site ne se contredit pas lui-meme, avant chaque mise en ligne.

    python3 tools/check-coherence.py

Code de sortie : 0 si tout est coherent, 1 si au moins une anomalie bloquante.

Ce script ne verifie PAS l'exactitude des montants face au droit en vigueur
(cela demande une source officielle). Il detecte les incoherences INTERNES,
qui sont le signe le plus fiable qu'une mise a jour a ete faite a moitie.
"""

import io
import os
import re
import sys
import collections
try:
    from html import unescape
except ImportError:
    from HTMLParser import HTMLParser
    unescape = HTMLParser().unescape

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(RACINE, 'index.html')
MANIFEST = os.path.join(RACINE, 'manifest.json')
SITEMAP = os.path.join(RACINE, 'sitemap.xml')
DEMARCHES = os.path.join(RACINE, 'demarches')

anomalies = []      # bloquantes
avertissements = [] # a regarder, pas bloquant


def lire(chemin):
    with io.open(chemin, encoding='utf-8') as f:
        return f.read()


def titre(t):
    print('\n' + t)
    print('-' * len(t))


# ---------------------------------------------------------------- chargement
if not os.path.exists(INDEX):
    print('index.html introuvable')
    sys.exit(1)

S = lire(INDEX)

RE_FICHE = re.compile(r'class="fiche-page" id="fiche-([a-z0-9-]+)"')
RE_LIEN = re.compile(r"showFiche\('([a-z0-9-]+)'\)\" class=\"demarche-link\"")
RE_MONTANT = re.compile(u'(\\d[\\d\u00a0 ]{2,9}(?:,\\d+)?)\\s*(?:&euro;|\u20ac)')
# les entrees du bot utilisent indifferemment fiche:'x' et fiche:"x"
RE_ENTREE = re.compile(
    r"\{\s*keys:\s*\[(.*?)\]\s*,\s*resp:\s*\"(.*?)\"\s*,\s*fiche:\s*['\"]([a-z0-9-]+)['\"]\s*\}",
    re.S)


def montants(texte):
    return {m.replace(u'\u00a0', ' ').strip() for m in RE_MONTANT.findall(texte)}


# --------------------------------------------------- 1. fiches et catalogue
titre('1. Fiches et catalogue')

positions = {m.group(1): m.start() for m in RE_FICHE.finditer(S)}
fiches = set(positions)
liens = set(RE_LIEN.findall(S))

ordre = sorted(positions, key=lambda k: positions[k])
texte_fiche = {}
for i, slug in enumerate(ordre):
    fin = positions[ordre[i + 1]] if i + 1 < len(ordre) else positions[slug] + 40000
    texte_fiche[slug] = S[positions[slug]:fin]

print('  fiches presentes    : %d' % len(fiches))
print('  liens au catalogue  : %d' % len(liens))

orphelines = sorted(fiches - liens)
mortes = sorted(liens - fiches)

if orphelines:
    anomalies.append('%d fiche(s) sans lien au catalogue : %s'
                     % (len(orphelines), ', '.join(orphelines)))
if mortes:
    anomalies.append('%d lien(s) vers une fiche inexistante : %s'
                     % (len(mortes), ', '.join(mortes)))
if not orphelines and not mortes:
    print('  OK - aucune orpheline, aucun lien mort')


# --------------------------------------------------- 2. le nombre affiche
titre('2. Nombre de demarches annonce')

attendu = len(fiches)
declares = collections.Counter(
    int(n) for n in re.findall(
        u'(\\d{3})\\s*(?:&nbsp;)?\\s*(?:d\u00e9marches|demarches|fiches)', S))

if os.path.exists(MANIFEST):
    for n in re.findall(u'(\\d{3})\\s*d\u00e9marches', lire(MANIFEST)):
        declares[int(n)] += 1

for valeur, combien in sorted(declares.items()):
    marque = 'OK ' if valeur == attendu else 'ECART'
    print('  %-5s %d mentions annoncent %d' % (marque, combien, valeur))

faux = [v for v in declares if v != attendu]
if faux:
    anomalies.append('le site annonce %s alors qu\'il y a %d fiches'
                     % (' et '.join(str(v) for v in sorted(faux)), attendu))
elif declares:
    print('  OK - toutes les mentions concordent avec %d fiches' % attendu)


# --------------------------------------------------- 3. sitemap
titre('3. Sitemap')

if os.path.exists(SITEMAP):
    urls = re.findall(r'<loc>(.*?)</loc>', lire(SITEMAP))
    slugs_sitemap = set()
    for u in urls:
        dernier = u.rstrip('/').split('/')[-1]
        if '/demarches/' in u and dernier != 'demarches':
            slugs_sitemap.add(dernier)
    print('  URLs de fiches : %d' % len(slugs_sitemap))
    absents = sorted(fiches - slugs_sitemap)
    fantomes = sorted(slugs_sitemap - fiches)
    if absents:
        avertissements.append('%d fiche(s) absente(s) du sitemap : %s'
                              % (len(absents), ', '.join(absents[:8])))
    if fantomes:
        avertissements.append('%d URL(s) du sitemap sans fiche : %s'
                              % (len(fantomes), ', '.join(fantomes[:8])))
    if not absents and not fantomes:
        print('  OK - le sitemap couvre exactement les fiches')
else:
    print('  (pas de sitemap.xml)')


# --------------------------------------------------- 4. pages statiques
titre('4. Pages statiques /demarches')

if os.path.isdir(DEMARCHES):
    dossiers = {d for d in os.listdir(DEMARCHES)
                if os.path.isdir(os.path.join(DEMARCHES, d))}
    print('  dossiers : %d' % len(dossiers))
    sans_page = sorted(fiches - dossiers)
    if sans_page:
        avertissements.append('%d fiche(s) sans page statique : %s'
                              % (len(sans_page), ', '.join(sans_page[:8])))
    # un dossier sans fiche est normal s'il s'agit d'une redirection
    en_trop = []
    for d in sorted(dossiers - fiches):
        page = os.path.join(DEMARCHES, d, 'index.html')
        contenu = lire(page) if os.path.exists(page) else ''
        if 'noindex' not in contenu and 'canonical' not in contenu:
            en_trop.append(d)
    if en_trop:
        avertissements.append('%d dossier(s) sans fiche ni redirection : %s'
                              % (len(en_trop), ', '.join(en_trop)))
    if not sans_page and not en_trop:
        print('  OK - fiches et pages statiques concordent')
else:
    print('  (pas de dossier demarches/)')


# --------------------------------------------------- 5. chatbot vs fiches
titre('5. Coherence chatbot / fiches')

entrees = list(RE_ENTREE.finditer(S))
print('  reponses du bot reliees a une fiche : %d' % len(entrees))

ecarts = []
for e in entrees:
    slug = e.group(3)
    if slug not in texte_fiche:
        avertissements.append('reponse du bot liee a la fiche inexistante "%s"' % slug)
        continue
    seuls = {v for v in montants(e.group(2)) - montants(texte_fiche[slug])
             if len(v.replace(' ', '')) >= 3}
    if seuls:
        ecarts.append((slug, sorted(seuls)))

if ecarts:
    print('  %d reponse(s) avancent un montant absent de leur fiche :' % len(ecarts))
    for slug, valeurs in ecarts:
        print('     %-34s %s' % (slug, ', '.join(valeurs)))
    avertissements.append(
        '%d montant(s) du bot a confronter a une source officielle' % len(ecarts))
else:
    print('  OK - aucun montant divergent')


# --------------------------------------------------- 6. millesimes suspects
titre('6. Millesimes')

annee_courante = 2026
suspects = collections.Counter()
for m in re.finditer(u'(?:en|pour|depuis le 1er janvier)\\s+(20\\d\\d)', S):
    an = int(m.group(1))
    if an < annee_courante:
        suspects[an] += 1

if suspects:
    for an, combien in sorted(suspects.items()):
        print('  %d mentions de "%d"' % (combien, an))
    print('  (une reference historique est legitime : "depuis 2025" par exemple)')
else:
    print('  OK - aucun millesime anterieur a %d' % annee_courante)


# --------------------------------------------------- 7. principe Premium
titre('7. Gratuite integrale, aucun verrou payant')

# Fonctions qui donnent acces au contenu et aux demarches : elles doivent
# rester exemptes de tout test d'abonnement. Si un verrou y reapparait,
# c'est une regression sur l'engagement fondateur du service.
DROITS_LIBRES = {
    'switchFicheTab': u"l'onglet \u00c9tapes d\u00e9taill\u00e9es",
    'checkAndStartDemarche': u"le lancement d'une d\u00e9marche",
    'downloadCerfa': u"le t\u00e9l\u00e9chargement des Cerfa",
}
MARQUEURS_PREMIUM = ['checkPremium', 'premium-gate', 'premium-blur',
                     'activatePremium', 'silka_premium', 'openMdpModal']

# Silka n'a plus aucune offre payante : tout le service est gratuit.
# Ce controle verifie donc l'inverse de ce qu'il verifiait avant : plus
# aucun verrou d'abonnement ne doit exister, et aucune page ne doit
# annoncer un contenu comme payant.
VERROUS_INTERDITS = ['premium-gate-overlay', 'premium-gate', 'premium-blur',
                     'silka_premium', 'gpt-paywall', 'paywall']
ANNONCES_INTERDITES = ['page-gratuit-premium', 'Passer Premium',
                       'Debloquer Premium', 'Version Premium']


def corps_fonction(nom, source):
    debut = source.find('function %s(' % nom)
    if debut < 0:
        return None
    ouvrante = source.find('{', debut)
    if ouvrante < 0:
        return None
    profondeur = 0
    for k in range(ouvrante, min(ouvrante + 30000, len(source))):
        if source[k] == '{':
            profondeur += 1
        elif source[k] == '}':
            profondeur -= 1
            if profondeur == 0:
                return source[debut:k + 1]
    return None


for fonction, libelle in sorted(DROITS_LIBRES.items()):
    corps = corps_fonction(fonction, S)
    if corps is None:
        avertissements.append('fonction "%s" introuvable : controle impossible' % fonction)
        print('  ?    %-30s (fonction introuvable)' % libelle)
        continue
    presents = [m for m in MARQUEURS_PREMIUM if m in corps]
    if presents:
        anomalies.append(
            u'%s est desormais conditionne a Premium (%s dans %s)'
            % (libelle, ', '.join(presents), fonction))
        print('  NON  %-30s verrou detecte : %s' % (libelle, ', '.join(presents)))
    else:
        print('  OK   %-30s libre' % libelle)

print('')
trouves = [m for m in VERROUS_INTERDITS if m in S]
if trouves:
    anomalies.append(
        u'un verrou d\'abonnement est reapparu dans le code : %s'
        % ', '.join(trouves))
    print('  NON  %-30s %s' % (u'aucun verrou payant', ', '.join(trouves)))
else:
    print('  OK   %-30s aucun verrou payant dans le code' % u'gratuite integrale')

annonces = [a for a in ANNONCES_INTERDITES if a in S]
if annonces:
    anomalies.append(
        u'une offre payante est annoncee alors que le service est gratuit : %s'
        % ', '.join(annonces))
    print('  NON  %-30s %s' % (u'aucune offre annoncee', ', '.join(annonces)))
else:
    print('  OK   %-30s aucune offre payante annoncee' % u'discours commercial')

# Rappel de la page tarifaire, pour relecture humaine
debut_gp = S.find('id="page-gratuit-premium"')
if debut_gp > 0:
    bloc = S[debut_gp:debut_gp + 4000]
    libres = re.findall(r'<span class="gp-check">&#10003;</span><span>(.*?)</span>', bloc)
    payants = re.findall(r'<span class="gp-check">&#10022;</span><span>(.*?)</span>', bloc)
    nettoyer = lambda t: ' '.join(unescape(re.sub(r'<[^>]+>', '', t)).split())
    print('\n  Page tarifaire \u2014 annonce gratuit (%d) :' % len(libres))
    for t in libres:
        print('     . ' + nettoyer(t))
    print('  Page tarifaire \u2014 annonce Premium (%d) :' % len(payants))
    for t in payants:
        print('     . ' + nettoyer(t))
    print('  (relire : chaque ligne "Premium" doit correspondre a un confort,')
    print('   jamais a un droit ni a un contenu)')


# --------------------------------------------------- verdict
print('\n' + '=' * 58)
if anomalies:
    print('ANOMALIES BLOQUANTES (%d)' % len(anomalies))
    for a in anomalies:
        print('  - ' + a)
if avertissements:
    print('\nA VERIFIER (%d)' % len(avertissements))
    for a in avertissements:
        print('  - ' + a)
if not anomalies and not avertissements:
    print('Tout est coherent.')
print('=' * 58)

sys.exit(1 if anomalies else 0)
