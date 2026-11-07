from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UserAlertsConfig(AppConfig):
    name = "user_alerts"
    verbose_name = _("User alerts")
    default_auto_field = "django.db.models.AutoField"
