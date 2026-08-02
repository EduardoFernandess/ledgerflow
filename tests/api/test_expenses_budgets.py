from datetime import date, timedelta

import pytest
from rest_framework.test import APIClient

from ledgerflow.apps.accounts.models import Membership
from ledgerflow.apps.expenses.models import Expense
from tests.factories import (
    BudgetFactory,
    CategoryFactory,
    MembershipFactory,
    OrganizationFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_employee_cannot_approve_and_budget_flow():
    owner = UserFactory()
    employee = UserFactory()
    manager = UserFactory()
    org = OrganizationFactory()
    MembershipFactory(user=owner, organization=org, role=Membership.Role.OWNER)
    MembershipFactory(user=employee, organization=org, role=Membership.Role.EMPLOYEE)
    MembershipFactory(user=manager, organization=org, role=Membership.Role.MANAGER)
    category = CategoryFactory(organization=org, name="Meals")
    BudgetFactory(
        organization=org,
        category=None,
        limit_amount="100.00",
        currency="USD",
        period_start=date.today() - timedelta(days=1),
        period_end=date.today() + timedelta(days=30),
    )

    client = APIClient()
    client.force_authenticate(user=employee)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    created = client.post(
        "/api/v1/expenses/",
        {
            "category": str(category.id),
            "title": "Lunch",
            "description": "",
            "amount": "40.00",
            "currency": "USD",
            "incurred_on": str(date.today()),
        },
        format="json",
    )
    assert created.status_code == 201
    expense_id = created.data["id"]
    submitted = client.post(f"/api/v1/expenses/{expense_id}/submit/")
    assert submitted.status_code == 200
    assert submitted.data["status"] == Expense.Status.SUBMITTED

    denied = client.post(f"/api/v1/expenses/{expense_id}/approve/", {"comment": "nope"}, format="json")
    assert denied.status_code == 403

    client.force_authenticate(user=manager)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    approved = client.post(
        f"/api/v1/expenses/{expense_id}/approve/", {"comment": "ok"}, format="json"
    )
    assert approved.status_code == 200
    assert approved.data["status"] == Expense.Status.APPROVED

    # Second expense that would exceed budget while first is approved
    client.force_authenticate(user=employee)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    second = client.post(
        "/api/v1/expenses/",
        {
            "category": str(category.id),
            "title": "Dinner",
            "description": "",
            "amount": "70.00",
            "currency": "USD",
            "incurred_on": str(date.today()),
        },
        format="json",
    )
    blocked = client.post(f"/api/v1/expenses/{second.data['id']}/submit/")
    assert blocked.status_code == 400
    assert blocked.data["code"] == "budget_exceeded"


@pytest.mark.django_db
def test_reject_releases_budget_capacity():
    employee = UserFactory()
    manager = UserFactory()
    org = OrganizationFactory()
    MembershipFactory(user=employee, organization=org, role=Membership.Role.EMPLOYEE)
    MembershipFactory(user=manager, organization=org, role=Membership.Role.MANAGER)
    category = CategoryFactory(organization=org)
    BudgetFactory(
        organization=org,
        limit_amount="50.00",
        currency="USD",
        period_start=date.today() - timedelta(days=1),
        period_end=date.today() + timedelta(days=30),
    )

    client = APIClient()
    client.force_authenticate(user=employee)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    first = client.post(
        "/api/v1/expenses/",
        {
            "category": str(category.id),
            "title": "Hotel",
            "amount": "50.00",
            "currency": "USD",
            "incurred_on": str(date.today()),
            "description": "",
        },
        format="json",
    )
    client.post(f"/api/v1/expenses/{first.data['id']}/submit/")

    client.force_authenticate(user=manager)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    rejected = client.post(
        f"/api/v1/expenses/{first.data['id']}/reject/", {"comment": "receipt missing"}, format="json"
    )
    assert rejected.status_code == 200
    assert rejected.data["status"] == Expense.Status.REJECTED

    client.force_authenticate(user=employee)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    second = client.post(
        "/api/v1/expenses/",
        {
            "category": str(category.id),
            "title": "Hotel 2",
            "amount": "50.00",
            "currency": "USD",
            "incurred_on": str(date.today()),
            "description": "",
        },
        format="json",
    )
    ok = client.post(f"/api/v1/expenses/{second.data['id']}/submit/")
    assert ok.status_code == 200
