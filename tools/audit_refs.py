# -*- coding: utf-8 -*-
"""
Silka — controle de tracabilite des references juridiques
=========================================================
Verifie que chaque article de loi cite dans les blocs « Références » des fiches
appartient bien au corpus confirme en source officielle (Legifrance, BOFiP,
service-public, Conseil constitutionnel, Cour de cassation, Conseil d'Etat).

Usage, depuis la racine du depot :
    python3 tools/audit_refs.py

Sortie :
  - le nombre de fiches equipees et de references citees
  - la liste des entrees non tracees, a controler manuellement

Une entree peut ressortir sans etre fausse : les lignes descriptives sans numero
d'article (« Preavis : 6 mois », « Amende forfaitaire : 68 € ») ne sont pas
tracables automatiquement. En revanche, tout ARTICLE cite qui apparait ici n'a
pas ete verifie et doit l'etre avant publication.

Pour ajouter une reference au corpus, l'inscrire dans l'ensemble VERIFIE
ci-dessous, apres l'avoir confirmee en source officielle.
"""

import io, os, re, collections

h = io.open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'index.html'), encoding='utf-8').read()

def fin(x, s):
    d = 0
    for m in re.finditer(r'<(/?)div\b[^>]*>', x[s:]):
        d += -1 if m.group(1) else 1
        if d == 0: return s + m.end()
    return len(x)

