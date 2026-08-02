from __future__ import annotations

from rest_framework.permissions import BasePermission

from ledgerflow.apps.accounts.models import Membership, Organization


ROLE_RANK = {
    Membership.Role.EMPLOYEE: 1,
    Membership.Role.MANAGER: 2,
    Membership.Role.ADMIN: 3,
    Membership.Role.OWNER: 4,
}


def resolve_membership(user, organization_id: str | None) -> tuple[Organization, Membership]:
    memberships = (
        Membership.objects.select_related("organization")
        .filter(user=user, organization__is_active=True)
    )
    if organization_id:
        membership = memberships.filter(organization_id=organization_id).first()
        if membership is None:
            raise Membership.DoesNotExist
        return membership.organization, membership

    count = memberships.count()
    if count == 0:
        raise Membership.DoesNotExist
    if count > 1:
        from rest_framework.exceptions import ValidationError

        raise ValidationError(
            {
                "detail": "X-Organization-ID header is required when the user belongs to multiple organizations.",
                "code": "organization_required",
            }
        )
    membership = memberships.get()
    return membership.organization, membership


class IsOrganizationMember(BasePermission):
    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            org, membership = resolve_membership(request.user, getattr(request, "organization_id", None))
        except Membership.DoesNotExist:
            return False
        except Exception:
            raise
        request.organization = org
        request.membership = membership
        return True


class HasMinRole(BasePermission):
    min_role = Membership.Role.EMPLOYEE

    def has_permission(self, request, view) -> bool:
        membership = getattr(request, "membership", None)
        if membership is None:
            return False
        return ROLE_RANK[membership.role] >= ROLE_RANK[self.min_role]


class IsManagerOrAbove(HasMinRole):
    min_role = Membership.Role.MANAGER


class IsAdminOrAbove(HasMinRole):
    min_role = Membership.Role.ADMIN
