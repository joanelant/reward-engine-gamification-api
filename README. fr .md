# Reward Engine Gamification API

🇬🇧 English version available here: [README.md](README.md)

Une API configurable de gamification construite avec le framework Frappe.

Reward Engine permet à des applications externes de récompenser les utilisateurs selon leurs actions. Le moteur peut enregistrer des événements, attribuer des points, calculer l’XP et les niveaux, accorder des récompenses, gérer l’utilisation des récompenses et exposer la progression utilisateur via des endpoints API.

---

## Présentation

Ce projet fournit un système backend de récompenses pour des applications gamifiées.

Une application cliente peut envoyer des événements utilisateur comme :

- connexion d’un utilisateur
- complétion d’une tâche
- fin d’un cours
- achat
- parrainage
- activité quotidienne
- actions métier personnalisées

Le moteur vérifie ensuite les règles de récompense configurées et met à jour le profil utilisateur avec les points, l’XP, les niveaux et les récompenses.

---

## Fonctionnalités

- Moteur de gamification basé sur une API
- Authentification des applications avec clé API et secret API
- Actions de récompense configurables
- Attribution de points et d’XP basée sur des règles
- Création automatique du profil de récompense utilisateur
- Progression de niveau basée sur l’XP
- Protection contre les événements dupliqués avec `event_id`
- Attribution de récompense unique
- Système d’utilisation des récompenses
- Historique des récompenses utilisateur
- DocTypes Frappe configurables depuis l’interface admin
- Support GitHub Actions CI
- Support pre-commit, linting et formatting

---

## Stack technique

- Python 3.10+
- Frappe Framework
- Bench CLI
- MariaDB / couche base de données Frappe
- GitHub Actions
- Ruff
- ESLint
- Prettier
- Pyupgrade
- Licence MIT

---

## Structure du projet

```txt
reward-engine-gamification-api/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── linter.yml
├── reward_engine/
│   ├── api.py
│   ├── hooks.py
│   ├── modules.txt
│   └── reward_engine/
│       └── doctype/
│           ├── action_log/
│           ├── reward/
│           ├── reward_action/
│           ├── reward_application/
│           ├── reward_rule/
│           ├── user_reward_grant/
│           └── user_reward_profile/
├── pyproject.toml
├── README.md
└── license.txt
```

---

## Concepts principaux

### Reward Application

Représente une application externe autorisée à utiliser le moteur de récompenses.

Chaque application peut avoir :

- un nom d’application
- une clé API
- un secret API
- un statut

Seules les applications actives peuvent envoyer des événements à l’API.

---

### Reward Action

Représente une action qu’un utilisateur peut effectuer.

Exemples :

- `login`
- `complete_task`
- `finish_course`
- `purchase`
- `refer_friend`

Chaque action appartient à une application de récompense.

---

### Reward Rule

Définit comment une action doit être récompensée.

Une règle peut définir :

- l’application cible
- l’action concernée
- les points à ajouter
- l’XP à ajouter
- une récompense optionnelle
- un seuil avant attribution de la récompense
- un statut actif ou inactif

---

### User Reward Profile

Stocke la progression de gamification d’un utilisateur.

Il suit :

- l’identifiant externe de l’utilisateur
- le nom de l’utilisateur
- le total des points
- le total d’XP
- le niveau actuel
- le statut

---

### Reward

Représente une récompense pouvant être attribuée à un utilisateur.

Exemples :

- badge
- coupon
- succès
- certificat
- réduction
- fonctionnalité débloquée

---

### User Reward Grant

Représente une récompense attribuée à un utilisateur spécifique.

Il suit :

- le profil utilisateur
- la récompense
- la règle source
- la date d’attribution
- le statut

---

### Action Log

Stocke chaque action utilisateur traitée.

Il suit :

- l’application
- le profil utilisateur
- l’action
- l’ID de l’événement
- la date de l’action
- les points ajoutés
- l’XP ajoutée
- le statut

Le champ `event_id` permet d’éviter le traitement des doublons.

---

## Système de niveaux

Le système de niveaux est basé sur le total d’XP.

| Niveau | XP minimum |
|---|---:|
| 1 | 0 |
| 2 | 50 |
| 3 | 150 |
| 4 | 300 |

Lorsqu’un utilisateur gagne de l’XP, le moteur recalcule automatiquement son niveau.

---

## Installation

Va dans ton dossier Frappe Bench :

```bash
cd $PATH_TO_YOUR_BENCH
```

Installe l’application depuis GitHub :

```bash
bench get-app https://github.com/joanelant/reward-engine-gamification-api --branch main
```

Installe l’application sur ton site :

```bash
bench --site your-site.local install-app reward_engine
```

Lance les migrations :

```bash
bench --site your-site.local migrate
```

Redémarre Bench :

```bash
bench restart
```

---

