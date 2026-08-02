from __future__ import annotations

from django.db import transaction

from ledgerflow.apps.accounts.models import Membership, Organization, User
from ledgerflow.apps.audit.services import log_event
from ledgerflow.apps.core.exceptions import ServiceError


@transaction.atomic
def register_user(
    *,
    email: str,
    password: str,
    full_name: str,
    organization_name: str | None = None,
) -> tuple[User, Organization | None, Membership | None]:
    if User.objects.filter(email__iexact=email).exists():
        raise ServiceError("A user with this email already exists.", code="email_taken")

    user = User.objects.create_user(email=email, password=password, full_name=full_name)
    organization = None
    membership = None
    if organization_name:
        organization, membership = create_organization(owner=user, name=organization_name)
    return user, organization, membership


@transaction.atomic
def create_organization(*, owner: User, name: str) -> tuple[Organization, Membership]:
    organization = Organization.objects.create(name=name)
    membership = Membership.objects.create(
        user=owner,
        organization=organization,
        role=Membership.Role.OWNER,
    )
    log_event(
        organization=organization,
        actor=owner,
        event_type="organization.created",
        payload={"name": name},
    )
    return organization, membership


@transaction.atomic
def add_member(
    *,
    organization: Organization,
    actor: User,
    email: str,
    full_name: str,
    password: str,
    role: str = Membership.Role.EMPLOYEE,
) -> Membership:
    if role == Membership.Role.OWNER:
        raise ServiceError("Cannot assign owner via member invite.", code="invalid_role")

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        user = User.objects.create_user(email=email, password=password, full_name=full_name)
    elif Membership.objects.filter(user=user, organization=organization).exists():
        raise ServiceError("User is already a member of this organization.", code="already_member")

    membership = Membership.objects.create(user=user, organization=organization, role=role)
    log_event(
        organization=organization,
        actor=actor,
        event_type="membership.created",
        payload={"user_id": str(user.id), "role": role},
    )
    return membership


@transaction.atomic
def update_member_role(
    *,
    organization: Organization,
    actor: User,
    target_user: User,
    role: str,
) -> Membership:
    membership = Membership.objects.select_for_update().get(
        organization=organization, user=target_user
    )
    if membership.role == Membership.Role.OWNER and role != Membership.Role.OWNER:
        owner_count = Membership.objects.filter(
            organization=organization, role=Membership.Role.OWNER
        ).count()
        if owner_count <= 1:
            raise ServiceError("Organization must retain at least one owner.", code="last_owner")
    membership.role = role
    membership.save(update_fields=["role"])
    log_event(
        organization=organization,
        actor=actor,
        event_type="membership.role_updated",
        payload={"user_id": str(target_user.id), "role": role},
    )
    return membership
