from __future__ import annotations

import uuid

from django.utils.deprecation import MiddlewareMixin


class RequestIDMiddleware(MiddlewareMixin):
    HEADER = "HTTP_X_REQUEST_ID"

    def process_request(self, request):
        request_id = request.META.get(self.HEADER) or str(uuid.uuid4())
        request.request_id = request_id


class OrganizationContextMiddleware(MiddlewareMixin):
    HEADER = "HTTP_X_ORGANIZATION_ID"

    def process_request(self, request):
        request.organization_id = request.META.get(self.HEADER)
        request.organization = None
        request.membership = None
