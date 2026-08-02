from rest_framework import serializers

from ledgerflow.apps.expenses.models import Category, Expense, ExpenseAttachment


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "is_active", "created_at")
        read_only_fields = ("id", "created_at")


class ExpenseAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseAttachment
        fields = ("id", "file_name", "content_type", "size_bytes", "file", "created_at")
        read_only_fields = fields


class ExpenseSerializer(serializers.ModelSerializer):
    attachments = ExpenseAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Expense
        fields = (
            "id",
            "category",
            "title",
            "description",
            "amount",
            "currency",
            "status",
            "incurred_on",
            "submitted_at",
            "created_at",
            "updated_at",
            "attachments",
        )
        read_only_fields = ("id", "status", "submitted_at", "created_at", "updated_at", "attachments")


class ExpenseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ("category", "title", "description", "amount", "currency", "incurred_on")
