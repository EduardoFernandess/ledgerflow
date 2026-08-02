from django.urls import path

from ledgerflow.apps.core.views import HealthView, ReadyView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("ready/", ReadyView.as_view(), name="ready"),
]
