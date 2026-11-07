from django.conf import settings

DEFAULT_STYLES = [
    ("info", "Info"),
    ("success", "Success"),
    ("warning", "Warning"),
    ("danger", "Danger"),
    ("primary", "Primary"),
    ("secondary", "Secondary"),
]

# Bootstrap contextual alert styles offered in the admin. Override with e.g.
# USER_ALERTS_STYLES = [("info", "Info"), ("danger", "Outage")]
STYLES = getattr(settings, "USER_ALERTS_STYLES", DEFAULT_STYLES)

# Alert text is escaped by default. Set True to render the admin-entered
# message as trusted HTML.
ALLOW_HTML = getattr(settings, "USER_ALERTS_ALLOW_HTML", False)

SESSION_KEY = "user_alerts_dismissed"
