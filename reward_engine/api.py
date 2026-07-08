import frappe
from frappe.utils import now_datetime
import unicodedata


# ---------------------------------------------------------
# LEVEL CONFIG
# ---------------------------------------------------------

LEVEL_THRESHOLDS = [
    {"level": 1, "min_xp": 0},
    {"level": 2, "min_xp": 50},
    {"level": 3, "min_xp": 150},
    {"level": 4, "min_xp": 300},
]


# ---------------------------------------------------------
# MAIN API: LOG ACTION
# ---------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def log_action():
    """
    API used by a client application to send a user action.

    Expected JSON:
    {
        "api_key": "APP_TEST_KEY",
        "api_secret": "APP_TEST_SECRET",
        "external_user_id": "USER001",
        "event_id": "EVT001",
        "action_code": "login",
        "user_name": "Test User"
    }
    """

    data = get_request_data()

    api_key = data.get("api_key")
    api_secret = data.get("api_secret")
    external_user_id = data.get("external_user_id")
    event_id = data.get("event_id")
    action_code = data.get("action_code")
    user_name = data.get("user_name")

    required_fields = {
        "api_key": api_key,
        "api_secret": api_secret,
        "external_user_id": external_user_id,
        "event_id": event_id,
        "action_code": action_code
    }

    for field, value in required_fields.items():
        if not value:
            return error_response(
                "MISSING_FIELD",
                f"The field {field} is required."
            )

    application_doc = find_application(api_key, api_secret)

    if not application_doc:
        return error_response(
            "INVALID_APPLICATION",
            "Invalid API Key, invalid API Secret, or inactive application."
        )

    existing_event = frappe.db.exists(
        "Action Log",
        {
            "application": application_doc.name,
            "event_id": event_id
        }
    )

    if existing_event:
        return {
            "status": "duplicate",
            "error_code": "DUPLICATE_EVENT",
            "message": "This event has already been processed.",
            "event_id": event_id
        }

    action_doc = find_action(application_doc.name, action_code)

    if not action_doc:
        return error_response(
            "INVALID_ACTION",
            "Action code does not exist or is inactive."
        )

    user_profile_doc = get_or_create_user_profile(
        application=application_doc.name,
        external_user_id=external_user_id,
        user_name=user_name
    )

    rule_doc = find_reward_rule(
        application=application_doc.name,
        action=action_doc.name
    )

    success_status = get_select_value(
        "Action Log",
        "status",
        ["Success", "Succès"],
        "Succès"
    )

    if not rule_doc:
        create_action_log(
            application=application_doc.name,
            user_profile=user_profile_doc.name,
            action=action_doc.name,
            event_id=event_id,
            points_added=0,
            xp_added=0,
            status=success_status
        )

        frappe.db.commit()

        return {
            "status": "success",
            "message": "Action saved, but no active reward rule found.",
            "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
            "external_user_id": external_user_id,
            "action_code": action_code,
            "points_added": 0,
            "xp_added": 0,
            "total_points": user_profile_doc.total_points or 0,
            "total_xp": user_profile_doc.total_xp or 0,
            "level": user_profile_doc.level or 1,
            "reward_granted": None
        }

    points_added = get_doc_value(rule_doc, ["points"], 0) or 0
    xp_added = get_doc_value(rule_doc, ["xp"], 0) or 0

    user_profile_doc.total_points = (user_profile_doc.total_points or 0) + points_added
    user_profile_doc.total_xp = (user_profile_doc.total_xp or 0) + xp_added
    user_profile_doc.level = calculate_level(user_profile_doc.total_xp)
    user_profile_doc.save(ignore_permissions=True)

    create_action_log(
        application=application_doc.name,
        user_profile=user_profile_doc.name,
        action=action_doc.name,
        event_id=event_id,
        points_added=points_added,
        xp_added=xp_added,
        status=success_status
    )

    reward_granted = None

    reward_name = get_doc_value(rule_doc, ["reward", "recompense"], None)
    threshold = get_doc_value(rule_doc, ["threshold", "seuil"], 1) or 1

    if reward_name:
        action_count = frappe.db.count(
            "Action Log",
            {
                "application": application_doc.name,
                "user_profile": user_profile_doc.name,
                "action": action_doc.name,
                "status": success_status
            }
        )

        if action_count >= threshold:
            reward_granted = grant_reward_once(
                user_profile=user_profile_doc.name,
                reward=reward_name,
                source_rule=rule_doc.name
            )

    frappe.db.commit()

    return {
        "status": "success",
        "message": "Action processed successfully.",
        "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
        "external_user_id": external_user_id,
        "action_code": action_code,
        "points_added": points_added,
        "xp_added": xp_added,
        "total_points": user_profile_doc.total_points,
        "total_xp": user_profile_doc.total_xp,
        "level": user_profile_doc.level,
        "reward_granted": reward_granted
    }


