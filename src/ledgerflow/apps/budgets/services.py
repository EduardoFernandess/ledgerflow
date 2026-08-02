from __future__ import annotations

from decimal import Decimal

from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone

from ledgerflow.apps.budgets.models import Budget
from ledgerflow.apps.core.exceptions import ServiceError
from ledgerflow.apps.expenses.models import Expense


ACTIVE_STATUSES = (Expense.Status.SUBMITTED, Expense.Status.APPROVED)


def _budgets_for_expense(expense: Expense):
    return Budget.objects.select_for_update().filter(
        organization=expense.organization,
        currency=expense.currency,
        period_start__lte=expense.incurred_on,
        period_end__gte=expense.incurred_on,
    ).filter(models.Q(category=expense.category) | models.Q(category__isnull=True))


def usage_for_budget(budget: Budget) -> Decimal:
    qs = Expense.objects.filter(
        organization=budget.organization,
        currency=budget.currency,
        status__in=ACTIVE_STATUSES,
        incurred_on__gte=budget.period_start,
        incurred_on__lte=budget.period_end,
    )
    if budget.category_id:
        qs = qs.filter(category_id=budget.category_id)
    total = qs.aggregate(total=Sum("amount"))["total"]
    return total or Decimal("0.00")


@transaction.atomic
def assert_budget_allows(expense: Expense) -> None:
    budgets = list(_budgets_for_expense(expense))
    for budget in budgets:
        used = usage_for_budget(budget)
        if used + expense.amount > budget.limit_amount:
            raise ServiceError(
                f"Expense exceeds budget limit of {budget.limit_amount} {budget.currency}.",
                code="budget_exceeded",
            )


@transaction.atomic
def create_budget(**kwargs) -> Budget:
    if kwargs["period_end"] < kwargs["period_start"]:
        raise ServiceError("period_end must be on or after period_start.", code="invalid_period")
    return Budget.objects.create(**kwargs)
