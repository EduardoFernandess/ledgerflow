from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from ledgerflow.apps.accounts.views import (
    EmailTokenObtainPairView,
    MeView,
    MemberDetailView,
    MemberListCreateView,
    OrganizationDetailView,
    OrganizationListCreateView,
    RegisterView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/token/", EmailTokenObtainPairView.as_view(), name="auth-token"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("organizations/", OrganizationListCreateView.as_view(), name="org-list"),
    path("organizations/<uuid:pk>/", OrganizationDetailView.as_view(), name="org-detail"),
    path(
        "organizations/<uuid:pk>/members/",
        MemberListCreateView.as_view(),
        name="org-members",
    ),
    path(
        "organizations/<uuid:pk>/members/<uuid:user_id>/",
        MemberDetailView.as_view(),
        name="org-member-detail",
    ),
]