# ---------------------------------------------------------
# API: GET POINTS
# ---------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_points():
    """
    API used by a client application to get user points.

    Expected JSON:
    {
        "api_key": "APP_TEST_KEY",
        "api_secret": "APP_TEST_SECRET",
        "external_user_id": "USER001"
    }
    """

    data = get_request_data()

    api_key = data.get("api_key")
    api_secret = data.get("api_secret")
    external_user_id = data.get("external_user_id")

    required_fields = {
        "api_key": api_key,
        "api_secret": api_secret,
        "external_user_id": external_user_id
    }

    for field, value in required_fields.items():
        if not value:
            return error_response(
                "MISSING_FIELD",
                f"The field {field} is required."
            )

    application_doc = find_application(api_key, api_secret)

    if not application_doc:
        return error_response(
            "INVALID_APPLICATION",
            "Invalid API Key, invalid API Secret, or inactive application."
        )

    user_profile_doc = find_user_profile(
        application=application_doc.name,
        external_user_id=external_user_id
    )

    if not user_profile_doc:
        return {
            "status": "success",
            "message": "User has no reward profile yet.",
            "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
            "external_user_id": external_user_id,
            "total_points": 0,
            "total_xp": 0,
            "level": 1,
            "profile_status": "New"
        }

    return {
        "status": "success",
        "message": "Points fetched successfully.",
        "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
        "external_user_id": external_user_id,
        "user_name": get_doc_value(user_profile_doc, ["user_name", "nom_utilisateur"], external_user_id),
        "total_points": user_profile_doc.total_points or 0,
        "total_xp": user_profile_doc.total_xp or 0,
        "level": user_profile_doc.level or 1,
        "profile_status": get_doc_value(user_profile_doc, ["status", "statut"], None)
    }


# ---------------------------------------------------------
# API: GET PROGRESS
# ---------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_progress():
    """
    API used by a client application to get user level progress.

    Expected JSON:
    {
        "api_key": "APP_TEST_KEY",
        "api_secret": "APP_TEST_SECRET",
        "external_user_id": "USER001"
    }
    """

    data = get_request_data()

    api_key = data.get("api_key")
    api_secret = data.get("api_secret")
    external_user_id = data.get("external_user_id")

    required_fields = {
        "api_key": api_key,
        "api_secret": api_secret,
        "external_user_id": external_user_id
    }

    for field, value in required_fields.items():
        if not value:
            return error_response(
                "MISSING_FIELD",
                f"The field {field} is required."
            )

    application_doc = find_application(api_key, api_secret)

    if not application_doc:
        return error_response(
            "INVALID_APPLICATION",
            "Invalid API Key, invalid API Secret, or inactive application."
        )

    user_profile_doc = find_user_profile(
        application=application_doc.name,
        external_user_id=external_user_id
    )

    if not user_profile_doc:
        progress_data = calculate_progress(0)

        return {
            "status": "success",
            "message": "User has no progress yet.",
            "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
            "external_user_id": external_user_id,
            "total_points": 0,
            "total_xp": 0,
            **progress_data,
            "profile_status": "New"
        }

    total_xp = user_profile_doc.total_xp or 0
    progress_data = calculate_progress(total_xp)

    return {
        "status": "success",
        "message": "Progress fetched successfully.",
        "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
        "external_user_id": external_user_id,
        "user_name": get_doc_value(user_profile_doc, ["user_name", "nom_utilisateur"], external_user_id),
        "total_points": user_profile_doc.total_points or 0,
        "total_xp": total_xp,
        **progress_data,
        "profile_status": get_doc_value(user_profile_doc, ["status", "statut"], None)
    }




