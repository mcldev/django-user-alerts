from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from . import conf
from .models import Alert, Dismissal


class DismissView(View):
    """POST-only: record that the current visitor has dismissed an alert."""

    http_method_names = ["post"]

    def post(self, request, pk):
        alert = get_object_or_404(Alert.objects.active(), pk=pk)
        if not alert.dismissible:
            return HttpResponse(status=409)
        user = request.user
        if alert.dismissal_type == Alert.DISMISS_PERMANENT and user.is_authenticated:
            Dismissal.objects.get_or_create(user=user, alert=alert)
        else:
            # Session dismissal; also the fallback for anonymous visitors.
            dismissed = set(request.session.get(conf.SESSION_KEY, []))
            dismissed.add(alert.pk)
            request.session[conf.SESSION_KEY] = sorted(dismissed)
        return HttpResponse(status=204)
