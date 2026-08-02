from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from ledgerflow.apps.accounts.models import Membership
from ledgerflow.apps.expenses.models import Expense
from ledgerflow.apps.expenses.services import cancel_expense, create_expense, submit_expense
from tests.factories import (
    BudgetFactory,
    CategoryFactory,
    MembershipFactory,
    OrganizationFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_health_and_ready():
    client = APIClient()
    assert client.get("/api/v1/health/").status_code == 200
    assert client.get("/api/v1/ready/").status_code == 200


@pytest.mark.django_db
def test_cancel_submitted_expense_releases_capacity():
    employee = UserFactory()
    org = OrganizationFactory()
    MembershipFactory(user=employee, organization=org, role=Membership.Role.EMPLOYEE)
    category = CategoryFactory(organization=org)
    BudgetFactory(
        organization=org,
        limit_amount="50.00",
        currency="USD",
        period_start=date.today() - timedelta(days=1),
        period_end=date.today() + timedelta(days=30),
    )
    expense = create_expense(
        organization=org,
        submitter=employee,
        category=category,
        title="Cab",
        description="",
        amount="50.00",
        currency="USD",
        incurred_on=date.today(),
    )
    submit_expense(expense=expense, actor=employee)
    cancel_expense(expense=expense, actor=employee)
    expense.refresh_from_db()
    assert expense.status == Expense.Status.CANCELLED

    replacement = create_expense(
        organization=org,
        submitter=employee,
        category=category,
        title="Cab 2",
        description="",
        amount="50.00",
        currency="USD",
        incurred_on=date.today(),
    )
    submit_expense(expense=replacement, actor=employee)
    replacement.refresh_from_db()
    assert replacement.status == Expense.Status.SUBMITTED


@pytest.mark.django_db
def test_create_budget_via_api():
    owner = UserFactory()
    org = OrganizationFactory()
    MembershipFactory(user=owner, organization=org, role=Membership.Role.OWNER)
    client = APIClient()
    client.force_authenticate(user=owner)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    response = client.post(
        "/api/v1/budgets/",
        {
            "limit_amount": "500.00",
            "currency": "USD",
            "period_start": str(date.today()),
            "period_end": str(date.today() + timedelta(days=30)),
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["limit_amount"] == "500.00"