# ---------------------------------------------------------
# API: GET REWARDS
# ---------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_rewards():
    """
    API used by a client application to get user rewards.

    Expected JSON:
    {
        "api_key": "APP_TEST_KEY",
        "api_secret": "APP_TEST_SECRET",
        "external_user_id": "USER001"
    }
    """

    data = get_request_data()

    api_key = data.get("api_key")
    api_secret = data.get("api_secret")
    external_user_id = data.get("external_user_id")

    required_fields = {
        "api_key": api_key,
        "api_secret": api_secret,
        "external_user_id": external_user_id
    }

    for field, value in required_fields.items():
        if not value:
            return error_response(
                "MISSING_FIELD",
                f"The field {field} is required."
            )

    application_doc = find_application(api_key, api_secret)

    if not application_doc:
        return error_response(
            "INVALID_APPLICATION",
            "Invalid API Key, invalid API Secret, or inactive application."
        )

    user_profile_doc = find_user_profile(
        application=application_doc.name,
        external_user_id=external_user_id
    )

    if not user_profile_doc:
        return {
            "status": "success",
            "message": "User has no reward profile yet.",
            "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
            "external_user_id": external_user_id,
            "total_rewards": 0,
            "rewards": []
        }

    grants = frappe.get_all(
        "User Reward Grant",
        filters={
            "user_profile": user_profile_doc.name
        },
        fields=[
            "name",
            "reward",
            "source_rule",
            "grant_date",
            "status"
        ],
        order_by="creation desc"
    )

    rewards = []

    for grant in grants:
        reward_title = grant.reward

        if grant.reward:
            try:
                reward_doc = frappe.get_doc("Reward", grant.reward)
                reward_title = get_doc_value(
                    reward_doc,
                    ["reward_name", "nom_recompense", "title", "titre"],
                    reward_doc.name
                )
            except Exception:
                reward_title = grant.reward

        rewards.append({
            "grant_id": grant.name,
            "reward": grant.reward,
            "reward_title": reward_title,
            "source_rule": grant.source_rule,
            "grant_date": grant.grant_date,
            "status": grant.status
        })

    return {
        "status": "success",
        "message": "Rewards fetched successfully.",
        "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
        "external_user_id": external_user_id,
        "user_name": get_doc_value(user_profile_doc, ["user_name", "nom_utilisateur"], external_user_id),
        "total_rewards": len(rewards),
        "rewards": rewards
    }


