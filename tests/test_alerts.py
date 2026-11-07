from datetime import timedelta

from django.contrib.auth import get_user_model
from django.template import Context, Template
from unittest.mock import patch

from django.test import RequestFactory, TestCase
from django.utils import timezone

from user_alerts import conf
from user_alerts.models import Alert, Dismissal

User = get_user_model()


def make_alert(**kwargs):
    kwargs.setdefault("title", "Maintenance")
    return Alert.objects.create(**kwargs)


class ActiveWindowTests(TestCase):
    def test_active_respects_enabled_and_window(self):
        now = timezone.now()
        live = make_alert(title="live")
        make_alert(title="disabled", enabled=False)
        make_alert(title="future", publish_start=now + timedelta(hours=1))
        make_alert(title="expired", publish_end=now - timedelta(hours=1))
        self.assertEqual(list(Alert.objects.active()), [live])
        self.assertTrue(live.is_active)

    def test_ordering(self):
        b = make_alert(title="b", order=2)
        a = make_alert(title="a", order=1)
        self.assertEqual(list(Alert.objects.all()), [a, b])


class VisibilityTests(TestCase):
    def request_for(self, user=None):
        request = RequestFactory().get("/")
        request.session = self.client.session
        request.user = user or type("Anon", (), {"is_authenticated": False})()
        return request

    def test_members_only_hidden_from_anonymous(self):
        make_alert(title="public")
        make_alert(title="private", members_only=True)
        titles = [a.title for a in Alert.objects.for_request(self.request_for())]
        self.assertEqual(titles, ["public"])

    def test_members_only_shown_to_users(self):
        user = User.objects.create_user("u")
        make_alert(title="private", members_only=True)
        self.assertEqual(Alert.objects.for_request(self.request_for(user)).count(), 1)

    def test_permanent_dismissal_hides_for_that_user_only(self):
        u1, u2 = User.objects.create_user("u1"), User.objects.create_user("u2")
        alert = make_alert(dismissal_type=Alert.DISMISS_PERMANENT)
        Dismissal.objects.create(user=u1, alert=alert)
        self.assertEqual(Alert.objects.for_request(self.request_for(u1)).count(), 0)
        self.assertEqual(Alert.objects.for_request(self.request_for(u2)).count(), 1)


class DismissViewTests(TestCase):
    def url(self, alert):
        return alert.dismiss_url()

    def test_no_dismiss_url_when_not_dismissible(self):
        self.assertIsNone(make_alert(dismissal_type=Alert.DISMISS_NONE).dismiss_url())

    def test_get_not_allowed(self):
        alert = make_alert()
        self.assertEqual(self.client.get(self.url(alert)).status_code, 405)

    def test_non_dismissible_returns_409(self):
        alert = make_alert(dismissal_type=Alert.DISMISS_NONE)
        url = f"/alerts/{alert.pk}/dismiss/"
        self.assertEqual(self.client.post(url).status_code, 409)

    def test_session_dismissal_hides_alert(self):
        alert = make_alert()
        self.assertEqual(self.client.post(self.url(alert)).status_code, 204)
        response = self.client.get("/alerts/")  # no such page; just keep session
        request = RequestFactory().get("/")
        request.session = self.client.session
        request.user = type("Anon", (), {"is_authenticated": False})()
        self.assertEqual(Alert.objects.for_request(request).count(), 0)

    def test_permanent_dismissal_recorded_once(self):
        user = User.objects.create_user("u")
        alert = make_alert(dismissal_type=Alert.DISMISS_PERMANENT)
        self.client.force_login(user)
        self.client.post(self.url(alert))
        self.client.post(self.url(alert))
        self.assertEqual(Dismissal.objects.filter(user=user, alert=alert).count(), 1)

    def test_permanent_falls_back_to_session_for_anonymous(self):
        alert = make_alert(dismissal_type=Alert.DISMISS_PERMANENT)
        self.assertEqual(self.client.post(self.url(alert)).status_code, 204)
        self.assertEqual(Dismissal.objects.count(), 0)
        self.assertIn(alert.pk, self.client.session["user_alerts_dismissed"])

    def test_inactive_alert_404(self):
        alert = make_alert(enabled=False)
        self.assertEqual(self.client.post(self.url(alert)).status_code, 404)


class TemplateTagTests(TestCase):
    def render(self, source, user=None):
        request = RequestFactory().get("/")
        request.session = self.client.session
        request.user = user or type("Anon", (), {"is_authenticated": False})()
        return Template("{% load user_alerts_tags %}" + source).render(Context({"request": request}))

    def test_render_tag_outputs_bootstrap_alert(self):
        make_alert(title="Down", message="Back soon", style="danger", icon="fas fa-bullhorn")
        html = self.render("{% render_user_alerts %}")
        self.assertIn("alert alert-danger alert-dismissible", html)
        self.assertIn("Down", html)
        self.assertIn("fas fa-bullhorn", html)
        self.assertIn("dismiss.js", html)

    def test_non_dismissible_has_no_close_button(self):
        make_alert(dismissal_type=Alert.DISMISS_NONE)
        html = self.render("{% render_user_alerts %}")
        self.assertNotIn("btn-close", html)

    def test_nothing_rendered_without_alerts(self):
        self.assertEqual(self.render("{% render_user_alerts %}").strip(), "")

    def test_message_escaped_by_default(self):
        make_alert(message="<script>x</script>")
        self.assertNotIn("<script>x", self.render("{% render_user_alerts %}"))

    def test_allow_html_setting(self):
        make_alert(message="<b>bold</b>")
        with patch.object(conf, "ALLOW_HTML", True):
            self.assertIn("<b>bold</b>", self.render("{% render_user_alerts %}"))

    def test_user_alerts_tag_as_variable(self):
        make_alert(title="one")
        out = self.render("{% user_alerts as a %}{{ a|length }}")
        self.assertEqual(out, "1")
