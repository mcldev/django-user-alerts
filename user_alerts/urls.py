from django.urls import path

from .views import DismissView

app_name = "user_alerts"

urlpatterns = [
    path("<int:pk>/dismiss/", DismissView.as_view(), name="dismiss"),
]
