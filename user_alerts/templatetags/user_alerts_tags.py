from django import template

from user_alerts import conf
from user_alerts.models import Alert

register = template.Library()


@register.simple_tag(takes_context=True)
def user_alerts(context):
    """``{% user_alerts as alerts %}`` - alerts the current visitor should see."""
    request = context.get("request")
    if request is None:
        return Alert.objects.none()
    return Alert.objects.for_request(request)


@register.inclusion_tag("user_alerts/alerts.html", takes_context=True)
def render_user_alerts(context):
    """``{% render_user_alerts %}`` - render all current alerts.

    Override ``user_alerts/alerts.html`` (or ``user_alerts/alert.html``) in your
    project's templates to change the markup.
    """
    return {
        "alerts": user_alerts(context),
        "allow_html": conf.ALLOW_HTML,
        "csrf_token": context.get("csrf_token", ""),
    }
