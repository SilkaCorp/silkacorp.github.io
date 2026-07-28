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
7. **Principe Premium** — vérifie que Premium ne verrouille jamais un droit :
   les fonctions qui donnent accès au contenu (`switchFicheTab`,
   `checkAndStartDemarche`, `downloadCerfa`) doivent rester exemptes de tout
   test d'abonnement. Inversement, chaque fonctionnalité annoncée comme
   payante sur la page tarifaire doit correspondre à un verrou réellement
   présent dans le code — sinon la page vend quelque chose de gratuit.
   Les deux colonnes de la page tarifaire sont affichées pour relecture.

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

- `annee_courante` dans le point 6, chaque 1er janvier.
- `DROITS_LIBRES` et `VERROUS_ATTENDUS` dans le point 7, si une fonctionnalité
  change de camp. Ce sont volontairement des listes courtes et explicites :
  modifier une de ces lignes doit être une décision consciente, pas un effet
  de bord.

### Point 7 : pourquoi ce contrôle existe

Il a été ajouté après avoir découvert que la page « Gratuit vs Premium »
annonçait l'onglet *Étapes détaillées* comme payant, alors que le verrou
correspondant avait été retiré du code depuis longtemps. Un visiteur pouvait
donc payer pour un contenu qu'il avait déjà. Le contrôle se déclenche dans
les deux sens : verrou réapparu sur un droit, ou verrou disparu sous une
promesse payante.
