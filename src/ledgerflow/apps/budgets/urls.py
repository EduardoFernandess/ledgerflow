from django.urls import path

from ledgerflow.apps.budgets.views import BudgetListCreateView

urlpatterns = [
    path("budgets/", BudgetListCreateView.as_view(), name="budget-list"),
]
