# CLAUDE.md - TvDatafeed Project Guide

## Vue d'ensemble du projet

**TvDatafeed** est une bibliothèque Python permettant de télécharger des données historiques et en temps réel depuis TradingView. Ce projet est un fork du projet original [rongardF/tvdatafeed](https://github.com/rongardF/tvdatafeed) qui n'est plus maintenu activement.

### Objectifs du fork

1. **Implémenter les merge requests** en attente du projet original
2. **Corriger les issues critiques** non résolues
3. **Supporter l'authentification TradingView moderne** incluant 2FA (authentification à deux facteurs)
4. **Maintenir la compatibilité** avec la dernière version de TradingView

### Version actuelle
- **Version**: 2.1.0
- **Branche de développement**: `claude/create-claude-md-01JsoAcW4PPRSPvGVx9rsJqg`

---

## Architecture du projet

### Structure des fichiers

```
tvdatafeed/
├── README.md                 # Documentation utilisateur
├── setup.py                  # Configuration du package
├── requirements.txt          # Dépendances
├── tv.ipynb                  # Notebook de démonstration
└── tvDatafeed/              # Package principal
    ├── __init__.py          # Point d'entrée, exports
    ├── main.py              # TvDatafeed (classe principale)
    ├── datafeed.py          # TvDatafeedLive (données temps réel)
    ├── seis.py              # Seis (Symbol-Exchange-Interval Set)
    └── consumer.py          # Consumer (callback threads)
```

### Classes principales

#### 1. `TvDatafeed` (main.py)
**Responsabilité**: Récupération de données historiques depuis TradingView

**Méthodes clés**:
- `__init__(username, password)` - Initialisation avec authentification
- `get_hist(symbol, exchange, interval, n_bars, fut_contract, extended_session)` - Récupère les données historiques
- `search_symbol(text, exchange)` - Recherche de symboles
- `__auth(username, password)` - Authentification (⚠️ **PROBLÈME CRITIQUE**)

**Points d'attention**:
- L'authentification utilise actuellement une simple requête POST qui échoue avec reCAPTCHA
- WebSocket vers `wss://data.tradingview.com/socket.io/websocket`
- Limite de 5000 barres par requête

#### 2. `TvDatafeedLive` (datafeed.py)
**Responsabilité**: Extension de TvDatafeed pour les données en temps réel

**Méthodes clés**:
- `new_seis(symbol, exchange, interval, timeout)` - Créer un nouveau flux de données
- `del_seis(seis, timeout)` - Supprimer un flux
- `new_consumer(seis, callback, timeout)` - Ajouter un callback
- `del_consumer(consumer, timeout)` - Supprimer un callback
- `_main_loop()` - Thread principal de surveillance (⚠️ **complexe**)

**Architecture threading**:
- Thread principal (`_main_loop`) qui surveille les expirations d'intervalles
- Threads Consumer pour chaque callback utilisateur
- Utilise des locks pour la thread-safety

#### 3. `Seis` (seis.py)
**Responsabilité**: Conteneur pour un ensemble Symbol-Exchange-Interval unique

**Propriétés**:
- `symbol` (read-only)
- `exchange` (read-only)
- `interval` (read-only)
- `tvdatafeed` (référence au TvDatafeedLive parent)

#### 4. `Consumer` (consumer.py)
**Responsabilité**: Thread de traitement des callbacks utilisateur

**Mécanisme**:
- Hérite de `threading.Thread`
- File `queue.Queue` pour recevoir les données
- Gestion d'exceptions gracieuse

### Intervalles supportés

```python
Interval.in_1_minute   = "1"
Interval.in_3_minute   = "3"
Interval.in_5_minute   = "5"
Interval.in_15_minute  = "15"
Interval.in_30_minute  = "30"
Interval.in_45_minute  = "45"
Interval.in_1_hour     = "1H"
Interval.in_2_hour     = "2H"
Interval.in_3_hour     = "3H"
Interval.in_4_hour     = "4H"
Interval.in_daily      = "1D"
Interval.in_weekly     = "1W"
Interval.in_monthly    = "1M"
```

---

## Issues critiques à résoudre

### 🔴 PRIORITÉ HAUTE

#### Issue #62 - Authentification avec reCAPTCHA
**Fichier**: `tvDatafeed/main.py:65-82`

**Problème**:
```python
def __auth(self, username, password):
    # ...
    response = requests.post(
        url=self.__sign_in_url, data=data, headers=self.__signin_headers)
    token = response.json()['user']['auth_token']
```
Cette méthode échoue car TradingView utilise maintenant reCAPTCHA et 2FA.

**Solution à implémenter**:
1. Utiliser Playwright/Selenium pour navigateur headless
2. Gérer le reCAPTCHA (manuel ou service tiers)
3. Supporter l'authentification 2FA
4. Sauvegarder et réutiliser les cookies/sessions

**Références**:
- Issue originale: https://github.com/rongardF/tvdatafeed/issues/62
- TradingView sign-in URL: `https://www.tradingview.com/accounts/signin/`

#### Issue #52 - Login avec compte Google OAuth
**Problème**: Les comptes créés via Google OAuth ne peuvent pas s'authentifier.

**Solution**:
- Implémenter un flow OAuth2 pour Google
- Alternative: utiliser une session navigateur existante

#### Issue #63 - get_hist() ne fonctionne plus
**Cause potentielle**: Changements dans l'API WebSocket de TradingView

**Investigation nécessaire**:
1. Analyser les messages WebSocket actuels
2. Comparer avec le protocole attendu
3. Mettre à jour les parsers si nécessaire

### 🟡 PRIORITÉ MOYENNE

#### Issue #72 - Problèmes de timezone
**Fichier**: Parsing des dates dans `__create_df()`

**Impact**: Dates incorrectes dans les DataFrames retournés

#### Issue #43 - Mauvaise assignation des dates
**Lié à**: Issue #72

#### Issue #70 - SyntaxWarning: invalid escape sequence
**Fichier**: À identifier (probablement regex dans main.py)

**Fix simple**: Utiliser raw strings `r"pattern"` ou échapper correctement

---

## Pull Requests à intégrer

### PR #73 - Fix overview batch
**Auteur**: enoreese (31 juillet 2025)

**À analyser**: Nature exacte du fix

### PR #69 - Added search interval
**Auteur**: ayush1920 (18 avril 2025)

**Fonctionnalité**: Amélioration de la fonction `search_symbol()`

### PR #61 - Enhanced async operations
**Auteur**: KoushikEng (25 novembre 2024)

**Fonctionnalité**: Support des opérations asynchrones (async/await)

**Impact**: Majeur - nécessite tests approfondis

### PR #37 - Added verbose logging
**Auteur**: Rna1h (20 décembre 2023)

**Fonctionnalité**: Amélioration du logging avec niveau verbose

**Facilité**: Simple - devrait être intégré rapidement

### PR #30 - Pro data access
**Auteur**: traderjoe1968 (26 septembre 2023)

**Fonctionnalité**: Accès aux données TradingView Pro

---

## Guide de développement

### Configuration de l'environnement

```bash
# Cloner le repository
git clone <repo-url>
cd tvdatafeed

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt
pip install -e .  # Installation en mode développement
```

### Dépendances actuelles

```
setuptools
pandas
websocket-client
requests
```

### Dépendances à ajouter (pour 2FA)

```
playwright>=1.40.0  # Pour navigation headless
python-dotenv>=1.0.0  # Pour gestion des secrets
```

### Workflow de développement

1. **Créer une branche** pour chaque issue/PR
   ```bash
   git checkout -b fix/issue-62-2fa-auth
   ```

2. **Développer et tester**
   ```bash
   # Tester localement
   python -m pytest tests/  # (si tests existants)

   # Ou tester manuellement
   python -c "from tvDatafeed import TvDatafeed; tv = TvDatafeed('user', 'pass'); print(tv.get_hist('AAPL', 'NASDAQ'))"
   ```

3. **Commit et push**
   ```bash
   git add .
   git commit -m "fix: implement 2FA authentication support (#62)"
   git push -u origin claude/create-claude-md-01JsoAcW4PPRSPvGVx9rsJqg
   ```

### Standards de code

- **Style**: PEP 8
- **Docstrings**: Google style (déjà utilisé dans le code)
- **Logging**: Utiliser le module `logging` (déjà en place)
- **Type hints**: Ajouter progressivement pour le nouveau code

---

## Points techniques importants

### 1. Protocole WebSocket TradingView

**Format des messages**:
```
~m~<length>~m~<json_payload>
```

**Exemple de séquence**:
1. `set_auth_token` - Authentification
2. `chart_create_session` - Créer session graphique
3. `quote_create_session` - Créer session quotes
4. `resolve_symbol` - Résoudre le symbole
5. `create_series` - Demander les données
6. Attendre `series_completed`

**⚠️ Attention**: Le protocole peut changer sans préavis de TradingView

### 2. Gestion des sessions

**Génération actuelle** (main.py:101-114):
```python
@staticmethod
def __generate_session():
    stringLength = 12
    letters = string.ascii_lowercase
    random_string = "".join(random.choice(letters) for i in range(stringLength))
    return "qs_" + random_string
```

Sessions: `qs_xxxxx` (quote session) et `cs_xxxxx` (chart session)

### 3. Threading dans TvDatafeedLive

**Architecture**:
- 1 thread principal (`_main_loop`) par instance TvDatafeedLive
- 1 thread Consumer par callback enregistré
- Lock global (`_lock`) pour toutes les opérations

**Synchronisation**:
- `threading.Event` pour interruptions
- `queue.Queue` pour communication Consumer

**⚠️ Attention**: Deadlocks possibles si mal utilisé

### 4. Format des données retournées

**DataFrame pandas** avec colonnes:
```
Index: datetime (pandas DatetimeIndex)
Columns: [symbol, open, high, low, close, volume]
```

---

## Roadmap suggérée

### Phase 1: Stabilisation (Priorité immédiate)
- [ ] Résoudre Issue #62 (Authentification 2FA)
- [ ] Résoudre Issue #63 (get_hist ne fonctionne plus)
- [ ] Corriger Issue #70 (SyntaxWarning)
- [ ] Tests sur différents symboles/exchanges

### Phase 2: Intégrations rapides
- [ ] Intégrer PR #37 (verbose logging)
- [ ] Intégrer PR #69 (search interval)
- [ ] Corriger Issues #72 et #43 (timezone)

### Phase 3: Améliorations majeures
- [ ] Analyser et intégrer PR #61 (async operations)
- [ ] Intégrer PR #73 (fix overview batch)
- [ ] Implémenter Issue #52 (Google OAuth)

### Phase 4: Features avancées
- [ ] Intégrer PR #30 (Pro data)
- [ ] Documentation complète
- [ ] Suite de tests automatisés
- [ ] CI/CD pipeline

---

## Debugging et tests

### Activer le debug WebSocket

```python
from tvDatafeed import TvDatafeed
import logging

logging.basicConfig(level=logging.DEBUG)

tv = TvDatafeed(username="...", password="...")
tv.ws_debug = True  # Active l'affichage des messages WebSocket
data = tv.get_hist("AAPL", "NASDAQ")
```

### Tester sans authentification

```python
tv = TvDatafeed()  # Mode sans login
# Symboles limités mais utile pour tester le protocole WS
data = tv.get_hist("BTCUSD", "BINANCE")
```

### Capturer les erreurs d'authentification

```python
try:
    tv = TvDatafeed(username="test", password="test")
    print(f"Token: {tv.token}")  # Vérifier le token obtenu
except Exception as e:
    print(f"Auth failed: {e}")
```

---

## Ressources utiles

### Documentation TradingView
- API officielle: Non publique (reverse engineering nécessaire)
- WebSocket endpoint: `wss://data.tradingview.com/socket.io/websocket`
- Sign-in URL: `https://www.tradingview.com/accounts/signin/`

### Projets similaires (inspiration)
- [python-tradingview-ta](https://github.com/brian-the-dev/python-tradingview-ta)
- [tradingview-scraper](https://github.com/mnwato/tradingview-scraper)

### Issues du projet original à consulter
- [Issue #62 - reCAPTCHA](https://github.com/rongardF/tvdatafeed/issues/62)
- [Issue #52 - Google OAuth](https://github.com/rongardF/tvdatafeed/issues/52)
- [Issue #63 - get_hist broken](https://github.com/rongardF/tvdatafeed/issues/63)
- [Liste complète des issues](https://github.com/rongardF/tvdatafeed/issues)
- [Liste des Pull Requests](https://github.com/rongardF/tvdatafeed/pulls)

---

## Notes pour Claude (AI Assistant)

### Quand je travaille sur ce projet:

1. **Toujours vérifier** la branche de travail: `claude/create-claude-md-01JsoAcW4PPRSPvGVx9rsJqg`

2. **Ne jamais modifier** directement les fichiers critiques sans backup

3. **Tester l'authentification** en priorité avant toute autre feature

4. **Documenter** tous les changements dans les commits

5. **Référencer** les issues/PR dans les commits: `fix: resolve authentication issue (#62)`

6. **Privilégier** les solutions non-invasives qui maintiennent la compatibilité

### Commandes Git à utiliser

```bash
# Status
git status
git log --oneline -5

# Développement
git checkout -b feature/nouvelle-fonctionnalite
git add .
git commit -m "feat: description"
git push -u origin claude/create-claude-md-01JsoAcW4PPRSPvGVx9rsJqg

# En cas de problème
git stash  # Sauvegarder les changements
git reset --hard HEAD  # Annuler tout
```

### Anti-patterns à éviter

❌ Modifier le protocole WebSocket sans comprendre l'impact
❌ Casser la compatibilité avec le code existant
❌ Ajouter des dépendances lourdes sans justification
❌ Ignorer les warnings du logger
❌ Commit directement sur main/master

### Bonnes pratiques

✅ Lire les issues/PR existantes avant de coder
✅ Tester avec et sans authentification
✅ Utiliser le logging pour debug
✅ Maintenir la documentation à jour
✅ Créer des branches par feature/fix
✅ Commits atomiques et descriptifs

---

## FAQ Technique

**Q: Pourquoi l'authentification échoue-t-elle?**
R: TradingView a ajouté reCAPTCHA et 2FA. La simple requête POST ne suffit plus.

**Q: Puis-je utiliser l'API sans login?**
R: Oui mais avec limitations (symboles, échanges, quotas).

**Q: Comment débugger les problèmes WebSocket?**
R: Activer `tv.ws_debug = True` et `logging.DEBUG`.

**Q: Quelle est la limite de données?**
R: 5000 barres maximum par requête `get_hist()`.

**Q: Le projet supporte-t-il async/await?**
R: Pas encore, mais PR #61 propose cette fonctionnalité.

**Q: Comment gérer les données temps réel?**
R: Utiliser `TvDatafeedLive` avec le système Seis/Consumer.

---

**Dernière mise à jour**: 2025-11-20
**Mainteneur**: Fork personnel du projet rongardF/tvdatafeed
**Licence**: MIT (voir LICENSE)
