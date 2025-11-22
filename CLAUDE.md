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
- **Limitations actuelles** :
  - ❌ Pas de support 2FA
  - ❌ Timeout WebSocket fixe (5 secondes)
  - ❌ Pas de retry automatique sur échec d'authentification
  - ❌ Gestion d'erreurs basique

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
- 🔴 **URGENT** : Implémenter le support 2FA
- 🔴 Sécuriser le stockage des credentials
- 🟡 Gérer l'expiration et le renouvellement des tokens
- 🟡 Logs sans exposer les credentials

#### WebSocket & Network
- 🔴 Améliorer la gestion des déconnexions
- 🟡 Rendre le timeout configurable
- 🟡 Implémenter auto-reconnect avec backoff exponentiel
- 🟡 Gérer les rate limits de TradingView

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
- 🔴 **URGENT** : Ajouter des tests unitaires
- 🔴 Tests d'intégration pour les flows critiques
- 🟡 Tests de charge pour le threading
- 🟡 Mocking de TradingView pour tests isolés

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

### Phase 1 : Fondations solides (URGENT)
- [ ] Implémenter le support 2FA
- [ ] Améliorer la gestion d'erreurs dans `__auth`
- [ ] Rendre les timeouts configurables
- [ ] Ajouter retry avec backoff sur auth

### Phase 2 : Robustesse network
- [ ] Auto-reconnect WebSocket
- [ ] Backoff exponentiel sur échecs
- [ ] Gestion rate limiting TradingView
- [ ] Meilleure gestion des timeouts

### Phase 3 : Threading bullet-proof
- [ ] Audit complet race conditions
- [ ] Améliorer shutdown propre
- [ ] Tests de charge threading
- [ ] Documentation patterns concurrence

### Phase 4 : Tests & Qualité
- [ ] Suite tests unitaires complète
- [ ] Tests d'intégration
- [ ] CI/CD pipeline
- [ ] Coverage > 80%

### Phase 5 : UX & Documentation
- [ ] Exemples complets pour tous les use cases
- [ ] Guide de troubleshooting
- [ ] Messages d'erreur ultra-clairs
- [ ] Documentation API complète

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

**Version** : 1.0
**Dernière mise à jour** : 2025-11-20
**Statut** : 🔴 En développement actif
