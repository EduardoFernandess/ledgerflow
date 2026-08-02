from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from ledgerflow.apps.budgets.models import Budget
from ledgerflow.apps.budgets.services import create_budget, usage_for_budget
from ledgerflow.apps.core.exceptions import ServiceError, error_response
from ledgerflow.apps.core.permissions import IsAdminOrAbove, IsOrganizationMember


class BudgetSerializer(serializers.ModelSerializer):
    used_amount = serializers.SerializerMethodField()

    class Meta:
        model = Budget
        fields = (
            "id",
            "category",
            "limit_amount",
            "currency",
            "period_start",
            "period_end",
            "used_amount",
            "created_at",
        )
        read_only_fields = ("id", "used_amount", "created_at")

    def get_used_amount(self, obj):
        return str(usage_for_budget(obj))


class BudgetListCreateView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request):
        qs = Budget.objects.filter(organization=request.organization)
        return Response(BudgetSerializer(qs, many=True).data)

    def post(self, request):
        if not IsAdminOrAbove().has_permission(request, self):
            return Response({"detail": "Forbidden.", "code": "forbidden"}, status=403)
        serializer = BudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            budget = create_budget(
                organization=request.organization, **serializer.validated_data
            )
        except ServiceError as exc:
            return error_response(exc)
        return Response(BudgetSerializer(budget).data, status=201)