# ---------------------------------------------------------
# API: REDEEM REWARD
# ---------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def redeem_reward():
    """
    API used by a client application to mark a user reward as used.

    Expected JSON:
    {
        "api_key": "APP_TEST_KEY",
        "api_secret": "APP_TEST_SECRET",
        "external_user_id": "USER001",
        "grant_id": "USER-REWARD-GRANT-00001"
    }
    """

    data = get_request_data()

    api_key = data.get("api_key")
    api_secret = data.get("api_secret")
    external_user_id = data.get("external_user_id")
    grant_id = data.get("grant_id") or data.get("reward_grant_id")

    required_fields = {
        "api_key": api_key,
        "api_secret": api_secret,
        "external_user_id": external_user_id,
        "grant_id": grant_id
    }

    for field, value in required_fields.items():
        if not value:
            return error_response(
                "MISSING_FIELD",
                f"The field {field} is required."
            )

    application_doc = find_application(api_key, api_secret)

    if not application_doc:
        return error_response(
            "INVALID_APPLICATION",
            "Invalid API Key, invalid API Secret, or inactive application."
        )

    user_profile_doc = find_user_profile(
        application=application_doc.name,
        external_user_id=external_user_id
    )

    if not user_profile_doc:
        return error_response(
            "USER_PROFILE_NOT_FOUND",
            "User reward profile not found."
        )

    grant_exists = frappe.db.exists(
        "User Reward Grant",
        {
            "name": grant_id,
            "user_profile": user_profile_doc.name
        }
    )

    if not grant_exists:
        return error_response(
            "REWARD_GRANT_NOT_FOUND",
            "Reward grant not found for this user."
        )

    grant_doc = frappe.get_doc("User Reward Grant", grant_exists)
    current_status = normalize_text(get_doc_value(grant_doc, ["status", "statut"], ""))

    if current_status in ["used", "utilise", "utilisee"]:
        return error_response(
            "REWARD_ALREADY_USED",
            "This reward has already been used."
        )

    if current_status in ["expired", "expire", "expiree"]:
        return error_response(
            "REWARD_EXPIRED",
            "This reward has expired."
        )

    used_status = get_select_value(
        "User Reward Grant",
        "status",
        ["Used", "Utilisée", "Utilisee"],
        "Used"
    )

    grant_doc.status = used_status

    set_first_existing_field(
        grant_doc,
        ["used_date", "used_at", "redeemed_at", "use_date"],
        now_datetime()
    )

    grant_doc.save(ignore_permissions=True)
    frappe.db.commit()

    reward_title = grant_doc.reward

    if grant_doc.reward:
        try:
            reward_doc = frappe.get_doc("Reward", grant_doc.reward)
            reward_title = get_doc_value(
                reward_doc,
                ["reward_name", "nom_recompense", "title", "titre"],
                reward_doc.name
            )
        except Exception:
            reward_title = grant_doc.reward

    return {
        "status": "success",
        "message": "Reward redeemed successfully.",
        "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
        "external_user_id": external_user_id,
        "grant_id": grant_doc.name,
        "reward": grant_doc.reward,
        "reward_title": reward_title,
        "reward_status": grant_doc.status
    }


# ---------------------------------------------------------
# API: GET HISTORY
# ---------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_history():
    """
    API used by a client application to get user action history.

    Expected JSON:
    {
        "api_key": "APP_TEST_KEY",
        "api_secret": "APP_TEST_SECRET",
        "external_user_id": "USER001",
        "limit": 20
    }
    """

    data = get_request_data()

    api_key = data.get("api_key")
    api_secret = data.get("api_secret")
    external_user_id = data.get("external_user_id")
    limit = data.get("limit") or 20

    try:
        limit = int(limit)
    except Exception:
        limit = 20

    if limit <= 0:
        limit = 20

    if limit > 100:
        limit = 100

    required_fields = {
        "api_key": api_key,
        "api_secret": api_secret,
        "external_user_id": external_user_id
    }

    for field, value in required_fields.items():
        if not value:
            return error_response(
                "MISSING_FIELD",
                f"The field {field} is required."
            )

    application_doc = find_application(api_key, api_secret)

    if not application_doc:
        return error_response(
            "INVALID_APPLICATION",
            "Invalid API Key, invalid API Secret, or inactive application."
        )

    user_profile_doc = find_user_profile(
        application=application_doc.name,
        external_user_id=external_user_id
    )

    if not user_profile_doc:
        return {
            "status": "success",
            "message": "User has no reward profile yet.",
            "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
            "external_user_id": external_user_id,
            "limit": limit,
            "total_returned": 0,
            "history": []
        }

    logs = frappe.get_all(
        "Action Log",
        filters={
            "application": application_doc.name,
            "user_profile": user_profile_doc.name
        },
        fields=[
            "name",
            "action",
            "event_id",
            "action_date",
            "points_added",
            "xp_added",
            "status"
        ],
        order_by="action_date desc",
        limit_page_length=limit
    )

    history = []

    for log in logs:
        action_code = log.action

        if log.action:
            try:
                action_doc = frappe.get_doc("Reward Action", log.action)
                action_code = get_doc_value(
                    action_doc,
                    ["action_code", "application_code", "code_action"],
                    action_doc.name
                )
            except Exception:
                action_code = log.action

        history.append({
            "log_id": log.name,
            "event_id": log.event_id,
            "action": log.action,
            "action_code": action_code,
            "action_date": log.action_date,
            "points_added": log.points_added or 0,
            "xp_added": log.xp_added or 0,
            "status": log.status
        })

    return {
        "status": "success",
        "message": "History fetched successfully.",
        "application": get_doc_value(application_doc, ["application_name", "nom_application"], application_doc.name),
        "external_user_id": external_user_id,
        "user_name": get_doc_value(user_profile_doc, ["user_name", "nom_utilisateur"], external_user_id),
        "limit": limit,
        "total_returned": len(history),
        "history": history
    }


