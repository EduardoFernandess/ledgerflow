import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from ledgerflow.apps.accounts.models import Membership
from tests.factories import MembershipFactory, OrganizationFactory, UserFactory


@pytest.mark.django_db
def test_register_and_token():
    client = APIClient()
    response = client.post(
        "/api/v1/auth/register/",
        {
            "email": "alice@example.com",
            "password": "password123",
            "full_name": "Alice",
            "organization_name": "Acme",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["organization"]["name"] == "Acme"

    token = client.post(
        "/api/v1/auth/token/",
        {"email": "alice@example.com", "password": "password123"},
        format="json",
    )
    assert token.status_code == status.HTTP_200_OK
    assert "access" in token.data


@pytest.mark.django_db
def test_tenant_isolation_for_expenses():
    client = APIClient()
    user1 = UserFactory()
    user2 = UserFactory()
    org1 = OrganizationFactory(name="Org One")
    org2 = OrganizationFactory(name="Org Two")
    MembershipFactory(user=user1, organization=org1, role=Membership.Role.OWNER)
    MembershipFactory(user=user2, organization=org2, role=Membership.Role.OWNER)

    client.force_authenticate(user=user1)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org1.id))
    cat = client.post("/api/v1/categories/", {"name": "Travel"}, format="json")
    assert cat.status_code == 201
    expense = client.post(
        "/api/v1/expenses/",
        {
            "category": cat.data["id"],
            "title": "Flight",
            "description": "",
            "amount": "120.00",
            "currency": "USD",
            "incurred_on": "2026-01-15",
        },
        format="json",
    )
    assert expense.status_code == 201
    expense_id = expense.data["id"]

    client.force_authenticate(user=user2)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org2.id))
    leaked = client.get(f"/api/v1/expenses/{expense_id}/")
    assert leaked.status_code == 404
