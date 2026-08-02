from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from ledgerflow.apps.audit.services import log_event
from ledgerflow.apps.budgets.services import assert_budget_allows
from ledgerflow.apps.core.exceptions import ServiceError
from ledgerflow.apps.expenses.models import Category, Expense, ExpenseAttachment


@transaction.atomic
def create_expense(*, organization, submitter, category: Category, **fields) -> Expense:
    if category.organization_id != organization.id:
        raise ServiceError("Category does not belong to this organization.", code="invalid_category")
    return Expense.objects.create(
        organization=organization,
        submitter=submitter,
        category=category,
        **fields,
    )


@transaction.atomic
def update_draft_expense(*, expense: Expense, actor, **fields) -> Expense:
    if expense.status != Expense.Status.DRAFT:
        raise ServiceError("Only draft expenses can be updated.", code="invalid_status")
    if expense.submitter_id != actor.id:
        raise ServiceError("Only the submitter can update this expense.", code="forbidden", status_code=403)
    for key, value in fields.items():
        setattr(expense, key, value)
    expense.save()
    return expense


@transaction.atomic
def submit_expense(*, expense: Expense, actor) -> Expense:
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.submitter_id != actor.id:
        raise ServiceError("Only the submitter can submit this expense.", code="forbidden", status_code=403)
    if expense.status != Expense.Status.DRAFT:
        raise ServiceError("Only draft expenses can be submitted.", code="invalid_status")
    assert_budget_allows(expense)
    expense.status = Expense.Status.SUBMITTED
    expense.submitted_at = timezone.now()
    expense.save(update_fields=["status", "submitted_at", "updated_at"])
    log_event(
        organization=expense.organization,
        actor=actor,
        event_type="expense.submitted",
        payload={"expense_id": str(expense.id), "amount": str(expense.amount)},
    )
    return expense


@transaction.atomic
def cancel_expense(*, expense: Expense, actor) -> Expense:
    expense = Expense.objects.select_for_update().get(pk=expense.pk)
    if expense.submitter_id != actor.id:
        raise ServiceError("Only the submitter can cancel this expense.", code="forbidden", status_code=403)
    if expense.status != Expense.Status.SUBMITTED:
        raise ServiceError("Only submitted expenses can be cancelled.", code="invalid_status")
    expense.status = Expense.Status.CANCELLED
    expense.save(update_fields=["status", "updated_at"])
    log_event(
        organization=expense.organization,
        actor=actor,
        event_type="expense.cancelled",
        payload={"expense_id": str(expense.id)},
    )
    return expense


@transaction.atomic
def add_attachment(*, expense: Expense, uploaded_file) -> ExpenseAttachment:
    if expense.status not in (Expense.Status.DRAFT, Expense.Status.SUBMITTED):
        raise ServiceError("Attachments cannot be added in the current status.", code="invalid_status")
    return ExpenseAttachment.objects.create(
        expense=expense,
        file=uploaded_file,
        file_name=uploaded_file.name,
        content_type=getattr(uploaded_file, "content_type", "application/octet-stream"),
        size_bytes=uploaded_file.size,
    )
