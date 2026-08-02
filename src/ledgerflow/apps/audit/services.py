from __future__ import annotations

from typing import Any

from ledgerflow.apps.accounts.models import Organization, User
from ledgerflow.apps.audit.models import AuditEvent


def log_event(
    *,
    organization: Organization,
    event_type: str,
    payload: dict[str, Any] | None = None,
    actor: User | None = None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        organization=organization,
        actor=actor,
        event_type=event_type,
        payload=payload or {},
    )
