# Plan d'Action - Résolution des Issues GitHub

**Date**: 2025-11-21
**Issues à traiter**: 43 issues ouvertes + 5 pull requests
**Agents mobilisés**: 7 agents spécialisés

---

## Classification par Criticité

### 🔴 CRITIQUE (P0) - À corriger immédiatement

| Issue | Titre | Agent | Complexité | Status |
|-------|-------|-------|------------|--------|
| #70 | SyntaxWarning: invalid escape sequence | Data Processing | ⭐ Facile | ✅ RÉSOLU |
| #62 | Token is None - recaptcha_required | Auth & Security | ⭐⭐⭐ Difficile | 🔄 En cours |
| #63 | tv.get_hist() stopped working | Data Processing | ⭐⭐ Moyen | 🔄 En cours |
| #66 | Getting driver error | WebSocket & Network | ⭐⭐ Moyen | ⏳ Planifié |

### 🟠 IMPORTANT (P1) - À corriger dans les 24h

| Issue | Titre | Agent | Complexité | Status |
|-------|-------|-------|------------|--------|
| #72 | Timezone issues | Data Processing | ⭐⭐ Moyen | ⏳ Planifié |
| #65 | Market holidays (data shifts) | Data Processing | ⭐⭐⭐ Difficile | ⏳ Planifié |
| #74 | Splits and Dividends Adjustment | Data Processing | ⭐⭐⭐ Difficile | ⏳ Planifié |
| #58 | Unable to fetch FXCM and ICE | WebSocket & Network | ⭐⭐ Moyen | ⏳ Planifié |

### 🟡 MOYEN (P2) - Features et améliorations

| Issue | Titre | Agent | Complexité | Status |
|-------|-------|-------|------------|--------|
| #64 | Strike History data for NIFTY | Data Processing | ⭐⭐ Moyen | ⏳ Planifié |
| #59 | Continue future B-ADJ data | Data Processing | ⭐⭐ Moyen | ⏳ Planifié |
| #57 | Getting company data | Data Processing | ⭐⭐ Moyen | ⏳ Planifié |
| #60 | YouTube video private | Documentation & UX | ⭐ Facile | ⏳ Planifié |

### 🟢 FAIBLE (P3) - Nice to have

| Issue | Titre | Agent | Complexité | Status |
|-------|-------|-------|------------|--------|
| Autres issues | 30+ autres issues | Divers | Variable | ⏳ À analyser |

---

## Pull Requests à Intégrer

| PR | Titre | Intérêt | Agent | Status |
|----|-------|---------|-------|--------|
| #73 | Fix overview batch | Élevé | Data Processing | ⏳ Analyse requise |
| #69 | Added search interval | Élevé | Data Processing | ⏳ Analyse requise |
| #61 | Async operations | Moyen | Threading & Concurrency | ⏳ Analyse requise |
| #37 | Added verbose | Faible | Documentation & UX | ⏳ Analyse requise |
| #30 | Pro data | Élevé | Auth & Security | ⏳ Analyse requise |

---

## Plan d'Exécution Détaillé

### Phase 1: Issues Critiques (En cours)

#### ✅ Issue #70 - SyntaxWarning
**Agent**: Data Processing
**Status**: RÉSOLU
**Action**: Ajout de raw strings (r-prefix) aux regex
**Commit**: cb5b17c

#### 🔄 Issue #62 - reCAPTCHA Authentication
**Agent**: Auth & Security
**Problème**:
- TradingView exige reCAPTCHA lors de l'authentification
- Token reste None même avec credentials valides
- Code erreur: "recaptcha_required"

**Solutions proposées**:
1. ❌ Bypass automatique du CAPTCHA (impossible/non éthique)
2. ✅ Manuel token extraction workflow
3. ✅ Browser-based auth avec Selenium
4. ✅ Documentation pour workaround manuel

**Plan d'action**:
- [ ] Détecter le code "recaptcha_required" dans la réponse
- [ ] Lever TwoFactorRequiredError ou CaptchaRequiredError
- [ ] Documenter le workaround manuel (extraction token du browser)
- [ ] Optionnel: Implémenter support Selenium pour CAPTCHA manuel
- [ ] Ajouter exemple dans documentation

**Complexité**: ⭐⭐⭐ Difficile
**Temps estimé**: 2-3h

#### 🔄 Issue #63 - get_hist() Connection Issues
**Agent**: Data Processing + WebSocket & Network
**Problème**:
- "Connection timed out"
- "no data, please check the exchange and symbol"
- Format symbol incorrect

**Causes identifiées**:
1. Symboles doivent inclure le préfixe exchange: "BINANCE:BTCUSDT"
2. Search function non fiable
3. Timeouts trop courts

**Plan d'action**:
- [x] Validation du format symbol (déjà fait avec Validators)
- [x] Messages d'erreur clairs (déjà fait avec DataNotFoundError)
- [ ] Améliorer search_symbol() pour être plus fiable
- [ ] Auto-détecter format "EXCHANGE:SYMBOL"
- [ ] Documentation sur le format correct

**Complexité**: ⭐⭐ Moyen
**Temps estimé**: 1-2h

#### ⏳ Issue #66 - Driver Error
**Agent**: WebSocket & Network
**Problème**: Non spécifié dans l'analyse
**Action**: Analyser l'issue en détail

---

### Phase 2: Issues Importantes (Planifiées)

#### Issue #72 - Timezone
**Agent**: Data Processing
**Problème**: Problèmes de timezone dans les données
**Plan d'action**:
- [ ] Analyser le problème exact
- [ ] Standardiser sur UTC
- [ ] Ajouter paramètre timezone optionnel
- [ ] Tests pour différentes timezones

