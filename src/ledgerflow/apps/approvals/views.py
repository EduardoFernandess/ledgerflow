from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from ledgerflow.apps.approvals.models import ApprovalPolicy
from ledgerflow.apps.approvals.services import approve_expense, reject_expense
from ledgerflow.apps.core.exceptions import ServiceError, error_response
from ledgerflow.apps.core.permissions import IsManagerOrAbove, IsOrganizationMember
from ledgerflow.apps.expenses.models import Expense
from ledgerflow.apps.expenses.serializers import ExpenseSerializer


class ApprovalDecisionSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, default="")


class ApprovalPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalPolicy
        fields = (
            "id",
            "min_amount",
            "max_amount",
            "required_role",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class ExpenseApproveView(APIView):
    permission_classes = [IsOrganizationMember, IsManagerOrAbove]

    def post(self, request, pk):
        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            expense = Expense.objects.get(pk=pk, organization=request.organization)
            expense = approve_expense(
                expense=expense,
                actor=request.user,
                membership=request.membership,
                comment=serializer.validated_data["comment"],
            )
        except Expense.DoesNotExist:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        except ServiceError as exc:
            return error_response(exc)
        return Response(ExpenseSerializer(expense).data)


class ExpenseRejectView(APIView):
    permission_classes = [IsOrganizationMember, IsManagerOrAbove]

    def post(self, request, pk):
        serializer = ApprovalDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            expense = Expense.objects.get(pk=pk, organization=request.organization)
            expense = reject_expense(
                expense=expense,
                actor=request.user,
                membership=request.membership,
                comment=serializer.validated_data["comment"],
            )
        except Expense.DoesNotExist:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        except ServiceError as exc:
            return error_response(exc)
        return Response(ExpenseSerializer(expense).data)


class ApprovalPolicyListCreateView(APIView):
    permission_classes = [IsOrganizationMember, IsManagerOrAbove]

    def get(self, request):
        qs = ApprovalPolicy.objects.filter(organization=request.organization)
        return Response(ApprovalPolicySerializer(qs, many=True).data)

    def post(self, request):
        serializer = ApprovalPolicySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        policy = ApprovalPolicy.objects.create(
            organization=request.organization, **serializer.validated_data
        )
        return Response(ApprovalPolicySerializer(policy).data, status=201)
