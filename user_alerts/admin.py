from django import forms
from django.contrib import admin

from . import conf
from .models import Alert, Dismissal


class AlertAdminForm(forms.ModelForm):
    style = forms.ChoiceField(choices=conf.STYLES, required=False)

    class Meta:
        model = Alert
        fields = "__all__"


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    form = AlertAdminForm
    list_display = ("title", "style", "enabled", "is_active", "members_only", "dismissal_type", "order")
    list_editable = ("enabled", "order")
    list_filter = ("enabled", "members_only", "style")
    search_fields = ("title", "message")

    @admin.display(boolean=True, description="Live now")
    def is_active(self, obj):
        return obj.is_active

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Dismissal)
class DismissalAdmin(admin.ModelAdmin):
    list_display = ("user", "alert", "dismissed_at")
    raw_id_fields = ("user",)