## URL de base de l’API

Les méthodes whitelisted de Frappe sont exposées avec ce format :

```txt
/api/method/reward_engine.api.<method_name>
```

Exemple :

```txt
/api/method/reward_engine.api.log_action
```

---

## Endpoints API

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/method/reward_engine.api.log_action` | Enregistre une action utilisateur et applique les règles de récompense |
| POST | `/api/method/reward_engine.api.get_points` | Retourne les points, l’XP et le niveau d’un utilisateur |
| POST | `/api/method/reward_engine.api.get_progress` | Retourne les informations de progression de niveau |
| POST | `/api/method/reward_engine.api.get_rewards` | Retourne les récompenses attribuées à un utilisateur |
| POST | `/api/method/reward_engine.api.redeem_reward` | Marque une récompense attribuée comme utilisée |
| POST | `/api/method/reward_engine.api.get_history` | Retourne l’historique des actions utilisateur |

L’API accepte les payloads JSON et les données de formulaire.

---

## Authentification

Chaque requête doit inclure :

```json
{
  "api_key": "APP_TEST_KEY",
  "api_secret": "APP_TEST_SECRET"
}
```

Le moteur valide ces identifiants avec une `Reward Application` active.

---

## Log Action

Enregistre une action utilisateur, applique la règle configurée, met à jour les points et l’XP, recalcule le niveau et attribue une récompense si le seuil défini est atteint.

### Requête

```bash
curl -X POST "https://your-site.com/api/method/reward_engine.api.log_action" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "APP_TEST_KEY",
    "api_secret": "APP_TEST_SECRET",
    "external_user_id": "USER001",
    "event_id": "EVT001",
    "action_code": "login",
    "user_name": "Test User"
  }'
```

### Exemple de réponse

```json
{
  "status": "success",
  "message": "Action processed successfully.",
  "application": "Demo App",
  "external_user_id": "USER001",
  "action_code": "login",
  "points_added": 10,
  "xp_added": 20,
  "total_points": 10,
  "total_xp": 20,
  "level": 1,
  "reward_granted": null
}
```

### Réponse en cas de doublon

Si le même `event_id` est envoyé deux fois, l’API retourne :

```json
{
  "status": "duplicate",
  "error_code": "DUPLICATE_EVENT",
  "message": "This event has already been processed.",
  "event_id": "EVT001"
}
```

---

## Get Points

Retourne les points, l’XP et le niveau actuel d’un utilisateur.

### Requête

```bash
curl -X POST "https://your-site.com/api/method/reward_engine.api.get_points" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "APP_TEST_KEY",
    "api_secret": "APP_TEST_SECRET",
    "external_user_id": "USER001"
  }'
```

### Exemple de réponse

```json
{
  "status": "success",
  "message": "Points fetched successfully.",
  "application": "Demo App",
  "external_user_id": "USER001",
  "user_name": "Test User",
  "total_points": 120,
  "total_xp": 180,
  "level": 3,
  "profile_status": "Active"
}
```

---

## Get Progress

Retourne la progression détaillée de l’utilisateur vers le prochain niveau.

### Requête

```bash
curl -X POST "https://your-site.com/api/method/reward_engine.api.get_progress" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "APP_TEST_KEY",
    "api_secret": "APP_TEST_SECRET",
    "external_user_id": "USER001"
  }'
```

### Exemple de réponse

```json
{
  "status": "success",
  "message": "Progress fetched successfully.",
  "application": "Demo App",
  "external_user_id": "USER001",
  "user_name": "Test User",
  "total_points": 120,
  "total_xp": 180,
  "current_level": 3,
  "next_level": 4,
  "current_level_min_xp": 150,
  "next_level_min_xp": 300,
  "xp_inside_current_level": 30,
  "xp_needed_for_next_level": 120,
  "progress_percentage": 20,
  "is_max_level": false,
  "profile_status": "Active"
}
```

---

## Get Rewards

Retourne toutes les récompenses attribuées à un utilisateur.

### Requête

```bash
curl -X POST "https://your-site.com/api/method/reward_engine.api.get_rewards" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "APP_TEST_KEY",
    "api_secret": "APP_TEST_SECRET",
    "external_user_id": "USER001"
  }'
```

### Exemple de réponse

```json
{
  "status": "success",
  "message": "Rewards fetched successfully.",
  "application": "Demo App",
  "external_user_id": "USER001",
  "user_name": "Test User",
  "total_rewards": 1,
  "rewards": [
    {
      "grant_id": "USER-REWARD-GRANT-00001",
      "reward": "First Login Badge",
      "reward_title": "First Login Badge",
      "source_rule": "RULE-00001",
      "grant_date": "2026-01-01 10:00:00",
      "status": "Granted"
    }
  ]
}
```

---

## Redeem Reward

Marque une récompense attribuée comme utilisée.

### Requête

```bash
curl -X POST "https://your-site.com/api/method/reward_engine.api.redeem_reward" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "APP_TEST_KEY",
    "api_secret": "APP_TEST_SECRET",
    "external_user_id": "USER001",
    "grant_id": "USER-REWARD-GRANT-00001"
  }'
