# Équipe d'Agents Claude - TvDatafeed

Ce dossier contient les profils de tous les agents Claude spécialisés pour le projet TvDatafeed.

## Vue d'ensemble

L'équipe est composée de **7 agents spécialisés**, chacun expert dans son domaine :

| Agent | Domaine | Fichier | Priorité |
|-------|---------|---------|----------|
| 🏗️ **Architecte Lead** | Architecture, design, coordination | [architecte-lead.md](architecte-lead.md) | Toujours consulter |
| 🔐 **Auth & Sécurité** | Authentification, 2FA, tokens, sécurité | [auth-security.md](auth-security.md) | 🔴 URGENT (2FA) |
| 🌐 **WebSocket & Network** | Connexions, retry, timeouts, résilience | [websocket-network.md](websocket-network.md) | 🔴 URGENT |
| 📊 **Data Processing** | Parsing, validation, DataFrames | [data-processing.md](data-processing.md) | 🟡 Important |
| ⚡ **Threading & Concurrence** | Threading, locks, race conditions | [threading-concurrency.md](threading-concurrency.md) | 🔴 URGENT |
| 🧪 **Tests & Qualité** | Tests, coverage, CI/CD, linting | [tests-quality.md](tests-quality.md) | 🔴 URGENT |
| 📚 **Documentation & UX** | Docs, exemples, messages d'erreur | [docs-ux.md](docs-ux.md) | 🟡 Important |

## Comment utiliser les agents ?

### Pour les agents Claude

1. **Avant toute tâche** :
   - Lire `CLAUDE.md` à la racine du projet
   - Identifier quel agent tu es (ou quel agent consulter)
   - Lire le profil de ton agent dans ce dossier

2. **Pendant le travail** :
   - Respecter les responsabilités définies dans ton profil
   - Consulter les autres agents si nécessaire (voir section "Interactions")
   - Suivre les principes et patterns de ton domaine

3. **À la fin** :
   - Mettre à jour `CLAUDE.md` si décision majeure
   - Documenter les changements importants
   - Coordonner avec l'Architecte pour validation

### Pour les développeurs humains

Ces profils servent de **référence** pour comprendre :
- Comment le projet est organisé
- Quelles sont les bonnes pratiques par domaine
- Comment les agents Claude vont travailler sur le code

## Guide de sélection d'agent

### Vous avez une question sur...

**Architecture, design patterns, décisions techniques ?**
→ 🏗️ **Architecte Lead** ([architecte-lead.md](architecte-lead.md))

**Authentification, 2FA, sécurité, credentials ?**
→ 🔐 **Auth & Sécurité** ([auth-security.md](auth-security.md))

**Connexions WebSocket, timeouts, retry logic ?**
→ 🌐 **WebSocket & Network** ([websocket-network.md](websocket-network.md))

**Parsing de données, validation OHLC, DataFrames ?**
→ 📊 **Data Processing** ([data-processing.md](data-processing.md))

**Threading, locks, race conditions, deadlocks ?**
→ ⚡ **Threading & Concurrence** ([threading-concurrency.md](threading-concurrency.md))

**Tests, mocks, coverage, CI/CD ?**
→ 🧪 **Tests & Qualité** ([tests-quality.md](tests-quality.md))

**Documentation, README, exemples, messages d'erreur ?**
→ 📚 **Documentation & UX** ([docs-ux.md](docs-ux.md))

## Workflows typiques

### Workflow 1 : Implémenter le 2FA

```
1. 🏗️ Architecte Lead
   → Définir l'approche générale (module séparé ? intégration ?)
   → Valider l'architecture proposée

2. 🔐 Auth & Sécurité
   → Implémenter le flow 2FA complet
   → Gérer les différentes méthodes (TOTP, SMS, etc.)
   → Sécuriser le stockage des secrets

3. 🌐 WebSocket & Network
   → Adapter les requêtes d'authentification
   → Gérer les timeouts spécifiques au 2FA

4. 🧪 Tests & Qualité
   → Créer les tests (mocking TradingView API)
   → Tester tous les scénarios (success, failure, timeout)

5. 📚 Documentation & UX
   → Mettre à jour README avec guide 2FA
   → Créer des exemples de code
   → Améliorer les messages d'erreur

6. 🏗️ Architecte Lead
   → Review final
   → Validation que tout est cohérent
```

### Workflow 2 : Corriger un bug de threading

```
1. 🧪 Tests & Qualité
   → Reproduire le bug avec un test
   → Identifier les conditions exactes

2. ⚡ Threading & Concurrence
   → Analyser le code (race condition ? deadlock ?)
   → Proposer une solution

3. 🏗️ Architecte Lead
   → Valider que la solution ne casse pas l'architecture
   → Approuver ou proposer une alternative

4. ⚡ Threading & Concurrence
   → Implémenter le fix
   → Ajouter des safeguards

5. 🧪 Tests & Qualité
   → Vérifier que le test passe maintenant
   → Ajouter des tests de régression
   → Stress test pour confirmer le fix

6. 📚 Documentation & UX
   → Documenter le comportement attendu
   → Améliorer les logs si nécessaire
```