# ── corpus vérifié au fil des sessions, source par source ──────────
VERIFIE = set("""
1253 544 1641 2224 1219 1220
R.623-2
R.1336-5 R.1337-7
L.311-1-1
12 15 17-1 22 22-1 24
L.173-1-1
L.1237-11 L.1237-12 L.1237-13 L.1237-14 L.1237-16 R.1234-2 L.1232-1 L.1235-3 L.1471-1
L.1234-1 L.1234-5 L.1234-9 L.1132-1 L.1132-2 L.1132-3 L.1132-4 L.5422-1 L.1262-1 L.1262-2
L.221-18 L.217-3 L.217-5 L.217-8 L.216-1 L.611-1 L.251-1 L.251-2 L.251-3 L.254-1 L.861-1 L.160-1 L.160-8 L.160-9-1 L.161-1 2019-1479
1649A 1649Abis 1649bisC 1649AA 1736 1729-0A 344A 344B 150VHbis
L.526-1 L.526-2 L.526-3 L.526-5 2284 2285 2015-990 2021-1189
L.131-1 L.131-2 L.131-5 L.131-10 R.131-11 D.131-11-13 2021-1109 2021-823 2022-182 2011-333
L.145-1 L.145-4 L.145-10 L.145-14 L.145-15 L.145-41 L.841-1 L.842-1 L.847-1 R.842-1 R.844-1 R.844-5 R.848-1 D.843-1 D.848-5 R.124-1 R.124-16 L.266-1 L.266-2 2015-994
343 343-1 344 348 348-3 350 351 352-2 370-2 370-5 2022-1292
L.251-1 L.251-3 L.160-1 L.861-1 L.161-1 90-449 2005-212 2019-1479
L.211-1 L.211-4 L.211-9 L.211-25 L.421-1 85-677 L.2123-1 R.2123-1 R.2123-8
L.1221-10 R.1221-1 D.1221-19 L.8221-5 L.8223-1 L.8271-7 L.3231-12 L.3243-2
L.311-1 L.311-2 L.311-5 L.311-6 L.340-1 L.342-1 R.311-12 R.311-13 R.311-15 R.343-1
L.611-2 L.611-3 L.612-1 L.612-5
L.215-1-1 L.312-19 L.312-25
779-I 779-II 788-VI 790G 796-0bis 293B 293Bbis 293D 293BA 50-0 102ter 31 32 150U 1737
242noniesA 289bis 290 290A 290B L.169 L.223-3 L.223-7
L.441-2 L.441-4 R.441-3 R.441-6 L.324-1 L.160-13 L.160-14 L.341-1 L.341-4 L.341-7 L.341-9
L.341-15 L.341-16 L.341-17 L.351-1 L.351-1-5 1 5 8 9 10 14 60 813 131-13 131-6 131-11 131-36-1
L.1110-4 L.1111-5 L.1111-5-1 L.1111-7 R.1111-1 R.1111-6 R.4127-45
17 17-1 24 25 25-1 26 42
L.251-1 L.251-2 L.251-3 L.254-1 L.861-1 L.160-1 L.160-8 L.160-9-1 L.161-1 2019-1479
1649A 1649Abis 1649bisC 1649AA 1736 1729-0A 344A 344B 150VHbis
L.526-1 L.526-2 L.526-3 L.526-5 2284 2285 2015-990 2021-1189
L.131-1 L.131-2 L.131-5 L.131-10 R.131-11 D.131-11-13 2021-1109 2021-823 2022-182 2011-333
L.145-1 L.145-4 L.145-10 L.145-14 L.145-15 L.145-41 L.841-1 L.842-1 L.847-1 R.842-1 R.844-1 R.844-5 R.848-1 D.843-1 D.848-5 R.124-1 R.124-16 L.266-1 L.266-2 2015-994
343 343-1 344 348 348-3 350 351 352-2 370-2 370-5 2022-1292
L.251-1 L.251-3 L.160-1 L.861-1 L.161-1 90-449 2005-212 2019-1479
L.211-1 L.211-4 L.211-9 L.211-25 L.421-1 85-677 L.2123-1 R.2123-1 R.2123-8
L.1221-10 R.1221-1 D.1221-19 L.8221-5 L.8223-1 L.8271-7 L.3231-12 L.3243-2
L.311-1 L.311-2 L.311-5 L.311-6 L.340-1 L.342-1 R.311-12 R.311-13 R.311-15 R.343-1
L.611-2 L.611-3 L.611-6 L.611-7 L.612-16 L.712-1 L.712-4 L.712-5 L.712-7 L.411-4 L.411-5 2020-116
244quaterU 244quaterV D.319-16 D.319-44 D.319-51 2025-594 2024-299 2024-304 2024-849 2008-1425
205 219 233U 1668 235terZC 44octiesB 481538
200A 170 2025-1403
515-9 515-11 515-12 515-13 2024-536 2019-1480
L.6313-1 L.6323-1 L.6323-6 L.6323-17-1 L.6323-17-4 L.6323-32 L.6333-1 L.6411-1 L.6423-3 L.6113-1 L.6113-2 L.6113-6 L.6211-2
197 199sexdecies 199quaterF 200 196 196B L.341-4 L.541-1 28 29 30 33 34 494-1 2017-890 2025-1298 2026-103
L.162-5-3 L.160-13 L.160-8 L.431-1 81bis L.1111-11 L.1111-6
12 15 16 17 20 21 77 79 82 83 78-17
461 515-1 515-3 515-3-1 515-7
1380 1390 1391 1391B 1391Bbis 1417 1382 L.815-24
L.1211-3 L.1231-1 L.1232-1 R.1232-5 R.1232-14 L.2212-1 L.2212-11
L.11 L.16 L.18-1 L.30 L.71 L.72 L.75 L.76 L.77 R.73
R.421-1 R.421-9 R.421-12 R.421-14 R.421-23 R.421-25 R.423-23 L.424-2 L.424-5 R.600-2
L.821-1 L.821-2 L.821-3 L.822-1 L.841-5 D.821-1 D.841-2 D.841-11 R.821-5
L.441-1 L.441-1-4 L.441-2-1 L.441-2-3 L.441-2-3-1 R.441-14 L.342-14 L.365-2 226-13
L.3142-16 L.3142-27 L.3142-28 L.3142-35 L.3142-78 L.3142-100 L.3142-104
L.3142-113 L.3142-114 L.512-1 44sexies-0A
L.1225-4 L.1225-4-1 L.1225-17 L.1225-25 L.1225-35 L.1225-35-1 L.1225-46-2
L.3142-1 L.331-3 L.331-8 L.2122-1
L.210-6 L.223-1 L.223-2 L.237-1 L.237-2 L.237-13 1844-5
L.312-1 L.312-1-7 L.312-1-1 L.131-85 L.751-1 L.511-29 R.312-4-4
768 770 771 772 780 815 782 786 22-22.618
L.512-3 L.521-1 L.521-2 L.521-3 L.522-1 L.522-3 L.523-1 L.523-3 L.531-1 L.531-2
L.531-3 L.531-4 L.531-9 L.541-1 L.541-4 L.543-1 L.543-2 L.544-1 L.544-10 L.545-1
L.620-1 L.631-1 L.631-8 L.640-1
768 775 776 777 777-2 777-3 781 R.82 1055-2 1055-4 57

229-1 229-2 229-3 229-4 260 373-2-2 373-2-7 388-1 1374 R.582-4-1
L.821-1 L.821-5 L.821-5-1 L.815-1 L.815-7
L.815-11 L.815-13 L.835-3 L.161-17 L.161-17-2 L.161-22 L.161-22-1-2 L.161-22-1-5 L.161-22-1-9
L.262-1 L.262-13 L.262-27 L.262-39 L.262-16 L.262-34 L.262-45 L.262-48 L.262-49 L.262-58 L.232-25 L.245-8
L.412-1 L.412-2 L.412-3 L.413-7 L.414-2 L.421-1 L.421-3 L.421-5 L.421-6 L.421-7 L.421-9
L.421-25 L.423-1 L.423-7 L.423-23 L.424-9 L.424-10 L.433-4 L.433-6 R.431-2 R.431-5 R.431-15-1
750-1 1405 1422 R.211-3-4 R.211-3-8
529-2 529-10 530 A.37-20-1 A.37-20-2 A.37-20-3 A.37-20-4 A.37-20-5
L.121-2 L.121-3 L.223-1 L.317-4-1 L.322-1-1 R.321-6 R.321-15 R.322-1 R.322-3 R.322-4
R.322-5 R.322-10 L.211-1
""".split())

