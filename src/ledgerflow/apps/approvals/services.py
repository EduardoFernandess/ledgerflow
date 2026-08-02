from __future__ import annotations

from django.db import transaction

from ledgerflow.apps.accounts.models import Membership
from ledgerflow.apps.approvals.models import ApprovalAction, ApprovalPolicy
from ledgerflow.apps.audit.services import log_event
from ledgerflow.apps.core.exceptions import ServiceError
from ledgerflow.apps.core.permissions import ROLE_RANK
from ledgerflow.apps.expenses.models import Expense


def _required_role_for(expense: Expense) -> str:
    policies = ApprovalPolicy.objects.filter(
        organization=expense.organization, is_active=True
    )
    matched = None
    for policy in policies:
        if expense.amount < policy.min_amount:
            continue
        if policy.max_amount is not None and expense.amount > policy.max_amount:
            continue
        matched = policy
        break
    return matched.required_role if matched else Membership.Role.MANAGER


@transaction.atomic
def approve_expense(*, expense: Expense, actor, membership: Membership, comment: str = "") -> Expense:
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.status != Expense.Status.SUBMITTED:
        raise ServiceError("Only submitted expenses can be approved.", code="invalid_status")
    required = _required_role_for(expense)
    if ROLE_RANK[membership.role] < ROLE_RANK[required]:
        raise ServiceError("Insufficient role to approve.", code="forbidden", status_code=403)
    expense.status = Expense.Status.APPROVED
    expense.save(update_fields=["status", "updated_at"])
    ApprovalAction.objects.create(
        expense=expense, actor=actor, action=ApprovalAction.Action.APPROVE, comment=comment
    )
    log_event(
        organization=expense.organization,
        actor=actor,
        event_type="expense.approved",
        payload={"expense_id": str(expense.id)},
    )
    return expense


@transaction.atomic
def reject_expense(*, expense: Expense, actor, membership: Membership, comment: str = "") -> Expense:
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.status != Expense.Status.SUBMITTED:
        raise ServiceError("Only submitted expenses can be rejected.", code="invalid_status")
    required = _required_role_for(expense)
    if ROLE_RANK[membership.role] < ROLE_RANK[required]:
        raise ServiceError("Insufficient role to reject.", code="forbidden", status_code=403)
    expense.status = Expense.Status.REJECTED
    expense.save(update_fields=["status", "updated_at"])
    ApprovalAction.objects.create(
        expense=expense, actor=actor, action=ApprovalAction.Action.REJECT, comment=comment
    )
    log_event(
        organization=expense.organization,
        actor=actor,
        event_type="expense.rejected",
        payload={"expense_id": str(expense.id), "comment": comment},
    )
    return expense
