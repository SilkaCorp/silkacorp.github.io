# Outils Silka

## check-coherence.py

Audit de cohérence interne du site. À lancer avant chaque mise en ligne :

```
python3 tools/check-coherence.py
```

Code de sortie `0` si tout concorde, `1` si une anomalie bloquante est trouvée
(le script peut donc servir de garde-fou avant un `git push`).

### Ce qu'il vérifie

1. **Fiches et catalogue** — aucune fiche orpheline (existante mais non reliée
   à un thème), aucun lien vers une fiche supprimée.
2. **Nombre annoncé** — toutes les mentions « N démarches / N fiches », dans
   `index.html` et `manifest.json`, correspondent au nombre réel de fiches.
3. **Sitemap** — couvre exactement les fiches existantes.
4. **Pages statiques** — chaque fiche a son dossier ; les dossiers sans fiche
   sont tolérés s'il s'agit de redirections (`noindex` ou `canonical`).
5. **Chatbot / fiches** — signale les réponses du bot qui renvoient vers une
   fiche inexistante, et celles qui avancent un montant absent de leur fiche.
6. **Millésimes** — repère les « en 20XX » antérieurs à l'année courante.

### Ce qu'il ne vérifie pas

L'exactitude des montants au regard du droit en vigueur : cela suppose une
source officielle et reste un travail humain. Le script détecte les
incohérences **internes**, qui sont le signal le plus fiable qu'une mise à
jour n'a été faite qu'à moitié — typiquement une fiche corrigée sans que la
réponse correspondante du chatbot le soit.

Le point 5 produit du bruit légitime : une fourchette de prix indicative
(coût d'un DPE, d'un divorce) n'a pas à figurer dans la fiche. Ce qui compte,
c'est de passer la liste en revue et de savoir pourquoi chaque écart est là.

### À mettre à jour

`annee_courante` dans le point 6, chaque 1er janvier.