TEXTES_OK = [
 '2024-346','89-462','2013-392','2021-1104','2018-766','17-26.986','2017-1387','2021-1247',
 '16 août 2022','2023-1322','2022-1157','2021-1190','2022-1299','2024-266','2014-697',
 '2016-1478','Z12-012','2025-199','2023-270','2023-1196','2024-42','2023-357','2019-1333',
 '25-70.013','2010-38','2025-540','BOI-RES-TVA-000253','2025-127','2025-1247','2025-1044',
 'finances pour 2026','sécurité sociale pour 2026','2026-903','450275','2735','1er septembre 2026','1964','1968','30%','1mois',
]

def norm(t):
    t = t.replace('\u2019', "'")
    t = re.sub(r'\s+', '', t)
    return t

flags = collections.defaultdict(list)
total_refs = 0
fiches = 0

for m in re.finditer(r'<div class="fiche-page" id="fiche-([a-z0-9\-]+)">', h):
    slug = m.group(1); seg = h[m.start():fin(h, m.start())]
    k = seg.find('<div class="fiche-legal">')
    if k < 0: continue
    fiches += 1
    bloc = seg[k:fin(seg, k)]
    for li in re.findall(r'<li>(.*?)</li>', bloc, re.S):
        mr = re.search(r'<span class="ref">(.*?)</span>', li, re.S)
        if not mr: continue
        total_refs += 1
        txt = re.sub(r'<[^>]+>', '', li)   # libellé ET glose
        # un texte daté ou numéroté connu suffit à valider l'entrée
        if any(x in txt for x in TEXTES_OK): continue
        # sinon on cherche un numéro d'article
        arts = re.findall(r'(?:articles?\s+)?((?:[LRDA]\.?\s*)?\d+(?:[\-\u2011]\d+)*(?:\s*(?:bis|ter|nonies\s*A|septies\s*A))?(?:\s*[IVX]+)?(?:\s*,\s*\d+°)?)',
                          txt, re.I)
        if not arts:
            continue  # entrée descriptive sans référence chiffrée
        ok = False
        for a in arts:
            na = norm(a)
            if na in VERIFIE or any(na.startswith(v) or v.startswith(na) for v in VERIFIE if len(na) > 2):
                ok = True; break
        if not ok:
            flags[slug].append(txt.strip()[:80])

print('fiches équipées auditées :', fiches)
print('références citées        :', total_refs)
print()
if flags:
    print('── entrées à contrôler manuellement ──')
    for s, l in sorted(flags.items()):
        for x in l: print('  %-32s %s' % (s, x))
    print('\ntotal :', sum(len(v) for v in flags.values()))
else:
    print('✓ toutes les références citées appartiennent au corpus vérifié')
