# -*- coding: utf-8 -*-
"""
Silka - detection de references juridiques hors sujet
=====================================================

audit_refs.py verifie qu'une reference EXISTE dans le corpus verifie.
Ce script verifie qu'elle est PERTINENTE pour la fiche ou elle figure.

C'est le trou par lequel sont passes l'article 529-7, l'article 12 de la LFSS
et l'article L. 841-5 (contribution de vie etudiante) cite sur une fiche
d'inscription en maternelle : reference exacte, fiche sans rapport.

Principe : une reference decrit un dispositif. Si AUCUN des termes distinctifs
de sa description n'apparait dans le corps de la fiche, la reference parle
d'autre chose que la fiche. C'est le signe d'un copier-coller.

Usage : python3 tools/audit_pertinence.py [--tout]
"""

import io, os, re, sys, unicodedata, collections

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
h = io.open(os.path.join(RACINE, 'index.html'), encoding='utf-8').read()

VIDES = set(u"""
le la les un une des du de d au aux a et ou ni mais donc or car que qui quoi dont ou
ce cet cette ces son sa ses leur leurs il elle ils elles on nous vous je tu me te se
est sont etre ete etait sera seront avoir ai as ont avait aura eu en y il ne pas plus
pour par sur sous dans avec sans vers chez entre depuis pendant apres avant jusqu
tout tous toute toutes meme aussi tres bien peut peuvent doit doivent lorsque si
article articles code loi decret arrete numero alinea premier deuxieme troisieme
selon cas cadre titre livre chapitre section paragraphe modifie modifiee prevu prevue
fixe fixee applicable applicables vigueur date dates jour jours mois an ans annee
annees euro euros montant montants taux conditions condition droit droits duree
personne personnes assure assures beneficiaire beneficiaires demande demandes
janvier fevrier mars avril mai juin juillet aout septembre octobre novembre decembre
journal officiel publie publiee texte textes disposition dispositions general generale
""".split())


def sansaccent(s):
    return u''.join(c for c in unicodedata.normalize('NFD', s)
                    if unicodedata.category(c) != 'Mn')


def mots(s):
    s = sansaccent(s.lower())
    return {m for m in re.findall(r"[a-z]{4,}", s) if m not in VIDES}


def nettoie(x):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', x)).strip()


RE_FICHE = re.compile(r'<div class="fiche-page" id="fiche-([a-z0-9-]+)"')
RE_REF = re.compile(r'<li><span class="ref">(.*?)</span>\s*:\s*(.*?)</li>', re.S)
RE_THEME = re.compile(r'<span class="fiche-tag theme">(.*?)</span>')

positions = [(m.group(1), m.start()) for m in RE_FICHE.finditer(h)]
resultats = []
n_refs = 0

for i, (slug, deb) in enumerate(positions):
    fin = positions[i + 1][1] if i + 1 < len(positions) else len(h)
    bloc = h[deb:fin]
    mt = RE_THEME.search(bloc)
    theme = nettoie(mt.group(1)) if mt else '?'

    refs = RE_REF.findall(bloc)
    # corps de la fiche = tout sauf le bloc References
    k = bloc.find('fiche-legal-title')
    corps = nettoie(bloc[:k] if k > 0 else bloc)
    vocab = mots(corps) | mots(slug.replace('-', ' '))

    for intitule, desc in refs:
        n_refs += 1
        d = nettoie(desc)
        termes = mots(d)
        if len(termes) < 3:
            continue                      # description trop courte pour juger
        communs = termes & vocab
        score = float(len(communs)) / len(termes)
        resultats.append((score, len(communs), slug, theme, nettoie(intitule), d, sorted(termes)[:9]))

resultats.sort()

print('fiches : %d | references analysees : %d' % (len(positions), n_refs))
print('\n' + '=' * 92)
print('REFERENCES SANS AUCUN TERME COMMUN AVEC LEUR FICHE  (contamination probable)')
print('=' * 92)

zero = [r for r in resultats if r[1] == 0]
for score, nc, slug, theme, intitule, desc, termes in zero:
    print('\n  %-34s [%s]' % (slug, theme[:20]))
    print('    ref  : %s' % intitule[:86])
    print('    dit  : %s' % desc[:100])
    print('    mots : %s' % ', '.join(termes))

print('\n  -> %d reference(s) sans recouvrement' % len(zero))

seuil = 0.10
faibles = [r for r in resultats if 0 < r[1] and r[0] < seuil]
print('\n' + '=' * 92)
print('RECOUVREMENT TRES FAIBLE (< %d%%) - a survoler' % (seuil * 100))
print('=' * 92)
for score, nc, slug, theme, intitule, desc, termes in faibles[:25]:
    print('  %4.0f%%  %-32s %s' % (score * 100, slug[:32], intitule[:60]))
print('\n  -> %d reference(s) a faible recouvrement' % len(faibles))

if '--tout' in sys.argv:
    print('\n' + '=' * 92)
    print('CLASSEMENT COMPLET')
    print('=' * 92)
    for score, nc, slug, theme, intitule, desc, termes in resultats[:120]:
        print('  %4.0f%%  %-30s %s' % (score * 100, slug[:30], intitule[:58]))
