from django.urls import path

from ledgerflow.apps.expenses.views import (
    CategoryListCreateView,
    ExpenseAttachmentCreateView,
    ExpenseCancelView,
    ExpenseDetailView,
    ExpenseListCreateView,
    ExpenseSubmitView,
)

urlpatterns = [
    path("categories/", CategoryListCreateView.as_view(), name="category-list"),
    path("expenses/", ExpenseListCreateView.as_view(), name="expense-list"),
    path("expenses/<uuid:pk>/", ExpenseDetailView.as_view(), name="expense-detail"),
    path("expenses/<uuid:pk>/submit/", ExpenseSubmitView.as_view(), name="expense-submit"),
    path("expenses/<uuid:pk>/cancel/", ExpenseCancelView.as_view(), name="expense-cancel"),
    path(
        "expenses/<uuid:pk>/attachments/",
        ExpenseAttachmentCreateView.as_view(),
        name="expense-attachments",
    ),
]