**Complexité**: ⭐⭐ Moyen
**Temps estimé**: 2h

#### Issue #65 - Market Holidays
**Agent**: Data Processing
**Problème**: Décalage des données lors des jours fériés
**Plan d'action**:
- [ ] Identifier la cause du décalage
- [ ] Implémenter détection des jours fériés
- [ ] Corriger l'alignement des données
- [ ] Tests avec données incluant holidays

**Complexité**: ⭐⭐⭐ Difficile
**Temps estimé**: 3-4h

#### Issue #74 - Splits and Dividends
**Agent**: Data Processing
**Problème**: Ajustement pour splits et dividendes
**Plan d'action**:
- [ ] Analyser les besoins
- [ ] Implémenter ajustement automatique
- [ ] Ajouter paramètre adjustment (optional)
- [ ] Documentation

**Complexité**: ⭐⭐⭐ Difficile
**Temps estimé**: 3-4h

#### Issue #58 - FXCM and ICE Exchanges
**Agent**: WebSocket & Network
**Problème**: Impossible de récupérer données de FXCM et ICE
**Plan d'action**:
- [ ] Tester connexion à ces exchanges
- [ ] Identifier le problème spécifique
- [ ] Corriger ou documenter limitations

**Complexité**: ⭐⭐ Moyen
**Temps estimé**: 1-2h

---

### Phase 3: Pull Requests (À analyser)

#### PR #73 - Fix Overview Batch
**Commits**: 9 commits
**Features**:
- Get overview and fundamental data
- Add bulk feature
- Add stream feature
- Add rate limit
- Exception handling in send_message

**Action**: Analyser et intégrer si pertinent

#### PR #69 - Search Interval
**Action**: Analyser pour améliorer search_symbol()

#### PR #61 - Async Operations
**Action**: Analyser pour future version async

---

## Affectation des Agents

### 🔐 Agent Auth & Security
**Responsabilités**:
- Issue #62 (reCAPTCHA)
- PR #30 (Pro data)
- Documentation sécurité

**Tâches**:
1. Détecter et gérer recaptcha_required
2. Créer CaptchaRequiredError
3. Documenter workaround manuel
4. Explorer intégration Selenium optionnelle

### 🌐 Agent WebSocket & Network
**Responsabilités**:
- Issue #66 (driver error)
- Issue #58 (FXCM/ICE)
- Améliorer timeouts et retry

**Tâches**:
1. Analyser driver error
2. Tester connexions FXCM/ICE
3. Implémenter retry avec backoff
4. Améliorer error messages

### 📊 Agent Data Processing
**Responsabilités**:
- Issue #63 (get_hist)
- Issue #72 (timezone)
- Issue #65 (holidays)
- Issue #74 (splits/dividends)
- PR #73 (overview batch)
- PR #69 (search interval)

**Tâches**:
1. Améliorer search_symbol()
2. Implémenter timezone handling
3. Corriger market holidays
4. Ajouter splits/dividends adjustment
5. Analyser et intégrer PR #73

### ⚡ Agent Threading & Concurrency
**Responsabilités**:
- PR #61 (async operations)
- Améliorer TvDatafeedLive

**Tâches**:
1. Analyser PR #61
2. Améliorer threading safety
3. Explorer async/await pattern

### 🧪 Agent Tests & Quality
**Responsabilités**:
- Tests pour toutes corrections
- Validation non-regression

**Tâches**:
1. Tests pour chaque issue corrigée
2. Tests d'intégration
3. Validation coverage

### 📚 Agent Documentation & UX
**Responsabilités**:
- Issue #60 (YouTube video)
- Documentation workarounds
- Exemples

**Tâches**:
1. Documenter workaround CAPTCHA
2. Documenter format symboles
3. Mettre à jour README
4. Exemples pour edge cases

### 🏗️ Agent Architecte Lead
**Responsabilités**:
- Coordination globale
- Validation architecture
- Code review

**Tâches**:
1. Valider approche pour chaque issue
2. Code review des corrections
3. S'assurer cohérence globale

---

## Calendrier d'Exécution

### Aujourd'hui (Session actuelle)
- [x] Issue #70 ✅
- [ ] Issue #62 (reCAPTCHA) - 2h
- [ ] Issue #63 (get_hist) - 1h
- [ ] Issue #66 (driver) - 1h
- [ ] Tests et validation - 1h

### Session suivante
- [ ] Issue #72 (timezone) - 2h
- [ ] Issue #65 (holidays) - 3h
- [ ] Issue #74 (splits) - 3h
- [ ] Issue #58 (FXCM/ICE) - 2h

### Futures sessions
- [ ] Analyse et intégration PRs
- [ ] Issues P2 et P3
- [ ] Amélioration générale

---

## Métriques de Succès

**Objectifs**:
- ✅ Résoudre 100% des issues P0 (critiques)
- 🎯 Résoudre 80%+ des issues P1 (importantes)
- 🎯 Intégrer 3/5 PRs pertinentes
- 🎯 Maintenir coverage >80%
- 🎯 0 régression sur fonctionnalités existantes

**Progress Tracking**:
- Issues résolues: 1/43 (2%)
- Issues critiques: 1/4 (25%)
- PRs intégrées: 0/5 (0%)
- Coverage: 30.29% → Target 80%

---

## Notes Importantes

1. **Backward Compatibility**: Toutes les corrections doivent maintenir la compatibilité
2. **Tests**: Chaque correction doit avoir des tests
3. **Documentation**: Chaque workaround doit être documenté
4. **Code Review**: Architecte Lead valide chaque changement majeur

---

**Dernière mise à jour**: 2025-11-21
**Responsable**: Claude Agent Team
