# Documentation Projet TvDatafeed pour Claude

## Vue d'ensemble du projet

**TvDatafeed** est une bibliothèque Python permettant de récupérer des données historiques et en temps réel depuis TradingView. Ce projet est un fork avec des fonctionnalités étendues pour le live data feed.

### Objectifs actuels du projet

1. **Rendre opérationnel** la connexion avec compte TradingView Pro
2. **Implémenter le support 2FA** (authentification à deux facteurs)
3. **Améliorer la robustesse** du code (gestion d'erreurs, retry, timeouts)
4. **Récupération fiable** de données multi-assets sur différents timeframes
5. **Maintenir la trajectoire** du projet avec une architecture solide

### Architecture du projet

```
tvdatafeed/
├── tvDatafeed/
│   ├── __init__.py           # Exports des classes principales
│   ├── main.py               # TvDatafeed (classe de base)
│   ├── datafeed.py           # TvDatafeedLive (live data + threading)
│   ├── seis.py               # Seis (Symbol-Exchange-Interval Set)
│   └── consumer.py           # Consumer (gestion callbacks)
├── scripts/
│   ├── get_auth_token.py     # Extraction JWT via Playwright (contourne reCAPTCHA)
│   └── token_manager.py      # Gestion lifecycle des tokens (cache, refresh, validation)
├── examples/
│   └── automated_data_fetch.py  # Exemple script automatisé serveur
├── tests/
│   ├── unit/                 # Tests unitaires
│   └── integration/          # Tests d'intégration
├── setup.py                  # Configuration installation
├── requirements.txt          # Dépendances
├── README.md                # Documentation utilisateur
└── CLAUDE.md                # Ce fichier - Documentation pour Claude
```

### Composants principaux

#### 1. TvDatafeed (main.py)
- **Rôle** : Classe de base pour récupération de données historiques
- **Fonctionnalités** :
  - Authentification TradingView (username/password)
  - Connexion WebSocket à `wss://data.tradingview.com/socket.io/websocket`
  - Récupération jusqu'à 5000 bars de données historiques
  - Recherche de symboles
- **Fonctionnalités récentes (PR #30 - Nov 2025)** :
  - ✅ Support 2FA/TOTP (totp_secret, totp_code) - commit a5288f3
  - ✅ Date Range Search (start_date, end_date) - commit ab62585
  - ✅ Verbose logging control (verbose parameter) - commit 0045714
  - ✅ Timeout WebSocket configurable (ws_timeout, TV_WS_TIMEOUT)
  - ✅ Gestion d'erreurs robuste (exceptions personnalisées)
- **Limitations restantes** :
  - ✅ Retry automatique sur connexion WebSocket (Phase 2)
  - ✅ Timeout cumulatif dans __get_response() (Phase 2)
  - ❌ Rate limiting TradingView non géré (Phase future)

#### 2. TvDatafeedLive (datafeed.py)
- **Rôle** : Extension avec support temps réel via threading
- **Fonctionnalités** :
  - Monitoring continu de plusieurs symboles simultanément
  - Système de callbacks (Consumers) pour traiter les nouvelles données
  - Thread principal + threads consumers
  - Gestion des timeframes avec auto-calcul des prochains updates
- **Complexité** :
  - Threading avancé avec locks
  - Gestion d'événements et synchronisation
  - Retry jusqu'à 50 tentatives (RETRY_LIMIT)

#### 3. Seis (seis.py)
- **Rôle** : Conteneur pour une combinaison unique Symbol-Exchange-Interval
- **Responsabilités** :
  - Stocker les métadonnées du ticker
  - Gérer la liste des consumers attachés
  - Détecter les nouvelles données

#### 4. Consumer (consumer.py)
- **Rôle** : Gestion des callbacks utilisateur dans des threads séparés
- **Responsabilités** :
  - Queue de données pour chaque callback
  - Exécution asynchrone des callbacks
  - Lifecycle management (start/stop)

### Intervalles supportés

Minutes : `1m, 3m, 5m, 15m, 30m, 45m`
Heures : `1H, 2H, 3H, 4H`
Autres : `1D (daily), 1W (weekly), 1M (monthly)`

### Points d'attention critiques

#### Sécurité & Authentification
- ✅ **COMPLÉTÉ** : Support 2FA/TOTP implémenté (PR #30 - Nov 2025)
- ✅ **COMPLÉTÉ** : Credentials masqués dans les logs (mask_sensitive_data)
- ✅ **CONTOURNÉ** : reCAPTCHA invisible → Solution JWT via Playwright (scripts/get_auth_token.py)
- ✅ **COMPLÉTÉ** : Gestion expiration/renouvellement tokens JWT (scripts/token_manager.py)
- 🟡 Nettoyer les credentials de la mémoire après auth

#### WebSocket & Network
- ✅ **COMPLÉTÉ** : Timeout configurable (ws_timeout, TV_WS_TIMEOUT)
- 🔴 **CRITIQUE** : Implémenter retry avec backoff sur connexion WebSocket
- 🔴 **CRITIQUE** : Ajouter timeout cumulatif dans __get_response()
- 🟡 Implémenter auto-reconnect avec backoff exponentiel
- 🟡 Gérer les rate limits de TradingView (HTTP 429)

#### Threading & Concurrence
- ✅ **COMPLÉTÉ** : Audit race conditions (12 corrections - Phase 3)
- ✅ **COMPLÉTÉ** : Shutdown propre avec `_graceful_shutdown()` et timeouts
- ✅ **COMPLÉTÉ** : Locks avec timeout pour éviter deadlocks
- ✅ **COMPLÉTÉ** : Cleanup des références dans threads (finally blocks)

#### Data Processing
- 🟡 Validation robuste des données reçues
- 🟡 Gestion des données manquantes ou corrompues
- 🟡 Parsing plus résilient (regex fragiles actuellement)

#### Tests & Qualité
- ✅ **COMPLÉTÉ** : Tests unitaires ajoutés (384 tests passants)
- ✅ **COMPLÉTÉ** : Tests d'intégration pour les flows critiques
- ✅ **COMPLÉTÉ** : Tests d'intégration 2FA avec mocks HTTP (43 tests)
- ✅ **COMPLÉTÉ** : Tests de charge pour le threading
- ✅ **COMPLÉTÉ** : Tests de sécurité des logs (credentials masqués)
- ✅ **COMPLÉTÉ** : Couverture globale 89.12% (objectif 80% atteint)

---

## Organisation de l'équipe d'agents

Pour mener ce projet à bien, une équipe de **7 agents spécialisés** a été créée :

### 1. 🏗️ Architecte / Lead Technique
**Fichier** : `.claude/agents/architecte-lead.md`
- Vision globale du projet
- Décisions d'architecture
- Revue de code cross-composants
- Documentation technique
- Coordination entre agents

### 2. 🔐 Authentification & Sécurité
**Fichier** : `.claude/agents/auth-security.md`
- Implémentation 2FA
- Gestion sécurisée des credentials
- Token management (génération, renouvellement, expiration)
- Logging sécurisé
- Fichier responsable : `main.py` (méthodes `__auth`, `__init__`)

### 3. 🌐 WebSocket & Network
**Fichier** : `.claude/agents/websocket-network.md`
- Gestion connexions WebSocket
- Retry avec backoff exponentiel
- Timeouts configurables
- Auto-reconnect
- Rate limiting
- Fichiers responsables : `main.py` (méthodes `__create_connection`, `__send_message`)

### 4. 📊 Data Processing
**Fichier** : `.claude/agents/data-processing.md`
- Parsing des données WebSocket
- Création des DataFrames pandas
- Validation des données
- Gestion des données manquantes
- Fichiers responsables : `main.py` (`__create_df`, `__filter_raw_message`)

### 5. ⚡ Threading & Concurrence
**Fichier** : `.claude/agents/threading-concurrency.md`
- Architecture threading de TvDatafeedLive
- Synchronisation (locks, events)
- Prévention race conditions
- Shutdown propre
- Performance
- Fichiers responsables : `datafeed.py`, `consumer.py`, `seis.py`

### 6. 🧪 Tests & Qualité
**Fichier** : `.claude/agents/tests-quality.md`
- Tests unitaires
- Tests d'intégration
- Tests de charge
- Code quality (linting, type hints)
- CI/CD
- Fichiers responsables : Tous + création de `tests/`

### 7. 📚 Documentation & UX
**Fichier** : `.claude/agents/docs-ux.md`
- Documentation utilisateur
- Exemples de code
- Messages d'erreur clairs
- Logging informatif
- README et guides
- Fichiers responsables : `README.md`, docstrings, exemples

---

## Workflow de développement

### Choix de l'agent approprié

Avant de commencer une tâche, identifier quel agent est le plus approprié :

```
❓ Question sur l'architecture globale
→ 🏗️ Architecte / Lead Technique

❓ Problème d'authentification, 2FA, sécurité
→ 🔐 Authentification & Sécurité

❓ Problème de connexion, timeout, WebSocket
→ 🌐 WebSocket & Network

❓ Données incorrectes, parsing, DataFrame
→ 📊 Data Processing

❓ Race condition, deadlock, performance threads
→ ⚡ Threading & Concurrence

❓ Besoin de tests, bug à reproduire
→ 🧪 Tests & Qualité

❓ Documentation, exemples, messages utilisateur
→ 📚 Documentation & UX
```

### Collaboration entre agents

Les agents doivent collaborer sur les tâches complexes :

**Exemple : Implémenter le 2FA**
1. 🏗️ **Architecte** : Définit l'approche générale et les impacts
2. 🔐 **Auth & Sécurité** : Implémente le flow 2FA
3. 🌐 **WebSocket** : Adapte les requêtes d'authentification
4. 🧪 **Tests** : Crée les tests pour valider le 2FA
5. 📚 **Documentation** : Met à jour le README avec exemples

**Exemple : Corriger un bug de threading**
1. 🧪 **Tests** : Reproduit le bug avec un test
2. ⚡ **Threading** : Identifie la race condition
3. 🏗️ **Architecte** : Valide la solution proposée
4. 🧪 **Tests** : Vérifie que le bug est corrigé
5. 📚 **Documentation** : Documente le comportement attendu

---

## Principes de développement

### Code Quality
- ✅ Type hints Python pour toutes les fonctions
- ✅ Docstrings au format numpy/google
- ✅ Gestion d'erreurs explicite (pas de pass silencieux)
- ✅ Logging approprié à tous les niveaux
- ✅ Code self-documented (noms clairs, pas de magic numbers)

### Robustesse
- ✅ Retry avec backoff exponentiel sur les opérations réseau
- ✅ Timeouts configurables partout
- ✅ Validation des inputs utilisateur
- ✅ Graceful degradation (fallback si fonctionnalité indisponible)
- ✅ Cleanup approprié (context managers, destructeurs)

### Performance
- ✅ Minimiser les locks (granularité fine)
- ✅ Éviter les busy loops
- ✅ Utiliser des Events au lieu de polling
- ✅ Pool de connexions si nécessaire

### Sécurité
- ✅ Jamais logger les passwords/tokens
- ✅ Utiliser des variables d'environnement pour secrets
- ✅ Valider et sanitizer tous les inputs
- ✅ HTTPS/WSS uniquement

---

## Patterns de Concurrence

Cette section documente les patterns de threading et concurrence utilisés dans le projet TvDatafeed, suite aux corrections de la Phase 3.

### Constantes de configuration

| Constante | Valeur | Fichier | Description |
|-----------|--------|---------|-------------|
| `RETRY_LIMIT` | 50 | datafeed.py | Nombre max de tentatives pour récupérer des données |
| `SHUTDOWN_TIMEOUT` | 10.0s | datafeed.py | Timeout pour le shutdown gracieux du main thread |
| `CONSUMER_STOP_TIMEOUT` | 5.0s | datafeed.py | Timeout pour l'arrêt des threads consumer |

### Locks par composant

#### TvDatafeedLive (datafeed.py)
| Lock | Attribut | Protège | Usage |
|------|----------|---------|-------|
| Lock principal | `_lock` | `_sat`, opérations publiques | Toutes les méthodes publiques (`new_seis`, `del_seis`, etc.) |
| Lock thread | `_thread_lock` | `_main_thread` | Accès/modification de la référence au thread principal |
| Lock état | `_state_lock` (dans _SeisesAndTrigger) | `_trigger_quit`, `_trigger_dt` | Synchronisation de l'état du trigger |

#### Consumer (consumer.py)
| Lock | Attribut | Protège | Usage |
|------|----------|---------|-------|
| Lock attributs | `_lock` | `_seis`, `_callback`, `_stopped` | Accès thread-safe aux propriétés |

#### Seis (seis.py)
| Lock | Attribut | Protège | Usage |
|------|----------|---------|-------|
| Lock consumers | `_consumers_lock` | `_consumers` | Ajout/suppression de consumers |
| Lock updated | `_updated_lock` | `_updated` | Détection de nouvelles données |

### Patterns de shutdown implementés

#### 1. Flag de shutdown (`_shutdown_in_progress`)
```python
# datafeed.py - TvDatafeedLive
with self._lock:
    if self._shutdown_in_progress:
        return  # Already shutting down
    self._shutdown_in_progress = True
```
- Empêche les nouvelles opérations pendant le shutdown
- Vérifié dans `new_seis()` avant création

#### 2. Event d'interruption (`_trigger_interrupt`)
```python
# datafeed.py - _SeisesAndTrigger
def quit(self):
    with self._state_lock:
        self._trigger_quit = True
    self._trigger_interrupt.set()
```
- Interrompt l'attente du trigger sans busy loop
- Permet un réveil immédiat pour shutdown

#### 3. Flag d'arrêt (`_stopped` dans Consumer)
```python
# consumer.py - Consumer
def stop(self):
    with self._lock:
        if self._stopped:
            return  # Already stopped
        self._stopped = True
    # Signal shutdown via queue
    self._buffer.put(None, timeout=1.0)
```
- Double vérification (flag + None dans queue)
- Timeout sur put pour éviter deadlock

#### 4. Shutdown gracieux (`_graceful_shutdown()`)
```python
# datafeed.py - TvDatafeedLive
def _graceful_shutdown(self):
    # 1. Collecter les consumers sous lock
    # 2. Les arrêter et les joindre hors lock
    # 3. Attendre avec timeout (CONSUMER_STOP_TIMEOUT)
```
- Copie des listes avant itération
- Join avec timeout pour éviter blocage infini
- Logging des threads qui ne terminent pas

### Best practices threading

#### 1. Copier les listes avant itération
```python
# Évite modification pendant itération
seises_copy = list(self._sat)
for seis in seises_copy:
    # Safe iteration
```

#### 2. Acquérir les locks avec timeout
```python
if self._lock.acquire(timeout=timeout) is False:
    return False  # Timeout
try:
    # Critical section
finally:
    self._lock.release()
```

#### 3. Séparer les locks par granularité
```python
self._lock = threading.Lock()         # Opérations principales
self._thread_lock = threading.Lock()  # Accès au thread
# Évite les deadlocks, améliore la concurrence
```

#### 4. Propriétés thread-safe
```python
@property
def seis(self):
    with self._lock:
        return self._seis

@seis.setter
def seis(self, value):
    with self._lock:
        self._seis = value
```

#### 5. Utiliser des Events au lieu de polling
```python
# Bon : Event.wait() avec timeout
interrupted = self._trigger_interrupt.wait(wait_seconds)

# Mauvais : polling actif
while not self._trigger_quit:
    time.sleep(0.1)  # Busy loop
```

#### 6. Cleanup dans finally
```python
def run(self):
    try:
        while True:
            # Processing loop
    finally:
        # Toujours exécuté
        with self._lock:
            self._seis = None
            self._callback = None
            self._stopped = True
```

#### 7. Queue avec timeout
```python
# Lecture avec timeout pour vérification périodique
data = self._buffer.get(timeout=1.0)

# Écriture avec timeout pour éviter blocage
self._buffer.put(data, timeout=5.0)
```

### Diagramme de synchronisation

```
TvDatafeedLive                  Consumer                    Seis
      |                            |                          |
      |-- _lock -------------------|--------------------------|
      |   (opérations globales)    |                          |
      |                            |                          |
      |-- _thread_lock             |                          |
      |   (accès _main_thread)     |                          |
      |                            |                          |
      |                            |-- _lock                  |
      |                            |   (attributs)            |
      |                            |                          |
      |                            |                          |-- _consumers_lock
      |                            |                          |   (liste consumers)
      |                            |                          |
      |                            |                          |-- _updated_lock
      |                            |                          |   (détection new data)
```

---

## Problème reCAPTCHA TradingView (Découverte Nov 2025)

### Contexte

L'authentification via `username/password` échoue systématiquement avec l'erreur :
```
AuthenticationError: Authentication failed: You have been locked out. Please try again later.
```

**Cette erreur est trompeuse** - ce n'est PAS un vrai rate limit.

### Analyse technique

#### Découverte
- TradingView utilise **Google reCAPTCHA v2 invisible** sur la page de login
- Clés reCAPTCHA identifiées :
  - `6Lcqv24UAAAAAIvkElDvwPxD0R8scDnMpizaBcHQ`
  - `6LeQMHgUAAAAAKCYctiBGWYrXN_tvrODSZ7i9dLA`
- Le reCAPTCHA s'exécute via JavaScript dans le navigateur
- Sans validation reCAPTCHA, TradingView renvoie `{"error": "...", "code": "rate_limit"}`

#### Preuve
```python
# Test avec credentials invalides -> "invalid_credentials" (OK)
# Test avec credentials valides -> "rate_limit" (reCAPTCHA bloque)
# Test sans auth (WebSocket) -> Fonctionne parfaitement
```

Cela prouve que :
1. L'IP n'est pas bloquée (sinon tout serait bloqué)
2. Les credentials sont corrects (sinon "invalid_credentials")
3. C'est le reCAPTCHA qui bloque spécifiquement l'auth automatisée

### Impact sur le code

| Fonctionnalité | Status | Détails |
|----------------|--------|---------|
| Auth username/password | ❌ Bloqué | reCAPTCHA invisible |
| Auth via `auth_token` JWT | ✅ Fonctionne | Contourne le reCAPTCHA |
| Mode non authentifié | ✅ Fonctionne | Données limitées |
| 2FA/TOTP | ⚠️ Inutilisable | Requiert auth initiale |
| Symbol Search (REST) | ❌ HTTP 403 | Requiert cookies auth |

### Solution : Authentification via JWT Token

#### Extraction du token
```javascript
// Dans la console du navigateur (F12) après login sur tradingview.com
window.user.auth_token
// Retourne: "eyJhbGciOiJSUzUxMiIsImtpZCI6IkdaeFUiLCJ0eXAiOiJKV1QifQ..."
```

#### Utilisation
```python
from tvDatafeed import TvDatafeed, Interval

# Avec le JWT token extrait
tv = TvDatafeed(auth_token="eyJhbGciOiJSUzUxMiIs...")

# Accès complet aux données Pro/Premium
df = tv.get_hist('BTCUSDT', 'BINANCE', Interval.in_1_hour, n_bars=5000)
```

#### Structure du JWT Token
```json
{
  "user_id": 1317342,
  "exp": 1763865315,           // Expiration timestamp
  "iat": 1763850915,           // Issued at
  "plan": "pro_premium",       // Subscription plan
  "perm": "cme,nymex_mini,...", // Permissions exchanges
  "max_charts": 8,
  "max_active_alerts": 400,
  "max_connections": 50
}
```

### Tokens importants (à ne PAS confondre)

| Token | Cookie/Source | Usage | Fonctionne ? |
|-------|---------------|-------|--------------|
| `auth_token` JWT | `window.user.auth_token` | WebSocket API | ✅ OUI |
| `sessionid` | Cookie HTTP | Session web | ❌ NON |
| CSRF token | Meta tag HTML | Formulaires | ❌ NON |

### Recommandations pour le code

1. **Documenter clairement** dans README.md (fait)
2. **Améliorer le message d'erreur** pour guider l'utilisateur vers la solution JWT
3. **Ajouter un helper** pour valider le format JWT token
4. **Considérer** l'auto-refresh du token (si possible via API)

### Tests d'intégration avec JWT

Un script de test réel a été créé : `tests/integration/test_real_connection.py`

Résultats avec JWT token (Pro Premium) :
- ✅ Crypto (BTCUSDT) : 100 bars
- ✅ Stocks US (AAPL) : 50 bars
- ✅ Forex (EURUSD) : 50 bars
- ✅ Stocks EU (TotalEnergies) : 30 bars
- ✅ Multiple intervals : 5/5
- ✅ Large data (5000 bars) : OK
- ✅ Commodities (Oil, Gold) : OK

---

## Roadmap prioritaire

### Phase 1 : Fondations solides ✅ COMPLÉTÉ (Nov 2025)
- [x] ✅ Implémenter le support 2FA (PR #30 - commit a5288f3)
- [x] ✅ Améliorer la gestion d'erreurs dans `__auth` (exceptions personnalisées)
- [x] ✅ Rendre les timeouts configurables (ws_timeout, TV_WS_TIMEOUT)
- [x] ✅ Date Range Search (start_date, end_date) - PR #69
- [x] ✅ Verbose logging control (verbose parameter) - PR #37
- [x] ✅ Ajouter retry avec backoff sur connexion WebSocket

### Phase 2 : Robustesse network ✅ COMPLÉTÉ (Nov 2025)
- [x] ✅ **CRITIQUE** : Retry WebSocket avec `retry_with_backoff()` dans `__create_connection()`
- [x] ✅ **CRITIQUE** : Timeout cumulatif dans `__get_response()` (TV_MAX_RESPONSE_TIME)
- [ ] Auto-reconnect WebSocket (Phase 3)
- [ ] Gestion rate limiting TradingView HTTP 429 (Phase 3)
- [x] ✅ Meilleure gestion des timeouts (configurable via param/env)

### Phase 3 : Threading bullet-proof ✅ COMPLÉTÉ (Nov 2025)
- [x] ✅ Audit complet race conditions (12 corrections)
- [x] ✅ Améliorer shutdown propre (`_graceful_shutdown()`, flags, timeouts)
- [x] ✅ Tests de charge threading
- [x] ✅ Documentation patterns concurrence (section "Patterns de Concurrence")

### Phase 4 : Tests & Qualité ✅ COMPLÉTÉ (Nov 2025)
- [x] ✅ Suite tests unitaires (384 tests passants)
- [x] ✅ Tests d'intégration pour flows critiques
- [x] ✅ CI/CD pipeline (GitHub Actions)
- [x] ✅ Coverage 89.12% (objectif 80% dépassé)
- [x] ✅ Tests d'intégration 2FA avec mocks HTTP (43 tests)
- [x] ✅ Tests unitaires datafeed.py (71 tests)
- [x] ✅ Tests exceptions et config (100% couverture)

### Phase 5 : UX & Documentation ✅ COMPLÉTÉ (Nov 2025)
- [x] ✅ Exemples complets (2FA, date range, quiet mode, CAPTCHA)
- [x] ✅ Guide de troubleshooting (README.md)
- [x] ✅ Messages d'erreur clairs (exceptions personnalisées)
- [x] ✅ Documentation API complète (MkDocs Material)
  - 19 fichiers de documentation
  - API Reference complete (TvDatafeed, TvDatafeedLive, Seis, Consumer, Exceptions, Config)
  - Getting Started guides (installation, quickstart, authentication)
  - Examples (basic, 2fa, live-feed, date-range)

---

## Utilisation de ce document

### Pour les agents Claude
1. **Lire ce document** avant toute intervention sur le projet
2. **Consulter le profil de votre agent** dans `.claude/agents/`
3. **Identifier les collaborations** nécessaires avec autres agents
4. **Respecter les principes** de développement listés ci-dessus
5. **Mettre à jour ce document** si l'architecture évolue

### Pour les développeurs humains
- Ce document sert de référence centrale pour comprendre le projet
- Les décisions d'architecture sont documentées ici
- Les agents Claude suivent ces guidelines strictement

---

## Ressources

### Documentation externe
- [TradingView API (unofficial)](https://github.com/tradingview)
- [WebSocket Python](https://websocket-client.readthedocs.io/)
- [Threading Python](https://docs.python.org/3/library/threading.html)
- [Pandas DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html)

### Fichiers clés du projet
- `tvDatafeed/main.py` - Cœur du système
- `tvDatafeed/datafeed.py` - Live feed
- `requirements.txt` - Dépendances
- `README.md` - Documentation utilisateur

---

**Version** : 1.6
**Dernière mise à jour** : 2025-11-22
**Statut** : ✅ Phase 1, Phase 2, Phase 3, Phase 4 et Phase 5 complétées | ⚠️ reCAPTCHA bloque auth username/password

---

## Historique des mises à jour

### Version 1.6 (2025-11-22)
- ✅ Phase 5 complétée : UX & Documentation
- ✅ Documentation API complète avec MkDocs Material
- ✅ Configuration mkdocs.yml avec Material theme, navigation tabs, search, code highlighting
- ✅ 19 fichiers de documentation créés :
  - `docs/index.md` : Page d'accueil avec features et quick start
  - `docs/api/index.md` : Vue d'ensemble API avec liens vers toutes les classes
  - `docs/api/tvdatafeed.md` : Documentation complète TvDatafeed (paramètres, méthodes, exemples)
  - `docs/api/tvdatafeedlive.md` : Documentation TvDatafeedLive avec architecture threading
  - `docs/api/helpers.md` : Seis, Consumer, utils, validators
  - `docs/api/exceptions.md` : Hiérarchie complète des exceptions avec patterns de handling
  - `docs/api/configuration.md` : NetworkConfig, AuthConfig, DataConfig, ThreadingConfig
  - `docs/getting-started/installation.md`, `quickstart.md`, `authentication.md`
  - `docs/examples/basic.md`, `2fa.md`, `live-feed.md`, `date-range.md`
- ✅ Tables de paramètres avec types, defaults, descriptions
- ✅ Exemples de code pour chaque méthode (tabs pour différentes options)
- ✅ Documentation complète des variables d'environnement
- ✅ Patterns avancés : keyring, AWS Secrets Manager, retry patterns
- ✅ Revue architecturale Phase 5 : 9/10 - APPROUVÉ

### Version 1.5 (2025-11-22)
- 🔴 **DÉCOUVERTE CRITIQUE** : reCAPTCHA invisible bloque l'authentification username/password
- ✅ Documenté la solution de contournement via JWT auth_token
- ✅ Mise à jour README.md avec section détaillée "reCAPTCHA / Rate Limit Issue"
- ✅ Ajout section technique dans CLAUDE.md "Problème reCAPTCHA TradingView"
- ✅ Création script de test réel : `tests/integration/test_real_connection.py`
- ✅ Tests d'intégration réels validés avec JWT token (7/9 tests passent)
- 📝 Clés reCAPTCHA TradingView identifiées
- 📝 Différence documentée entre `sessionid` (cookie) et `auth_token` (JWT)

### Version 1.6 (2025-11-23)
- ✅ **Scripts d'automatisation token** créés :
  - `scripts/get_auth_token.py` : Extraction JWT via Playwright + stealth mode
  - `scripts/token_manager.py` : Gestion lifecycle tokens (cache, validation, refresh)
  - `examples/automated_data_fetch.py` : Exemple utilisation serveur automatisé
- ✅ **Tests complets** pour token scripts :
  - `tests/unit/test_token_manager.py` : 28 tests unitaires
  - `tests/integration/test_token_integration.py` : 13 tests d'intégration
  - Couverture : token_manager.py 66%, get_auth_token.py 41%
- ✅ **Fonctionnalités token_manager** :
  - `get_valid_token()` : Récupère token valide (env > cache > refresh)
  - `is_token_valid()` : Valide expiration avec threshold configurable
  - `get_token_info()` : Extrait plan, permissions, expiration du JWT
  - `save_cached_token()` / `get_cached_token()` : Cache sécurisé
  - `refresh_token()` : Renouvellement automatique via Playwright
- 📝 Documentation mise à jour (CLAUDE.md, README.md)

### Version 1.4 (2025-11-22)
- ✅ Phase 4 complétée : Tests & Qualité
- ✅ Couverture globale : 68.73% -> **89.12%** (objectif 80% dépassé)
- ✅ Tests passants : 250 -> **384 tests**
- ✅ Nouveaux fichiers de tests créés :
  - `tests/unit/test_datafeed.py` : 71 tests pour TvDatafeedLive et _SeisesAndTrigger
  - `tests/unit/test_exceptions.py` : Tests complets pour toutes les exceptions
  - `tests/unit/test_config.py` : Tests pour NetworkConfig, AuthConfig, DataConfig, ThreadingConfig
  - `tests/integration/test_2fa_integration.py` : 43 tests d'intégration 2FA avec mocks HTTP
- ✅ Couverture par fichier :
  - `__init__.py`: 100%
  - `config.py`: 100%
  - `exceptions.py`: 100%
  - `seis.py`: 100%
  - `validators.py`: 98.92%
  - `utils.py`: 95.58%
  - `consumer.py`: 94.51%
  - `datafeed.py`: 83.29%
  - `main.py`: 80.51%
- ✅ Revue architecturale : 9/10 - APPROUVÉ

### Version 1.3 (2025-11-22)
- ✅ Phase 3 complétée : Threading bullet-proof
- ✅ Audit complet des race conditions (12 corrections dans datafeed.py, consumer.py, seis.py)
- ✅ Shutdown propre implementé (`_graceful_shutdown()`, `_shutdown_in_progress` flag)
- ✅ Locks séparés par granularité (`_lock`, `_thread_lock`, `_state_lock`)
- ✅ Propriétés thread-safe dans Consumer (`seis`, `callback` avec lock)
- ✅ Locks dédiés dans Seis (`_consumers_lock`, `_updated_lock`)
- ✅ Copie des listes avant itération pour éviter modification concurrente
- ✅ Timeouts sur toutes les opérations de queue et join
- ✅ Cleanup des références dans finally blocks
- ✅ Documentation complète des patterns de concurrence (nouvelle section CLAUDE.md)

### Version 1.2 (2025-11-22)
- ✅ Phase 2 complétée : Robustesse network
- ✅ Retry WebSocket avec `retry_with_backoff()` dans `__create_connection()`
- ✅ Timeout cumulatif dans `__get_response()` avec TV_MAX_RESPONSE_TIME
- ✅ 20 tests supplémentaires pour Phase 2
- ✅ Revue architecturale : 8.5/10 - APPROUVÉ

### Version 1.1 (2025-11-22)
- ✅ PR #30 mergée : Support 2FA/TOTP complet
- ✅ PR #69 intégrée : Date Range Search
- ✅ PR #37 intégrée : Verbose logging control
- ✅ Revue de sécurité par agent Auth & Sécurité : 8.5/10 - APPROUVÉ
- ✅ 15+ tests unitaires pour 2FA