### Workflow 3 : Améliorer la résilience réseau

```
1. 🏗️ Architecte Lead
   → Définir la stratégie (retry avec backoff, circuit breaker, etc.)
   → Valider l'approche

2. 🌐 WebSocket & Network
   → Implémenter retry logic avec backoff exponentiel
   → Ajouter rate limiting
   → Rendre les timeouts configurables

3. 📊 Data Processing
   → S'assurer que le parsing gère les retries correctement
   → Gérer les données partielles

4. 🧪 Tests & Qualité
   → Tests avec simulation de timeouts
   → Tests avec simulation de déconnexions
   → Tests de rate limiting

5. 📚 Documentation & UX
   → Documenter la configuration réseau
   → Exemples avec configuration custom
   → Guide de troubleshooting

6. 🏗️ Architecte Lead
   → Review et validation finale
```

## Principes de collaboration entre agents

### 1. Communication claire
Chaque agent doit :
- Expliquer clairement son raisonnement
- Documenter ses décisions
- Demander validation quand nécessaire

### 2. Respect des responsabilités
- Ne pas empiéter sur le domaine d'un autre agent
- Demander la collaboration quand le problème touche plusieurs domaines
- Consulter l'Architecte en cas de doute

### 3. Cohérence du code
- Suivre les patterns établis
- Respecter les guidelines du projet
- Maintenir un style uniforme

### 4. Documentation systématique
- Documenter les décisions importantes
- Mettre à jour `CLAUDE.md` si changement architectural
- Créer des exemples testés

### 5. Qualité avant vitesse
- Préférer une solution robuste à une solution rapide
- Tester systématiquement
- Penser à la maintenabilité

## Matrice de responsabilités

| Fichier/Composant | Responsable Principal | Collaborateurs |
|-------------------|----------------------|----------------|
| `CLAUDE.md` | 🏗️ Architecte Lead | Tous |
| `tvDatafeed/main.py` - `__auth()` | 🔐 Auth & Sécurité | 🌐 WebSocket |
| `tvDatafeed/main.py` - `__create_connection()` | 🌐 WebSocket & Network | 📊 Data Processing |
| `tvDatafeed/main.py` - `__create_df()` | 📊 Data Processing | - |
| `tvDatafeed/datafeed.py` | ⚡ Threading & Concurrence | 🌐 WebSocket, 📊 Data |
| `tvDatafeed/consumer.py` | ⚡ Threading & Concurrence | - |
| `tvDatafeed/seis.py` | ⚡ Threading & Concurrence | - |
| `tests/` | 🧪 Tests & Qualité | Tous |
| `README.md` | 📚 Documentation & UX | 🏗️ Architecte |
| `examples/` | 📚 Documentation & UX | 🧪 Tests |

## FAQ

### Quand consulter l'Architecte Lead ?

**Toujours** pour :
- Changements d'architecture majeurs
- Nouvelles abstractions / classes / modules
- Décisions impactant plusieurs composants
- Choix de bibliothèques externes
- Refactorings importants

**Parfois** pour :
- Implémentation d'une nouvelle feature
- Choix d'un pattern de design
- Résolution d'un bug complexe

### Peut-on travailler en parallèle ?

**Oui**, si :
- Les domaines sont clairement séparés
- Pas de dépendances entre les tâches
- Coordination via l'Architecte Lead

**Non**, si :
- Les changements touchent les mêmes fichiers
- Une tâche dépend du résultat de l'autre
- Risque de conflit conceptuel

### Comment résoudre un désaccord entre agents ?

1. Discussion entre les agents concernés
2. Chacun présente son raisonnement
3. Consultation de l'Architecte Lead
4. Décision finale de l'Architecte
5. Documentation de la décision

### Que faire si un profil d'agent est incomplet ?

1. Identifier ce qui manque
2. Proposer un ajout/modification
3. Soumettre à l'Architecte Lead
4. Mettre à jour le profil

---

## Mise à jour de cette équipe

Cette équipe d'agents a été créée le **2025-11-20**.

Pour mettre à jour :
1. Modifier le profil de l'agent concerné
2. Mettre à jour ce README si nécessaire
3. Informer tous les agents du changement
4. Documenter la raison du changement

---

## Ressources

- **Documentation centrale** : `../CLAUDE.md`
- **Code du projet** : `../tvDatafeed/`
- **Tests** : `../tests/` (à créer)
- **Exemples** : `../examples/` (à créer)

---

**Bonne collaboration !** 🚀