```

### Exemple de réponse

```json
{
  "status": "success",
  "message": "Reward redeemed successfully.",
  "application": "Demo App",
  "external_user_id": "USER001",
  "grant_id": "USER-REWARD-GRANT-00001",
  "reward": "First Login Badge",
  "reward_title": "First Login Badge",
  "reward_status": "Used"
}
```

---

## Get History

Retourne les derniers logs d’actions utilisateur.

### Requête

```bash
curl -X POST "https://your-site.com/api/method/reward_engine.api.get_history" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "APP_TEST_KEY",
    "api_secret": "APP_TEST_SECRET",
    "external_user_id": "USER001",
    "limit": 20
  }'
```

### Exemple de réponse

```json
{
  "status": "success",
  "message": "History fetched successfully.",
  "application": "Demo App",
  "external_user_id": "USER001",
  "user_name": "Test User",
  "limit": 20,
  "total_returned": 1,
  "history": [
    {
      "log_id": "ACTION-LOG-00001",
      "event_id": "EVT001",
      "action": "Reward Action",
      "action_code": "login",
      "action_date": "2026-01-01 10:00:00",
      "points_added": 10,
      "xp_added": 20,
      "status": "Success"
    }
  ]
}
```

---

## Exemple de configuration

1. Créer une `Reward Application`
   - Définir le nom de l’application
   - Définir la clé API
   - Définir le secret API
   - Mettre le statut sur actif

2. Créer une `Reward Action`
   - Exemple de code d’action : `login`

3. Créer une `Reward`
   - Exemple de récompense : `First Login Badge`

4. Créer une `Reward Rule`
   - Sélectionner l’application
   - Sélectionner l’action
   - Définir les points
   - Définir l’XP
   - Sélectionner une récompense si nécessaire
   - Définir le seuil
   - Mettre le statut sur actif

5. Envoyer une requête vers :

```txt
/api/method/reward_engine.api.log_action
```

6. Vérifier le profil utilisateur, les points, l’XP, le niveau et les récompenses.

---

## Format des erreurs

Les erreurs sont retournées avec ce format :

```json
{
  "status": "error",
  "error_code": "ERROR_CODE",
  "message": "Error message"
}
```

Codes d’erreur fréquents :

| Code d’erreur | Signification |
|---|---|
| `MISSING_FIELD` | Un champ obligatoire est manquant |
| `INVALID_APPLICATION` | La clé API ou le secret API est invalide, ou l’application est inactive |
| `INVALID_ACTION` | Le code d’action n’existe pas ou l’action est inactive |
| `DUPLICATE_EVENT` | L’événement a déjà été traité |
| `USER_PROFILE_NOT_FOUND` | Le profil de récompense utilisateur est introuvable |
| `REWARD_GRANT_NOT_FOUND` | La récompense attribuée est introuvable pour cet utilisateur |
| `REWARD_ALREADY_USED` | La récompense a déjà été utilisée |
| `REWARD_EXPIRED` | La récompense a expiré |

---

## Développement

Va dans le dossier de l’application :

```bash
cd apps/reward_engine
```

Installe les hooks pre-commit :

```bash
pre-commit install
```

Lance les tests :

```bash
bench --site your-site.local run-tests --app reward_engine
```

Lance les migrations :

```bash
bench --site your-site.local migrate
```

---

## CI

Ce dépôt inclut des workflows GitHub Actions pour :

- l’intégration continue
- le linting
- les contrôles de qualité et de sécurité du code

Les fichiers de workflow se trouvent dans :

```txt
.github/workflows/
```

---

## Notes de sécurité

Ne jamais exposer ton `api_secret` dans du code frontend public.

Pour une utilisation en production, cette API doit être appelée depuis un backend sécurisé. Le backend doit garder le secret API privé et transmettre uniquement les données nécessaires depuis le frontend.

Vérifie également que les fichiers `.env`, identifiants de base de données, clés privées et tokens personnels ne sont pas envoyés sur GitHub.

---

## Roadmap

Améliorations possibles :

- endpoint de leaderboard
- catégories de badges
- règles d’expiration des récompenses
- suivi des streaks
- graphiques dans le dashboard admin
- rate limiting
- support des webhooks
- tests unitaires pour tous les endpoints API
- documentation OpenAPI / Swagger
- environnement de développement local avec Docker

---

## Dépôt

Dépôt GitHub :

```txt
https://github.com/joanelant/reward-engine-gamification-api
```

---

## Licence

Ce projet est sous licence MIT.