# ---------------------------------------------------------
# FINDERS
# ---------------------------------------------------------

def find_application(api_key, api_secret):
    apps = frappe.get_all(
        "Reward Application",
        filters={
            "api_key": api_key
        },
        fields=["name"]
    )

    for app in apps:
        app_doc = frappe.get_doc("Reward Application", app.name)

        if not is_active_doc(app_doc):
            continue

        saved_secret = get_password_value(app_doc, "api_secret")

        if saved_secret == api_secret:
            return app_doc

    return None


def find_action(application, action_code):
    actions = frappe.get_all(
        "Reward Action",
        filters={
            "application": application
        },
        fields=["name"]
    )

    for action in actions:
        action_doc = frappe.get_doc("Reward Action", action.name)

        if not is_active_doc(action_doc):
            continue

        saved_action_code = get_doc_value(
            action_doc,
            ["action_code", "application_code", "code_action"],
            None
        )

        if saved_action_code == action_code:
            return action_doc

    return None


def find_reward_rule(application, action):
    rules = frappe.get_all(
        "Reward Rule",
        filters={
            "application": application,
            "action": action
        },
        fields=["name"],
        order_by="creation asc"
    )

    for rule in rules:
        rule_doc = frappe.get_doc("Reward Rule", rule.name)

        if is_active_doc(rule_doc):
            return rule_doc

    return None


def find_user_profile(application, external_user_id):
    existing_profile = frappe.db.exists(
        "User Reward Profile",
        {
            "application": application,
            "external_user_id": external_user_id
        }
    )

    if existing_profile:
        return frappe.get_doc("User Reward Profile", existing_profile)

    return None


# ---------------------------------------------------------
# USER PROFILE
# ---------------------------------------------------------

def get_or_create_user_profile(application, external_user_id, user_name=None):
    existing_profile = frappe.db.exists(
        "User Reward Profile",
        {
            "application": application,
            "external_user_id": external_user_id
        }
    )

    if existing_profile:
        return frappe.get_doc("User Reward Profile", existing_profile)

    active_status = get_select_value(
        "User Reward Profile",
        "status",
        ["Active", "Actif", "actif"],
        "actif"
    )

    profile_doc = frappe.get_doc({
        "doctype": "User Reward Profile",
        "application": application,
        "external_user_id": external_user_id,
        "user_name": user_name or external_user_id,
        "total_points": 0,
        "total_xp": 0,
        "level": 1,
        "status": active_status
    })

    profile_doc.insert(ignore_permissions=True)

    return profile_doc


# ---------------------------------------------------------
# ACTION LOG
# ---------------------------------------------------------

def create_action_log(application, user_profile, action, event_id, points_added, xp_added, status):
    log_doc = frappe.get_doc({
        "doctype": "Action Log",
        "application": application,
        "user_profile": user_profile,
        "action": action,
        "event_id": event_id,
        "action_date": now_datetime(),
        "points_added": points_added,
        "xp_added": xp_added,
        "status": status
    })

    log_doc.insert(ignore_permissions=True)

    return log_doc.name


# ---------------------------------------------------------
# REWARD GRANT
# ---------------------------------------------------------

def grant_reward_once(user_profile, reward, source_rule):
    existing_grant = frappe.db.exists(
        "User Reward Grant",
        {
            "user_profile": user_profile,
            "reward": reward,
            "source_rule": source_rule
        }
    )

    if existing_grant:
        return None

    reward_doc = frappe.get_doc("Reward", reward)

    grant_status = get_select_value(
        "User Reward Grant",
        "status",
        ["Granted", "Attribuée", "Attribuee"],
        "Granted"
    )

    grant_doc = frappe.get_doc({
        "doctype": "User Reward Grant",
        "user_profile": user_profile,
        "reward": reward,
        "source_rule": source_rule,
        "grant_date": now_datetime(),
        "status": grant_status
    })

    grant_doc.insert(ignore_permissions=True)

    return get_doc_value(reward_doc, ["reward_name", "nom_recompense"], reward_doc.name)


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def get_request_data():
    data = {}

    try:
        json_data = frappe.request.get_json(silent=True)
        if json_data:
            data.update(json_data)
    except Exception:
        pass

    try:
        form_data = frappe.form_dict or {}
        data.update(form_data)
    except Exception:
        pass

    data.pop("cmd", None)

    return data


