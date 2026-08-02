from datetime import date

import pytest
from rest_framework.test import APIClient

from ledgerflow.apps.accounts.models import Membership
from ledgerflow.apps.reporting.models import ExportJob
from tests.factories import (
    CategoryFactory,
    MembershipFactory,
    OrganizationFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_export_job_succeeds_eager():
    manager = UserFactory()
    org = OrganizationFactory()
    MembershipFactory(user=manager, organization=org, role=Membership.Role.MANAGER)
    category = CategoryFactory(organization=org)
    employee = UserFactory()
    MembershipFactory(user=employee, organization=org, role=Membership.Role.EMPLOYEE)

    client = APIClient()
    client.force_authenticate(user=employee)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    expense = client.post(
        "/api/v1/expenses/",
        {
            "category": str(category.id),
            "title": "Train",
            "amount": "15.00",
            "currency": "USD",
            "incurred_on": str(date.today()),
            "description": "",
        },
        format="json",
    )
    assert expense.status_code == 201

    client.force_authenticate(user=manager)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    job = client.post("/api/v1/reports/exports/", format="json")
    assert job.status_code == 201
    detail = client.get(f"/api/v1/reports/exports/{job.data['id']}/")
    assert detail.status_code == 200
    assert detail.data["status"] == ExportJob.Status.SUCCEEDED
    assert detail.data["result_file"]
