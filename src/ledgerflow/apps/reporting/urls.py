from django.urls import path

from ledgerflow.apps.reporting.views import ExportJobCreateView, ExportJobDetailView

urlpatterns = [
    path("reports/exports/", ExportJobCreateView.as_view(), name="export-create"),
    path("reports/exports/<uuid:pk>/", ExportJobDetailView.as_view(), name="export-detail"),
]
