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
  - ❌ Pas de retry automatique sur connexion WebSocket
  - ❌ Pas de timeout cumulatif dans __get_response()
  - ❌ Rate limiting TradingView non géré

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
- 🟡 Gérer l'expiration et le renouvellement des tokens
- 🟡 Nettoyer les credentials de la mémoire après auth

#### WebSocket & Network
- ✅ **COMPLÉTÉ** : Timeout configurable (ws_timeout, TV_WS_TIMEOUT)
- 🔴 **CRITIQUE** : Implémenter retry avec backoff sur connexion WebSocket
- 🔴 **CRITIQUE** : Ajouter timeout cumulatif dans __get_response()
- 🟡 Implémenter auto-reconnect avec backoff exponentiel
- 🟡 Gérer les rate limits de TradingView (HTTP 429)

#### Threading & Concurrence
- 🔴 Vérifier les race conditions potentielles
- 🟡 Améliorer la gestion du shutdown propre
- 🟡 Éviter les deadlocks avec timeouts appropriés
- 🟡 Memory leaks dans les threads long-running

#### Data Processing
- 🟡 Validation robuste des données reçues
- 🟡 Gestion des données manquantes ou corrompues
- 🟡 Parsing plus résilient (regex fragiles actuellement)

#### Tests & Qualité
- ✅ **COMPLÉTÉ** : Tests unitaires ajoutés (100+ tests, 15+ pour 2FA)
- ✅ **COMPLÉTÉ** : Tests d'intégration pour les flows critiques
- 🟡 Ajouter tests d'intégration 2FA (avec mocks HTTP)
- 🟡 Tests de charge pour le threading
- 🟡 Tests de sécurité des logs (credentials masqués)

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

### Phase 3 : Threading bullet-proof
- [ ] Audit complet race conditions
- [ ] Améliorer shutdown propre
- [ ] Tests de charge threading
- [ ] Documentation patterns concurrence

### Phase 4 : Tests & Qualité ✅ PARTIELLEMENT COMPLÉTÉ
- [x] ✅ Suite tests unitaires (100+ tests)
- [x] ✅ Tests d'intégration pour flows critiques
- [x] ✅ CI/CD pipeline (GitHub Actions)
- [ ] Coverage > 80%
- [ ] Tests d'intégration 2FA avec mocks HTTP

### Phase 5 : UX & Documentation ✅ PARTIELLEMENT COMPLÉTÉ
- [x] ✅ Exemples complets (2FA, date range, quiet mode, CAPTCHA)
- [x] ✅ Guide de troubleshooting (README.md)
- [x] ✅ Messages d'erreur clairs (exceptions personnalisées)
- [ ] Documentation API complète (Sphinx/MkDocs)

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

**Version** : 1.2
**Dernière mise à jour** : 2025-11-22
**Statut** : ✅ Phase 1 et Phase 2 complétées

---

## Historique des mises à jour

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
