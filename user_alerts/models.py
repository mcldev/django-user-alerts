from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import conf


class AlertQuerySet(models.QuerySet):
    def active(self, now=None):
        """Enabled alerts whose publish window includes ``now``."""
        now = now or timezone.now()
        return self.filter(enabled=True, publish_start__lte=now).filter(
            Q(publish_end__isnull=True) | Q(publish_end__gt=now)
        )

    def for_request(self, request):
        """Active alerts this request's user should currently see."""
        qs = self.active()
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            qs = qs.exclude(dismissals__user=user)
        else:
            qs = qs.filter(members_only=False)
        session = getattr(request, "session", None)
        dismissed = session.get(conf.SESSION_KEY, []) if session is not None else []
        return qs.exclude(pk__in=dismissed)


class Alert(models.Model):
    DISMISS_NONE = 1
    DISMISS_SESSION = 2
    DISMISS_PERMANENT = 3
    DISMISSAL_CHOICES = [
        (DISMISS_NONE, _("Cannot be dismissed")),
        (DISMISS_SESSION, _("Dismissed until the session ends")),
        (DISMISS_PERMANENT, _("Dismissed permanently (signed-in users)")),
    ]

    title = models.CharField(_("title"), max_length=100)
    message = models.TextField(_("message"), blank=True)
    style = models.CharField(_("style"), max_length=20, default="info", blank=True)
    icon = models.CharField(
        _("icon"), max_length=100, blank=True,
        help_text=_("Optional icon CSS classes, e.g. 'bi bi-exclamation-triangle' or 'fas fa-bullhorn'."),
    )
    enabled = models.BooleanField(_("enabled"), default=True)
    members_only = models.BooleanField(_("signed-in users only"), default=False)
    dismissal_type = models.IntegerField(_("dismissal"), choices=DISMISSAL_CHOICES, default=DISMISS_SESSION)
    publish_start = models.DateTimeField(_("publish start"), default=timezone.now)
    publish_end = models.DateTimeField(_("publish end"), blank=True, null=True)
    order = models.PositiveIntegerField(_("order"), default=0, help_text=_("Lower numbers show first."))
    created = models.DateTimeField(_("created"), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_("created by"),
        null=True, blank=True, editable=False, on_delete=models.SET_NULL, related_name="+",
    )

    objects = AlertQuerySet.as_manager()

    class Meta:
        verbose_name = _("alert")
        verbose_name_plural = _("alerts")
        ordering = ["order", "-created"]

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        now = timezone.now()
        return self.enabled and self.publish_start <= now and (self.publish_end is None or self.publish_end > now)

    @property
    def dismissible(self):
        return self.dismissal_type != self.DISMISS_NONE

    def dismiss_url(self):
        if self.dismissible:
            return reverse("user_alerts:dismiss", args=[self.pk])


class Dismissal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alert_dismissals")
    alert = models.ForeignKey(Alert, on_delete=models.CASCADE, related_name="dismissals")
    dismissed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "alert"], name="user_alerts_unique_dismissal")]
