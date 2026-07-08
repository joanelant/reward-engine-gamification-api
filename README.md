# Reward Engine Gamification API

A configurable gamification reward engine built with the Frappe Framework.

Reward Engine allows external applications to reward users based on their actions. It can track events, assign points, calculate XP and levels, grant rewards, manage reward redemption, and expose user progress through API endpoints.

---

## Overview

This project provides a backend reward system for gamified applications.

A client application can send user events such as:

- user login
- task completion
- course completion
- purchase
- referral
- daily activity
- custom business actions

The engine checks the configured reward rules and updates the user profile with points, XP, levels, and rewards.

---

## Features

- API-based gamification engine
- Application authentication using API key and API secret
- Configurable reward actions
- Rule-based points and XP attribution
- Automatic user reward profile creation
- XP-based level progression
- Duplicate event protection using `event_id`
- One-time reward granting
- Reward redemption system
- User reward history
- Admin-configurable Frappe DocTypes
- GitHub Actions CI support
- Pre-commit, linting, and formatting support

---

## Tech Stack

- Python 3.10+
- Frappe Framework
- Bench CLI
- MariaDB / Frappe database layer
- GitHub Actions
- Ruff
- ESLint
- Prettier
- Pyupgrade
- MIT License

---

## Project Structure

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

## Core Concepts

### Reward Application

Represents an external application allowed to use the reward engine.

Each application can have:

- application name
- API key
- API secret
- status

Only active applications can send events to the API.

---

### Reward Action

Represents an action that users can perform.

Examples:

- `login`
- `complete_task`
- `finish_course`
- `purchase`
- `refer_friend`

Each action belongs to a reward application.

---

### Reward Rule

Defines how an action should be rewarded.

A rule can define:

- the target application
- the action
- points to add
- XP to add
- optional reward
- threshold before granting the reward
- active or inactive status

---

### User Reward Profile

Stores the gamification progress of a user.

It tracks:

- external user ID
- user name
- total points
- total XP
- current level
- status

---

### Reward

Represents a reward that can be granted to a user.

Examples:

- badge
- coupon
- achievement
- certificate
- discount
- unlockable feature

---

### User Reward Grant

Represents a reward granted to a specific user.

It tracks:

- user profile
- reward
- source rule
- grant date
- status

---

### Action Log

Stores every processed user action.

It tracks:

- application
- user profile
- action
- event ID
- action date
- points added
- XP added
- status

The `event_id` helps prevent duplicate processing.

---

## Level System

The level system is based on total XP.

| Level | Minimum XP |
|---|---:|
| 1 | 0 |
| 2 | 50 |
| 3 | 150 |
| 4 | 300 |

When a user gains XP, the engine recalculates their level automatically.

---

## Installation

Go to your Frappe bench directory:

```bash
cd $PATH_TO_YOUR_BENCH
```

Install the app from GitHub:

```bash
bench get-app https://github.com/joanelant/reward-engine-gamification-api --branch main
```

Install the app on your site:

```bash
bench --site your-site.local install-app reward_engine
```

Run migrations:

```bash
bench --site your-site.local migrate
```

Restart bench:

```bash
bench restart
```

---

## API Base URL

Frappe whitelisted methods are exposed using this format:

```txt
/api/method/reward_engine.api.<method_name>
```

Example:

```txt
/api/method/reward_engine.api.log_action
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/method/reward_engine.api.log_action` | Logs a user action and applies reward rules |
| POST | `/api/method/reward_engine.api.get_points` | Returns user points, XP and level |
| POST | `/api/method/reward_engine.api.get_progress` | Returns level progress information |
| POST | `/api/method/reward_engine.api.get_rewards` | Returns rewards granted to a user |
| POST | `/api/method/reward_engine.api.redeem_reward` | Marks a granted reward as used |
| POST | `/api/method/reward_engine.api.get_history` | Returns user action history |

The API accepts JSON payloads and form data.

---

## Authentication

Each request must include:

