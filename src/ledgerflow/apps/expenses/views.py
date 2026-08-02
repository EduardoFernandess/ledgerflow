from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ledgerflow.apps.core.exceptions import ServiceError, error_response
from ledgerflow.apps.core.permissions import IsAdminOrAbove, IsOrganizationMember
from ledgerflow.apps.expenses.models import Category, Expense
from ledgerflow.apps.expenses.serializers import (
    CategorySerializer,
    ExpenseAttachmentSerializer,
    ExpenseCreateSerializer,
    ExpenseSerializer,
)
from ledgerflow.apps.expenses.services import (
    add_attachment,
    cancel_expense,
    create_expense,
    submit_expense,
    update_draft_expense,
)


class CategoryListCreateView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request):
        qs = Category.objects.filter(organization=request.organization, is_active=True)
        return Response(CategorySerializer(qs, many=True).data)

    def post(self, request):
        if not IsAdminOrAbove().has_permission(request, self):
            return Response({"detail": "Forbidden.", "code": "forbidden"}, status=403)
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = Category.objects.create(
            organization=request.organization, **serializer.validated_data
        )
        return Response(CategorySerializer(category).data, status=status.HTTP_201_CREATED)


class ExpenseListCreateView(APIView):
    permission_classes = [IsOrganizationMember]

    def get(self, request):
        qs = Expense.objects.filter(organization=request.organization).select_related("category")
        if request.membership.role == "employee":
            qs = qs.filter(submitter=request.user)
        return Response(ExpenseSerializer(qs, many=True).data)

    def post(self, request):
        serializer = ExpenseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            expense = create_expense(
                organization=request.organization,
                submitter=request.user,
                category=data.pop("category"),
                **data,
            )
        except ServiceError as exc:
            return error_response(exc)
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)


class ExpenseDetailView(APIView):
    permission_classes = [IsOrganizationMember]

    def _get(self, request, pk):
        try:
            expense = Expense.objects.get(pk=pk, organization=request.organization)
        except Expense.DoesNotExist:
            return None
        if request.membership.role == "employee" and expense.submitter_id != request.user.id:
            return None
        return expense

    def get(self, request, pk):
        expense = self._get(request, pk)
        if expense is None:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        return Response(ExpenseSerializer(expense).data)

    def patch(self, request, pk):
        expense = self._get(request, pk)
        if expense is None:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        serializer = ExpenseCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            expense = update_draft_expense(
                expense=expense, actor=request.user, **serializer.validated_data
            )
        except ServiceError as exc:
            return error_response(exc)
        return Response(ExpenseSerializer(expense).data)


class ExpenseSubmitView(APIView):
    permission_classes = [IsOrganizationMember]

    def post(self, request, pk):
        try:
            expense = Expense.objects.get(pk=pk, organization=request.organization)
            expense = submit_expense(expense=expense, actor=request.user)
        except Expense.DoesNotExist:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        except ServiceError as exc:
            return error_response(exc)
        return Response(ExpenseSerializer(expense).data)


class ExpenseCancelView(APIView):
    permission_classes = [IsOrganizationMember]

    def post(self, request, pk):
        try:
            expense = Expense.objects.get(pk=pk, organization=request.organization)
            expense = cancel_expense(expense=expense, actor=request.user)
        except Expense.DoesNotExist:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        except ServiceError as exc:
            return error_response(exc)
        return Response(ExpenseSerializer(expense).data)


class ExpenseAttachmentCreateView(APIView):
    permission_classes = [IsOrganizationMember]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, pk):
        try:
            expense = Expense.objects.get(pk=pk, organization=request.organization)
        except Expense.DoesNotExist:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        uploaded = request.FILES.get("file")
        if uploaded is None:
            return Response(
                {"detail": "file is required.", "code": "validation_error"}, status=400
            )
        try:
            attachment = add_attachment(expense=expense, uploaded_file=uploaded)
        except ServiceError as exc:
            return error_response(exc)
        return Response(ExpenseAttachmentSerializer(attachment).data, status=201)
