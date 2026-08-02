from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from ledgerflow.apps.accounts.models import Membership, Organization
from ledgerflow.apps.accounts.serializers import (
    AddMemberSerializer,
    MembershipSerializer,
    OrganizationSerializer,
    RegisterSerializer,
    UpdateMemberSerializer,
    UserSerializer,
)
from ledgerflow.apps.accounts.services import (
    add_member,
    create_organization,
    register_user,
    update_member_role,
)
from ledgerflow.apps.accounts.tokens import EmailTokenObtainPairSerializer
from ledgerflow.apps.core.exceptions import ServiceError, error_response
from ledgerflow.apps.core.permissions import ROLE_RANK

User = get_user_model()


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


def _load_org_membership(request, org_id):
    try:
        membership = Membership.objects.select_related("organization").get(
            user=request.user, organization_id=org_id, organization__is_active=True
        )
    except Membership.DoesNotExist:
        return None, None
    request.organization = membership.organization
    request.membership = membership
    return membership.organization, membership


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, organization, membership = register_user(**serializer.validated_data)
        except ServiceError as exc:
            return error_response(exc)
        payload = {
            "user": UserSerializer(user).data,
            "organization": OrganizationSerializer(organization).data if organization else None,
            "membership": MembershipSerializer(membership).data if membership else None,
        }
        return Response(payload, status=status.HTTP_201_CREATED)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = Membership.objects.select_related("organization").filter(user=request.user)
        return Response(
            {
                "user": UserSerializer(request.user).data,
                "memberships": [
                    {
                        "id": str(m.id),
                        "role": m.role,
                        "organization": OrganizationSerializer(m.organization).data,
                    }
                    for m in memberships
                ],
            }
        )


class OrganizationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orgs = Organization.objects.filter(memberships__user=request.user, is_active=True)
        return Response(OrganizationSerializer(orgs, many=True).data)

    def post(self, request):
        serializer = OrganizationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization, membership = create_organization(
            owner=request.user, name=serializer.validated_data["name"]
        )
        return Response(
            {
                "organization": OrganizationSerializer(organization).data,
                "membership": MembershipSerializer(membership).data,
            },
            status=status.HTTP_201_CREATED,
        )


class OrganizationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        org, membership = _load_org_membership(request, pk)
        if org is None:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        return Response(OrganizationSerializer(org).data)

    def patch(self, request, pk):
        org, membership = _load_org_membership(request, pk)
        if org is None:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        if ROLE_RANK[membership.role] < ROLE_RANK["admin"]:
            return Response({"detail": "Forbidden.", "code": "forbidden"}, status=403)
        serializer = OrganizationSerializer(org, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MemberListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        org, membership = _load_org_membership(request, pk)
        if org is None:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        if ROLE_RANK[membership.role] < ROLE_RANK["admin"]:
            return Response({"detail": "Forbidden.", "code": "forbidden"}, status=403)
        members = Membership.objects.select_related("user").filter(organization=org)
        return Response(MembershipSerializer(members, many=True).data)

    def post(self, request, pk):
        org, membership = _load_org_membership(request, pk)
        if org is None:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        if ROLE_RANK[membership.role] < ROLE_RANK["admin"]:
            return Response({"detail": "Forbidden.", "code": "forbidden"}, status=403)
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            created = add_member(
                organization=org,
                actor=request.user,
                **serializer.validated_data,
            )
        except ServiceError as exc:
            return error_response(exc)
        return Response(MembershipSerializer(created).data, status=status.HTTP_201_CREATED)


class MemberDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk, user_id):
        org, membership = _load_org_membership(request, pk)
        if org is None:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        if ROLE_RANK[membership.role] < ROLE_RANK["admin"]:
            return Response({"detail": "Forbidden.", "code": "forbidden"}, status=403)
        serializer = UpdateMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            target = User.objects.get(pk=user_id)
            updated = update_member_role(
                organization=org,
                actor=request.user,
                target_user=target,
                role=serializer.validated_data["role"],
            )
        except User.DoesNotExist:
            return Response({"detail": "User not found.", "code": "not_found"}, status=404)
        except Membership.DoesNotExist:
            return Response({"detail": "Membership not found.", "code": "not_found"}, status=404)
        except ServiceError as exc:
            return error_response(exc)
        return Response(MembershipSerializer(updated).data)

    def delete(self, request, pk, user_id):
        org, membership = _load_org_membership(request, pk)
        if org is None:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        if ROLE_RANK[membership.role] < ROLE_RANK["admin"]:
            return Response({"detail": "Forbidden.", "code": "forbidden"}, status=403)
        try:
            target_membership = Membership.objects.get(organization=org, user_id=user_id)
        except Membership.DoesNotExist:
            return Response({"detail": "Membership not found.", "code": "not_found"}, status=404)
        if target_membership.role == Membership.Role.OWNER:
            return Response(
                {"detail": "Cannot remove an owner.", "code": "cannot_remove_owner"},
                status=400,
            )
        target_membership.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
