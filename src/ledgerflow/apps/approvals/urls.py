from django.urls import path

from ledgerflow.apps.approvals.views import (
    ApprovalPolicyListCreateView,
    ExpenseApproveView,
    ExpenseRejectView,
)

urlpatterns = [
    path("approval-policies/", ApprovalPolicyListCreateView.as_view(), name="approval-policies"),
    path("expenses/<uuid:pk>/approve/", ExpenseApproveView.as_view(), name="expense-approve"),
    path("expenses/<uuid:pk>/reject/", ExpenseRejectView.as_view(), name="expense-reject"),
]
