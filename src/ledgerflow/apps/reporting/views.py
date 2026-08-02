from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from ledgerflow.apps.core.permissions import IsManagerOrAbove, IsOrganizationMember
from ledgerflow.apps.reporting.models import ExportJob
from ledgerflow.apps.reporting.tasks import generate_csv_export


class ExportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportJob
        fields = (
            "id",
            "status",
            "format",
            "result_file",
            "error_message",
            "created_at",
            "finished_at",
        )
        read_only_fields = fields


class ExportJobCreateView(APIView):
    permission_classes = [IsOrganizationMember, IsManagerOrAbove]

    def post(self, request):
        job = ExportJob.objects.create(
            organization=request.organization,
            requested_by=request.user,
            format=ExportJob.Format.CSV,
        )
        generate_csv_export.delay(str(job.id))
        job.refresh_from_db()
        return Response(ExportJobSerializer(job).data, status=201)


class ExportJobDetailView(APIView):
    permission_classes = [IsOrganizationMember, IsManagerOrAbove]

    def get(self, request, pk):
        try:
            job = ExportJob.objects.get(pk=pk, organization=request.organization)
        except ExportJob.DoesNotExist:
            return Response({"detail": "Not found.", "code": "not_found"}, status=404)
        return Response(ExportJobSerializer(job).data)