def normalize_text(value):
    if value is None:
        return ""

    value = str(value).strip().lower()

    value = unicodedata.normalize("NFD", value)
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")

    return value


def is_active_value(value):
    return normalize_text(value) in ["active", "actif"]


def is_active_doc(doc):
    status_value = get_doc_value(
        doc,
        ["status", "statut"],
        None
    )

    return is_active_value(status_value)


def get_doc_value(doc, fieldnames, default=None):
    for fieldname in fieldnames:
        if hasattr(doc, fieldname):
            value = doc.get(fieldname)
            if value not in [None, ""]:
                return value

    return default


def get_password_value(doc, fieldname):
    try:
        return doc.get_password(fieldname)
    except Exception:
        return doc.get(fieldname)


def get_select_value(doctype, fieldname, possible_values, default_value):
    """
    Returns the real option available in the Select field.
    Example:
    possible_values = ["Success", "Succès"]
    If the DocType contains "Succès", it returns "Succès".
    """

    try:
        meta = frappe.get_meta(doctype)
        field = meta.get_field(fieldname)

        if not field or not field.options:
            return default_value

        options = [
            option.strip()
            for option in field.options.split("\n")
            if option.strip()
        ]

        for expected in possible_values:
            for option in options:
                if normalize_text(option) == normalize_text(expected):
                    return option

    except Exception:
        pass

    return default_value


def calculate_level(total_xp):
    total_xp = total_xp or 0

    if total_xp >= 300:
        return 4

    if total_xp >= 150:
        return 3

    if total_xp >= 50:
        return 2

    return 1


def calculate_progress(total_xp):
    total_xp = total_xp or 0
    current_level = calculate_level(total_xp)

    current_level_min_xp = 0
    next_level = None
    next_level_min_xp = None

    for item in LEVEL_THRESHOLDS:
        if item["level"] == current_level:
            current_level_min_xp = item["min_xp"]

    for item in LEVEL_THRESHOLDS:
        if item["level"] > current_level:
            next_level = item["level"]
            next_level_min_xp = item["min_xp"]
            break

    if not next_level:
        return {
            "current_level": current_level,
            "next_level": None,
            "current_level_min_xp": current_level_min_xp,
            "next_level_min_xp": None,
            "xp_inside_current_level": total_xp - current_level_min_xp,
            "xp_needed_for_next_level": 0,
            "progress_percentage": 100,
            "is_max_level": True
        }

    xp_inside_current_level = total_xp - current_level_min_xp
    xp_range = next_level_min_xp - current_level_min_xp
    xp_needed_for_next_level = next_level_min_xp - total_xp

    if xp_range <= 0:
        progress_percentage = 0
    else:
        progress_percentage = int((xp_inside_current_level / xp_range) * 100)

    if progress_percentage < 0:
        progress_percentage = 0

    if progress_percentage > 100:
        progress_percentage = 100

    return {
        "current_level": current_level,
        "next_level": next_level,
        "current_level_min_xp": current_level_min_xp,
        "next_level_min_xp": next_level_min_xp,
        "xp_inside_current_level": xp_inside_current_level,
        "xp_needed_for_next_level": xp_needed_for_next_level,
        "progress_percentage": progress_percentage,
        "is_max_level": False
    }



def set_first_existing_field(doc, fieldnames, value):
    """
    Sets the first field that exists on a DocType.
    Useful because some DocTypes may use used_date, used_at, redeemed_at, etc.
    """

    for fieldname in fieldnames:
        if hasattr(doc, fieldname):
            doc.set(fieldname, value)
            return fieldname

    return None

def error_response(error_code, message):
    return {
        "status": "error",
        "error_code": error_code,
        "message": message
    }