# django-user-alerts

Simple, admin-managed alerts for a Django site. Administrators post an alert (new service, outage, maintenance...) and
visitors see it as a Bootstrap 5 alert, either permanent or dismissible. No CMS, no jQuery, no other dependencies.

Requires Python 3.12+ and Django 4.2+.

## Install

```bash
pip install django-user-alerts
```

```python
# settings.py
INSTALLED_APPS = [..., "django.contrib.sessions", "user_alerts"]

# urls.py  (only needed for the dismiss endpoint)
path("alerts/", include("user_alerts.urls")),
```

```bash
python manage.py migrate
```

Add the request context processor (`django.template.context_processors.request`) if you don't already have it, then in
your base template:

```django
{% load user_alerts_tags %}
{% render_user_alerts %}
```

Manage alerts under **User alerts** in the Django admin.

## Alert fields

| Field | Purpose |
|---|---|
| title / message | Bold title followed by the message |
| style | Bootstrap contextual class: info, success, warning, danger, ... |
| icon | Optional icon CSS classes (e.g. `bi bi-megaphone`, `fas fa-bullhorn`) |
| enabled, publish start/end | Show only inside the window |
| members only | Hide from anonymous visitors |
| dismissal | Cannot be dismissed, dismissed for the session, or dismissed permanently (signed-in users; anonymous visitors fall back to session) |
| order | Lower shows first |

## Customising

Override templates by creating the same path in your project's `templates/` directory:

- `user_alerts/alerts.html` - the wrapper and dismiss script
- `user_alerts/alert.html` - one alert (context: `alert`, `allow_html`, `csrf_token`)

For full control use the data tag and write your own markup:

```django
{% user_alerts as alerts %}
{% for alert in alerts %}...{% endfor %}
```

The built-in markup uses Bootstrap 5's `btn-close`; the small `user_alerts/dismiss.js` tells the server when one is
closed, so make sure Bootstrap's JS is loaded for the close animation.

## Settings

- `USER_ALERTS_STYLES` - list of `(value, label)` styles offered in the admin.
- `USER_ALERTS_ALLOW_HTML` - default `False` (messages are escaped, newlines kept). Set `True` to render the message as trusted HTML.

## Development

```bash
uv venv --python 3.12 && uv pip install django
DJANGO_SETTINGS_MODULE=tests.settings python -m django test tests
```

## Credit

Derived from the idea of [pinax-announcements](https://github.com/pinax/pinax-announcements) (MIT), rewritten as a
standalone app.
