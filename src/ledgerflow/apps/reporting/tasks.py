from __future__ import annotations

import csv
import io

from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone

from ledgerflow.apps.expenses.models import Expense
from ledgerflow.apps.reporting.models import ExportJob


@shared_task
def generate_csv_export(job_id: str) -> str:
    job = ExportJob.objects.select_related("organization").get(pk=job_id)
    job.status = ExportJob.Status.RUNNING
    job.save(update_fields=["status"])
    try:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["id", "title", "amount", "currency", "status", "category", "incurred_on", "submitter"]
        )
        expenses = (
            Expense.objects.filter(organization=job.organization)
            .select_related("category", "submitter")
            .order_by("created_at")
        )
        for expense in expenses:
            writer.writerow(
                [
                    str(expense.id),
                    expense.title,
                    expense.amount,
                    expense.currency,
                    expense.status,
                    expense.category.name,
                    expense.incurred_on.isoformat(),
                    expense.submitter.email,
                ]
            )
        content = ContentFile(buffer.getvalue().encode("utf-8"))
        job.result_file.save(f"export-{job.id}.csv", content, save=False)
        job.status = ExportJob.Status.SUCCEEDED
        job.finished_at = timezone.now()
        job.save()
    except Exception as exc:  # noqa: BLE001
        job.status = ExportJob.Status.FAILED
        job.error_message = str(exc)
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])
        raise
    return str(job.id)