```json
{
  "api_key": "APP_TEST_KEY",
  "api_secret": "APP_TEST_SECRET"
}
```

The engine validates these credentials against an active `Reward Application`.

---

## Log Action

Logs a user action, applies the configured rule, updates points and XP, recalculates the level, and grants a reward if the rule threshold is reached.

### Request

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

### Example Response

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

### Duplicate Event Response

If the same `event_id` is sent twice, the API returns:

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

Returns the current points, XP and level of a user.

### Request

```bash
curl -X POST "https://your-site.com/api/method/reward_engine.api.get_points" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "APP_TEST_KEY",
    "api_secret": "APP_TEST_SECRET",
    "external_user_id": "USER001"
  }'
```

### Example Response

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

Returns detailed XP progress toward the next level.

### Request

```bash
curl -X POST "https://your-site.com/api/method/reward_engine.api.get_progress" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "APP_TEST_KEY",
    "api_secret": "APP_TEST_SECRET",
    "external_user_id": "USER001"
  }'
```

### Example Response

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

Returns all rewards granted to a user.

### Request

```bash
curl -X POST "https://your-site.com/api/method/reward_engine.api.get_rewards" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "APP_TEST_KEY",
    "api_secret": "APP_TEST_SECRET",
    "external_user_id": "USER001"
  }'
```

### Example Response

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

Marks a granted reward as used.

### Request

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

### Example Response

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

Returns the latest user action logs.

### Request

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

### Example Response

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

## Example Setup Flow

1. Create a `Reward Application`
   - Set application name
   - Set API key
   - Set API secret
   - Set status to active

2. Create a `Reward Action`
   - Example action code: `login`

3. Create a `Reward`
   - Example reward: `First Login Badge`

4. Create a `Reward Rule`
   - Select the application
   - Select the action
   - Set points
   - Set XP
   - Optionally select a reward
   - Set threshold
   - Set status to active

5. Send a request to:

```txt
/api/method/reward_engine.api.log_action
```

6. Check the user profile, points, XP, level and rewards.

---

## Error Format

Errors are returned using this format:

```json
{
  "status": "error",
  "error_code": "ERROR_CODE",
  "message": "Error message"
}
```

Common error codes:

| Error Code | Meaning |
|---|---|
| `MISSING_FIELD` | A required field is missing |
| `INVALID_APPLICATION` | API key or API secret is invalid, or the application is inactive |
| `INVALID_ACTION` | The action code does not exist or is inactive |
| `DUPLICATE_EVENT` | The event has already been processed |
| `USER_PROFILE_NOT_FOUND` | User reward profile was not found |
| `REWARD_GRANT_NOT_FOUND` | Reward grant was not found for the user |
| `REWARD_ALREADY_USED` | Reward has already been redeemed |
| `REWARD_EXPIRED` | Reward has expired |

---

## Development

Go to the app directory:

```bash
cd apps/reward_engine
```

Install pre-commit hooks:

```bash
pre-commit install
```

Run tests:

```bash
bench --site your-site.local run-tests --app reward_engine
```

Run migrations:

```bash
bench --site your-site.local migrate
```

---

## CI

This repository includes GitHub Actions workflows for:

- continuous integration
- linting
- security and code quality checks

Workflow files are located in:

```txt
.github/workflows/
```

---

## Security Notes

Do not expose your `api_secret` in public frontend code.

For production usage, call this API from a secure backend service. The backend should keep the API secret private and forward only safe data from the frontend.

Also make sure that `.env`, database credentials, private keys, and personal tokens are not committed to GitHub.

---

## Roadmap

Possible future improvements:

- leaderboard endpoint
- badge categories
- reward expiration rules
- streak tracking
- admin dashboard charts
- rate limiting
- webhook support
- unit tests for all API endpoints
- OpenAPI / Swagger documentation
- Docker-based local development setup

---

## Repository

GitHub repository:

```txt
https://github.com/joanelant/reward-engine-gamification-api
```

---

## License

This project is licensed under the MIT License.
