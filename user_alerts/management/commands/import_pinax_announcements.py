from django.core.management.base import BaseCommand
from django.db import connection, transaction

from user_alerts.models import Alert, Dismissal

OLD_ANNOUNCEMENTS = "announcements_announcement"
OLD_DISMISSALS = "announcements_dismissal"


class Command(BaseCommand):
    help = (
        "One-off import of announcements and dismissals from the old pinax-announcements tables "
        f"({OLD_ANNOUNCEMENTS}, {OLD_DISMISSALS}). Safe to re-run: already imported rows are skipped."
    )

    def handle(self, *args, **options):
        tables = connection.introspection.table_names()
        if OLD_ANNOUNCEMENTS not in tables:
            self.stdout.write("No pinax-announcements table found; nothing to import.")
            return

        id_map = {}
        with connection.cursor() as cursor, transaction.atomic():
            cursor.execute(
                f"SELECT id, title, content, creator_id, creation_date, enabled, members_only, dismissal_type, "
                f"publish_start, publish_end, announcement_style, icon, \"order\" FROM {OLD_ANNOUNCEMENTS}"
            )
            for (old_id, title, content, creator_id, created, enabled, members_only, dismissal_type,
                 start, end, style, icon, order) in cursor.fetchall():
                alert, new = Alert.objects.get_or_create(
                    title=title, publish_start=start,
                    defaults=dict(
                        message=content or "", style=style or "info", icon=icon or "", enabled=enabled,
                        members_only=members_only, dismissal_type=dismissal_type, publish_end=end,
                        order=order, created_by_id=creator_id,
                    ),
                )
                if new:
                    Alert.objects.filter(pk=alert.pk).update(created=created)
                id_map[old_id] = alert.pk

            dismissals = 0
            if OLD_DISMISSALS in tables:
                cursor.execute(f"SELECT user_id, announcement_id, dismissed_at FROM {OLD_DISMISSALS}")
                for user_id, old_id, dismissed_at in cursor.fetchall():
                    if old_id in id_map:
                        _, new = Dismissal.objects.get_or_create(
                            user_id=user_id, alert_id=id_map[old_id], defaults={"dismissed_at": dismissed_at}
                        )
                        dismissals += new
        self.stdout.write(self.style.SUCCESS(
            f"Imported {len(id_map)} alert(s) and {dismissals} new dismissal(s). "
            "Review the message text: the old content was HTML."
        ))
