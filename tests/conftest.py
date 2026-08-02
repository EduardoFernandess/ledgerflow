import pytest
from rest_framework.test import APIClient

from ledgerflow.apps.accounts.models import Membership
from tests.factories import MembershipFactory, OrganizationFactory, UserFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def owner_context():
    user = UserFactory()
    org = OrganizationFactory()
    membership = MembershipFactory(user=user, organization=org, role=Membership.Role.OWNER)
    return user, org, membership


@pytest.fixture
def auth_client(api_client, owner_context):
    user, org, membership = owner_context
    api_client.force_authenticate(user=user)
    api_client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    return api_client, user, org, membership
