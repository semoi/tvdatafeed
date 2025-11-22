# Plan d'Intégration des Pull Requests - TvDatafeed

**Date:** 2025-11-21
**Document:** Plan Exécutif
**Responsable:** Agent Architecte Lead

---

## Vue d'Ensemble Rapide

Sur **5 Pull Requests** analysées du projet rongardF/tvdatafeed :

- ✅ **2 à intégrer immédiatement** (PR #37, #69)
- ⏸️ **2 à investiguer avant décision** (PR #30, #73)
- ❌ **1 à rejeter** (PR #61 - incompatible)

**Temps total estimé : 4-6 semaines**

---

## Tableau de Décision

| # | PR | Auteur | Feature Principale | Recommandation | Priorité | Effort | Date Cible |
|---|----|----|----|----|----|----|---|
| 37 | Verbose logging | Rna1h | Contrôle verbosité logs | ✅ **INTÉGRER** | 🟢 P1 | ⭐ 15min | Semaine 1 |
| 69 | Search interval | ayush1920 | Recherche par date range | ✅ **INTÉGRER** | 🟡 P2 | ⭐⭐ 1 semaine | Semaine 2 |
| 30 | Pro data | traderjoe1968 | 2FA + Pro Data >5K bars | ⏸️ **INVESTIGUER** | 🟠 P3 | ⭐⭐⭐ 3 jours | Semaine 3 |
| 73 | Overview batch | enoreese | Rate limit + Fundamentals | ⏸️ **INVESTIGUER** | 🟠 P4 | ⭐⭐⭐ 2 jours | Semaine 3 |
| 61 | Async operations | KoushikEng | Migration async/await | ❌ **REJETER** | 🔴 N/A | ⭐⭐⭐⭐ Impossible | - |

---

## Timeline d'Intégration

```
SEMAINE 1
├─ Jour 1 : ✅ PR #37 - Verbose logging (0.5j)
└─ Jour 2-5 : ✅ PR #69 - Date range search (4j)

SEMAINE 2
├─ Jour 1-3 : 🧪 Tests & Documentation PR #69
└─ Jour 4-5 : 🔍 Investigation PR #30 (début)

SEMAINE 3
├─ Jour 1-3 : 🔍 Investigation PR #30 (2FA + Pro Data)
└─ Jour 4-5 : 🔍 Investigation PR #73 (Rate limit + Features)

SEMAINE 4
└─ Décision GO/NO-GO basée sur investigations
   ├─ SI GO : Extraction 2FA (priorité haute)
   └─ SI NO-GO : Alternative implémentation

SEMAINE 5-6 (Si GO)
└─ Intégration features validées (2FA, Rate limiting, etc.)
```

---

## Détail par Sprint

### 🚀 Sprint 1 - Quick Win : Verbose Logging

**Durée :** 0.5 jour
**PR :** #37
**Agent :** 📚 Documentation & UX

**Objectif :** Permettre aux utilisateurs de désactiver les warnings répétitifs.

**Tâches :**
```python
# 1. Ajouter paramètre dans __init__()
def __init__(self, username=None, password=None, verbose=True):
    self.verbose = verbose
    # ...

# 2. Wrapper le warning
if self.verbose:
    logger.warning("Using unauthenticated access...")

# 3. Support env var
verbose = os.getenv('TV_VERBOSE', 'true').lower() == 'true'
```

**Checklist :**
- [ ] Créer branche `feature/verbose-logging`
- [ ] Implémenter changement (10 min)
- [ ] Tests unitaires (2 tests)
- [ ] Update README + .env.example
- [ ] Review + Merge

**Impact :** 🟢 Amélioration UX immédiate

---

### 🚀 Sprint 2 - Feature Majeure : Date Range Search

**Durée :** 1 semaine (4-5 jours)
**PR :** #69
**Agents :** 📊 Data Processing, 🌐 WebSocket, 🧪 Tests, 📚 Docs

**Objectif :** Permettre la recherche de données par dates (start/end) au lieu de n_bars.

**Fonctionnalités ajoutées :**

1. **API étendue** :
```python
# Ancienne méthode (toujours supportée)
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=100)

# Nouvelle méthode (date range)
df = tv.get_hist(
    'BTCUSDT', 'BINANCE', Interval.in_1_hour,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

2. **Validation dates** :
   - Empêche dates futures
   - Empêche dates avant 2000-01-01
   - Valide start < end

3. **Support timezone** :
   - DataFrame retourné inclut timezone info
   - Gestion automatique des fuseaux horaires

**Checklist :**
- [ ] Review des 196 lignes de changements
- [ ] Créer branche `feature/date-range-search`
- [ ] Porter interval_len dictionary
- [ ] Implémenter `is_valid_date_range()`
- [ ] Extraire `__get_response()` method
- [ ] Étendre `__create_df()` avec params timezone
- [ ] Modifier `get_hist()` avec logique date range
- [ ] Type hints + docstrings complets
- [ ] Tests unitaires (validation)
- [ ] Tests intégration (date range queries)
- [ ] Tests edge cases (timezones, DST)
- [ ] Documentation README
- [ ] Jupyter notebook exemple
- [ ] Review + Merge

**Impact :** 🟢 Feature critique pour backtesting et analyse quantitative

---

### 🔍 Sprint 3A - Investigation : 2FA & Pro Data

**Durée :** 3 jours
**PR :** #30
**Agents :** 🔐 Auth & Security, 🌐 WebSocket

**Objectif :** Déterminer si 2FA et Pro Data peuvent être extraits et intégrés.

**Questions à résoudre :**

1. **2FA (priorité haute)** :
   - ✅ Code 2FA isolable du reste ?
   - ✅ Dépendance pyotp seule suffisante ?
   - ✅ Intégration dans notre `__auth()` clean ?
   - ✅ Tests possibles sans compte 2FA réel ?

2. **Pro Data (incertain)** :
   - ❓ API TradingView fonctionne toujours pour >10K bars ?
   - ❓ Limites réelles par tier (Essential/Premium/Expert/etc.) ?
   - ❓ URL `wss://prodata.tradingview.com` accessible ?
   - ❓ Auto-detection type de compte possible ?

**Méthodologie :**

```bash
# 1. Cloner le fork
git remote add traderjoe1968 https://github.com/traderjoe1968/tvdatafeed.git
git fetch traderjoe1968 ProData
git checkout -b investigate/pr30 traderjoe1968/ProData

# 2. Analyser les 26 commits
git log --oneline main..investigate/pr30
git diff main..investigate/pr30 -- tvDatafeed/main.py

# 3. Identifier composants
# - Code 2FA uniquement
# - Code Pro Data uniquement
# - Code async (à ignorer)
# - Code autres features

# 4. Tester (si compte Pro disponible)
python test.py  # Avec compte Pro
```

**Livrables :**
- [ ] Rapport d'investigation `docs/investigations/PR30_ANALYSIS.md`
- [ ] Code 2FA extrait et commenté
- [ ] Résultats tests Pro Data (si compte dispo)
- [ ] Décision GO/NO-GO pour 2FA
- [ ] Décision GO/NO-GO pour Pro Data
- [ ] Plan d'intégration si GO

**Impact attendu :**
- 🟢 2FA : Très positif (P1 dans roadmap)
- 🟡 Pro Data : Dépend des tests

---

### 🔍 Sprint 3B - Investigation : Rate Limiting & Features

**Durée :** 2 jours
**PR :** #73
**Agents :** 📊 Data Processing, 🌐 WebSocket

**Objectif :** Accéder au code de PR #73 et analyser les features.

**Questions à résoudre :**

1. **Rate Limiting** :
   - ✅ Stratégie utilisée (decorator ? middleware ?) ?
   - ✅ Limites configurables ?
   - ✅ Backoff strategy ?
   - ✅ Compatible avec notre code ?

2. **Overview/Fundamental Data** :
   - ✅ Quelles données exactement ?
   - ✅ Nouvelles méthodes ajoutées ?
   - ✅ Format de retour ?
   - ✅ Utile pour nos utilisateurs ?

3. **Bulk Feature** :
   - ✅ Implémentation async ou threading ?
   - ✅ Conflit avec notre TvDatafeedLive ?
   - ✅ Performance vs notre approche ?

4. **Stream Feature** :
   - ✅ Duplicate de notre TvDatafeedLive ?
   - ✅ Différences avec notre implémentation ?

5. **Exception Handling** :
   - ✅ Améliore vraiment `__send_message()` ?
   - ✅ Quelle logique de retry ?

**Méthodologie :**

```bash
# 1. Cloner le fork
git remote add enoreese https://github.com/enoreese/tvdatafeed.git
git fetch enoreese fix-overview-batch
git checkout -b investigate/pr73 enoreese/fix-overview-batch

# 2. Analyser les 9 commits un par un
git show <commit-hash-1>  # get overview and fundamental data
git show <commit-hash-2>  # add bulk feature
# ... etc

# 3. Tester localement
pip install -e .
python
>>> from tvDatafeed import TvDatafeed
>>> # Tester nouvelles méthodes
```

**Livrables :**
- [ ] Rapport d'investigation `docs/investigations/PR73_ANALYSIS.md`
- [ ] Matrice features vs effort vs utilité
- [ ] Décision GO/NO-GO pour chaque feature
- [ ] Plan d'extraction si GO (cherry-pick commits sélectionnés)

**Impact attendu :**
- 🟢 Rate limiting : Positif (P2 roadmap)
- 🟡 Fundamental data : Dépend du besoin utilisateurs
- 🔴 Stream/Bulk : Probablement rejet (conflit avec TvDatafeedLive)

---

### 🚀 Sprint 4 - Intégration 2FA (si GO)

**Durée :** 1.5 semaine (6-8 jours)
**Prerequisite :** Investigation Sprint 3A validée
**Agent :** 🔐 Authentification & Sécurité

**Objectif :** Implémenter le support 2FA/TOTP.

**Architecture cible :**

```python
# 1. Nouvelle exception
class TwoFactorRequiredError(AuthenticationError):
    """Raised when 2FA is required"""
    def __init__(self, username):
        super().__init__(
            f"2FA required for account: {username}. "
            f"Provide TOTP key via TV_TOTP_KEY environment variable."
        )

# 2. Méthode __auth() étendue
def __auth(self, username, password, totp_key=None):
    # Auth normale
    response = requests.post(self.__sign_in_url, data=data, ...)

    # Si 2FA requis
    if response_data.get('error_code') == 'totp_required':
        if not totp_key:
            raise TwoFactorRequiredError(username=username)

        import pyotp
        totp = pyotp.TOTP(totp_key)
        code = totp.now()

        # Envoyer le code 2FA
        response_2fa = requests.post(
            url=self.__2fa_url,
            data={'code': code},
            ...
        )
        # Récupérer token

# 3. __init__ support TOTP
def __init__(self, username=None, password=None, totp_key=None, ...):
    # Load from env if not provided
    if username and not totp_key:
        totp_key = os.getenv('TV_TOTP_KEY')

    self.token = self.__auth(username, password, totp_key)
```

**Checklist :**
- [ ] Ajouter dépendance `pyotp` à requirements.txt
- [ ] Créer branche `feature/2fa-support`
- [ ] Créer exception `TwoFactorRequiredError`
- [ ] Extraire code TOTP de PR #30
- [ ] Adapter dans notre `__auth()`
- [ ] Support param `totp_key` dans `__init__()`
- [ ] Support env var `TV_TOTP_KEY`
- [ ] Validation format TOTP key
- [ ] Tests unitaires (avec mock pyotp)
- [ ] Tests intégration (si compte 2FA dispo)
- [ ] Documentation README section 2FA
- [ ] .env.example : Add TV_TOTP_KEY
- [ ] Guide extraction TOTP key
- [ ] Example script `examples/2fa_authentication.py`
- [ ] CHANGELOG : Major feature
- [ ] Review + Merge

**Impact :** 🟢 Feature P1 résolue - Support comptes 2FA

---

### ⏸️ Sprints 5-6 - Features Optionnelles

**Durée :** Variable selon décisions investigation
**Prerequisite :** Investigations Sprint 3 complétées

#### Option A : Pro Data Integration
- **Effort :** 5-8 jours
- **Condition :** Si tests confirment >10K bars fonctionne
- **Agent :** 🌐 WebSocket

#### Option B : Rate Limiting
- **Effort :** 2-3 jours
- **Condition :** Si PR #73 investigation positive
- **Agent :** 🌐 WebSocket

#### Option C : Fundamental Data
- **Effort :** 3-5 jours
- **Condition :** Si PR #73 investigation positive + besoin utilisateurs
- **Agent :** 📊 Data Processing

#### Option D : Multi-Symbol Threading (alternative PR #61)
- **Effort :** 3-4 jours
- **Agent :** ⚡ Threading & Concurrence
- **Implémentation :**

```python
from concurrent.futures import ThreadPoolExecutor

def get_hist_multi(
    self,
    symbols: List[str],
    exchange: str,
    interval: Interval,
    n_bars: int = 10,
    max_workers: int = 5
) -> Dict[str, pd.DataFrame]:
    """Fetch multiple symbols in parallel using threads"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(self.get_hist, symbol, exchange, interval, n_bars): symbol
            for symbol in symbols
        }

        results = {}
        for future in concurrent.futures.as_completed(futures):
            symbol = futures[future]
            try:
                results[symbol] = future.result()
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
                results[symbol] = None

        return results
```

---

## ❌ PR Rejetée : Async Operations (PR #61)

**Raison du rejet :** Architecture incompatible

Notre `TvDatafeedLive` est basé sur **threading** :
- `threading.Thread` pour main loop
- `threading.Lock` pour synchronisation
- `queue.Queue` pour consumers
- `websocket-client` (synchrone)

PR #61 utilise **async/await** :
- `asyncio.gather()` pour concurrence
- `websockets` (async)
- Nécessite event loop

❌ **Ces deux paradigmes sont mutuellement exclusifs.**

**Alternative implémentée :** `get_hist_multi()` avec `ThreadPoolExecutor` (voir Option D ci-dessus)

---

## Estimation Globale

| Phase | Durée | Effort (jours-agent) | Agents |
|-------|-------|---------------------|--------|
| Sprint 1 - Verbose | 0.5j | 0.5j | 1 |
| Sprint 2 - Date Range | 1 semaine | 5j | 4 |
| Sprint 3 - Investigations | 1 semaine | 5j | 3 |
| Sprint 4 - 2FA | 1.5 semaine | 8j | 2 |
| Sprints 5-6 - Optionnel | 2-3 semaines | 10j | 3 |
| **TOTAL** | **4-6 semaines** | **28.5j** | **6 agents** |

**Note :** Les sprints peuvent se chevaucher partiellement.

---

## Risques et Mitigation

| Risque | Mitigation |
|--------|-----------|
| **API TradingView changée (Pro Data)** | Investigation approfondie avant intégration |
| **Compte Pro non disponible pour tests** | Demander à la communauté de tester |
| **Breaking changes utilisateurs** | Backward compatibility stricte, semantic versioning |
| **2FA bugs** | Tests exhaustifs avec mocks, puis compte réel |
| **Date range performance** | Benchmarks avant/après intégration |
| **Code PR #73 inaccessible** | Clone du fork, analyse locale |

---

## Critères de Succès

### Sprint 1
- ✅ Verbose option disponible
- ✅ Tests passent
- ✅ Backward compatible

### Sprint 2
- ✅ Date range search fonctionnelle
- ✅ Tests coverage >80%
- ✅ Documentation complète
- ✅ Aucune régression

### Sprint 3
- ✅ 2 rapports d'investigation complets
- ✅ Décisions GO/NO-GO justifiées
- ✅ Plan d'action si GO

### Sprint 4
- ✅ 2FA fonctionnel avec compte test
- ✅ Documentation utilisateur claire
- ✅ Gestion erreurs robuste

---

## Prochaines Actions Immédiates

### Cette Semaine
1. ✅ **Valider ce plan** avec l'équipe
2. ✅ **Créer branche** `feature/verbose-logging`
3. ✅ **Implémenter PR #37** (verbose)
4. ✅ **Merge PR #37**
5. ✅ **Créer branche** `feature/date-range-search`
6. ✅ **Commencer review** PR #69 (196 lignes)

### Semaine Prochaine
1. ✅ **Terminer implémentation** PR #69
2. ✅ **Tests exhaustifs** date range
3. ✅ **Documentation** README + Jupyter
4. ✅ **Clone forks** pour investigations Sprint 3

---

## Versions Cibles

| Release | Features | Date Cible |
|---------|----------|-----------|
| **v1.X.1** | Verbose logging (PR #37) | Semaine 1 |
| **v1.X+1.0** | Date range search (PR #69) | Semaine 2 |
| **v1.X+2.0** | 2FA support (si GO) | Semaine 5 |
| **v2.0.0** | Si breaking changes nécessaires | TBD |

**Convention :** Semantic Versioning (MAJOR.MINOR.PATCH)
- PATCH : Bug fixes, verbose option
- MINOR : New features (date range, 2FA)
- MAJOR : Breaking changes (à éviter)

---

**Document maintenu par :** Agent Architecte Lead
**Dernière mise à jour :** 2025-11-21
**Prochaine revue :** Post Sprint 3 (après investigations)
