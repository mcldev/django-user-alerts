from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TransactionTestCase

from user_alerts.models import Alert, Dismissal


class ImportPinaxTests(TransactionTestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        self.user = get_user_model().objects.create_user("u")
        with connection.cursor() as c:
            c.execute(
                'CREATE TABLE announcements_announcement (id integer primary key, title text, content text, '
                'creator_id integer, creation_date datetime, enabled bool, members_only bool, dismissal_type integer, '
                'publish_start datetime, publish_end datetime, announcement_style text, icon text, "order" integer)'
            )
            c.execute("CREATE TABLE announcements_dismissal (id integer primary key, user_id integer, "
                      "announcement_id integer, dismissed_at datetime)")
            c.execute(
                "INSERT INTO announcements_announcement VALUES (7,'Old','<p>hi</p>',%s,'2024-01-01 00:00:00',1,0,3,"
                "'2024-01-01 00:00:00',NULL,'warning','fas fa-bullhorn',4)", [self.user.pk])
            c.execute("INSERT INTO announcements_dismissal VALUES (1,%s,7,'2024-02-01 00:00:00')", [self.user.pk])

    def tearDown(self):
        with connection.cursor() as c:
            c.execute("DROP TABLE IF EXISTS announcements_dismissal")
            c.execute("DROP TABLE IF EXISTS announcements_announcement")

    def test_imports_and_is_idempotent(self):
        for _ in range(2):
            call_command("import_pinax_announcements", stdout=StringIO())
        alert = Alert.objects.get()
        self.assertEqual((alert.title, alert.style, alert.order, alert.created_by_id),
                         ("Old", "warning", 4, self.user.pk))
        self.assertEqual(Dismissal.objects.filter(alert=alert, user=self.user).count(), 1)

    def test_no_old_tables(self):
        with connection.cursor() as c:
            c.execute("DROP TABLE IF EXISTS announcements_dismissal")
            c.execute("DROP TABLE IF EXISTS announcements_announcement")
        out = StringIO()
        call_command("import_pinax_announcements", stdout=out)
        self.assertIn("nothing to import", out.getvalue())
