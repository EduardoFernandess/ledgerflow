from django.contrib.auth import get_user_model
from rest_framework import serializers

from ledgerflow.apps.accounts.models import Membership, Organization

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "full_name", "created_at")
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "user", "role", "created_at")
        read_only_fields = fields


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "is_active", "created_at")
        read_only_fields = ("id", "slug", "is_active", "created_at")


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    full_name = serializers.CharField(max_length=255)
    organization_name = serializers.CharField(max_length=255, required=False, allow_blank=True)


class AddMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255)
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(
        choices=[c for c in Membership.Role.choices if c[0] != Membership.Role.OWNER],
        default=Membership.Role.EMPLOYEE,
    )


class UpdateMemberSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=Membership.Role.choices)
